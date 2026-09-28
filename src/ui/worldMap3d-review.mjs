/* Silent headless played review of the opt-in island selector. */
/* oxlint-disable no-undef -- Playwright evaluate callbacks execute in the browser. */
import fs from 'node:fs';
import { chromium } from 'playwright';

const out = '/tmp/rockhop-world-map-3d-review';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const context = await browser.newContext({ viewport: { width: 932, height: 430 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, recordVideo: { dir: out, size: { width: 932, height: 430 } } });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const playedVideo = page.video();
const errors = [];
const report = {};
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('pageerror', error => errors.push(error.message));

try {
  await page.goto('http://127.0.0.1:5173/?map3d=1&sw=0');
  await page.waitForFunction(() => !!document.querySelector('.menu-screen.live'), null, { timeout: 120000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.dataset.ready === '1' && !!window.__rockhopMap3d, null, { timeout: 30000 });
  await page.waitForTimeout(1000);
  const open = await page.evaluate(() => ({ stats: window.__rockhopMap3d?.stats(), detail: document.querySelector('.wm3d-detail')?.textContent, markers: document.querySelectorAll('.wm-marker').length }));
  report.open = open;
  await page.screenshot({ path: `${out}/front.png` });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(250);
  const portrait = await page.evaluate(() => ({ rotate: getComputedStyle(document.querySelector('.wm3d-rotate')).display, canvas: document.querySelectorAll('.wm3d-host canvas').length }));
  report.portrait = portrait;
  await page.screenshot({ path: `${out}/portrait.png` });
  await page.setViewportSize({ width: 932, height: 430 });
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.dataset.ready === '1' && !!window.__rockhopMap3d, null, { timeout: 30000 });
  const cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 600, y: 185, id: 0 }] });
  for (let step = 1; step <= 30; step++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 600 - step * 10, y: 185, id: 0 }] });
    await page.waitForTimeout(16);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(800);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 600, y: 185, id: 0 }] });
  for (let step = 1; step <= 30; step++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 600 - step * 10, y: 185, id: 0 }] });
    await page.waitForTimeout(16);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(800);
  await page.waitForFunction(() => !!window.__rockhopMap3d, null, { timeout: 30000 });
  const selected = [];
  for (let index = 0; index < 12; index++) {
    const point = await page.evaluate(i => { window.__rockhopMap3d.selectStage(i, true); return window.__rockhopMap3d.towerScreenPoint(i); }, index);
    await page.waitForTimeout(900);
    const settled = await page.evaluate(i => window.__rockhopMap3d.towerScreenPoint(i), index);
    const p = settled ?? point;
    if (p) await page.touchscreen.tap(p.x, p.y);
    selected.push(await page.evaluate(() => ({ id: document.querySelector('.wm3d-detail')?.dataset.track, stats: window.__rockhopMap3d.stats() })));
  }
  report.selected = selected;
  console.log(JSON.stringify({ open, portrait, selected, errors, out }));
  await page.locator('.worldmap-screen.live .backbtn').click();
  await page.waitForFunction(() => !!document.querySelector('.menu-screen.live'), null, { timeout: 10000 });
  const afterMenu = await page.evaluate(() => ({ canvas: document.querySelectorAll('.wm3d-host canvas').length, hook: !!window.__rockhopMap3d }));
  report.afterMenu = afterMenu;
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.dataset.ready === '1', null, { timeout: 30000 });
  await page.evaluate(() => window.__rockhopMap3d.selectStage(0, true));
  await page.waitForTimeout(1200);
  const c1 = await page.evaluate(() => window.__rockhopMap3d.towerScreenPoint(0));
  if (c1) await page.touchscreen.tap(c1.x, c1.y);
  await page.waitForTimeout(500);
  const beforeRide = await page.evaluate(() => ({ track: document.querySelector('.wm3d-detail')?.dataset.track, rideDisabled: document.querySelector('.wm-ride')?.disabled }));
  report.beforeRide = beforeRide;
  if (!beforeRide.rideDisabled) await page.locator('.wm-ride').click();
  await page.waitForFunction(() => window.__rockhop?.app?.screen?.() === 'run', null, { timeout: 20000 });
  await page.waitForTimeout(700);
  const afterRide = await page.evaluate(() => ({ screen: window.__rockhop.app.screen(), canvas: document.querySelectorAll('.wm3d-host canvas').length, hook: !!window.__rockhopMap3d }));
  report.afterRide = afterRide;
  console.log(JSON.stringify({ afterMenu, beforeRide, afterRide, errors, out }));
  const plain = await context.newPage();
  const mapRequests = [];
  plain.on('request', request => { if (request.url().includes('worldMap3dScene')) mapRequests.push(request.url()); });
  await plain.goto('http://127.0.0.1:5173/?sw=0');
  await plain.waitForFunction(() => !document.getElementById('loader'), null, { timeout: 180000 });
  await plain.waitForFunction(() => !!document.querySelector('.menu-screen.live'), null, { timeout: 120000 });
  await plain.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await plain.waitForFunction(() => !!document.querySelector('.worldmap-screen.live'), null, { timeout: 20000 });
  report.default3dRequests = mapRequests.length;
  report.defaultPaintedVisible = await plain.locator('.wm-view').isVisible();
  report.errors = errors;
  fs.writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ default3dRequests: mapRequests.length, defaultPaintedVisible: await plain.locator('.wm-view').isVisible() }));
} finally {
  await context.close();
  if (playedVideo) fs.copyFileSync(await playedVideo.path(), `${out}/integrated-play.webm`);
  await browser.close();
}
