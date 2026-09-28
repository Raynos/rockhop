/** Long continuous-GO probe for both bikes on the isolated C2 candidate. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
const rows = [];
for (const bike of ['rookie', 'pro'] as const) for (let k = 0; k < 3; k++) {
  const seed = (C2_CHALLENGE.seed + k) >>> 0;
  const sim = await createSim(C2_CHALLENGE.id, seed, 120, { bike });
  let firstFault: unknown = null;
  let firstCraneFault: unknown = null;
  let faultEvents = 0;
  let maxX = 0;
  let finishTick: number | null = null;
  for (let tick = 0; tick < 600 * sim.hz; tick++) {
    const before = sim.state();
    const x = before.bike.pos.x;
    for (const event of sim.step(GO)) {
      if (event.type === 'fault') {
        const fault = { tick: tick + 1, x: +x.toFixed(2), checkpoint: before.checkpoint, reason: event.reason };
        firstFault ??= fault;
        if (x > 280) firstCraneFault ??= fault;
        faultEvents++;
      }
      if (event.type === 'finish') finishTick = tick + 1;
    }
    maxX = Math.max(maxX, x);
    if (finishTick !== null) break;
  }
  const row = { bike, seed, finishTick, clear: finishTick !== null, faults: sim.faults(), faultEvents, firstFault, firstCraneFault, maxX: +maxX.toFixed(2), finishX: C2_CHALLENGE.finishX, hash: sim.hash() };
  rows.push(row);
  process.stdout.write(`${bike} seed+${k}: ${row.clear ? `CLEAR ${finishTick}` : 'STUCK'} maxX=${row.maxX} faults=${faultEvents} crane=${JSON.stringify(firstCraneFault)}\n`);
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/go-probe.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
