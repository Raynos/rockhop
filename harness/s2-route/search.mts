/** Reproduce the clean S2 Pro upper-line input: measured first jump, then oracle suffix. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder } from '../../src/core/replay';
import { createSim } from '../lib/sim';
import { recordingHeader } from '../lib/recording';
import { configFor, playTrack } from '../bot/play';
import { DEFAULT_WEIGHTS } from '../bot/score';

const budgetMs = Number(process.argv[2] ?? 700);
const wallMs = Number(process.argv[3] ?? 90000);
const outDir = path.resolve('docs/evidence/s2-wind-shelf');
fs.mkdirSync(outDir, { recursive: true });
const source = decodeJSON(fs.readFileSync('docs/evidence/snowline-retarget/s2-cornice-pro-skill3.rec.json', 'utf8'));
const sim = await createSim('s2-cornice', source.header.seed, source.header.physicsHz, { bike: 'pro' });
const prefix = [];
for (const frame of expandFrames(source)) {
  if (sim.rules.counters().diamondRouteCrossed === true && sim.state().bike.pos.x >= 166) break;
  sim.step(frame);
  prefix.push(frame);
  if (sim.faults()) throw new Error('Pro approach faulted before the wind shelf');
}
if (sim.rules.counters().diamondRouteCrossed !== true) throw new Error('Pro approach did not prove the upper route');
const result = playTrack(sim, { skill: 'oracle', config: configFor('oracle', budgetMs), weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 20, maxRewinds: 200, maxSimSeconds: 100, maxWallMs: wallMs } });
const recorder = new InputRecorder(recordingHeader(sim, 'S2 Pro wind-shelf upper line'));
for (const frame of [...prefix, ...result.frames]) recorder.push(frame);
const recording = recorder.toRecording();
recording.header.routeProof = { goalId: 's2-wind-shelf', crossed: sim.rules.counters().diamondRouteCrossed === true };
const fresh = await createSim('s2-cornice', source.header.seed, source.header.physicsHz, { bike: 'pro' });
fresh.run(expandFrames(recording));
const row = { budgetMs, wallMs, prefixTicks: prefix.length, outcome: result.outcome, faults: sim.faults(),
  proof: sim.rules.counters().diamondRouteCrossed, finishTimeS: result.finishTime, phase: sim.phase(), maxX: result.maxX,
  wallActualMs: result.wallMs, rewinds: result.rewinds, hash: sim.hash(), replayHash: fresh.hash(), replayFaults: fresh.faults(),
  replayProof: fresh.rules.counters().diamondRouteCrossed, replayFinishS: fresh.phase() === 'finished' ? fresh.runTime() : null };
if (result.outcome !== 'finished' || sim.faults() !== 0 || fresh.hash() !== sim.hash() || row.proof !== true) {
  throw new Error(`S2 upper search failed: ${JSON.stringify(row)}`);
}
fs.writeFileSync(path.join(outDir, 'search.json'), `${JSON.stringify(row, null, 2)}\n`);
fs.writeFileSync(path.join(outDir, 's2-pro-upper.rec.json'), `${encodeJSON(recording)}\n`);
console.log(JSON.stringify(row, null, 2));
