/** Read-only old/new canonical1200 and Pro golden audit for the three pinned Pro entries. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { synthesizeRecording } from '../lib/synth';

const expected = JSON.parse(fs.readFileSync('harness/gate/expected.json', 'utf8')) as Record<string,
  { golden?: { hash: string; finishTime: number | null; ticks: number }; canonical1200?: { hash: string } }>;
for (const id of ['flat-test', 'b1-first-ride', 'c1-low-tide', 'c2-crane-hop', 'd3-rope-walk']) {
  const file = `harness/inputs/${id}/bot-3-pro.json`;
  const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
  const golden = await createSimFor(rec);
  golden.run(expandFrames(rec));
  const sim = await createSimFor(rec);
  const canon = synthesizeRecording({ trackId: rec.header.trackId, seed: rec.header.seed,
    physicsHz: rec.header.physicsHz, seconds: 1200 / rec.header.physicsHz, style: 'wiggle' });
  const hash = sim.run(expandFrames(canon)).hash;
  console.log(JSON.stringify({ key: `${id}:pro`, file, old: expected[`${id}:pro`],
    current: { golden: { phase: golden.phase(), faults: golden.faults(),
      finishTime: golden.phase() === 'finished' ? golden.runTime() : null, hash: golden.hash(),
      ticks: expandFrames(rec).length }, canonical1200: { hash } } }));
}
