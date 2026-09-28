/** Silent phone-landscape capture of the registered C2 line and its real HUD cue. */
import fs from 'node:fs';
import path from 'node:path';
import { createSim } from './lib/sim';
import { launchBrowser } from './lib/browser';
import { encodeMp4 } from './lib/ffmpeg';
import { HookClient, openGame } from './lib/hook';
import { startServer } from './lib/server';
import { decodeJSON, expandFrames } from '../src/core/replay';

const bike = process.argv[2] === 'pro' ? 'pro' : 'rookie';
const recordingFile = new URL(`./inputs/c2-crane-hop/bot-3${bike === 'pro' ? '-pro' : ''}.json`, import.meta.url);
const rec = decodeJSON(fs.readFileSync(recordingFile, 'utf8'));
const frames = expandFrames(rec);
const sim = await createSim(rec.header.trackId, rec.header.seed, rec.header.physicsHz, { bike });
let startTick = -1;
let endTick = -1;
for (let tick = 0; tick < frames.length; tick++) {
  const x = sim.state().bike.pos.x;
  sim.step(frames[tick]!);
  if (startTick < 0 && x >= 280) startTick = tick + 1;
  if (endTick < 0 && x >= 352) { endTick = tick + 1; break; }
}
if (startTick < 0 || endTick < 0) throw new Error('recording misses crane window');
const ticksPerFrame = 6;
startTick = Math.floor(Math.max(0, startTick - 48) / ticksPerFrame) * ticksPerFrame;
endTick = Math.ceil(Math.min(frames.length, endTick + 24) / ticksPerFrame) * ticksPerFrame;
const endSim = await createSim(rec.header.trackId, rec.header.seed, rec.header.physicsHz, { bike });
for (const frame of frames.slice(0, endTick)) endSim.step(frame);
const expectedHash = endSim.hash();

const outDir = path.resolve('docs/evidence/c2-production-integration', bike);
const framesDir = path.join(outDir, 'frames');
fs.mkdirSync(framesDir, { recursive: true });
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
try {
  const page = browser.page;
  await openGame(page, server.url);
  const hook = new HookClient(page);
  await hook.setBike(bike);
  if (!(await hook.loadTrack(rec.header.trackId, rec.header.seed))) throw new Error('registered C2 unavailable');
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  await hook.resize(852, 392);
  await hook.setQuality('low');
  for (let tick = 0; tick < startTick; tick += 600) {
    const chunk = frames.slice(tick, Math.min(startTick, tick + 600));
    await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const input of inputs) { h.setInput(input); h.step(1); }
    }, chunk);
  }
  let cameraBoxViolations = 0;
  let maxAbsCameraRoll = 0;
  let cueFrames = 0;
  let cueOutsideLane = 0;
  let index = 0;
  for (let tick = startTick; tick < endTick; tick += ticksPerFrame) {
    const info = await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const input of inputs) { h.setInput(input); h.step(1); }
      h.render();
      const cue = document.querySelector<HTMLElement>('.skill-cue');
      return { x: h.getState().bike.pos.x, camera: h.camera?.(), phase: h.phase(),
        cueVisible: cue?.classList.contains('show') && getComputedStyle(cue).display !== 'none',
        cueText: cue?.textContent ?? '' };
    }, frames.slice(tick, tick + ticksPerFrame));
    if (info.camera) {
      const { bikeScreenX, bikeScreenY, roll = 0 } = info.camera;
      maxAbsCameraRoll = Math.max(maxAbsCameraRoll, Math.abs(roll));
      if (info.phase === 'riding' && (bikeScreenX < 0.2 || bikeScreenX > 0.8 || bikeScreenY < 0.2 || bikeScreenY > 0.8)) cameraBoxViolations++;
    }
    if (info.cueVisible) {
      cueFrames++;
      if (info.x < 284 || info.x >= 323 || !info.cueText.includes('RELEASE OR LEAN FORWARD')) cueOutsideLane++;
    }
    await page.screenshot({ path: path.join(framesDir, `frame-${String(index++).padStart(5, '0')}.png`), type: 'png', animations: 'disabled', caret: 'hide' });
  }
  await encodeMp4({ fps: 20, pattern: path.join(framesDir, 'frame-%05d.png'), out: path.join(outDir, 'clip.mp4'), crf: 22, preset: 'fast' });
  const browserHash = await hook.hashState();
  const report = { bike, width: 852, height: 392, fps: 20, startTick, endTick, frames: index,
    cueFrames, cueOutsideLane, cameraBoxViolations, maxAbsCameraRoll, expectedHash, browserHash };
  fs.writeFileSync(path.join(outDir, 'clip.json'), `${JSON.stringify(report, null, 2)}\n`);
  if (browserHash !== expectedHash || cueFrames === 0 || cueOutsideLane > 0 || cameraBoxViolations > 0) {
    throw new Error(`integrated clip verification failed: ${JSON.stringify(report)}`);
  }
  process.stdout.write(`${JSON.stringify(report)}\n`);
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await browser.close();
  await server.close();
}
