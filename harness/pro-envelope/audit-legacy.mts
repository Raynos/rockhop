/** Read-only audit of every v2 harness bot-3 fixture the historical R7/R8 tests load. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';

const inputDir = 'harness/inputs';
const removed = new Set(['p-coast', 'p-alpine', 'p-quarry', 'p-snowline']);
const rows = [];
for (const dir of fs.readdirSync(inputDir, { withFileTypes: true })) {
  if (!dir.isDirectory() || removed.has(dir.name)) continue;
  for (const name of ['bot-3.json', 'bot-3-pro.json']) {
    const file = path.join(inputDir, dir.name, name);
    if (!fs.existsSync(file)) continue;
    const recording = decodeJSON(fs.readFileSync(file, 'utf8'));
    if (recording.header.physics === 'v1') continue;
    const sim = await createSimFor(recording);
    sim.run(expandFrames(recording));
    rows.push({ file, track: dir.name, bike: recording.header.bike ?? 'rookie', phase: sim.phase(),
      faults: sim.faults(), timeS: sim.runTime(), hash: sim.hash() });
  }
}
console.log(JSON.stringify(rows, null, 2));
