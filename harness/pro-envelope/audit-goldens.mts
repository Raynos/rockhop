/** Record which checked-in bike references still finish on current physics. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { ROCKHOP_TRACK_DEFS } from '../../src/tracks/rockhop';
import { createSimFor } from '../lib/sim';

const rows = [];
for (const track of ROCKHOP_TRACK_DEFS) for (const bike of ['rookie', 'pro'] as const) {
  const path = `harness/inputs/${track.id}/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
  if (!fs.existsSync(path)) { rows.push({ track: track.id, bike, path, missing: true }); continue; }
  const rec = decodeJSON(fs.readFileSync(path, 'utf8'));
  const sim = await createSimFor(rec);
  sim.run(expandFrames(rec));
  rows.push({ track: track.id, bike, path, phase: sim.phase(), faults: sim.faults(),
    runTime: sim.runTime(), hash: sim.hash(), routeProof: sim.rules.counters().diamondRouteCrossed });
}
console.log(JSON.stringify(rows, null, 2));
