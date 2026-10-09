/** Continuous headless film: actual held inputs and simulated rider state. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { webkit } from 'playwright';
import { register } from 'tsx/esm/api';
import { createPrivateDevReview } from './private-dev-review.mjs';
import { witnessGlbResponse } from './glb-response-witness.mjs';
import { installGarageCaptureMeter } from './garage-capture-meter.mjs';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const source = arg('source'), contractPath = arg('contract'), out = path.resolve(arg('out') ?? '');
assert(source && contractPath && arg('out'), 'Pass --source, --contract and fresh --out');
const bike = arg('bike') ?? 'rookie'; assert(['rookie', 'pro'].includes(bike));
const backend = arg('backend') ?? 'webkit';
assert(['webkit', 'metal'].includes(backend), 'Pass --backend=webkit|metal');
const cameraYaw = Number(arg('camera-yaw') ?? 1.4);
assert(Number.isFinite(cameraYaw) && Math.abs(cameraYaw) <= Math.PI, 'Camera yaw must be finite radians within ±pi');
await fs.mkdir(out, { recursive: false });
const contract = JSON.parse(await fs.readFile(contractPath));
const development = await createPrivateDevReview({ source, contractPath, allowFailedDiagnostic: true });
const phases = [{ name: 'neutral', ticks: 240, lean: 0 }, { name: 'forward', ticks: 360, lean: 1 },
  { name: 'backward', ticks: 360, lean: -1 }, { name: 'neutral-return', ticks: 240, lean: 0 }];
const report = { accepted: false, status: 'UNACCEPTED_ACTUAL_GAMEPLAY_LEAN', bike,
  source: development.receipt, phases, errors: [], loaded: [],
  browser: { backend, version: null, renderer: null, flagSet: backend === 'webkit' ? 'webkit-default' : null, helper: null },
  method: 'Continuous real-time fixed120Hz game inputs; simulated COM/torso drives selected rider. No pose, joint, animation-clock or physics-state injection.' };
let browser, context, page, launched;
const responses = [], witnesses = new Map();
try {
  assert.equal(development.receipt.diagnosticKind, 'actual-gameplay-lean');
  if (backend === 'metal') {
    const helperURL = new URL('../lib/browser.ts', import.meta.url);
    report.browser.helper = { path: 'harness/lib/browser.ts',
      sha256: crypto.createHash('sha256').update(await fs.readFile(helperURL)).digest('hex') };
    register();
    const { launchBrowser } = await import(helperURL.href);
    const previousBackend = process.env.TRIALS_BROWSER_BACKEND;
    try {
      // This capture child alone selects Metal; restore its environment after launch.
      process.env.TRIALS_BROWSER_BACKEND = 'metal';
      launched = await launchBrowser({ width: 1440, height: 900 });
    } finally {
      if (previousBackend === undefined) delete process.env.TRIALS_BROWSER_BACKEND;
      else process.env.TRIALS_BROWSER_BACKEND = previousBackend;
    }
    browser = launched.browser;
    Object.assign(report.browser, { version: browser.version(), flagSet: launched.flagSet,
      probe: launched.probe, renderer: launched.probe.renderer });
    assert(launched.probe.ok && launched.probe.kind === 'webgl2' && /Metal/.test(launched.probe.renderer)
      && !/swiftshader|llvmpipe|software/i.test(launched.probe.renderer), 'Actual Metal WebGL2 required; no software fallback');
    await launched.context.close(); // Retire the helper probe before the recorded context.
  } else browser = await webkit.launch({ headless: true });
  report.browser.version = browser.version();
  context = await browser.newContext({ viewport: { width: 1440, height: 900 },
    recordVideo: { dir: out, size: { width: 1440, height: 900 } } });
  page = await context.newPage();
  const started = performance.now();
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('response', response => {
    if (response.url().endsWith('.glb')) responses.push(witnessGlbResponse(response, witnesses)
      .then(row => report.loaded.push(row)).catch(error => report.errors.push(error.message)));
  });
  await page.goto(development.server.resolvedUrls.local[0] + '?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120&track=b1-first-ride');
  await page.waitForFunction(() => globalThis.window.__rockhop?.ready && globalThis.window.__rockhop.info().trackId === 'b1-first-ride', null, { timeout: 120000 });
  report.browser.renderer = await page.evaluate(() => {
    const gl = globalThis.window.__render.debug.renderer.getContext(), extension = gl.getExtension('WEBGL_debug_renderer_info');
    return String(gl.getParameter(extension ? extension.UNMASKED_RENDERER_WEBGL : gl.RENDERER));
  });
  if (backend === 'metal') assert(/Metal/.test(report.browser.renderer)
    && !/swiftshader|llvmpipe|software/i.test(report.browser.renderer), 'Actual game renderer must use Metal');
  report.camera = await page.evaluate(async ({ bike, cameraYaw }) => {
    const t = globalThis.window.__rockhop, r = globalThis.window.__render;
    // Main already loads this registered track; avoid warming and discarding flat-test.
    if (bike !== 'rookie') { t.setBike(bike); await t.loadTrack('b1-first-ride', 138717428); }
    await r.whenReady();
    const info = t.info();
    if (info.trackId !== 'b1-first-ride' || info.seed !== 138717428 || info.bike !== bike)
      throw new Error('Initial track/seed/physics bike differs from measured preflight'); t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
    const candidate = r.debug.rider.debug.candidate;
    const id = Array.isArray(candidate.roles.pelvis) ? candidate.roles.pelvis[0] : candidate.roles.pelvis;
    const pelvis = r.debug.rider.binding.byId.get(id);
    const p = pelvis.getWorldPosition(new r.debug.THREE.Vector3());
    globalThis.window.__gameplayLeanCamera = { mode: 'orbit', x: p.x, y: p.y + .12, yaw: cameraYaw, pitch: .08,
      dist: 4.6, screenX: .5, screenY: .5 };
    r.setCameraOverride(globalThis.window.__gameplayLeanCamera);
    t.render(true);
    return structuredClone(globalThis.window.__gameplayLeanCamera);
  }, { bike, cameraYaw });
  report.readyOffsetSeconds = (performance.now() - started) / 1000;
  await page.evaluate(installGarageCaptureMeter);
  report.played = await page.evaluate(async phases => {
    const t = globalThis.window.__rockhop, rider = globalThis.window.__render.debug.rider;
    const inputs = phases.flatMap(phase => Array.from({ length: phase.ticks }, () =>
      ({ throttle: 0, brake: 0, lean: phase.lean, hop: false, restart: false })));
    const endpoints = new Map(); let end = 0;
    for (const phase of phases) { end += phase.ticks; endpoints.set(end, phase.name); }
    const samples = [], faults = [], motionSamples = [], started = performance.now(); let tick = 0, maximumCatchupTicks = 0;
    const label = globalThis.document.createElement('div');
    label.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#000d;color:white;padding:8px 14px;font:18px monospace';
    globalThis.document.body.append(label);
    const joints = [...rider.binding.byId], originalUpdate = rider.update;
    const rootBone = joints.find(([, bone]) => !bone.parent?.isBone)[1];
    let latestFrame;
    rider.update = function (frame) {
      const result = originalUpdate.call(this, frame);
      latestFrame = { bikeX: frame.bikeX, bikeY: frame.bikeY, bikeAngle: frame.bikeAngle,
        tSim: frame.tSim, tick: frame.tick, crashed: frame.crashed, faulted: frame.faulted,
        ragdoll: structuredClone(frame.ragdoll), rider: structuredClone(frame.rider), riderBody: structuredClone(frame.riderBody) };
      return result;
    };
    const motionSnapshot = () => {
      const phase = tick <= 240 ? 'neutral' : tick <= 600 ? 'forward' : tick <= 960 ? 'backward' : 'neutral-return';
      motionSamples.push({ tick, timeSeconds: tick / 120, phase,
        input: inputs[Math.max(0, tick - 1)], frame: structuredClone(latestFrame),
        debug: { physicalPose: rider.debug.physicalPose, stageClip: rider.debug.stageClip,
          allBoneFinite: rider.debug.allBoneFinite, gripErr: structuredClone(rider.debug.gripErr),
          soleErr: structuredClone(rider.debug.soleErr), anthropometry: structuredClone(rider.debug.anthropometry), stance: structuredClone(rider.debug.stance) },
        bikeFrameWorld: rider.bike.frame.matrixWorld.toArray(), skeletonWorld: rootBone.parent.matrixWorld.toArray(),
        joints: joints.map(([id, bone]) => ({ id, name: bone.name, position: bone.position.toArray(),
          quaternion: bone.quaternion.toArray(), scale: bone.scale.toArray(), worldMatrix: bone.matrixWorld.toArray() })) });
    };
    const snapshot = name => ({ name, tick, state: structuredClone(t.getState()),
      hash: t.hashState(), debug: structuredClone(rider.debug),
      joints: [...rider.binding.byId].map(([id, bone]) => ({ id, position: bone.position.toArray(),
        quaternion: bone.quaternion.toArray(), scale: bone.scale.toArray() })) });
    // Force a draw of the existing state so the observer has an actual initial frame.
    globalThis.window.__render.setCameraOverride(globalThis.window.__gameplayLeanCamera);
    t.render(true); t.render(true); motionSnapshot(); samples.push(snapshot('initial'));
    try { await new Promise((resolve, reject) => {
      function frame() {
        try {
          label.textContent = tick < 240 ? 'Actual gameplay: neutral' : tick < 600 ? 'Actual gameplay: lean forward' : tick < 960 ? 'Actual gameplay: lean backward' : 'Actual gameplay: return to neutral';
          const wanted = Math.min(inputs.length, Math.floor((performance.now() - started) * .12));
          maximumCatchupTicks = Math.max(maximumCatchupTicks, wanted - tick);
          while (tick < wanted) {
            t.setInput(inputs[tick]); t.step(1); tick++;
            const state = t.getState();
            if (state.faulted && faults.length < 16) faults.push({ tick, faulted: state.faulted });
            if (tick % 5 === 0) { t.render(true); t.render(true); motionSnapshot(); }
            if (endpoints.has(tick)) samples.push(snapshot(endpoints.get(tick)));
          }
          t.render(true);
          if (tick === inputs.length) resolve(); else globalThis.requestAnimationFrame(frame);
        } catch (error) { reject(error); }
      }
      globalThis.requestAnimationFrame(frame);
    }); } finally { rider.update = originalUpdate; }
    return { samples, faults, motionSamples,
      jointOrder: joints.map(([id, bone]) => ({ id, loadedName: bone.name })),
      localTRSConvention: 'local translationXYZ / quaternionXYZW / scaleXYZ; original native75 hierarchy; bike matrixWorld is column-major Three.js',
      ticks: tick, maximumCatchupTicks,
      wallSeconds: (performance.now() - started) / 1000, finalHash: t.hashState(), inputs };
  }, phases);
  report.performance = await page.evaluate(() => globalThis.window.__garageCaptureMeter.stop());
  await page.screenshot({ path: path.join(out, 'gameplay-return.png') });
  await Promise.all(responses);
  assert.deepEqual(report.errors, []);
  assert(report.loaded.some(row => row.sha256 === contract.glbSHA256), 'Actual selected dressed source served');
  assert.equal(report.played.ticks, 1200);
  assert(report.played.samples.every(row => row.debug.physicalPose && row.debug.stageClip === null
    && row.debug.allBoneFinite), 'Every endpoint uses actual simulated rider state and finite native75');
  assert.equal(report.played.motionSamples.length, 241);
  assert(report.played.motionSamples.every((row, i) => row.tick === i * 5 && row.debug.physicalPose
    && row.debug.stageClip === null && row.joints.length === 75
    && row.joints.every(j => [...j.position, ...j.quaternion, ...j.scale, ...j.worldMatrix].every(Number.isFinite))),
    'All exact24Hz physics samples retain physical driver and finite original75 transforms');
  report.performanceLimit = 'Additional24Hz exact-state witness draws are included; this capture is not a normal-player FPS benchmark.';
  assert.deepEqual(report.played.faults, [], 'Held lean sequence stays live; failures remain evidence');
} catch (error) { report.failure = error.stack; process.exitCode = 1; }
finally {
  const cleanup = async (name, close) => {
    try { await close(); } catch (error) {
      report.errors.push(`${name}: ${error.message}`); report.failure ??= error.stack; process.exitCode = 1;
    }
  };
  const video = page?.video();
  await cleanup('context close', () => context?.close());
  if (video) await cleanup('video save', () => video.saveAs(path.join(out, 'gameplay-played.webm')));
  await cleanup('browser close', () => launched ? launched.close() : browser?.close());
  await cleanup('server close', () => development.server.close());
  report.recipeSHA256 = crypto.createHash('sha256').update(await fs.readFile(new URL(import.meta.url))).digest('hex');
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, ticks: report.played?.ticks, failure: report.failure }));
}
