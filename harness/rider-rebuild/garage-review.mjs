/** Silent, headless review of the actual Garage with UI and authored motion. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { witnessGlbResponse } from './glb-response-witness.mjs';
import { inspectPreparedRiderMaterials, inspectRiderMaterialInventory } from './inspect-prepared-materials.mjs';
import { inspectActualCuffFragment } from './inspect-posed-cuffs.mjs';
import { identifyActualWristFragment } from './identify-wrist-fragment.mjs';

const arg = (name, fallback = '') => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
const requestedClip = arg('clip');
const requestedBike = arg('bike', 'rookie');
assert(['rookie', 'pro'].includes(requestedBike), '--bike must be rookie or pro');
assert(arg('contract'), 'Pass the exact selected rider contract');
const contractPath = path.resolve(arg('contract')), contractBytes = fs.readFileSync(contractPath);
const contract = JSON.parse(contractBytes), expected = contract.specification.meshNames;
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json')));
const bikeAsset = catalog.models.find(row => row.logical === `models/bike-${requestedBike}.glb`);
assert(bikeAsset, 'Selected authored bike catalogue pin required');
const required = ['RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'];
for (const name of required) assert(Object.values(expected).includes(name), `Missing selected dressed object ${name}`);
assert(!fs.existsSync(out), 'Use a fresh output directory');
fs.mkdirSync(out, { recursive: true });
const report = { build, requestedClip: requestedClip || null, requestedBike, bikeAsset, contract: { path: contractPath, sha256: crypto.createHash('sha256').update(contractBytes).digest('hex'), expectedObjects: expected }, recipeSHA256: crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'), errors: [], loaded: [], snapshots: [], audio: 'silent webdriver; audio=0', review: 'Actual Garage UI, selected native clip or riding IK with breathing, pointer-driven orbit; no pose injection' };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, recordVideo: { dir: out, size: { width: 1440, height: 900 } } });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1');
  // Isolated review profile owns both bikes; selection still uses actual UI.
  localStorage.setItem('rockhop.economy.v1', JSON.stringify({
    version: 1, wallet: 0, medals: {}, proOwned: true, equipped: 'rookie',
  }));
});
const page = await context.newPage(), responses = [], witnesses = new Map();
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', response => {
  if (response.url().endsWith('.glb')) responses.push(witnessGlbResponse(response, witnesses)
    .then(row => report.loaded.push(row)).catch(error => report.errors.push(error.message)));
});
try {
  const query = new URLSearchParams({ audio: '0', sw: '0' });
  if (requestedClip) query.set('riderClip', requestedClip);
  await page.goto(server.resolvedUrls.local[0] + '?' + query);
  await page.locator('.menu-screen.live .menu-item[data-id=garage]').click({ timeout: 120000 });
  await page.waitForSelector('.garage-screen.live');
  await page.locator(`button[data-bike=${requestedBike}]`).click();
  await page.locator('button[data-outfit=street-mustard]').click();
  await page.evaluate(async () => window.__render.whenReady());
  await page.locator(`button[data-bike=${requestedBike}][aria-pressed=true]`).waitFor();
  await page.waitForTimeout(1500);
  const inspect = async name => {
    // Five cheap read-only witnesses only; no per-frame pose readback or clock injection.
    const diagnostic = await page.evaluate(() => {
      const renderer = window.__render, rider = renderer.debug.rider;
      const boneLocalTRS = [...rider.binding.byId].map(([id, bone]) => ({
        id, name: bone.name, parent: bone.parent?.isBone ? bone.parent.name : null,
        translation: bone.position.toArray(), rotationXYZW: bone.quaternion.toArray(),
        scale: bone.scale.toArray(),
      }));
      return { debug: structuredClone(rider.debug), render: renderer.debugInfo(),
        attachedToBikeFrame: rider.placement.parent === rider.bike?.frame,
        placementBike: rider.placement.position.toArray(),
        stageTime: renderer.stageTime, riderStageTime: rider.stageTime,
        clipDuration: rider.clip?.duration ?? null,
        clipTime: rider.clip ? ((rider.stageTime % rider.clip.duration) + rider.clip.duration) % rider.clip.duration : null,
        boneLocalTRS };
    });
    assert.equal(diagnostic.boneLocalTRS.length, 75, 'Capture every actual native75 local TRS');
    assert.deepEqual(diagnostic.boneLocalTRS.map(row => row.id).sort(), Object.keys(contract.specification.jointNames).sort(), 'Exact declared joint identities');
    for (const bone of diagnostic.boneLocalTRS) {
      for (const [key, width] of [['translation', 3], ['rotationXYZW', 4], ['scale', 3]]) {
        assert.equal(bone[key].length, width); assert(bone[key].every(Number.isFinite), `Finite actual ${bone.id} ${key}`);
      }
    }
    if (requestedClip) {
      assert.equal(diagnostic.debug.stageClip, requestedClip, 'Exact requested native action is playing');
      assert(diagnostic.debug.clips.includes(requestedClip), 'Requested clip exists in actual selected source');
      assert(Number.isFinite(diagnostic.clipDuration) && diagnostic.clipDuration > 0, 'Actual clip has finite positive duration');
      assert(Number.isFinite(diagnostic.riderStageTime), 'Actual rider stage clock is finite');
      const authored = contract.genericActions?.[requestedClip];
      if (authored) assert(Math.abs(diagnostic.clipDuration - authored.durationSeconds) < 1e-6, 'Actual clip duration matches source-bound action');
    } else {
      assert.equal(diagnostic.debug.stageClip, 'Riding IK/breathing', 'Default Garage uses the riding solver');
      assert(diagnostic.attachedToBikeFrame, 'Selected rider attached to actual bike frame');
      assert.deepEqual(diagnostic.placementBike, [0, 0, 0], 'No isolated animation offset');
      assert(diagnostic.debug.handOnGrip.every(Boolean), 'Both hands reach actual grips');
      assert(diagnostic.debug.footOnPeg.every(Boolean), 'Both soles reach selected peg targets');
      assert.equal(diagnostic.debug.stance.pose, 'seated', 'Neutral seated Garage stance');
    }
    report.snapshots.push({ name, ...diagnostic });
    if (name === 'garage-front' && arg('material-probe')) {
      report.materialProbe = await page.evaluate(inspectPreparedRiderMaterials);
      report.materialProbeRecipeSHA256 = crypto.createHash('sha256')
        .update(fs.readFileSync(new URL('./inspect-prepared-materials.mjs', import.meta.url))).digest('hex');
    }
    if (name === 'garage-front' && arg('cuff-probe')) {
      report.posedCuffProbe = await page.evaluate(inspectActualCuffFragment);
      report.posedCuffProbeRecipeSHA256 = crypto.createHash('sha256')
        .update(fs.readFileSync(new URL('./inspect-posed-cuffs.mjs', import.meta.url))).digest('hex');
      report.probeLimit = 'Read-only synchronous surface inspection stalls this diagnostic capture; use separate uninterrupted films for moving art.';
    }
    if (name === 'garage-front' && arg('identity-probe')) {
      report.wristFragmentIdentity = await page.evaluate(identifyActualWristFragment);
      report.wristFragmentIdentityRecipeSHA256 = crypto.createHash('sha256')
        .update(fs.readFileSync(new URL('./identify-wrist-fragment.mjs', import.meta.url))).digest('hex');
      report.probeLimit = 'Synchronous read-only scene identity; separate uninterrupted films judge moving art.';
    }
    await page.screenshot({ path: path.join(out, name + '.png') });
  };
  report.materialInventory = await page.evaluate(inspectRiderMaterialInventory);
  await inspect('garage-front');
  const box = await page.locator('.garage-stage').boundingBox();
  assert(box);
  const center = { x: box.x + box.width * .5, y: box.y + box.height * .45 };
  for (let quarter = 1; quarter <= 4; quarter++) {
    await page.mouse.move(center.x, center.y); await page.mouse.down();
    await page.mouse.move(center.x - 160, center.y, { steps: 40 });
    await page.waitForTimeout(100); await page.mouse.up();
    await page.waitForTimeout(1700);
    if (quarter === 4 && requestedClip) {
      const first = report.snapshots[0], target = first.riderStageTime + first.clipDuration;
      const before = await page.evaluate(() => window.__render.debug.rider.stageTime);
      report.clipCoverage = { name: requestedClip, durationSeconds: first.clipDuration,
        firstRiderStageTime: first.riderStageTime, beforeFinalWaitStageTime: before,
        additionalWaitRequired: before < target };
      if (before < target) {
        // Clock-only polling extends the uninterrupted film if dense rendering
        // advanced less than one complete cycle during the existing orbit.
        await page.waitForFunction(targetTime => window.__render.debug.rider.stageTime >= targetTime,
          target, { polling: 250, timeout: 60000 });
      }
    }
    await inspect('garage-orbit-' + quarter);
  }
  await Promise.all(responses);
  assert.deepEqual(report.errors, []);
  assert(report.loaded.some(row => row.sha256 === contract.glbSHA256), 'Exact selected GLB served by actual build');
  assert(report.loaded.some(row => row.sha256 === bikeAsset.sha256), 'Exact selected bike GLB served by actual build');
  for (const row of report.snapshots) {
    assert.deepEqual(row.debug.candidate?.authorMeshRoles, expected, 'Exact selected source object inventory loaded');
    const visible = new Set(row.debug.candidate.visibleMeshes.filter(mesh => mesh.skinned && mesh.triangles > 0).map(mesh => mesh.name));
    for (const mesh of row.debug.candidate.meshRoles) assert(visible.has(mesh.name), `Selected dressed primitive is visible and skinned: ${mesh.name}`);
    assert(row.debug.candidate.meshRoles.length >= Object.keys(expected).length, 'Every declared selected object has a dressed material primitive');
  }
  assert(report.snapshots.at(-1).stageTime > report.snapshots[0].stageTime, 'Actual Garage motion clock advances');
  if (requestedClip) {
    const first = report.snapshots[0], last = report.snapshots.at(-1);
    report.clipCoverage.lastRiderStageTime = last.riderStageTime;
    report.clipCoverage.continuousRiderSeconds = last.riderStageTime - first.riderStageTime;
    assert(report.clipCoverage.continuousRiderSeconds >= first.clipDuration, 'Continuous Garage film covers at least one whole native action cycle');
    assert(report.snapshots.every(row => row.clipDuration === first.clipDuration), 'Actual clip duration stays unchanged through orbit');
  }
} catch (error) { report.failure = error.stack; process.exitCode = 1; }
finally {
  const video = page.video(); await context.close(); await browser.close();
  const videoPath = await video.path();
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', videoPath, '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(out, 'garage-played.mp4')], { encoding: 'utf8' });
  report.encoding = { exitCode: encoded.status, stderr: encoded.stderr };
  await new Promise(resolve => server.httpServer.close(resolve));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, snapshots: report.snapshots.length, errors: report.errors, failure: report.failure }));
}
