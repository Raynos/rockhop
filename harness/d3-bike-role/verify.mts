/** Exact full-course D3 role regression and passive GO check after the longer high deck. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { D3 } from '../../src/tracks/rockhop/quarry';
import { createQuarrySim } from '../quarry-sim';

const inputPath = (bike: 'rookie' | 'pro') => `harness/inputs/d3-rope-walk/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
const runs = [];
for (const bike of ['rookie', 'pro'] as const) {
  const recording = decodeJSON(fs.readFileSync(inputPath(bike), 'utf8'));
  const samples = [];
  for (let n = 0; n < 2; n++) {
    const sim = await createQuarrySim(D3.id, recording.header.seed, 120, bike);
    sim.run(expandFrames(recording));
    const route = sim.rules.counters().diamondRouteCrossed === true;
    samples.push({ phase: sim.phase(), faults: sim.faults(), ticks: sim.runTicks(), seconds: sim.runTime(),
      route, medal: medalFor(sim.runTime(), sim.faults(), D3.meta?.targetTimeS, bike, route), hash: sim.hash() });
  }
  if (JSON.stringify(samples[0]) !== JSON.stringify(samples[1])) throw new Error(`${bike} diverged across fresh worlds`);
  if (samples[0]?.phase !== 'finished' || samples[0].faults !== 0 || samples[0].route !== (bike === 'pro')) {
    throw new Error(`${bike} pinned clear regressed: ${JSON.stringify(samples[0])}`);
  }
  runs.push({ bike, ...samples[0], freshWorldIdentical: true });
}

const passive = [];
const go = quantizeInput({ throttle: 1 });
for (const bike of ['rookie', 'pro'] as const) for (const seed of [D3.seed, 1, 2]) {
  const sim = await createQuarrySim(D3.id, seed, 120, bike);
  let maxX = sim.state().bike.pos.x;
  const firstFaults = [];
  for (let tick = 0; tick < 600 * 120 && sim.phase() !== 'finished'; tick++) {
    for (const event of sim.step(go)) {
      if (event.type === 'fault' && firstFaults.length < 3) firstFaults.push({ tick: tick + 1, x: sim.state().bike.pos.x, reason: event.reason });
    }
    maxX = Math.max(maxX, sim.state().bike.pos.x);
  }
  passive.push({ bike, seed, phase: sim.phase(), faults: sim.faults(), maxX, firstFaults, hash: sim.hash() });
  if (sim.phase() === 'finished') throw new Error(`held GO cleared ${bike} seed ${seed}`);
}

const report = { deck: { x: D3.obstacles[D3.diamondGoal!.platformObstacleIndex]!.pos.x,
    length: D3.obstacles[D3.diamondGoal!.platformObstacleIndex]!.params?.['length'],
    height: D3.obstacles[D3.diamondGoal!.platformObstacleIndex]!.params?.['height'] },
  runs, passive };
fs.writeFileSync('docs/evidence/d3-bike-role/verify.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ runs, passive: passive.map(({ bike, seed, phase, faults, maxX }) => ({ bike, seed, phase, faults, maxX })) }, null, 2));
