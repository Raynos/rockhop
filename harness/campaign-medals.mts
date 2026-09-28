/** Replay the committed skill-3 campaign references against the actual medal rule. */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames } from '../src/core/replay';
import type { BikeClass } from '../src/core/types';
import { medalFor, targetForBike } from '../src/game/rules';
import { ROCKHOP_TRACKS } from '../src/tracks/rockhop';
import { loadRecording } from './lib/recording';
import { srcFingerprint } from './lib/metrics';
import { createSimFor } from './lib/sim';

interface Row {
  course: string;
  bike: BikeClass;
  targetS: number;
  diamondS: number;
  reference: string | null;
  clearS: number | null;
  faults: number | null;
  medal: string | null;
  diamondRouteCrossed: boolean | null;
  hash: string | null;
}

const rows: Row[] = [];
for (const entry of ROCKHOP_TRACKS) {
  for (const bike of ['rookie', 'pro'] as const) {
    const target = targetForBike(entry.def.meta?.targetTimeS, bike);
    if (target === null) throw new Error(`${entry.id}: no medal target`);
    const file = path.join('harness', 'inputs', entry.id, `bot-3${bike === 'pro' ? '-pro' : ''}.json`);
    const row: Row = {
      course: entry.id, bike, targetS: target, diamondS: +(target * 0.85).toFixed(3),
      reference: fs.existsSync(file) ? file : null, clearS: null, faults: null, medal: null,
      diamondRouteCrossed: null, hash: null,
    };
    if (row.reference) {
      const rec = loadRecording(file);
      if (rec.header.trackId !== entry.id || (rec.header.bike ?? 'rookie') !== bike) throw new Error(`${file}: wrong course/bike`);
      const sim = await createSimFor(rec);
      const played = sim.run(expandFrames(rec));
      if (sim.phase() !== 'finished') throw new Error(`${file}: reference does not finish`);
      const crossed = entry.def.diamondGoal ? sim.rules.counters().diamondRouteCrossed === true : null;
      row.clearS = +sim.runTime().toFixed(3);
      row.faults = sim.faults();
      row.medal = medalFor(sim.runTime(), sim.faults(), entry.def.meta?.targetTimeS, bike, crossed ?? undefined);
      row.diamondRouteCrossed = crossed;
      row.hash = played.hash;
    }
    rows.push(row);
  }
}

const count = (bike: BikeClass, medal: string): number => rows.filter((r) => r.bike === bike && r.medal === medal).length;
const report = {
  schema: 1,
  srcFingerprint: srcFingerprint(),
  note: 'Bot skill-3 references only; neither a human difficulty curve nor the fastest possible routes.',
  references: rows.filter((r) => r.reference).length,
  missing: rows.filter((r) => !r.reference).map((r) => `${r.course}:${r.bike}`),
  medals: Object.fromEntries((['rookie', 'pro'] as const).map((bike) => [bike, Object.fromEntries(['bronze', 'silver', 'gold', 'platinum'].map((medal) => [medal, count(bike, medal)]))])),
  rows,
};
const output = process.argv[2];
if (output) {
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
}
console.log(JSON.stringify(report, null, 2));
