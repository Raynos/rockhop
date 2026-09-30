/** Silent 852×393 landscape phone check of the always-visible frame meter and its tap-to-toggle details. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
import { startServer } from '../lib/server';

const server = await startServer({ freeze: true });
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
const page = await context.newPage();
const out = path.join(process.cwd(), 'harness', 'out', 'perf-panel');
fs.mkdirSync(out, { recursive: true });
const errors: string[] = [];
page.on('pageerror', (error) => errors.push(error.message));
try {
  await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
  await page.goto(`${server.url}/?sw=0&audio=0&track=c1-low-tide`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.getElementById('loader') === null, null, { timeout: 120_000 });
  const pill = page.locator('.fpsmeter');
  const panel = page.locator('.perf');
  await pill.waitFor({ state: 'visible', timeout: 30_000 });
  await page.waitForFunction(() => /\d+ fps/.test(document.querySelector('.fpsmeter')?.textContent ?? ''), null, { timeout: 10_000 });
  assert.equal(await pill.getAttribute('aria-expanded'), 'false');
  assert.equal(await panel.isHidden(), true);
  const pillBox = await pill.boundingBox();
  assert.ok(pillBox && pillBox.height >= 44 && pillBox.width >= 44, `touch target ${JSON.stringify(pillBox)}`);
  const restartBox = await page.locator('.tz-restart').boundingBox();
  assert.ok(!restartBox || pillBox.y >= restartBox.y + restartBox.height || pillBox.x + pillBox.width <= restartBox.x,
    `FPS pill overlaps restart: ${JSON.stringify({ pillBox, restartBox })}`);
  await page.screenshot({ path: path.join(out, 'closed.png') });
  await pill.click();
  await panel.waitFor({ state: 'visible' });
  await page.waitForFunction(() => /DRAW \d+ calls/.test(document.querySelector('.perf')?.textContent ?? ''), null, { timeout: 10_000 });
  assert.equal(await pill.getAttribute('aria-expanded'), 'true');
  const details = await panel.textContent();
  for (const label of ['FPS', 'PHYS', 'DRAW', 'RENDER', 'shadow', 'skipped']) assert.ok(details?.includes(label), label);
  await page.screenshot({ path: path.join(out, 'open.png') });
  await pill.click();
  assert.equal(await pill.getAttribute('aria-expanded'), 'false');
  assert.equal(await panel.isHidden(), true);
  assert.deepEqual(errors, []);
  await context.close();

  const desktop = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await desktop.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
  const desktopPage = await desktop.newPage();
  await desktopPage.goto(`${server.url}/?sw=0&audio=0&track=c1-low-tide`, { waitUntil: 'domcontentloaded' });
  await desktopPage.waitForFunction(() => document.getElementById('loader') === null, null, { timeout: 120_000 });
  const desktopPill = desktopPage.locator('.fpsmeter');
  await desktopPill.waitFor({ state: 'visible' });
  await desktopPill.click();
  await desktopPage.locator('.perf').waitFor({ state: 'visible' });
  await desktopPage.screenshot({ path: path.join(out, 'desktop-open.png') });
  await desktopPill.click();
  assert.equal(await desktopPage.locator('.perf').isHidden(), true);
  await desktop.close();
  console.log(`PASS phone landscape FPS pill ${pillBox.width}×${pillBox.height}; phone+desktop detail toggles; 0 phone page errors; ${out}`);
} finally {
  await browser.close();
  await server.close();
}
