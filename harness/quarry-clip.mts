/** Played, silent 852x392 landscape clip from an exact Quarry bot input recording. */
import fs from 'node:fs';
import path from 'node:path';
import { launchBrowser } from './lib/browser';
import { encodeMp4 } from './lib/ffmpeg';
import { HookClient, openGame } from './lib/hook';
import { startServer } from './lib/server';
import { decodeJSON, expandFrames } from '../src/core/replay';
import { createQuarrySim } from './quarry-sim';

const id = process.argv[2] ?? 'd1-dust-devil';
const bike = process.argv[3] === 'pro' ? 'pro' : 'rookie';
const xStart = Number(process.argv[4] ?? 75);
const xEnd = Number(process.argv[5] ?? 150);
const prefix = `${id}-${bike}`;
const outDir = path.resolve('docs/evidence/quarry-retarget');
const rec = decodeJSON(fs.readFileSync(path.join(outDir, `${prefix}-bot.json`), 'utf8'));
const frames = expandFrames(rec);
const sim = await createQuarrySim(id, rec.header.seed, rec.header.physicsHz, bike);
let startTick = -1;
let endTick = -1;
for (let tick = 0; tick < frames.length; tick++) {
  const x = sim.state().bike.pos.x;
  sim.step(frames[tick]!);
  if (startTick < 0 && x >= xStart) startTick = tick + 1;
  if (endTick < 0 && x >= xEnd) { endTick = tick + 1; break; }
}
if (startTick < 0 || endTick < 0) throw new Error(`recording misses ${xStart}..${xEnd}`);
const ticksPerFrame = 6;
startTick = Math.floor(Math.max(0, startTick - 36) / ticksPerFrame) * ticksPerFrame;
endTick = Math.ceil(Math.min(frames.length, endTick + 24) / ticksPerFrame) * ticksPerFrame;
const expected = await createQuarrySim(id, rec.header.seed, rec.header.physicsHz, bike);
for (const frame of frames.slice(0, endTick)) expected.step(frame);
const expectedHash = expected.hash();

const framesDir = path.join(outDir, `.frames-${prefix}`);
fs.mkdirSync(framesDir, { recursive: true });
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
try {
  const page = browser.page;
  await openGame(page, server.url);
  const hook = new HookClient(page);
  await hook.setBike(bike);
  if (!(await hook.loadTrack(id, rec.header.seed))) throw new Error(`registered ${id} unavailable`);
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
  let index = 0;
  for (let tick = startTick; tick < endTick; tick += ticksPerFrame) {
    const info = await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const input of inputs) { h.setInput(input); h.step(1); }
      h.render();
      return { camera: h.camera?.(), phase: h.phase() };
    }, frames.slice(tick, tick + ticksPerFrame));
    if (info.camera) {
      const { bikeScreenX, bikeScreenY, roll = 0 } = info.camera;
      maxAbsCameraRoll = Math.max(maxAbsCameraRoll, Math.abs(roll));
      if (info.phase === 'riding' && (bikeScreenX < 0.2 || bikeScreenX > 0.8 || bikeScreenY < 0.2 || bikeScreenY > 0.8)) cameraBoxViolations++;
    }
    await page.screenshot({ path: path.join(framesDir, `frame-${String(index++).padStart(5, '0')}.png`), type: 'png', animations: 'disabled', caret: 'hide' });
  }
  await encodeMp4({ fps: 20, pattern: path.join(framesDir, 'frame-%05d.png'), out: path.join(outDir, `${prefix}-clip.mp4`), crf: 22, preset: 'fast' });
  const browserHash = await hook.hashState();
  const report = { id, bike, width: 852, height: 392, fps: 20, xStart, xEnd, startTick, endTick, frames: index,
    cameraBoxViolations, maxAbsCameraRoll, expectedHash, browserHash };
  fs.writeFileSync(path.join(outDir, `${prefix}-clip.json`), `${JSON.stringify(report, null, 2)}\n`);
  if (browserHash !== expectedHash) throw new Error(`browser/Node replay mismatch: ${JSON.stringify(report)}`);
  process.stdout.write(`${JSON.stringify(report)}\n`);
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await browser.close();
  await server.close();
}
