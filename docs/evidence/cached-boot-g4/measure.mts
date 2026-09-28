/** Silent cached landscape boot in headless Chromium/WebKit. `BOOT_DIST=/absolute/dist pnpm exec tsx docs/evidence/cached-boot-g4/measure.mts chromium 3`. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { chromium, webkit } from 'playwright';
import { preview } from 'vite';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const distDir = process.env['BOOT_DIST'] ?? path.join(root, 'dist');
const engine = process.argv[2] ?? 'chromium';
if (engine !== 'chromium' && engine !== 'webkit') throw new Error('engine must be chromium or webkit');
const runs = Number(process.argv[3] ?? '3');
if (!Number.isInteger(runs) || runs < 1 || runs > 10) throw new Error('runs must be 1–10');
const htmlSha256 = createHash('sha256').update(fs.readFileSync(path.join(distDir, 'index.html'))).digest('hex');
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: distDir }, preview: { host: '127.0.0.1', port: 0 } });
const url = server.resolvedUrls?.local[0];
if (!url) throw new Error('preview URL unavailable');
const browser = await (engine === 'chromium' ? chromium : webkit).launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
await context.addInitScript({ path: path.join(root, 'docs/evidence/cached-boot-g4/instrument.js') });
const page = await context.newPage();
const pageErrors: string[] = [];
page.on('pageerror', e => pageErrors.push(e.message));

async function boot(label: string) {
  pageErrors.length = 0;
  const t0 = Date.now();
  await page.goto(url);
  await page.waitForFunction(() => !document.getElementById('loader'), null, { timeout: 120000 });
  const wallMs = Date.now() - t0;
  const detail = await page.evaluate(() => {
    const state = (window as typeof window & { __cachedBootG4: { firstScriptMs: number; download100Ms: number | null; setup100Ms: number | null; readyMs: number | null; rows: Record<string, number>; phases: unknown[] } }).__cachedBootG4;
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return { ...state, navigation: { responseEndMs: Math.round(nav.responseEnd), domContentLoadedMs: Math.round(nav.domContentLoadedEventEnd), transferSize: nav.transferSize },
      marks: performance.getEntriesByType('mark').filter(m => m.name.startsWith('render:')).map(m => ({ name: m.name, ms: Math.round(m.startTime) })),
      serviceWorkerControlled: !!navigator.serviceWorker.controller, canvasPresent: !!document.querySelector('canvas'), menuVisible: !!document.querySelector('#ui .menu-screen.show') };
  });
  const postBytes100Ms = detail.readyMs !== null && detail.download100Ms !== null ? detail.readyMs - detail.download100Ms : null;
  const phase = detail.rows;
  console.log(JSON.stringify({ engine, label, htmlSha256: htmlSha256.slice(0, 16), wallMs, postBytes100Ms, pageErrors: [...pageErrors], ...detail,
    shaderMs: phase['shaders'] !== undefined && phase['bootArt'] !== undefined ? phase['shaders'] - phase['bootArt'] : null,
    firstFrameMs: phase['firstFrame'] !== undefined && phase['shaders'] !== undefined ? phase['firstFrame'] - phase['shaders'] : null }));
}

try {
  await boot('cold-fill');
  for (let i = 1; i <= runs; i++) await boot(`warm-${i}`);
} finally {
  await page.close();
  await browser.close();
  await new Promise<void>((resolve, reject) => server.httpServer.close(err => err ? reject(err) : resolve()));
}
