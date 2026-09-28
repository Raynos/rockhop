/** Headless, silent landscape startup probe. Run against the current dist with `pnpm exec tsx docs/evidence/cached-boot/measure.mts`. */
import { chromium, type Page } from 'playwright';
import { preview } from 'vite';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const distDir = process.env['BOOT_DIST'] ?? path.join(root, 'dist');
const indexBytes = fs.readFileSync(path.join(distDir, 'index.html'));
const fingerprint = createHash('sha256').update(indexBytes).digest('hex').slice(0, 16);
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: distDir }, preview: { host: '127.0.0.1', port: 0 } });
const url = server.resolvedUrls?.local[0];
if (!url) throw new Error('preview URL missing');
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, serviceWorkers: process.argv.includes('--sw-off') ? 'block' : 'allow',
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
await context.addInitScript({ path: path.join(root, 'docs/evidence/cached-boot/instrument.js') });
let page: Page | null = null;

async function run(label: string, offline = false, skipSwBoot = false) {
  await context.setOffline(offline);
  if (!page || process.argv.includes('--new-tab')) {
    if (page) await page.close();
    page = await context.newPage();
  }
  const active = page;
  const errors: string[] = [];
  active.on('pageerror', e => errors.push(e.message));
  const t0 = Date.now();
  await active.goto(url + (skipSwBoot || process.argv.includes('--sw-off') ? '?sw=0' : ''));
  await active.waitForFunction(() => !document.getElementById('loader'), null, { timeout: 90000 });
  const wall = Date.now() - t0;
  const result = await active.evaluate(() => {
    const probe = (window as typeof window & { __bootProbe: { end: number; rows: Record<string, number>; phases: { t: number; label: string }[] } }).__bootProbe;
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return { ...probe, navigation: { workerStart: Math.round(nav.workerStart), fetchStart: Math.round(nav.fetchStart), responseStart: Math.round(nav.responseStart), responseEnd: Math.round(nav.responseEnd), domContentLoaded: Math.round(nav.domContentLoadedEventEnd), transferSize: nav.transferSize }, marks: performance.getEntriesByType('mark').filter(m => m.name.startsWith('render:')).map(m => ({ name: m.name, t: Math.round(m.startTime) })),
      hero: !!document.querySelector('canvas'), controlled: !!navigator.serviceWorker.controller, screen: document.querySelector('#ui .screen.show')?.className ?? '' };
  });
  console.log(JSON.stringify({ label, wall, fingerprint, errors, ...result }));
}

try {
  const repeats = Number(process.argv.find(a => a.startsWith('--repeat='))?.split('=')[1] ?? 3);
  await run('cold-online');
  // First visit installs and fills the worker; all later visits share this context and its Cache Storage.
  for (let i = 0; i < repeats; i++) await run(`cached-online-${i + 1}`);
  if (!process.argv.includes('--online-only')) {
    for (let i = 0; i < repeats; i++) await run(`cached-origin-down-${i + 1}`, true);
    if (repeats) await run('cached-origin-down-skip-sw-boot', true, true);
  }
  if (process.argv.includes('--trailing-simple') && page) {
    const t0 = Date.now();
    await page.goto(url + 'offline.html');
    const simple = await page.evaluate(() => ({ initT: (window as typeof window & { __bootProbe: { initT: number } }).__bootProbe?.initT,
      nav: performance.getEntriesByType('navigation').map(e => ({ responseEnd: Math.round((e as PerformanceNavigationTiming).responseEnd), dcl: Math.round((e as PerformanceNavigationTiming).domContentLoadedEventEnd) })) }));
    console.log(JSON.stringify({ label: 'trailing-simple-page', wall: Date.now() - t0, fingerprint, ...simple }));
  }
} finally {
  await page?.close();
  await browser.close();
  await new Promise<void>((resolve, reject) => server.httpServer.close(err => err ? reject(err) : resolve()));
}
