/** Search lower, legible teeter-bridge dimensions against constant GO on both bikes. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { makeSlope } from './candidate-slope';

const rows = [];
for (const angleDeg of [28, 30, 32, 34, 36, 38, 40]) for (const rise of [1.6, 2.2, 2.8, 3.2]) {
  const id = `c1-slope-${angleDeg}-${Math.round(rise*10)}`;
  let track;
  try { track = makeSlope(id, angleDeg, rise); }
  catch (error) { rows.push({ angleDeg, rise, error: (error as Error).message }); continue; }
  registerTrack(track);
  const results = [];
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(id, track.seed, 120, { bike });
    let finishTime = null, firstFault = null, maxX = 0;
    for (let tick = 0; tick < 600 * sim.hz; tick++) {
      const s = sim.state();
      maxX = Math.max(maxX, s.bike.pos.x);
      for (const event of sim.step({ throttle: 1, brake: 0, lean: 0, hop: false, restart: false })) {
        if (event.type === 'fault') firstFault ??= { x: +s.bike.pos.x.toFixed(2), checkpoint: s.checkpoint };
        if (event.type === 'finish') finishTime = sim.runTime();
      }
      if (finishTime !== null) break;
    }
    results.push({ bike, clear: finishTime !== null, finishTime, faults: sim.faults(), firstFault, maxPct: +(100 * maxX / track.finishX).toFixed(1) });
  }
  const row = { angleDeg, rise, results };
  rows.push(row);
  if (results.every((r) => !r.clear)) process.stdout.write(`BOTH STUCK angle${angleDeg} rise${rise} ${results.map((r) => `${r.bike}:${r.maxPct}%/${r.faults}`).join(' ')}\n`);
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/slope-sweep.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
