/** Isolated Quarry search: writes only the Quarry retarget evidence directory. */
import fs from 'node:fs';
import path from 'node:path';
import { InputRecorder, encodeJSON, expandFrames } from '../src/core/replay';
import type { BikeClass } from '../src/core/types';
import { configFor, playTrack } from './bot/play';
import { DEFAULT_WEIGHTS } from './bot/score';
import { recordingHeader } from './lib/recording';
import { createQuarrySim } from './quarry-sim';

const id = process.argv[2] ?? 'd1-dust-devil';
const bike: BikeClass = process.argv[3] === 'pro' ? 'pro' : 'rookie';
const budgetMs = Number(process.argv[4] ?? 1000);
const seed = Number(process.argv[5] ?? 1);
const sim = await createQuarrySim(id, seed, 120, bike);
const result = playTrack(sim, { skill: 3, config: configFor(3, budgetMs), weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 16, maxSimSeconds: 180, maxWallMs: 150000 } });
const recorder = new InputRecorder(recordingHeader(sim, `quarry retarget bot-3 outcome=${result.outcome}`));
for (const f of result.frames) recorder.push(f);
const recording = recorder.toRecording();
const replay = await createQuarrySim(id, seed, 120, bike);
replay.run(expandFrames(recording));
const report = { id, bike, seed, outcome: result.outcome, attempts: result.attempts, faults: result.faults,
  finishTime: result.finishTime, maxX: result.maxX, wallMs: result.wallMs, ticks: result.frames.length,
  playHash: sim.hash(), replayHash: replay.hash(), replayPhase: replay.phase(), replayFaults: replay.faults() };
const dir = path.resolve('docs/evidence/quarry-retarget');
fs.mkdirSync(dir, { recursive: true });
const prefix = `${id}-${bike}-bot`;
fs.writeFileSync(path.join(dir, `${prefix}.json`), `${encodeJSON(recording)}\n`);
fs.writeFileSync(path.join(dir, `${prefix}-report.json`), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report));
