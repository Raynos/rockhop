import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';

const file = process.argv[2] ?? 'docs/evidence/snowline-diamond/s3-whiteout-rookie.rec.json';
const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
const sim = await createSimFor(rec);
let tick = 0;
let lastCell = -1;
for (const frame of expandFrames(rec)) {
  sim.step(frame);
  tick++;
  const s = sim.state();
  if (s.bike.pos.x < 124 || s.bike.pos.x > 159) continue;
  const cell = Math.floor(s.bike.pos.x * 2);
  if (cell === lastCell) continue;
  lastCell = cell;
  const r = s.wheels.rear, f = s.wheels.front;
  console.log(JSON.stringify({ tick, time: tick / rec.header.physicsHz, bikeX: s.bike.pos.x,
    bikeY: s.bike.pos.y, rearX: r.pos.x, rearY: r.pos.y, rearGrounded: r.grounded,
    frontX: f.pos.x, frontY: f.pos.y, frontGrounded: f.grounded,
    proof: sim.rules.counters().diamondRouteCrossed, fault: sim.faults() }));
}
