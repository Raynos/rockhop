/** Matched full-course input sweep around the three snowline Diamond shelves. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import type { BikeClass, InputFrame } from '../../src/core/types';
import { createSim } from '../lib/sim';

const courses = [
  { id: 's1-lift-line', approachX: 277 },
  { id: 's2-cornice', approachX: 149 },
  { id: 's3-whiteout', approachX: 133 },
] as const;
const bikes: BikeClass[] = ['rookie', 'pro'];
const variants = ['base', 'coast12', 'brake12', 'forward24', 'leanBack24', 'leanFront24'] as const;
type Variant = typeof variants[number];

function mutate(frame: InputFrame, variant: Variant): InputFrame {
  switch (variant) {
    case 'coast12': return quantizeInput({ ...frame, throttle: 0, brake: 0 });
    case 'brake12': return quantizeInput({ ...frame, throttle: 0, brake: 0.25 });
    case 'forward24': return quantizeInput({ ...frame, throttle: 1, brake: 0, lean: 0 });
    case 'leanBack24': return quantizeInput({ ...frame, throttle: 1, brake: 0, lean: -0.5 });
    case 'leanFront24': return quantizeInput({ ...frame, throttle: 1, brake: 0, lean: 0.5 });
    default: return frame;
  }
}

const rows = [];
for (const { id, approachX } of courses) {
  for (const sourceBike of bikes) {
    const recording = decodeJSON(fs.readFileSync(`harness/inputs/${id}/bot-3${sourceBike === 'pro' ? '-pro' : ''}.json`, 'utf8'));
    const frames = expandFrames(recording);
    const locator = await createSim(id, recording.header.seed, 120, { bike: sourceBike });
    let approachTick = -1;
    for (let tick = 0; tick < frames.length && locator.phase() !== 'finished'; tick++) {
      if (locator.state().bike.pos.x >= approachX) { approachTick = tick; break; }
      locator.step(frames[tick]!);
    }
    if (approachTick < 0) throw new Error(`${id} ${sourceBike}: pinned input never approaches Diamond shelf`);
    for (const variant of variants) {
      const duration = variant.endsWith('24') ? 24 : 12;
      const scripted = variant === 'base' ? frames : frames.map((frame, tick) =>
        tick >= approachTick && tick < approachTick + duration ? mutate(frame, variant) : frame);
      for (const bike of bikes) {
        const sim = await createSim(id, recording.header.seed, 120, { bike });
        let maxX = sim.state().bike.pos.x;
        let firstFaultX: number | null = null;
        for (const frame of scripted) {
          const previousFaults = sim.faults();
          sim.step(frame);
          maxX = Math.max(maxX, sim.state().bike.pos.x);
          if (firstFaultX === null && sim.faults() > previousFaults) firstFaultX = sim.state().bike.pos.x;
          if (sim.phase() === 'finished') break;
        }
        const route = sim.rules.counters().diamondRouteCrossed === true;
        rows.push({ id, sourceBike, bike, variant, approachTick, inputTicks: scripted.length,
          phase: sim.phase(), faults: sim.faults(), firstFaultX, maxX,
          seconds: sim.runTime(), route, medal: sim.phase() === 'finished'
            ? medalFor(sim.runTime(), sim.faults(), sim.track.meta?.targetTimeS, bike, route) : null,
          hash: sim.hash() });
      }
    }
  }
}
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/sweep.json', `${JSON.stringify(rows, null, 2)}\n`);
for (const id of courses.map(c => c.id)) {
  const selected = rows.filter(row => row.id === id).map(({ sourceBike, bike, variant, phase, faults, route, seconds, firstFaultX }) =>
    ({ sourceBike, bike, variant, phase, faults, route, seconds: +seconds.toFixed(3), firstFaultX }));
  console.log(id, JSON.stringify(selected));
}
