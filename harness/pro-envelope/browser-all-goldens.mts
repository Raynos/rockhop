/** Verify all 12 shipping Pro goldens against source and two fresh production-browser contexts each. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { ROCKHOP_TRACK_DEFS } from '../../src/tracks/rockhop';
import { BrowserVerifier } from '../lib/verify';
import { createSimFor } from '../lib/sim';

const verifier = new BrowserVerifier();
let failures = 0;
try {
  for (const track of ROCKHOP_TRACK_DEFS) {
    const file = `harness/inputs/${track.id}/bot-3-pro.json`;
    const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    const expected = { phase: sim.phase(), faults: sim.faults(), finishTime: sim.state().finishTime, hash: sim.hash(), tick: sim.state().tick };
    if (expected.phase !== 'finished' || expected.faults !== 0) failures++;
    for (let load = 1; load <= 2; load++) {
      const browser = await verifier.run(rec);
      const pass = expected.phase === 'finished' && expected.faults === 0 && browser.faults === 0
        && browser.finishTime === expected.finishTime && browser.hash === expected.hash && browser.state.tick === expected.tick;
      if (!pass) failures++;
      console.log(JSON.stringify({ track: track.id, load, pass, source: expected,
        browser: { faults: browser.faults, finishTime: browser.finishTime, hash: browser.hash, tick: browser.state.tick, wallMs: browser.wallMs } }));
    }
  }
} finally {
  await verifier.close();
}
if (failures) process.exitCode = 1;
