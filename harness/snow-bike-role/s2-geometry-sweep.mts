/** Isolated S2 wind-shelf dimensions sweep; no source edit. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { S2 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const deck = S2.obstacles[S2.diamondGoal!.platformObstacleIndex]!;
const original = { params: { ...deck.params }, pos: { ...deck.pos }, goal: { ...S2.diamondGoal! } };
const configs = [
  [157, 13, 8.5], [156, 14, 8.5], [155, 15, 8.5], [158, 12, 8.5],
  [157, 14, 8.5], [157, 15, 8.5], [157, 12, 8.5],
  [157, 13, 8.4], [157, 13, 8.6], [156, 14, 8.6], [156, 14, 8.4],
] as const;
const recordings = ['rookie', 'pro'].map(bike => ({ bike,
  recording: decodeJSON(fs.readFileSync(`harness/inputs/s2-cornice/bot-3${bike === 'pro' ? '-pro' : ''}.json`, 'utf8')) }));
const rows = [];
for (const [x, length, height] of configs) {
  deck.pos = { ...original.pos, x };
  deck.params = { ...original.params, length, height };
  S2.diamondGoal = { ...original.goal, minRearY: height + 0.2 };
  for (const { bike, recording } of recordings) {
    const sim = await createSim(S2.id, recording.header.seed, 120, { bike: bike as 'rookie' | 'pro' });
    let firstFaultX: number | null = null;
    let maxX = sim.state().bike.pos.x;
    for (const frame of expandFrames(recording)) {
      const faults = sim.faults();
      sim.step(frame);
      maxX = Math.max(maxX, sim.state().bike.pos.x);
      if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
      if (sim.phase() === 'finished') break;
    }
    const route = sim.rules.counters().diamondRouteCrossed === true;
    rows.push({ x, length, height, bike, phase: sim.phase(), faults: sim.faults(), firstFaultX, maxX,
      seconds: sim.runTime(), route, medal: sim.phase() === 'finished'
        ? medalFor(sim.runTime(), sim.faults(), S2.meta?.targetTimeS, bike as 'rookie' | 'pro', route) : null,
      hash: sim.hash() });
  }
}
deck.pos = original.pos;
deck.params = original.params;
S2.diamondGoal = original.goal;
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/s2-geometry-sweep.json', `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify(rows.map(({ x, length, height, bike, phase, faults, route, seconds, firstFaultX }) =>
  ({ x, length, height, bike, phase, faults, route, seconds: +seconds.toFixed(3), firstFaultX })), null, 2));
