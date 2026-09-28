/** Silent full-App pointer check for all four production result actions. */
import fs from 'node:fs';
import type { Page } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { startServer } from '../lib/server';
import { launchBrowser } from '../lib/browser';

const rec = decodeJSON(fs.readFileSync('harness/inputs/c1-low-tide/bot-3.json', 'utf8'));
const inputs = expandFrames(rec);
const server = await startServer({ freeze: true });
const browser = await launchBrowser({ width: 852, height: 393 });
const results: Array<{ action: string; liveBefore: boolean; enabled: boolean; screen: string; phase: string; trackId: string; liveAfter: boolean }> = [];

async function finish(page: Page): Promise<void> {
  await page.evaluate(() => window.__rockhop!.app!.play('c1-low-tide'));
  await page.waitForFunction(() => window.__rockhop?.app?.screen() === 'run', undefined, { timeout: 20_000 });
  await page.evaluate((seed) => window.__rockhop!.loadTrack('c1-low-tide', seed), rec.header.seed);
  // Track preparation gets native RAF. Once ready, only the recorded 120 Hz
  // frames may advance the physics clock.
  await page.evaluate(async () => {
    window.requestAnimationFrame = () => 0;
    await new Promise((resolve) => setTimeout(resolve, 80));
  });
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  for (let i = 0; i < inputs.length; i += 600) {
    await page.evaluate((batch) => { const h = window.__rockhop!; for (const f of batch) { h.setInput(f); h.step(1); } }, inputs.slice(i, i + 600));
  }
  await page.evaluate(() => {
    const h = window.__rockhop!;
    for (let i = 0; i < 30; i++) { h.step(8); h.render(); }
  });
  // Wait for the CSS tile rise to become visibly opaque, then start the
  // invariant's 150 ms drawn clock. App.frame polls the same watcher as RAF.
  await page.waitForTimeout(350);
  await page.evaluate(() => window.__rockhop!.app!.frame());
  await page.waitForTimeout(200);
  await page.evaluate(() => window.__rockhop!.app!.frame());
  await page.locator('.results.live').waitFor({ state: 'visible', timeout: 5_000 });
}

try {
  const page = browser.page;
  await page.addInitScript(() => {
    localStorage.setItem('rockhop.onboarded', '1');
    (window as typeof window & { __nativeRaf: typeof requestAnimationFrame }).__nativeRaf = window.requestAnimationFrame.bind(window);
  });
  await page.goto(server.url, { waitUntil: 'commit' });
  await page.waitForFunction(() => window.__rockhop?.app?.screen() === 'menu' && !document.querySelector('#loader'), undefined, { timeout: 120_000 });

  // Map is last because the track-select fly-up requires the live App RAF to
  // retire its overlay; this harness deliberately stops that loop for exact
  // recorded physics time.
  for (const action of ['replay', 'retry', 'next', 'menu'] as const) {
    await finish(page);
    const tile = page.locator(`.results .tile[data-id="${action}"]`);
    const liveBefore = await page.locator('.results.live').count() === 1;
    const enabled = await tile.isEnabled();
    if (!enabled) throw new Error(`${action} disabled on a finished C1 run`);
    await tile.click({ timeout: 5_000 });
    const actual = await page.evaluate(() => ({
      screen: window.__rockhop!.app!.screen(),
      phase: window.__rockhop!.phase(),
      trackId: window.__rockhop!.info().trackId,
      liveAfter: document.querySelector('.results')?.classList.contains('live') ?? false,
    }));
    results.push({ action, liveBefore, enabled, ...actual });
    const expectedScreen = action === 'menu' ? 'tracks' : action === 'replay' ? 'replay' : 'run';
    if (actual.screen !== expectedScreen) throw new Error(`${action} routed to ${actual.screen}; expected ${expectedScreen}`);
    if (action === 'retry' && (actual.phase !== 'countdown' || actual.trackId !== 'c1-low-tide')) throw new Error('Retry did not reset C1');
    if (action === 'next' && actual.trackId === 'c1-low-tide') throw new Error('Next did not load C2');
    await page.evaluate(() => { window.requestAnimationFrame = (window as typeof window & { __nativeRaf: typeof requestAnimationFrame }).__nativeRaf; });
    console.log(`${action}: ${actual.screen} / ${actual.phase} / ${actual.trackId}`);
  }
  fs.mkdirSync('docs/evidence/finish-remaster', { recursive: true });
  fs.writeFileSync('docs/evidence/finish-remaster/production-actions.json', JSON.stringify({ renderer: browser.probe.renderer, viewport: [852, 393], actions: results }, null, 2) + '\n');
} finally {
  await browser.close();
  await server.close();
}
