/** Silent headless WebKit check of the live menu hero after loading has settled. */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { startServer } from '../lib/server';

const out = path.resolve(process.argv[2] ?? 'docs/evidence/menu-loader-audit/stable-hero');
fs.mkdirSync(out, { recursive: true });
const server = await startServer({ freeze: true, forceBuild: true });
const browser = await webkit.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, reducedMotion: 'no-preference', serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${server.url}?audio=0&sw=0`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !document.querySelector('#loader') && document.querySelector('.menu-keyart.loaded') && document.querySelector('.menu-screen.show'), null, { timeout: 120_000 });
  await page.waitForTimeout(1000);
  const sample = async (name: string) => {
    const state = await page.evaluate(() => {
      const hero = document.querySelector('.menu-keyart.loaded')!;
      const style = getComputedStyle(hero);
      const rect = hero.getBoundingClientRect();
      return { transform: style.transform, animationName: style.animationName, opacity: style.opacity, backgroundImage: style.backgroundImage, rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height } };
    });
    await page.screenshot({ path: path.join(out, `${name}.png`), clip: { x: 550, y: 50, width: 280, height: 240 } });
    return state;
  };
  const first = await sample('first');
  await page.waitForTimeout(2500);
  const second = await sample('second');
  const report = { geometry: '852x393@2', elapsedBetweenSamplesMs: 2500, first, second, errors, pass: first.animationName === 'none' && second.animationName === 'none' && first.transform === second.transform && JSON.stringify(first.rect) === JSON.stringify(second.rect) && errors.length === 0 };
  fs.writeFileSync(path.join(out, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  if (!report.pass) throw new Error('menu hero moved or page errored');
  await context.close();
} finally {
  await browser.close();
  await server.close();
}
