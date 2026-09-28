/** Isolate the crane action while correcting the unrelated early pier on Pro. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { quantizeInput } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const variants = [
  { name: 'GO neutral', throttle: 1, brake: 0, lean: 0 },
  { name: 'release only', throttle: 0, brake: 0, lean: 0 },
  { name: 'forward only', throttle: 1, brake: 0, lean: 0.5 },
  { name: 'release and forward', throttle: 0, brake: 0, lean: 0.5 },
  { name: 'brake and forward', throttle: 0, brake: 1, lean: 0.5 },
] as const;
const rows = [];
for (const bike of ['rookie', 'pro'] as const) for (const variant of variants) {
  const sim = await createSim(C2_CHALLENGE.id, C2_CHALLENGE.seed, 120, { bike });
  let finished = false;
  let firstCraneFault: unknown = null;
  let maxX = 0;
  for (let tick = 0; tick < 90 * 120; tick++) {
    const x = sim.state().bike.pos.x;
    const pier = x >= 120 && x < 140;
    const crane = x >= 308 && x < 322;
    const action = pier ? { throttle: 0, brake: 0, lean: 1 } : crane ? variant : { throttle: 1, brake: 0, lean: 0 };
    const frame = quantizeInput(action);
    for (const event of sim.step(frame)) {
      if (event.type === 'fault' && x > 280) firstCraneFault ??= { tick: tick + 1, x: +x.toFixed(2) };
      if (event.type === 'finish') finished = true;
    }
    maxX = Math.max(maxX, x);
    if (finished) break;
  }
  const row = { bike, variant: variant.name, finished, finishTick: finished ? sim.runTicks() : null, faults: sim.faults(), firstCraneFault, maxX: +maxX.toFixed(2), hash: sim.hash() };
  rows.push(row);
  process.stdout.write(`${bike} ${variant.name}: ${finished ? 'CLEAR' : 'FAIL'} faults=${row.faults} maxX=${row.maxX}\n`);
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/ablation.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
