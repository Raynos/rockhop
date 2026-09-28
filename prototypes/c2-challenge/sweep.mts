/** Scan visible crane kicker dimensions with the shipped v2 solver. */
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { makeCandidate } from './candidate';

const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
for (const [angle, rise] of [[14, 1.5], [18, 1.8], [20, 2], [22, 2.2], [24, 2.4], [26, 2.6], [28, 2.8], [30, 3]] as const) {
  let track;
  try {
    track = makeCandidate(angle, rise, 5.5, `c2-challenge-${angle}`);
  } catch (error) {
    process.stdout.write(`${angle}/${rise} INVALID ${String(error).split('\n')[0]}\n`);
    continue;
  }
  registerTrack(track);
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(track.id, track.seed, 120, { bike });
    let firstFault: unknown = null;
    let maxX = 0;
    let finished = false;
    for (let tick = 0; tick < 90 * 120; tick++) {
      const before = sim.state();
      const events = sim.step(GO);
      maxX = Math.max(maxX, before.bike.pos.x);
      for (const event of events) {
        if (event.type === 'fault') firstFault ??= { x: +before.bike.pos.x.toFixed(1), t: +sim.runTime().toFixed(2), checkpoint: before.checkpoint };
        if (event.type === 'finish') finished = true;
      }
      if (finished) break;
    }
    process.stdout.write(`${angle}/${rise} ${bike} ${finished ? 'CLEAR' : 'FAIL'} t=${sim.runTime().toFixed(2)} faults=${sim.faults()} first=${JSON.stringify(firstFault)} maxX=${maxX.toFixed(1)}\n`);
  }
}
