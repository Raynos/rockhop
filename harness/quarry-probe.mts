/** Repeatable Quarry baseline: held GO and current checked-in skilled input, both classes. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, expandFrames } from '../src/core/replay';
import type { BikeClass, InputFrame } from '../src/core/types';
import { createQuarrySim } from './quarry-sim';

const ids = ['d1-dust-devil', 'd2-conveyor', 'd3-rope-walk'];
const go: InputFrame = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false };
const rows = [];
for (const id of ids) for (const bike of ['rookie', 'pro'] as BikeClass[]) {
  const sim = await createQuarrySim(id, undefined, 120, bike);
  const faults: { tick: number; x: number; reason: string }[] = [];
  let maxX = sim.state().bike.pos.x;
  for (let tick = 1; tick <= 120 * 90 && sim.phase() !== 'finished'; tick++) {
    for (const event of sim.step(go)) if (event.type === 'fault') faults.push({ tick, x: sim.state().bike.pos.x, reason: event.reason });
    maxX = Math.max(maxX, sim.state().bike.pos.x);
  }
  rows.push({ id, bike, route: 'held-go', phase: sim.phase(), time: sim.runTime(), faults: faults.length, faultSites: faults, maxX, hash: sim.hash() });

  const name = bike === 'pro' && fs.existsSync(path.join('harness/inputs', id, 'bot-3-pro.json')) ? 'bot-3-pro.json' : 'bot-3.json';
  const file = path.join('harness/inputs', id, name);
  if (!fs.existsSync(file)) continue;
  const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
  const replay = await createQuarrySim(id, rec.header.seed, rec.header.physicsHz, bike);
  replay.run(expandFrames(rec));
  rows.push({ id, bike, route: 'old-bot-3', phase: replay.phase(), time: replay.runTime(), faults: replay.faults(), x: replay.state().bike.pos.x, hash: replay.hash() });
}
console.log(JSON.stringify(rows, null, 2));
