/** Continue a clean prefix with measured controls. If none finishes, emits the longest clean extension for repair. */
import fs from 'node:fs';
import { expandFrames, InputRecorder, quantizeInput } from '../../../../src/core/replay';
import { createSimFor } from '../../../../harness/lib/sim';
import { loadRecording } from '../../../../harness/lib/recording';

const track = process.argv[2];
const sourcePath = process.argv[3];
if (!track || !sourcePath) throw new Error('usage: extend-tail.mts track candidate-path');
const source = loadRecording(sourcePath);
const prefix = expandFrames(source);
const options = [];
for (const throttle of [0.35, 0.65, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1])
  options.push({ code: `t${throttle}l${lean}`, frame: quantizeInput({ throttle, lean }) });
const rows = [];
let best: { score: number; code: string; frames: typeof prefix; phase: string; time: number; hash: string; maxX: number; fault: unknown } | null = null;
for (const option of options) {
  const sim = await createSimFor(source);
  const frames = [...prefix];
  for (const f of prefix) sim.step(f);
  if (sim.phase() !== 'riding' || sim.faults()) throw new Error(`${track} source prefix is not clean riding`);
  let maxX = sim.state().bike.pos.x;
  let fault = null;
  for (let tick = 0; tick < 2400 && sim.phase() !== 'finished'; tick++) {
    const events = sim.step(option.frame);
    frames.push(option.frame);
    maxX = Math.max(maxX, sim.state().bike.pos.x);
    const first = events.find(e => e.type === 'fault');
    if (first) { fault = { x: sim.state().bike.pos.x, tick: prefix.length + tick + 1, reason: first.reason }; break; }
  }
  const score = sim.phase() === 'finished' ? Infinity : fault?.x ?? maxX;
  const row = { code: option.code, phase: sim.phase(), time: sim.runTime(), hash: sim.hash(), maxX, fault, appended: frames.length - prefix.length };
  rows.push(row);
  if (!best || score > best.score || score === Infinity && row.time < best.time) best = { ...row, score, frames };
}
const out = `/tmp/rockhop-pro-early-${track}-tail`;
fs.writeFileSync(`${out}.report.json`, `${JSON.stringify({ track, sourcePath, prefixFrames: prefix.length, best: best && { code: best.code, phase: best.phase, time: best.time, hash: best.hash, maxX: best.maxX, fault: best.fault }, rows }, null, 2)}\n`);
if (!best) throw new Error('no control tested');
const recording = new InputRecorder({ ...source.header, note: `Pro early tail ${best.code}` });
for (const f of best.frames) recording.push(f);
fs.writeFileSync(`${out}.candidate.json`, `${JSON.stringify({ magic: 'TRIN', ...recording.toRecording() })}\n`);
console.log(JSON.stringify({ track, sourcePath, best: { code: best.code, phase: best.phase, time: best.time, hash: best.hash, maxX: best.maxX, fault: best.fault }, candidate: `${out}.candidate.json` }));
