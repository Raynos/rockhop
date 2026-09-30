/** Silent actual Garage review of a frozen hero build; never a posed substitute scene.
 * tsx harness/hero-remaster/review.mts --build=DIR --out=DIR [--outfit=street-mustard]
 */
/* oxlint-disable typescript/no-explicit-any -- actual browser review hooks. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { GARAGE_VIEW } from '../../src/ui/garage';

const arg = (name: string, fallback = '') => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build'));
const out = path.resolve(arg('out'));
const outfit = arg('outfit', 'street-mustard');
const dimensions = arg('size', '1280x720').split('x').map(Number);
const width = dimensions[0]!, height = dimensions[1]!;
const dpr = Number(arg('dpr', '1'));
const inspection = arg('inspection', 'after');
assert(['before', 'after'].includes(inspection));
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
const manifestFile = path.join(build, 'hero-review.json');
const manifest = fs.existsSync(manifestFile)
  ? JSON.parse(fs.readFileSync(manifestFile, 'utf8'))
  : { kind: 'normal game build', mapping: Object.fromEntries(
    ['models/rider-street-mustard.glb', 'models/rider-street-mustard-lod.glb'].map(logical => [logical, logical])),
  models: JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8')).models };
const hash = (bytes: Buffer) => crypto.createHash('sha256').update(bytes).digest('hex');
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const url = server.resolvedUrls!.local[0];
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: dpr, ...(dpr > 1 ? { isMobile: true, hasTouch: true } : {}) });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage();
const report: any = { build, outfit, width, height, dpr, inspection, view: GARAGE_VIEW, manifest, loaded: [], errors: [], samples: [] };
const responses: Promise<void>[] = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => {
  if (!r.url().endsWith('.glb')) return;
  responses.push(r.body().then(bytes => report.loaded.push({ url: r.url(), sha256: hash(bytes), status: r.status() })));
});
try {
  await page.goto(url + '?sw=0&audio=0', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => {
    const button = document.querySelector('.menu-screen.live .menu-item[data-id=garage]');
    const box = button?.getBoundingClientRect();
    if (!button || !box) return false;
    const hit = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
    return hit === button || !!hit && button.contains(hit);
  }, null, { timeout: 120_000 });
  await page.locator('.menu-screen.live .menu-item[data-id=garage]').click();
  await page.waitForSelector('.garage-screen.live', { timeout: 30_000 });
  await page.locator(`button[data-outfit="${outfit}"]`).click();
  await page.waitForFunction(id => (window as any).__render.debugInfo().riderOutfit === id, outfit);
  await page.evaluate(async () => (window as any).__render.whenReady());
  await page.waitForTimeout(500);
  if (inspection === 'before') await page.evaluate(({ width, height, dpr }) => {
    const r = (window as any).__render;
    // Reproduce the previous inspection policy on identical candidate bytes,
    // camera and lighting. This comparison cannot change the riding policy.
    const ratio = Math.min(dpr, 1.5);
    r.pixelRatio = ratio;
    r.debug.renderer.setPixelRatio(ratio);
    r.debug.renderer.setSize(width, height, false);
    r.debug.post.setInspection(false);
    r.debug.post.setSize(width, height, ratio);
    r.invalidate();
  }, { width, height, dpr });
  await page.screenshot({ path: path.join(out, 'garage.png') });
  report.initial = await page.evaluate(() => ({ info: (window as any).__render.debugInfo(), hook: (window as any).__rockhop.info() }));
  report.aa = await page.evaluate(() => {
    const post = (window as any).__render.debug.post;
    return { threshold: post.aa._materialEdges.defines.SMAA_THRESHOLD, searchSteps: post.aa._materialWeights.defines.SMAA_MAX_SEARCH_STEPS, samples: post.sceneTarget.samples };
  });
  report.heroBounds = await page.evaluate(({ width, height }) => {
    const d = (window as any).__render.debug;
    const v = new d.THREE.Vector3();
    const camera = d.rig.camera;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const root of [d.rider.scene, d.bike.scene]) {
      root.updateMatrixWorld(true);
      root.traverse((mesh: any) => {
        if (!mesh.isMesh || !mesh.visible) return;
        const positions = mesh.geometry.getAttribute('position');
        for (let i = 0; i < positions.count; i++) {
          mesh.getVertexPosition(i, v); mesh.localToWorld(v).project(camera);
          const x = (v.x * 0.5 + 0.5) * width, y = (0.5 - v.y * 0.5) * height;
          x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
        }
      });
    }
    return { x0, y0, x1, y1, widthShare: (x1 - x0) / width, heightShare: (y1 - y0) / height };
  }, { width, height });
  assert(report.heroBounds.x0 >= 0 && report.heroBounds.y0 >= 0 && report.heroBounds.x1 <= width && report.heroBounds.y1 <= height, 'complete hero fits the opening view');
  // Real Garage orbit: ordered frames through both sides/back, with the same
  // camera and exact screenshot cadence in baseline and candidate builds.
  for (let i = 0; i < 120; i++) {
    const yaw = i * Math.PI * 2 / 120;
    const sample = await page.evaluate(({ yaw, i, view }) => {
      const r = (window as any).__render;
      r.setCameraOverride({ mode: 'orbit', yaw, pitch: view.pitch, dist: view.dist, screenX: view.screenX, screenY: view.screenY });
      (window as any).__rockhop.render(true);
      const d = r.debug?.rider;
      const neck = d?.scene?.getObjectByName('neck');
      return i % 10 === 0 ? { i, yaw, stageTime: r.stageTime, physicsTime: (window as any).__rockhop.getState().time, neck: neck?.quaternion.toArray(), rider: d?.debug ? JSON.parse(JSON.stringify(d.debug)) : null } : null;
    }, { yaw, i, view: GARAGE_VIEW });
    if (sample) report.samples.push(sample);
    await page.screenshot({ path: path.join(out, 'frames', `${String(i).padStart(4, '0')}.png`) });
  }
  await Promise.all(responses);
  for (const model of manifest.models) {
    const seen = report.loaded.find((r: any) => r.url.endsWith('/' + model.url));
    if (!seen) continue;
    assert.equal(seen.sha256, model.sha256, `consumed ${model.logical}`);
    assert.equal(seen.status, 200);
  }
  for (const logical of Object.keys(manifest.mapping)) {
    const model = manifest.models.find((m: any) => m.logical === logical);
    assert(report.loaded.some((r: any) => r.url.endsWith('/' + model.url) && r.sha256 === model.sha256), `candidate bytes consumed: ${logical}`);
  }
  assert.equal(report.initial.info.garage.on, true, 'actual Garage stage');
  assert.deepEqual(report.errors, []);
  if (report.samples[0]?.rider?.stageClip === 'idle_breathe') {
    assert(report.samples.at(-1).stageTime > report.samples[0].stageTime, 'Garage presentation clock advances');
    assert(report.samples.every((s: any) => s.physicsTime === report.samples[0].physicsTime), 'Garage animation leaves physics clock frozen');
    assert(report.samples.some((s: any) => s.neck?.some((v: number, i: number) => Math.abs(v - report.samples[0].neck[i]) > 1e-5)), 'actual Garage neck moves');
  }
  const ff = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '30', '-i', path.join(out, 'frames/%04d.png'), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'orbit.mp4')], { encoding: 'utf8' });
  assert.equal(ff.status, 0, ff.stderr);
} catch (e) { report.failure = e instanceof Error ? e.message : String(e); }
finally {
  await context.close(); await browser.close();
  await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, errors: report.errors, failure: report.failure, loaded: report.loaded.length }));
  if (report.failure) process.exitCode = 1;
}
