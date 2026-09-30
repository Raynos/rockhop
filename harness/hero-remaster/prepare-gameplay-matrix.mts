/** Freeze actual Game input/events for later matched rider comparisons.
 * No renderer, asset, physics, synthetic pose, teleport or audio changes.
 * tsx harness/hero-remaster/prepare-gameplay-matrix.mts --out=FRESH_DIRECTORY
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Game } from '../../src/game/game';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import { decodeJSON, expandFrames, type RecordingHeader } from '../../src/core/replay';
import type { BikeClass, GameEvent, PhysicsState } from '../../src/core/types';
import type { GameRenderer } from '../../src/render/index';
import { FrameBuilder } from '../../src/render/frame';

const arg = (name: string) => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3);
const outArg = arg('out');
assert(outArg, 'provide --out=FRESH_DIRECTORY');
const out = path.resolve(outArg);
assert(!fs.existsSync(out), 'never overwrite frozen evidence');
const sha = (file: string) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const floatBytes = (value: number | null) => {
  if (value === null) return null;
  const bytes = Buffer.alloc(8); bytes.writeDoubleLE(value); return bytes.toString('hex');
};
const finite = (value: unknown): boolean => typeof value === 'number' ? Number.isFinite(value)
  : Array.isArray(value) ? value.every(finite)
  : value !== null && typeof value === 'object' ? Object.values(value).every(finite) : true;
interface Sample {
  inputTick: number; physicsTick: number; stateHash: string; phase: string;
  lean: number; commandedLean: number; grounded: { rear: boolean; front: boolean };
  riderBody: { relX: number; relY: number; relAngle: number; relUp: number };
}
interface Landing {
  event: Extract<GameEvent, { type: 'land' }>; sample: Sample;
  precedingAirborneTicks: number; oppositeWheelGrounded: boolean;
  recovery: { sample: Sample; uninterruptedRiding: boolean } | null;
}
interface Run {
  file: string; sourceSHA256: string; header: RecordingHeader; inputTicks: number;
  traceSHA256: string; final: { hash: string; phase: string; faults: number; runTime: number; finishTimeFloat64LE: string | null };
  forward: Sample | null; backward: Sample | null; landings: Landing[];
  events: (GameEvent & { inputTick: number })[]; snapshots: Sample[];
}
const files = (['rookie', 'pro'] as const).flatMap(bike => [
  ...['lean-transitions', 'hop', 'crash-restart', 'thrown', 'thrown-2249'].map(name => `harness/inputs/riding-poses/${name}-${bike}.json`),
  `harness/inputs/b1-first-ride/bot-3${bike === 'pro' ? '-pro' : ''}.json`,
  `harness/inputs/e2-rear-wheel-first/bot-3${bike === 'pro' ? '-pro' : ''}.json`,
]).concat(['harness/inputs/lab-ramp-jump/bot-3.json', 'harness/inputs/c1-low-tide/bot-3-pro.json']);

const codeFiles = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap(e =>
  e.isDirectory() ? codeFiles(path.join(dir, e.name)) : e.name.endsWith('.ts') && !e.name.endsWith('.test.ts') ? [path.join(dir, e.name)] : []);
const sourceFiles = ['harness/hero-remaster/prepare-gameplay-matrix.mts', 'src/game/game.ts', 'src/game/routeGoal.ts',
  'src/render/frame.ts', 'src/core/riderGeometry.ts', 'src/core/replay.ts', 'src/core/hash.ts',
  ...codeFiles('src/physics'), ...codeFiles('src/tracks')].map(file => ({ file, sha256: sha(file) }));

function replay(file: string): Run {
  const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
  assert.equal(rec.header.physics, 'v2');
  const hz = rec.header.physicsHz;
  const game = new Game({ physics: createBikePhysicsV2(hz), physicsHz: hz,
    renderer: { setTrack() {}, onEvent() {}, setQuality() {}, setBikeClass() {} } as unknown as GameRenderer,
    autoSkipCountdown: true, ghostEnabled: false });
  game.loadTrack(rec.header.trackId, rec.header.seed, rec.header.bike);
  const frames = new FrameBuilder();
  const trace = crypto.createHash('sha256');
  const inputs = expandFrames(rec);
  const run: Run = { file, sourceSHA256: sha(file), header: rec.header, inputTicks: inputs.length,
    traceSHA256: '', final: { hash: '', phase: '', faults: 0, runTime: 0, finishTimeFloat64LE: null },
    forward: null, backward: null, landings: [], events: [], snapshots: [] };
  let emitted: GameEvent[] = [], airborneTicks = 0;
  const phases: string[] = [];
  game.onEvent(event => emitted.push(structuredClone(event)));
  for (let index = 0; index < inputs.length; index++) {
    emitted = []; game.setInput(inputs[index]!); game.step(1);
    const st: PhysicsState = game.getState();
    assert(finite(st), `${file} input tick ${index + 1} finite physics`);
    const f = frames.build(st, 1);
    assert(f.riderBody.present, `${file} uses actual physical rider body`);
    const sample: Sample = { inputTick: index + 1, physicsTick: st.tick, stateHash: game.hashState(), phase: game.phase(),
      lean: st.rider.lean, commandedLean: inputs[index]!.lean,
      grounded: { rear: st.wheels.rear.grounded, front: st.wheels.front.grounded },
      riderBody: { relX: f.riderBody.relX, relY: f.riderBody.relY, relAngle: f.riderBody.relAngle, relUp: f.riderBody.relUp } };
    run.snapshots.push(sample); phases.push(sample.phase);
    trace.update(JSON.stringify([sample, game.runTime(), game.faults(), floatBytes(st.finishTime)]));
    if (sample.phase === 'riding') {
      if (run.forward === null || sample.lean > run.forward.lean) run.forward = sample;
      if (run.backward === null || sample.lean < run.backward.lean) run.backward = sample;
    }
    for (const event of emitted) {
      run.events.push({ ...event, inputTick: index + 1 });
      if (event.type === 'land' && sample.phase === 'riding' && sample.grounded[event.wheel] && airborneTicks >= Math.ceil(hz * .1)) {
        run.landings.push({ event, sample, precedingAirborneTicks: airborneTicks,
          oppositeWheelGrounded: event.wheel === 'front' ? sample.grounded.rear : sample.grounded.front, recovery: null });
      }
    }
    airborneTicks = sample.phase === 'riding' && !sample.grounded.front && !sample.grounded.rear ? airborneTicks + 1 : 0;
  }
  for (const land of run.landings) {
    const last = land.sample.inputTick + hz;
    if (last <= run.snapshots.length) land.recovery = {
      sample: run.snapshots[last - 1]!,
      uninterruptedRiding: phases.slice(land.sample.inputTick - 1, last).every(p => p === 'riding'),
    };
  }
  run.traceSHA256 = trace.digest('hex');
  run.final = { hash: game.hashState(), phase: game.phase(), faults: game.faults(), runTime: game.runTime(),
    finishTimeFloat64LE: floatBytes(game.getState().finishTime) };
  return run;
}

const runs: Run[] = [];
for (const file of files) {
  const first = replay(file), second = replay(file);
  assert.deepEqual(first, second, `${file}: independent actual Game traces match exactly`);
  assert.equal(sha(file), first.sourceSHA256);
  runs.push(first);
  console.log(JSON.stringify({ file, ticks: first.inputTicks, lean: [first.backward?.lean, first.forward?.lean],
    landings: first.landings.map(l => ({ wheel: l.event.wheel, tick: l.sample.inputTick, impulse: l.event.impulse,
      recovery: l.recovery?.uninterruptedRiding, oppositeGrounded: l.oppositeWheelGrounded })), final: first.final }));
}

const cases: object[] = [], missing: string[] = [];
const recordings = new Map<string, string>();
function addCase(bike: BikeClass, kind: string, run: Run, center: Sample, detail: object) {
  const hz = run.header.physicsHz, id = `${bike}-${kind}`;
  const recording = `recordings/${path.basename(path.dirname(run.file))}-${path.basename(run.file)}`;
  recordings.set(recording, run.file);
  const start = Math.max(1, center.inputTick - Math.round(hz * .5));
  const end = Math.min(run.inputTicks, center.inputTick + hz);
  cases.push({ id, bike, kind, recording, sourcePath: run.file, sourceSHA256: run.sourceSHA256,
    header: run.header, replayFromInputTick: 1, window: { startInputTick: start, centerInputTick: center.inputTick, endInputTick: end },
    matchedSamples: [start, center.inputTick, end].map(t => run.snapshots[t - 1]), detail,
    wholeRecordingTraceSHA256: run.traceSHA256, final: run.final });
}
for (const bike of ['rookie', 'pro'] as const) {
  const subjects = runs.filter(r => (r.header.bike ?? 'rookie') === bike);
  const lean = subjects.find(r => r.file.includes('lean-transitions'))!;
  for (const [kind, sample, sign] of [['maximum-forward-lean', lean.forward, 1], ['maximum-backward-lean', lean.backward, -1]] as const) {
    if (sample && sample.commandedLean === sign && sign * sample.lean >= .99) addCase(bike, kind, lean, sample, { observedLean: sample.lean, commandedLean: sign });
    else missing.push(`${bike}/${kind}: no riding state reached physical lean magnitude .99 under full command`);
  }
  for (const wheel of ['front', 'rear'] as const) {
    const landings = subjects.flatMap(run => run.landings.map(landing => ({ run, landing })))
      .filter(({ landing: l }) => l.event.wheel === wheel && !l.oppositeWheelGrounded && l.recovery?.uninterruptedRiding)
      .sort((a, b) => b.landing.event.impulse - a.landing.event.impulse);
    const chosen = landings[0];
    if (chosen) addCase(bike, `${wheel}-landing-recovery`, chosen.run, chosen.landing.sample, chosen.landing);
    else missing.push(`${bike}/${wheel}-landing-recovery: no exclusive first-wheel landing after >=100ms airborne with one uninterrupted riding second`);
  }
  const crash = subjects.find(r => r.file.includes('crash-restart'))!;
  const restart = crash.events.find(e => e.type === 'restart' && crash.events.some(f => f.type === 'fault' && f.inputTick < e.inputTick)
    && crash.snapshots[e.inputTick - 1]?.phase === 'riding' && crash.snapshots[e.inputTick - 1]!.physicsTick <= 1);
  if (restart) addCase(bike, 'crash-instant-restart', crash, crash.snapshots[restart.inputTick - 1]!, { restart, faults: crash.final.faults });
  else missing.push(`${bike}/crash-instant-restart: prescribed recording does not restart from crash within one tick`);
  const clear = subjects.find(r => r.file.includes('b1-first-ride') && r.final.finishTimeFloat64LE !== null)
    ?? subjects.find(r => r.file.includes('c1-low-tide') && r.final.finishTimeFloat64LE !== null);
  const finish = clear?.events.find(e => e.type === 'finish');
  if (clear && finish) addCase(bike, 'recorded-clear', clear, clear.snapshots[finish.inputTick - 1]!, { finish, finishTimeFloat64LE: clear.final.finishTimeFloat64LE });
  else missing.push(`${bike}/recorded-clear: no prescribed B1/C1 inputs clear current physics/rules`);
}
assert(sourceFiles.every(s => sha(s.file) === s.sha256), 'physics/game/track source remained fixed during both plays');
fs.mkdirSync(path.join(out, 'recordings'), { recursive: true });
for (const [recording, source] of recordings) fs.copyFileSync(source, path.join(out, recording));
const report = { status: 'input preparation only; no new body, rendered contact or later visual gate accepted',
  method: 'Actual production Game + createBikePhysicsV2 + FrameBuilder; two independent whole input plays, no teleport or pose injection',
  repeat: 'Every per-tick state/phase/run-clock/finish-byte trace and event/sample object matches exactly',
  sourceFiles,
  scanned: runs.map(({ snapshots: _snapshots, ...run }) => run), cases, missing,
  requirementsStillUnmeasured: ['Candidate and baseline browser physics parity', 'Visible palm/grip and sole/peg geometry in both tiers',
    'Full moving clips at matched cameras', 'Restart wall-clock latency', 'Selected body and explicit rig mapping', 'Phone/desktop review'],
  recoveryDefinition: 'No crash/finish/respawn during the second after the landing; not a claim that pose/velocity has fully settled',
  landingDefinition: 'Game land event after >=100ms both-wheel airborne, landed wheel grounded, opposite wheel not yet grounded',
};
fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ out, cases: cases.length, missing }));
