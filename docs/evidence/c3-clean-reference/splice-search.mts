/* Replan only the C3 breach from a fault-free prefix of the pinned Rookie ride.
   The resulting candidate always replays from GO as one complete recording. */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames } from '../../../src/core/replay';
import { configFor, playTrack } from '../../../harness/bot/play';
import { recordingFromFrames } from '../../../harness/bot/bot';
import { createSimFor } from '../../../harness/lib/sim';
import { loadRecording, saveRecording } from '../../../harness/lib/recording';

const dir = path.resolve('docs/evidence/c3-clean-reference');
const base = loadRecording('harness/inputs/c3-hull-breach/bot-3.json');
const prefixTicks = 2300;
const prefix = [...expandFrames(base)].slice(0, prefixTicks);
const sim = await createSimFor(base);
const prefixEvents = sim.run(prefix).events;
if (sim.phase() !== 'riding' || sim.faults() !== 0 || prefixEvents.some(event => event.type === 'fault')) {
  throw new Error('Pinned prefix is not a fault-free riding state');
}
const prefixState = { x: sim.state().bike.pos.x, hash: sim.hash(), runTime: sim.runTime() };
const started = performance.now();
const result = playTrack(sim, {
  skill: 'oracle',
  config: { ...configFor('oracle', 30_000), budgetTicks: 100_000 },
  limits: { maxWallMs: 180_000, maxSimSeconds: 90, maxRewinds: 100 },
});
const recording = recordingFromFrames(sim, [...prefix, ...result.frames], 'C3 zero-fault Rookie splice candidate');
const fresh = await createSimFor(recording);
const encoded = [...expandFrames(recording)];
const replay = fresh.run(encoded);
const faultEvents = replay.events.filter(event => event.type === 'fault').length;
const exact = replay.hash === sim.hash() && encoded.length === prefix.length + result.frames.length;
const clean = result.outcome === 'finished' && result.faults.length === 0 && result.attempts === 1
  && fresh.phase() === 'finished' && fresh.faults() === 0 && faultEvents === 0 && exact;
const report = {
  trackId: base.header.trackId, bike: 'rookie', seed: base.header.seed, physics: base.header.physics,
  prefix: { ticks: prefixTicks, ...prefixState },
  search: { skill: 'oracle', wallMs: Math.round(performance.now() - started), outcome: result.outcome,
    plans: result.plans.length, ticksSimulated: result.ticksSimulated, rewinds: result.rewinds,
    attempts: result.attempts, faultCount: result.faults.length, firstFault: result.faults[0] ?? null },
  replay: { clean, exact, ticks: encoded.length, phase: fresh.phase(), faults: fresh.faults(),
    faultEvents, finishTime: fresh.state().finishTime, hash: replay.hash },
};
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'splice-search-result.json'), JSON.stringify(report, null, 2) + '\n');
if (clean) saveRecording(path.join(dir, 'rookie-zero-fault.rec.json'), recording);
console.log(JSON.stringify(report));
