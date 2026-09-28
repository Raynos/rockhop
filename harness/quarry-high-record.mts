/** Save exact clean upper and lower D3 inputs selected from the bounded sweep. */
import fs from 'node:fs';
import path from 'node:path';
import { InputRecorder, decodeJSON, encodeJSON, expandFrames, quantizeInput } from '../src/core/replay';
import type { BikeClass } from '../src/core/types';
import { medalFor } from '../src/game/rules';
import { recordingHeader } from './lib/recording';
import { createQuarrySim } from './quarry-sim';

const bike: BikeClass = process.argv[2] === 'pro' ? 'pro' : 'rookie';
const route = process.argv[3] === 'lower' ? 'lower' : 'upper';
const dir = path.resolve('docs/evidence/quarry-retarget');
const source = decodeJSON(fs.readFileSync(path.join(dir, `d3-rope-walk-${bike}-bot.json`), 'utf8'));
const search = (JSON.parse(fs.readFileSync(path.join(dir, 'd3-high-search-summary.json'), 'utf8')) as Record<string, {
  upperClears: Array<Record<string, number>>; lowerClears: Array<Record<string, number> & { atGoal: { rearY: number } }>;
}>)[bike]!;
const plan = route === 'upper' ? search.upperClears[0] : search.lowerClears.find((r) => r.atGoal.rearY < 2);
if (!plan) throw new Error(`no proven ${route} ${bike} plan`);
const sim = await createQuarrySim('d3-rope-walk', source.header.seed, 120, bike);
const recorder = new InputRecorder(recordingHeader(sim, `Quarry D3 ${route} route: pre/launch/landing three-window input`));
for (const frame of expandFrames(source)) {
  if (sim.state().bike.pos.x >= 380) break;
  recorder.push(frame);
  sim.step(frame);
}
if (sim.faults() !== 0) throw new Error('prefix faulted');
for (let tick = 0; tick < 1600 && sim.phase() !== 'finished'; tick++) {
  const x = sim.state().bike.pos.x;
  const frame = quantizeInput({ throttle: x < 385.7 ? plan.preThrottle! : x < 391 ? plan.launchThrottle! : x < 428 ? plan.landThrottle! : 1,
    brake: 0, lean: x < 385.7 ? plan.preLean! : x < 391 ? plan.launchLean! : x < 428 ? plan.landLean! : 0 });
  recorder.push(frame);
  sim.step(frame);
  if (sim.faults()) break;
}
const proof = sim.rules.counters().diamondRouteCrossed === true;
const rec = recorder.toRecording();
rec.header.routeProof = { goalId: 'd3-high-bridge', crossed: proof };
const fresh = await createQuarrySim('d3-rope-walk', source.header.seed, 120, bike);
fresh.run(expandFrames(rec));
const report = { bike, route, plan, phase: sim.phase(), faults: sim.faults(), tick: sim.runTicks(), time: sim.runTime(),
  proof, medal: medalFor(sim.runTime(), sim.faults(), sim.track.meta?.targetTimeS, bike, proof),
  hash: sim.hash(), replayHash: fresh.hash(), replayProof: fresh.rules.counters().diamondRouteCrossed === true };
if (sim.phase() !== 'finished' || sim.faults() !== 0 || proof !== (route === 'upper') || fresh.hash() !== sim.hash()) {
  throw new Error(`D3 ${route} ${bike} replay failed: ${JSON.stringify(report)}`);
}
const prefix = `d3-${bike}-${route}`;
fs.writeFileSync(path.join(dir, `${prefix}.json`), `${encodeJSON(rec)}\n`);
fs.writeFileSync(path.join(dir, `${prefix}-report.json`), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report));
