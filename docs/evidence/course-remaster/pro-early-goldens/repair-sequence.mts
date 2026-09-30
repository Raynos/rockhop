/** Greedy, bounded Node-only repair of a stale Pro input: each step moves the first fault farther down-course. */
import fs from 'node:fs';
import { expandFrames, InputRecorder, quantizeInput } from '../../../../src/core/replay';
import { createSim } from '../../../../harness/lib/sim';
import { loadRecording } from '../../../../harness/lib/recording';

const track = process.argv[2];
const maxRounds = Number(process.argv[3] ?? 20);
if (!track) throw new Error('usage: repair-sequence.mts track [max-rounds]');
const sourcePath = process.argv[4] ?? `harness/inputs/${track}/bot-3-pro.json`;
const original = loadRecording(sourcePath);
let frames = expandFrames(original);
const controls = [];
for (const throttle of [0, 0.35, 0.65, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1])
  controls.push({ code: `t${throttle}l${lean}`, frame: quantizeInput({ throttle, lean }) });
for (const lean of [-1, 0, 1]) controls.push({ code: `bl${lean}`, frame: quantizeInput({ brake: 1, lean }) });
const durations = [30, 60, 120, 180, 300];
const report = [];
const sim = await createSim(track, original.header.seed, original.header.physicsHz, { bike: 'pro' });
async function assess(candidate: typeof frames) {
  const fresh = await createSim(track, original.header.seed, original.header.physicsHz, { bike: 'pro' });
  let fault: { x: number; tick: number; reason: string } | null = null;
  let maxX = 0;
  let ticks = 0;
  for (let tick = 0; tick < candidate.length && fresh.phase() !== 'finished'; tick++) {
    const events = fresh.step(candidate[tick]!);
    ticks = tick + 1;
    maxX = Math.max(maxX, fresh.state().bike.pos.x);
    const first = events.find(e => e.type === 'fault');
    if (first) { fault = { x: fresh.state().bike.pos.x, tick: tick + 1, reason: first.reason }; break; }
  }
  return { fault, maxX, phase: fresh.phase(), time: fresh.runTime(), hash: fresh.hash(), ticks };
}
let current = await assess(frames);
for (let round = 0; round < maxRounds && current.phase !== 'finished'; round++) {
  if (!current.fault) break;
  const faultX = current.fault.x;
  const roots = [Math.max(0, faultX - 40), Math.max(0, faultX - 25), Math.max(0, faultX - 15), Math.max(0, faultX - 8), Math.max(0, faultX - 3)];
  let best = { ...current, frames, patch: 'source' };
  let tested = 0;
  for (const rootX of [...new Set(roots)]) {
    let index = 0;
    const root = await createSim(track, original.header.seed, original.header.physicsHz, { bike: 'pro' });
    while (index < frames.length && root.state().bike.pos.x < rootX && root.phase() === 'riding' && !root.faults()) root.step(frames[index++]!);
    if (root.faults()) continue;
    const snapshot = root.snap();
    for (const duration of durations) for (const control of controls) {
      sim.restore(snapshot);
      const end = Math.min(frames.length, index + duration);
      let firstFault: { x: number; tick: number; reason: string } | null = null;
      let maxX = sim.state().bike.pos.x;
      for (let tick = index; tick < frames.length && sim.phase() !== 'finished'; tick++) {
        const frame = tick < end ? control.frame : frames[tick]!;
        const first = sim.step(frame).find(e => e.type === 'fault');
        maxX = Math.max(maxX, sim.state().bike.pos.x);
        if (first) { firstFault = { x: sim.state().bike.pos.x, tick: tick + 1, reason: first.reason }; break; }
      }
      tested++;
      const result = { fault: firstFault, maxX, phase: sim.phase(), time: sim.runTime(), hash: sim.hash(), ticks: firstFault?.tick ?? frames.length };
      const score = result.phase === 'finished' ? Infinity : firstFault?.x ?? maxX;
      const bestScore = best.phase === 'finished' ? Infinity : best.fault?.x ?? best.maxX;
      if (score > bestScore + 0.25 || (score === Infinity && result.time < best.time)) {
        const patched = frames.slice();
        for (let tick = index; tick < end; tick++) patched[tick] = control.frame;
        best = { ...result, frames: patched, patch: `x${rootX.toFixed(1)}-tick${index}-${duration}-${control.code}` };
      }
    }
  }
  report.push({ round: round + 1, before: current, after: { fault: best.fault, maxX: best.maxX, phase: best.phase, time: best.time, hash: best.hash }, patch: best.patch, tested });
  console.log(JSON.stringify(report.at(-1)));
  if (best.patch === 'source') break;
  frames = best.frames;
  current = await assess(frames);
  if (current.hash !== best.hash || current.phase !== best.phase) throw new Error(`snapshot search did not replay at round ${round + 1}`);
}
const prefix = `/tmp/rockhop-pro-early-${track}-repair`;
fs.writeFileSync(`${prefix}.report.json`, `${JSON.stringify({ track, seed: original.header.seed, sourcePath, rounds: report, outcome: current }, null, 2)}\n`);
const recording = new InputRecorder({ ...original.header, note: `Pro early repair, ${report.length} measured windows` });
for (const frame of frames.slice(0, current.phase === 'finished' ? current.ticks : undefined)) recording.push(frame);
fs.writeFileSync(`${prefix}.candidate.json`, `${JSON.stringify({ magic: 'TRIN', ...recording.toRecording() })}\n`);
console.log(JSON.stringify({ track, outcome: current, rounds: report.length, candidate: `${prefix}.candidate.json` }));
