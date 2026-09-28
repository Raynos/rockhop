/** Silent iOS-WebKit smoke for the review-only C island, from the real menu. */
/* oxlint-disable typescript/no-explicit-any -- browser probes read the review hook. */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

const out = path.resolve(REPO_ROOT, process.argv[2] ?? 'harness/out/worldmap-3d-webkit');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 852, height: 393 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
  recordVideo: { dir: out, size: { width: 852, height: 393 } },
});
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const video = page.video();
const errors: string[] = [];
const assetResponses: { url: string; status: number }[] = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('response', response => {
  if (response.url().includes('island-sky') || response.url().includes('worldMap3dScene')) {
    assetResponses.push({ url: response.url(), status: response.status() });
  }
});
const report: Record<string, unknown> = { source: (await import('node:child_process')).execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO_ROOT, encoding: 'utf8' }).trim(), engine: 'Playwright WebKit', errors, assetResponses };

try {
  await page.goto(`${server.url}?map3d=1&sw=0&audio=0`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' && !!(window as any).__rockhopMap3d, null, { timeout: 60_000 });
  await page.waitForTimeout(800);
  report.open = await page.evaluate(() => ({
    canvas: document.querySelectorAll('.wm3d-host canvas').length,
    rotate: getComputedStyle(document.querySelector('.wm3d-rotate')!).display,
    stats: (window as any).__rockhopMap3d.stats(),
  }));
  await page.screenshot({ path: path.join(out, 'landscape-front.png') });

  await page.setViewportSize({ width: 393, height: 852 });
  await page.waitForTimeout(400);
  report.portrait = await page.evaluate(() => ({
    rotate: getComputedStyle(document.querySelector('.wm3d-rotate')!).display,
    prompt: document.querySelector('.wm3d-rotate')?.textContent?.trim(),
    canvas: document.querySelectorAll('.wm3d-host canvas').length,
    host: getComputedStyle(document.querySelector('.wm3d-host')!).display,
  }));
  await page.screenshot({ path: path.join(out, 'portrait-rotate.png') });
  await page.setViewportSize({ width: 852, height: 393 });
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' && !!(window as any).__rockhopMap3d, null, { timeout: 60_000 });

  // Move the real camera before tapping; screenshot the resulting three-quarter composition.
  await page.mouse.move(620, 280);
  await page.mouse.down();
  for (let i = 1; i <= 24; i++) {
    await page.mouse.move(620 - i * 9, 280 - i * 2);
    await page.waitForTimeout(16);
  }
  await page.mouse.up();
  await page.waitForTimeout(600);
  report.orbit = await page.evaluate(() => (window as any).__rockhopMap3d.stats());
  await page.screenshot({ path: path.join(out, 'landscape-orbit.png') });

  const selections: { from: number; target: number; point: { x: number; y: number } | null; track: string | undefined; selected: number | undefined }[] = [];
  for (const from of [0, 5, 10]) {
    const target = from + 1;
    await page.evaluate(i => (window as any).__rockhopMap3d.selectStage(i, true), from);
    await page.waitForTimeout(850);
    const point = await page.evaluate(i => (window as any).__rockhopMap3d.towerScreenPoint(i), target) as { x: number; y: number } | null;
    if (point) await page.touchscreen.tap(point.x, point.y);
    await page.waitForTimeout(100);
    selections.push(await page.evaluate(({ from, target, point }) => ({
      from, target, point, track: document.querySelector('.wm3d-detail')?.getAttribute('data-track') ?? undefined,
      selected: (window as any).__rockhopMap3d?.stats()?.selected,
    }), { from, target, point }));
  }
  report.selections = selections;
  await page.screenshot({ path: path.join(out, 'landscape-selection.png') });
  const portrait = report.portrait as { rotate: string; prompt: string; canvas: number; host: string };
  const open = report.open as { canvas: number; rotate: string };
  const passed = open.canvas === 1 && open.rotate === 'none' && portrait.rotate === 'flex' && portrait.host === 'none' && portrait.canvas === 0 && portrait.prompt.includes('Rotate your phone') && selections.every(s => !!s.point && !!s.track && s.selected === s.target) && errors.length === 0;
  report.pass = passed;
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  if (!passed) process.exitCode = 1;
} catch (error) {
  report.failure = String(error);
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await context.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'played-map.webm'));
  await browser.close();
  await server.close();
  console.log(JSON.stringify(report, null, 2));
}
