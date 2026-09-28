/** Simulates the standalone candidate with the shipped compiler, physics and run rules. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { medalFor } from '../../src/game/rules';
import { registerTrack } from '../../src/tracks';
import { C1_CHALLENGE } from './candidate';

registerTrack(C1_CHALLENGE);
const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  for (const seed of [C1_CHALLENGE.seed, C1_CHALLENGE.seed + 1, C1_CHALLENGE.seed + 2]) {
    const sim = await createSim(C1_CHALLENGE.id, seed, 120, { bike });
    let firstFault = null;
    let faultEvents = 0;
    let maxX = 0;
    let finishTime = null;
    for (let tick = 0; tick < 600 * sim.hz; tick++) {
      const events = sim.step(GO);
      const state = sim.state();
      maxX = Math.max(maxX, state.bike.pos.x);
      for (const event of events) {
        if (event.type === 'fault') {
          faultEvents++;
          firstFault ??= { x: +state.bike.pos.x.toFixed(2), time: +sim.runTime().toFixed(2), checkpoint: state.checkpoint, reason: event.reason };
        }
        if (event.type === 'finish') finishTime = sim.runTime();
      }
      if (finishTime !== null) break;
    }
    const row = {
      bike, seed, clear: finishTime !== null, finishTime,
      medal: finishTime === null ? null : medalFor(finishTime, sim.faults(), C1_CHALLENGE.meta?.targetTimeS ?? 50, bike),
      faults: sim.faults(), faultEvents, firstFault,
      maxX: +maxX.toFixed(2), maxPct: +(100 * maxX / C1_CHALLENGE.finishX).toFixed(1),
      checkpoints: C1_CHALLENGE.checkpoints.map((c) => +c.x.toFixed(2)),
      finishX: C1_CHALLENGE.finishX,
      hash: sim.hash(),
    };
    rows.push(row);
    process.stdout.write(`${bike} seed=${seed} ${row.clear ? `CLEAR ${finishTime?.toFixed(3)} ${row.medal}` : `STUCK ${row.maxPct}%`} faults=${faultEvents} first=${JSON.stringify(firstFault)}\n`);
  }
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/go-probe.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
