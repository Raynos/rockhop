/** Finish a clean S3 upper-deck partial recording with committed controls. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { playTrack, configFor } from '../bot/play';
import { DEFAULT_WEIGHTS } from '../bot/score';

const index = Number(process.argv[2] ?? 10);
const skill = process.argv[3] === 'oracle' ? 'oracle' : 3;
const dir = '/tmp/rockhop-pro-envelope-audit';
const rec = decodeJSON(fs.readFileSync(`${dir}/s3-upper-post-${index}.replay.json`, 'utf8'));
const sim = await createSimFor(rec);
const prefix = expandFrames(rec);
for (const frame of prefix) sim.step(frame);
if (sim.phase() !== 'riding' || sim.faults() || sim.rules.counters().diamondRouteCrossed !== true || sim.state().bike.pos.x < 180) throw Error('invalid upper route partial');
const start = { x: sim.state().bike.pos.x, t: sim.runTime(), hash: sim.hash() };
const result = playTrack(sim, { skill, config: { ...configFor(3), budgetTicks: 900_000 }, weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 10, maxRewinds: 100, maxSimSeconds: 600, maxWallMs: 240_000 } });
const report = { index, skill, start, outcome: result.outcome, faults: result.faults.map((f) => ({ x: f.x, reason: f.reason })),
  attempts: result.attempts, finishTime: result.finishTime, routeProof: sim.rules.counters().diamondRouteCrossed,
  finalHash: sim.hash(), wallMs: result.wallMs, simTicks: sim.totalTicks(), rewinds: result.rewinds };
fs.writeFileSync(`${dir}/s3-upper-post-${index}-${skill}-finish.json`, `${JSON.stringify(report, null, 2)}\n`);
if (result.outcome === 'finished') {
  const full = new InputRecorder({ ...rec.header, note: `Pro S3 upper deck continuation ${index}/${skill}` });
  for (const frame of [...prefix, ...result.frames]) full.push(frame);
  fs.writeFileSync(`${dir}/s3-upper-post-${index}-${skill}-finish.replay.json`, encodeJSON(full.toRecording()));
}
console.log(JSON.stringify(report));
