/** Actual recorded game inputs, complete dressed rider and measured joint debug. */
/* oxlint-disable typescript/no-explicit-any -- read-only renderer evidence. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
const arg = (name: string, fallback = '') => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
assert(!fs.existsSync(out), 'Fresh output required');
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
const recording = decodeJSON(fs.readFileSync(arg('recording', 'harness/inputs/b1-first-ride/bot-3.json'), 'utf8'));
const inputs = expandFrames(recording), fps = 12, stride = recording.header.physicsHz / fps;
assert(Number.isInteger(stride));
const count = Math.min(Math.floor(inputs.length / stride), Math.round(Number(arg('seconds', '16')) * fps));
const yaw = Number(arg('yaw', '1.4'));
const report: any = { build, fps, stride, count, errors: [], loaded: [], samples: [], scope: 'Actual recorded game inputs; camera follows declared pelvis; no pose injection or physics mutation' };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const responses: Promise<void>[] = [];
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', response => {
  if (response.url().endsWith('.glb')) responses.push(response.body().then(bytes => report.loaded.push({ url: response.url(), status: response.status(), sha256: crypto.createHash('sha256').update(bytes).digest('hex') })));
});
try {
  await page.goto(server.resolvedUrls!.local[0] + `?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${recording.header.physics ?? 'v1'}&hz=${recording.header.physicsHz}`);
  await page.waitForFunction(() => (window as any).__rockhop?.ready, null, { timeout: 120000 });
  await page.evaluate(async header => {
    const t = (window as any).__rockhop, r = (window as any).__render;
    t.setBike(header.bike ?? 'rookie'); await r.whenReady();
    await t.loadTrack(header.trackId, header.seed); await r.whenReady(); t.setQuality('high'); await r.whenReady(); t.skipCountdown();
  }, recording.header);
  for (let i = 0; i < count; i++) {
    const sample = await page.evaluate(({ input, yaw }) => {
      const t = (window as any).__rockhop, r = (window as any).__render, d = r.debug;
      for (const frame of input) { t.setInput(frame); t.step(1); }
      t.render(true);
      const candidate = d.rider.debug.candidate, pelvisName = candidate.jointNames[candidate.roles.pelvis];
      const pelvis = d.rider.scene.getObjectByName(pelvisName); if (!pelvis) throw new Error('Missing declared pelvis');
      const p = pelvis.getWorldPosition(new d.THREE.Vector3());
      r.setCameraOverride({ mode: 'orbit', x: p.x, y: p.y + .22, yaw, pitch: .08, dist: 6.0, screenX: .5, screenY: .5 });
      t.render(true);
      return { tick: t.getState().tick, input: input.at(-1), state: structuredClone(t.getState()), debug: structuredClone(d.rider.debug), hash: t.hashState() };
    }, { input: inputs.slice(i * stride, (i + 1) * stride), yaw });
    report.samples.push(sample);
    await page.screenshot({ path: path.join(out, 'frames', `${String(i).padStart(4, '0')}.png`) });
  }
  await Promise.all(responses); assert.deepEqual(report.errors, []);
  assert(report.samples.every((row: any) => row.debug.allBoneFinite), 'Complete hierarchy finite');
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(out, 'frames/%04d.png'), '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'ride-played.mp4')], { encoding: 'utf8' });
  assert.equal(encoded.status, 0, encoded.stderr);
} catch (error) { report.failure = error instanceof Error ? error.stack : String(error); process.exitCode = 1; }
finally {
  await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, samples: report.samples.length, errors: report.errors, failure: report.failure }));
}
