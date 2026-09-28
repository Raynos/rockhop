/** Search lower, legible teeter-bridge dimensions against constant GO on both bikes. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { makeTilt } from './candidate-tilt';

const rows = [];
for (const length of [5, 6, 7, 8, 10]) for (const ratio of [0.18, 0.22, 0.25]) for (const runup of [16, 30, 45]) {
  const height = Math.round(length * ratio * 100) / 100;
  const id = `c1-tilt-${length}-${Math.round(ratio * 100)}-${runup}`;
  let track;
  try { track = makeTilt(id, length, height, runup); }
  catch (error) { rows.push({ length, height, runup, error: (error as Error).message }); continue; }
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
  const row = { length, height, runup, results };
  rows.push(row);
  if (results.every((r) => !r.clear)) process.stdout.write(`BOTH STUCK L${length} h${height} runup${runup} ${results.map((r) => `${r.bike}:${r.maxPct}%/${r.faults}`).join(' ')}\n`);
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/tilt-sweep.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
