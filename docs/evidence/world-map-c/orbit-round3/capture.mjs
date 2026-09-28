/* Silent, played orbit of the real dev-only selector. Usage:
   node docs/evidence/world-map-c/orbit-round3/capture.mjs baseline|revised [port] [dpr]
   A drag, not a camera assignment, drives every review angle. */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const label = process.argv[2] || 'revised';
const port = Number(process.argv[3] || 5184);
const dpr = Number(process.argv[4] || 1);
const tapAll = process.argv.includes('--taps');
const out = path.resolve('docs/evidence/world-map-c/orbit-round3', label);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const context = await browser.newContext({
  viewport: { width: 932, height: 430 }, deviceScaleFactor: dpr, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: { width: 932, height: 430 } },
});
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const video = page.video();
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });

try {
  await page.goto(`http://127.0.0.1:${port}/?map3d=1&sw=0`);
  await page.waitForFunction(() => !!document.querySelector('.menu-screen.live'), null, { timeout: 120000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.dataset.ready === '1' && !!window.__rockhopMap3d, null, { timeout: 60000 });
  await page.waitForTimeout(800);
  const cdp = await context.newCDPSession(page);
  const samples = [];
  async function sample(name) {
    const data = await page.evaluate(() => ({ stats: window.__rockhopMap3d.stats(), markers: document.querySelectorAll('.wm-marker').length }));
    await page.screenshot({ path: path.join(out, `${name}.png`) });
    samples.push({ name, ...data });
  }
  await sample('front');
  const x0 = 725, y = 181;
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y, id: 0 }] });
  for (let step = 1; step <= 48; step++) {
    const x = x0 - step * 7.5;
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y, id: 0 }] });
    if (step % 12 === 0) await sample(`orbit-${step / 12}`);
    await page.waitForTimeout(32);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(450);
  await sample('settled');
  const selections = [];
  if (tapAll) for (let index = 0; index < 12; index++) {
    await page.evaluate(i => window.__rockhopMap3d.selectStage(i, true), index);
    await page.waitForTimeout(800);
    const point = await page.evaluate(i => window.__rockhopMap3d.towerScreenPoint(i), index);
    if (point) await page.touchscreen.tap(point.x, point.y);
    selections.push(await page.evaluate(() => document.querySelector('.wm3d-detail')?.dataset.track));
  }
  fs.writeFileSync(path.join(out, 'measurements.json'), JSON.stringify({ dpr, samples, selections, errors }, null, 2));
} finally {
  await context.close();
  if (video) {
    const source = await video.path();
    fs.copyFileSync(source, path.join(out, 'played-orbit.webm'));
    fs.unlinkSync(source);
  }
  await browser.close();
}
