/** Actual recorded game inputs, complete dressed rider and measured joint debug.
 * Optional --bike=rookie|pro uses the existing game-supported bike choice.
 */
/* oxlint-disable typescript/no-explicit-any -- read-only renderer evidence. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { witnessGlbResponse } from './glb-response-witness.mjs';
import { inspectRiderMaterialInventory } from './inspect-prepared-materials.mjs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
const arg = (name: string, fallback = '') => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
assert(!fs.existsSync(out), 'Fresh output required');
const recording = decodeJSON(fs.readFileSync(arg('recording', 'harness/inputs/b1-first-ride/bot-3.json'), 'utf8'));
const bike = arg('bike', recording.header.bike ?? 'rookie');
assert(bike === 'rookie' || bike === 'pro', '--bike must be rookie or pro');
const source = JSON.parse(fs.readFileSync(path.join(build, 'rider-rebuild-inputs.json'), 'utf8'));
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8'));
const bikeAssets = Object.fromEntries(['rookie', 'pro'].map(choice => [choice,
  catalog.models.find((row: any) => row.logical === `models/bike-${choice}.glb`)]));
assert(bikeAssets.rookie && bikeAssets.pro, 'Both authored bike catalogue pins required');
fs.mkdirSync(path.join(out, 'frames'), { recursive: true });
const inputs = expandFrames(recording), fps = 12, stride = recording.header.physicsHz / fps;
assert(Number.isInteger(stride));
const count = Math.min(Math.floor(inputs.length / stride), Math.round(Number(arg('seconds', '16')) * fps));
const yaw = Number(arg('yaw', '1.4'));
const report: any = { build, fps, stride, count, errors: [], loaded: [], samples: [],
  selectedRiderSource: { sha256: source.sourceSHA256, metadataSHA256: source.metadataSHA256 },
  bikeSelection: { requested: bike, recorded: recording.header.bike ?? 'rookie',
    overridden: !!arg('bike'), inputRecordingUnchanged: true, assets: bikeAssets,
    path: 'Existing __rockhop.setBike -> Game.setBike, also used by Garage choice' },
  scope: 'Actual recorded game inputs and supported bike choice; camera follows declared pelvis; no pose injection or physics mutation' };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const responses: Promise<void>[] = [];
const witnesses = new Map();
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', response => {
  if (response.url().endsWith('.glb')) responses.push(witnessGlbResponse(response, witnesses)
    .then(row => { report.loaded.push(row); }).catch(error => { report.errors.push(error.message); }));
});
try {
  await page.goto(server.resolvedUrls!.local[0] + `?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${recording.header.physics ?? 'v1'}&hz=${recording.header.physicsHz}`);
  await page.waitForFunction(() => (window as any).__rockhop?.ready, null, { timeout: 120000 });
  report.bikeSelection.effective = await page.evaluate(async ({ header, bike }) => {
    const t = (window as any).__rockhop, r = (window as any).__render;
    t.setBike(bike); await r.whenReady();
    await t.loadTrack(header.trackId, header.seed); await r.whenReady(); t.setQuality('high'); await r.whenReady(); t.skipCountdown();
    return t.info().bike;
  }, { header: recording.header, bike });
  assert.equal(report.bikeSelection.effective, bike, 'Actual game selected requested bike');
  report.materialInventory = await page.evaluate(inspectRiderMaterialInventory);
  for (let i = 0; i < count; i++) {
    const sample = await page.evaluate(({ input, yaw }) => {
      const t = (window as any).__rockhop, r = (window as any).__render, d = r.debug;
      for (const frame of input) { t.setInput(frame); t.step(1); }
      // Alpha zero first renders the previous sampled state; settle the same
      // unchanged state before measuring a camera target from actual bones.
      t.render(true); t.render(true);
      const candidate = d.rider.debug.candidate, pelvisName = candidate.jointNames[candidate.roles.pelvis];
      const pelvis = d.rider.scene.getObjectByName(pelvisName); if (!pelvis) throw new Error('Missing declared pelvis');
      const p = pelvis.getWorldPosition(new d.THREE.Vector3());
      r.setCameraOverride({ mode: 'orbit', x: p.x, y: p.y + .22, yaw, pitch: .08, dist: 6.0, screenX: .5, screenY: .5 });
      t.render(true);
      const screen = pelvis.getWorldPosition(new d.THREE.Vector3()).project(d.rig.camera);
      // Actual posed transforms allow continuity review across supported frames;
      // these are read-only witnesses after the same recorded physics inputs.
      const jointPose = [...d.rider.binding.byId].map(([id, bone]: any) => ({ id,
        localPosition: bone.position.toArray(), localQuaternion: bone.quaternion.toArray(),
        localScale: bone.scale.toArray(), worldPosition: bone.getWorldPosition(new d.THREE.Vector3()).toArray() }));
      return { cameraAim: p.toArray(), pelvisScreen: screen.toArray(), camera: d.rig.debug(), tick: t.getState().tick, input: input.at(-1), state: structuredClone(t.getState()), debug: structuredClone(d.rider.debug), jointPose, hash: t.hashState() };
    }, { input: inputs.slice(i * stride, (i + 1) * stride), yaw });
    report.samples.push(sample);
    await page.screenshot({ path: path.join(out, 'frames', `${String(i).padStart(4, '0')}.png`) });
  }
  await Promise.all(responses); assert.deepEqual(report.errors, []);
  assert(report.loaded.some((row: any) => row.sha256 === source.sourceSHA256), 'Exact selected GLB served by actual build');
  assert(report.loaded.some((row: any) => row.sha256 === bikeAssets[bike].sha256), 'Exact selected authored bike GLB served by actual build');
  assert(report.samples.every((row: any) => row.debug.allBoneFinite), 'Complete hierarchy finite');
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i', path.join(out, 'frames/%04d.png'), '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'ride-played.mp4')], { encoding: 'utf8' });
  assert.equal(encoded.status, 0, encoded.stderr);
} catch (error) { report.failure = error instanceof Error ? error.stack : String(error); process.exitCode = 1; }
finally {
  await browser.close(); await new Promise<void>(resolve => server.httpServer.close(() => resolve()));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, samples: report.samples.length, errors: report.errors, failure: report.failure }));
}
