/** Grid search a compact, explainable C1 bow line; never modifies production. */
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { quantizeInput } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { C1_CHALLENGE } from './candidate';

registerTrack(C1_CHALLENGE);
const candidates = [];
for (const start of [192]) {
  for (const target of [8, 9, 10, 11, 12, 13, 14, 15, 16]) {
    for (const lean of [0, 0.5, 1]) {
      for (const after of [0]) {
        const results = [];
        for (const bike of ['rookie', 'pro'] as const) {
          const sim = await createSim(C1_CHALLENGE.id, C1_CHALLENGE.seed, 120, { bike });
          let finishTime = null;
          let firstFault = null;
          for (let tick = 0; tick < 90 * sim.hz; tick++) {
            const s = sim.state();
            const x = s.bike.pos.x;
            const v = s.bike.vel.x;
            let throttle = 1, brake = 0, l = 0;
            if (x >= start && x < 208) {
              if (v > target + 1) { throttle = 0; brake = 1; }
              else if (v > target) { throttle = 0; }
            }
            if (x >= 208 && x < 215) { throttle = 1; l = lean; }
            if (x >= 215 && x < 221) { throttle = 0; l = after; }
            const events = sim.step(quantizeInput({ throttle, brake, lean: l }));
            for (const e of events) {
              if (e.type === 'fault') firstFault ??= +s.bike.pos.x.toFixed(1);
              if (e.type === 'finish') finishTime = sim.runTime();
            }
            if (finishTime !== null) break;
          }
          results.push({ bike, finishTime, faults: sim.faults(), firstFault, medal: finishTime === null ? null : medalFor(finishTime, sim.faults(), C1_CHALLENGE.meta?.targetTimeS ?? 50, bike) });
        }
        candidates.push({ start, target, lean, after, results });
      }
    }
  }
}
candidates.sort((a, b) => (a.results[0]!.faults + a.results[1]!.faults) - (b.results[0]!.faults + b.results[1]!.faults) || (a.results[0]!.finishTime! + a.results[1]!.finishTime!) - (b.results[0]!.finishTime! + b.results[1]!.finishTime!));
import {writeFileSync} from 'node:fs'; writeFileSync(new URL('../../docs/evidence/c1-challenge/control-envelope.json', import.meta.url), JSON.stringify(candidates,null,2)+'\n'); process.stdout.write(candidates.map(c=>`${c.target} ${c.lean} ${c.results.map(r=>r.finishTime===null?'X':r.faults).join('/')}`).join('\n')+'\n');
