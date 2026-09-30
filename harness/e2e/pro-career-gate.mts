/** Silent, normal-app career gate: fresh save -> eight medals -> purchase -> final-four launch. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';
import { ROCKHOP_ALL } from '../../src/tracks';
import { startServer } from '../lib/server';
import { REPO_ROOT } from '../lib/paths';

const server = await startServer({ freeze: true });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
const firstEight = ROCKHOP_ALL.slice(0, 8).map((track) => track.id);
const pageErrors: string[] = [];
const report: Record<string, unknown> = { app: 'normal (no harness or dev URL)', firstEight, pageErrors };

async function visit(track: string): Promise<void> {
  const url = new URL(server.url);
  url.searchParams.set('sw', '0');
  url.searchParams.set('track', track);
  assert.equal(url.searchParams.has('dev'), false);
  await page.goto(url.toString(), { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => ['tracks', 'run'].includes((window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() ?? ''), null, { timeout: 120_000 });
  await page.waitForFunction(() => document.getElementById('loader') === null, null, { timeout: 120_000 });
}

function appState() {
  return page.evaluate(() => {
    const hook = (window as unknown as { __rockhop: { app: { screen(): string }; info(): { trackId: string; bike: string } } }).__rockhop;
    const { trackId, bike } = hook.info();
    return { screen: hook.app.screen(), trackId, bike, focused: document.querySelector('.wm3d-detail')?.getAttribute('data-track'),
      rule: document.querySelector('.wm-ride .rule')?.textContent, quick: document.querySelector('.wm-quick')?.textContent,
      wallet: JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}').wallet };
  });
}

const page = await context.newPage();
page.on('pageerror', (error) => pageErrors.push(error.message));
try {
  await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
  await visit('d3-rope-walk');
  report.fresh = await appState();
  assert.equal((report.fresh as { screen: string }).screen, 'tracks');
  assert.equal((report.fresh as { focused: string }).focused, 'd3-rope-walk');
  assert.match((report.fresh as { rule: string }).rule, /Medal levels 01–08/);

  await page.evaluate((ids) => {
    for (const id of ids) localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 40, faults: 0, medal: 'bronze' }));
  }, firstEight);
  await visit('d3-rope-walk');
  report.eightBronze = await appState();
  assert.equal((report.eightBronze as { screen: string }).screen, 'tracks');
  assert.equal((report.eightBronze as { wallet: number }).wallet, 800);
  assert.match((report.eightBronze as { rule: string }).rule, /Buy the Pro bike/);
  assert.match((report.eightBronze as { quick: string }).quick, /Earn Scrap/);
  await page.locator('.wm-quick').click();
  await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
  assert.equal(await page.locator('.garage-screen.live .gp-name b').textContent(), 'Pro');
  assert.equal(await page.locator('.garage-screen.live .gp-buy[disabled]').count(), 1);
  await page.evaluate((ids) => {
    for (const [index, id] of ids.entries()) localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 35, faults: 0, medal: index === 7 ? 'platinum' : 'gold' }));
  }, firstEight);
  await visit('d3-rope-walk');
  report.improved = await appState();
  assert.equal((report.improved as { wallet: number }).wallet, 1840);
  assert.match((report.improved as { quick: string }).quick, /Buy Pro/);
  await page.locator('.wm-quick').click();
  await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
  assert.equal(await page.locator('.garage-screen.live .gp-name b').textContent(), 'Pro');
  assert.equal(await page.locator('.garage-screen.live .gp-buy:not([disabled])').count(), 1);
  await page.locator('.garage-screen.live .gp-buy:not([disabled])').click();
  await page.waitForFunction(() => document.querySelector('.garage-screen .bike-chip[data-bike=pro]')?.getAttribute('aria-pressed') === 'true');
  report.purchase = await page.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}'));
  assert.equal((report.purchase as { proOwned: boolean }).proOwned, true);
  assert.equal((report.purchase as { equipped: string }).equipped, 'pro');
  assert.equal((report.purchase as { wallet: number }).wallet, 0);

  await visit('d3-rope-walk');
  report.proD3 = await appState();
  assert.equal((report.proD3 as { screen: string }).screen, 'run');
  assert.equal((report.proD3 as { trackId: string }).trackId, 'd3-rope-walk');
  assert.equal((report.proD3 as { bike: string }).bike, 'pro');
  await visit('s1-lift-line');
  report.noD3Medal = await appState();
  assert.equal((report.noD3Medal as { screen: string }).screen, 'tracks');
  assert.match((report.noD3Medal as { rule: string }).rule, /Medal every Quarry track/);

  await page.evaluate(() => localStorage.setItem('rockhop.best.d3-rope-walk', JSON.stringify({ time: 40, faults: 0, medal: 'bronze', bike: 'pro' })));
  await visit('s1-lift-line');
  report.proS1 = await appState();
  assert.equal((report.proS1 as { screen: string }).screen, 'run');
  assert.equal((report.proS1 as { bike: string }).bike, 'pro');
  const proFinalFour: Record<string, unknown>[] = [];
  for (const id of ['s2-cornice', 's3-whiteout']) {
    await visit(id);
    const state = await appState();
    assert.equal(state.screen, 'run');
    assert.equal(state.trackId, id);
    assert.equal(state.bike, 'pro');
    proFinalFour.push({ id, screen: state.screen, bike: state.bike });
  }
  report.proFinalFour = proFinalFour;

  await page.evaluate(() => (window as unknown as { __rockhop: { app: { goto(screen: 'garage'): void } } }).__rockhop.app.goto('garage'));
  await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
  await page.locator('.garage-screen.live .bike-chip[data-bike=rookie]').click();
  await page.waitForFunction(() => document.querySelector('.garage-screen .bike-chip[data-bike=rookie]')?.getAttribute('aria-pressed') === 'true');
  await visit('s1-lift-line');
  report.rookieS1 = await appState();
  assert.equal((report.rookieS1 as { screen: string }).screen, 'tracks');
  assert.match((report.rookieS1 as { rule: string }).rule, /Equip the Pro bike/);
  assert.equal((report.rookieS1 as { focused: string }).focused, 's1-lift-line');
  const rookieFinalFour: Record<string, unknown>[] = [];
  for (const id of ['d3-rope-walk', 's2-cornice', 's3-whiteout']) {
    await visit(id);
    const state = await appState();
    assert.equal(state.screen, 'tracks');
    assert.equal(state.focused, id);
    assert.match(state.rule ?? '', /Equip the Pro bike/);
    rookieFinalFour.push({ id, screen: state.screen, rule: state.rule });
  }
  report.rookieFinalFour = rookieFinalFour;
  await page.locator('.wm-quick').click();
  await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
  assert.equal(await page.locator('.garage-screen.live .gp-name b').textContent(), 'Pro');
  assert.equal(await page.locator('.garage-screen.live .gp-equip').textContent(), 'Equip Pro');
  await page.locator('.garage-screen.live .gp-equip').click();
  report.reequip = await page.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}').equipped);
  assert.equal(report.reequip, 'pro');
  await visit('s3-whiteout');
  assert.equal((await appState()).screen, 'run');

  // A separate fresh save proves the other exact-price medal combination.
  const alternate = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
  try {
    await alternate.addInitScript((ids) => {
      localStorage.setItem('rockhop.onboarded', '1');
      for (const [index, id] of ids.entries()) {
        localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 35, faults: 0, medal: index < 4 ? 'silver' : 'platinum' }));
      }
    }, firstEight);
    const alternatePage = await alternate.newPage();
    alternatePage.on('pageerror', (error) => pageErrors.push(error.message));
    const direct = new URL(server.url);
    direct.searchParams.set('sw', '0');
    direct.searchParams.set('track', 'd3-rope-walk');
    assert.equal(direct.searchParams.has('dev'), false);
    await alternatePage.goto(direct.toString(), { waitUntil: 'domcontentloaded' });
    await alternatePage.waitForFunction(() => (window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() === 'tracks', null, { timeout: 120_000 });
    await alternatePage.waitForFunction(() => document.getElementById('loader') === null, null, { timeout: 120_000 });
    assert.equal(await alternatePage.locator('.wm-quick').textContent().then((value) => /Buy Pro/.test(value ?? '')), true);
    assert.equal(await alternatePage.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}').wallet), 1840);
    await alternatePage.locator('.wm-quick').click();
    await alternatePage.waitForSelector('.garage-screen.live .gp-buy:not([disabled])', { timeout: 30_000 });
    await alternatePage.locator('.garage-screen.live .gp-buy:not([disabled])').click();
    const alternatePurchase = await alternatePage.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}'));
    assert.equal(alternatePurchase.wallet, 0);
    assert.equal(alternatePurchase.proOwned, true);
    report.fourSilverFourDiamond = { price: 1840, walletAfterPurchase: alternatePurchase.wallet, proOwned: alternatePurchase.proOwned };
    await alternatePage.goto(direct.toString(), { waitUntil: 'domcontentloaded' });
    await alternatePage.waitForFunction(() => (window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() === 'run', null, { timeout: 120_000 });
    assert.equal(await alternatePage.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}').wallet), 0);
  } finally {
    await alternate.close();
  }

  // A historical Pro garage selection remains owned and usable after migration.
  const legacy = await browser.newContext({ viewport: { width: 852, height: 393 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
  try {
    await legacy.addInitScript((ids) => {
      localStorage.setItem('rockhop.onboarded', '1');
      localStorage.setItem('rockhop.bikeClass', 'pro');
      for (const id of ids) localStorage.setItem(`rockhop.best.${id}`, JSON.stringify({ time: 40, faults: 0, medal: 'bronze' }));
    }, firstEight);
    const legacyPage = await legacy.newPage();
    legacyPage.on('pageerror', (error) => pageErrors.push(error.message));
    const direct = new URL(server.url);
    direct.searchParams.set('sw', '0');
    direct.searchParams.set('track', 'd3-rope-walk');
    assert.equal(direct.searchParams.has('dev'), false);
    await legacyPage.goto(direct.toString(), { waitUntil: 'domcontentloaded' });
    await legacyPage.waitForFunction(() => (window as unknown as { __rockhop?: { app?: { screen(): string } } }).__rockhop?.app?.screen() === 'run', null, { timeout: 120_000 });
    const migrated = await legacyPage.evaluate(() => JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}'));
    assert.equal(migrated.proOwned, true);
    assert.equal(migrated.equipped, 'pro');
    assert.equal(migrated.wallet, 800);
    report.legacyPro = { proOwned: migrated.proOwned, equipped: migrated.equipped, wallet: migrated.wallet, charged: false };
  } finally {
    await legacy.close();
  }

  assert.equal(pageErrors.length, 0, pageErrors.join('\n'));
  report.pass = true;
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.failure = String(error);
  throw error;
} finally {
  const reportPath = path.join(REPO_ROOT, 'harness/out/metrics/pro-career-gate.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  await context.close();
  await browser.close();
  await server.close();
}
