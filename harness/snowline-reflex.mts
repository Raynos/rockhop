/** Bounded stranger-proxy ride of the three Snowline courses on both bikes. */
import fs from 'node:fs';
import { createSim } from './lib/sim';
import { playReflex } from './reflex/play';
import { expandFrames, InputRecorder } from '../src/core/replay';
import { recordingHeader } from './lib/recording';

const rows = [];
for (const track of ['s1-lift-line', 's2-cornice', 's3-whiteout']) {
  for (const bike of ['rookie', 'pro'] as const) {
    for (const seed of [7, 19]) {
      const sim = await createSim(track, seed, 120, { bike });
      const result = playReflex(sim, { skill: 'average', seed, attemptsCap: 30, maxSimSeconds: 300 });
      const recorder = new InputRecorder(recordingHeader(sim, `snowline reflex ${bike} seed ${seed}`));
      for (const frame of result.frames) recorder.push(frame);
      const replay = await createSim(track, seed, 120, { bike });
      replay.run(expandFrames(recorder.toRecording()));
      const restartLatencies = [];
      for (let i = 0; i < result.events.length; i++) {
        const fault = result.events[i];
        if (fault?.event.type !== 'fault') continue;
        const restart = result.events.slice(i + 1).find((e) => e.event.type === 'restart');
        if (restart) restartLatencies.push((restart.runTick - fault.runTick) / 120);
      }
      rows.push({
        track, bike, seed, outcome: result.outcome, attempts: result.attempts,
        faults: result.faults.length, faultXs: result.faults.map((f) => Number(f.x.toFixed(2))),
        finishS: result.finishTime, maxX: result.maxX, ticks: result.frames.length,
        restartLatenciesS: restartLatencies,
        hash: sim.hash(), replayHash: replay.hash(), exact: sim.hash() === replay.hash(),
      });
      process.stdout.write(`${track} ${bike} seed=${seed} ${result.outcome} attempts=${result.attempts} finish=${result.finishTime ?? '-'}\n`);
    }
  }
}
fs.mkdirSync('docs/evidence/snowline-retarget', { recursive: true });
fs.writeFileSync('docs/evidence/snowline-retarget/reflex.json', JSON.stringify(rows, null, 2));
