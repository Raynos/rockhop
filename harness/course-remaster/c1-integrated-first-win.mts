/**
 * One silent headless WebKit page, one frozen production build:
 * Menu → default 3D map → exact C1 first clear → result → Map → Garage →
 * reload → 3D map with saved medal. The same input is then played a second
 * time on that page, off-video, to prove no duplicate Scrap payout.
 *
 * The actual App routes and touch targets are used. A recorded 120 Hz input is
 * manually stepped during both rides while the App clock is paused, then every
 * rendered frame is captured. The final countdown fraction is skipped to align
 * the pinned recording, just as in the existing finish App harness.
 *
 * Run only when the shared browser/build slot is free:
 *   pnpm exec tsx harness/course-remaster/c1-integrated-first-win.mts
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { webkit } from 'playwright';
import { build, preview } from 'vite';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { resolveFfmpeg } from '../lib/ffmpeg';

type MapProbe = {
  towerScreenPoint(index: number): { x: number; y: number } | null;
  viewState(): { states: string[] };
};
type MapWindow = Window & { __rockhopMap3d?: MapProbe };

const root = process.cwd();
const out = path.join(root, 'docs/evidence/course-remaster/c1/integrated-first-win');
const privateDist = path.join(root, 'harness/out/c1-integrated-first-win-dist');
const framesDir = path.join(root, 'harness/out/c1-integrated-first-win-frames');
const clip = path.join(out, 'played-flow.mp4');
const reportFile = path.join(out, 'report.json');
const blockerFile = path.join(out, 'blocker.json');
const recordingPath = path.join(root, 'harness/inputs/c1-low-tide/bot-3.json');
const recordingBytes = fs.readFileSync(recordingPath);
const rec = decodeJSON(recordingBytes.toString('utf8'));
const inputs = expandFrames(rec);
const fps = 20, width = 852, height = 392, ticksPerFrame = rec.header.physicsHz / fps;
if (ticksPerFrame !== 6) throw new Error(`Expected 120 Hz / 20 fps, got ${ticksPerFrame}`);

const sha256 = (bytes: Buffer | string): string => crypto.createHash('sha256').update(bytes).digest('hex');
const git = (...args: string[]): string => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
function sourceTreeSha256(): string {
  const sum = crypto.createHash('sha256');
  const visit = (dir: string): void => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) { sum.update(path.relative(root, full)); sum.update(fs.readFileSync(full)); }
    }
  };
  visit(path.join(root, 'src'));
  return sum.digest('hex');
}
function sourceStamp(): { head: string; sourceTreeSha256: string; archive: boolean; wip: { path: string; sha256: string }[] } {
  const archiveCommit = process.env.ROCKHOP_CAPTURE_COMMIT;
  if (archiveCommit) return { head: archiveCommit, sourceTreeSha256: sourceTreeSha256(), archive: true, wip: [] };
  const names = [
    ...git('diff', '--name-only', '--', 'src').split('\n'),
    ...git('ls-files', '--others', '--exclude-standard', 'src').split('\n'),
  ].filter(Boolean);
  return { head: git('rev-parse', 'HEAD'), sourceTreeSha256: sourceTreeSha256(), archive: false,
    wip: [...new Set(names)].sort().map(name => ({ path: name, sha256: sha256(fs.readFileSync(path.join(root, name))) })) };
}

fs.mkdirSync(out, { recursive: true });
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
fs.rmSync(privateDist, { recursive: true, force: true });
fs.rmSync(clip, { force: true });
fs.rmSync(blockerFile, { force: true });

const sim = await createSimFor(rec);
for (const input of inputs) sim.step(input);
const expected = { hash: sim.hash(), finishTime: sim.state().finishTime, tick: sim.state().tick, faults: sim.faults() };
if (sim.phase() !== 'finished' || expected.faults !== 0 || expected.hash !== '2bfe061963ffb058') {
  throw new Error(`Pinned C1 input no longer clears as expected: ${JSON.stringify(expected)}`);
}

const source = sourceStamp();
await build({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: privateDist, emptyOutDir: true } });
if (JSON.stringify(sourceStamp()) !== JSON.stringify(source)) throw new Error('Source changed while building the frozen candidate');
const indexSha256 = sha256(fs.readFileSync(path.join(privateDist, 'index.html')));
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: privateDist }, preview: { host: '127.0.0.1', port: 0 } });
const serverUrl = server.resolvedUrls?.local[0];
if (!serverUrl) throw new Error('Private build preview has no URL');
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
await context.addInitScript(() => { localStorage.setItem('rockhop.onboarded', '1'); });
const page = await context.newPage();
const pageErrors: string[] = [];
const consoleErrors: string[] = [];
page.on('pageerror', error => pageErrors.push(error.message));
page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
let stage = 'boot';
let frame = 0;
let filming = true;
const marks: Array<Record<string, unknown>> = [];
const rideSamples: Array<Record<string, unknown>> = [];
const wallStart = Date.now();

function assert(condition: unknown, label: string, data?: unknown): asserts condition {
  if (!condition) throw new Error(`${label}${data === undefined ? '' : `: ${JSON.stringify(data)}`}`);
}
async function state(): Promise<Record<string, unknown>> {
  return page.evaluate(() => {
    const h = window.__rockhop;
    const map = (window as MapWindow).__rockhopMap3d;
    const rawLedger = localStorage.getItem('rockhop.economy.v1');
    const rawPb = localStorage.getItem('rockhop.best.c1-low-tide');
    return {
      screen: h?.app?.screen() ?? null,
      phase: h?.phase() ?? null,
      trackId: h?.info().trackId ?? null,
      seed: h?.info().seed ?? null,
      entryHold: h?.info().entryHold ?? null,
      renderEntering: (h?.info().render as { entering?: boolean } | null)?.entering ?? null,
      runTime: h?.runTime() ?? null,
      finishTime: h?.finishTime() ?? null,
      faults: h?.faults() ?? null,
      mapCanvasCount: document.querySelectorAll('.wm3d-host canvas').length,
      paintedMapPresent: document.querySelector('.wm-view') !== null,
      mapStates: map?.viewState().states ?? null,
      mapSelected: document.querySelector('.wm3d-detail')?.getAttribute('data-track') ?? null,
      medal: document.querySelector('.fr-medal-name')?.textContent?.trim() ?? null,
      reward: document.querySelector('.tk-reward')?.textContent?.trim() ?? null,
      walletText: document.querySelector('.fr-wallet')?.textContent?.trim() ?? null,
      resultTime: document.querySelector('.fr-time-row .time')?.textContent?.trim() ?? null,
      garageWallet: document.querySelector('.gp-wallet')?.textContent?.trim() ?? null,
      ledger: rawLedger ? JSON.parse(rawLedger) : null,
      pb: rawPb ? (() => { const value = JSON.parse(rawPb) as { time?: number; bestMedal?: string; faults?: number }; return { time: value.time, bestMedal: value.bestMedal, faults: value.faults }; })() : null,
    };
  });
}
async function mark(name: string): Promise<Record<string, unknown>> {
  const row: Record<string, unknown> = { name, onVideo: filming, frame, videoS: frame / fps, ...(await state()) };
  marks.push(row);
  console.log(`[c1-flow] ${name} frame=${frame} screen=${String(row.screen)} phase=${String(row.phase)}`);
  return row;
}
async function shot(): Promise<void> {
  if (!filming) return;
  await page.screenshot({ path: path.join(framesDir, `frame-${String(frame).padStart(5, '0')}.png`), type: 'png', caret: 'hide', timeout: 180_000 });
  frame++;
}
async function clockFrame(): Promise<void> { await page.clock.runFor(1000 / fps); await shot(); }
async function roll(count: number): Promise<void> { for (let i = 0; i < count; i++) await clockFrame(); }
async function pump(label: string, predicate: () => Promise<boolean>, cap = 180): Promise<void> {
  for (let i = 0; i < cap; i++) {
    if (await predicate()) return;
    await clockFrame();
    await new Promise(resolve => setTimeout(resolve, 15));
  }
  throw new Error(`Timed out waiting for ${label} after ${cap} frames`);
}
async function tap(selector: string): Promise<void> {
  const box = await page.locator(selector).boundingBox();
  assert(box, `Missing touch target ${selector}`);
  await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
}
async function mapReady(label: string): Promise<void> {
  try {
    await pump(label, () => page.evaluate(() => document.querySelector('.wm3d-host')?.getAttribute('data-ready') === '1' && !!(window as MapWindow).__rockhopMap3d), 240);
  } catch (error) {
    const diagnostic = await page.evaluate(() => ({
      menuClass: document.querySelector('.menu-screen')?.className,
      tracksClass: document.querySelector('.tracks-screen')?.className,
      hostClass: document.querySelector('.wm3d-host')?.className,
      hostReady: document.querySelector('.wm3d-host')?.getAttribute('data-ready'),
      loading: document.querySelector('.wm3d-loading')?.textContent?.trim(),
      mapHook: !!(window as MapWindow).__rockhopMap3d,
      loader: document.getElementById('loader')?.textContent?.trim().slice(0, 120),
    }));
    throw new Error(`${label}: ${String(error)}; ${JSON.stringify({ state: await state(), diagnostic, pageErrors, consoleErrors })}`, { cause: error });
  }
  const m = await state();
  assert(m.mapCanvasCount === 1 && m.paintedMapPresent === false, 'Default 3D map missing or painted map present', m);
}
async function selectC1AndRide(): Promise<void> {
  const point = await page.evaluate(() => (window as MapWindow).__rockhopMap3d?.towerScreenPoint(0) ?? null);
  assert(point, 'C1 tower has no screen point');
  await page.touchscreen.tap(point.x, point.y);
  await pump('C1 tower selection', () => page.locator('.wm3d-detail[data-track="c1-low-tide"]').count().then(Boolean), 80);
  await roll(9);
  await tap('.tracks-screen.live .wm-ride');
  await pump('C1 countdown', () => page.evaluate(() => window.__rockhop?.app?.screen() === 'run' && window.__rockhop?.phase() === 'countdown'), 180);
  await mark('c1-countdown');
  await roll(50);
  const beforeGo = await state();
  assert(beforeGo.phase === 'countdown' && beforeGo.entryHold === false && beforeGo.renderEntering === false, 'Course not rendered before GO', beforeGo);
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  const armed = await state();
  assert(armed.screen === 'run' && armed.phase === 'riding' && armed.trackId === rec.header.trackId && armed.seed === rec.header.seed && armed.runTime === 0 && armed.faults === 0, 'Pinned C1 run not aligned at GO', armed);
}
async function ride(label: string): Promise<Record<string, unknown>> {
  stage = label;
  await mark(`${label}-go`);
  for (let tick = 0; tick < inputs.length; tick += ticksPerFrame) {
    const batch = inputs.slice(tick, tick + ticksPerFrame);
    await page.evaluate(frames => {
      const h = window.__rockhop!;
      for (const input of frames) { h.setInput(input); h.step(1); }
      h.render();
    }, batch);
    await shot();
    if (tick % 240 === 0) {
      const sample = await state();
      assert(sample.renderEntering === false, 'Renderer showed entry placeholder during ride', { label, tick, sample });
      rideSamples.push({ label, frame, inputTick: tick + batch.length, runTime: sample.runTime, phase: sample.phase });
    }
  }
  const exact = await page.evaluate(() => ({ hash: window.__rockhop!.hashState(), finishTime: window.__rockhop!.finishTime(), tick: window.__rockhop!.getState().tick, faults: window.__rockhop!.faults(), phase: window.__rockhop!.phase() }));
  assert(exact.phase === 'finished' && exact.hash === expected.hash && exact.finishTime === expected.finishTime && exact.tick === expected.tick && exact.faults === 0, 'Browser finish differed from Node', { label, exact, expected });
  await mark(`${label}-exact-finish`);
  await pump(`${label} live result`, () => page.locator('.results.show.stage-5.live').count().then(Boolean), 120);
  await roll(24);
  return mark(`${label}-result`);
}
function encode(): void {
  execFileSync(resolveFfmpeg(), [
    '-y', '-hide_banner', '-loglevel', 'error', '-framerate', String(fps),
    '-i', path.join(framesDir, 'frame-%05d.png'), '-c:v', 'libx264',
    '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', clip,
  ], { stdio: 'pipe', timeout: 300_000 });
}

try {
  const clock0 = Date.now();
  await page.clock.install({ time: clock0 });
  const url = new URL(serverUrl);
  url.searchParams.set('sw', '0');
  url.searchParams.set('audio', '0');
  await page.goto(url.toString(), { waitUntil: 'commit' });
  await page.waitForFunction(() => !document.getElementById('loader') && !!document.querySelector('.menu-screen.live') && !!window.__rockhop?.ready, undefined, { timeout: 180_000 });
  await page.clock.pauseAt(Math.max(clock0, Date.now()) + 2000);
  stage = 'menu';
  const initial = await mark('menu');
  assert((initial.ledger as { wallet?: number } | null)?.wallet === 0, 'Career was not fresh', initial);
  await roll(16);
  await tap('.menu-screen.live .menu-item[data-id=play]');
  stage = 'first-map';
  await mapReady('initial 3D map');
  const firstMap = await mark('first-3d-map');
  assert((firstMap.mapStates as string[] | null)?.[0] === 'available', 'C1 not available before first ride', firstMap);
  await roll(20);
  await selectC1AndRide();
  const firstResult = await ride('first');
  const firstLedger = firstResult.ledger as { wallet?: number; medals?: Record<string, string> } | null;
  assert(firstResult.medal === 'Diamond' && firstResult.reward === '+300' && firstResult.walletText === '300' && firstResult.resultTime === '0:30.350' && firstLedger?.wallet === 300 && firstLedger.medals?.['c1-low-tide'] === 'platinum', 'First-win reward/medal incorrect', firstResult);

  await tap('.results.live .tile[data-id=menu]');
  stage = 'return-map';
  await mapReady('3D map after first result');
  const earnedMap = await mark('earned-medal-map');
  assert((earnedMap.mapStates as string[] | null)?.[0] === 'platinum', 'C1 Diamond marker absent after first win', earnedMap);
  await roll(18);
  await tap('.tracks-screen.live .backbtn');
  await pump('Menu after Map', () => page.locator('.menu-screen.live').count().then(Boolean), 120);
  await tap('.menu-screen.live .menu-item[data-id=garage]');
  stage = 'garage';
  await pump('Garage after first win', () => page.locator('.garage-screen.live').count().then(Boolean), 150);
  await roll(18);
  const garage = await mark('garage-wallet');
  assert((garage.ledger as {wallet?: number} | null)?.wallet === 300 && String(garage.garageWallet).includes('300'), 'Garage did not show earned Scrap', garage);

  stage = 'reload';
  // A WebKit navigation needs its timers to run naturally while the App and
  // GPU context initialize. Re-pausing before the next map interaction keeps
  // the recorded UI frames deterministic without stranding the map loader.
  await page.clock.resume();
  await page.reload({ waitUntil: 'commit' });
  await page.waitForFunction(() => !document.getElementById('loader') && !!document.querySelector('.menu-screen.live') && !!window.__rockhop?.ready, undefined, { timeout: 180_000 });
  await page.clock.pauseAt((await page.evaluate(() => Date.now())) + 1000);
  const reloaded = await mark('menu-after-reload');
  assert((reloaded.ledger as {wallet?: number} | null)?.wallet === 300, 'Reload lost wallet', reloaded);
  await roll(12);
  stage = 'reload-map';
  await tap('.menu-screen.live .menu-item[data-id=play]');
  await mapReady('3D map after reload');
  const savedMap = await mark('saved-medal-map');
  assert((savedMap.mapStates as string[] | null)?.[0] === 'platinum' && (savedMap.ledger as {wallet?: number} | null)?.wallet === 300, 'Reload lost C1 medal or Scrap', savedMap);
  await roll(16);
  await mark('film-end-saved-map');
  filming = false;
  // Keep the first-journey video continuous and concise. The same live App
  // page then performs a second exact ride for the payout assertion off-film.
  await selectC1AndRide();
  const repeatedResult = await ride('repeat');
  const repeatLedger = repeatedResult.ledger as { wallet?: number; medals?: Record<string, string> } | null;
  assert(repeatedResult.medal === 'Diamond' && repeatedResult.reward === 'No new Scrap' && repeatedResult.walletText === '300' && repeatLedger?.wallet === 300 && repeatLedger.medals?.['c1-low-tide'] === 'platinum', 'Repeated Diamond paid twice or changed medal', repeatedResult);
  await roll(14);
  assert(pageErrors.length === 0 && consoleErrors.length === 0, 'Browser errors during first-win flow', { pageErrors, consoleErrors });
  encode();
  const report = {
    verdict: 'PASS', engine: 'headless WebKit', source, privateBuildIndexSha256: indexSha256,
    wipHarnessSha256: sha256(fs.readFileSync(new URL(import.meta.url))),
    viewportCss: [width, height], video: { path: path.relative(root, clip), fps, frames: frame, seconds: frame / fps, sizeBytes: fs.statSync(clip).size, sha256: sha256(fs.readFileSync(clip)), audio: 'none' },
    recording: path.relative(root, recordingPath), recordingSha256: sha256(recordingBytes), recordingHeader: rec.header,
    method: 'One live App page; Playwright clock drives UI; 120 Hz pinned input manually stepped and rendered at 20 fps; final countdown fraction skipped for exact input alignment. The repeated clean C1 ride and no-duplicate-payout check run after the continuous first-journey clip ends, on the same reloaded page.',
    expected, firstResult, earnedMap, garage, reloaded, savedMap, repeatedResult,
    marks, rideSamples, pageErrors, consoleErrors, wallMs: Date.now() - wallStart,
  };
  fs.writeFileSync(reportFile, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`[c1-flow] PASS ${frame} frames / ${(frame / fps).toFixed(2)} s: ${path.relative(root, clip)}`);
} catch (error) {
  fs.rmSync(clip, { force: true });
  const blocker = { verdict: 'BLOCKED', stage, message: error instanceof Error ? error.message : String(error), framesDiscarded: frame, marks, pageErrors, consoleErrors, wallMs: Date.now() - wallStart };
  fs.writeFileSync(blockerFile, `${JSON.stringify(blocker, null, 2)}\n`);
  console.error(`[c1-flow] BLOCKED ${JSON.stringify(blocker)}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await context.close().catch(() => undefined);
  await browser.close().catch(() => undefined);
  await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.rmSync(privateDist, { recursive: true, force: true });
  fs.rmSync(`${privateDist}-maps`, { recursive: true, force: true });
}
