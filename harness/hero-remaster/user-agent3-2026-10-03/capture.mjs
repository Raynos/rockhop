/** Exact candidate poses on actual Garage stage; riding geometry is diagnostic. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- Playwright browser globals and constructor-only silent audio trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';

const [buildArg, driverArg, outputArg] = process.argv.slice(2);
assert(outputArg, 'Usage: capture.mjs private-build driver.json fresh-output');
const build = path.resolve(buildArg), out = path.resolve(outputArg);
assert(!fs.existsSync(out), 'Capture output must be fresh');
fs.mkdirSync(out, { recursive: true });
const driverBytes = fs.readFileSync(driverArg), driver = JSON.parse(driverBytes);
const manifestBytes = fs.readFileSync(path.join(build, 'hero-review.json'));
const manifest = JSON.parse(manifestBytes);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const candidate = manifest.models.find(m => m.logical === 'models/rider-street-mustard.glb');
assert.equal(candidate.sha256, driver.conditionedGLBSHA256);
assert(!manifest.newRiderAdapter && !manifest.newRiderSeam && !manifest.newRiderHipCorrective);
const report = { status: 'CAPTURE_PENDING_UNACCEPTED', build, driverSHA256: sha(driverBytes),
  manifestSHA256: sha(manifestBytes), candidate, errors: [], samples: [], clips: [], loaded: [],
  limits: ['Exact authored pose override; no physics-driven candidate riding.',
    'Garage normally selects authored geometry; riding geometry is explicitly staged for comparison.',
    'Native film shares candidate, pose times and named directions; native orthographic and Garage perspective projections differ.',
    'Gray/structural PBR control, no protected generated identity or finished hoodie.',
    'Finite frames do not certify continuous parity, clearance, support, art or device acceptance.'] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build },
  preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 960, height: 640 }, deviceScaleFactor: 1 });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1'); window.__agent3AudioCount = 0;
  for (const key of ['AudioContext', 'webkitAudioContext']) window[key] = class {
    constructor() { window.__agent3AudioCount++; throw new Error('Silent capture forbids AudioContext'); }
  };
});
const page = await context.newPage(), loaded = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => {
  if (r.url().includes(candidate.url)) loaded.push(r.body().then(b => report.loaded.push({ sha256: sha(b), bytes: b.length, status: r.status() })));
});
try {
  report.launchURL = server.resolvedUrls.local[0] + '?audio=0&sw=0&outfit=street-mustard&rider=gltf&bike=gltf&physics=v2&hz=120';
  await page.goto(report.launchURL, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__rockhop?.ready && window.__rockhop?.app, null, { timeout: 120000 });
  await page.waitForFunction(() => !document.querySelector('#loader') || document.querySelector('#loader')?.getAttribute('data-done') === '1', null, { timeout: 120000 });
  await page.evaluate(async () => {
    const t = window.__rockhop, r = window.__render;
    t.setQuality('high'); await r.whenReady(); t.app.goto('garage'); await r.whenReady(); t.render(true);
  });
  await page.waitForFunction(() => window.__render.debugInfo().garage.on);
  await page.waitForTimeout(700);
  await page.addStyleTag({ content: '#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;top:8px;left:10px;color:white;background:#101820e8;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}' });
  await page.evaluate(driver => {
    const r = window.__render, d = r.debug, T = d.THREE, rider = d.rider;
    const label = document.createElement('div'); label.id = 'agent3-label'; document.body.append(label);
    const bones = new Map();
    for (const [o, assoc] of rider.source.parser.associations) {
      if (!o.isBone || assoc.nodes === undefined) continue;
      const name = rider.source.parser.json.nodes[assoc.nodes].name;
      const matches = rider.scene.getObjectsByProperty('name', o.name);
      if (matches.length !== 1) throw new Error('Ambiguous runtime bone ' + name);
      bones.set(name, matches[0]);
    }
    if (bones.size !== driver.jointOrderNative.length) throw new Error('Complete skin joint count mismatch');
    rider.scene.updateMatrixWorld(true);
    const wrapper = rider.scene.matrixWorld.clone();
    const target = new T.Vector3(.65, .9, 0).applyMatrix4(wrapper);
    window.__agent3 = { rider, bones, wrapper, target, driver, index: 0, geometry: 'authored', apply() {
      for (const item of rider.sleeveGeometry) item.mesh.geometry = this.geometry === 'authored' ? item.authored : item.riding;
      rider.scene.updateMatrixWorld(true);
      const f = driver.frames[this.index], desired = new Map();
      for (const [name, bone] of bones) desired.set(bone, wrapper.clone().multiply(new T.Matrix4().fromArray(f.jointWorldColumnMajor[name])));
      for (const [bone, world] of desired) {
        const parent = desired.get(bone.parent) ?? bone.parent.matrixWorld;
        bone.matrixAutoUpdate = false; bone.matrix.copy(parent.clone().invert().multiply(world));
      }
      rider.scene.updateMatrixWorld(true);
      rider.scene.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
    } };
    rider.update = () => window.__agent3.apply();
  }, driver);
  const views = [['side', 0], ['front-three-quarter', Math.PI / 4], ['rear-three-quarter', -Math.PI / 4]];
  const anchors = new Map();
  for (const shading of ['pbr', 'gray']) for (const [view, yaw] of views) {
    // Gray uses only one complete side sequence initially; avoid a broad gallery.
    if (shading === 'gray' && view !== 'side') continue;
    for (const geometry of ['authored', 'riding']) {
      const folder = path.join(out, shading, view, geometry); fs.mkdirSync(folder, { recursive: true });
      for (let n = 0; n <= 132; n++) {
        const index = n * 4;
        const sample = await page.evaluate(({ index, geometry, shading, yaw, view }) => {
          const t = window.__rockhop, r = window.__render, d = r.debug, a = window.__agent3;
          a.index = index; a.geometry = geometry; a.apply();
          a.rider.scene.traverse(o => { if (o.isMesh) {
            const materials = Array.isArray(o.material) ? o.material : [o.material];
            for (const m of materials) { m.userData.agent3Color ??= m.color.clone(); m.color.copy(m.userData.agent3Color); if (shading === 'gray') m.color.setRGB(.55, .55, .55); }
          } });
          r.setCameraOverride({ mode: 'orbit', yaw, pitch: .10, dist: 4.5,
            x: a.target.x, y: a.target.y, screenX: .5, screenY: .5 });
          document.getElementById('agent3-label').textContent = `ACTUAL GARAGE | UNACCEPTED DIAGNOSTIC\n${geometry === 'authored' ? 'Normal Garage authored geometry' : 'Normal RIDING geometry shown on Garage stage'} | ${shading} | ${view}\nShared source t=${(index / 48).toFixed(3)}s | no candidate physics/contact pass`;
          r.invalidate(); t.render(true);
          let matrixMaxError = 0, worstBone;
          const inverseWrapper = a.wrapper.clone().invert();
          for (const [name, bone] of a.bones) {
            const actual = inverseWrapper.clone().multiply(bone.matrixWorld).elements;
            const wanted = a.driver.frames[index].jointWorldColumnMajor[name];
            const error = Math.max(...actual.map((v, k) => Math.abs(v - wanted[k])));
            if (error > matrixMaxError) { matrixMaxError = error; worstBone = name; }
          }
          return { index, timeS: index / 48, geometry, shading, view, matrixMaxError, worstBone,
            stateHash: t.hashState(), webdriver: navigator.webdriver, audioContexts: window.__agent3AudioCount,
            garage: r.debugInfo().garage.on, camera: { world: d.rig.camera.matrixWorld.toArray(), projection: d.rig.camera.projectionMatrix.toArray() },
            riderWrapperWorld: a.wrapper.toArray(), bikeFrameWorld: d.bike.frame.matrixWorld.toArray(),
            meshes: a.rider.sleeveGeometry.map(item => ({ name: item.mesh.name,
              authoredSelected: item.mesh.geometry === item.authored, ridingSelected: item.mesh.geometry === item.riding,
              vertices: item.mesh.geometry.getAttribute('position').count,
              sourceIDAttribute: Boolean(item.mesh.geometry.getAttribute('_source_id')) })) };
        }, { index, geometry, shading, yaw, view });
        if (!(sample.webdriver && sample.garage && sample.audioContexts === 0 && sample.matrixMaxError < 1e-5))
          report.rejectedSample = sample;
        assert(sample.webdriver && sample.garage && sample.audioContexts === 0 && sample.matrixMaxError < 1e-5,
          JSON.stringify({ index, matrixMaxError: sample.matrixMaxError, worstBone: sample.worstBone, audioContexts: sample.audioContexts }));
        assert(sample.meshes.every(m => m.sourceIDAttribute));
        const key = `${shading}/${view}/${index}`;
        if (geometry === 'authored') anchors.set(key, sample.camera);
        else assert.deepEqual(sample.camera, anchors.get(key), 'Paired effective cameras differ');
        await page.screenshot({ path: path.join(folder, `${String(n).padStart(4, '0')}.png`) });
        report.samples.push(sample);
      }
      const movie = path.join(folder, 'played.mp4');
      const ff = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '12', '-i', path.join(folder, '%04d.png'),
        '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', movie], { encoding: 'utf8' });
      assert.equal(ff.status, 0, ff.stderr);
      report.clips.push({ path: movie, sha256: sha(fs.readFileSync(movie)), frames: 133, fps: 12, audio: false });
    }
  }
  await Promise.all(loaded);
  assert(report.loaded.some(r => r.sha256 === driver.conditionedGLBSHA256 && r.status === 200));
  assert.equal(new Set(report.samples.map(s => s.stateHash)).size, 1, 'Physics changed during authored capture');
  assert.deepEqual(report.errors, []); report.status = 'CAPTURED_UNACCEPTED';
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await context.close(); await browser.close(); await new Promise(resolve => server.httpServer.close(resolve));
  console.log(JSON.stringify({ status: report.status, frames: report.samples.length, clips: report.clips.length, failure: report.failure }));
}
