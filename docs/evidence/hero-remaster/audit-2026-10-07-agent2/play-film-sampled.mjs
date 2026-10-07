/** Audit playback: continuous silent1x; at most64 PNG captures, all callback metadata.
 * Original play-film retained all full-resolution PNGs in browser memory.
 * Sampling limits permit historical defect review only, never contact/acceptance. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { webkit } from 'playwright';

const [outArg, ...movies] = process.argv.slice(2);
assert(outArg && movies.length);
const out = path.resolve(outArg);
assert(!fs.existsSync(out));
fs.mkdirSync(out, { recursive: true });
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const inputs = movies.map(file => ({ file: path.resolve(file), bytes: fs.readFileSync(file) }));
const server = http.createServer((req, res) => {
  const i = Number(req.url?.slice(1));
  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<!doctype html><video muted playsinline preload="auto"></video><canvas></canvas>');
    return;
  }
  const item = inputs[i];
  if (!item) { res.writeHead(404); res.end(); return; }
  const range = req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
  const start = range ? Number(range[1]) : 0;
  const end = range?.[2] ? Math.min(Number(range[2]), item.bytes.length - 1) : item.bytes.length - 1;
  assert(start <= end && start >= 0);
  res.writeHead(range ? 206 : 200, {
    'Content-Type': 'video/mp4', 'Accept-Ranges': 'bytes',
    'Content-Length': end - start + 1,
    ...(range ? { 'Content-Range': `bytes ${start}-${end}/${item.bytes.length}` } : {}),
  });
  res.end(item.bytes.subarray(start, end + 1));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await webkit.launch({ headless: true });
const results = [];
const errors = [];
try {
  for (let i = 0; i < inputs.length; i++) {
    const page = await browser.newPage({ viewport: { width: 768, height: 768 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    const result = await page.evaluate(async index => {
      const video = document.querySelector('video');
      const canvas = document.querySelector('canvas');
      if (!video.requestVideoFrameCallback) throw new Error('Actual presented video callback required');
      video.muted = true; video.volume = 0; video.playbackRate = 1;
      const ready = new Promise((resolve, reject) => {
        video.addEventListener('loadedmetadata', resolve, { once: true });
        video.addEventListener('error', () => reject(new Error(`Media error ${video.error?.code}`)), { once: true });
      });
      video.src = `/${index}`;
      await ready;
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      const frames = [], events = [];
      for (const name of ['play', 'playing', 'waiting', 'stalled', 'seeking', 'seeked', 'pause', 'ended'])
        video.addEventListener(name, () => events.push({ name, mediaTime: video.currentTime, wallMs: performance.now() }));
      let ended = false;
      let nextCapture = 0;
      const capturePeriod = video.duration / 63;
      const onFrame = (now, metadata) => {
        const frame = { mediaTime: metadata.mediaTime, presentedFrames: metadata.presentedFrames, callbackWallMs: now };
        if (metadata.mediaTime >= nextCapture) {
          context.drawImage(video, 0, 0);
          frame.png = canvas.toDataURL('image/png').split(',')[1];
          nextCapture += capturePeriod;
        }
        frames.push(frame);
        if (!ended) video.requestVideoFrameCallback(onFrame);
      };
      video.requestVideoFrameCallback(onFrame);
      const wallStart = performance.now();
      await new Promise(async (resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Playback timeout')), (video.duration + 10) * 1000);
        video.addEventListener('ended', () => { ended = true; clearTimeout(timeout); resolve(); }, { once: true });
        try { await video.play(); } catch (error) { clearTimeout(timeout); reject(error); }
      });
      return { frames, events, duration: video.duration, width: video.videoWidth, height: video.videoHeight,
        wallSeconds: (performance.now() - wallStart) / 1000, ended: video.ended,
        finalTime: video.currentTime, muted: video.muted, volume: video.volume, playbackRate: video.playbackRate,
        navigatorWebdriver: navigator.webdriver, quality: video.getVideoPlaybackQuality?.() ?? null };
    }, i);
    assert(result.ended && result.muted && result.volume === 0 && result.playbackRate === 1);
    assert(result.navigatorWebdriver && result.frames.length > 0);
    assert(!result.events.some(event => ['seeking', 'seeked', 'stalled'].includes(event.name)));
    assert(result.frames.every((frame, j) => !j || frame.mediaTime > result.frames[j-1].mediaTime));
    const directory = path.join(out, String(i)); fs.mkdirSync(directory);
    for (let j = 0; j < result.frames.length; j++) {
      const frame = result.frames[j];
      if (!frame.png) continue;
      const bytes = Buffer.from(frame.png, 'base64');
      frame.path = path.join(directory, `${String(j).padStart(4, '0')}.png`);
      frame.sha256 = sha(bytes); fs.writeFileSync(frame.path, bytes); delete frame.png;
    }
    result.source = { path: inputs[i].file, sha256: sha(inputs[i].bytes) };
    result.recipeSHA256 = sha(fs.readFileSync(new URL(import.meta.url)));
    result.accepted = false;
    result.capturedPNGFrames = result.frames.filter(frame => frame.path).length;
    result.capturePolicy = 'At most64 full-resolution actual presented PNGs during uninterrupted1x playback; all callbacks retained as metadata. No seeks or poses. Historical temporal defect review only.';
    assert(result.capturedPNGFrames <= 64);
    result.limits = 'Continuous actual silent playback and presented-frame capture only; root must interpret temporal evidence. Callback omissions must remain visible. No art/geometry/engine/device acceptance.';
    results.push(result);
    await page.close();
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close(); await new Promise(resolve => server.close(resolve));
  fs.writeFileSync(path.join(out, 'playback.json'), JSON.stringify({ results, errors }, null, 2) + '\n');
}
console.log(JSON.stringify(results.map(({ source, frames, duration, wallSeconds }) => ({ source, capturedFrames: frames.length, duration, wallSeconds }))));
