/** Re-run the four final Pro upper-route input recordings on the current source. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';

const files = ['d3', 's1', 's2', 's3'].map((id) => `docs/evidence/course-remaster/pro-envelope/${id}-pro-upper.replay.json`);
let failures = 0;
for (const file of files) {
  const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
  const sim = await createSimFor(rec);
  sim.run(expandFrames(rec));
  const row = { file, track: rec.header.trackId, bike: sim.bike, phase: sim.phase(), faults: sim.faults(),
    timeS: sim.runTime(), hash: sim.hash(), routeProof: sim.rules.counters().diamondRouteCrossed === true };
  console.log(JSON.stringify(row));
  if (row.phase !== 'finished' || row.faults !== 0 || !row.routeProof) failures++;
}
if (failures) process.exitCode = 1;
