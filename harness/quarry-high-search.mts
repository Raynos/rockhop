/** Bounded input sweep from the real D3 bridge approach; tests the optional upper deck and lower exit. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../src/core/replay';
import type { BikeClass, InputFrame } from '../src/core/types';
import { createQuarrySim } from './quarry-sim';

const bike: BikeClass = process.argv[2] === 'pro' ? 'pro' : 'rookie';
const rec = decodeJSON(fs.readFileSync(`docs/evidence/quarry-retarget/d3-rope-walk-${bike}-bot.json`, 'utf8'));
const prefixSim = await createQuarrySim('d3-rope-walk', rec.header.seed, 120, bike);
const prefix: InputFrame[] = [];
for (const frame of expandFrames(rec)) {
  if (prefixSim.state().bike.pos.x >= 380) break;
  prefixSim.step(frame);
  prefix.push(frame);
}
if (prefixSim.phase() !== 'riding' || prefixSim.faults()) throw new Error('old bot prefix does not reach the final bridge cleanly');
const snapshot = prefixSim.snap();
const prefixX = prefixSim.state().bike.pos.x;
const sim = prefixSim;
const leans = [-1, -0.5, 0, 0.5, 1];
const throttles = [0, 0.5, 1];
const results = [];
for (const preLean of leans) for (const preThrottle of throttles)
  for (const launchLean of leans) for (const launchThrottle of throttles)
    for (const landLean of [-0.5, 0, 0.5, 1]) for (const landThrottle of [0, 1]) {
      sim.restore(snapshot);
      let fault = false;
      let maxX = sim.state().bike.pos.x;
      let maxY = sim.state().bike.pos.y;
      let atGoal: { rearY: number; rearGrounded: boolean; rearContact: string | null } | null = null;
      for (let tick = 0; tick < 1600 && sim.phase() !== 'finished'; tick++) {
        const x = sim.state().bike.pos.x;
        const frame = quantizeInput({ throttle: x < 385.7 ? preThrottle : x < 391 ? launchThrottle : x < 428 ? landThrottle : 1,
          brake: 0, lean: x < 385.7 ? preLean : x < 391 ? launchLean : x < 428 ? landLean : 0 });
        if (sim.step(frame).some((e) => e.type === 'fault')) { fault = true; break; }
        maxX = Math.max(maxX, sim.state().bike.pos.x);
        maxY = Math.max(maxY, sim.state().bike.pos.y);
        const state = sim.state();
        if (!atGoal && state.wheels.rear.pos.x >= 404) atGoal = {
          rearY: state.wheels.rear.pos.y, rearGrounded: state.wheels.rear.grounded, rearContact: state.contacts.rear };
      }
      const proof = sim.rules.counters().diamondRouteCrossed === true;
      if (sim.phase() === 'finished' || proof || maxX > 420) results.push({ preLean, preThrottle, launchLean, launchThrottle,
        landLean, landThrottle, phase: sim.phase(), proof, fault, maxX, maxY, atGoal, time: sim.runTime(), hash: sim.hash() });
    }
results.sort((a, b) => Number(b.phase === 'finished' && b.proof) - Number(a.phase === 'finished' && a.proof)
  || Number(b.proof) - Number(a.proof) || Number(b.phase === 'finished') - Number(a.phase === 'finished') || b.maxX - a.maxX);
console.log(JSON.stringify({ bike, prefixTicks: prefix.length, prefixX, candidates: results.length,
  proofCount: results.filter((r) => r.proof).length, finishCount: results.filter((r) => r.phase === 'finished').length,
  upperClears: results.filter((r) => r.proof && r.phase === 'finished').sort((a, b) => a.time - b.time).slice(0, 20),
  lowerClears: results.filter((r) => !r.proof && r.phase === 'finished').sort((a, b) => a.time - b.time).slice(0, 20),
  closest: [...results].filter((r) => r.atGoal).sort((a, b) =>
    Math.abs(a.atGoal!.rearY - 3.34) - Math.abs(b.atGoal!.rearY - 3.34)).slice(0, 15) }, null, 2));
