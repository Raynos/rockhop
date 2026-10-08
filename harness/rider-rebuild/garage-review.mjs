/** Silent, headless review of the actual Garage with UI and authored motion. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { witnessGlbResponse } from './glb-response-witness.mjs';

const arg = (name, fallback = '') => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
assert(arg('contract'), 'Pass the exact selected rider contract');
const contractPath = path.resolve(arg('contract')), contractBytes = fs.readFileSync(contractPath);
const contract = JSON.parse(contractBytes), expected = contract.specification.meshNames;
const required = ['RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'];
for (const name of required) assert(Object.values(expected).includes(name), `Missing selected dressed object ${name}`);
assert(!fs.existsSync(out), 'Use a fresh output directory');
fs.mkdirSync(out, { recursive: true });
const report = { build, contract: { path: contractPath, sha256: crypto.createHash('sha256').update(contractBytes).digest('hex'), expectedObjects: expected }, recipeSHA256: crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'), errors: [], loaded: [], snapshots: [], audio: 'silent webdriver; audio=0', review: 'Actual Garage UI, selected native clip or riding IK with breathing, pointer-driven orbit; no pose injection' };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, recordVideo: { dir: out, size: { width: 1440, height: 900 } } });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage(), responses = [], witnesses = new Map();
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', response => {
  if (response.url().endsWith('.glb')) responses.push(witnessGlbResponse(response, witnesses)
    .then(row => report.loaded.push(row)).catch(error => report.errors.push(error.message)));
});
try {
  await page.goto(server.resolvedUrls.local[0] + '?audio=0&sw=0');
  await page.locator('.menu-screen.live .menu-item[data-id=garage]').click({ timeout: 120000 });
  await page.waitForSelector('.garage-screen.live');
  await page.locator('button[data-outfit=street-mustard]').click();
  await page.evaluate(async () => window.__render.whenReady());
  await page.waitForTimeout(1500);
  const inspect = async name => {
    const diagnostic = await page.evaluate(() => ({ debug: structuredClone(window.__render.debug.rider.debug), render: window.__render.debugInfo(), stageTime: window.__render.stageTime }));
    report.snapshots.push({ name, ...diagnostic });
    await page.screenshot({ path: path.join(out, name + '.png') });
  };
  await inspect('garage-front');
  const box = await page.locator('.garage-stage').boundingBox();
  assert(box);
  const center = { x: box.x + box.width * .5, y: box.y + box.height * .45 };
  for (let quarter = 1; quarter <= 4; quarter++) {
    await page.mouse.move(center.x, center.y); await page.mouse.down();
    await page.mouse.move(center.x - 160, center.y, { steps: 40 });
    await page.waitForTimeout(100); await page.mouse.up();
    await page.waitForTimeout(1700); await inspect('garage-orbit-' + quarter);
  }
  await Promise.all(responses);
  assert.deepEqual(report.errors, []);
  assert(report.loaded.some(row => row.sha256 === contract.glbSHA256), 'Exact selected GLB served by actual build');
  for (const row of report.snapshots) {
    assert.deepEqual(row.debug.candidate?.authorMeshRoles, expected, 'Exact selected source object inventory loaded');
    const visible = new Set(row.debug.candidate.visibleMeshes.filter(mesh => mesh.skinned && mesh.triangles > 0).map(mesh => mesh.name));
    for (const mesh of row.debug.candidate.meshRoles) assert(visible.has(mesh.name), `Selected dressed primitive is visible and skinned: ${mesh.name}`);
    assert(row.debug.candidate.meshRoles.length >= Object.keys(expected).length, 'Every declared selected object has a dressed material primitive');
  }
  assert(report.snapshots.at(-1).stageTime > report.snapshots[0].stageTime, 'Actual Garage motion clock advances');
} catch (error) { report.failure = error.stack; process.exitCode = 1; }
finally {
  const video = page.video(); await context.close(); await browser.close();
  const videoPath = await video.path();
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', videoPath, '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'garage-played.mp4')], { encoding: 'utf8' });
  report.encoding = { exitCode: encoded.status, stderr: encoded.stderr };
  await new Promise(resolve => server.httpServer.close(resolve));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, snapshots: report.snapshots.length, errors: report.errors, failure: report.failure }));
}
