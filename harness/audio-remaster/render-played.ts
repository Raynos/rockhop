/** Played audio evidence: the video input drives the same run rules, model and DSP, without speakers. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { NEUTRAL_INPUT, type GameEvent } from '../../src/core/types';
import { expandFrames } from '../../src/core/replay';
import { ModelDriver, SCENE_INDEX, silenceGameplay } from '../../src/audio/driver';
import { RockhopSynth } from '../../src/audio/dsp/synth';
import { encodeWav16, interleave } from '../../src/audio/offline';
import { P_HEADER, P_TRANSIENT_COUNT, P_TRANSIENT_STRIDE, TK } from '../../src/audio/params';
import type { SampleManifest } from '../../src/audio/samples/player';
import { zoneOf } from '../../src/audio/music/zone';
import { engineDuckDb } from '../../src/audio/graph/webAudio';
import { loadRecording } from '../lib/recording';
import { createSimFor } from '../lib/sim';
import { srcFingerprint } from '../lib/metrics';

const candidateFamilies = new Map<number, string>([
  [TK.grunt, 'grunt'], [TK.crowdRoar, 'crowdRoar'], [TK.crowdCheer, 'crowdCheer'],
  [TK.crowdGroan, 'crowdGroan'], [TK.crowdApplause, 'crowdApplause'],
]);
const rate = 48_000;
const hz = 60;
const samplesPerUpdate = rate / hz;
const sha = (bytes: Uint8Array): string => createHash('sha256').update(bytes).digest('hex');

async function render(file: string, seconds: number) {
  const rec = loadRecording(file);
  const frames = expandFrames(rec);
  const sim = await createSimFor(rec);
  const manifestBytes = await fs.readFile('src/audio/samples/manifest.json');
  const manifest = JSON.parse(manifestBytes.toString('utf8')) as SampleManifest;
  const available = async (file: string): Promise<boolean> => fs.access(path.join('public/audio/sfx', file)).then(() => true, () => false);
  const recordedFamilies = new Map<number, string>();
  for (const [kind, family] of candidateFamilies) {
    for (const clip of manifest.oneshots[family] ?? []) {
      if (clip.duration > 0 && await available(clip.file)) { recordedFamilies.set(kind, family); break; }
    }
  }
  const zone = zoneOf(sim.compiled);
  const bed = manifest.beds[zone];
  const bedCovered = !!bed && bed.duration > 0 && await available(bed.file);
  const driver = new ModelDriver();
  driver.setTrack(sim.compiled, sim.seed);
  driver.setBike(sim.bike);
  driver.setScene('run');
  driver.onEvent({ type: 'go' });
  const synth = new RockhopSynth(rate, { seed: sim.seed });
  synth.setBed(false); // The separately mastered recorded score carries this review.
  synth.setAmbienceEnabled(!bedCovered); // A shipped generated biome bed replaces its procedural version.
  const updates = Math.ceil(seconds * hz);
  const left = new Float32Array(updates * samplesPerUpdate);
  const right = new Float32Array(left.length);
  const events: { time: number; tick: number; event: GameEvent }[] = [];
  const transients: { time: number; update: number; kind: number; family: string; gain: number; pitch: number; pan: number; delay: number }[] = [];
  const envelope: { time: number; scene: string; ambientGain: number; duckDb: number; musicDuckDb: number }[] = [];
  let finish: { time: number; tick: number; hash: string } | null = null;
  let tick = 0;
  const ticksPerUpdate = sim.hz / hz;
  assert.ok(Number.isInteger(ticksPerUpdate));
  for (let update = 0; update < updates; update++) {
    for (let sub = 0; sub < ticksPerUpdate; sub++) {
      const emitted = sim.step(frames[tick] ?? NEUTRAL_INPUT);
      tick++;
      for (const event of emitted) {
        events.push({ time: tick / sim.hz, tick, event });
        driver.onEvent(event);
        if (event.type === 'finish' && !finish) {
          finish = { time: sim.runTime(), tick, hash: sim.hash() };
        }
      }
    }
    // App.onResults changes the scene when the run rules publish the panel, 0.4 s after finish.
    driver.setScene(sim.rules.counters().resultsShown ? 'results' : 'run');
    const params = driver.update(sim.state(), 1 / hz, sim.state().input);
    if (driver.scene !== SCENE_INDEX.run) silenceGameplay(params);
    let retained = 0;
    for (let i = 0; i < driver.params.transientCount; i++) {
      const t = driver.params.transients[i]!;
      const family = recordedFamilies.get(t.kind);
      if (family) {
        transients.push({ time: update / hz + t.delay, update, ...t, family });
      } else {
        const from = P_HEADER + i * P_TRANSIENT_STRIDE;
        const to = P_HEADER + retained++ * P_TRANSIENT_STRIDE;
        if (from !== to) params.copyWithin(to, from, from + P_TRANSIENT_STRIDE);
      }
    }
    params[P_TRANSIENT_COUNT] = retained;
    const running = driver.scene === SCENE_INDEX.run;
    envelope.push({ time: update / hz, scene: running ? 'run' : 'results', ambientGain: driver.params.ambientGain, duckDb: driver.params.duckDb, musicDuckDb: running ? engineDuckDb(driver.params.engineGain, driver.params.load) : 0 });
    synth.setParams(params);
    driver.flush();
    synth.process(left, right, update * samplesPerUpdate, samplesPerUpdate);
  }
  return {
    wav: encodeWav16(interleave(left, right), rate, 2),
    data: {
      recording: { path: file, sha256: sha(await fs.readFile(file)), header: rec.header, frames: frames.length },
      physics: { sourceFingerprint: srcFingerprint(), solver: sim.physicsName, finish, faults: sim.faults(), finalHash: sim.hash(), finalTick: tick },
      audio: { seconds: updates / hz, sampleRate: rate, updateHz: hz, channels: 2, proceduralRecordedFamiliesSuppressed: [...recordedFamilies.values()], proceduralBiomeBedSuppressed: bedCovered, zone, sampleManifestSha256: sha(manifestBytes), musicSuppressed: true },
      events, transients, envelope,
      limits: 'Sample start times are model update + transient delay (same 60Hz/48kHz schedule as live DSP). Video input is identical; any source fingerprint/hash difference must be resolved before claiming visual alignment. No speakers or subjective audio verdict.',
    },
  };
}

const jobs = [
  { name: 'c1-ride', recording: 'harness/inputs/c1-low-tide/bot-3.json', seconds: 30.8 },
  { name: 'c1-crash-restart', recording: 'harness/inputs/c1-low-tide/crash.json', seconds: 5 },
];
const out = path.resolve('harness/out/audio-remaster');
await fs.mkdir(out, { recursive: true });
for (const job of jobs) {
  const first = await render(job.recording, job.seconds);
  const second = await render(job.recording, job.seconds);
  assert.equal(sha(first.wav), sha(second.wav), 'played audio render must be byte identical');
  assert.deepEqual(first.data, second.data);
  await fs.writeFile(path.join(out, `${job.name}-procedural.wav`), first.wav);
  await fs.writeFile(path.join(out, `${job.name}-events.json`), JSON.stringify({ ...first.data, wavSha256: sha(first.wav), byteIdenticalSecondRender: true }, null, 2) + '\n');
  console.log(JSON.stringify({ name: job.name, finish: first.data.physics.finish, faults: first.data.physics.faults, sampleEvents: first.data.transients.length, wavSha256: sha(first.wav), byteIdentical: true }));
}
