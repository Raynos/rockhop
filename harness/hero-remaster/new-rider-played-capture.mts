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
import { installPrivateEyeOptics24 } from './new-rider-eye-optics24-install.mjs';
const arg = (key: string, fallback = '') => process.argv.find(a => a.startsWith(`--${key}=`))?.slice(key.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
const mode = arg('mode', 'garage'), tier = arg('tier', 'high');
assert(['garage', 'ride'].includes(mode)); assert(['low', 'high'].includes(tier));
const recording = decodeJSON(fs.readFileSync(arg('recording', 'harness/inputs/b1-first-ride/bot-3.json'), 'utf8'));
const inputs = expandFrames(recording), fps = Number(arg('fps', '12')), ticksPerFrame = recording.header.physicsHz / fps;
assert(Number.isInteger(ticksPerFrame));
const frames = Math.min(Math.floor(inputs.length / ticksPerFrame), Math.round(Number(arg('seconds', '40')) * fps));
const eyeOptics24 = arg('eye-optics24', '0') === '1';
const surface = arg('surface', 'textured'); assert(['textured', 'gray'].includes(surface));
const focus = arg('focus', 'body'); assert(['body', 'hands', 'feet', 'face'].includes(focus));
const detailZoom = Number(arg('detail-zoom', '1'));
const centerFocus = arg('center-focus', '0') === '1';
assert(!centerFocus || focus === 'face', 'surface centering is an explicit face diagnostic');
assert(Number.isFinite(detailZoom) && detailZoom >= 1 && detailZoom <= 4);
assert(detailZoom === 1 || focus !== 'body', 'detail zoom is only for explicit closeup diagnostics');
assert(frames > 0 && frames * ticksPerFrame <= inputs.length);
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
assert.equal(fs.readdirSync(path.join(out, 'frames')).length, 0, 'fresh capture directory');
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8'));
const report: any = { build, mode, tier, frames, fps, focus, surface, detailZoom, centerFocus, camera: 'actual runtime bone midpoint; optional skinned face vertex projection centering, no pose injection', ui: 'HUD hidden only for geometry inspection', samples: [], errors: [], loaded: [] };
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
  if (eyeOptics24) {
    assert.equal(surface, 'textured', 'Optics24 is an isolated PBR material comparison; original gray geometry is unchanged');
    const model = catalog.models.find((m: any) => m.logical === 'models/rider-street-mustard.glb');
    report.privateEyeOptics24 = await installPrivateEyeOptics24(page, model.sha256);
  }
  report.loadedMaterials = await page.evaluate(() => {
    const rows: any[] = [];
    (window as any).__render.debug.rider.scene.traverse((o: any) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        const maps: any[] = [];
        for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap']) {
          const t = m[key]; if (!t) continue;
          maps.push({ key, name: t.name, width: t.image?.width, height: t.image?.height,
            channel: t.channel, colorSpace: t.colorSpace, anisotropy: t.anisotropy,
            minFilter: t.minFilter, magFilter: t.magFilter, generateMipmaps: t.generateMipmaps });
        }
        rows.push({ mesh: o.name, material: m.name, type: m.type, roughness: m.roughness,
          metalness: m.metalness, color: m.color?.toArray(), maps });
      }
    });
    return rows;
  });
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
    const sample = await page.evaluate(({ input, yaw, i, focus, detailZoom, centerFocus }) => {
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
      // Orbit intentionally clamps distance to >=3m. Zoom the real camera projection
      // for private closeups; record the effective camera rather than claiming requested distance.
      d.rig.camera.clearViewOffset(); d.rig.camera.zoom = detailZoom;
      d.rig.camera.updateProjectionMatrix(); r.invalidate();
      t.render(true);
      let surfaceFocus: any = null;
      if (centerFocus) {
        // Read one fixed source nose/face vertex through actual skinning. The
        // projection window follows it; renderer, pose and physics stay intact.
        let headMesh: any = null, headBone: any = null;
        d.rider.scene.traverse((o: any) => {
          if (o.isBone && o.name === 'head') headBone = o;
          if (o.isSkinnedMesh && o.material?.name === 'Material.002') headMesh = o;
        });
        if (!headMesh || !headBone) throw new Error('missing actual head surface/bone');
        const sourceTarget = new d.THREE.Vector3(.752, 1.69, 0);
        const attribute = headMesh.geometry.getAttribute('position');
        let index = -1, distance = Infinity;
        const p = new d.THREE.Vector3();
        for (let j = 0; j < attribute.count; j++) {
          p.fromBufferAttribute(attribute, j);
          const next = p.distanceToSquared(sourceTarget);
          if (next < distance) { distance = next; index = j; }
        }
        const rest = new d.THREE.Vector3().fromBufferAttribute(attribute, index);
        const world = headMesh.localToWorld(headMesh.getVertexPosition(index, new d.THREE.Vector3()));
        const headLocal = headBone.worldToLocal(world.clone());
        const before = world.clone().project(d.rig.camera);
        if (![...world.toArray(), ...before.toArray()].every(Number.isFinite)) throw new Error('nonfinite surface focus');
        if (before.z <= -1 || before.z >= 1) throw new Error('surface focus outside depth range');
        const size = d.renderer.getSize(new d.THREE.Vector2());
        d.rig.camera.setViewOffset(size.x, size.y, before.x * size.x / 2, -before.y * size.y / 2, size.x, size.y);
        d.rig.camera.updateProjectionMatrix(); r.invalidate(); t.render(true);
        const after = world.clone().project(d.rig.camera);
        if (Math.hypot(after.x, after.y) > 1e-6) throw new Error('surface projection failed to center');
        surfaceFocus = { mesh: headMesh.name, vertex: index, rest: rest.toArray(), world: world.toArray(),
          headLocal: headLocal.toArray(), sourceTarget: sourceTarget.toArray(), sourceTargetDistanceM: Math.sqrt(distance),
          projectedBefore: before.toArray(), projectedAfter: after.toArray(), headWorld: headBone.getWorldPosition(new d.THREE.Vector3()).toArray(),
          headQuaternion: headBone.getWorldQuaternion(new d.THREE.Quaternion()).toArray() };
      }
      const effectiveCamera = { position: d.rig.camera.position.toArray(), quaternion: d.rig.camera.quaternion.toArray(),
        fov: d.rig.camera.fov, zoom: d.rig.camera.zoom, distance: d.rig.distance,
        ...(centerFocus ? { view: structuredClone(d.rig.camera.view) } : {}) };
      const positions: Record<string, number[]> = {};
      d.rider.scene.traverse((o: any) => { if (o.isBone && /^(forearm|hand)[.]?[LR]$/.test(o.name)) positions[o.name] = o.getWorldPosition(new d.THREE.Vector3()).toArray(); });
      return { i, ...(centerFocus ? { surfaceFocus } : {}), effectiveCamera, inputLast: input.at(-1), state: structuredClone(t.getState()), phase: t.phase(), tick: t.getState().tick, physicsTime: t.getState().time, stageTime: r.stageTime, hash: t.hashState(), positions, privateClothRim: structuredClone(d.rider.scene.userData.rockhopPrivateClothRim ?? null), heroDoc: r.debugInfo().heroDoc, debug: structuredClone(d.rider.debug) };
    }, { input: mode === 'ride' ? inputs.slice(i * ticksPerFrame, (i + 1) * ticksPerFrame) : [], yaw: 0.4 + 1.35 * Math.sin(i * Math.PI * 2 / Math.max(1, frames - 1)), i, focus, detailZoom, centerFocus });
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
