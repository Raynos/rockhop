/** Replay the existing Snowline skill-3 recordings on the current source. */
import fs from 'node:fs';
import { loadRecording } from './lib/recording';
import { createSim, createSimFor } from './lib/sim';
import { expandFrames } from '../src/core/replay';

const rows = [];
for (const track of ['s1-lift-line', 's2-cornice', 's3-whiteout']) {
  for (const bike of ['rookie', 'pro'] as const) {
    const file = `harness/inputs/${track}/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
    const source = fs.existsSync(file) ? file : `harness/inputs/${track}/bot-3.json`;
    const rec = loadRecording(source);
    const sim = fs.existsSync(file) ? await createSimFor(rec) : await createSim(track, rec.header.seed, rec.header.physicsHz, { bike });
    const frames = expandFrames(rec);
    sim.run(frames);
    const replay = fs.existsSync(file) ? await createSimFor(rec) : await createSim(track, rec.header.seed, rec.header.physicsHz, { bike });
    replay.run(frames);
    rows.push({ track, bike, file: source, borrowedInputs: source !== file, phase: sim.phase(), finishS: sim.phase() === 'finished' ? sim.runTime() : null, faults: sim.faults(), maxX: sim.state().bike.pos.x, diamond: sim.rules.counters().diamondRouteCrossed, hash: sim.hash(), replayHash: replay.hash(), exact: sim.hash() === replay.hash(), ticks: frames.length });
  }
}
fs.mkdirSync('docs/evidence/snowline-retarget', { recursive: true });
fs.writeFileSync('docs/evidence/snowline-retarget/existing-goldens.json', JSON.stringify(rows, null, 2));
process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
