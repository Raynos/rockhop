/** Isolate whether the bow asks for braking, forward lean, or both. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { quantizeInput } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { makeSlope } from './candidate-slope';
const C1_CHALLENGE = makeSlope('c1-low-tide', 28, 2.8);

registerTrack(C1_CHALLENGE);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  for (const brakeBow of [false, true]) {
    for (const leanBow of [false, true]) {
      const sim = await createSim(C1_CHALLENGE.id, C1_CHALLENGE.seed, 120, { bike });
      let finishTime = null;
      let firstFault = null;
      let maxX = 0;
      for (let tick = 0; tick < 600 * sim.hz; tick++) {
        const s = sim.state();
        const x = s.bike.pos.x, v = s.bike.vel.x;
        maxX = Math.max(maxX, x);
        let throttle = 1, brake = 0, lean = 0;
        if (brakeBow && x >= 192 && x < 208) {
          if (v > 15) { throttle = 0; brake = 1; }
          else if (v > 14) throttle = 0;
        }
        if (x >= 208 && x < 215) { throttle = 1; if (leanBow) lean = 1; }
        if (brakeBow && x >= 215 && x < 221) throttle = 0;
        for (const e of sim.step(quantizeInput({ throttle, brake, lean }))) {
          if (e.type === 'fault') firstFault ??= { x: +s.bike.pos.x.toFixed(2), time: sim.runTime(), checkpoint: s.checkpoint };
          if (e.type === 'finish') finishTime = sim.runTime();
        }
        if (finishTime !== null) break;
      }
      const row = { bike, brakeBow, leanBow, finishTime, faults: sim.faults(), firstFault, maxX: +maxX.toFixed(2), maxPct: +(100 * maxX / C1_CHALLENGE.finishX).toFixed(1) };
      rows.push(row);
      process.stdout.write(`${bike} brake=${brakeBow} lean=${leanBow} ${finishTime === null ? `STUCK ${row.maxPct}%` : `CLEAR ${finishTime.toFixed(3)}s`} faults=${row.faults}\n`);
    }
  }
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/ablation-slope28.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
