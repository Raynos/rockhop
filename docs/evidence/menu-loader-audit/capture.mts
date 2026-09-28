/** Silent production-preview menu/loader capture. Run: pnpm exec tsx docs/evidence/menu-loader-audit/capture.mts */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { chromium, webkit, type Browser, type Page } from 'playwright';
import { startServer } from '../../../harness/lib/server';

const arg = (name: string) => process.argv.find((x) => x.startsWith(`--${name}=`))?.slice(name.length + 3);
const out = path.resolve(arg('out') ?? path.dirname(new URL(import.meta.url).pathname));
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true, forceBuild: process.argv.includes('--build') });
const modes = [
  { engine: 'webkit', w: 932, h: 430, dpr: 2 },
  { engine: 'webkit', w: 430, h: 932, dpr: 2 },
  { engine: 'chromium', w: 932, h: 430, dpr: 2 },
  { engine: 'chromium', w: 430, h: 932, dpr: 2 },
] as const;

type Run = { engine: string; geometry: string; cache: string; elapsedMs: number; result: string; data: unknown; errors: string[]; video: string };
const rows: Run[] = [];

async function measure(page: Page, engine: string, geometry: string, cache: string): Promise<void> {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.addInitScript({ content: `(() => {
    const records = [];
    window.__audit = records;
    const box = (selector) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return { x: +r.x.toFixed(2), y: +r.y.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2), display: s.display, opacity: +s.opacity, background: s.backgroundImage, text: (el.textContent ?? '').trim().slice(0, 100) };
    };
    let last = -100;
    const tick = (now) => {
      if (now - last >= 30 && records.length < 500) {
        last = now;
        records.push({ t: +now.toFixed(1), inner: [innerWidth, innerHeight], visual: [visualViewport?.width, visualViewport?.height], loader: box('#loader'), badge: box('#loader .badge'), gauges: box('#loader .gauges'), dial: box('#loader .dial'), detail: box('#loader .line'), row: box('#loader .row'), turn: box('#loader .turn'), menu: box('.menu-screen'), keyart: box('.menu-keyart'), rotate: box('.rotate.armed') });
      }
      if (records.length < 500) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  })();` });
  const start = Date.now();
  await page.goto(server.url, { waitUntil: 'domcontentloaded', timeout: 120_000 });
  await page.waitForTimeout(350);
  if (await page.locator('#loader').count()) await page.screenshot({ path: path.join(out, `${engine}-${geometry}-${cache}-loading.png`) });
  let result = 'menu';
  try {
    await page.waitForFunction(() => !document.querySelector('#loader') && !!document.querySelector('.menu-screen.show'), null, { timeout: 120_000 });
  } catch {
    result = 'timeout';
  }
  const elapsedMs = Date.now() - start;
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(out, `${engine}-${geometry}-${cache}-end.png`) });
  const data = await page.evaluate(`(() => {
    const rect = (el) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: +r.x.toFixed(2), y: +r.y.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2), cx: +(r.x + r.width / 2).toFixed(2), cy: +(r.y + r.height / 2).toFixed(2) };
    };
    const keyart = document.querySelector('.menu-keyart');
    return { timeline: window.__audit ?? [], ready: performance.now(), nav: performance.getEntriesByType('navigation').map((n) => ({ duration: n.duration, startTime: n.startTime })), screen: { innerWidth, innerHeight, dpr: devicePixelRatio, visualWidth: visualViewport?.width, visualHeight: visualViewport?.height }, loaderExists: !!document.querySelector('#loader'), menuVisible: !!document.querySelector('.menu-screen.show'), rotateDisplay: getComputedStyle(document.querySelector('.rotate.armed')).display, rotateText: document.querySelector('.rotate.armed')?.textContent, heroBackground: keyart ? getComputedStyle(keyart).backgroundImage : null, heroLoaded: keyart?.classList.contains('loaded'), cards: [...document.querySelectorAll('.menu-screen .menu-item')].map((el) => ({ id: el.dataset.id, text: el.textContent?.trim(), rect: rect(el), icon: rect(el.querySelector('.ico')), word: rect(el.querySelector('.label,span:not(.ico)')) })), band: rect(document.querySelector('.menu-band')), wordmark: rect(document.querySelector('.menu-wordmark')), pageText: document.body.textContent?.slice(0, 300) };
  })()`);
  rows.push({ engine, geometry, cache, elapsedMs, result, data, errors, video: `${engine}-${geometry}-${cache}.mp4` });
}

try {
  for (const m of modes) {
    const browser: Browser = m.engine === 'webkit' ? await webkit.launch({ headless: true }) : await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--mute-audio'] });
    const geometry = `${m.w}x${m.h}`;
    const context = await browser.newContext({ viewport: { width: m.w, height: m.h }, deviceScaleFactor: m.dpr, isMobile: true, hasTouch: true, recordVideo: { dir: out, size: { width: m.w, height: m.h } }, serviceWorkers: 'allow' });
    for (const cache of ['cold', 'warm']) {
      const page = await context.newPage();
      await measure(page, m.engine, geometry, cache);
      const video = page.video();
      await page.close();
      if (video) {
        const raw = await video.path();
        const copy = path.join(out, `${m.engine}-${geometry}-${cache}.webm`);
        const mp4 = path.join(out, `${m.engine}-${geometry}-${cache}.mp4`);
        await video.saveAs(copy);
        const ffmpeg = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', copy, '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4], { encoding: 'utf8' });
        if (ffmpeg.status !== 0) throw new Error(`ffmpeg failed: ${ffmpeg.stderr}`);
        fs.rmSync(raw);
        fs.rmSync(copy);
      }
    }
    await context.close();
    await browser.close();
    fs.writeFileSync(path.join(out, 'measurements.json'), JSON.stringify({ url: server.url, rows }, null, 2));
  }
} finally {
  await server.close();
}
console.log(rows.map(({ engine, geometry, cache, elapsedMs, result, errors }) => ({ engine, geometry, cache, elapsedMs, result, errors })));
