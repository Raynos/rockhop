/** Measure fault-to-commanded-respawn latency on each Quarry bike/course pair. */
import fs from 'node:fs';
import type { BikeClass, InputFrame } from '../src/core/types';
import { createQuarrySim } from './quarry-sim';

const go: InputFrame = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false };
const restart: InputFrame = { ...go, throttle: 0, restart: true };
const rows = [];
for (const id of ['d1-dust-devil', 'd2-conveyor', 'd3-rope-walk']) for (const bike of ['rookie', 'pro'] as BikeClass[]) {
  const sim = await createQuarrySim(id, undefined, 120, bike);
  let faultTick = -1;
  for (let tick = 1; tick <= 120 * 90; tick++) {
    const events = sim.step(go);
    if (events.some((event) => event.type === 'fault')) { faultTick = tick; break; }
  }
  if (faultTick < 0 || sim.phase() !== 'crashed') throw new Error(`${id} ${bike}: no held-GO crash`);
  const events = sim.step(restart);
  const restartEvent = events.find((event) => event.type === 'restart');
  const row = { id, bike, faultTick, restartLatencyTicks: restartEvent ? 1 : -1,
    restartLatencyMs: restartEvent ? 1000 / 120 : -1, phaseAfter: sim.phase(),
    checkpoint: restartEvent?.checkpoint ?? null };
  if (!restartEvent || sim.phase() !== 'riding') throw new Error(`${id} ${bike}: failed next-tick respawn`);
  rows.push(row);
}
fs.writeFileSync('docs/evidence/quarry-retarget/restart-latency.json', `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify(rows));
