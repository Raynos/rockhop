/** Exact real-track lower/upper proof, live browser replay, and held-GO exclusion. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, encodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { decodeSnapshot } from '../../src/game/hook';
import { createSim } from '../lib/sim';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';

const outDir = path.resolve('docs/evidence/s2-wind-shelf');
fs.mkdirSync(outDir, { recursive: true });
const upperFile = path.join(outDir, 's2-pro-upper.rec.json');
const upper = decodeJSON(fs.readFileSync(upperFile, 'utf8'));
const lower = decodeJSON(fs.readFileSync('harness/inputs/s2-cornice/bot-3.json', 'utf8'));
const cases = [
  { name: 'rookie-lower', bike: 'rookie' as const, rec: lower, expectedProof: false, expectedMedal: 'gold' },
  { name: 'pro-upper', bike: 'pro' as const, rec: upper, expectedProof: true, expectedMedal: 'platinum' },
];
const rows = [];
const server = await startServer({ dev: true });
const launched = await launchBrowser({ width: 852, height: 392 });
try {
  for (const c of cases) {
    const node = await createSim('s2-cornice', c.rec.header.seed, c.rec.header.physicsHz, { bike: c.bike });
    node.run(expandFrames(c.rec));
    const proof = node.rules.counters().diamondRouteCrossed === true;
    const medal = medalFor(node.runTime(), node.faults(), node.track.meta?.targetTimeS, c.bike, proof);
    const browserRuns = [];
    for (let i = 0; i < 2; i++) {
      const page = await launched.context.newPage();
      try {
        await openGame(page, server.url);
        const hook = new HookClient(page);
        const run = await hook.runRecording(encodeJSON(c.rec));
        const snap = decodeSnapshot(await page.evaluate(() => window.__rockhop!.snapshot()));
        browserRuns.push({ hash: run.hash, finishS: run.state.finishTime, proof: snap.counters?.diamondRouteCrossed === true,
          phase: snap.counters?.phase, faults: snap.counters?.faults });
      } finally { await page.close(); }
    }
    const row = { name: c.name, bike: c.bike, source: c.name === 'pro-upper' ? upperFile : 'harness/inputs/s2-cornice/bot-3.json',
      node: { phase: node.phase(), finishS: node.runTime(), faults: node.faults(), hash: node.hash(), proof, medal }, browserRuns };
    rows.push(row);
    if (node.phase() !== 'finished' || node.faults() !== 0 || proof !== c.expectedProof || medal !== c.expectedMedal ||
      browserRuns.some(b => b.hash !== node.hash() || b.finishS !== node.runTime() || b.proof !== proof || b.phase !== 'finished' || b.faults !== 0)) {
      throw new Error(`${c.name}: ${JSON.stringify(row)}`);
    }
  }
} finally {
  await launched.close();
  await server.close();
}
const seededReplays = [];
for (const c of cases) for (const seed of [1, 2]) {
  const sim = await createSim('s2-cornice', seed, c.rec.header.physicsHz, { bike: c.bike });
  sim.run(expandFrames(c.rec));
  const proof = sim.rules.counters().diamondRouteCrossed === true;
  const medal = medalFor(sim.runTime(), sim.faults(), sim.track.meta?.targetTimeS, c.bike, proof);
  const row = { name: c.name, seed, phase: sim.phase(), faults: sim.faults(), finishS: sim.runTime(), proof, medal, hash: sim.hash() };
  seededReplays.push(row);
  if (sim.phase() !== 'finished' || sim.faults() !== 0 || proof !== c.expectedProof || medal !== c.expectedMedal) {
    throw new Error(`seeded replay failed: ${JSON.stringify(row)}`);
  }
}
const heldGo = [];
for (const bike of ['rookie', 'pro'] as const) for (const seed of [undefined, 1, 2]) {
  const sim = await createSim('s2-cornice', seed, 120, { bike });
  const go = quantizeInput({ throttle: 1 });
  for (let tick = 0; tick < 600 * 120 && sim.phase() !== 'finished'; tick++) sim.step(go);
  const row = { bike, seed: sim.seed, phase: sim.phase(), faults: sim.faults(), proof: sim.rules.counters().diamondRouteCrossed === true };
  heldGo.push(row);
  if (sim.phase() === 'finished') throw new Error(`held GO cleared: ${JSON.stringify(row)}`);
}
const report = { rows, seededReplays, heldGo };
fs.writeFileSync(path.join(outDir, 'verify.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));
