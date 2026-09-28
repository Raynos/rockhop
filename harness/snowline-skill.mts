/** Bounded Snowline skill-3 search, writing only this lane's evidence. */
import fs from 'node:fs';
import { createSim } from './lib/sim';
import { recordingHeader } from './lib/recording';
import { InputRecorder, encodeJSON, expandFrames } from '../src/core/replay';
import { configFor, playTrack } from './bot/play';
import { DEFAULT_WEIGHTS } from './bot/score';

const track = process.argv[2] ?? 's1-lift-line';
const bike = process.argv[3] === 'pro' ? 'pro' : 'rookie';
const budgetMs = Number(process.argv[4] ?? 750);
const wallMs = Number(process.argv[5] ?? 120000);
const outDir = 'docs/evidence/snowline-retarget';
fs.mkdirSync(outDir, { recursive: true });
const sim = await createSim(track, undefined, 120, { bike });
const started = performance.now();
const result = playTrack(sim, {
  skill: 3,
  config: configFor(3, budgetMs),
  weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 30, maxSimSeconds: 180, maxWallMs: wallMs },
});
const recorder = new InputRecorder(recordingHeader(sim, `snowline retarget skill=3 ${bike}`));
for (const frame of result.frames) recorder.push(frame);
const recording = recorder.toRecording();
const replay = await createSim(track, sim.seed, 120, { bike });
replay.run(expandFrames(recording));
const row = {
  track, bike, budgetMs, wallMs, wallActualMs: Math.round(performance.now() - started),
  outcome: result.outcome, attempts: result.attempts, faults: result.faults.length,
  finishS: result.finishTime, maxX: result.maxX, finishX: sim.track.finishX,
  ticks: result.frames.length, nodeHash: sim.hash(), replayHash: replay.hash(),
  replayPhase: replay.phase(), replayFinishS: replay.phase() === 'finished' ? replay.runTime() : null,
  exact: result.outcome === 'finished' && replay.phase() === 'finished' && result.finishTime === replay.runTime(),
  diamond: replay.rules.counters().diamondRouteCrossed,
};
const stem = `${track}-${bike}-skill3`;
fs.writeFileSync(`${outDir}/${stem}.json`, JSON.stringify(row, null, 2));
if (result.outcome === 'finished') fs.writeFileSync(`${outDir}/${stem}.rec.json`, encodeJSON(recording));
process.stdout.write(`${JSON.stringify(row, null, 2)}\n`);
