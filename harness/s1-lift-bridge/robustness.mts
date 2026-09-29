/** Fixed-continuation S1 Pro approach sweep, with bounded post-recording recovery attempts. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { S1 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const rec = decodeJSON(fs.readFileSync('harness/inputs/s1-lift-line/bot-3-pro.json', 'utf8'));
const frames = expandFrames(rec);
const original = S1.obstacles.slice();
const exitIndex = original.findIndex((o) => o.kind === 'plank' && o.pos.x === 298 && o.params?.angleDeg === -15);
if (exitIndex < 0) throw new Error('expected S1 exit');
const vars = [{ name: 'pinned', x: 0, ticks: 0, throttle: -1, lean: 0 }];
for (const x of [278, 281, 284]) for (const ticks of [4, 8, 12]) {
  vars.push({ name: `coast${ticks}@${x}`, x, ticks, throttle: 0, lean: 0 });
  vars.push({ name: `half${ticks}@${x}`, x, ticks, throttle: 0.5, lean: 0 });
  vars.push({ name: `back${ticks}@${x}`, x, ticks, throttle: 1, lean: -0.2 });
  vars.push({ name: `front${ticks}@${x}`, x, ticks, throttle: 1, lean: 0.2 });
}
const loc = await createSim(S1.id, rec.header.seed, 120, { bike: 'pro' });
const ticksAtX = new Map<number, number>();
for (let tick = 0; tick < frames.length; tick++) {
  for (const x of [278, 281, 284]) if (!ticksAtX.has(x) && loc.state().bike.pos.x >= x) ticksAtX.set(x, tick);
  loc.step(frames[tick]!);
  if (ticksAtX.size === 3) break;
}
const rows = [];
for (const withExit of [false, true]) {
  S1.obstacles = original.slice();
  if (!withExit) S1.obstacles.splice(exitIndex, 1);
  for (const v of vars) {
    const start = ticksAtX.get(v.x) ?? -1;
    const sim = await createSim(S1.id, rec.header.seed, 120, { bike: 'pro' });
    let firstFaultX: number | null = null;
    for (let tick = 0; tick < frames.length; tick++) {
      const src = frames[tick]!;
      const changed = start >= 0 && tick >= start && tick < start + v.ticks;
      const input = changed ? quantizeInput({ ...src, throttle: v.throttle, brake: 0, lean: v.lean }) : src;
      const faults = sim.faults();
      sim.step(input);
      if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
      if (sim.phase() === 'finished') break;
    }
    const route = sim.rules.counters().diamondRouteCrossed === true;
    const row = { withExit, variation: v.name, phase: sim.phase(), faults: sim.faults(), firstFaultX,
      route, seconds: sim.runTime(), x: sim.state().bike.pos.x, recoveries: [] as unknown[] };
    if (sim.phase() !== 'finished' && sim.faults() === 0 && route) {
      const snapshot = sim.snap();
      for (const policy of ['gas-neutral', 'gas-back', 'gas-front', 'angle-balance'] as const) {
        sim.restore(snapshot);
        let recoveryFaultX: number | null = null;
        for (let tick = 0; tick < 1200 && sim.phase() !== 'finished'; tick++) {
          const lean = policy === 'gas-back' ? -0.2 : policy === 'gas-front' ? 0.2 :
            policy === 'angle-balance' ? Math.max(-0.4, Math.min(0.4, -sim.state().bike.angle * 0.4)) : 0;
          const faults = sim.faults();
          sim.step(quantizeInput({ throttle: 1, lean }));
          if (recoveryFaultX === null && sim.faults() > faults) recoveryFaultX = sim.state().bike.pos.x;
          if (recoveryFaultX !== null) break;
        }
        row.recoveries.push({ policy, phase: sim.phase(), faults: sim.faults(), firstFaultX: recoveryFaultX,
          seconds: sim.runTime(), x: sim.state().bike.pos.x });
      }
    }
    rows.push(row);
  }
}
S1.obstacles = original;
fs.mkdirSync('docs/evidence/s1-lift-bridge', { recursive: true });
fs.writeFileSync('docs/evidence/s1-lift-bridge/robustness.json', `${JSON.stringify(rows, null, 2)}\n`);
for (const withExit of [false, true]) {
  const subset = rows.filter((r) => r.withExit === withExit);
  const complete = subset.filter((r) => r.phase === 'finished' && r.faults === 0 && r.route);
  const recoveries = subset.flatMap((r) => r.recoveries as { phase: string; faults: number }[])
    .filter((r) => r.phase === 'finished' && r.faults === 0);
  console.log(`exit=${withExit}: ${complete.length}/${subset.length} clean fixed finishes; ${recoveries.length} clean continuation recoveries`);
}
