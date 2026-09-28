/** Campaign-wide passive-input gate on the current registered tracks. */
import fs from 'node:fs';
import { quantizeInput } from '../src/core/replay';
import { ROCKHOP_TRACKS } from '../src/tracks/rockhop';
import { srcFingerprint } from './lib/metrics';
import { createSim } from './lib/sim';

const hz = 120;
const limitS = Number(process.argv[2] ?? 600);
const seedCount = Math.max(1, Number(process.argv[3] ?? 1));
const go = quantizeInput({ throttle: 1 });
const rows = [];

for (const track of ROCKHOP_TRACKS) {
  for (const bike of ['rookie', 'pro'] as const) {
    for (let seedIndex = 0; seedIndex < seedCount; seedIndex++) {
      const sim = await createSim(track.def.id, seedIndex === 0 ? undefined : seedIndex, hz, { bike });
      let maxX = sim.state().bike.pos.x;
      const firstFaults: { tick: number; x: number; reason: string }[] = [];
      let ticks = 0;
      for (; ticks < limitS * hz && sim.phase() !== 'finished'; ticks++) {
        for (const event of sim.step(go)) {
          if (event.type === 'fault' && firstFaults.length < 5) {
            firstFaults.push({ tick: ticks + 1, x: +sim.state().bike.pos.x.toFixed(3), reason: event.reason });
          }
        }
        maxX = Math.max(maxX, sim.state().bike.pos.x);
      }
      rows.push({
        code: track.code, id: track.def.id, bike, seed: sim.seed, phase: sim.phase(),
        simSeconds: +(ticks / hz).toFixed(3), faults: sim.faults(),
        maxX: +maxX.toFixed(3), finishX: +sim.track.finishX.toFixed(3), firstFaults,
        hash: sim.hash(),
      });
    }
  }
}

const out = { sourceFingerprint: srcFingerprint(), limitS, seedCount, rows, passiveClears: rows.filter((row) => row.phase === 'finished').map(({ code, bike, seed }) => `${code}:${bike}:${seed}`) };
fs.mkdirSync('docs/evidence/campaign-retarget', { recursive: true });
fs.writeFileSync('docs/evidence/campaign-retarget/held-go.json', JSON.stringify(out, null, 2));
process.stdout.write(`${JSON.stringify({ sourceFingerprint: out.sourceFingerprint, limitS, seedCount, courses: ROCKHOP_TRACKS.length, runs: rows.length, passiveClears: out.passiveClears }, null, 2)}\n`);
