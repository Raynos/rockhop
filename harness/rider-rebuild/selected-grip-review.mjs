/** Silent selected-source grip review: actual Garage gestures or trusted held keys.
 * --build=DIR --source=GLB --contract=JSON --profile=JSON --profile-sha256=HASH --out=FRESH_DIR --mode=garage|lean
 * --bike=rookie|pro --backend=webkit|metal --camera-yaw=RAD --camera-pitch=RAD --review-zoom=2.2
 * Existing reviewer orbit + explicit optical camera zoom; no private source, pose or clock overrides.
 */
import fs from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { register } from 'tsx/esm/api';
import { installGarageCaptureMeter } from './garage-capture-meter.mjs';

const arg = (name, fallback) => process.argv.find(v => v.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
for (const name of ['build', 'source', 'contract', 'profile', 'profile-sha256', 'out']) assert(arg(name), `Missing --${name}`);
const build = path.resolve(arg('build')), source = path.resolve(arg('source'));
const contractPath = path.resolve(arg('contract')), out = path.resolve(arg('out'));
const profilePath = path.resolve(arg('profile'));
const profileBytes = await fs.readFile(profilePath), gripProfile = JSON.parse(profileBytes);
const profileSHA256 = arg('profile-sha256'); assert(/^[a-f0-9]{64}$/.test(profileSHA256), 'Exact intended grip profile SHA256 required');
const mode = arg('mode', 'lean'), bike = arg('bike', 'rookie'), backend = arg('backend', 'metal');
const cameraYaw = Number(arg('camera-yaw', '.8')), cameraPitch = Number(arg('camera-pitch', '.22'));
const reviewZoom = Number(arg('review-zoom', '2.2'));
const cameraDistance = Number(arg('camera-distance', '3')), orbitSeconds = Number(arg('orbit-seconds', '18'));
assert(['garage', 'lean'].includes(mode)); assert(['rookie', 'pro'].includes(bike));
assert(['webkit', 'metal'].includes(backend));
assert(Number.isFinite(cameraYaw) && Math.abs(cameraYaw) <= Math.PI);
assert(Number.isFinite(cameraPitch) && cameraPitch >= -.06 && cameraPitch <= .55);
assert(Number.isFinite(cameraDistance) && cameraDistance >= 3 && cameraDistance <= 8, 'Existing runtime orbit limits');
assert(Number.isFinite(reviewZoom) && reviewZoom >= 1 && reviewZoom <= 4);
assert(Number.isFinite(orbitSeconds) && orbitSeconds >= 16 && orbitSeconds <= 60);
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
async function streamedPin(filename) {
  const hash = crypto.createHash('sha256'); let bytes = 0;
  for await (const chunk of createReadStream(filename)) { hash.update(chunk); bytes += chunk.length; }
  return { path: filename, sha256: hash.digest('hex'), bytes };
}
const contractBytes = await fs.readFile(contractPath), contract = JSON.parse(contractBytes);
const selected = JSON.parse(await fs.readFile(path.join(build, 'rider-remaster-source.json')));
const runtimeMetadataBytes = await fs.readFile(path.join(build, 'rider-remaster-contract.json'));
const runtimeMetadata = JSON.parse(runtimeMetadataBytes);
const upstreamContractSHA256 = contract.metadataSHA256 ?? sha(contractBytes);
assert.equal(selected.sha256, contract.glbSHA256 ?? contract.sourceSHA256);
assert.equal(selected.contractSHA256, upstreamContractSHA256);
assert.equal(runtimeMetadata.sourceSHA256, selected.sha256);
assert.equal(runtimeMetadata.metadataSHA256, upstreamContractSHA256);
assert.deepEqual(runtimeMetadata.driver, contract.driver, 'Requested and built runtime grip driver differ');
assert.equal(sha(profileBytes), profileSHA256, 'Exact source-pinned profile bytes required');
assert.equal(gripProfile.schema, 'rockhop-selected-grip-kinematic-v2');
assert.equal(gripProfile.source.sha256, selected.sha256);
assert.equal(gripProfile.contractSHA256, upstreamContractSHA256);
assert.equal(runtimeMetadata.driver.gripProfileHash, profileSHA256, 'Built driver declares exact fitted profile');
for (const side of ['left', 'right']) {
  const hand = gripProfile.hands[side];
  assert.equal(Object.keys(hand.digitFlex).length, 15, 'All15 digit controls per actual hand');
  assert.deepEqual(runtimeMetadata.driver.digitFlex[side], hand.digitFlex, `Exact source-derived digit controls ${side}`);
  assert.deepEqual(runtimeMetadata.driver.gripSocketPositionBike[side], hand.gripSocketPositionBike, `Exact fitted socket position ${side}`);
  assert.deepEqual(runtimeMetadata.driver.gripSocketQuaternionBike[side], hand.gripSocketQuaternionBike, `Exact fitted socket orientation ${side}`);
}
if (contract.sourceSHA256) assert.equal(sha(runtimeMetadataBytes), sha(contractBytes), 'Exact compiled metadata differs');
const sourcePin = await streamedPin(source);
assert.equal(sourcePin.sha256, selected.sha256); assert.equal(sourcePin.bytes, selected.bytes);
const catalog = JSON.parse(await fs.readFile(path.join(build, 'model-catalog.json')));
const bikeAsset = catalog.models.find(row => row.logical === `models/bike-${bike}.glb`);
assert(bikeAsset);
const bikePin = await streamedPin(path.join(build, bikeAsset.url));
assert.equal(bikePin.sha256, bikeAsset.sha256); assert.equal(bikePin.bytes, bikeAsset.bytes);
const garageSource = await fs.readFile('src/ui/garage.ts');
const fullTurnPixels = Number(garageSource.toString().match(/yawPerPx:\s*\(2 \* Math.PI\) \/ ([\d.]+)/)?.[1]);
assert(Number.isFinite(fullTurnPixels) && fullTurnPixels > 0);
await fs.mkdir(out, { recursive: false });
const phases = [{ name: 'neutral', ticks: 240, lean: 0 }, { name: 'forward', ticks: 360, lean: 1 },
  { name: 'backward', ticks: 360, lean: -1 }, { name: 'neutral-return', ticks: 240, lean: 0 }];
const report = { accepted: false, status: 'UNACCEPTED_SELECTED_GRIP_PLAYED_REVIEW', mode, bike,
  source: sourcePin, requestedGripProfileSHA256: profileSHA256, gripProfile: { path: profilePath, sha256: profileSHA256, schema: gripProfile.schema, source: gripProfile.source }, selectedManifest: selected, bikeAsset: { ...bikeAsset, buildFile: bikePin }, contract: { path: contractPath, sha256: sha(contractBytes) },
  runtimeMetadata: { path: path.join(build, 'rider-remaster-contract.json'), sha256: sha(runtimeMetadataBytes), upstreamContractSHA256 },
  sourcePinsAtCapture: await Promise.all(['src/render/hero/selected/rider.mjs', 'src/render/hero/selected/contract.mjs',
    'src/render/hero/selected/mass.mjs', 'src/render/camera/rig.ts', 'src/game/game.ts', 'src/render/frame.ts',
    'src/core/riderGeometry.ts', 'src/ui/garage.ts'].map(streamedPin)),
  sourcePinScope: 'Working-tree source hashes at capture; parent private-build receipt establishes compiled-source provenance.',
  build, phases: mode === 'lean' ? phases : null, errors: [], loaded: [],
  browser: { backend, version: null, renderer: null }, audio: 'Silent webdriver; audio=0; no audible override.',
  method: mode === 'garage' ? 'Normal Garage UI, trusted wheel zoom and continuous trusted pointer orbit; actual riding solver/breathing clock.'
    : 'Trusted held Arrow keys observed by harness; real-time paced120Hz game.setInput/step; actual simulated rider COM/torso; existing reviewer orbit camera with explicitly reported optical zoom.',
  limits: ['Parent judges the played movie. Presence/TRS/contact diagnostics do not accept palm, finger or elbow art.',
    'Capture render FPS counts actual CPU submissions, not GPU completion or encoded-video cadence.',
    'No geometry, source transforms, bone pose, animation clock, physics state or renderer cap writes.'] };
let browser, context, page, launched, server;
const pending = []; let videoStart;

// Cheap post-submission witness; never read skin buffers or vertices in the film.
function installPresenceMonitor({ sourceSHA256, metadataSHA256, meshRoles, expectedZoom, expectedBikeLogical, expectedProfileSHA256 }) {
  const owner = globalThis.window.__render, original = owner.render, cached = new WeakMap();
  const state = { submittedFrames: 0, invalidFrames: 0, examples: [], first: null, last: null };
  const visible = node => { for (let p = node; p; p = p.parent) if (!p.visible) return false; return true; };
  const attached = node => { for (let p = node; p; p = p.parent) if (p === owner.scene) return true; return false; };
  const inspect = () => {
    const rider = owner.debug.rider;
    if (rider && !cached.has(rider)) {
      const skins = [], bones = new Set();
      rider.scene.traverse(node => { if (node.isSkinnedMesh) {
        skins.push(node); for (const bone of node.skeleton.bones) bones.add(bone.uuid);
      } });
      const declaredRoles = Object.entries(meshRoles).map(([role, sourceName]) => ({ role, sourceName,
        meshes: rider.binding.meshes.filter(part => part.role === role || part.role.startsWith(role + '.primitive')).map(part => part.mesh) }));
      cached.set(rider, { skins, bones: bones.size, declaredRoles });
    }
    const bike = owner.debug.bike;
    if (bike && !cached.has(bike)) { const meshes = []; bike.root.traverse(node => { if (node.isMesh) meshes.push(node); }); cached.set(bike, { meshes }); }
    const bikePart = cached.get(bike);
    const part = cached.get(rider), candidate = rider?.debug?.candidate;
    return { sourceSHA256: candidate?.sourceSHA256 ?? null, metadataSHA256: candidate?.metadataSHA256 ?? null,
      selectedMarker: rider?.source?.scene?.userData?.selectedRemaster === true,
      bikeSourceLogical: bike?.source ? owner.heroDocUrl.get(bike.source) ?? null : null,
      bikeSourceUUID: bike?.source?.scene?.uuid ?? null, riderAttachedToSubmittedBike: rider?.bike === bike && rider?.placement?.parent === bike?.frame,
      visibleBikeMeshes: bikePart?.meshes.filter(node => visible(node) && attached(node) && node.geometry.attributes.position.count > 0).length ?? 0,
      sourceUUID: rider?.source?.scene?.uuid ?? null, instanceUUID: rider?.root?.uuid ?? null,
      nativeJoints: rider?.binding?.byId?.size ?? 0, skeletonBones: part?.bones ?? 0,
      visibleSkins: part?.skins.filter(node => visible(node) && attached(node) && node.geometry.attributes.position.count > 0).map(node => node.name) ?? [],
      authorRolesPresent: part?.declaredRoles.every(row => candidate.authorMeshRoles[row.role] === row.sourceName
        && row.meshes.length > 0 && row.meshes.every(node => visible(node) && attached(node) && node.geometry.attributes.position.count > 0)) ?? false,
      stageClip: rider?.debug?.stageClip ?? null, physicalPose: rider?.debug?.physicalPose ?? false,
      allBoneFinite: rider?.debug?.allBoneFinite ?? false,
      gripProfileHash: rider?.debug?.gripProfileHash ?? rider?.debug?.candidate?.gripProfileHash ?? null,
      opticalZoom: owner.debug.rig.camera.zoom, actualFOVDegrees: owner.debug.rig.camera.fov, effectiveFOVDegrees: owner.debug.rig.camera.getEffectiveFOV() };
  };
  function wrapped(...args) {
    const before = owner.renderer.info.render.frame, result = original.apply(this, args);
    if (owner.renderer.info.render.frame > before) {
      const row = inspect(); state.submittedFrames++; state.first ??= row; state.last = row;
      if (row.sourceSHA256 !== sourceSHA256 || row.metadataSHA256 !== metadataSHA256 || !row.selectedMarker
        || row.nativeJoints !== 75 || row.skeletonBones !== 75 || !row.allBoneFinite
        || row.gripProfileHash !== expectedProfileSHA256 || !row.authorRolesPresent || row.bikeSourceLogical !== expectedBikeLogical || !row.riderAttachedToSubmittedBike || !row.visibleBikeMeshes || Math.abs(row.opticalZoom - expectedZoom) > 1e-12) {
        state.invalidFrames++; if (state.examples.length < 12) state.examples.push({ frame: state.submittedFrames, ...row });
      }
    }
    return result;
  }
  owner.render = wrapped;
  globalThis.window.__selectedGripPresence = { state, inspect, stop() {
    if (owner.render === wrapped) owner.render = original; return state;
  } };
}

try {
  server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build },
    preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
  if (backend === 'metal') {
    const helper = new URL('../lib/browser.ts', import.meta.url);
    report.browser.helper = { path: 'harness/lib/browser.ts', sha256: sha(await fs.readFile(helper)) };
    register(); const { launchBrowser } = await import(helper.href);
    const previous = process.env.TRIALS_BROWSER_BACKEND;
    try { process.env.TRIALS_BROWSER_BACKEND = 'metal'; launched = await launchBrowser({ width: 1440, height: 900 }); }
    finally { if (previous === undefined) delete process.env.TRIALS_BROWSER_BACKEND; else process.env.TRIALS_BROWSER_BACKEND = previous; }
    browser = launched.browser;
    Object.assign(report.browser, { flagSet: launched.flagSet, probe: launched.probe });
    assert(launched.probe.ok && launched.probe.kind === 'webgl2' && /Metal/.test(launched.probe.renderer)
      && !/swiftshader|llvmpipe|software/i.test(launched.probe.renderer));
    await launched.context.close();
  } else browser = await webkit.launch({ headless: true });
  report.browser.version = browser.version();
  context = await browser.newContext({ viewport: { width: 1440, height: 900 },
    recordVideo: { dir: out, size: { width: 1440, height: 900 } } });
  await context.addInitScript(() => {
    localStorage.setItem('rockhop.onboarded', '1');
    localStorage.setItem('rockhop.quality', 'high');
    localStorage.setItem('rockhop.riderOutfit', 'street-remastered');
    localStorage.setItem('rockhop.economy.v1', JSON.stringify({ version: 1, wallet: 0, medals: {}, proOwned: true, equipped: 'rookie' }));
  });
  videoStart = performance.now(); page = await context.newPage(); page.setDefaultTimeout(120000);
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('response', response => {
    if (response.url() === selected.url) pending.push((async () => {
      assert.equal(response.status(), 200);
      // Stream independently; never copy the browser's large response body.
      const stream = await fetch(selected.url), hash = crypto.createHash('sha256'); let bytes = 0;
      assert.equal(stream.status, 200); assert.equal(stream.url, selected.url);
      for await (const chunk of stream.body) { hash.update(chunk); bytes += chunk.length; }
      const row = { url: response.url(), status: response.status(), sha256: hash.digest('hex'), bytes,
        hashScope: 'Independent public stream; browser response body not read' };
      assert.equal(row.sha256, selected.sha256); assert.equal(bytes, selected.bytes); report.loaded.push(row);
    })().catch(error => report.errors.push(error.message)));
  });
  const query = mode === 'lean' ? '?harness=1&audio=0&sw=0&outfit=street-remastered&physics=v2&hz=120&track=b1-first-ride' : '?audio=0&sw=0';
  await page.goto(server.resolvedUrls.local[0] + query);
  if (mode === 'garage') {
    await page.locator('.menu-screen.live .menu-item[data-id=garage]').click();
    await page.waitForSelector('.garage-screen.live');
    await page.locator(`button[data-bike=${bike}]`).click();
    await page.locator('button[data-outfit=street-remastered]').click();
    await page.evaluate(() => globalThis.window.__render.whenReady());
    await page.locator(`button[data-bike=${bike}][aria-pressed=true]`).waitFor();
  } else {
    await page.waitForFunction(() => globalThis.window.__rockhop?.ready && globalThis.window.__rockhop.info().trackId === 'b1-first-ride');
    report.camera = await page.evaluate(async ({ bike, cameraYaw, cameraPitch, cameraDistance, reviewZoom }) => {
      const t = globalThis.window.__rockhop, r = globalThis.window.__render;
      if (bike !== 'rookie') { t.setBike(bike); await t.loadTrack('b1-first-ride', 138717428); }
      t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
      const info = t.info(); if (info.bike !== bike || info.seed !== 138717428 || info.physicsHz !== 120)
        throw new Error('Track, bike, seed or120Hz preflight differs');
      const rider = r.debug.rider;
      const points = ['left', 'right'].map(side => rider.binding.exact(rider.binding.contract.hands[side].socketNodeName).getWorldPosition(new r.debug.THREE.Vector3()));
      const center = points[0].clone().add(points[1]).multiplyScalar(.5);
      const camera = { mode: 'orbit', x: center.x - .1, y: center.y + .02, yaw: cameraYaw,
        pitch: cameraPitch, dist: cameraDistance, screenX: .5, screenY: .5 };
      r.setCameraOverride(camera); t.render(true);
      const optical = r.debug.rig.camera;
      if (!optical?.isPerspectiveCamera || !Number.isFinite(optical.zoom)
        || typeof optical.updateProjectionMatrix !== 'function' || typeof optical.getEffectiveFOV !== 'function')
        throw new Error('Existing Three PerspectiveCamera optical zoom API required');
      optical.zoom = reviewZoom; optical.updateProjectionMatrix(); t.render(true);
      // Automation observes only actual trusted held-key events. No synthetic DOM input.
      const held = new Set(), events = [];
      for (const type of ['keydown', 'keyup']) globalThis.window.addEventListener(type, event => {
        if (!event.isTrusted || !['ArrowLeft', 'ArrowRight'].includes(event.code)) return;
        event.preventDefault(); if (type === 'keydown') held.add(event.code); else held.delete(event.code);
        events.push({ type, code: event.code, trusted: event.isTrusted, atMs: performance.now() });
      });
      globalThis.window.__selectedGripKeys = { held, events };
      return { requested: camera, actual: r.camera(), target: 'Initial actual bilateral palm socket midpoint, shifted10cm toward elbows',
        control: 'Existing public GameRenderer.setCameraOverride orbit API; existing3m minimum; reviewer optical zoom; no clock mutation',
        opticalReviewFraming: { zoom: optical.zoom, fovDegrees: optical.fov, effectiveFOVDegrees: optical.getEffectiveFOV(),
          worldMatrix: optical.matrixWorld.toArray(), projectionMatrix: optical.projectionMatrix.toArray(),
          effect: 'Magnifies the actual unchanged rendered scene; not player-camera/performance acceptance.' }, info };
    }, { bike, cameraYaw, cameraPitch, cameraDistance, reviewZoom });
  }
  report.browser.renderer = await page.evaluate(() => {
    const gl = globalThis.window.__render.renderer.getContext(), extension = gl.getExtension('WEBGL_debug_renderer_info');
    return String(gl.getParameter(extension ? extension.UNMASKED_RENDERER_WEBGL : gl.RENDERER));
  });
  if (backend === 'metal') assert(/Metal/.test(report.browser.renderer) && !/swiftshader|llvmpipe|software/i.test(report.browser.renderer));
  report.identity = await page.evaluate(() => ({ candidate: structuredClone(globalThis.window.__render.debug.rider.debug.candidate),
    driver: structuredClone(globalThis.window.__render.debug.rider.driver),
    gripProfileHash: globalThis.window.__render.debug.rider.debug.gripProfileHash ?? globalThis.window.__render.debug.rider.debug.candidate.gripProfileHash ?? null, nativeJointNames: [...globalThis.window.__render.debug.rider.binding.byId].map(([id, bone]) => ({ id, name: bone.name })) }));
  assert.equal(report.identity.candidate.sourceSHA256, sourcePin.sha256);
  assert.equal(report.identity.gripProfileHash, profileSHA256, 'Exact intended selected grip profile is activated in the actual runtime');
  assert.equal(report.identity.candidate.metadataSHA256, upstreamContractSHA256);
  assert.deepEqual(report.identity.driver, runtimeMetadata.driver, 'Actual selected driver equals built metadata');
  assert.equal(report.identity.nativeJointNames.length, 75);
  assert.deepEqual(report.identity.nativeJointNames.map(row => row.id).sort(), Object.keys(contract.specification.jointNames).sort(), 'Exact native75 identities');
  report.driverSHA256 = sha(JSON.stringify(report.identity.driver));
  report.profileDriverIdentity = { sourceSHA256: sourcePin.sha256, runtimeMetadataSHA256: sha(runtimeMetadataBytes),
    runtimeDriverSHA256: report.driverSHA256, activatedGripProfileSHA256: report.identity.gripProfileHash,
    selectedGripProfile: structuredClone(report.identity.driver.selectedGripProfile ?? null),
    exactProfileControlsVerified: { sides: 2, nativeDigitControls: 30, socketPositionAndOrientation: true }, definition: 'Entire actual runtime driver, including palm/contact and per-digit/opposed-thumb settings; exact equality to built metadata checked.' };
  await page.evaluate(installPresenceMonitor, { sourceSHA256: sourcePin.sha256, metadataSHA256: upstreamContractSHA256, meshRoles: contract.specification.meshNames, expectedZoom: mode === 'lean' ? reviewZoom : 1, expectedBikeLogical: bikeAsset.logical, expectedProfileSHA256: profileSHA256 });
  await page.evaluate(installGarageCaptureMeter);
  report.readyOffsetSeconds = (performance.now() - videoStart) / 1000;
  if (mode === 'garage') {
    const box = await page.locator('.garage-stage').boundingBox(); assert(box);
    const point = { x: box.x + box.width * .72, y: box.y + box.height * .55 };
    assert(point.x - fullTurnPixels >= 0);
    assert(await page.evaluate(p => !!globalThis.document.elementFromPoint(p.x, p.y)?.closest('.garage-stage'), point));
    await page.mouse.move(point.x, point.y); await page.mouse.wheel(0, -240); await page.mouse.wheel(0, -240);
    await page.waitForTimeout(500); await page.mouse.down();
    await page.evaluate(() => globalThis.window.__garageCaptureMeter.reset());
    const started = performance.now(); let progress = 0, moves = 0;
    while (progress < 1) {
      progress = Math.min(1, (performance.now() - started) / (orbitSeconds * 1000));
      await page.mouse.move(point.x - fullTurnPixels * progress, point.y); moves++;
      if (progress < 1) await page.waitForTimeout(16);
    }
    await page.waitForTimeout(100); await page.mouse.up();
    report.orbit = { wallSeconds: (performance.now() - started) / 1000, fullTurnPixels, moves,
      pointerSensitivitySourceSHA256: sha(garageSource), zoom: 'Trusted wheel to player3m minimum' };
    report.garageEnd = await page.evaluate(() => ({ debug: structuredClone(globalThis.window.__render.debug.rider.debug), camera: globalThis.window.__render.camera() }));
    assert.equal(report.garageEnd.debug.stageClip, 'Riding IK/breathing');
  } else {
    report.played = { phases: [], inputs: [], motionSamples: [], ticks: 0 };
    for (const phase of phases) {
      if (phase.lean === 1) await page.keyboard.down('ArrowRight');
      if (phase.lean === -1) { await page.keyboard.up('ArrowRight'); await page.keyboard.down('ArrowLeft'); }
      if (phase.lean === 0) { await page.keyboard.up('ArrowRight'); await page.keyboard.up('ArrowLeft'); }
      const played = await page.evaluate(async ({ phase, startTick }) => {
        const t = globalThis.window.__rockhop, r = globalThis.window.__render, rider = r.debug.rider;
        const keys = globalThis.window.__selectedGripKeys, inputs = [], motionSamples = [], faults = [];
        const joints = [...rider.binding.byId], started = performance.now(); let tick = 0, maximumCatchupTicks = 0, latestFrame;
        const rootBone = joints.find(([, bone]) => !bone.parent?.isBone)[1], originalUpdate = rider.update;
        const label = globalThis.document.getElementById('selected-grip-phase') ?? globalThis.document.createElement('div');
        label.id = 'selected-grip-phase'; label.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#000d;color:white;padding:8px 14px;font:18px monospace';
        label.textContent = `${t.info().bike} actual held-key gameplay: ${phase.name}`; globalThis.document.body.append(label);
        rider.update = function(frame) { const result = originalUpdate.call(this, frame);
          latestFrame = { bikeX: frame.bikeX, bikeY: frame.bikeY, bikeAngle: frame.bikeAngle, tSim: frame.tSim,
            tick: frame.tick, crashed: frame.crashed, faulted: frame.faulted, rider: structuredClone(frame.rider), riderBody: structuredClone(frame.riderBody) }; return result; };
        const snapshot = () => motionSamples.push({ tick: startTick + tick, phase: phase.name, input: inputs.at(-1) ?? null,
          frame: structuredClone(latestFrame), debug: structuredClone(rider.debug),
          bikeFrameWorld: rider.bike.frame.matrixWorld.toArray(), skeletonWorld: rootBone.parent.matrixWorld.toArray(),
          submittedRenderFrame: r.renderer.info.render.frame,
          camera: { zoom: r.debug.rig.camera.zoom, fovDegrees: r.debug.rig.camera.fov, effectiveFOVDegrees: r.debug.rig.camera.getEffectiveFOV(),
            worldMatrix: r.debug.rig.camera.matrixWorld.toArray(), projectionMatrix: r.debug.rig.camera.projectionMatrix.toArray() },
          joints: joints.map(([id, bone]) => ({ id, name: bone.name, position: bone.position.toArray(), quaternion: bone.quaternion.toArray(), scale: bone.scale.toArray(), worldMatrix: bone.matrixWorld.toArray() })) });
        t.render(true); if (startTick === 0) snapshot();
        try { await new Promise((resolve, reject) => {
          function frame() { try {
            const wanted = Math.min(phase.ticks, Math.floor((performance.now() - started) * .12));
            maximumCatchupTicks = Math.max(maximumCatchupTicks, wanted - tick); let lastRenderedTick = -1;
            while (tick < wanted) {
              const input = { throttle: 0, brake: 0, lean: Number(keys.held.has('ArrowRight')) - Number(keys.held.has('ArrowLeft')), hop: false, restart: false };
              if (input.lean !== phase.lean) throw new Error('Trusted held input differs from requested phase');
              inputs.push(input); t.setInput(input); t.step(1); tick++;
              const state = t.getState(); if (state.faulted && faults.length < 16) faults.push({ tick: startTick + tick, faulted: state.faulted });
              if (tick % 5 === 0) { t.render(true); lastRenderedTick = tick; snapshot(); }
            }
            if (lastRenderedTick !== tick) t.render(true);
            if (tick === phase.ticks) resolve(); else globalThis.requestAnimationFrame(frame);
          } catch (error) { reject(error); } }
          globalThis.requestAnimationFrame(frame);
        }); } finally { rider.update = originalUpdate; }
        return { name: phase.name, ticks: tick, inputs, motionSamples, faults, maximumCatchupTicks,
          wallSeconds: (performance.now() - started) / 1000, state: structuredClone(t.getState()), hash: t.hashState(),
          debug: structuredClone(rider.debug), trustedKeyEvents: [...keys.events] };
      }, { phase, startTick: report.played.ticks });
      report.played.inputs.push(...played.inputs); report.played.motionSamples.push(...played.motionSamples);
      report.played.ticks += played.ticks; const endpoint = { ...played }; delete endpoint.inputs; delete endpoint.motionSamples; report.played.phases.push(endpoint);
      assert.deepEqual(played.faults, [], 'Actual held lean must stay live');
    }
    report.played.finalHash = report.played.phases.at(-1).hash;
    report.played.localTRSConvention = 'Native75 local translationXYZ/quaternionXYZW/scaleXYZ; column-major Three world matrices; no source-rest edits.';
    assert.equal(report.played.ticks, 1200); assert.equal(report.played.motionSamples.length, 241);
    assert(report.played.motionSamples.every((row, i) => row.tick === i * 5 && row.debug.physicalPose && row.debug.stageClip === null
      && row.debug.allBoneFinite && (row.debug.gripProfileHash ?? row.debug.candidate.gripProfileHash) === profileSHA256 && row.joints.length === 75
      && [...row.camera.worldMatrix, ...row.camera.projectionMatrix, row.camera.fovDegrees, row.camera.effectiveFOVDegrees, row.camera.zoom].every(Number.isFinite)
      && row.joints.every(j => [...j.position, ...j.quaternion, ...j.scale, ...j.worldMatrix].every(Number.isFinite))));
    report.performanceLimit = 'Exact24Hz state witness draws count in displayed actual render FPS; additional draws under catchup mean this is not normal-player FPS.';
  }
  report.performance = await page.evaluate(() => globalThis.window.__garageCaptureMeter.stop());
  report.presence = await page.evaluate(() => globalThis.window.__selectedGripPresence.stop());
  assert(report.presence.submittedFrames > 0); assert.equal(report.presence.invalidFrames, 0, 'Exact selected source/75/visible authored skins on every observed submission');
  await Promise.all(pending); assert.deepEqual(report.errors, []); assert(report.loaded.length > 0);
  await page.screenshot({ path: path.join(out, 'played-end.png') });
  report.captureChecksCompleted = true;
} catch (error) { report.failure = error.stack; process.exitCode = 1; }
finally {
  const cleanup = async (name, close) => { try { await close(); } catch (error) { report.errors.push(`${name}: ${error.message}`); report.failure ??= error.stack; process.exitCode = 1; } };
  const video = page?.video(), rawVideoPath = path.join(out, `${mode}-played.webm`);
  await cleanup('context', () => context?.close());
  if (video) await cleanup('video', () => video.saveAs(rawVideoPath));
  await cleanup('browser', () => launched ? launched.close() : browser?.close());
  await cleanup('server', () => server && new Promise((resolve, reject) => server.httpServer.close(error => error ? reject(error) : resolve())));
  report.recipeSHA256 = sha(await fs.readFile(new URL(import.meta.url)));
  report.rawVideoPath = video ? rawVideoPath : null;
  report.captureCheckpoint = { status: 'PARTIAL_CAPTURE_SAVED_ENCODING_AND_PARENT_REVIEW_PENDING',
    accepted: false, requires: 'Successful encoding, external guard exit and parent played-movie judgment',
    rawStreamRetention: 'Raw stream retained even if encoding fails or the external guard stops this process.' };
  // Durable capture receipt precedes any encoding; a guard stop must not erase results.
  await fs.writeFile(path.join(out, 'report.capture.partial.json'), JSON.stringify(report, null, 2) + '\n');
  if (video) {
    const encodedPath = path.join(out, `${mode}-played.mp4`);
    const ffmpegArgs = ['-v', 'error', '-y', '-threads', '2', '-i', rawVideoPath];
    if (Number.isFinite(report.readyOffsetSeconds)) ffmpegArgs.push('-ss', report.readyOffsetSeconds.toFixed(3));
    ffmpegArgs.push('-an', '-vf', 'fps=25', '-c:v', 'libx264', '-threads', '2', '-crf', '18',
      '-pix_fmt', 'yuv420p', '-movflags', '+faststart', encodedPath);
    const encoded = spawnSync('ffmpeg', ffmpegArgs, { encoding: 'utf8', maxBuffer: 1024 * 1024 });
    report.encoding = { exitCode: encoded.status, signal: encoded.signal, stderr: encoded.stderr,
      args: ffmpegArgs, decoderThreads: 2, encoderThreads: 2, presentationFPS: 25,
      rawRetained: true, encodedPath, trimmedStartSeconds: report.readyOffsetSeconds ?? 0 };
    const probeVideo = filename => {
      const result = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,r_frame_rate,avg_frame_rate,nb_frames,duration:format=duration',
        '-of', 'json', filename], { encoding: 'utf8' });
      return { exitCode: result.status, stderr: result.stderr, metadata: result.status === 0 ? JSON.parse(result.stdout) : null };
    };
    report.videoRates = { raw: probeVideo(rawVideoPath), presentation: probeVideo(encodedPath),
      meaning: 'Presentation normalized to25fps without interpolation. Encoded-video cadence is separate from measured actual render submissions and RAF FPS.' };
    if (encoded.status !== 0 || report.videoRates.presentation.exitCode !== 0) {
      report.failure ??= `Encoding failed: ${encoded.status} ${encoded.stderr}`; process.exitCode = 1;
    }
  }
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, mode, bike, ticks: report.played?.ticks, submittedFrames: report.presence?.submittedFrames, failure: report.failure }));
}
