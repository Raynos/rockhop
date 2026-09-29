/** Local input tolerance of an S1 upper station shelf shifted backward by at most one metre. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { S1 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const pro = decodeJSON(fs.readFileSync('harness/inputs/s1-lift-line/bot-3-pro.json', 'utf8'));
const frames = expandFrames(pro);
const deck = S1.obstacles[S1.diamondGoal!.platformObstacleIndex]!;
const original = { params: { ...deck.params }, pos: { ...deck.pos } };
const configs = [[288, 10], [287.75, 10.25], [287.5, 10.5], [287.25, 10.75], [287, 11]] as const;
const variations = [{ name: 'base', x: 0, ticks: 0, throttle: -1, lean: 0 }];
for (const x of [278, 281, 284]) for (const ticks of [4, 8, 12]) {
  variations.push({ name: `coast${ticks}@${x}`, x, ticks, throttle: 0, lean: 0 });
  variations.push({ name: `half${ticks}@${x}`, x, ticks, throttle: 0.5, lean: 0 });
  variations.push({ name: `back${ticks}@${x}`, x, ticks, throttle: 1, lean: -0.2 });
  variations.push({ name: `front${ticks}@${x}`, x, ticks, throttle: 1, lean: 0.2 });
}
const locator = await createSim(S1.id, pro.header.seed, 120, { bike: 'pro' });
const ticksAtX = new Map<number, number>();
for (let tick = 0; tick < frames.length; tick++) {
  for (const x of [278, 281, 284]) if (!ticksAtX.has(x) && locator.state().bike.pos.x >= x) ticksAtX.set(x, tick);
  locator.step(frames[tick]!);
  if (ticksAtX.size === 3) break;
}
const rows = [];
for (const [x, length] of configs) {
  deck.pos = { ...original.pos, x };
  deck.params = { ...original.params, length };
  for (const variation of variations) {
    const start = ticksAtX.get(variation.x) ?? -1;
    const sim = await createSim(S1.id, pro.header.seed, 120, { bike: 'pro' });
    let firstFaultX: number | null = null;
    for (let tick = 0; tick < frames.length; tick++) {
      const src = frames[tick]!;
      const changed = start >= 0 && tick >= start && tick < start + variation.ticks;
      const input = changed ? quantizeInput({ ...src, throttle: variation.throttle, brake: 0, lean: variation.lean }) : src;
      const faults = sim.faults();
      sim.step(input);
      if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
      if (sim.phase() === 'finished') break;
    }
    rows.push({ x, length, variation: variation.name, phase: sim.phase(), faults: sim.faults(), firstFaultX,
      route: sim.rules.counters().diamondRouteCrossed === true, seconds: sim.runTime() });
  }
}
deck.pos = original.pos;
deck.params = original.params;
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/s1-robustness.json', `${JSON.stringify(rows, null, 2)}\n`);
for (const [x, length] of configs) {
  const pass = rows.filter(row => row.x === x && row.phase === 'finished' && row.faults === 0 && row.route);
  console.log(JSON.stringify({ x, length, passed: pass.length, of: variations.length,
    inputs: pass.map(row => row.variation) }));
}
