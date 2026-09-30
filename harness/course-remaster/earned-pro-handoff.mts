/** One fresh normal App page earns its first-eight medals, then explicitly purchases Pro. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { webkit } from 'playwright';
import { decodeJSON, encodeJSON, expandFrames } from '../../src/core/replay';
import { getTrack } from '../../src/tracks';
import { medalFor, targetTimeOf } from '../../src/game/rules';
import { STARTER_COURSE_IDS } from '../../src/ui/progress';
import { createSimFor } from '../lib/sim';
import { preview } from 'vite';
import { encodeMp4, probeVideo } from '../lib/ffmpeg';

const root = process.cwd();
const out = path.join(root, 'docs/evidence/course-remaster/earned-pro-handoff');
const framesDir = path.join(root, 'harness/out/earned-pro-handoff-frames');
const privateDist = path.join(root, 'harness/out/earned-pro-handoff-dist');
const frozenSource = path.join(root, 'harness/out/earned-pro-handoff-source.json');
const fps = 15, width = 852, height = 392;
const sha256 = (bytes: Buffer | string) => crypto.createHash('sha256').update(bytes).digest('hex');
const git = (...args: string[]) => execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim();
fs.mkdirSync(out, { recursive: true });
const failedAttempt = path.join(out, 'blocker.json');
if (fs.existsSync(failedAttempt)) fs.renameSync(failedAttempt, path.join(out, `harness-blocker-${Date.now()}.json`));
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
// Retain this sole frozen input across failed captures; shared dist is never reread on a rerun.
if (!fs.existsSync(path.join(privateDist, 'index.html'))) {
  fs.cpSync(path.join(root, 'dist'), privateDist, { recursive: true });
  fs.writeFileSync(frozenSource, JSON.stringify({ headAtFreeze: git('rev-parse', 'HEAD'),
    buildVersion: JSON.parse(fs.readFileSync(path.join(privateDist, 'version.json'), 'utf8')),
    workingAppSha256AtFreeze: sha256(fs.readFileSync(path.join(root, 'src/game/app.ts'))),
    workingHudSha256AtFreeze: sha256(fs.readFileSync(path.join(root, 'src/ui/hud.ts'))),
    note: 'Build version and served-byte hashes identify the actual capture; working source hashes are provenance, not a claim that the version SHA includes all current working source.' }));
}
const fileIds = ['index.html', 'version.json', ...fs.readdirSync(path.join(privateDist, 'assets')).filter(file => file.endsWith('.js')).map(file => `assets/${file}`)];
const frozenIdentities = Object.fromEntries(fileIds.map(file => [file, sha256(fs.readFileSync(path.join(privateDist, file)))]));
const source = JSON.parse(fs.readFileSync(frozenSource, 'utf8'));
const recordings = await Promise.all(STARTER_COURSE_IDS.map(async id => {
  const file = `harness/inputs/${id}/bot-3.json`, bytes = fs.readFileSync(path.join(root, file));
  const recording = decodeJSON(bytes.toString('utf8')), track = getTrack(id)!;
  const parentHeader = { ...recording.header };
  recording.header.seed = track.seed;
  const derivedFile = parentHeader.seed === track.seed ? null : `authored-seed-${id}.json`;
  const derivedBytes = encodeJSON(recording);
  if (derivedFile) fs.writeFileSync(path.join(out, derivedFile), derivedBytes);
  const inputs = expandFrames(recording), sim = await createSimFor(recording);
  for (const input of inputs) sim.step(input);
  assert.equal(sim.phase(), 'finished', `${id} reference does not finish`);
  assert.equal(sim.faults(), 0, `${id} reference faults`);
  const medal = medalFor(sim.state().finishTime!, sim.faults(), targetTimeOf(track), 'rookie', track.diamondGoal ? false : undefined);
  assert.equal(medal, id === 'c1-low-tide' ? 'platinum' : 'gold', `${id} authored-seed reference has wrong medal`);
  return { id, file, sha256: sha256(bytes), parentHeader, derivedFile, derivedSha256: derivedFile ? sha256(derivedBytes) : null, header: recording.header, inputs,
    expected: { hash: sim.hash(), finishTime: sim.state().finishTime, tick: sim.state().tick, faults: sim.faults() } };
}));
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir: privateDist }, preview: { host: '127.0.0.1', port: 0 } });
const serverUrl = server.resolvedUrls?.local[0]; assert(serverUrl, 'Frozen preview has no URL');
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const pageErrors: string[] = [], consoleErrors: string[] = [], served: Record<string, string> = {};
page.on('pageerror', error => pageErrors.push(error.message));
page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
const responseJobs: Promise<void>[] = [];
page.on('response', response => {
  const file = new URL(response.url()).pathname.slice(1);
  if (frozenIdentities[file]) responseJobs.push(response.body().then(bytes => { served[file] = sha256(bytes); }));
});
let stage = 'boot', frame = 0, filming = false;
const marks: Record<string, unknown>[] = [], rides: Record<string, unknown>[] = [];
async function state() {
  return page.evaluate(() => {
    const h = window.__rockhop!;
    return { screen: h.app!.screen(), phase: h.phase(), trackId: h.info().trackId, bike: h.info().bike,
      ledger: JSON.parse(localStorage.getItem('rockhop.economy.v1') ?? '{}'),
      reward: document.querySelector('.tk-reward')?.textContent?.trim(), next: document.querySelector('.results [data-id="next"]')?.textContent?.trim(),
      nextDisabled: document.querySelector<HTMLButtonElement>('.results [data-id="next"]')?.disabled,
      resultMedal: document.querySelector('.fr-medal-name')?.textContent?.trim(), garageState: document.querySelector('.gp-bike-state')?.textContent?.trim() };
  });
}
async function mark(name: string) {
  const row = { name, frame, videoS: frame / fps, onVideo: filming, ...(await state()) };
  marks.push(row); console.log(`[earned-pro] ${name} ${row.screen} wallet=${row.ledger.wallet}`); return row;
}
async function shot() {
  if (!filming) return;
  await page.screenshot({ path: path.join(framesDir, `frame-${String(frame++).padStart(5, '0')}.png`), caret: 'hide' });
}
async function clockFrame() { await page.clock.runFor(1000 / fps); await shot(); }
async function roll(n: number) { for (let i = 0; i < n; i++) await clockFrame(); }
async function pump(label: string, predicate: () => Promise<boolean>, cap = 240) {
  for (let i = 0; i < cap; i++) {
    if (await predicate()) return;
    await clockFrame(); await new Promise(resolve => setTimeout(resolve, 15));
  }
  throw new Error(`Timed out: ${label}`);
}
async function tap(selector: string) {
  const box = await page.locator(selector).boundingBox(); assert(box, `Missing target ${selector}`);
  await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);
}
async function playReference(row: typeof recordings[number]) {
  stage = `ride:${row.id}`;
  await page.evaluate(id => window.__rockhop!.app!.play(id), row.id);
  await pump(`${row.id} ready`, () => page.evaluate(id => {
    const h = window.__rockhop!;
    return h.app!.screen() === 'run' && h.info().trackId === id && h.info().entryHold === false &&
      (h.info().render as { entering?: boolean } | null)?.entering === false;
  }, row.id));
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  const start = await page.evaluate(() => ({ time: window.__rockhop!.runTime(), bike: window.__rockhop!.info().bike, seed: window.__rockhop!.info().seed }));
  assert.equal(start.time, 0, `${row.id} GO misaligned`); assert.equal(start.bike, 'rookie'); assert.equal(start.seed, row.header.seed);
  await page.evaluate(inputs => {
    const h = window.__rockhop!;
    for (const input of inputs) { h.setInput(input); h.step(1); }
    h.render();
  }, row.inputs);
  const actual = await page.evaluate(() => ({ hash: window.__rockhop!.hashState(), finishTime: window.__rockhop!.finishTime(), tick: window.__rockhop!.getState().tick, faults: window.__rockhop!.faults() }));
  assert.deepEqual(actual, row.expected, `${row.id} Node/browser finish mismatch`);
  await mark(`${row.id}:exact-finish`);
  // Game publishes the result after its finish hold; leaving sooner cancels the pending reward.
  await pump(`${row.id} published result`, () => page.locator('.results.show.stage-5.live').count().then(Boolean));
  const finish = await mark(`${row.id}:published-result`);
  rides.push({ id: row.id, recording: row.file, recordingSha256: row.sha256, parentHeader: row.parentHeader, derivedRecording: row.derivedFile, derivedRecordingSha256: row.derivedSha256, header: row.header, expected: row.expected, actual, ledger: finish.ledger, reward: finish.reward, medal: finish.resultMedal });
  return finish;
}
try {
  const clock0 = Date.now(); await page.clock.install({ time: clock0 });
  const url = new URL(serverUrl); url.searchParams.set('sw', '0'); url.searchParams.set('audio', '0');
  await page.goto(url.toString(), { waitUntil: 'commit' });
  await page.waitForFunction(() => !document.getElementById('loader') && !!document.querySelector('.menu-screen.live') && !!window.__rockhop?.ready, undefined, { timeout: 180_000 });
  await page.clock.pauseAt(Math.max(clock0, Date.now()) + 1000);
  const initial = await mark('fresh-menu'); assert.equal(initial.ledger.wallet, 0); assert.equal(Object.keys(initial.ledger.medals).length, 0);
  for (const row of recordings) await playReference(row);
  const earned = await state(); assert.equal(earned.ledger.wallet, 1840); assert.equal(earned.ledger.proOwned, false);
  assert.equal(Object.values(earned.ledger.medals).filter(m => m === 'gold').length, 7);
  assert.equal(Object.values(earned.ledger.medals).filter(m => m === 'platinum').length, 1);
  filming = true; stage = 'd2-result';
  await pump('D2 live result', () => page.locator('.results.show.stage-5.live').count().then(Boolean));
  const d2 = await mark('earned-d2-buy-pro'); assert.match(d2.next ?? '', /Buy Pro/); assert.equal(d2.nextDisabled, false);
  await roll(20); await tap('.results.live [data-id="next"]'); stage = 'garage';
  await pump('Pro Garage', () => page.locator('.garage-screen.live .gp-buy').count().then(Boolean));
  const garage = await mark('explicit-purchase-ready'); assert.equal(garage.screen, 'garage'); assert.equal(garage.ledger.wallet, 1840); assert.equal(garage.ledger.proOwned, false);
  await roll(20); await tap('.garage-screen.live .gp-buy'); await roll(20);
  const purchased = await mark('purchased-and-equipped'); assert.equal(purchased.ledger.wallet, 0); assert.equal(purchased.ledger.proOwned, true); assert.equal(purchased.ledger.equipped, 'pro');
  await tap('.garage-screen.live .backbtn'); await pump('Menu', () => page.locator('.menu-screen.live').count().then(Boolean));
  await tap('.menu-screen.live .menu-item[data-id="play"]'); stage = 'map';
  await pump('Map', () => page.locator('.tracks-screen.live .wm-quick').count().then(Boolean));
  assert.match(await page.locator('.wm-quick').textContent() ?? '', /Play next/);
  await roll(15); await tap('.tracks-screen.live .wm-quick'); stage = 'd3-launch';
  await pump('D3 Pro ready', () => page.evaluate(() => {
    const h = window.__rockhop!; return h.app!.screen() === 'run' && h.info().trackId === 'd3-rope-walk' && h.info().bike === 'pro' && h.info().entryHold === false;
  }));
  await mark('d3-pro-launched'); await roll(20); filming = false;
  await page.evaluate(() => { window.__rockhop!.app!.quit(); window.__rockhop!.app!.goto('garage'); });
  await pump('Starter chip after Pro launch', () => page.locator('.garage-screen.live [data-bike=rookie]').count().then(Boolean));
  await tap('.garage-screen.live [data-bike=rookie]');
  assert.equal((await state()).ledger.equipped, 'rookie');
  const repeated = await playReference(recordings[7]!);
  assert.equal(repeated.ledger.wallet, 0); assert.equal(repeated.reward, 'No new Scrap'); assert.equal(repeated.ledger.proOwned, true);
  await Promise.all(responseJobs);
  for (const [file, hash] of Object.entries(served)) assert.equal(hash, frozenIdentities[file], `Served ${file} drifted`);
  assert.equal(pageErrors.length, 0); assert.equal(consoleErrors.length, 0);
  const clip = path.join(out, 'played-handoff.mp4');
  await encodeMp4({ fps, pattern: path.join(framesDir, 'frame-%05d.png'), out: clip, crf: 25, preset: 'medium' });
  const report = { verdict: 'PASS', engine: 'headless WebKit', viewport: [width, height], source, frozenIdentities, served,
    method: 'One initially empty normal App page; only onboarded flag set. First eight checked-in inputs manually stepped through App.play and Game finishes with paused browser clock. No medals, PBs, wallet, ownership or equip state seeded. Earlier rides off-video. Actual DOM taps perform the explicit purchase and D3 launch. This is input-driven integration evidence, not human difficulty or wall-time pacing.',
    rides, marks, repeated, pageErrors, consoleErrors, video: { ...(await probeVideo(clip)), sha256: sha256(fs.readFileSync(clip)), audio: 'none' } };
  fs.writeFileSync(path.join(out, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  console.log(`[earned-pro] PASS ${frame} frames`);
} catch (error) {
  fs.writeFileSync(path.join(out, 'blocker.json'), `${JSON.stringify({ verdict: 'BLOCKED', source, frozenIdentities, served, stage, message: String(error), marks, rides, state: await state().catch(() => null), pageErrors, consoleErrors }, null, 2)}\n`);
  console.error(`[earned-pro] BLOCKED ${stage}: ${String(error)}`); process.exitCode = 1;
} finally {
  await context.close(); await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve())); fs.rmSync(framesDir, { recursive: true, force: true });
}
