/**
 * Four real production App C1 finish states from the authored Rookie recording.
 * Derived rides prepend documented neutral input ticks; no result, PB or
 * currency state is injected. Browser storageState carries the actual saved
 * career across fresh contexts and App boots, which tests reload persistence.
 * Each silent clip contains the live closing ride, full result reveal and a
 * touchscreen action. Physics is stepped manually at exactly 120 Hz.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium, type BrowserContext, type Page } from 'playwright';
import { build, preview } from 'vite';
import { NEUTRAL_INPUT, type InputFrame } from '../../src/core/types';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor, targetTimeOf } from '../../src/game/rules';
import { createSimFor } from '../lib/sim';
import { resolveFfmpeg } from '../lib/ffmpeg';

const root = process.cwd();
const out = path.join(root, 'docs/evidence/finish-remaster/state-audit');
const work = path.join(root, 'harness/finish-remaster');
const frozenDir = path.join(work, '.dist-frozen-states');
const framesDir = path.join(work, '.state-audit-frames');
const reportPath = path.join(out, 'states.json');
const blockerPath = path.join(out, 'blocker.json');
const recPath = path.join(root, 'harness/inputs/c1-low-tide/bot-3.json');
const recBytes = fs.readFileSync(recPath);
const rec = decodeJSON(recBytes.toString('utf8'));
const baseInputs = expandFrames(rec);
const fps = 20;
const width = 852;
const height = 393;
const ticksPerFrame = rec.header.physicsHz / fps;
if (ticksPerFrame !== 6) throw new Error(`Expected six 120 Hz ticks per 20 fps frame, got ${ticksPerFrame}`);
fs.mkdirSync(out, { recursive: true });
fs.rmSync(blockerPath, { force: true });

const cases = [
  { id: '01-first-clear', leadTicks: 120, medal: 'Gold', reward: '+220', wallet: 220, tag: 'NEW COURSE CLEAR', headline: 'YOU FOUND THE LINE', pbLabel: 'First personal best', action: 'retry', route: 'run' },
  { id: '02-faster-same-medal', leadTicks: 60, medal: 'Gold', reward: 'No new Scrap', wallet: 220, tag: 'NEW PERSONAL BEST', headline: 'FASTER THROUGH THE GATE', pbLabel: 'Beat previous best', action: 'replay', route: 'replay' },
  { id: '03-medal-upgrade', leadTicks: 0, medal: 'Diamond', reward: '+80', wallet: 300, tag: 'MEDAL UPGRADED', headline: 'THE CLEAN LINE PAID OFF', pbLabel: 'Beat previous best', action: 'menu', route: 'tracks' },
  { id: '04-no-gain-after-reload', leadTicks: 0, medal: 'Diamond', reward: 'No new Scrap', wallet: 300, tag: 'COURSE CLEARED', headline: 'ONE MORE RUN?', pbLabel: 'Personal best stands', action: 'next', route: 'run' },
] as const;

async function expectedFor(leadTicks: number): Promise<{ hash: string; time: number; faults: number; medal: string; totalTicks: number; inputs: InputFrame[] }> {
  const inputs = [...Array.from({ length: leadTicks }, () => NEUTRAL_INPUT), ...baseInputs];
  const sim = await createSimFor(rec);
  for (const input of inputs) sim.step(input);
  const time = sim.state().finishTime;
  if (time === null) throw new Error(`Derived C1 ride with ${leadTicks} neutral ticks does not finish`);
  return { hash: sim.hash(), time, faults: sim.faults(), medal: medalFor(time, sim.faults(), targetTimeOf(sim.track), sim.bike), totalTicks: inputs.length, inputs };
}
const expectedRuns = await Promise.all(cases.map(c => expectedFor(c.leadTicks)));
if (expectedRuns[0]!.time <= expectedRuns[1]!.time || expectedRuns[1]!.time <= expectedRuns[2]!.time || expectedRuns[2]!.time !== expectedRuns[3]!.time) {
  throw new Error('The derived rides do not establish the intended PB sequence');
}

// A private build prevents a shared dist rebuild from changing this audit.
await build({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: frozenDir, emptyOutDir: true } });
const frozenIndexSha256 = crypto.createHash('sha256').update(fs.readFileSync(path.join(frozenDir, 'index.html'))).digest('hex');
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: frozenDir }, preview: { host: '127.0.0.1', port: 0 } });
const serverUrl = server.resolvedUrls?.local[0];
if (!serverUrl) throw new Error('Frozen preview server has no local URL');
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--mute-audio'] });
async function newAuditContext(saved?: Awaited<ReturnType<BrowserContext['storageState']>>): Promise<BrowserContext> {
  const context = await browser.newContext({
    viewport: { width, height }, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    ...(saved ? { storageState: saved } : {}),
  });
  await context.addInitScript(() => { localStorage.setItem('rockhop.onboarded', '1'); });
  return context;
}
let context = await newAuditContext();
const url = new URL(serverUrl);
url.searchParams.set('sw', '0');
url.searchParams.set('audio', '0');
const errors: string[] = [];
const outputs: Array<Record<string, unknown>> = [];
let stage = 'setup';
let currentCase = '';
let page: Page | null = null;
let frames = 0;
const wallStart = Date.now();

async function state(p: Page): Promise<Record<string, unknown>> {
  return p.evaluate(() => {
    const h = window.__rockhop;
    const rawLedger = localStorage.getItem('rockhop.economy.v1');
    const rawPb = localStorage.getItem('rockhop.best.c1-low-tide');
    const pb = rawPb ? JSON.parse(rawPb) as Record<string, unknown> : null;
    return {
      screen: h?.app?.screen() ?? null,
      phase: h?.phase() ?? null,
      trackId: h?.info().trackId ?? null,
      seed: h?.info().seed ?? null,
      runTime: h?.runTime() ?? null,
      finishTime: h?.finishTime() ?? null,
      faults: h?.faults() ?? null,
      renderEntering: (h?.info().render as { entering?: boolean } | null)?.entering ?? null,
      ledger: rawLedger ? JSON.parse(rawLedger) : null,
      pb: pb ? { time: pb.time, medal: pb.medal, bestMedal: pb.bestMedal, faults: pb.faults,
        recordingSha256: typeof pb.recording === 'string' ? 'stored' : null } : null,
      tag: document.querySelector('.fr-tag')?.textContent?.trim() ?? null,
      kicker: document.querySelector('.fr-kicker')?.textContent?.trim() ?? null,
      headline: document.querySelector('.fr-headline')?.textContent?.trim() ?? null,
      pbLabel: document.querySelector('.fr-pb-label')?.textContent?.trim() ?? null,
      pbText: document.querySelector('.pb')?.textContent?.trim() ?? null,
      medal: document.querySelector('.fr-medal-name')?.textContent?.trim() ?? null,
      timeText: document.querySelector('.fr-time-row .time')?.textContent?.trim() ?? null,
      reward: document.querySelector('.tk-reward')?.textContent?.trim() ?? null,
      walletText: document.querySelector('.fr-wallet')?.textContent?.trim() ?? null,
      goal: document.querySelector('.fr-goal')?.textContent?.trim() ?? null,
      tiles: [...document.querySelectorAll('.results .tile')].map(t => ({ id: t.getAttribute('data-id'), text: t.textContent?.trim(), disabled: t.hasAttribute('disabled') })),
    };
  });
}
function assert(condition: unknown, message: string, data?: unknown): asserts condition {
  if (!condition) throw new Error(`${message}${data === undefined ? '' : `: ${JSON.stringify(data)}`}`);
}
async function shot(p: Page): Promise<void> {
  await p.screenshot({ path: path.join(framesDir, `frame-${String(frames).padStart(5, '0')}.png`), type: 'png', caret: 'hide', timeout: 180_000 });
  frames++;
}
async function frame(p: Page): Promise<void> { await p.clock.runFor(1000 / fps); await shot(p); }
async function advance(p: Page, count: number): Promise<void> { for (let i = 0; i < count; i++) await p.clock.runFor(1000 / fps); }
async function tap(p: Page, selector: string): Promise<void> {
  const box = await p.locator(selector).boundingBox();
  assert(box, `No visible pointer target ${selector}`);
  await p.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
}
async function pump(p: Page, label: string, check: () => Promise<boolean>, max = 160, capture = false): Promise<void> {
  for (let i = 0; i < max; i++) {
    if (await check()) return;
    if (capture) await frame(p); else await p.clock.runFor(1000 / fps);
    await new Promise(resolve => setTimeout(resolve, 15));
  }
  throw new Error(`Timeout waiting for ${label}`);
}
function encode(id: string): string {
  const target = path.join(out, `${id}.mp4`);
  execFileSync(resolveFfmpeg(), [
    '-y', '-hide_banner', '-loglevel', 'error', '-framerate', String(fps),
    '-i', path.join(framesDir, 'frame-%05d.png'),
    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
    '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', target,
  ], { stdio: 'pipe', timeout: 180_000 });
  return path.relative(root, target);
}

try {
  for (let n = 0; n < cases.length; n++) {
    const test = cases[n]!;
    const expected = expectedRuns[n]!;
    currentCase = test.id;
    stage = 'boot';
    fs.rmSync(framesDir, { recursive: true, force: true });
    fs.mkdirSync(framesDir);
    frames = 0;
    page = await context.newPage();
    const p = page;
    p.on('pageerror', e => errors.push(`${test.id}: ${e.message}`));
    p.on('console', m => { if (m.type() === 'error') errors.push(`${test.id}: ${m.text()}`); });
    const clock0 = Date.now();
    await p.clock.install({ time: clock0 });
    await p.goto(url.toString(), { waitUntil: 'commit' });
    await p.waitForFunction(() => !document.getElementById('loader') && !!document.querySelector('.menu-screen.live') && !!window.__rockhop?.ready, undefined, { timeout: 180_000 });
    await p.clock.pauseAt(Math.max(clock0, Date.now()) + 2000);
    const before = await state(p);
    assert((before.ledger as { wallet?: number } | null)?.wallet === (n === 0 ? 0 : cases[n - 1]!.wallet), 'Ledger did not persist across fresh App boot', before);
    if (n > 0) assert(Math.abs(((before.pb as { time?: number } | null)?.time ?? Number.NaN) - expectedRuns[n - 1]!.time) < 0.000001, 'PB did not persist across fresh App boot', before);
    console.log(`[states] ${test.id} boot wallet=${(before.ledger as {wallet:number}).wallet}`);
    await tap(p, '.menu-screen.live .menu-item[data-id=play]');
    await pump(p, 'painted Map', async () => p.locator('.tracks-screen.live .wm-world.loaded').count().then(Boolean));
    const rideText = await p.locator('.tracks-screen.live .wm-ride').textContent();
    if (!rideText?.includes('Low Tide')) {
      await tap(p, '.tracks-screen.live .wm-marker[data-track="c1-low-tide"]');
    }
    assert((await p.locator('.tracks-screen.live .wm-ride').textContent())?.includes('Low Tide'), 'Map did not select C1');
    await tap(p, '.tracks-screen.live .wm-ride');
    await pump(p, 'C1 countdown', async () => p.evaluate(() => window.__rockhop?.app?.screen() === 'run' && window.__rockhop?.phase() === 'countdown'));
    await advance(p, 50);
    const ready = await state(p);
    assert(ready.phase === 'countdown' && ready.renderEntering === false, 'Course not painted before GO', ready);
    await p.evaluate(() => window.__rockhop!.skipCountdown());
    const armed = await state(p);
    assert(armed.phase === 'riding' && armed.trackId === 'c1-low-tide' && armed.seed === rec.header.seed && armed.runTime === 0 && armed.faults === 0, 'Cannot align recording at GO', armed);
    stage = 'ride';
    const filmFrom = expected.inputs.length - 40 * ticksPerFrame;
    for (let tick = 0; tick < expected.inputs.length;) {
      const batchSize = tick < filmFrom ? Math.min(60, filmFrom - tick) : ticksPerFrame;
      const batch = expected.inputs.slice(tick, tick + batchSize);
      await p.evaluate(inputs => {
        const h = window.__rockhop!;
        for (const input of inputs) { h.setInput(input); h.step(1); }
        h.render();
      }, batch);
      tick += batch.length;
      if (tick > filmFrom) await shot(p);
      if (tick % 600 === 0) console.log(`[states] ${test.id} tick=${tick}/${expected.totalTicks}`);
    }
    const exact = await p.evaluate(() => ({ hash: window.__rockhop!.hashState(), time: window.__rockhop!.finishTime(), faults: window.__rockhop!.faults(), phase: window.__rockhop!.phase() }));
    assert(exact.hash === expected.hash && exact.time === expected.time && exact.faults === expected.faults && exact.phase === 'finished', 'Played ride failed exact Node reference', { exact, expected: { ...expected, inputs: undefined } });
    stage = 'result';
    await pump(p, 'live result stage 5', async () => p.locator('.results.show.stage-5.live').count().then(Boolean), 100, true);
    for (let i = 0; i < 20; i++) await frame(p);
    const result = await state(p);
    const ledger = result.ledger as { wallet?: number; medals?: Record<string, string> } | null;
    const pb = result.pb as { time?: number; medal?: string; bestMedal?: string } | null;
    assert(result.tag === test.tag && result.headline === test.headline && result.pbLabel === test.pbLabel && result.medal === test.medal && result.reward === test.reward && result.walletText === String(test.wallet), 'Visible result copy or reward disagrees', result);
    assert(ledger?.wallet === test.wallet && ledger.medals?.['c1-low-tide'] === (test.medal === 'Diamond' || n === 3 ? 'platinum' : 'gold'), 'Career medal or wallet disagrees', result);
    assert(Math.abs((pb?.time ?? Number.NaN) - Math.min(...expectedRuns.slice(0, n + 1).map(r => r.time))) < 0.000001, 'Stored PB time disagrees', result);
    assert((result.tiles as Array<{id:string; disabled:boolean}>).every(t => !t.disabled), 'One or more result actions disabled', result.tiles);
    await tap(p, `.results.live .tile[data-id=${test.action}]`);
    const route = await state(p);
    assert(route.screen === test.route, `Result action ${test.action} reached wrong screen`, route);
    if (test.action === 'retry') assert(route.trackId === 'c1-low-tide' && route.phase === 'countdown', 'Retry did not reset C1', route);
    if (test.action === 'next') assert(route.trackId !== 'c1-low-tide' && route.phase === 'countdown', 'Next did not load C2', route);
    for (let i = 0; i < 12; i++) await frame(p);
    const clip = encode(test.id);
    outputs.push({ case: test.id, leadNeutralTicks: test.leadTicks, expected: { hash: expected.hash, time: expected.time, faults: expected.faults, medal: expected.medal, totalTicks: expected.totalTicks }, before, exact, result, pointerAction: test.action, route, clip, frames, seconds: frames / fps });
    console.log(`[states] ${test.id} PASS ${expected.time.toFixed(3)} ${test.medal} ${test.reward} → ${test.action}`);
    await p.close();
    page = null;
    if (n < cases.length - 1) {
      const saved = await context.storageState();
      await context.close();
      context = await newAuditContext(saved);
    }
  }
  assert(errors.length === 0, 'Browser page/console errors', errors);
  const report = {
    verdict: 'PASS', source: 'production App, four fresh page boots with actual local storage carried into new browser contexts',
    viewportCss: [width, height], encodedVideo: [width, height + 1], fps,
    recipe: 'authored C1 Rookie bot-3 recording, with 120/60/0/0 leading neutral ticks; actual physics and career ledger, no injected result or PB',
    recording: path.relative(root, recPath), recordingSha256: crypto.createHash('sha256').update(recBytes).digest('hex'),
    clock: 'Playwright clock paused after Menu boot; C1 inputs stepped manually at 120 Hz; result reveal advanced in 50 ms frames',
    gitSha: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    frozenIndexSha256, browser: 'headless Chromium / ANGLE SwiftShader', onboarding: 'returning player; fresh career at case 1, then actual storage survives three fresh App boots',
    cases: outputs, errors, wallMs: Date.now() - wallStart,
  };
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`[states] PASS ${outputs.length} authentic result states, ${path.relative(root, reportPath)}`);
} catch (error) {
  for (const test of cases) fs.rmSync(path.join(out, `${test.id}.mp4`), { force: true });
  const blocker = { verdict: 'BLOCKED', case: currentCase, stage, message: error instanceof Error ? error.message : String(error), completedCases: outputs.map(o => o.case), errors, wallMs: Date.now() - wallStart };
  fs.writeFileSync(blockerPath, `${JSON.stringify(blocker, null, 2)}\n`);
  console.error(`[states] BLOCKED ${JSON.stringify(blocker)}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await page?.close().catch(() => undefined);
  await context.close().catch(() => undefined);
  await browser.close().catch(() => undefined);
  await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.rmSync(frozenDir, { recursive: true, force: true });
  fs.rmSync(`${frozenDir}-maps`, { recursive: true, force: true });
}
