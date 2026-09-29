/**
 * Silent WebKit cutover gate on the normal URL:
 * pnpm exec tsx harness/e2e/worldmap-3d-webkit.mts [output-directory]
 */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { ROCKHOP_ALL } from '../../src/tracks';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

type MapProbe = {
  selectStage(index: number, focus?: boolean): void;
  setProgress(locked: boolean[], medals: (string | null)[]): void;
  viewState(): { dragMode: string; target: { x: number; y: number; z: number }; azimuth: number; states: string[] };
  towerScreenPoint(index: number): { x: number; y: number } | null;
  stats(): { selected: number; disposed: boolean };
};
type HookWindow = Window & { __rockhopMap3d?: MapProbe; __render?: { canvas: HTMLCanvasElement }; __rockhop?: { app?: { screen(): string } } };

const out = path.resolve(REPO_ROOT, process.argv[2] ?? 'harness/out/worldmap-3d-webkit');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true, forceBuild: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: { width: 852, height: 393 } },
});
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const video = page.video();
const errors: string[] = [];
const requests: string[] = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('request', request => requests.push(request.url()));
const expected = ROCKHOP_ALL.map(track => track.id);
const report: Record<string, unknown> = { engine: 'headless WebKit', normalUrl: true, expected, errors };

const mapReady = () => page.waitForFunction(() =>
  document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' &&
  !!(window as HookWindow).__rockhopMap3d, null, { timeout: 60_000 });

try {
  await page.goto(`${server.url}?sw=0`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  const bootRequests = [...requests];
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await mapReady();
  report.open = await page.evaluate(() => ({
    canvas: document.querySelectorAll('.wm3d-host canvas').length,
    painted: document.querySelector('.wm-view') !== null,
    loading: getComputedStyle(document.querySelector('.wm3d-loading')!).display,
    gameContextLost: (window as HookWindow).__render?.canvas.getContext('webgl2')?.isContextLost(),
  }));
  await page.screenshot({ path: path.join(out, 'landscape-front.png') });
  report.campaignStates = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState().states);
  await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.setProgress(
    Array.from({ length: 12 }, (_, i) => i === 5),
    ['bronze', 'silver', 'gold', 'platinum', null, null, null, null, null, null, null, null],
  ));
  report.medalStates = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState().states);
  await page.screenshot({ path: path.join(out, 'medal-state-markers.png') });

  const selected: { index: number; id: string | null; tower: { x: number; y: number } | null }[] = [];
  for (let i = 0; i < expected.length; i++) {
    await page.evaluate(index => (window as HookWindow).__rockhopMap3d!.selectStage(index, true), i);
    await page.waitForTimeout(760);
    const tower = await page.evaluate(index => (window as HookWindow).__rockhopMap3d!.towerScreenPoint(index), i);
    if (tower) await page.touchscreen.tap(tower.x, tower.y);
    const id = await page.locator('.wm3d-detail').getAttribute('data-track');
    selected.push({ index: i, id, tower });
  }
  report.selected = selected;
  await page.screenshot({ path: path.join(out, 'twelve-towers.png') });

  await page.setViewportSize({ width: 393, height: 852 });
  await page.waitForFunction(() => document.querySelectorAll('.wm3d-host canvas').length === 0, null, { timeout: 20_000 });
  report.portrait = await page.evaluate(() => ({
    prompt: document.querySelector('.wm3d-rotate')?.textContent?.trim(),
    display: getComputedStyle(document.querySelector('.wm3d-rotate')!).display,
    canvas: document.querySelectorAll('.wm3d-host canvas').length,
  }));
  await page.screenshot({ path: path.join(out, 'portrait-rotate.png') });

  await page.setViewportSize({ width: 852, height: 393 });
  await mapReady();
  const beforePan = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState());
  await page.mouse.move(620, 280);
  await page.mouse.down();
  for (let i = 1; i <= 24; i++) {
    await page.mouse.move(620 - i * 9, 280 - i * 2);
    await page.waitForTimeout(16);
  }
  await page.mouse.up();
  await page.waitForTimeout(300);
  const afterPan = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState());
  report.pan = { before: beforePan, after: afterPan };
  await page.screenshot({ path: path.join(out, 'landscape-panned.png') });
  await page.locator('.wm-orbit').click();
  const beforeOrbit = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState());
  await page.mouse.move(620, 280);
  await page.mouse.down();
  for (let i = 1; i <= 20; i++) {
    await page.mouse.move(620 - i * 7, 280);
    await page.waitForTimeout(16);
  }
  await page.mouse.up();
  await page.waitForTimeout(300);
  const afterOrbit = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.viewState());
  report.orbit = { before: beforeOrbit, after: afterOrbit };
  await page.screenshot({ path: path.join(out, 'landscape-rotated.png') });

  await page.locator('.worldmap-screen.live .backbtn').click();
  await page.waitForSelector('.menu-screen.live', { timeout: 20_000 });
  report.menu = await page.evaluate(() => ({
    mapCanvases: document.querySelectorAll('.wm3d-host canvas').length,
    mapHook: !!(window as HookWindow).__rockhopMap3d,
  }));

  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await mapReady();
  await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.selectStage(0, true));
  await page.waitForTimeout(760);
  const c1 = await page.evaluate(() => (window as HookWindow).__rockhopMap3d!.towerScreenPoint(0));
  if (c1) await page.touchscreen.tap(c1.x, c1.y);
  await page.locator('.wm-ride').click();
  await page.waitForFunction(() => (window as HookWindow).__rockhop?.app?.screen() === 'run', null, { timeout: 60_000 });
  report.ride = await page.evaluate(() => ({
    screen: (window as HookWindow).__rockhop?.app?.screen(),
    mapCanvases: document.querySelectorAll('.wm3d-host canvas').length,
    mapHook: !!(window as HookWindow).__rockhopMap3d,
    gameContextLost: (window as HookWindow).__render?.canvas.getContext('webgl2')?.isContextLost(),
  }));

  const open = report.open as { canvas: number; painted: boolean; loading: string; gameContextLost: boolean };
  const portrait = report.portrait as { prompt: string; display: string; canvas: number };
  const menu = report.menu as { mapCanvases: number; mapHook: boolean };
  const ride = report.ride as { screen: string; mapCanvases: number; mapHook: boolean; gameContextLost: boolean };
  report.requests = {
    painted: requests.filter(url => url.includes('/art/worldmap/')),
    mapChunk: requests.filter(url => url.includes('worldMap3dScene')),
    sky: requests.filter(url => /\/assets\/sky-alpine-a-[\w-]+\.webp/.test(url)),
    bootMapChunk: bootRequests.filter(url => url.includes('worldMap3dScene')),
    bootSky: bootRequests.filter(url => /\/assets\/sky-alpine-a-[\w-]+\.webp/.test(url)),
  };
  const r = report.requests as { painted: string[]; mapChunk: string[]; sky: string[]; bootMapChunk: string[]; bootSky: string[] };
  const moved = Math.hypot(afterPan.target.x - beforePan.target.x, afterPan.target.z - beforePan.target.z);
  const spun = Math.abs(afterOrbit.azimuth - beforeOrbit.azimuth);
  report.pass =
    expected.length === 12 && selected.every((entry, i) => !!entry.tower && entry.id === expected[i]) &&
    open.canvas === 1 && !open.painted && open.loading === 'none' &&
    portrait.canvas === 0 && portrait.display === 'flex' && portrait.prompt.includes('Rotate your phone') &&
    menu.mapCanvases === 0 && !menu.mapHook && ride.screen === 'run' && ride.mapCanvases === 0 && !ride.mapHook &&
    ride.gameContextLost === false && r.painted.length === 0 && r.mapChunk.length >= 1 && r.sky.length >= 1 &&
    r.bootMapChunk.length >= 1 && r.bootSky.length >= 1 &&
    moved > 1 && Math.abs(afterPan.azimuth - beforePan.azimuth) < 0.02 &&
    beforePan.dragMode === 'pan' && beforeOrbit.dragMode === 'orbit' && spun > 0.1 &&
    (report.medalStates as string[]).slice(0, 6).join(',') === 'bronze,silver,gold,platinum,available,locked' &&
    errors.length === 0;
  if (!report.pass) process.exitCode = 1;
} catch (error) {
  report.failure = String(error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await context.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'played-map.webm'));
  await browser.close();
  await server.close();
  console.log(JSON.stringify(report, null, 2));
}
