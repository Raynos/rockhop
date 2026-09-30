/** Broad two-window launch sweep from both bikes' measured x=138 approach. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { S2 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const id = 's2-cornice';
if (S2.diamondGoal?.id !== 's2-wind-shelf') throw new Error('S2 wind shelf is not authored');
const options: { code: string; frame: InputFrame }[] = [];
for (const throttle of [0, 0.35, 0.65, 1]) for (const lean of [-1, -0.5, 0, 0.5, 1])
  options.push({ code: `t${throttle}-l${lean}`, frame: quantizeInput({ throttle, lean }) });
for (const lean of [-1, 0, 1]) options.push({ code: `brake-l${lean}`, frame: quantizeInput({ brake: 1, lean }) });

const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  const file = bike === 'rookie' ? 'harness/inputs/s2-cornice/bot-3.json' : 'docs/evidence/course-remaster/pro-envelope/s2-pro-upper.replay.json';
  const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
  const sim = await createSim(id, rec.header.seed, rec.header.physicsHz, { bike });
  for (const frame of expandFrames(rec)) {
    if (sim.state().bike.pos.x >= 138) break;
    sim.step(frame);
  }
  if (sim.faults()) throw new Error(`${bike} approach faulted`);
  const root = sim.snap();
  const prefixX = sim.state().bike.pos.x;
  const candidates = [];
  for (const pre of options) for (const flight of options) {
    sim.restore(root);
    let maxY = -Infinity;
    let at157 = null;
    let at165 = null;
    let tick = 0;
    for (; tick < 900 && sim.phase() === 'riding' && !sim.faults() && sim.state().bike.pos.x < 178; tick++) {
      const x = sim.state().bike.pos.x;
      const frame = x < 143 ? pre.frame : x < 165 ? flight.frame : quantizeInput({ throttle: 0.8, lean: 0 });
      sim.step(frame);
      const st = sim.state();
      maxY = Math.max(maxY, st.bike.pos.y);
      if (!at157 && st.bike.pos.x >= 157) at157 = { y: st.bike.pos.y, rearY: st.wheels.rear.pos.y, vx: st.bike.vel.x };
      if (!at165 && st.wheels.rear.pos.x >= 165) at165 = { rearY: st.wheels.rear.pos.y, grounded: st.wheels.rear.grounded, contact: st.contacts.rear };
    }
    candidates.push({ pre: pre.code, flight: flight.code, tick, x: sim.state().bike.pos.x, maxY, at157, at165,
      proof: sim.rules.counters().diamondRouteCrossed === true, fault: sim.faults() > 0 });
  }
  rows.push({ bike, prefixX, total: candidates.length,
    proof: candidates.filter(c => c.proof).length,
    proofAliveAt178: candidates.filter(c => c.proof && !c.fault && c.x >= 178).length,
    lowerAliveAt178: candidates.filter(c => !c.proof && !c.fault && c.x >= 178).length,
    bestUpper: candidates.filter(c => c.proof).sort((a,b) => Number(a.fault)-Number(b.fault) || b.x-a.x).slice(0, 10),
    bestLower: candidates.filter(c => !c.proof && !c.fault).sort((a,b) => b.x-a.x).slice(0,5) });
}
const out = '/tmp/rockhop-pro-envelope-audit/s2-mechanic.json';
fs.mkdirSync('/tmp/rockhop-pro-envelope-audit', { recursive: true });
fs.writeFileSync(out, `${JSON.stringify(rows, null, 2)}\n`);
console.log(JSON.stringify(rows, null, 2));
