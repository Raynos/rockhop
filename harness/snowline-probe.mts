/** Snowline held-GO baseline and deterministic replay probe. */
import fs from 'node:fs';
import { createSim } from './lib/sim';
import { quantizeInput, InputRecorder, expandFrames, encodeJSON } from '../src/core/replay';

const outDir = 'docs/evidence/snowline-retarget';
fs.mkdirSync(outDir, { recursive: true });
const rows = [];
for (const track of ['s1-lift-line', 's2-cornice', 's3-whiteout']) {
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(track, undefined, 120, { bike });
    const record = new InputRecorder({ version: 1, trackId: track, seed: sim.seed, physicsHz: 120, bike, physics: 'v2' });
    const go = quantizeInput({ throttle: 1 });
    let firstFault = null;
    const faultXs = [];
    let maxX = sim.state().bike.pos.x;
    let ticks = 0;
    for (let tick = 0; tick < 120 * 120 && sim.phase() !== 'finished'; tick++) {
      ticks++;
      record.push(go);
      sim.step(go);
      maxX = Math.max(maxX, sim.state().bike.pos.x);
      if (sim.faults() > faultXs.length) {
        const fault = { tick: tick + 1, x: sim.state().bike.pos.x, timeS: (tick + 1) / 120 };
        faultXs.push(fault);
        if (firstFault === null) firstFault = fault;
      }
    }
    const replay = await createSim(track, sim.seed, 120, { bike });
    const recording = record.toRecording();
    replay.run(expandFrames(recording));
    fs.writeFileSync(`${outDir}/${track}-${bike}-held-go.rec.json`, encodeJSON(recording));
    const row = { track, bike, finishX: sim.track.finishX, checkpoints: sim.track.checkpoints, maxX, firstFault, faultXs, faults: sim.faults(), phase: sim.phase(), runTimeS: sim.runTime(), hash: sim.hash(), replayHash: replay.hash(), exact: sim.hash() === replay.hash(), ticks };
    rows.push(row);
  }
}
fs.writeFileSync(`${outDir}/held-go.json`, JSON.stringify(rows, null, 2));
process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
