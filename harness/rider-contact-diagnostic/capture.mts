/** Isolated real-game Garage evidence. Authored pose override, never a gameplay pass. */
/* oxlint-disable typescript/no-explicit-any, typescript/no-extraneous-class -- inspected runtime objects and constructor-only silent audio traps. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync, execFileSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';

const arg = (key: string, fallback: string) => process.argv.find(x => x.startsWith(`--${key}=`))?.slice(key.length + 3) ?? fallback;
const wrapperMode = arg('wrapper', 'ordinary');
assert(['ordinary', 'source-file'].includes(wrapperMode));
const stepOnly = arg('step-only', '0') === '1';
const build = path.resolve(arg('build', 'harness/out/rider-contact-diagnostic-2026-10-03/build'));
const out = path.resolve(arg('out', 'harness/out/rider-contact-diagnostic-2026-10-03/capture'));
fs.mkdirSync(out, { recursive: true });
const posesPath = path.resolve(arg('poses', 'harness/out/rider-contact-diagnostic-2026-10-03/source/diagnostic-poses.json'));
const poses = JSON.parse(fs.readFileSync(posesPath, 'utf8'));
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(posesPath)).digest('hex'), 'aba49af57424d52427929ce419871aa12d007dceb853ef36593ddd00e821cbce');
const manifest = JSON.parse(fs.readFileSync(path.join(build, 'hero-review.json'), 'utf8'));
const report: any = { scope: 'Actual Rockhop Garage; isolated authored diagnostic pose override; NOT physics-driven riding or production promotion',
  repoSHA: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), build, manifest,
  browser: 'Playwright WebKit headless on macOS', device: '1280x720 DPR1 desktop emulation; physical iOS untested',
  wrapperMode, errors: [], loaded: [], samples: [], audioContexts: 0, limits: ['STEP only: no sparse-key linear interpolation acceptance.', 'T/A poses use cloud manifest aba49af5, all26localTRS, animations/morphsOFF.', 'No contact, clothing, normals, mobile or art pass asserted.'] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1');
  (window as any).__diagnosticAudioCount = 0;
  for (const key of ['AudioContext', 'webkitAudioContext']) (window as any)[key] = class { constructor() { (window as any).__diagnosticAudioCount++; throw new Error('AudioContext forbidden in silent QA'); } };
});
const page = await context.newPage(), responses: Promise<void>[] = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => { if (/\.glb(?:\?|$)/.test(r.url())) responses.push(r.body().then(b => report.loaded.push({ url: r.url(), status: r.status(), bytes: b.length, sha256: crypto.createHash('sha256').update(b).digest('hex') }))); });
try {
  const launch = server.resolvedUrls!.local[0] + '?audio=0&sw=0&outfit=street-mustard&rider=gltf&bike=gltf&physics=v2&hz=120';
  report.launchURL = launch;
  await page.goto(launch, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => (window as any).__rockhop?.ready && (window as any).__rockhop?.app, null, { timeout: 120000 });
  await page.waitForFunction(() => !document.querySelector('#loader') || document.querySelector('#loader')?.getAttribute('data-done') === '1', null, { timeout: 120000 });
  await page.evaluate(async () => {
    const t = (window as any).__rockhop, r = (window as any).__render;
    t.setQuality('high'); await r.whenReady(); t.app.goto('garage'); await r.whenReady(); t.render(true);
  });
  await page.waitForFunction(() => (window as any).__render.debugInfo().garage.on);
  await page.waitForTimeout(700);
  await page.addStyleTag({ content: '#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #diagnostic-label{position:fixed;z-index:99999;top:12px;left:16px;right:16px;background:#101820e8;color:white;padding:10px;font:16px monospace;white-space:pre-line;visibility:visible!important;pointer-events:none}' });
  await page.evaluate(() => { const label = document.createElement('div'); label.id = 'diagnostic-label'; document.body.append(label); });
  for (const [variant, outfit] of (stepOnly ? [['repaired', 'street-mustard']] : [['repaired', 'street-mustard'], ['raw-body11', 'street-openface']]) as [string, string][]) {
    await page.evaluate(async outfit => { const r = (window as any).__render; await r.setRiderOutfit(outfit); await r.whenReady(); }, outfit);
    await page.evaluate(({ poses, wrapperMode }) => {
      const r = (window as any).__render, rider = r.debug.rider, T = r.debug.THREE;
      // Restore authored geometry explicitly. Garage already uses it; prevent any
      // runtime weight smoothing from confounding raw/repaired comparisons.
      for (const entry of rider.sleeveGeometry) entry.mesh.geometry = entry.authored;
      if (wrapperMode === 'source-file') rider.scene.position.x += .65;
      const rest = new Map();
      rider.scene.traverse((o: any) => { if (o.isBone) rest.set(o, { p: o.position.clone(), q: o.quaternion.clone(), s: o.scale.clone() }); });
      // Clone is initially posed by the game. Restore exact source local TRS.
      const original = new Map(); rider.source.scene.traverse((o: any) => { if (o.isBone) original.set(o.name, o); });
      for (const [o, v] of rest) { const src = original.get(o.name); v.p.copy(src.position); v.q.copy(src.quaternion); v.s.copy(src.scale); }
      const clip = rider.source.animations.find((a: any) => a.name === 'diagnostic_contact_observations_STEP');
      const sampler = clip?.tracks.map((track: any) => { const binding = new T.PropertyBinding(rider.scene, track.name); binding.bind(); return { name: track.name, interpolant: track.createInterpolant(), binding }; });
      const mixer = new T.AnimationMixer(rider.scene);
      const action = clip ? mixer.clipAction(clip) : null;
      if (action) { action.setLoop(T.LoopOnce, 1); action.clampWhenFinished = true; action.play(); }
      const nodeObjects = new Map();
      for (const [o, assoc] of rider.source.parser.associations) if (assoc.nodes !== undefined) nodeObjects.set(assoc.nodes, rider.scene.getObjectByName(o.name));
      (window as any).__diag = { rider, rest, mixer, clip, poses, nodeObjects, time: 0, pose: 'T', variant: '', apply() {
        for (const [o, v] of rest) { o.position.copy(v.p); o.quaternion.copy(v.q); o.scale.copy(v.s); }
        rider.scene.traverse((o: any) => { if (o.morphTargetInfluences) o.morphTargetInfluences.fill(0); });
        rider.scene.updateMatrixWorld(true);
        if (this.pose === 'STEP') { if (!action) throw new Error('No exact STEP clip'); for (const track of sampler) track.binding.setValue(track.interpolant.evaluate(this.time), 0); }
        else if (this.pose !== 'rest') {
          mixer.stopAllAction();
          const pose = poses.poses.find((p: any) => p.name === this.pose);
          for (const n of pose.nodes) {
            const o = nodeObjects.get(n.index); if (!o) throw new Error('Missing exact source node ' + n.index);
            o.position.fromArray(n.translation); o.quaternion.fromArray(n.rotation); o.scale.fromArray(n.scale);
          }
        }
        rider.scene.updateMatrixWorld(true); rider.scene.traverse((o: any) => { if (o.isSkinnedMesh) o.skeleton.update(); });
      } };
      rider.update = () => (window as any).__diag.apply();
    }, { poses, wrapperMode });
    const jobs: any[] = [];
    if (variant === 'repaired') for (let i = 0; i <= 16; i++) jobs.push({ pose: 'STEP', time: i / 8, view: 'side', yaw: 0, zoom: 1, frame: i, family: 'step-contact' });
    const views = [['left', 0], ['front', Math.PI / 2], ['right', Math.PI], ['rear', -Math.PI / 2], ['front-three-quarter', Math.PI / 4], ['rear-three-quarter', -Math.PI / 4]];
    for (const pose of stepOnly ? [] : ['T', 'A']) {
      for (let i = 0; i < 24; i++) jobs.push({ pose, time: null, view: 'orbit', yaw: i / 24 * Math.PI * 2, zoom: 1, frame: i, family: pose + '-orbit' });
      for (const [view, yaw] of views) jobs.push({ pose, time: null, view, yaw, zoom: 1, family: pose + '-views' });
      for (const [view, yaw, anchor] of [['underarm-left', 0, 'upperArm.L'], ['underarm-right', Math.PI, 'upperArm.R'], ['cuff-left', 0, 'hand.L'], ['cuff-right', Math.PI, 'hand.R'], ['neck', Math.PI / 4, 'neck']]) jobs.push({ pose, time: null, view, yaw, zoom: 4, anchor, family: pose + '-closeups' });
    }
    for (const job of jobs) {
      const sample = await page.evaluate(({ job, variant, wrapperMode }) => {
        const t = (window as any).__rockhop, r = (window as any).__render, d = r.debug, T = d.THREE, diag = (window as any).__diag;
        diag.pose = job.pose; diag.time = job.time ?? 0;
        d.bike.root.visible = job.pose === 'STEP'; d.bike.frame.visible = true;
        // Rider belongs to bike.frame, so hide only bike meshes when arms out.
        d.bike.root.visible = true; d.bike.root.traverse((o: any) => { if (o.isMesh) o.visible = job.pose === 'STEP'; });
        diag.rider.scene.traverse((o: any) => { if (o.isMesh) o.visible = true; });
        diag.apply();
        const box = new T.Box3().setFromObject(diag.rider.scene), center = box.getCenter(new T.Vector3());
        let anchor = job.anchor ? diag.rider.bones.get(job.anchor).getWorldPosition(new T.Vector3()) : center;
        const anchorKey = `${job.family}/${job.frame ?? job.view}`;
        const anchors = (window as any).__diagnosticAnchors ??= {};
        if (variant === 'repaired') anchors[anchorKey] = anchor.toArray();
        else anchor = new T.Vector3().fromArray(anchors[anchorKey]);
        r.setCameraOverride({ mode: 'orbit', yaw: job.yaw, pitch: .10, dist: job.pose === 'STEP' ? 5.3 : 5.9, x: anchor.x, y: anchor.y, screenX: .5, screenY: .5 });
        d.rig.camera.zoom = job.zoom; d.rig.camera.updateProjectionMatrix();
        document.getElementById('diagnostic-label')!.textContent = `ROCKHOP ACTUAL GARAGE | DIAGNOSTIC / UNACCEPTED\n${variant} wrapper=${wrapperMode} | ${job.pose}${job.time !== null ? ' source clip t=' + job.time.toFixed(3) + 's STEP' : ' explicit arms-out; corrective morphs zero'} | ${job.view}\nAuthored pose override; physics-driven riding, contact and mobile gates OPEN`;
        r.invalidate(); t.render(true);
        const bones: any = {}; diag.rider.scene.traverse((o: any) => { if (o.isBone) bones[o.name] = { local: o.matrix.toArray(), world: o.matrixWorld.toArray() }; });
        const meshes: any[] = []; diag.rider.scene.traverse((o: any) => { if (o.isSkinnedMesh) meshes.push({ name: o.name, vertices: o.geometry.attributes.position.count, matrix: o.matrixWorld.toArray(), morphNames: o.morphTargetDictionary, morphWeights: o.morphTargetInfluences }); });
        const matrixErrors: number[] = [];
        if (job.pose !== 'STEP') {
          const wrapperInverse = diag.rider.scene.matrixWorld.clone().invert();
          for (const n of diag.poses.poses.find((p: any) => p.name === job.pose).nodes) {
            const o = diag.nodeObjects.get(n.index); const actual = wrapperInverse.clone().multiply(o.matrixWorld);
            const expected = new T.Matrix4().set(...n.worldMatrix.flat());
            matrixErrors.push(Math.max(...actual.elements.map((v: number, i: number) => Math.abs(v - expected.elements[i]))));
          }
        }
        let fixture;
        if (job.pose === 'STEP' && job.frame === 0) {
          const nodes: any[] = []; d.bike.root.traverse((o: any) => { if (o !== diag.rider.scene && !o.isBone) nodes.push({ name: o.name, parent: o.parent?.name, local: o.matrix.toArray(), world: o.matrixWorld.toArray() }); });
          fixture = { bikeFrameWorld: d.bike.frame.matrixWorld.toArray(), bikeRootWorld: d.bike.root.matrixWorld.toArray(), bikeFrameLocal: d.bike.frameLocal.toArray(), bikeSourceJSON: d.bike.source.parser.json, bikeRuntimeNodes: nodes, bikeDebug: d.bike.debug, riderWrapperLocal: diag.rider.scene.matrix.toArray(), riderWrapperWorld: diag.rider.scene.matrixWorld.toArray(), riderParentWorld: diag.rider.scene.parent.matrixWorld.toArray(), state: t.getState() };
        }
        return { ...job, variant, wrapperMode, fixture, cloudPoseMatrixMaxError: Math.max(0, ...matrixErrors), bones, meshes, sceneMatrix: diag.rider.scene.matrixWorld.toArray(), stateHash: t.hashState(), garage: r.debugInfo().garage, camera: { matrix: d.rig.camera.matrixWorld.toArray(), zoom: d.rig.camera.zoom, fov: d.rig.camera.fov }, webdriver: navigator.webdriver, audioContexts: (window as any).__diagnosticAudioCount };
      }, { job, variant, wrapperMode });
      assert(sample.cloudPoseMatrixMaxError < 1e-5, 'Shared cloud pose matrix mismatch'); assert.equal(sample.webdriver, true); assert.equal(sample.audioContexts, 0); assert.equal(sample.garage.on, true);
      assert(Object.values(sample.bones).every((b: any) => b.world.every(Number.isFinite)));
      const folder = path.join(out, variant, job.family); fs.mkdirSync(folder, { recursive: true });
      sample.image = path.join(folder, job.frame !== undefined ? `${String(job.frame).padStart(4, '0')}.png` : `${job.view}.png`);
      await page.screenshot({ path: sample.image }); report.samples.push(sample);
    }
    for (const family of ['step-contact', 'T-orbit', 'A-orbit']) {
      const folder = path.join(out, variant, family); if (!fs.existsSync(folder)) continue;
      const ff = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', family === 'step-contact' ? '4' : '8', '-i', path.join(folder, '%04d.png'), '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', path.join(folder, 'played.mp4')], { encoding: 'utf8' });
      assert.equal(ff.status, 0, ff.stderr);
    }
  }
  await Promise.all(responses); assert.deepEqual(report.errors, []);
  for (const outfit of stepOnly ? ['street-mustard'] : ['street-mustard', 'street-openface']) {
    const expected = manifest.models.find((m: any) => m.logical === `models/rider-${outfit}.glb`);
    assert(report.loaded.some((m: any) => m.sha256 === expected.sha256 && m.status === 200), 'Exact source bytes not loaded');
  }
  const stepRows = report.samples.filter((s: any) => s.pose === 'STEP');
  assert(new Set(stepRows.map((s: any) => JSON.stringify(s.bones))).size > 1, 'STEP clip did not move');
  assert(stepRows.every((s: any) => s.meshes.some((m: any) => m.morphWeights.some((w: number) => w > .5))), 'STEP correctives inactive');
  const paired = new Map(report.samples.filter((s: any) => s.variant === 'repaired' && s.pose !== 'STEP').map((s: any) => [s.family + '/' + (s.frame ?? s.view), s]));
  for (const raw of report.samples.filter((s: any) => s.variant === 'raw-body11')) {
    const repaired = paired.get(raw.family + '/' + (raw.frame ?? raw.view)) as any;
    assert.deepEqual(raw.camera, repaired.camera, 'Matched effective cameras differ');
    assert.deepEqual(raw.bones, repaired.bones, 'Matched skeleton matrices differ');
    assert(raw.meshes.every((m: any) => (m.morphWeights ?? []).every((w: number) => w === 0)));
    assert(repaired.meshes.every((m: any) => (m.morphWeights ?? []).every((w: number) => w === 0)));
  }
  report.status = 'CAPTURED_UNACCEPTED';
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await context.close(); await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  console.log(JSON.stringify({ out, frames: report.samples.length, status: report.status, failure: report.failure, errors: report.errors }));
}
