/** Continue a measured clean Snowline approach with the oracle, then replay its recording from GO. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder, quantizeInput } from '../../src/core/replay';
import { createSim, createSimFor } from '../lib/sim';
import { recordingHeader } from '../lib/recording';
import { configFor, playTrack } from '../bot/play';
import { DEFAULT_WEIGHTS } from '../bot/score';

const id = process.argv[2] === 'S3' ? 's3-whiteout' : 's1-lift-line';
const bike = process.argv[3] === 'rookie' ? 'rookie' : 'pro';
const splitX = Number(process.argv[4] ?? (id === 's1-lift-line' ? 315 : 160));
const budgetMs = Number(process.argv[5] ?? 700);
const wallMs = Number(process.argv[6] ?? 90000);
const launch = process.argv[7] === 'snowcat' || process.argv[7] === 'rookie-lower' || process.argv[7] === 's1-lower' ? process.argv[7] : 'source';
const file = id === 's3-whiteout' && bike === 'rookie' ? 'harness/inputs/s3-whiteout/bot-3.json' : `docs/evidence/snowline-retarget/${id}-${bike}-skill3.rec.json`;
const source = decodeJSON(fs.readFileSync(file, 'utf8'));
const sim = await createSimFor(source);
const prefix = [];
for (const frame of expandFrames(source)) {
  const x = sim.state().bike.pos.x;
  const applied = launch === 'snowcat' && x >= 125 && x < 132 ? quantizeInput({ throttle: 0, lean: 0.5 })
    : launch === 'rookie-lower' && x >= 125 && x < 152 ? quantizeInput({ throttle: 1, lean: 0 })
    : launch === 's1-lower' && x >= 260 && x < 295 ? quantizeInput({ throttle: 0, lean: 0 }) : frame;
  sim.step(applied); prefix.push(applied);
  if (sim.state().bike.pos.x >= splitX) break;
  if (sim.faults()) throw new Error(`${bike} faults before x=${splitX}`);
}
if (sim.faults()) throw new Error(`${bike} faults at split x=${splitX}`);
const prefixProof = sim.rules.counters().diamondRouteCrossed === true;
const result = playTrack(sim, { skill: 'oracle', config: configFor('oracle', budgetMs), weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 30, maxRewinds: 300, maxSimSeconds: 120, maxWallMs: wallMs } });
const recorder = new InputRecorder(recordingHeader(sim, `${id} ${bike} optional shelf`));
for (const frame of [...prefix, ...result.frames]) recorder.push(frame);
const recording = recorder.toRecording();
recording.header.routeProof = { goalId: sim.track.diamondGoal?.id ?? 'none', crossed: sim.rules.counters().diamondRouteCrossed === true };
const fresh = await createSim(id, source.header.seed, source.header.physicsHz, { bike });
fresh.run(expandFrames(recording));
const row = { id, bike, file, splitX, launch, budgetMs, wallMs, prefixTicks: prefix.length, prefixProof, outcome: result.outcome,
  phase: sim.phase(), faults: sim.faults(), proof: sim.rules.counters().diamondRouteCrossed === true,
  finishS: sim.phase() === 'finished' ? sim.runTime() : null, maxX: result.maxX, wallActualMs: result.wallMs,
  rewinds: result.rewinds, hash: sim.hash(), replayHash: fresh.hash(), replayPhase: fresh.phase(),
  replayFaults: fresh.faults(), replayProof: fresh.rules.counters().diamondRouteCrossed === true,
  replayFinishS: fresh.phase() === 'finished' ? fresh.runTime() : null };
const outDir = path.resolve('docs/evidence/snowline-diamond');
fs.mkdirSync(outDir,{recursive:true});
fs.writeFileSync(path.join(outDir,`${id}-${bike}-search.json`),`${JSON.stringify(row,null,2)}\n`);
if(row.phase === 'finished' && row.faults === 0 && row.replayHash === row.hash && row.replayPhase === 'finished')
  fs.writeFileSync(path.join(outDir,`${id}-${bike}.rec.json`),`${encodeJSON(recording)}\n`);
console.log(JSON.stringify(row,null,2));
if(row.phase !== 'finished' || row.faults !== 0 || row.replayHash !== row.hash || row.replayPhase !== 'finished')process.exitCode=1;
