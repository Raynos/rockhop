/* Search a zero-fault Rookie C3 reference without touching pinned inputs.
   Usage: pnpm exec tsx docs/evidence/c3-clean-reference/search.mts */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames } from '../../../src/core/replay';
import { configFor, playTrack } from '../../../harness/bot/play';
import { recordingFromFrames } from '../../../harness/bot/bot';
import { createSim, createSimFor } from '../../../harness/lib/sim';
import { saveRecording } from '../../../harness/lib/recording';

const dir = path.resolve('docs/evidence/c3-clean-reference');
const trackId = 'c3-hull-breach';
const sim = await createSim(trackId, undefined, undefined, { bike: 'rookie' });
const started = performance.now();
const result = playTrack(sim, {
  skill: 'oracle',
  config: { ...configFor('oracle', 30_000), budgetTicks: 100_000 },
  limits: { maxWallMs: 180_000, maxSimSeconds: 90, maxRewinds: 100 },
});
const recording = recordingFromFrames(sim, result.frames, 'C3 zero-fault Rookie oracle candidate');
const replay = await createSimFor(recording);
let divergence: { tick: number; playHash: string; replayHash: string } | null = null;
for (let i = 0; i < result.frames.length; i++) {
  replay.step(result.frames[i]!);
  if (!divergence && replay.hash() !== result.hashes[i]) {
    divergence = { tick: i + 1, playHash: result.hashes[i]!, replayHash: replay.hash() };
  }
}
const expanded = [...expandFrames(recording)];
const fresh = await createSimFor(recording);
const fromEncoded = fresh.run(expanded);
const replayFaultEvents = fromEncoded.events.filter(event => event.type === 'fault').length;
const clean = result.outcome === 'finished' && result.faults.length === 0 && result.attempts === 1
  && replay.faults() === 0 && fresh.faults() === 0 && replayFaultEvents === 0 && !divergence
  && replay.hash() === fromEncoded.hash && result.frames.length === expanded.length;
const report = {
  trackId, bike: 'rookie', seed: sim.seed, physics: sim.physicsName,
  search: { skill: 'oracle', wallMs: Math.round(performance.now() - started), outcome: result.outcome,
    plans: result.plans.length, ticksSimulated: result.ticksSimulated, rewinds: result.rewinds,
    attempts: result.attempts, faultCount: result.faults.length, firstFault: result.faults[0] ?? null },
  replay: { clean, divergence, ticks: expanded.length, phase: fresh.phase(), faults: fresh.faults(),
    faultEvents: replayFaultEvents,
    finishTime: fresh.state().finishTime, hash: fromEncoded.hash },
};
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'search-result.json'), JSON.stringify(report, null, 2) + '\n');
if (clean) saveRecording(path.join(dir, 'rookie-zero-fault.rec.json'), recording);
console.log(JSON.stringify(report));
