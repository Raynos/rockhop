/** Continuous headless film: actual held inputs and simulated rider state. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { webkit } from 'playwright';
import { createPrivateDevReview } from './private-dev-review.mjs';
import { witnessGlbResponse } from './glb-response-witness.mjs';
import { installGarageCaptureMeter } from './garage-capture-meter.mjs';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const source = arg('source'), contractPath = arg('contract'), out = path.resolve(arg('out') ?? '');
assert(source && contractPath && arg('out'), 'Pass --source, --contract and fresh --out');
const bike = arg('bike') ?? 'rookie'; assert(['rookie', 'pro'].includes(bike));
await fs.mkdir(out, { recursive: false });
const contract = JSON.parse(await fs.readFile(contractPath));
const development = await createPrivateDevReview({ source, contractPath, allowFailedDiagnostic: true });
assert.equal(development.receipt.diagnosticKind, 'actual-gameplay-lean');
const phases = [{ name: 'neutral', ticks: 240, lean: 0 }, { name: 'forward', ticks: 360, lean: 1 },
  { name: 'backward', ticks: 360, lean: -1 }, { name: 'neutral-return', ticks: 240, lean: 0 }];
const report = { accepted: false, status: 'UNACCEPTED_ACTUAL_GAMEPLAY_LEAN', bike,
  source: development.receipt, phases, errors: [], loaded: [],
  method: 'Continuous real-time fixed120Hz game inputs; simulated COM/torso drives selected rider. No pose, joint, animation-clock or physics-state injection.' };
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 },
  recordVideo: { dir: out, size: { width: 1440, height: 900 } } });
const page = await context.newPage(), responses = [], witnesses = new Map();
const started = performance.now();
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', response => {
  if (response.url().endsWith('.glb')) responses.push(witnessGlbResponse(response, witnesses)
    .then(row => report.loaded.push(row)).catch(error => report.errors.push(error.message)));
});
try {
  await page.goto(development.server.resolvedUrls.local[0] + '?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');
  await page.waitForFunction(() => window.__rockhop?.ready, null, { timeout: 120000 });
  await page.evaluate(async bike => {
    const t = window.__rockhop, r = window.__render;
    t.setBike(bike); await r.whenReady(); await t.loadTrack('b1-first-ride', 138717428);
    await r.whenReady(); t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
    const candidate = r.debug.rider.debug.candidate;
    const id = Array.isArray(candidate.roles.pelvis) ? candidate.roles.pelvis[0] : candidate.roles.pelvis;
    const pelvis = r.debug.rider.binding.byId.get(id);
    const p = pelvis.getWorldPosition(new r.debug.THREE.Vector3());
    r.setCameraOverride({ mode: 'orbit', x: p.x, y: p.y + .12, yaw: 1.4, pitch: .08,
      dist: 4.6, screenX: .5, screenY: .5 });
    t.render(true);
  }, bike);
  report.readyOffsetSeconds = (performance.now() - started) / 1000;
  await page.evaluate(installGarageCaptureMeter);
  report.played = await page.evaluate(async phases => {
    const t = window.__rockhop, rider = window.__render.debug.rider;
    const inputs = phases.flatMap(phase => Array.from({ length: phase.ticks }, () =>
      ({ throttle: 0, brake: 1, lean: phase.lean, hop: false, restart: false })));
    const endpoints = new Map(); let end = 0;
    for (const phase of phases) { end += phase.ticks; endpoints.set(end, phase.name); }
    const samples = [], faults = [], started = performance.now(); let tick = 0, maximumCatchupTicks = 0;
    const snapshot = name => ({ name, tick, state: structuredClone(t.getState()),
      hash: t.hashState(), debug: structuredClone(rider.debug),
      joints: [...rider.binding.byId].map(([id, bone]) => ({ id, position: bone.position.toArray(),
        quaternion: bone.quaternion.toArray(), scale: bone.scale.toArray() })) });
    samples.push(snapshot('initial'));
    await new Promise((resolve, reject) => {
      function frame() {
        try {
          const wanted = Math.min(inputs.length, Math.floor((performance.now() - started) * .12));
          maximumCatchupTicks = Math.max(maximumCatchupTicks, wanted - tick);
          while (tick < wanted) {
            t.setInput(inputs[tick]); t.step(1); tick++;
            const state = t.getState();
            if (state.faulted && faults.length < 16) faults.push({ tick, faulted: state.faulted });
            if (endpoints.has(tick)) { t.render(true); samples.push(snapshot(endpoints.get(tick))); }
          }
          t.render(true);
          if (tick === inputs.length) resolve(); else requestAnimationFrame(frame);
        } catch (error) { reject(error); }
      }
      requestAnimationFrame(frame);
    });
    return { samples, faults, ticks: tick, maximumCatchupTicks,
      wallSeconds: (performance.now() - started) / 1000, finalHash: t.hashState(), inputs };
  }, phases);
  report.performance = await page.evaluate(() => window.__garageCaptureMeter.stop());
  await page.screenshot({ path: path.join(out, 'gameplay-return.png') });
  await Promise.all(responses);
  assert.deepEqual(report.errors, []);
  assert(report.loaded.some(row => row.sha256 === contract.glbSHA256), 'Actual selected dressed source served');
  assert.equal(report.played.ticks, 1200);
  assert(report.played.samples.every(row => row.debug.physicalPose && row.debug.stageClip === null
    && row.debug.allBoneFinite), 'Every endpoint uses actual simulated rider state and finite native75');
  assert.deepEqual(report.played.faults, [], 'Held lean sequence stays live; failures remain evidence');
} catch (error) { report.failure = error.stack; process.exitCode = 1; }
finally {
  const video = page.video();
  await context.close(); if (video) await video.saveAs(path.join(out, 'gameplay-played.webm'));
  await browser.close(); await development.server.close();
  report.recipeSHA256 = crypto.createHash('sha256').update(await fs.readFile(new URL(import.meta.url))).digest('hex');
  await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, ticks: report.played?.ticks, failure: report.failure }));
}
