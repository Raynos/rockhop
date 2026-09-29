/** Silent, played phone-landscape gate for the selected command-strip map HUD. */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

const out = path.resolve(REPO_ROOT, process.argv[2] ?? 'harness/out/worldmap-hud-webkit');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true, forceBuild: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: { width: 852, height: 393 } },
});
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1');
  const medals = [
    ['c1-low-tide', 'gold'],
    ['c2-crane-hop', 'silver'],
    ['c3-hull-breach', 'bronze'],
  ];
  for (const [id, medal] of medals) localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 40, faults: 0, medal }));
});
const page = await context.newPage();
const video = page.video();
const errors: string[] = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const report: Record<string, unknown> = { engine: 'headless WebKit', viewport: '852×393', errors };

async function geometry() {
  return page.evaluate(() => {
    const keys = ['.wm-progress', '.wm-previous', '.wm-ride', '.wm-next', '.wm-levels', '.wm-quick', '.wm-orbit', '.backbtn'];
    return Object.fromEntries(keys.map(key => {
      const r = document.querySelector(key)!.getBoundingClientRect();
      return [key, { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom }];
    }));
  });
}

function controlsFit(g: Record<string, { x: number; y: number; width: number; height: number; right: number; bottom: number }>, width: number, height: number): boolean {
  const keys = ['.wm-previous', '.wm-ride', '.wm-next', '.wm-levels', '.wm-quick', '.wm-orbit', '.backbtn'];
  const inside = keys.every(key => {
    const r = g[key]!;
    return r.width >= 44 && r.height >= 44 && r.x >= 0 && r.y >= 0 && r.right <= width && r.bottom <= height;
  });
  const dock = keys.slice(0, 5).map(key => g[key]!);
  return inside && dock.every((r, i) => i === 0 || dock[i - 1]!.right <= r.x);
}

try {
  await page.goto(`${server.url}?sw=0`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.menu-screen.live', { timeout: 120_000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1', null, { timeout: 60_000 });
  await page.waitForTimeout(600);
  report.first = await page.evaluate(() => ({
    cleared: document.querySelector('.wm-progress')?.textContent,
    selected: document.querySelector('.wm3d-detail')?.getAttribute('data-track'),
    quick: document.querySelector('.wm-quick')?.getAttribute('aria-label'),
    image: document.querySelector('.wm-ride img')?.getAttribute('src'),
  }));
  report.geometry852 = await geometry();
  await page.screenshot({ path: path.join(out, 'command-strip-852x393.png') });
  await page.setViewportSize({ width: 667, height: 375 });
  await page.waitForTimeout(200);
  report.geometry667 = await geometry();
  await page.screenshot({ path: path.join(out, 'command-strip-667x375.png') });
  await page.setViewportSize({ width: 852, height: 393 });
  await page.waitForTimeout(200);

  await page.locator('.wm-next').click();
  report.nextSelected = await page.locator('.wm3d-detail').getAttribute('data-track');
  await page.locator('.wm-previous').click();
  report.previousSelected = await page.locator('.wm3d-detail').getAttribute('data-track');
  await page.locator('.wm-levels').click();
  report.levels = await page.locator('.wm-level-grid .wm-level').count();
  await page.screenshot({ path: path.join(out, 'twelve-level-picker.png') });
  await page.locator('.wm-level[data-index="6"]').click();
  report.locked = await page.evaluate(() => ({
    selected: document.querySelector('.wm3d-detail')?.getAttribute('data-track'),
    rideDisabled: (document.querySelector('.wm-ride') as HTMLButtonElement)?.disabled,
    rule: document.querySelector('.wm-ride .rule')?.textContent,
    quick: document.querySelector('.wm-quick')?.getAttribute('aria-label'),
  }));
  await page.screenshot({ path: path.join(out, 'locked-stop-play-next.png') });
  report.geometryPass = controlsFit(report.geometry852 as Awaited<ReturnType<typeof geometry>>, 852, 393) &&
    controlsFit(report.geometry667 as Awaited<ReturnType<typeof geometry>>, 667, 375);
  await page.locator('.wm-quick').click();
  await page.waitForFunction(() => (window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() === 'run', null, { timeout: 60_000 });
  report.play = await page.evaluate(() => ({
    screen: (window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen(),
    mapCanvases: document.querySelectorAll('.wm3d-host canvas').length,
    title: document.querySelector('.run-screen.live')?.textContent?.slice(0, 200),
  }));
  const first = report.first as { cleared: string; selected: string; quick: string; image: string };
  const locked = report.locked as { selected: string; rideDisabled: boolean; rule: string; quick: string };
  const play = report.play as { screen: string; mapCanvases: number };
  report.pass = first.cleared.includes('3 / 12 cleared') && first.selected === 'a1-sawdust' &&
    first.quick.includes('A1 Sawdust') && first.image.includes('a1-sawdust.webp') &&
    report.nextSelected === 'a2-log-jam' && report.previousSelected === 'a1-sawdust' && report.levels === 12 &&
    locked.selected === 'd1-dust-devil' && locked.rideDisabled && locked.rule.includes('Medal every Alpine track') &&
    locked.quick.includes('A1 Sawdust') && report.geometryPass === true &&
    play.screen === 'run' && play.mapCanvases === 0 && errors.length === 0;
  if (!report.pass) process.exitCode = 1;
} catch (error) {
  report.failure = String(error);
  process.exitCode = 1;
} finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2));
  await context.close();
  if (video) fs.renameSync(await video.path(), path.join(out, 'played-map-hud.webm'));
  await browser.close();
  await server.close();
  console.log(JSON.stringify({ pass: report.pass, failure: report.failure, first: report.first, nextSelected: report.nextSelected, previousSelected: report.previousSelected, locked: report.locked, levels: report.levels, geometryPass: report.geometryPass, play: report.play, errors }, null, 2));
}
