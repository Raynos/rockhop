/** Actual recorded hip motion, fixed cameras and final presented pelvis anchor. */
/* oxlint-disable typescript/no-explicit-any -- isolated actual renderer diagnostics. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { installPrivateHipReviewDriver } from './new-rider-hip-review-install.mjs';

const arg = (key: string, fallback = '') => process.argv.find(a => a.startsWith(`--${key}=`))?.slice(key.length + 3) ?? fallback;
const build = path.resolve(arg('build'));
const out = path.resolve(arg('out'));
const angle = arg('angle', 'side');
const surface = arg('surface', 'textured');
const cameraVersion = arg('camera-version', 'orbit02');
const hipReviewDriver = arg('hip-review-driver', '0') === '1';
assert(['orbit01', 'orbit02'].includes(cameraVersion));
// rig.dir=(-sin(yaw),-sin(pitch),-cos(yaw)); yaw0 is the true side.
const angles: Record<string, number> = cameraVersion === 'orbit01' ? { side: Math.PI / 2, 'rear-three-quarter': 2.3 } : { side: 0, 'rear-three-quarter': -.8 };
const yaw = angles[angle];
assert(yaw !== undefined && ['textured', 'gray'].includes(surface));
const recording = decodeJSON(fs.readFileSync('docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json', 'utf8'));
const inputs = expandFrames(recording), fps = 12, steps = recording.header.physicsHz / fps, frames = 264;
assert(Number.isInteger(steps) && inputs.length >= frames * steps);
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8'));
const model = catalog.models.find((m: any) => m.logical === 'models/rider-street-mustard.glb');
assert(model);
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
assert(!fs.existsSync(path.join(out, 'report.json')) && fs.readdirSync(path.join(out, 'frames')).length === 0);
const report: any = { build, sourceSHA256: model.sha256, angle, cameraVersion, surface, frames, fps,
  scope: 'Actual recorded seated riding/maximum lean/landing-recovery; camera only, no pose injection', hipReviewDriver, reviewOverlay: hipReviewDriver ? JSON.parse(fs.readFileSync(path.join(build, 'hip-overlay.json'), 'utf8')) : null, samples: [], errors: [], loaded: [] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage(), responses: Promise<void>[] = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => { if (r.url().endsWith('.glb')) responses.push(r.body().then(bytes => report.loaded.push({ url: r.url(), sha256: crypto.createHash('sha256').update(bytes).digest('hex'), status: r.status() }))); });
try {
  await page.goto(server.resolvedUrls!.local[0] + `?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${recording.header.physics ?? 'v1'}&hz=${recording.header.physicsHz}`);
  await page.waitForFunction(() => (window as any).__rockhop?.ready, null, { timeout: 120000 });
  await page.evaluate(async header => {
    const t = (window as any).__rockhop, r = (window as any).__render;
    t.setBike(header.bike ?? 'rookie'); await r.whenReady();
    await t.loadTrack(header.trackId, header.seed); await r.whenReady();
    t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
  }, recording.header);
  if (hipReviewDriver) await installPrivateHipReviewDriver(page);
  await page.evaluate(surface => {
    if (surface === 'gray') (window as any).__render.debug.rider.scene.traverse((o: any) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        m.color?.setRGB(.48, .48, .48); m.metalness = 0; m.roughness = .72;
        for (const key of ['map', 'normalMap', 'bumpMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap']) m[key] = null;
        m.emissive?.setRGB(0, 0, 0); m.needsUpdate = true;
      }
    });
  }, surface);
  await page.addStyleTag({ content: '.hud,.hud-top,.hud-bottom,.run-hud,.touch-controls,.countdown{visibility:hidden!important}' });
  await page.evaluate(() => { for (const e of document.querySelectorAll<HTMLElement>('body > *')) if (e.tagName !== 'CANVAS' && !e.querySelector('canvas')) e.style.visibility = 'hidden'; });
  for (let i = 0; i < frames; i++) {
    const sample = await page.evaluate(({ input, yaw, i }) => {
      const t = (window as any).__rockhop, r = (window as any).__render, d = r.debug, T = d.THREE;
      for (const frame of input) { t.setInput(frame); t.step(1); }
      r.invalidate(); t.render(true);
      let pelvis: any = null;
      d.rider.scene.traverse((o: any) => { if (o.isBone && o.name === 'pelvis') pelvis = o; });
      if (!pelvis) throw new Error('Missing actual pelvis');
      const first = pelvis.getWorldPosition(new T.Vector3()); first.y -= .08;
      const orbit = { mode: 'orbit', x: first.x, y: first.y, yaw, pitch: .1, dist: 3, screenX: .5, screenY: .5 };
      r.setCameraOverride(orbit);
      d.rig.camera.clearViewOffset(); d.rig.camera.zoom = 2.2; d.rig.camera.updateProjectionMatrix();
      r.invalidate(); t.render(true);
      const presented = pelvis.getWorldPosition(new T.Vector3()); presented.y -= .08;
      const before = presented.clone().project(d.rig.camera), size = d.renderer.getSize(new T.Vector2());
      d.rig.camera.setViewOffset(size.x, size.y, before.x * size.x / 2, -before.y * size.y / 2, size.x, size.y);
      d.rig.camera.updateProjectionMatrix(); r.invalidate(); t.render(true);
      const final = pelvis.getWorldPosition(new T.Vector3()); final.y -= .08;
      const projected = final.clone().project(d.rig.camera);
      if (final.distanceTo(presented) > 1e-6 || Math.hypot(projected.x, projected.y) > 1e-6) throw new Error('Final pelvis presentation changed after camera centering');
      const bones: Record<string, unknown> = {};
      d.rider.scene.traverse((o: any) => { if (o.isBone) bones[o.name] = { position: o.getWorldPosition(new T.Vector3()).toArray(), quaternion: o.getWorldQuaternion(new T.Quaternion()).toArray() }; });
      return { i, tick: t.getState().tick, state: structuredClone(t.getState()), hash: t.hashState(), phase: t.phase(),
        debug: structuredClone(d.rider.debug), hipCorrective: structuredClone(d.rider.scene.userData.privateHipCorrectiveDiagnostic ?? null), bones, orbit, camera: { position: d.rig.camera.position.toArray(), quaternion: d.rig.camera.quaternion.toArray(), fov: d.rig.camera.fov, zoom: d.rig.camera.zoom, view: structuredClone(d.rig.camera.view) },
        anchor: { initial: first.toArray(), final: final.toArray(), projected: projected.toArray() } };
    }, { input: inputs.slice(i * steps, (i + 1) * steps), yaw, i });
    report.samples.push(sample);
    await page.screenshot({ path: path.join(out, 'frames', `${String(i).padStart(4, '0')}.png`) });
  }
  await Promise.all(responses);
  assert(report.loaded.some((m: any) => m.sha256 === model.sha256 && m.status === 200));
  assert.deepEqual(report.errors, []);
  if (hipReviewDriver) assert(report.samples.every((s: any) => s.hipCorrective && s.hipCorrective.weights.every(Number.isFinite)));
  const ff = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(out, 'frames/%04d.png'), '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', path.join(out, 'played.mp4')], { encoding: 'utf8' });
  assert.equal(ff.status, 0, ff.stderr);
} catch (error) { report.failure = error instanceof Error ? error.message : String(error); process.exitCode = 1; }
finally {
  await context.close(); await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, frames: report.samples.length, failure: report.failure, errors: report.errors }));
}
