/** Current-source passive-clear gate: 12 courses x 2 bikes x 3 seeds x 600 s. */
import { quantizeInput } from '../../src/core/replay';
import { ROCKHOP_TRACK_DEFS } from '../../src/tracks/rockhop';
import { createSim } from '../lib/sim';

const held = quantizeInput({ throttle: 1 });
let finishes = 0;
for (const track of ROCKHOP_TRACK_DEFS) {
  for (const seed of [track.seed, 1, 2]) {
    for (const bike of ['rookie', 'pro'] as const) {
      const sim = await createSim(track.id, seed, 120, { bike });
      let maxX = sim.state().bike.pos.x;
      for (let tick = 0; tick < 600 * sim.hz && sim.phase() !== 'finished'; tick++) {
        sim.step(held);
        maxX = Math.max(maxX, sim.state().bike.pos.x);
      }
      const finished = sim.phase() === 'finished';
      if (finished) finishes++;
      console.log(JSON.stringify({ id: track.id, seed, bike, phase: sim.phase(), maxX: Number(maxX.toFixed(2)),
        faults: sim.faults(), finishTime: sim.state().finishTime }));
    }
  }
}
if (finishes) process.exitCode = 1;
