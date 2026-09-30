/** Bounded Node search around a stale recording's first obstacle. No browser or golden writes. */
import fs from 'node:fs';
import { expandFrames, InputRecorder, quantizeInput } from '../../../../src/core/replay';
import { createSim } from '../../../../harness/lib/sim';
import { loadRecording } from '../../../../harness/lib/recording';

const track = process.argv[2];
const source = process.argv[3] === 'rookie' ? 'rookie' : 'pro';
const faultX = Number(process.argv[4]);
if (!track || !Number.isFinite(faultX)) throw new Error('usage: search-window.mts track rookie|pro first-fault-x');
const original = loadRecording(`harness/inputs/${track}/bot-3${source === 'pro' ? '-pro' : ''}.json`);
const oldFrames = expandFrames(original);
const options = [];
for (const throttle of [0, 0.35, 0.65, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1]) {
  options.push({ name: `t${throttle}l${lean}`, frame: quantizeInput({ throttle, lean }) });
}
for (const lean of [-1, 0, 1]) options.push({ name: `bl${lean}`, frame: quantizeInput({ brake: 1, lean }) });
const roots = [faultX - 30, faultX - 20, faultX - 12, faultX - 6].filter(x => x > 0);
const durations = [30, 60, 120, 180];
const results = [];
let best: { frames: typeof oldFrames; x: number; time: number; hash: string; desc: string } | null = null;
for (const rootX of roots) {
  const sim = await createSim(track, original.header.seed, original.header.physicsHz, { bike: 'pro' });
  let index = 0;
  while (index < oldFrames.length && sim.state().bike.pos.x < rootX && sim.phase() === 'riding' && !sim.faults()) sim.step(oldFrames[index++]!);
  if (sim.faults()) { results.push({ rootX, blocked: `source fault before x=${rootX}` }); continue; }
  const snap = sim.snap();
  for (const duration of durations) for (const option of options) {
    sim.restore(snap);
    const trial = [...oldFrames.slice(0, index)];
    let maxX = sim.state().bike.pos.x;
    let firstFault = null;
    for (let j = index; j < oldFrames.length && sim.phase() !== 'finished'; j++) {
      const f = j < index + duration ? option.frame : oldFrames[j]!;
      trial.push(f);
      const events = sim.step(f);
      if (events.some(e => e.type === 'fault') && firstFault === null) firstFault = { x: sim.state().bike.pos.x, tick: j + 1 };
      maxX = Math.max(maxX, sim.state().bike.pos.x);
      if (firstFault) break;
    }
    const row = { rootX, startTick: index, duration, option: option.name, maxX, firstFault, phase: sim.phase(), time: sim.runTime(), hash: sim.hash() };
    results.push(row);
    if (!firstFault && sim.phase() === 'finished' && (!best || row.time < best.time)) best = { frames: trial, x: maxX, time: row.time, hash: row.hash, desc: `${rootX}:${duration}:${option.name}` };
  }
}
results.sort((a, b) => Number(b.phase === 'finished' && !b.firstFault) - Number(a.phase === 'finished' && !a.firstFault) || (b.maxX ?? 0) - (a.maxX ?? 0));
const prefix = `/tmp/rockhop-pro-early-${track}-${source}`;
fs.writeFileSync(`${prefix}.search.json`, `${JSON.stringify({ track, source, seed: original.header.seed, tested: results.length, best: best && { x: best.x, time: best.time, hash: best.hash, desc: best.desc }, top: results.slice(0, 25) }, null, 2)}\n`);
if (best) {
  const rec = new InputRecorder({ ...original.header, bike: 'pro', physics: 'v2', note: `candidate ${best.desc}` });
  for (const f of best.frames) rec.push(f);
  fs.writeFileSync(`${prefix}.candidate.json`, `${JSON.stringify({ magic: 'TRIN', ...rec.toRecording() })}\n`);
}
console.log(JSON.stringify({ track, source, tested: results.length, best: best && { x: best.x, time: best.time, hash: best.hash, desc: best.desc }, top: results.slice(0, 5) }));
