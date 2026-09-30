/** Runtime GLB failure and late-resolution checks against the frozen integrated build. */
import { writeFileSync } from 'node:fs';
import { expandFrames } from '../../../../../src/core/replay';
import { loadRecording } from '../../../../../harness/lib/recording';
import { launchBrowser } from '../../../../../harness/lib/browser';
import { openGame } from '../../../../../harness/lib/hook';

const [outFile] = process.argv.slice(2);
const url = process.env.C1_CAPTURE_URL;
const sha = process.env.C1_CAPTURE_SHA;
if (!outFile || !url || !sha) throw new Error('C1_CAPTURE_URL=... C1_CAPTURE_SHA=... tsx lifecycle.mts output.json');
const version = await fetch(new URL('/version.json', url)).then(r => r.json()) as { sha: string };
if (version.sha !== sha) throw new Error(`frozen build mismatch: ${version.sha} != ${sha}`);
const frameInput = expandFrames(loadRecording('harness/inputs/c1-low-tide/bot-3.json')).slice(0, 1360);

const broken = await launchBrowser({ width: 852, height: 392, logConsole: false });
let missing: unknown;
try {
  const page = broken.page;
  const errors: string[] = [];
  const blocked: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/c1-harbor-tug*.glb', route => { blocked.push(route.request().url()); return route.abort('failed'); });
  console.log('missing: opening');
  await openGame(page, url);
  console.log('missing: opened');
  await page.evaluate(() => {
    const game = window.__rockhop!;
    game.setQuality('low');
    game.setBike('rookie');
    game.loadTrack('c1-low-tide', 341352973);
  });
  console.log('missing: explicit C1 load', blocked.length);
  await page.waitForFunction(() => window.__rockhop?.info().render.entering === false, undefined, { timeout: 20_000 });
  console.log('missing: entry completed');
  const result = await page.evaluate((input) => {
    const game = window.__rockhop!;
    game.skipCountdown();
    for (const frame of input) { game.setInput(frame); game.step(1); }
    game.render(false);
    return { tick: game.getState().tick, x: game.getState().bike.pos.x, hash: game.hashState(),
      stats: game.stats(), render: game.info().render };
  }, frameInput);
  await page.screenshot({ path: outFile.replace(/\.json$/, '-missing.png') });
  missing = { blocked, errors, result };
  console.log('missing: captured');
} finally {
  await broken.close();
}

const delayed = await launchBrowser({ width: 852, height: 392, logConsole: false });
let switched: unknown;
try {
  const page = delayed.page;
  const errors: string[] = [];
  const held: string[] = [];
  const release: Array<() => void> = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/c1-harbor-tug*.glb', async route => {
    held.push(route.request().url());
    await new Promise<void>(resolve => release.push(resolve));
    await route.continue();
  });
  console.log('delayed: opening');
  await openGame(page, url);
  console.log('delayed: opened');
  await page.evaluate(() => { window.__rockhop!.loadTrack('c1-low-tide', 341352973); return true; });
  await page.waitForFunction(() => window.__rockhop?.info().render.entering === true, undefined, { timeout: 10_000 });
  console.log('delayed: pending');
  await page.waitForTimeout(250);
  if (!held.length) throw new Error('C1 GLB request was not held');
  await page.evaluate(() => window.__rockhop!.loadTrack('a1-sawdust', 1));
  console.log('delayed: switched');
  await page.waitForFunction(() => {
    const r = window.__rockhop?.info().render;
    return r?.biome === 'alpine' && r.entering === false;
  }, undefined, { timeout: 20_000 });
  console.log('delayed: A1 ready');
  await page.evaluate(() => window.__rockhop!.render(false));
  const beforeRelease = await page.evaluate(() => ({ stats: window.__rockhop!.stats(), render: window.__rockhop!.info().render }));
  for (const done of release) done();
  console.log('delayed: released');
  await page.waitForTimeout(1200);
  await page.evaluate(() => window.__rockhop!.render(false));
  const afterRelease = await page.evaluate(() => ({ stats: window.__rockhop!.stats(), render: window.__rockhop!.info().render }));
  switched = { held, errors, beforeRelease, afterRelease };
} finally {
  await delayed.close();
}
const report = { sha, backend: process.env.TRIALS_BROWSER_BACKEND ?? 'swiftshader', missing, switched };
writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n');
const m = missing as { blocked: string[]; errors: string[]; result: { stats: { calls: number } } };
const s = switched as { errors: string[]; beforeRelease: { stats: { texturesMB: number; calls: number } }; afterRelease: { stats: { texturesMB: number; calls: number } } };
console.log(outFile, 'blocked', m.blocked.length, 'missingCalls', m.result.stats.calls,
  'switchTexturesMB', s.beforeRelease.stats.texturesMB, s.afterRelease.stats.texturesMB,
  'switchCalls', s.beforeRelease.stats.calls, s.afterRelease.stats.calls,
  'pageErrors', m.errors.length + s.errors.length);
if (!m.blocked.length || m.errors.length || s.errors.length ||
  s.afterRelease.stats.texturesMB > s.beforeRelease.stats.texturesMB + 0.01) process.exitCode = 1;
