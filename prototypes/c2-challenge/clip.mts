/** Silent played browser clip of the unregistered C2 jump at phone landscape size. */
import fs from 'node:fs';
import path from 'node:path';
import { createSim } from '../../harness/lib/sim';
import { launchBrowser } from '../../harness/lib/browser';
import { encodeMp4, contactSheet } from '../../harness/lib/ffmpeg';
import { HookClient, openGame } from '../../harness/lib/hook';
import { startServer } from '../../harness/lib/server';
import { decodeJSON, expandFrames, type InputFrame } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const bike = process.argv[2] === 'pro' ? 'pro' : 'rookie';
const goOnly = process.argv[3] === 'go';
const rec = decodeJSON(fs.readFileSync(new URL(`../../docs/evidence/c2-challenge/${bike}-skilled.json`, import.meta.url), 'utf8'));
const frames: InputFrame[] = goOnly
  ? Array.from({ length: 45 * 120 }, () => ({ throttle: 1, brake: 0, lean: 0, hop: false, restart: false }))
  : expandFrames(rec);
const sim = await createSim(C2_CHALLENGE.id, rec.header.seed, 120, { bike });
let startTick = -1;
let endTick = -1;
for (let tick = 0; tick < frames.length; tick++) {
  const beforeX = sim.state().bike.pos.x;
  const events = sim.step(frames[tick]!);
  if (startTick < 0 && beforeX >= 291) startTick = tick + 1;
  if (goOnly && beforeX > 280 && events.some((event) => event.type === 'fault')) { endTick = tick + 1 + 96; break; }
  if (!goOnly && endTick < 0 && beforeX >= 352) { endTick = tick + 1; break; }
}
if (startTick < 0 || endTick < 0) throw new Error(`recording misses crane: ${startTick}, ${endTick}`);
startTick = Math.max(0, startTick - 120);
endTick = Math.min(frames.length, endTick + 24);
const fps = 20;
const ticksPerFrame = 120 / fps;
startTick = Math.floor(startTick / ticksPerFrame) * ticksPerFrame;
endTick = Math.ceil(endTick / ticksPerFrame) * ticksPerFrame;
const endSim = await createSim(C2_CHALLENGE.id, rec.header.seed, 120, { bike });
for (const frame of frames.slice(0, endTick)) endSim.step(frame);
const expectedWindowHash = endSim.hash();

const outDir = new URL(`../../docs/evidence/c2-challenge/clips/${bike}-${goOnly ? 'go' : 'skilled'}/`, import.meta.url);
fs.mkdirSync(outDir, { recursive: true });
const framesDir = path.join(outDir.pathname, 'frames');
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
try {
  const page = browser.page;
  await openGame(page, server.url);
  await page.evaluate(async () => {
    const [{ C2_CHALLENGE }, { registerTrack }] = await Promise.all([
      import('/prototypes/c2-challenge/candidate.ts'), import('/src/tracks/index.ts'),
    ]);
    registerTrack(C2_CHALLENGE);
  });
  const hook = new HookClient(page);
  await hook.setBike(bike);
  if (!(await hook.loadTrack(C2_CHALLENGE.id, rec.header.seed))) throw new Error('browser could not load candidate');
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  await hook.resize(852, 392);
  await hook.setQuality('low');
  await page.evaluate(async () => {
    const { installC2Cue } = await import('/prototypes/c2-challenge/cue.ts');
    (window as unknown as { __c2CueUpdate: (x: number) => void }).__c2CueUpdate = installC2Cue();
  });
  for (let tick = 0; tick < startTick; tick += 600) {
    const chunk = frames.slice(tick, Math.min(startTick, tick + 600));
    await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const input of inputs) { h.setInput(input); h.step(1); }
    }, chunk);
  }
  const pictures = [];
  let index = 0;
  let cameraBoxViolations = 0;
  let maxAbsCameraRoll = 0;
  for (let tick = startTick; tick < endTick; tick += ticksPerFrame) {
    const chunk = frames.slice(tick, tick + ticksPerFrame);
    const info = await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const input of inputs) { h.setInput(input); h.step(1); }
      h.render();
      const x = h.getState().bike.pos.x;
      (window as unknown as { __c2CueUpdate: (x: number) => void }).__c2CueUpdate(x);
      return { x, camera: h.camera?.(), phase: h.phase() };
    }, chunk);
    if (info.camera) {
      const { bikeScreenX, bikeScreenY, roll = 0 } = info.camera;
      maxAbsCameraRoll = Math.max(maxAbsCameraRoll, Math.abs(roll));
      if (info.phase === 'riding' && (bikeScreenX < 0.2 || bikeScreenX > 0.8 || bikeScreenY < 0.2 || bikeScreenY > 0.8)) cameraBoxViolations++;
    }
    const picture = path.join(framesDir, `frame-${String(index++).padStart(5, '0')}.png`);
    await page.screenshot({ path: picture, type: 'png', animations: 'disabled', caret: 'hide' });
    pictures.push(picture);
    if (index % 25 === 0) process.stdout.write(`${bike} ${goOnly ? 'GO' : 'skill'} frame ${index} x=${info.x.toFixed(1)}\n`);
  }
  const mp4 = path.join(outDir.pathname, 'clip.mp4');
  await encodeMp4({ fps, pattern: path.join(framesDir, 'frame-%05d.png'), out: mp4, crf: 22, preset: 'fast' });
  await contactSheet({ frames: pictures, out: path.join(outDir.pathname, 'sheet.jpg'), cols: 4, rows: 2, tileWidth: 426 });
  const browserHash = await hook.hashState();
  if (browserHash !== expectedWindowHash) throw new Error(`browser/node window hash mismatch: ${browserHash} vs ${expectedWindowHash}`);
  fs.writeFileSync(path.join(outDir.pathname, 'clip.json'), `${JSON.stringify({ bike, input: goOnly ? 'held GO' : 'skilled recording', fps, width: 852, height: 392, startTick, endTick, frames: pictures.length, seconds: pictures.length / fps, source: goOnly ? 'constant GO' : `${bike}-skilled.json`, cue: 'prototype-only crane landing cue, visible x=284..323', nodeHashAtWindowEnd: expectedWindowHash, browserHashAtWindowEnd: browserHash, cameraBoxViolations, maxAbsCameraRoll }, null, 2)}\n`);
  process.stdout.write(`${mp4} ${pictures.length} frames\n`);
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await browser.close();
  await server.close();
}
