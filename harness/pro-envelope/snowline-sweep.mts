/** Deterministic two-window upper-route control sweep from fresh clean approaches. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { createSimFor } from '../lib/sim';

const id = process.argv[2] === 'S1' ? 's1-lift-line' : 's3-whiteout';
const output = '/tmp/rockhop-pro-envelope-audit';
fs.mkdirSync(output, { recursive: true });
const windows = id === 's1-lift-line'
  ? { start: 260, pre: 267, flight: 295, stop: 315 }
  : { start: 125, pre: 132, flight: 152, stop: 160 };
const options: { name: string; frame: InputFrame | null }[] = [{ name: 'source', frame: null }];
for (const throttle of [0, 0.5, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1]) {
  options.push({ name: `t${throttle}l${lean}`, frame: quantizeInput({ throttle, lean }) });
}

for (const bike of ['rookie', 'pro'] as const) {
  const path = bike === 'pro'
    ? `docs/evidence/course-remaster/pro-envelope/${id === 's1-lift-line' ? 's1-pro-upper' : 's3-pro-lower-approach'}.replay.json`
    : `harness/inputs/${id}/bot-3.json`;
  const recording = decodeJSON(fs.readFileSync(path, 'utf8'));
  const source = expandFrames(recording);
  const sim = await createSimFor(recording);
  let start = 0;
  while (start < source.length && sim.state().bike.pos.x < windows.start) sim.step(source[start++]!);
  if (sim.phase() !== 'riding' || sim.faults()) throw new Error(`${bike}: clean approach missing at x=${windows.start}`);
  const startX = sim.state().bike.pos.x;
  const snapshot = sim.snap();
  const candidates = [];
  const postSamples: { pre: string; flight: string; post: string; x: number; time: number }[] = [];
  let best: { key: string; time: number; frames: InputFrame[] } | null = null;
  for (const pre of options) for (const flight of options) {
    sim.restore(snapshot);
    let index = start;
    const injected: InputFrame[] = [];
    while (index < source.length && sim.state().bike.pos.x < windows.stop && !sim.faults() && sim.phase() === 'riding') {
      const x = sim.state().bike.pos.x;
      const frame = x < windows.pre ? (pre.frame ?? source[index]!) : x < windows.flight ? (flight.frame ?? source[index]!) : source[index]!;
      injected.push(frame);
      sim.step(frame);
      index++;
    }
    const proof = sim.rules.counters().diamondRouteCrossed === true;
    const alive = sim.faults() === 0 && sim.state().bike.pos.x >= windows.stop;
    if (id === 's3-whiteout' && bike === 'pro' && proof && alive) {
      const local = sim.snap();
      for (const throttle of [0, 0.5, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1]) {
        sim.restore(local);
        const post = quantizeInput({ throttle, lean });
        const postFrames: InputFrame[] = [];
        while (postFrames.length < 900 && sim.state().bike.pos.x < 180 && sim.phase() === 'riding' && !sim.faults()) {
          sim.step(post); postFrames.push(post);
        }
        if (!sim.faults() && sim.state().bike.pos.x >= 180) {
          const name = `t${throttle}l${lean}`;
          postSamples.push({ pre: pre.name, flight: flight.name, post: name, x: sim.state().bike.pos.x, time: sim.runTime() });
          if (postSamples.length <= 12) {
            const rec = new InputRecorder({ ...recording.header, note: `Pro S3 upper postdeck ${pre.name}/${flight.name}/${name}` });
            for (const frame of [...source.slice(0, start), ...injected, ...postFrames]) rec.push(frame);
            fs.writeFileSync(`${output}/s3-upper-post-${postSamples.length}.replay.json`, encodeJSON(rec.toRecording()));
          }
        }
      }
      sim.restore(local);
    }
    let finished = false;
    if (proof && alive) {
      while (index < source.length && !sim.faults() && sim.phase() === 'riding') sim.step(source[index++]!);
      finished = sim.phase() === 'finished' && !sim.faults();
      if (finished && (!best || sim.runTime() < best.time)) best = {
        key: `${pre.name}/${flight.name}`, time: sim.runTime(),
        frames: [...source.slice(0, start), ...injected, ...source.slice(start + injected.length, index)],
      };
    }
    candidates.push({ pre: pre.name, flight: flight.name, proof, alive, finished });
  }
  const report = { id, bike, path, startX, tested: candidates.length,
    proof: candidates.filter((c) => c.proof).length,
    proofAlive: candidates.filter((c) => c.proof && c.alive).length,
    proofFinished: candidates.filter((c) => c.finished).length,
    postAliveAt180: postSamples.length,
    postSamples: postSamples.slice(0, 12),
    best: best && { key: best.key, time: best.time },
    sample: candidates.filter((c) => c.proof && c.alive).slice(0, 10) };
  fs.writeFileSync(`${output}/${id}-${bike}-sweep.json`, `${JSON.stringify(report, null, 2)}\n`);
  if (best) {
    const rec = new InputRecorder({ ...recording.header, note: `pro envelope snowline sweep ${best.key}` });
    for (const frame of best.frames) rec.push(frame);
    fs.writeFileSync(`${output}/${id}-${bike}-upper-sweep.replay.json`, encodeJSON(rec.toRecording()));
  }
  console.log(JSON.stringify(report));
}
