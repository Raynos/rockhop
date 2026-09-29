/** Exact current-source S1 replay on fresh Node and silent browser worlds, plus held-GO rejection. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { decodeSnapshot } from '../../src/game/hook';
import { medalFor } from '../../src/game/rules';
import { S1 } from '../../src/tracks/rockhop/snowline';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { srcFingerprint } from '../lib/metrics';
import { startServer } from '../lib/server';
import { createSim } from '../lib/sim';

const results = [];
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 393 });
try {
  for (const bike of ['rookie', 'pro'] as const) {
    const file = `harness/inputs/s1-lift-line/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
    const rec = decodeJSON(fs.readFileSync(file, 'utf8'));
    const node = [];
    for (let i = 0; i < 2; i++) {
      const sim = await createSim(S1.id, rec.header.seed, 120, { bike });
      sim.run(expandFrames(rec));
      const route = sim.rules.counters().diamondRouteCrossed === true;
      node.push({ phase: sim.phase(), faults: sim.faults(), ticks: sim.runTicks(), seconds: sim.runTime(), route,
        medal: medalFor(sim.runTime(), sim.faults(), S1.meta?.targetTimeS, bike, route), hash: sim.hash() });
    }
    if (JSON.stringify(node[0]) !== JSON.stringify(node[1])) throw new Error(`${bike}: fresh Node mismatch`);
    const browserRuns = [];
    for (let i = 0; i < 2; i++) {
      const page = await browser.context.newPage();
      try {
        await openGame(page, server.url);
        const hook = new HookClient(page);
        const result = await hook.runRecording(encodeJSON(rec));
        const counters = decodeSnapshot(await page.evaluate(() => window.__rockhop!.snapshot())).counters;
        browserRuns.push({ hash: result.hash, seconds: result.state.finishTime,
          phase: await page.evaluate(() => window.__rockhop!.phase()),
          faults: await page.evaluate(() => window.__rockhop!.faults()),
          route: counters?.diamondRouteCrossed === true });
      } finally { await page.close(); }
    }
    const n = node[0]!;
    const b = browserRuns[0]!;
    if (JSON.stringify(browserRuns[0]) !== JSON.stringify(browserRuns[1]) ||
      n.phase !== 'finished' || n.faults !== 0 || n.route !== (bike === 'pro') ||
      n.medal !== (bike === 'pro' ? 'platinum' : 'gold') ||
      n.hash !== b.hash || Math.abs((b.seconds ?? 0) - n.seconds) > 1e-9 ||
      b.phase !== n.phase || b.faults !== n.faults || b.route !== n.route) {
      throw new Error(`${bike}: replay mismatch ${JSON.stringify({ node, browserRuns })}`);
    }
    results.push({ bike, recording: file, node: n, browser: b, identicalFreshWorlds: true });
    console.log(`${bike}: ${n.medal} ${n.seconds.toFixed(3)} s ${n.hash}`);
  }
} finally { await browser.close(); await server.close(); }

const passive = [];
const go = quantizeInput({ throttle: 1 });
for (const bike of ['rookie', 'pro'] as const) for (const seed of [S1.seed, 1, 2]) {
  const sim = await createSim(S1.id, seed, 120, { bike });
  let firstFaultX: number | null = null;
  for (let tick = 0; tick < 600 * 120 && sim.phase() !== 'finished'; tick++) {
    const faults = sim.faults();
    sim.step(go);
    if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
  }
  if (sim.phase() === 'finished') throw new Error(`${bike}/${seed}: held GO clears`);
  passive.push({ bike, seed, phase: sim.phase(), faults: sim.faults(), firstFaultX });
}
const report = { sourceFingerprint: srcFingerprint(), results, passive };
fs.mkdirSync('docs/evidence/s1-lift-bridge', { recursive: true });
fs.writeFileSync('docs/evidence/s1-lift-bridge/verify.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(`Exact 2/2; held GO 0/${passive.length}`);
