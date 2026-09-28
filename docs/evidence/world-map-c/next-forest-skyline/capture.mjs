/* Silent, played performance capture of the real opt-in C selector.
   Usage: node capture.mjs <url> <output-directory> [--taps]
   Input drags the island; camera positions are never assigned. */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const url = process.argv[2] || 'http://127.0.0.1:5194/?map3d=1&sw=0';
const out = path.resolve(process.argv[3] || 'docs/evidence/world-map-c/performance-pass/before');
const tapAll = process.argv.includes('--taps');
const record = !process.argv.includes('--no-video');
fs.mkdirSync(out, { recursive: true });
const angle = process.argv.find(value => value.startsWith('--angle='))?.split('=')[1] || 'swiftshader';
const browser = await chromium.launch({ headless: true, args: [`--use-angle=${angle}`, '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const context = await browser.newContext({
  viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  ...(record ? { recordVideo: { dir: out, size: { width: 852, height: 393 } } } : {}),
});
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const video = record ? page.video() : null;
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const samples = [];
const selections = [];

try {
  await page.goto(url);
  await page.waitForFunction(() => !!document.querySelector('.menu-screen.live'), null, { timeout: 120000 });
  await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
  await page.waitForFunction(() => document.querySelector('.wm3d-host')?.dataset.ready === '1' && !!window.__rockhopMap3d, null, { timeout: 60000 });
  await page.evaluate(() => {
    const intervals = [];
    let last = 0;
    function tick(now) { if (last) intervals.push(now - last); last = now; requestAnimationFrame(tick); }
    requestAnimationFrame(tick);
    window.__mapPerfIntervals = intervals;
  });
  async function sample(name) {
    const data = await page.evaluate(() => ({ stats: window.__rockhopMap3d.stats(), frameIntervals: window.__mapPerfIntervals.splice(0) }));
    if (record) await page.screenshot({ path: path.join(out, `${name}.png`) });
    const times = data.frameIntervals.filter(value => value > 0).sort((a, b) => a - b);
    const percentile = p => times.length ? Math.round(times[Math.floor((times.length - 1) * p)] * 10) / 10 : null;
    samples.push({ name, stats: data.stats, frames: times.length, frameMsMedian: percentile(.5), frameMsP95: percentile(.95), frameMsMax: percentile(1) });
  }
  await page.waitForTimeout(3000);
  await sample('front');
  const cdp = await context.newCDPSession(page);
  const x0 = 650, y = 181;
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y, id: 0 }] });
  for (let step = 1; step <= 48; step++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x0 - step * 7.5, y, id: 0 }] });
    if (step % 12 === 0) await sample(step === 12 ? 'three-quarter' : step === 36 ? 'reverse' : `orbit-${step / 12}`);
    await page.waitForTimeout(32);
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await page.waitForTimeout(1300);
  await sample('settled');
  if (tapAll) for (let i = 0; i < 12; i++) {
    await page.evaluate(index => window.__rockhopMap3d.selectStage(index, true), i);
    await page.waitForTimeout(800);
    const point = await page.evaluate(index => window.__rockhopMap3d.towerScreenPoint(index), i);
    if (point) await page.touchscreen.tap(point.x, point.y);
    selections.push(await page.evaluate(() => document.querySelector('.wm3d-detail')?.dataset.track));
  }
  const backend = await page.evaluate(() => {
    const gl = document.querySelector('.wm3d-host canvas')?.getContext('webgl2');
    const ext = gl?.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl?.getParameter(gl.RENDERER) || null;
  });
  const report = { url, viewport: '852x393', dpr: 2, angle, backend, samples, selections, errors };
  fs.writeFileSync(path.join(out, 'measurements.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally {
  await context.close();
  if (video) {
    const source = await video.path();
    fs.copyFileSync(source, path.join(out, 'played-orbit.webm'));
    fs.unlinkSync(source);
  }
  await browser.close();
}
