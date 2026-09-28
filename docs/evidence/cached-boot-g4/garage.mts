/** Silent first Garage bike-swap check against an isolated release dist. */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, webkit } from 'playwright';
import { preview } from 'vite';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const distDir = process.env['BOOT_DIST'] ?? path.join(root, 'dist');
const engine = process.argv[2] ?? 'chromium';
if (engine !== 'chromium' && engine !== 'webkit') throw new Error('engine must be chromium or webkit');
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: distDir }, preview: { host: '127.0.0.1', port: 0 } });
const url = server.resolvedUrls?.local[0];
if (!url) throw new Error('preview URL unavailable');
const browser = await (engine === 'chromium' ? chromium : webkit).launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.sound', '0');
  // Existing Pro selection is grandfathered by CareerEconomy, which makes both
  // Garage chips available while exercising the same renderer swap path.
  localStorage.setItem('rockhop.bikeClass', 'pro');
});
const page = await context.newPage();
const pageErrors: string[] = [];
page.on('pageerror', error => pageErrors.push(error.message));

try {
  await page.goto(url);
  await page.waitForFunction(() => !document.getElementById('loader'), null, { timeout: 120000 });
  await page.locator('.menu-screen .menu-item[data-id="garage"]').click();
  await page.locator('.garage-screen.show').waitFor();
  await page.waitForFunction(() => (window as typeof window & { __render: { bikeDocumentClass: string | null; heroLoading: number } }).__render.heroLoading === 0, null, { timeout: 20000 });
  const initial = await page.evaluate(() => ({ installed: (window as typeof window & { __render: { bikeDocumentClass: string | null; debugInfo(): { heroSwap: { swaps: unknown[] } } } }).__render.bikeDocumentClass,
    swaps: (window as typeof window & { __render: { debugInfo(): { heroSwap: { swaps: unknown[] } } } }).__render.debugInfo().heroSwap.swaps.length,
    chips: [...document.querySelectorAll('.garage-screen .bike-chip')].map(el => ({ bike: (el as HTMLElement).dataset['bike'], disabled: (el as HTMLButtonElement).disabled, text: el.textContent })) }));
  console.log(JSON.stringify({ engine, initial }));
  const order = initial.installed === 'pro' ? ['rookie', 'pro'] as const : ['pro', 'rookie'] as const;
  for (const bike of order) {
    const before = await page.evaluate(() => (window as typeof window & { __render: { debugInfo(): { heroSwap: { swaps: unknown[] } } } }).__render.debugInfo().heroSwap.swaps.length);
    const startedAt = Date.now();
    await page.locator(`.garage-screen .bike-chip[data-bike="${bike}"]`).click();
    await page.waitForFunction(count => (window as typeof window & { __render: { debugInfo(): { heroSwap: { swaps: unknown[] } } } }).__render.debugInfo().heroSwap.swaps.length > count, before, { timeout: 20000 });
    const detail = await page.evaluate(() => ({ swaps: (window as typeof window & { __render: { debugInfo(): { heroSwap: { swaps: unknown[] } } } }).__render.debugInfo().heroSwap.swaps,
      installed: (window as typeof window & { __render: { bikeDocumentClass: string | null } }).__render.bikeDocumentClass,
      garageVisible: !!document.querySelector('.garage-screen.show') }));
    console.log(JSON.stringify({ engine, bike, wallMs: Date.now() - startedAt, swap: detail.swaps?.at(-1), installed: detail.installed,
      garageVisible: detail.garageVisible, pageErrors: [...pageErrors] }));
  }
} finally {
  await page.close();
  await browser.close();
  await new Promise<void>((resolve, reject) => server.httpServer.close(error => error ? reject(error) : resolve()));
}
