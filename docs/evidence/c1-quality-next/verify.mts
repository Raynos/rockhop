/** C1 art-only change: exact fresh Node/browser clears on both bikes, plus a long held-GO rejection. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../../src/core/replay';
import { srcFingerprint } from '../../../harness/lib/metrics';
import { BrowserVerifier } from '../../../harness/lib/verify';
import { createSim } from '../../../harness/lib/sim';

const report: {
  sourceFingerprint: string;
  clears: object[];
  heldGo: object[];
} = { sourceFingerprint: srcFingerprint(), clears: [], heldGo: [] };

const browser = new BrowserVerifier({ dev: true });
try {
  for (const bike of ['rookie', 'pro'] as const) {
    const file = `harness/inputs/c1-low-tide/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
    const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
    const sim = await createSim('c1-low-tide', rec.header.seed, rec.header.physicsHz, { bike });
    sim.run(expandFrames(rec));
    const page = await browser.run(rec);
    // Compare the frozen state value on both sides. `runTime()` is a separately rounded
    // presentation clock (30.35 here); the saved finishTime is the replay invariant.
    const node = { phase: sim.phase(), faults: sim.faults(), finishTime: sim.state().finishTime, hash: sim.hash() };
    const web = { phase: page.state.finished ? 'finished' : 'riding', faults: page.faults, finishTime: page.finishTime, hash: page.hash };
    if (node.phase !== 'finished' || node.faults !== 0 || JSON.stringify(node) !== JSON.stringify(web)) {
      throw new Error(`${bike}: browser replay differs from Node: ${JSON.stringify({ node, web })}`);
    }
    report.clears.push({ bike, recording: file, node, web, exact: true });
  }
} finally { await browser.close(); }

const held = quantizeInput({ throttle: 1 });
for (const bike of ['rookie', 'pro'] as const) for (const seed of [341352973, 1, 2]) {
  const sim = await createSim('c1-low-tide', seed, 120, { bike });
  let firstFaultX: number | null = null;
  for (let t = 0; t < 600 * 120 && sim.phase() !== 'finished'; t++) {
    const n = sim.faults();
    sim.step(held);
    if (firstFaultX === null && sim.faults() > n) firstFaultX = sim.state().bike.pos.x;
  }
  if (sim.phase() === 'finished') throw new Error(`${bike}/${seed}: held GO cleared C1`);
  report.heldGo.push({ bike, seed, phase: sim.phase(), faults: sim.faults(), firstFaultX });
}
fs.writeFileSync('docs/evidence/c1-quality-next/verify.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(`C1 exact ${report.clears.length}/${report.clears.length}; held GO 0/${report.heldGo.length}`);
