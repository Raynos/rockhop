/** Full recorded clear, crash and one-tick restart on exact private hero bytes. */
/* oxlint-disable typescript/no-explicit-any -- browser test hooks. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { installPrivateHipReviewDriver } from './new-rider-hip-review-install.mjs';
import { installPrivateSleeveReviewDriver } from './new-rider-sleeve-review-install.mjs';

const arg = (name: string, fallback = '') => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build'));
const out = path.resolve(arg('out'));
const hipReviewDriver = arg('hip-review-driver', '0') === '1';
const sleeveReviewDriver = arg('sleeve-review-driver', '0') === '1';
assert(!(hipReviewDriver && sleeveReviewDriver), 'Independent corrective trials must stay separate');
const recordingFile = arg('recording', 'harness/inputs/b1-first-ride/bot-3.json');
const rec = decodeJSON(fs.readFileSync(recordingFile, 'utf8'));
const inputs = expandFrames(rec);
const node = await createSimFor(rec);
for (const frame of inputs) node.step(frame);
const expected = { hash: node.hash(), runTime: node.runTime(), faults: node.faults(), finishTime: node.state().finishTime, tick: node.state().tick };
assert.notEqual(expected.finishTime, null, 'recorded bot clears the track in Node');
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const report: any = { build, recordingFile, expected, hipReviewDriver, sleeveReviewDriver, sleeveReviewOverlay: sleeveReviewDriver ? JSON.parse(fs.readFileSync(path.join(build, 'sleeve-overlay.json'), 'utf8')) : null, reviewOverlay: hipReviewDriver ? JSON.parse(fs.readFileSync(path.join(build, 'hip-overlay.json'), 'utf8')) : null, runs: [], errors: [] };
try {
  for (const tier of ['low', 'high']) {
    const page = await browser.newPage({ viewport: { width: 874, height: 330 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
    page.on('pageerror', e => report.errors.push(e.message));
    await page.goto(server.resolvedUrls!.local[0] + `?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${rec.header.physics ?? 'v1'}&hz=${rec.header.physicsHz}`);
    await page.waitForFunction(() => (window as any).__rockhop?.ready);
    await page.evaluate(async ({ header, tier }) => {
      const t = (window as any).__rockhop, r = (window as any).__render;
      t.setBike(header.bike ?? 'rookie'); await r.whenReady();
      await t.loadTrack(header.trackId, header.seed); await r.whenReady();
      t.setQuality(tier); await r.whenReady(); t.skipCountdown();
    }, { header: rec.header, tier });
    if (hipReviewDriver) await installPrivateHipReviewDriver(page);
    if (sleeveReviewDriver) await installPrivateSleeveReviewDriver(page);
    const result = await page.evaluate(inputs => {
      const t = (window as any).__rockhop;
      for (let i = 0; i < inputs.length; i++) {
        t.setInput(inputs[i]); t.step(1);
        if (i % 4 === 0) t.render(true);
      }
      t.render(true);
      return { hash: t.hashState(), runTime: t.runTime(), faults: t.faults(), finishTime: t.getState().finishTime, tick: t.getState().tick };
    }, inputs);
    assert.deepEqual(result, expected, `${tier} full rendered clear equals Node`);
    const crashRestart = await page.evaluate(() => {
      const t = (window as any).__rockhop;
      t.restart(); t.skipCountdown();
      let ticks = 0;
      t.setInput({ throttle: 1, lean: -1, brake: 0, hop: false, restart: false });
      while (t.phase() !== 'crashed' && ticks < 2400) { t.step(1); if (ticks++ % 4 === 0) t.render(true); }
      const phase = t.phase();
      const start = performance.now();
      t.setInput({ throttle: 0, lean: 0, restart: true }); t.step(1); t.render(true);
      return { crashed: phase === 'crashed', crashTicks: ticks, restartPhase: t.phase(), restartTick: t.getState().tick, restartMs: performance.now() - start };
    });
    assert.equal(crashRestart.crashed, true, 'lean-back input crashes');
    assert.equal(crashRestart.restartPhase, 'riding', 'restart edge resumes immediately');
    assert(crashRestart.restartTick <= 1, 'restart resets in one tick');
    const clockBytes = Buffer.alloc(8); clockBytes.writeDoubleLE(result.finishTime!);
    const hipCorrective = hipReviewDriver ? await page.evaluate(() => structuredClone((window as any).__render.debug.rider.scene.userData.privateHipCorrectiveDiagnostic)) : null;
    if (hipReviewDriver) assert(hipCorrective?.weights.every(Number.isFinite));
    const sleeveCorrective = sleeveReviewDriver ? await page.evaluate(() => structuredClone((window as any).__render.debug.rider.scene.userData.privateSleeveCorrectiveDiagnostic)) : null;
    if (sleeveReviewDriver) assert(sleeveCorrective?.weights.every(Number.isFinite));
    report.runs.push({ sleeveCorrective, tier, result, finishTimeFloat64LE: clockBytes.toString('hex'), crashRestart, hipCorrective });
    await page.close();
  }
  assert.deepEqual(report.errors, []);
} catch (e) { report.failure = e instanceof Error ? e.message : String(e); }
finally {
  await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report)); if (report.failure) process.exitCode = 1;
}
