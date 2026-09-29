/** Isolated S3 snow-cat wind-shelf sweep; no source edit. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { S3 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const deck = S3.obstacles[S3.diamondGoal!.platformObstacleIndex]!;
const original = { params: { ...deck.params }, pos: { ...deck.pos }, goal: { ...S3.diamondGoal! } };
const configs = [
  [144, 8, 3.1], [144, 9, 3.1], [144, 10, 3.1], [144, 11, 3.1],
  [144, 8, 3.2], [144, 9, 3.2], [144, 10, 3.2],
  [144, 8, 3.3], [144, 9, 3.3], [144, 10, 3.3],
  [145, 9, 3.1], [143, 9, 3.1],
] as const;
const recordings = ['rookie', 'pro'].map(bike => ({ bike,
  recording: decodeJSON(fs.readFileSync(`harness/inputs/s3-whiteout/bot-3${bike === 'pro' ? '-pro' : ''}.json`, 'utf8')) }));
const rows = [];
for (const [x, length, height] of configs) {
  deck.pos = { ...original.pos, x };
  deck.params = { ...original.params, length, height };
  S3.diamondGoal = { ...original.goal, minRearY: height + 0.2 };
  for (const { bike, recording } of recordings) {
    const sim = await createSim(S3.id, recording.header.seed, 120, { bike: bike as 'rookie' | 'pro' });
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
        ? medalFor(sim.runTime(), sim.faults(), S3.meta?.targetTimeS, bike as 'rookie' | 'pro', route) : null,
      hash: sim.hash() });
  }
}
deck.pos = original.pos;
deck.params = original.params;
S3.diamondGoal = original.goal;
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/s3-geometry-sweep.json', `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify(rows.map(({ x, length, height, bike, phase, faults, route, seconds, firstFaultX }) =>
  ({ x, length, height, bike, phase, faults, route, seconds: +seconds.toFixed(3), firstFaultX })), null, 2));
