/**
 * Warm a service-worker-controlled visit, switch the browser offline before
 * the first PLAY, then prove the 3D island and all twelve towers work.
 * pnpm exec tsx harness/e2e/worldmap-3d-offline.mts [output-directory]
 */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { ROCKHOP_ALL } from '../../src/tracks';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

type HookWindow = Window & { __rockhopMap3d?: {
  towerScreenPoint(index: number): { x: number; y: number } | null;
  selectStage(index: number, focus?: boolean): void;
} };
const out = path.resolve(REPO_ROOT, process.argv[2] ?? 'harness/out/worldmap-3d-offline');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true });
let serverClosed = false;
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  serviceWorkers: 'allow', recordVideo: { dir: out, size: { width: 852, height: 393 } } });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const video = page.video();
const errors: string[] = [];
const failedRequests: string[] = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('requestfailed', request => failedRequests.push(`${request.url()}: ${request.failure()?.errorText ?? 'unknown'}`));
const report: Record<string, unknown> = { engine: 'headless WebKit with service worker', errors, failedRequests };
try {
  await page.goto(server.url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(() => !!navigator.serviceWorker.controller, null, { timeout: 30_000 });
  // A controlled warm visit ensures the boot's map prefetch is stored in Cache Storage.
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  const cached = await page.evaluate(async () => {
    const names = await caches.keys();
    const urls = (await Promise.all(names.map(async name => (await (await caches.open(name)).keys()).map(key => key.url)))).flat();
    return { controlled: !!navigator.serviceWorker.controller, names,
      chunk: urls.find(url => /\/assets\/worldMap3dScene-[\w-]+\.js$/.test(url)) ?? null,
      sky: urls.find(url => /\/assets\/sky-alpine-a-[\w-]+\.webp$/.test(url)) ?? null };
  });
  report.cached = cached;
  // Stop the origin itself. WebKit's context.setOffline() blocks even SW-served
  // responses, so a dead origin is the stronger useful test here.
  await server.close();
  serverClosed = true;
  report.offlineFetch = await page.evaluate(async (urls) => {
    const chunk = await fetch(urls.chunk!);
    const sky = await fetch(urls.sky!);
    return { chunk: { status: chunk.status, bytes: (await chunk.arrayBuffer()).byteLength },
      sky: { status: sky.status, bytes: (await sky.arrayBuffer()).byteLength } };
  }, cached);
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' &&
    !!(window as HookWindow).__rockhopMap3d, null, { timeout: 60_000 });
  const points: ({ x: number; y: number } | null)[] = [];
  for (let index = 0; index < ROCKHOP_ALL.length; index++)
    points.push(await page.evaluate(i => (window as HookWindow).__rockhopMap3d!.towerScreenPoint(i), index));
  await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.selectStage(0, true));
  await page.waitForTimeout(800);
  const c1 = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.towerScreenPoint(0));
  if (c1) await page.touchscreen.tap(c1.x, c1.y);
  report.offlineMap = {
    selected: await page.locator('.wm3d-detail').getAttribute('data-track'),
    canvas: await page.locator('.wm3d-host canvas').count(),
    towerPoints: points.length,
    nonNullPoints: points.filter(Boolean).length,
  };
  await page.screenshot({ path: path.join(out, 'offline-first-map.png') });
  const map = report.offlineMap as { selected: string | null; canvas: number; towerPoints: number; nonNullPoints: number };
  const unexpectedFailures = failedRequests.filter(line => !line.includes('/version.json?'));
  const expectedVersionProbe = failedRequests.filter(line => line.includes('/version.json?'));
  report.expectedOfflineVersionProbe = expectedVersionProbe;
  report.pass = cached.controlled && !!cached.chunk && !!cached.sky &&
    map.selected === 'c1-low-tide' && map.canvas === 1 && map.towerPoints === 12 && map.nonNullPoints === 12 &&
    unexpectedFailures.length === 0 && errors.length === expectedVersionProbe.length;
  if (!report.pass) process.exitCode = 1;
} catch (error) {
  report.failure = String(error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await context.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'played-offline-map.webm'));
  await browser.close();
  if (!serverClosed) await server.close();
  console.log(JSON.stringify(report, null, 2));
}
