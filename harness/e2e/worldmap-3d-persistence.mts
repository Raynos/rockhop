/** Silent WebKit check of saved Coast medals, Alpine unlock, touch selection, and Ride on the review C map. */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

const out = path.resolve(REPO_ROOT, process.argv[2] ?? 'harness/out/worldmap-3d-persistence');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: { width: 852, height: 393 } } });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1');
  // A saved career fixture. The browser still reads this through the normal BestTimes store and builds the map.
  for (const id of ['c1-low-tide', 'c2-crane-hop']) localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 35, faults: 0, medal: 'bronze' }));
});
const page = await context.newPage();
const video = page.video();
const errors: string[] = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const report: Record<string, unknown> = { source: (await import('node:child_process')).execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO_ROOT, encoding: 'utf8' }).trim(), engine: 'Playwright WebKit', fixture: 'two then three saved Coast bronze medals', errors };

async function openMap(): Promise<void> {
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' && !!(window as Window & { __rockhopMap3d?: unknown }).__rockhopMap3d, null, { timeout: 60_000 });
  await page.waitForTimeout(850); // finish the real menu-to-map transition before evidence frames
}

try {
  await page.goto(`${server.url}?map3d=1&sw=0&audio=0`, { waitUntil: 'domcontentloaded' });
  await openMap();
  report.before = await page.evaluate(() => ({
    count: document.querySelector('.wm-progress')?.textContent?.trim(),
    coast: [...document.querySelectorAll('.wm-marker')].slice(0, 3).map(e => e.className),
    alpine: document.querySelector('.wm-marker[data-track="a1-sawdust"]')?.className,
  }));
  await page.evaluate(() => (window as Window & { __rockhopMap3d?: { selectStage(i: number, focus: boolean): void } }).__rockhopMap3d!.selectStage(0, true));
  await page.waitForTimeout(850);
  const earnedPoint = await page.evaluate(() => (window as Window & { __rockhopMap3d?: { towerScreenPoint(i: number): { x: number; y: number } } }).__rockhopMap3d!.towerScreenPoint(0));
  await page.touchscreen.tap(earnedPoint.x, earnedPoint.y);
  report.medal = await page.locator('.wm3d-detail .wm3d-medal').textContent();
  await page.screenshot({ path: path.join(out, 'two-coast-saved.png') });
  await page.evaluate(() => localStorage.setItem('rockhop.best.c3-hull-breach', JSON.stringify({ time: 45, faults: 0, medal: 'bronze' })));
  await page.reload({ waitUntil: 'domcontentloaded' });
  await openMap();
  report.after = await page.evaluate(() => ({
    count: document.querySelector('.wm-progress')?.textContent?.trim(),
    coast: [...document.querySelectorAll('.wm-marker')].slice(0, 3).map(e => e.className),
    alpine: document.querySelector('.wm-marker[data-track="a1-sawdust"]')?.className,
  }));
  await page.screenshot({ path: path.join(out, 'alpine-unlocked.png') });
  await page.evaluate(() => (window as Window & { __rockhopMap3d?: { selectStage(i: number, focus: boolean): void } }).__rockhopMap3d!.selectStage(2, true));
  await page.waitForTimeout(850);
  const point = await page.evaluate(() => (window as Window & { __rockhopMap3d?: { towerScreenPoint(i: number): { x: number; y: number } } }).__rockhopMap3d!.towerScreenPoint(3));
  await page.touchscreen.tap(point.x, point.y);
  await page.waitForTimeout(100);
  report.touch = await page.evaluate(() => ({ track: document.querySelector('.wm3d-detail')?.getAttribute('data-track'), rideDisabled: (document.querySelector('.wm-ride') as HTMLButtonElement)?.disabled }));
  await page.locator('.wm-ride').click();
  await page.waitForFunction(() => (window as Window & { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() === 'run', null, { timeout: 60_000 });
  report.ride = await page.evaluate(() => (window as Window & { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen());
  const before = report.before as { count?: string; alpine?: string };
  const after = report.after as { count?: string; alpine?: string };
  const touch = report.touch as { track?: string; rideDisabled?: boolean };
  report.pass = before.count?.includes('2 / 12') && before.alpine?.includes('locked') && report.medal === 'bronze cleared' && after.count?.includes('3 / 12') && !after.alpine?.includes('locked') && touch.track === 'a1-sawdust' && touch.rideDisabled === false && report.ride === 'run' && errors.length === 0;
  if (!report.pass) process.exitCode = 1;
} catch (error) {
  report.failure = String(error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await context.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'played-save-reload.webm'));
  await browser.close();
  await server.close();
  console.log(JSON.stringify(report, null, 2));
}
