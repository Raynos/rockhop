/** Bounded S1 exit experiment. Mutates the local track definition only during this process. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { S1 } from '../../src/tracks/rockhop/snowline';
import { createSim } from '../lib/sim';

const originals = S1.obstacles.slice();
const exitIndex = originals.findIndex((o) => o.kind === 'plank' && o.pos.x === 298 && o.params?.angleDeg === -15);
const recordings = (['rookie', 'pro'] as const).map((bike) => ({
  bike,
  rec: decodeJSON(fs.readFileSync(`harness/inputs/s1-lift-line/bot-3${bike === 'pro' ? '-pro' : ''}.json`, 'utf8')),
}));

const candidates = [
  { label: 'without-exit', start: 0, length: 0, angleDeg: 0 },
  ...[298, 299, 300].flatMap((start) => [-10, -15, -20].map((angleDeg) => ({
    label: `exit-${start}-${Math.abs(angleDeg)}`, start, length: 8, angleDeg,
  }))),
];
const rows = [];
for (const candidate of candidates) {
  S1.obstacles = originals.slice();
  if (exitIndex >= 0) S1.obstacles.splice(exitIndex, 1);
  if (candidate.length) {
    // One-way snow ramp: starts on or beyond the optional upper shelf and ends above the lower piste.
    S1.obstacles.push({ kind: 'plank', pos: { x: candidate.start, y: 0 }, params: {
      length: candidate.length, height: 4.6 + (candidate.start - 298) * Math.tan(candidate.angleDeg * Math.PI / 180),
      angleDeg: candidate.angleDeg, thickness: 0.18, oneWay: true, surface: 'snow',
    } });
  }
  for (const { bike, rec } of recordings) {
    const frames = expandFrames(rec);
    const sim = await createSim(S1.id, rec.header.seed, 120, { bike });
    let firstFaultX: number | null = null;
    let maxX = 0;
    const trace = [];
    const traceAt = [284, 288, 292, 296, 298, 300, 302, 306, 310, 315];
    let nextTrace = 0;
    for (const frame of frames) {
      const faults = sim.faults();
      sim.step(frame);
      const state = sim.state();
      maxX = Math.max(maxX, state.bike.pos.x);
      if (firstFaultX === null && sim.faults() > faults) firstFaultX = state.bike.pos.x;
      if (nextTrace < traceAt.length && state.bike.pos.x >= traceAt[nextTrace]!) {
        trace.push({ x: traceAt[nextTrace], actualX: state.bike.pos.x, y: state.bike.pos.y,
          angle: state.bike.angle, faultCount: sim.faults(), tick: sim.totalTicks() });
        nextTrace++;
      }
      if (sim.phase() === 'finished') break;
    }
    const route = sim.rules.counters().diamondRouteCrossed === true;
    rows.push({ candidate: candidate.label, bike, phase: sim.phase(), faults: sim.faults(), firstFaultX, maxX,
      seconds: sim.runTime(), route, medal: sim.phase() === 'finished'
        ? medalFor(sim.runTime(), sim.faults(), S1.meta?.targetTimeS, bike, route) : null,
      hash: sim.hash(), trace });
  }
}
S1.obstacles = originals;
fs.mkdirSync('docs/evidence/s1-lift-bridge', { recursive: true });
fs.writeFileSync('docs/evidence/s1-lift-bridge/exit-sweep.json', `${JSON.stringify(rows, null, 2)}\n`);
for (const row of rows) console.log(`${row.candidate} ${row.bike}: ${row.phase} faults=${row.faults} first=${row.firstFaultX} ${row.seconds.toFixed(3)}s ${row.medal}`);
