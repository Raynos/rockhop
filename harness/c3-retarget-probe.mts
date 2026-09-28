/** Read-only baseline for the C3 course challenge round. */
import { readFileSync } from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../src/core/replay';
import { createSim } from './lib/sim';

const id = 'c3-hull-breach';
const golden = decodeJSON(readFileSync(`harness/inputs/${id}/bot-3.json`, 'utf8'));
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  const held = await createSim(id, undefined, 120, { bike });
  const faults: { tick: number; x: number; reason: string }[] = [];
  const go = quantizeInput({ throttle: 1 });
  for (let tick = 0; tick < 120 * 600 && held.phase() !== 'finished'; tick++) {
    const events = held.step(go);
    for (const event of events) if (event.type === 'fault' && faults.length < 40) {
      faults.push({ tick, x: held.state().bike.pos.x, reason: event.reason });
    }
  }
  const row: Record<string, unknown> = {
    bike, held: { phase: held.phase(), time: held.runTime(), x: held.state().bike.pos.x,
      faults: held.faults(), sampledFaults: faults, hash: held.hash() },
  };
  if (bike === 'rookie') {
    const sim = await createSim(id, golden.header.seed, golden.header.physicsHz, { bike });
    const crossings: { tick: number; x: number }[] = [];
    const faults: { tick: number; x: number }[] = [];
    let lastX = sim.state().bike.pos.x;
    let tick = 0;
    for (const frame of expandFrames(golden)) {
      const events = sim.step(frame);
      const x = sim.state().bike.pos.x;
      if (lastX < 275 && x >= 275) crossings.push({ tick, x });
      for (const event of events) if (event.type === 'fault') faults.push({ tick, x });
      lastX = x;
      tick++;
    }
    row.golden = { phase: sim.phase(), time: sim.runTime(), faults: sim.faults(), hash: sim.hash(), crossings, faultSites: faults };
  }
  rows.push(row);
}
process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
