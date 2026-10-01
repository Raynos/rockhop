/** Private NEW rider played geometry diagnostic; actual input replay, no injected pose.
 * tsx harness/hero-remaster/wrist-capture.mts --build=DIR --out=DIR
 * [--mode=garage|ride] [--tier=low|high] [--recording=FILE] [--seconds=12]
 * The camera follows the real wrist midpoint; no bone or mesh pose is injected.
 */
/* oxlint-disable typescript/no-explicit-any -- actual browser renderer diagnostics. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
const arg = (key: string, fallback = '') => process.argv.find(a => a.startsWith(`--${key}=`))?.slice(key.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
const mode = arg('mode', 'garage'), tier = arg('tier', 'high');
assert(['garage', 'ride'].includes(mode)); assert(['low', 'high'].includes(tier));
const recording = decodeJSON(fs.readFileSync(arg('recording', 'harness/inputs/b1-first-ride/bot-3.json'), 'utf8'));
const inputs = expandFrames(recording), fps = Number(arg('fps', '12')), ticksPerFrame = recording.header.physicsHz / fps;
assert(Number.isInteger(ticksPerFrame));
const frames = Math.min(Math.floor(inputs.length / ticksPerFrame), Math.round(Number(arg('seconds', '40')) * fps));
const surface = arg('surface', 'textured'); assert(['textured', 'gray'].includes(surface));
const focus = arg('focus', 'body'); assert(['body', 'hands', 'feet', 'face'].includes(focus));
assert(frames > 0 && frames * ticksPerFrame <= inputs.length);
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
assert.equal(fs.readdirSync(path.join(out, 'frames')).length, 0, 'fresh capture directory');
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8'));
const report: any = { build, mode, tier, frames, fps, focus, surface, camera: 'actual runtime bone midpoint; read-only focus/orbit camera, no pose injection', ui: 'HUD hidden only for geometry inspection', samples: [], errors: [], loaded: [] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
await context.addInitScript(() => localStorage.setItem('rockhop.onboarded', '1'));
const page = await context.newPage(), responses: Promise<void>[] = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => { if (r.url().endsWith('.glb')) responses.push(r.body().then(bytes => report.loaded.push({ url: r.url(), sha256: crypto.createHash('sha256').update(bytes).digest('hex'), status: r.status() }))); });
try {
  const url = server.resolvedUrls!.local[0]!;
  await page.goto(url + (mode === 'ride' ? `?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${recording.header.physics ?? 'v1'}&hz=${recording.header.physicsHz}` : '?audio=0&sw=0'));
  if (mode === 'garage') {
    await page.waitForSelector('.menu-screen.live .menu-item[data-id=garage]', { timeout: 120000 });
    await page.locator('.menu-screen.live .menu-item[data-id=garage]').click();
    await page.waitForSelector('.garage-screen.live');
    await page.locator('button[data-outfit=street-mustard]').click();
    await page.evaluate(async () => (window as any).__render.whenReady());
  } else {
    await page.waitForFunction(() => (window as any).__rockhop?.ready, null, { timeout: 120000 });
    await page.evaluate(async ({ header, tier }) => {
      const t = (window as any).__rockhop, r = (window as any).__render;
      t.setBike(header.bike ?? 'rookie'); await r.whenReady();
      await t.loadTrack(header.trackId, header.seed); await r.whenReady();
      t.setQuality(tier); await r.whenReady(); t.skipCountdown();
    }, { header: recording.header, tier });
  }
  report.surfaceDiagnostic = await page.evaluate(surface => {
    const r = (window as any).__render, meshes: any[] = [];
    if (surface === 'gray') r.debug.rider.scene.traverse((o: any) => {
      if (!o.isMesh) return;
      const materials = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of materials) {
        meshes.push({ mesh: o.name, material: m.name, originalColor: m.color?.toArray(), originalMap: !!m.map, originalNormalMap: !!m.normalMap });
        m.color?.setRGB(.48, .48, .48); m.metalness = 0; m.roughness = .72;
        for (const key of ['map','normalMap','bumpMap','roughnessMap','metalnessMap','aoMap','emissiveMap']) m[key] = null;
        m.emissive?.setRGB(0, 0, 0); m.needsUpdate = true;
      }
    });
    r.invalidate(); return { surface, meshes, scope: 'Read-only geometry/rig/input; temporary neutral materials on rider only, same lights/camera and unchanged bike' };
  }, surface);
  await page.addStyleTag({ content: '.hud, .hud-top, .hud-bottom, .run-hud, .touch-controls, .countdown { visibility: hidden !important; }' });
  // Cover every UI element above the canvas; scene materials and geometry stay intact.
  await page.evaluate(() => { for (const o of document.querySelectorAll<HTMLElement>('body > *')) if (o.tagName !== 'CANVAS' && !o.querySelector('canvas')) o.style.visibility = 'hidden'; });
  await page.waitForTimeout(500);
  for (let i = 0; i < frames; i++) {
    const sample = await page.evaluate(({ input, yaw, i, focus }) => {
      const t = (window as any).__rockhop, r = (window as any).__render, d = r.debug;
      for (const frame of input) { t.setInput(frame); t.step(1); }
      t.render(true);
      const midpoint = new d.THREE.Vector3(); let found = 0;
      d.rider.scene.traverse((o: any) => {
        const pattern = focus === 'hands' ? /^hand[.]?[LR]$/ : focus === 'feet' ? /^foot[.]?[LR]$/ : focus === 'face' ? /^head$/ : /^pelvis$/;
        if (!o.isBone || !pattern.test(o.name)) return;
        midpoint.add(o.getWorldPosition(new d.THREE.Vector3())); found++;
      });
      const expected = focus === 'hands' || focus === 'feet' ? 2 : 1;
      if (found !== expected) throw new Error(`expected actual focus bones, got ${found}`);
      midpoint.multiplyScalar(1 / found); if (focus === 'body') midpoint.y += .12; if (focus === 'face') midpoint.y += .04;
      r.setCameraOverride({ mode: 'orbit', x: midpoint.x, y: midpoint.y, yaw, pitch: 0.12, dist: focus === 'body' ? 5.2 : focus === 'hands' ? 2.0 : focus === 'feet' ? 2.0 : 1.3, screenX: 0.5, screenY: 0.5 });
      t.render(true);
      const positions: Record<string, number[]> = {};
      d.rider.scene.traverse((o: any) => { if (o.isBone && /^(forearm|hand)[.]?[LR]$/.test(o.name)) positions[o.name] = o.getWorldPosition(new d.THREE.Vector3()).toArray(); });
      return { i, inputLast: input.at(-1), state: structuredClone(t.getState()), phase: t.phase(), tick: t.getState().tick, physicsTime: t.getState().time, stageTime: r.stageTime, hash: t.hashState(), positions, heroDoc: r.debugInfo().heroDoc, debug: structuredClone(d.rider.debug) };
    }, { input: mode === 'ride' ? inputs.slice(i * ticksPerFrame, (i + 1) * ticksPerFrame) : [], yaw: 0.4 + 1.35 * Math.sin(i * Math.PI * 2 / Math.max(1, frames - 1)), i, focus });
    report.samples.push(sample);
    await page.screenshot({ path: path.join(out, 'frames', `${String(i).padStart(4, '0')}.png`) });
  }
  await Promise.all(responses);
  for (const logical of ['models/rider-street-mustard.glb', 'models/rider-street-mustard-lod.glb']) {
    const model = catalog.models.find((m: any) => m.logical === logical);
    assert(model && report.loaded.some((m: any) => m.url.endsWith('/' + model.url) && m.sha256 === model.sha256 && m.status === 200), `consumed exact ${logical}`);
  }
  assert.deepEqual(report.errors, []);
  if (mode === 'garage') assert(report.samples.every((s: any) => s.physicsTime === report.samples[0].physicsTime), 'Garage leaves physics frozen');
  report.note = 'Moving real-engine evidence. Socket debug values are not a wrist surface-continuity verdict. Garage screenshot cadence follows host presentation time; movie duration does not measure idle speed.';
  const ff = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(out, 'frames/%04d.png'), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'played.mp4')], { encoding: 'utf8' });
  assert.equal(ff.status, 0, ff.stderr);
} catch (e) { report.failure = e instanceof Error ? e.message : String(e); }
finally {
  await context.close(); await browser.close();
  await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, failure: report.failure, errors: report.errors, samples: report.samples.length }));
  if (report.failure) process.exitCode = 1;
}
