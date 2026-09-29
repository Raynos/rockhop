/** Current-source exact Snowline replays and three-seed passive-GO rejection. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { decodeSnapshot } from '../../src/game/hook';
import { medalFor } from '../../src/game/rules';
import { S1, S2, S3 } from '../../src/tracks/rockhop/snowline';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { srcFingerprint } from '../lib/metrics';
import { startServer } from '../lib/server';
import { createSim } from '../lib/sim';

const tracks = [S1, S2, S3];
const bikes = ['rookie', 'pro'] as const;
const runs = [];
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 393 });
try {
  for (const track of tracks) for (const bike of bikes) {
    const file = `harness/inputs/${track.id}/bot-3${bike === 'pro' ? '-pro' : ''}.json`;
    const recording = decodeJSON(fs.readFileSync(file, 'utf8'));
    const samples = [];
    for (let n = 0; n < 2; n++) {
      const sim = await createSim(track.id, recording.header.seed, 120, { bike });
      sim.run(expandFrames(recording));
      const route = sim.rules.counters().diamondRouteCrossed === true;
      samples.push({ phase: sim.phase(), faults: sim.faults(), ticks: sim.runTicks(), seconds: sim.runTime(),
        route, medal: medalFor(sim.runTime(), sim.faults(), track.meta?.targetTimeS, bike, route), hash: sim.hash() });
    }
    if (JSON.stringify(samples[0]) !== JSON.stringify(samples[1])) throw new Error(`${track.id}/${bike}: fresh Node worlds differ`);
    const node = samples[0]!;
    if (node.phase !== 'finished' || node.faults !== 0 || node.route !== (bike === 'pro') ||
        node.medal !== (bike === 'pro' ? 'platinum' : 'gold')) throw new Error(`${track.id}/${bike}: pinned route regressed ${JSON.stringify(node)}`);
    const browserSamples = [];
    for (let n = 0; n < 2; n++) {
      const page = await browser.context.newPage();
      try {
        await openGame(page, server.url);
        const hook = new HookClient(page);
        const result = await hook.runRecording(encodeJSON(recording));
        const counters = decodeSnapshot(await page.evaluate(() => window.__rockhop!.snapshot())).counters;
        browserSamples.push({ hash: result.hash, seconds: result.state.finishTime,
          phase: await page.evaluate(() => window.__rockhop!.phase()),
          faults: await page.evaluate(() => window.__rockhop!.faults()),
          route: counters?.diamondRouteCrossed === true });
      } finally { await page.close(); }
    }
    const browserRun = browserSamples[0]!;
    if (JSON.stringify(browserSamples[0]) !== JSON.stringify(browserSamples[1]) ||
        browserRun.hash !== node.hash || Math.abs((browserRun.seconds ?? 0) - node.seconds) > 1e-9 ||
        browserRun.phase !== node.phase || browserRun.faults !== node.faults || browserRun.route !== node.route) {
      throw new Error(`${track.id}/${bike}: Node/browser mismatch ${JSON.stringify({ node, browserSamples })}`);
    }
    runs.push({ track: track.id, bike, recording: file, ...node, browser: browserRun,
      browserSecondsDelta: (browserRun.seconds ?? 0) - node.seconds, freshWorldIdentical: true });
    console.log(`${track.id}/${bike}: ${node.medal} ${node.seconds.toFixed(3)} s ${node.hash}`);
  }
} finally {
  await browser.close();
  await server.close();
}

const passive = [];
const go = quantizeInput({ throttle: 1 });
for (const track of tracks) for (const bike of bikes) for (const seed of [track.seed, 1, 2]) {
  const sim = await createSim(track.id, seed, 120, { bike });
  let maxX = sim.state().bike.pos.x;
  let firstFaultX: number | null = null;
  for (let tick = 0; tick < 600 * 120 && sim.phase() !== 'finished'; tick++) {
    const faults = sim.faults();
    sim.step(go);
    maxX = Math.max(maxX, sim.state().bike.pos.x);
    if (firstFaultX === null && sim.faults() > faults) firstFaultX = sim.state().bike.pos.x;
  }
  passive.push({ track: track.id, bike, seed, phase: sim.phase(), faults: sim.faults(), firstFaultX, maxX,
    finishX: sim.track.finishX, hash: sim.hash() });
  if (sim.phase() === 'finished') throw new Error(`${track.id}/${bike}/${seed}: held GO cleared`);
}
const report = { sourceFingerprint: srcFingerprint(), runs, passive };
fs.mkdirSync('docs/evidence/snow-bike-role', { recursive: true });
fs.writeFileSync('docs/evidence/snow-bike-role/verify.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(`Exact runs ${runs.length}/6, held-GO rejects ${passive.length}/18`);
