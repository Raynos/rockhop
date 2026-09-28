/** Silent full-App finish route: real recorded C1 clear, career award, then Map destination. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { startServer } from '../lib/server';
import { launchBrowser } from '../lib/browser';

const rec = decodeJSON(fs.readFileSync('harness/inputs/c1-low-tide/bot-3.json', 'utf8'));
const inputs = expandFrames(rec);
const server = await startServer({ freeze: true });
console.log('finish-qa: frozen server ready');
const browser = await launchBrowser({ width: 852, height: 393 });
console.log(`finish-qa: ${browser.probe.renderer}`);
try {
  const page = browser.page;
  await page.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
  await page.goto(server.url, { waitUntil: 'commit' });
  console.log('finish-qa: navigated');
  await page.waitForFunction(() => window.__rockhop?.app?.screen() === 'menu' && !document.querySelector('#loader'), undefined, { timeout: 120_000 });
  console.log('finish-qa: menu');
  await page.evaluate(() => window.__rockhop!.app!.play('c1-low-tide'));
  console.log('finish-qa: play requested');
  await page.waitForFunction(() => window.__rockhop?.app?.screen() === 'run', undefined, { timeout: 20_000 });
  console.log('finish-qa: run');
  await page.evaluate((seed) => window.__rockhop!.loadTrack('c1-low-tide', seed), rec.header.seed);
  console.log('finish-qa: seeded track loaded');
  await page.evaluate(async () => {
    // The real renderer needs RAF while it prepares the course. Once entry is
    // ready, drain the already queued frame and let manual ticks own the run.
    window.requestAnimationFrame = () => 0;
    await new Promise((resolve) => setTimeout(resolve, 80));
  });
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  for (let i = 0; i < inputs.length; i += 600) {
    await page.evaluate((batch) => { const h=window.__rockhop!; for(const f of batch){h.setInput(f); h.step(1);} }, inputs.slice(i,i+600));
  }
  await page.evaluate(() => {
    const h = window.__rockhop!;
    for (let i = 0; i < 30; i++) { h.step(8); h.render(); }
  });
  const result = await page.evaluate(() => ({ phase: window.__rockhop!.phase(), screen: window.__rockhop!.app!.screen(), tag: document.querySelector('.fr-tag')?.textContent, earned: document.querySelector('.tk-reward')?.textContent, wallet: document.querySelector('.fr-wallet')?.textContent, medal: document.querySelector('.fr-medal-name')?.textContent, time: document.querySelector('.fr-time-row .time')?.textContent, buttons: [...document.querySelectorAll('.results .tile')].map(x => ({ id:(x as HTMLElement).dataset.id, disabled:(x as HTMLButtonElement).disabled })) }));
  fs.mkdirSync('docs/evidence/finish-remaster', { recursive: true });
  await page.screenshot({ path: 'docs/evidence/finish-remaster/production-live-c1.png', animations: 'disabled' });
  // Manual physics owns the recorded time, but the touch invariant uses wall
  // time. Poll its real reveal clock across the required 150 ms drawn interval,
  // then send a browser pointer through the visible Map tile.
  await page.evaluate(() => window.__rockhop!.app!.frame());
  await page.waitForTimeout(200);
  await page.evaluate(() => window.__rockhop!.app!.frame());
  const live = await page.locator('.results.live').count();
  if (!live) throw new Error('Results never became pointer-interactive');
  await page.locator('.results .tile[data-id="menu"]').click({ timeout: 5_000 });
  const afterMap = await page.evaluate(() => window.__rockhop!.app!.screen());
  fs.writeFileSync('docs/evidence/finish-remaster/production-live-c1.json', JSON.stringify({ ...result, afterMap, actionMethod: 'Playwright pointer click after reveal invariant' }, null, 2)+'\n');
  console.log(JSON.stringify({ ...result, afterMap }));
  if (result.phase !== 'finished' || result.tag !== 'NEW COURSE CLEAR' || result.earned !== '+300' || result.wallet !== '300' || result.medal !== 'Diamond' || result.time !== '0:30.350' || afterMap !== 'tracks') throw new Error('Production finish integration failed');
} finally {
  await browser.close();
  await server.close();
}
