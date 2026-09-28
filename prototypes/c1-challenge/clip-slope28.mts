/** Silent played browser clip of the unregistered C1 prototype at phone landscape size. */
import fs from 'node:fs';
import path from 'node:path';
import { createSim } from '../../harness/lib/sim';
import { launchBrowser } from '../../harness/lib/browser';
import { encodeMp4, contactSheet } from '../../harness/lib/ffmpeg';
import { HookClient, openGame } from '../../harness/lib/hook';
import { startServer } from '../../harness/lib/server';
import { decodeJSON, expandFrames, type InputFrame } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { makeSlope } from './candidate-slope';
const C1_CHALLENGE = makeSlope('c1-low-tide', 28, 2.8);

registerTrack(C1_CHALLENGE);
const bike = process.argv[2] === 'pro' ? 'pro' : 'rookie';
const goOnly = process.argv[3] === 'go';
const rec = decodeJSON(fs.readFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-skilled-slope28.json`, import.meta.url), 'utf8'));
const frames: InputFrame[] = goOnly
  ? Array.from({ length: 25 * 120 }, () => ({ throttle: 1, brake: 0, lean: 0, hop: false, restart: false }))
  : expandFrames(rec);
const sim = await createSim(C1_CHALLENGE.id, rec.header.seed, 120, { bike });
let startTick = -1, endTick = -1;
for (let tick = 0; tick < frames.length; tick++) {
  const events = sim.step(frames[tick]!);
  const x = sim.state().bike.pos.x;
  if (startTick < 0 && x >= 188) startTick = tick + 1;
  if (goOnly && events.some((e) => e.type === 'fault')) { endTick = tick + 1 + 120; break; }
  if (!goOnly && endTick < 0 && x >= 244) { endTick = tick + 1; break; }
}
if (startTick < 0 || endTick < 0) throw new Error(`recording misses obstacle: ${startTick},${endTick}`);
startTick = Math.max(0, startTick - 120);
endTick = Math.min(frames.length, endTick + 24);
const fps = 24;
const ticksPerFrame = 120 / fps;
startTick = Math.floor(startTick / ticksPerFrame) * ticksPerFrame;
endTick = Math.ceil(endTick / ticksPerFrame) * ticksPerFrame;
const endSim = await createSim(C1_CHALLENGE.id, rec.header.seed, 120, { bike });
for (const frame of frames.slice(0, endTick)) endSim.step(frame);
const expectedWindowHash = endSim.hash();

const outDir = new URL(`../../docs/evidence/c1-challenge/clips/slope28/${bike}${goOnly ? '-go' : ''}/`, import.meta.url);
fs.mkdirSync(outDir, { recursive: true });
const framesDir = path.join(outDir.pathname, 'frames');
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
try {
  const page = browser.page;
  await openGame(page, server.url);
  const injected = await page.evaluate(async () => {
    const [{ makeSlope }, { registerTrack, getTrack }] = await Promise.all([
      import('/prototypes/c1-challenge/candidate-slope.ts'),
      import('/src/tracks/index.ts'),
    ]);
    const C1_CHALLENGE = makeSlope('c1-low-tide', 28, 2.8);
    registerTrack(C1_CHALLENGE);
    return { id: getTrack(C1_CHALLENGE.id)?.id, obstacles: getTrack(C1_CHALLENGE.id)?.obstacles.length, checkpoints: getTrack(C1_CHALLENGE.id)?.checkpoints.length };
  });
  process.stdout.write(`injected ${JSON.stringify(injected)}\n`);
  const hook = new HookClient(page);
  await hook.setBike(bike);
  if (!(await hook.loadTrack(C1_CHALLENGE.id, rec.header.seed))) throw new Error('browser could not load candidate');
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  await hook.resize(852, 392);
  await hook.setQuality('low');
  for (let t = 0; t < startTick; t += 600) {
    const chunk: InputFrame[] = frames.slice(t, Math.min(startTick, t + 600));
    await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const f of inputs) { h.setInput(f); h.step(1); }
    }, chunk);
  }
  const pictures = [];
  let index = 0;
  for (let tick = startTick; tick < endTick; tick += ticksPerFrame) {
    const chunk = frames.slice(tick, tick + ticksPerFrame);
    const info = await page.evaluate((inputs) => {
      const h = window.__rockhop!;
      for (const f of inputs) { h.setInput(f); h.step(1); }
      h.render();
      return { x: h.getState().bike.pos.x, camera: h.camera?.() };
    }, chunk);
    const pic = path.join(framesDir, `frame-${String(index++).padStart(5, '0')}.png`);
    await page.screenshot({ path: pic, type: 'png', animations: 'disabled', caret: 'hide' });
    pictures.push(pic);
    if (index % 24 === 0) process.stdout.write(`frame ${index} x=${info.x.toFixed(1)}\n`);
  }
  const mp4 = path.join(outDir.pathname, 'clip.mp4');
  await encodeMp4({ fps, pattern: path.join(framesDir, 'frame-%05d.png'), out: mp4, crf: 22, preset: 'fast' });
  await contactSheet({ frames: pictures, out: path.join(outDir.pathname, 'sheet.jpg'), cols: 4, rows: 2, tileWidth: 426 });
  const browserHash = await hook.hashState();
  if (browserHash !== expectedWindowHash) throw new Error(`browser/node window hash mismatch: ${browserHash} vs ${expectedWindowHash}`);
  fs.writeFileSync(path.join(outDir.pathname, 'clip.json'), `${JSON.stringify({ bike, input: goOnly ? 'held GO' : 'skilled recording', fps, width: 852, height: 392, startTick, endTick, frames: pictures.length, seconds: pictures.length / fps, source: goOnly ? 'constant GO' : `${bike}-skilled-slope28.json`, nodeHashAtWindowEnd: expectedWindowHash, browserHashAtWindowEnd: browserHash }, null, 2)}\n`);
  process.stdout.write(`${mp4} ${pictures.length} frames\n`);
} finally {
  fs.rmSync(framesDir, { recursive: true, force: true });
  await browser.close();
  await server.close();
}
