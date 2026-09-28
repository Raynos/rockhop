/** Record the selected bounded D3 bridge approaches and verify exact fresh Node replays. */
import fs from 'node:fs';
import path from 'node:path';
import { InputRecorder, decodeJSON, encodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import type { BikeClass } from '../../src/core/types';
import { medalFor } from '../../src/game/rules';
import { recordingHeader } from '../lib/recording';
import { createQuarrySim } from '../quarry-sim';

const out = path.resolve('docs/evidence/d3-diamond-route');
fs.mkdirSync(out, { recursive: true });
type Plan = { preLean: number; preThrottle: number; launchLean: number; launchThrottle: number; landLean: number; landThrottle: number; time: number };
type Search = { upperClears: Plan[]; lowerClears: Plan[]; proofCount: number; finishCount: number };
const reports = [];
for (const bike of ['rookie', 'pro'] as BikeClass[]) {
  const source = decodeJSON(fs.readFileSync(`docs/evidence/quarry-retarget/d3-rope-walk-${bike}-bot.json`, 'utf8'));
  const search = JSON.parse(fs.readFileSync(path.join(out, `${bike}-search-3p5.json`), 'utf8')) as Search;
  for (const route of ['lower', 'upper'] as const) {
    const plan = (route === 'upper' ? search.upperClears : search.lowerClears)[0];
    if (!plan) continue;
    const sim = await createQuarrySim('d3-rope-walk', source.header.seed, 120, bike);
    const recorder = new InputRecorder(recordingHeader(sim, `D3 ${bike} ${route}: bounded three-window bridge approach`));
    for (const frame of expandFrames(source)) {
      if (sim.state().bike.pos.x >= 380) break;
      recorder.push(frame);
      sim.step(frame);
    }
    if (sim.faults()) throw new Error(`${bike} prefix faulted`);
    for (let tick = 0; tick < 1600 && sim.phase() !== 'finished'; tick++) {
      const x = sim.state().bike.pos.x;
      const frame = quantizeInput({ throttle: x < 385.7 ? plan.preThrottle : x < 391 ? plan.launchThrottle : x < 428 ? plan.landThrottle : 1,
        brake: 0, lean: x < 385.7 ? plan.preLean : x < 391 ? plan.launchLean : x < 428 ? plan.landLean : 0 });
      recorder.push(frame);
      sim.step(frame);
      if (sim.faults()) break;
    }
    const proof = sim.rules.counters().diamondRouteCrossed === true;
    const rec = recorder.toRecording();
    rec.header.routeProof = { goalId: 'd3-high-bridge', crossed: proof };
    const fresh = await createQuarrySim('d3-rope-walk', source.header.seed, 120, bike);
    fresh.run(expandFrames(rec));
    const report = { bike, route, plan, phase: sim.phase(), faults: sim.faults(), ticks: sim.runTicks(), time: sim.runTime(),
      proof, medal: medalFor(sim.runTime(), sim.faults(), sim.track.meta?.targetTimeS, bike, proof),
      hash: sim.hash(), replayHash: fresh.hash(), replayProof: fresh.rules.counters().diamondRouteCrossed === true };
    if (sim.phase() !== 'finished' || sim.faults() !== 0 || proof !== (route === 'upper') || fresh.hash() !== sim.hash())
      throw new Error(`D3 ${bike} ${route} failed: ${JSON.stringify(report)}`);
    fs.writeFileSync(path.join(out, `${bike}-${route}.json`), `${encodeJSON(rec)}\n`);
    reports.push(report);
  }
  // The earlier clean bot is a separate lower-line regression, not a fitted search plan.
  const old = await createQuarrySim('d3-rope-walk', source.header.seed, 120, bike);
  old.run(expandFrames(source));
  reports.push({ bike, route: 'old-bot', phase: old.phase(), faults: old.faults(), ticks: old.runTicks(), time: old.runTime(),
    proof: old.rules.counters().diamondRouteCrossed === true, hash: old.hash() });
}
fs.writeFileSync(path.join(out, 'node-verify.json'), `${JSON.stringify(reports, null, 2)}\n`);
console.log(JSON.stringify(reports, null, 2));
