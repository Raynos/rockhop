/** Isolated S1 upper-station landing-shelf geometry sweep; no source edit. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { S1 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const deck = S1.obstacles[S1.diamondGoal!.platformObstacleIndex]!;
const original = { ...deck.params };
const originalPos = { ...deck.pos };
const originalGoal = { ...S1.diamondGoal! };
const configs = [
  [288, 10, 4.6], [287, 11, 4.6], [286, 12, 4.6], [285, 13, 4.6], [284, 14, 4.6],
  [286, 11, 4.6], [285, 12, 4.6], [284, 13, 4.6],
  [287, 10, 4.6], [286, 10, 4.6],
] as const;
const recordings = ['rookie', 'pro'].map(bike => ({ bike,
  recording: decodeJSON(fs.readFileSync(`harness/inputs/s1-lift-line/bot-3${bike === 'pro' ? '-pro' : ''}.json`, 'utf8')) }));
const rows = [];
for (const [x, length, height] of configs) {
  deck.pos = { ...originalPos, x };
  deck.params = { ...original, length, height };
  S1.diamondGoal = { ...originalGoal, minRearY: height + 0.2 };
  for (const { bike, recording } of recordings) {
    const sim = await createSim(S1.id, recording.header.seed, 120, { bike: bike as 'rookie' | 'pro' });
    const frames = expandFrames(recording);
    let firstFaultX: number | null = null;
    let maxX = sim.state().bike.pos.x;
    for (const frame of frames) {
      const faults = sim.faults();
      sim.step(frame);
      maxX = Math.max(maxX, sim.state().bike.pos.x);
      if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
      if (sim.phase() === 'finished') break;
    }
    const route = sim.rules.counters().diamondRouteCrossed === true;
    rows.push({ x, length, height, bike, phase: sim.phase(), faults: sim.faults(), firstFaultX, maxX,
      seconds: sim.runTime(), route, medal: sim.phase() === 'finished'
        ? medalFor(sim.runTime(), sim.faults(), S1.meta?.targetTimeS, bike as 'rookie' | 'pro', route) : null,
      hash: sim.hash() });
  }
}
deck.params = original;
deck.pos = originalPos;
S1.diamondGoal = originalGoal;
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/geometry-sweep.json', `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify(rows, null, 2));
