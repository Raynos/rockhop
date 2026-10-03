/* oxlint-disable eslint/no-undef -- document belongs to browser callbacks executed by Playwright. */
/** Silent headless playback check of delivered engine movies. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import { webkit } from 'playwright';

const root = path.resolve(process.argv[2] ?? 'harness/out/rider-contact-diagnostic-2026-10-03/delivery');
const files = fs.readdirSync(root).filter(n => n.endsWith('.mp4'));
const server = http.createServer((request, response) => {
  const file = files.find(n => '/' + encodeURIComponent(n) === request.url);
  if (!file) { response.writeHead(404); response.end(); return; }
  response.writeHead(200, { 'Content-Type': 'video/mp4', 'Content-Length': fs.statSync(path.join(root, file)).size });
  fs.createReadStream(path.join(root, file)).pipe(response);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await webkit.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const rows = [], errors = [];
page.on('pageerror', e => errors.push(e.message));
try {
  for (const file of files) {
    await page.setContent(`<body style="margin:0;background:#111"><video muted playsinline style="width:100%" src="http://127.0.0.1:${server.address().port}/${encodeURIComponent(file)}"></video></body>`);
    await page.evaluate(async () => { const v = document.querySelector('video'); v.muted = true; await v.play(); });
    await page.waitForFunction(() => { const v = document.querySelector('video'); return v.ended && v.currentTime > 3; }, null, { timeout: 20000 });
    const row = await page.evaluate(() => { const v = document.querySelector('video'); return { currentTime: v.currentTime, duration: v.duration, width: v.videoWidth, height: v.videoHeight, muted: v.muted, ended: v.ended, decodedFrames: v.getVideoPlaybackQuality().totalVideoFrames }; });
    assert(row.muted && row.ended && row.decodedFrames >= 17); rows.push({ file, ...row });
    await page.screenshot({ path: path.join(root, file + '.played.png') });
  }
  assert.deepEqual(errors, []);
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
fs.writeFileSync(path.join(root, 'playback-qa.json'), JSON.stringify({ status: 'PLAYED_SILENT_HEADLESS', browser: 'macOS Playwright WebKit', rows, errors }, null, 2) + '\n');
console.log(JSON.stringify(rows));
