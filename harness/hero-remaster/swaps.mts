/** Resident full-family Garage swap check on a frozen private review build. */
/* oxlint-disable typescript/no-explicit-any -- browser inspection hooks. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { preview } from 'vite';
import { webkit } from 'playwright';

const arg = (name: string) => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? '';
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
fs.mkdirSync(out, { recursive: true });
const server = await preview({ configFile: false, build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 874, height: 330 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
const report: any = { build, swaps: [], errors: [] };
let modelResponses = 0;
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => { if (r.url().endsWith('.glb')) modelResponses++; });
try {
  await page.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
  await page.goto(server.resolvedUrls!.local[0] + '?audio=0&sw=0');
  await page.locator('.menu-screen.live .menu-item[data-id=garage]').click({ timeout: 120_000 });
  await page.waitForSelector('.garage-screen.live');
  await page.evaluate(async () => (window as any).__render.whenReady());
  const loadedBefore = modelResponses;
  const outfits = ['street-mustard', 'street-charcoal', 'street-openface', 'race-bluewhite', 'race-charcoalyellow'];
  for (let round = 0; round < 2; round++) for (const outfit of outfits) for (const bike of ['rookie', 'pro']) {
    // Unlock state is deliberately untouched: class testing uses the same
    // resident renderer API; outfit selection uses the actual Garage button.
    await page.locator(`button[data-outfit="${outfit}"]`).click();
    const result = await page.evaluate(async ({ bike, outfit, round }) => {
      const r = (window as any).__render, t = (window as any).__rockhop;
      const start = performance.now();
      r.setBikeClass(bike); await r.whenReady(); t.render(true); r.finish();
      const info = r.debugInfo();
      return { round, outfit, bike, ms: performance.now() - start, textures: r.debug.renderer.info.memory.textures, programs: r.debug.renderer.info.programs.length, pool: r.heroPool.size, info: { dpr: info.dpr, canvasW: info.canvasW, canvasH: info.canvasH, riderOutfit: info.riderOutfit }, aa: { threshold: r.debug.post.aa._materialEdges.defines.SMAA_THRESHOLD, steps: r.debug.post.aa._materialWeights.defines.SMAA_MAX_SEARCH_STEPS } };
    }, { bike, outfit, round });
    assert.equal(result.info.riderOutfit, outfit);
    assert.equal(result.info.dpr, 2);
    assert.equal(result.aa.threshold, '0.1');
    assert.equal(result.aa.steps, '8');
    report.swaps.push(result);
    if (round === 0) await page.screenshot({ path: path.join(out, `${outfit}-${bike}.png`) });
  }
  assert.equal(modelResponses, loadedBefore, 'twenty swaps fetch no models');
  for (const result of report.swaps.slice(10)) {
    assert.equal(result.pool, report.swaps[9].pool, 'warm swaps create no new hero instances');
    assert(result.textures <= report.swaps[9].textures, 'warm swaps bound live textures');
    assert(result.programs <= report.swaps[9].programs, 'warm swaps bound programs');
  }
  report.modelResponses = modelResponses;
  await page.locator('.garage-screen.live .backbtn').click();
  report.exit = await page.evaluate(() => {
    const r = (window as any).__render;
    return { info: r.debugInfo(), aa: { threshold: r.debug.post.aa._materialEdges.defines.SMAA_THRESHOLD, steps: r.debug.post.aa._materialWeights.defines.SMAA_MAX_SEARCH_STEPS } };
  });
  assert.equal(report.exit.info.garage.on, false);
  assert.equal(report.exit.info.dpr, 1.5, 'exit restores phone riding pixel budget');
  assert.equal(report.exit.aa.threshold, '0.15');
  assert.equal(report.exit.aa.steps, '4');
  assert.deepEqual(report.errors, []);
} catch (e) { report.failure = e instanceof Error ? e.message : String(e); }
finally {
  await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, swaps: report.swaps.length, failure: report.failure, errors: report.errors }));
  if (report.failure) process.exitCode = 1;
}
