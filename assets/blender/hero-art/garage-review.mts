/** Silent phone-sized WebKit review of the three street riders after `pnpm build`.
 *  node_modules/.bin/tsx assets/blender/hero-art/garage-review.mts [--out=DIR]
 *  The catalog/public hash preflight refuses a stale dist, so the clip cannot
 *  accidentally judge the previous export. The garage plays sit_cruise itself.
 */
/* oxlint-disable typescript/no-explicit-any -- in-page probes use browser-only review hooks. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { webkit } from 'playwright';
import { startServer } from '../../../harness/lib/server';
import { REPO_ROOT } from '../../../harness/lib/paths';

const out = path.resolve(process.argv.find(a => a.startsWith('--out='))?.slice(6) ?? 'harness/out/street-rider-review');
fs.mkdirSync(out, { recursive: true });
const hash = (data: Buffer) => crypto.createHash('sha256').update(data).digest('hex');
const catalog = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'dist/model-catalog.json'), 'utf8')) as {
  models: { logical: string; url: string; sha256: string }[];
};
const street = catalog.models.filter(m => /^models\/rider-street-.*\.glb$/.test(m.logical));
assert.equal(street.length, 6, 'all six street models in dist catalog');
for (const m of street) {
  const publicFile = path.join(REPO_ROOT, 'public', m.logical);
  const distFile = path.join(REPO_ROOT, 'dist', m.url);
  assert.equal(hash(fs.readFileSync(publicFile)), m.sha256, `catalog/public ${m.logical}`);
  assert.equal(hash(fs.readFileSync(distFile)), m.sha256, `catalog/dist ${m.logical}`);
}

const server = await startServer({ freeze: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 874, height: 330 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: { width: 874, height: 330 } },
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const report: { catalog: typeof street; loaded: { url: string; sha256: string; status: number }[]; models: unknown[]; errors: string[]; navigation?: unknown; navigationFallback?: boolean; failure?: string } =
  { catalog: street, loaded: [], models: [], errors: [] };
const responses: Promise<void>[] = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', response => {
  if (!response.url().endsWith('.glb')) return;
  responses.push((async () => report.loaded.push({ url: response.url(), status: response.status(), sha256: hash(await response.body()) }))());
});
async function tap(selector: string): Promise<void> {
  const box = await page.locator(selector).boundingBox();
  if (!box) throw new Error(`missing ${selector}`);
  await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
}

try {
  await page.goto(server.url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  // The game may create the live menu below its loading overlay. A tap there
  // legitimately hits #loader; wait until the button is the real touch target.
  await page.waitForFunction(() => {
    const button = document.querySelector('.menu-screen.live .menu-item[data-id=garage]');
    const rect = button?.getBoundingClientRect();
    if (!button || !rect) return false;
    const hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return hit === button || button.contains(hit);
  }, null, { timeout: 120_000 });
  const navigation: any = {};
  const inspectGarage = () => page.evaluate(() => {
    const el = document.querySelector('.menu-screen.live .menu-item[data-id=garage]');
    const rect = el?.getBoundingClientRect();
    const centre = rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : null;
    const hit = centre ? document.elementFromPoint(centre.x, centre.y) : null;
    return { button: el?.outerHTML.slice(0, 350), centre, hit: hit?.outerHTML.slice(0, 350), menuLive: !!document.querySelector('.menu-screen.live'), garageLive: !!document.querySelector('.garage-screen.live') };
  });
  navigation.before = await inspectGarage();
  await tap('.menu-screen.live .menu-item[data-id=garage]');
  try { await page.waitForSelector('.garage-screen.live', { timeout: 2_000 }); navigation.firstTap = 'navigated'; }
  catch {
    navigation.afterFirstTap = await inspectGarage();
    await page.screenshot({ path: path.join(out, 'menu-after-first-tap.png') });
    await tap('.menu-screen.live .menu-item[data-id=garage]');
    try { await page.waitForSelector('.garage-screen.live', { timeout: 2_000 }); navigation.secondTap = 'navigated'; }
    catch {
      navigation.afterSecondTap = await inspectGarage();
      await page.evaluate(() => (window as any).__rockhop.app.goto('garage'));
      await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
      report.navigationFallback = true;
    }
  }
  report.navigation = navigation;
  await page.evaluate(async () => (window as any).__render.whenReady());
  for (const outfit of ['street-mustard', 'street-charcoal', 'street-openface']) {
    await tap(`button[data-outfit="${outfit}"]`);
    await page.waitForFunction(id => localStorage.getItem('rockhop.riderOutfit') === id && (window as any).__render.debugInfo().riderOutfit === id, outfit, { timeout: 30_000 });
    await page.evaluate(async () => (window as any).__render.whenReady());
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(out, `${outfit}.png`) });
    const debug = await page.evaluate(() => {
      const d = (window as any).__render.debugInfo();
      return { outfit: d.riderOutfit, heroDoc: d.heroDoc, heroTris: d.heroTris, tier: d.tier, stageClip: (window as any).__render.debug?.rider?.debug?.stageClip };
    });
    assert.equal(debug.stageClip, 'sit_cruise', `${outfit} animated stage`);
    report.models.push(debug);
  }
  await Promise.all(responses);
  for (const m of street) {
    const seen = report.loaded.find(r => r.url.endsWith('/' + m.url));
    assert.equal(seen?.sha256, m.sha256, `fetched ${m.logical}`);
    assert.equal(seen?.status, 200, `served ${m.logical}`);
  }
  assert.deepEqual(report.errors, [], 'page errors');
} catch (e) { report.failure = e instanceof Error ? e.message : String(e); }
finally {
  const video = page.video();
  await page.close(); await context.close(); await browser.close(); await server.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'clip.webm'));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ models: report.models, navigationFallback: report.navigationFallback, errors: report.errors, failure: report.failure, video: path.join(out, 'clip.webm') }, null, 2));
  if (report.failure) process.exitCode = 1;
}
