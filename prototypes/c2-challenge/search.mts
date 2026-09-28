/** Search simple release / pitch windows at the crane hop, keeping the rest of C2 intact. */
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { makeCandidate } from './candidate';

const track = makeCandidate(18, 1.8);
registerTrack(track);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  const sim = await createSim(track.id, track.seed, 120, { bike });
  for (const from of [292, 296, 300, 304, 308]) {
    for (const to of [310, 316, 322, 328, 334]) {
      if (to <= from) continue;
      for (const lean of [-1, -0.5, 0, 0.5, 1]) {
        sim.reload();
        let finished = false;
        let maxX = 0;
        let faultAtHop = 0;
        for (let tick = 0; tick < 70 * 120; tick++) {
          const state = sim.state();
          const x = state.bike.pos.x;
          const inWindow = x >= from && x < to;
          const input = { throttle: inWindow ? 0 : 1, brake: 0, lean: inWindow ? lean : 0, hop: false, restart: false };
          const events = sim.step(input);
          maxX = Math.max(maxX, x);
          if (events.some(e => e.type === 'fault') && x > 280) faultAtHop++;
          if (events.some(e => e.type === 'finish')) { finished = true; break; }
        }
        rows.push({ bike, from, to, lean, finished, time: sim.runTime(), faults: sim.faults(), faultAtHop, maxX: +maxX.toFixed(1) });
      }
    }
  }
}
rows.sort((a,b) => Number(b.finished)-Number(a.finished) || a.faultAtHop-b.faultAtHop || b.maxX-a.maxX || a.time-b.time);
for (const row of rows.slice(0, 25)) process.stdout.write(`${JSON.stringify(row)}\n`);
