/** Silent headless technical playback; the parent alone judges appearance. */
import { createServer } from 'node:http';
import { createReadStream } from 'node:fs';
import { stat, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
const [movieArgument, outputArgument] = process.argv.slice(2);
if (!movieArgument || !outputArgument) throw new Error('movie and output paths required');
const movie = resolve(movieArgument);
const output = resolve(outputArgument);
const info = await stat(movie);
const movieSha256 = createHash('sha256').update(await readFile(movie)).digest('hex');
const server = createServer((request, response) => {
  if (request.url === '/movie.mp4') {
    response.writeHead(200, { 'content-type': 'video/mp4', 'content-length': info.size });
    createReadStream(movie).pipe(response);
  } else {
    response.writeHead(200, { 'content-type': 'text/html' });
    response.end('<!doctype html><video id="review" muted playsinline controls src="/movie.mp4" style="width:100%"></video>');
  }
});
await new Promise((done) => server.listen(0, '127.0.0.1', done));
const address = server.address();
if (!address || typeof address === 'string') throw new Error('no localhost port');
const browser = await chromium.launch({ headless: true, args: ['--mute-audio', '--use-angle=metal', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 640 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
try {
  await page.goto(`http://127.0.0.1:${address.port}/`);
  const played = await page.evaluate(async () => {
    const video = globalThis.document.getElementById('review');
    if (!(video instanceof globalThis.HTMLVideoElement)) throw new Error('missing video');
    if (!navigator.webdriver || !video.muted) throw new Error('silent automation required');
    let callbacks = 0;
    let firstMediaTime = null;
    let lastMediaTime = null;
    let presentedFrames = 0;
    const observe = (now, metadata) => {
      callbacks += 1;
      firstMediaTime ??= metadata.mediaTime;
      lastMediaTime = metadata.mediaTime;
      presentedFrames = metadata.presentedFrames;
      if (!video.ended) video.requestVideoFrameCallback(observe);
    };
    video.requestVideoFrameCallback(observe);
    const started = performance.now();
    const ended = new Promise((done, reject) => {
      video.addEventListener('ended', done, { once: true });
      video.addEventListener('error', () => reject(new Error(`media error ${video.error?.code}`)), { once: true });
      setTimeout(() => reject(new Error('playback timeout')), 60000);
    });
    await video.play();
    await ended;
    const quality = video.getVideoPlaybackQuality();
    return { muted: video.muted, automation: navigator.webdriver, ended: video.ended, durationS: video.duration, finalMediaTimeS: video.currentTime, elapsedMs: performance.now() - started, width: video.videoWidth, height: video.videoHeight, callbacks, firstMediaTime, lastMediaTime, presentedFrames, totalVideoFrames: quality.totalVideoFrames, droppedVideoFrames: quality.droppedVideoFrames, mediaError: video.error?.code ?? null };
  });
  if (!played.ended || played.mediaError || errors.length || played.callbacks < 100 || Math.abs(played.durationS - played.finalMediaTimeS) > 0.1) throw new Error(JSON.stringify({ played, errors }));
  const report = { status: 'UNACCEPTED silent headless technical full movie playback', movie, movieSha256, bytes: info.size, browser: 'chromium', browserVersion: browser.version(), played, errors, limits: ['Full technical playback only; no parent played appearance verdict, garment motion, M0-M5 or physical iOS acceptance. No audio/game/source mutation or promotion.'] };
  await writeFile(output, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({ ended: played.ended, durationS: played.durationS, callbacks: played.callbacks, errors })}\n`);
} finally {
  await browser.close();
  await new Promise((done, reject) => server.close((error) => error ? reject(error) : done()));
}
