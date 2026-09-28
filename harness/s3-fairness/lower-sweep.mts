/** Bounded three-window search for a physically lower S3 snow-cat exit. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';

const file = 'docs/evidence/snowline-diamond/s3-whiteout-rookie.rec.json';
const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
const frames = expandFrames(rec);
const sim = await createSimFor(rec);
let start = 0;
while (start < frames.length && sim.state().bike.pos.x < 112) sim.step(frames[start++]!);
if (sim.faults()) throw new Error('faulted before x=112');
const snap = sim.snap();
const prefixX = sim.state().bike.pos.x;
const options = [
  { name: 'source', frame: null },
  ...[0, 0.5, 1].flatMap(throttle => [-1, 0, 1].map(lean => ({
    name: `t${throttle}l${lean}`, frame: quantizeInput({ throttle, lean }),
  }))),
];
const rows = [];
for (const pre of options) for (const launch of options) for (const flight of options) {
  sim.restore(snap);
  let idx = start;
  let maxFrontY = -Infinity, maxBikeY = -Infinity, maxRearY = -Infinity, frontContacts = 0;
  let at144: unknown = null, at148: unknown = null;
  while (idx < frames.length && sim.state().bike.pos.x < 160 && sim.phase() === 'riding' && sim.faults() === 0) {
    const x = sim.state().bike.pos.x;
    const input = x < 125 ? pre.frame ?? frames[idx]! : x < 132 ? launch.frame ?? frames[idx]! :
      x < 152 ? flight.frame ?? frames[idx]! : frames[idx]!;
    sim.step(input);
    idx++;
    const s = sim.state();
    if (s.wheels.front.pos.x >= 144 && s.wheels.front.pos.x <= 152) {
      maxFrontY = Math.max(maxFrontY, s.wheels.front.pos.y);
      maxBikeY = Math.max(maxBikeY, s.bike.pos.y);
      maxRearY = Math.max(maxRearY, s.wheels.rear.pos.y);
      if (s.wheels.front.grounded && s.wheels.front.pos.y >= 3.3) frontContacts++;
    }
    if (at144 === null && s.bike.pos.x >= 144) at144 = {y:s.bike.pos.y,frontY:s.wheels.front.pos.y,rearY:s.wheels.rear.pos.y};
    if (at148 === null && s.bike.pos.x >= 148) at148 = {y:s.bike.pos.y,frontY:s.wheels.front.pos.y,rearY:s.wheels.rear.pos.y};
  }
  const x = sim.state().bike.pos.x;
  rows.push({ pre: pre.name, launch: launch.name, flight: flight.name,
    alive: x >= 160 && sim.faults() === 0, x, fault: sim.faults(),
    proof:sim.rules.counters().diamondRouteCrossed === true,
    maxFrontY, maxBikeY, maxRearY, frontContacts, at144, at148 });
}
rows.sort((a,b) => Number(b.alive)-Number(a.alive) || a.frontContacts-b.frontContacts ||
  a.maxFrontY-b.maxFrontY || a.maxBikeY-b.maxBikeY);
const out = { source: file, prefixX, total:rows.length,
  alive:rows.filter(r=>r.alive).length, cleanLower:rows.filter(r=>r.alive && !r.proof && r.frontContacts===0 && r.maxBikeY<3).length,
  top:rows.slice(0,50) };
fs.mkdirSync('docs/evidence/s3-fairness',{recursive:true});
fs.writeFileSync('docs/evidence/s3-fairness/lower-sweep.json',JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({total:out.total,alive:out.alive,cleanLower:out.cleanLower,top:out.top.slice(0,15)},null,2));
