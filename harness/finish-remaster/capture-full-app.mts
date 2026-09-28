/**
 * Silent, uninterrupted production-UI flow at landscape phone geometry:
 * Menu → painted Map → C1 from its authored 120 Hz recording → actual finish
 * → Map → Menu → Garage. One real App page and one sequential frame stream.
 *
 * Physics stepping is manual during the ride so the authored input is exact.
 * Playwright's paused clock advances App/CSS frames before and after that ride.
 * No DOM text or art is injected. On failure, no partial clip is retained.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { build, preview } from 'vite';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSim } from '../lib/sim';
import { resolveFfmpeg } from '../lib/ffmpeg';

const root = process.cwd();
const evidence = path.join(root, 'docs/evidence/finish-remaster');
const work = path.join(root, 'harness/finish-remaster');
const framesDir = path.join(work, '.full-app-frames');
const frozenDir = path.join(work, '.dist-frozen');
const clip = path.join(evidence, 'full-app-flow.mp4');
const reportFile = path.join(evidence, 'full-app-flow.json');
const blockerFile = path.join(evidence, 'full-app-flow.blocker.json');
const recordingPath = path.join(root, 'harness/inputs/c1-low-tide/bot-3.json');
const recordingBytes = fs.readFileSync(recordingPath);
const rec = decodeJSON(recordingBytes.toString('utf8'));
const inputs = expandFrames(rec);
const fps = 20, width = 852, height = 393, ticksPerFrame = rec.header.physicsHz / fps;
if (!Number.isInteger(ticksPerFrame)) throw new Error(`physics Hz ${rec.header.physicsHz} is not divisible by ${fps}`);
fs.mkdirSync(evidence, { recursive: true });
fs.mkdirSync(work, { recursive: true });
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir);
fs.rmSync(clip, { force: true });
fs.rmSync(blockerFile, { force: true });

const sim = await createSim(rec.header.trackId, rec.header.seed, rec.header.physicsHz, { bike: 'rookie' });
for (const input of inputs) sim.step(input);
const expected = { hash: sim.hash(), finishTime: sim.state().finishTime };
if (expected.finishTime === null) throw new Error('Authored recording did not finish in Node');

// Build into this lane's own directory. Other agents can continue editing
// their source files or rebuilding shared dist without changing this capture.
await build({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: frozenDir, emptyOutDir: true } });
const frozenIndexSha256 = crypto.createHash('sha256').update(fs.readFileSync(path.join(frozenDir, 'index.html'))).digest('hex');
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: frozenDir }, preview: { host: '127.0.0.1', port: 0 } });
const serverUrl = server.resolvedUrls?.local[0];
if (!serverUrl) throw new Error('Frozen preview server did not expose a local URL');
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--mute-audio'] });
const context = await browser.newContext({
  viewport: { width, height }, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
// A returning player reaches Menu directly; the career ledger is otherwise empty.
await context.addInitScript(() => { localStorage.setItem('rockhop.onboarded', '1'); });
const page = await context.newPage();
const pageErrors: string[] = [];
page.on('pageerror', e => pageErrors.push(e.message));
page.on('console', m => { if (m.type() === 'error') pageErrors.push(m.text()); });
let stage = 'boot';
let frameIndex = 0;
const marks: Array<Record<string, unknown>> = [];
const rideSamples: Array<Record<string, unknown>> = [];
const wallStart = Date.now();

async function state(): Promise<Record<string, unknown>> {
  return page.evaluate(() => {
    const h = window.__rockhop;
    const ledger = localStorage.getItem('rockhop.economy.v1');
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
      bikeX: h?.getState().bike.pos.x ?? null,
      award: document.querySelector('.tk-reward')?.textContent?.trim() ?? null,
      walletText: document.querySelector('.fr-wallet')?.textContent?.trim() ?? null,
      medal: document.querySelector('.fr-medal-name')?.textContent?.trim() ?? null,
      resultTime: document.querySelector('.fr-time-row .time')?.textContent?.trim() ?? null,
      garageWallet: document.querySelector('.gp-wallet')?.textContent?.trim() ?? null,
      ledger: ledger ? JSON.parse(ledger) : null,
    };
  });
}
async function mark(name: string): Promise<void> {
  const row: Record<string, unknown> = { name, frame: frameIndex, videoS: frameIndex / fps, ...(await state()) };
  marks.push(row);
  console.log(`[flow] ${name} frame=${frameIndex} screen=${String(row.screen)} phase=${String(row.phase)}`);
}
async function shot(): Promise<void> {
  await page.screenshot({ path: path.join(framesDir, `frame-${String(frameIndex).padStart(5, '0')}.png`), type: 'png', caret: 'hide', timeout: 180_000 });
  frameIndex++;
}
async function clockFrame(): Promise<void> {
  await page.clock.runFor(1000 / fps);
  await shot();
}
async function roll(count: number): Promise<void> {
  for (let i = 0; i < count; i++) await clockFrame();
}
async function pump(what: string, predicate: () => Promise<boolean>, cap = 180): Promise<void> {
  for (let i = 0; i < cap; i++) {
    if (await predicate()) return;
    await clockFrame();
    // Asset imports/decodes are real async work even while the page clock is paused.
    await new Promise(resolve => setTimeout(resolve, 15));
  }
  throw new Error(`Timed out waiting for ${what} after ${cap} captured frames`);
}
async function tap(selector: string): Promise<void> {
  const box = await page.locator(selector).boundingBox();
  if (!box) throw new Error(`No visible target: ${selector}`);
  await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
}
const live = (selector: string) => page.evaluate(s => !!document.querySelector(s), selector);
function encode(): void {
  execFileSync(resolveFfmpeg(), [
    '-y', '-hide_banner', '-loglevel', 'error', '-framerate', String(fps),
    '-i', path.join(framesDir, 'frame-%05d.png'),
    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
    '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', clip,
  ], { stdio: 'pipe', timeout: 240_000 });
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
  await mark('menu-painted');
  await roll(20);
  await tap('.menu-screen.live .menu-item[data-id=play]');
  await mark('tap-play');
  stage = 'map-first';
  await pump('painted live Map', async () => live('.tracks-screen.live .wm-world.loaded'), 180);
  await mark('map-painted');
  await roll(26);
  await tap('.tracks-screen.live .wm-ride');
  await mark('tap-ride');
  stage = 'countdown';
  await pump('C1 countdown', async () => page.evaluate(() => window.__rockhop?.app?.screen() === 'run' && window.__rockhop?.phase() === 'countdown'), 120);
  await mark('c1-countdown');
  // Show most of the real 3-2-1, then skip the last fraction from the same
  // loaded course. Reloading here restarts the renderer's async entry job;
  // under a paused RAF that paints only the biome fog for the whole ride.
  await roll(50);
  const beforeGo = await state();
  if (beforeGo.phase !== 'countdown' || beforeGo.entryHold || beforeGo.renderEntering) {
    throw new Error(`Course was not ready while countdown remained active: ${JSON.stringify(beforeGo)}`);
  }
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  const armed = await state();
  if (armed.screen !== 'run' || armed.phase !== 'riding' || armed.trackId !== rec.header.trackId || armed.seed !== rec.header.seed || armed.runTime !== 0 || armed.faults !== 0 || armed.renderEntering) {
    throw new Error(`Cannot align authored C1 recording with GO: ${JSON.stringify(armed)}`);
  }
  stage = 'ride';
  await mark('recording-go');
  for (let tick = 0; tick < inputs.length; tick += ticksPerFrame) {
    const batch = inputs.slice(tick, tick + ticksPerFrame);
    await page.evaluate(frames => {
      const h = window.__rockhop!;
      for (const input of frames) { h.setInput(input); h.step(1); }
      h.render();
    }, batch);
    await shot();
    if (tick % 120 === 0) {
      const snap = await state();
      if (snap.renderEntering) throw new Error(`Renderer re-entered placeholder during ride at tick ${tick + batch.length}`);
      rideSamples.push({ frame: frameIndex, inputTick: tick + batch.length, runTime: snap.runTime, bikeX: snap.bikeX, phase: snap.phase });
      if (tick % 600 === 0) console.log(`[flow] ride tick=${tick + batch.length}/${inputs.length} x=${Number(snap.bikeX).toFixed(1)} frame=${frameIndex}`);
    }
  }
  const exact = await page.evaluate(() => ({ hash: window.__rockhop!.hashState(), finishTime: window.__rockhop!.finishTime(), faults: window.__rockhop!.faults(), phase: window.__rockhop!.phase() }));
  if (exact.phase !== 'finished' || exact.hash !== expected.hash || exact.finishTime !== expected.finishTime || exact.faults !== 0) {
    throw new Error(`Authored ride mismatch: ${JSON.stringify({ exact, expected })}`);
  }
  await mark('exact-finish');
  stage = 'finish-report';
  await pump('actual live result', async () => live('.results.show.stage-5.live'), 100);
  await roll(30);
  const result = await state();
  if (result.award !== '+300' || result.walletText !== '300' || result.medal !== 'Diamond' || result.resultTime !== '0:30.350') {
    throw new Error(`Unexpected production finish reward: ${JSON.stringify(result)}`);
  }
  await mark('result-painted');
  await tap('.results.live .tile[data-id=menu]');
  await mark('tap-result-map');
  stage = 'map-return';
  await pump('painted Map after result', async () => live('.tracks-screen.live .wm-world.loaded'), 180);
  await mark('map-return-painted');
  await roll(25);
  await tap('.tracks-screen.live .backbtn');
  await mark('tap-map-menu');
  stage = 'menu-return';
  await pump('Menu after Map', async () => live('.menu-screen.live'), 100);
  await roll(14);
  await tap('.menu-screen.live .menu-item[data-id=garage]');
  await mark('tap-garage');
  stage = 'garage';
  await pump('painted Garage', async () => live('.garage-screen.live'), 120);
  await roll(35);
  const final = await state();
  if (final.screen !== 'garage' || !String(final.garageWallet).includes('300') || (final.ledger as {wallet?:number}|null)?.wallet !== 300) {
    throw new Error(`Garage did not reflect earned Scrap: ${JSON.stringify(final)}`);
  }
  await mark('garage-painted');
  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.slice(0, 5).join(' | ')}`);
  encode();
  const navLog = await page.evaluate(() => window.__rockhop?.navLog?.() ?? []);
  const report = {
    verdict: 'PASS',
    source: 'normal App UI in one headless Chromium page',
    viewportCss: [width, height], encodedVideo: [width, height + 1], fps, frames: frameIndex, seconds: frameIndex / fps,
    clock: 'Playwright clock paused after Menu boot; 50 ms App frames before/after manually stepped 120 Hz ride',
    ride: 'authored recording stepped through window.__rockhop, 6 exact input ticks per video frame',
    recording: path.relative(root, recordingPath), recordingSha256: crypto.createHash('sha256').update(recordingBytes).digest('hex'),
    expected, exact, result, final, marks, rideSamples, navLog,
    gitSha: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    browser: 'headless Chromium / ANGLE SwiftShader', server: 'own frozen Vite build', frozenIndexSha256,
    onboarding: 'returning player flag set; fresh career ledger',
    quality: await page.evaluate(() => window.__rockhop?.info().quality ?? null),
    pageErrors, wallMs: Date.now() - wallStart,
  };
  fs.writeFileSync(reportFile, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`[flow] PASS ${frameIndex} frames / ${(frameIndex / fps).toFixed(2)} s, ${path.relative(root, clip)}`);
} catch (error) {
  fs.rmSync(clip, { force: true });
  const blocker = { verdict: 'BLOCKED', stage, message: error instanceof Error ? error.message : String(error), framesCapturedButDiscarded: frameIndex, marks, pageErrors, wallMs: Date.now() - wallStart };
  fs.writeFileSync(blockerFile, `${JSON.stringify(blocker, null, 2)}\n`);
  console.error(`[flow] BLOCKED ${JSON.stringify(blocker)}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await context.close().catch(() => undefined);
  await browser.close().catch(() => undefined);
  await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.rmSync(frozenDir, { recursive: true, force: true });
  fs.rmSync(`${frozenDir}-maps`, { recursive: true, force: true });
}
