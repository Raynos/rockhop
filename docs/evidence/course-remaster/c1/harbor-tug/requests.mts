/** Compare normal-menu offline prefetch with a played C1 model decode. */
import { writeFileSync } from 'node:fs';
import { launchBrowser } from '../../../../../harness/lib/browser';
import { openGame } from '../../../../../harness/lib/hook';

const [outFile] = process.argv.slice(2);
const url = process.env.C1_CAPTURE_URL;
const sha = process.env.C1_CAPTURE_SHA;
if (!outFile || !url || !sha) throw new Error('C1_CAPTURE_URL=... C1_CAPTURE_SHA=... tsx requests.mts output.json');
const browser = await launchBrowser({ width: 852, height: 392, logConsole: false });
try {
  const page = browser.page;
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.addInitScript(() => {
    const original = XMLHttpRequest.prototype.open;
    const originalFetch = window.fetch.bind(window);
    const observed = window as typeof window & { __c1ModelXHR: string[]; __c1ModelFetch: string[]; __c1ModelFetchKind: string[]; __c1ModelFetchStack: string[] };
    observed.__c1ModelXHR = [];
    observed.__c1ModelFetch = [];
    observed.__c1ModelFetchKind = [];
    observed.__c1ModelFetchStack = [];
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
      if (String(url).includes('c1-harbor-tug')) {
        observed.__c1ModelXHR.push(`${method} ${url}`);
      }
      return original.call(this, method, url, ...rest);
    };
    window.fetch = (...args) => {
      const request = args[0];
      const target = typeof request === 'string' ? request : request instanceof URL ? request.href : request.url;
      if (target.includes('c1-harbor-tug')) {
        observed.__c1ModelFetch.push(target);
        observed.__c1ModelFetchKind.push(typeof request === 'string' ? 'string' : request instanceof URL ? 'URL' : 'Request');
        observed.__c1ModelFetchStack.push(new Error().stack ?? '');
      }
      return originalFetch(...args);
    };
  });
  const version = await page.request.get(new URL('/version.json', url).href).then((r) => r.json()) as { sha: string };
  if (version.sha !== sha) throw new Error(`frozen build mismatch: ${version.sha} != ${sha}`);
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => {
    const menu = document.querySelector('.menu-screen.show');
    const play = menu?.querySelector<HTMLButtonElement>('.menu-item[data-id="play"]');
    const loader = document.querySelector('#loader');
    const loading = loader && !loader.classList.contains('out') && getComputedStyle(loader).display !== 'none';
    return !!play && !play.disabled && !!play.getClientRects().length && !loading;
  }, undefined, { timeout: 40_000 });
  await page.waitForTimeout(350);
  const menuReady = await page.evaluate(() => ({
    menuShown: !!document.querySelector('.menu-screen.show .menu-item[data-id="play"]'),
    loader: document.querySelector('#loader')?.className ?? null,
  }));
  await page.locator('.menu-screen.show .menu-item[data-id="garage"]').click();
  await page.waitForSelector('.garage-screen.show');
  await page.waitForTimeout(500);
  await page.locator('.garage-screen.show .backbtn').click();
  await page.waitForSelector('.menu-screen.show .menu-item[data-id="play"]');
  const menu = await page.evaluate(() => ({
    xhr: (window as typeof window & { __c1ModelXHR: string[] }).__c1ModelXHR,
    fetch: (window as typeof window & { __c1ModelFetch: string[] }).__c1ModelFetch,
    fetchKind: (window as typeof window & { __c1ModelFetchKind: string[] }).__c1ModelFetchKind,
    fetchStack: (window as typeof window & { __c1ModelFetchStack: string[] }).__c1ModelFetchStack,
    resources: performance.getEntriesByType('resource').filter(e => e.name.includes('c1-harbor-tug')).map(e => e.name),
    title: document.title,
    hasCanvas: !!document.querySelector('canvas'),
  }));
  await openGame(page, url);
  const harnessBefore = await page.evaluate(() => ({
    xhr: (window as typeof window & { __c1ModelXHR: string[] }).__c1ModelXHR,
    fetch: (window as typeof window & { __c1ModelFetch: string[] }).__c1ModelFetch,
    fetchKind: (window as typeof window & { __c1ModelFetchKind: string[] }).__c1ModelFetchKind,
  }));
  const loaded = await page.evaluate(async () => {
    const game = window.__rockhop!;
    await game.loadTrack('c1-low-tide', 1);
    return { stats: game.stats(), info: game.info() };
  });
  await page.waitForTimeout(1000);
  const harnessAfter = await page.evaluate(() => ({
    xhr: (window as typeof window & { __c1ModelXHR: string[] }).__c1ModelXHR,
    fetch: (window as typeof window & { __c1ModelFetch: string[] }).__c1ModelFetch,
    fetchKind: (window as typeof window & { __c1ModelFetchKind: string[] }).__c1ModelFetchKind,
    fetchStack: (window as typeof window & { __c1ModelFetchStack: string[] }).__c1ModelFetchStack,
    resources: performance.getEntriesByType('resource').filter(e => e.name.includes('c1-harbor-tug')).map(e => e.name),
  }));
  const afterSwitch = await page.evaluate(async () => {
    const game = window.__rockhop!;
    await game.loadTrack('d1-dust-devil', 1);
    const render = game.info().render as Record<string, unknown> | null;
    return { enabled: render?.['courseAssetsEnabled'], mounted: render?.['courseAssetsMounted'], textureMB: render?.['courseAssetsTextureMB'] };
  });
  const loadedRender = loaded.info.render as Record<string, unknown> | null;
  const loadedAsset = { enabled: loadedRender?.['courseAssetsEnabled'], mounted: loadedRender?.['courseAssetsMounted'], textureMB: loadedRender?.['courseAssetsTextureMB'] };
  const report = { sha, renderer: browser.probe.renderer, menuReady, menu, harnessBefore, harnessAfter, loaded, afterSwitch, errors };
  writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n');
  console.log(outFile, 'menuFetch', menu.fetchKind, 'harnessBefore', harnessBefore.fetchKind,
    'harnessAfter', harnessAfter.fetchKind, 'errors', errors.length);
  if (!menuReady.menuShown || !menu.hasCanvas || !menu.fetchKind.length ||
    menu.fetchKind.some(kind => kind !== 'string') ||
    !harnessAfter.fetchKind.includes('Request') ||
    !loadedAsset?.enabled || loadedAsset.mounted !== 1 ||
    afterSwitch.enabled || afterSwitch.mounted !== 0 || errors.length) process.exitCode = 1;
} finally {
  await browser.close();
}
