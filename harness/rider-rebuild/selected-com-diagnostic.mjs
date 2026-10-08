/** Read-only XYZ COM comparison; run under the parent's serialized CPU guard. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../src/render/frame.ts';
import { BIKE_GEOMETRY_V2 } from '../../src/render/hero/assetFrame.ts';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from './private-rider.mjs';
import { measureAnthropometricCOM } from './anthropometric-inverse.mjs';

const arg = (name, fallback) => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const base = 'harness/out/rider-rebuild/selected-complete-engine01/engine05/';
const source = arg('source', base + 'rider.glb'), contract = arg('contract', base + 'rider-contract.json');
const calibration = arg('calibration', 'assets/blender/rider-rebuild/selected-complete-engine01/engine05-contact-calibration02.json');
const baselineBlob = '20bd22b34bc1334c339dde34c98b77c2d56b2e49';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const metadata = JSON.parse(fs.readFileSync(contract)), overlay = JSON.parse(fs.readFileSync(calibration));
metadata.sourceSHA256 = sha(fs.readFileSync(source));
assert.equal(metadata.sourceSHA256, overlay.sourceSHA256);
Object.assign(metadata.driver, overlay.driver, { nearSimilarityTolerance: 1e-4 });
// Load the immutable pre-refinement adapter with its original imports resolved in place.
const oldSource = execFileSync('git', ['show', baselineBlob], { encoding: 'utf8' });
const adapterURL = new URL('./private-rider.mjs', import.meta.url);
const resolvable = oldSource.replace(/from (['"])([^'"]+)\1/g, (_, quote, name) =>
  `from ${JSON.stringify(name.startsWith('.') ? new URL(name, adapterURL).href : import.meta.resolve(name))}`);
const baseline = await import('data:text/javascript;base64,' + Buffer.from(resolvable).toString('base64'));
const loaded = await loadRigAt(pathToFileURL(source), true);
const instance = factory => {
  const Rider = factory(metadata), rider = new Rider(loaded, { complete() {} }), frame = new THREE.Group();
  frame.position.set(BIKE_GEOMETRY_V2.chassisToAxle.x, BIKE_GEOMETRY_V2.chassisToAxle.y, 0);
  frame.updateWorldMatrix(true, true); rider.attach({ frame }); return rider;
};
const riders = { baseline: instance(baseline.createPrivateRiderClass), coupled: instance(createPrivateRiderClass) };
const result = { accepted: false, sourceSHA256: metadata.sourceSHA256, contractSHA256: sha(fs.readFileSync(contract)),
  calibrationSHA256: sha(fs.readFileSync(calibration)), baselineBlob, baselineSHA256: sha(oldSource),
  currentAdapterSHA256: sha(fs.readFileSync(adapterURL)), rows: [],
  limits: 'Exact existing test targets only; XYZ diagnosis, no range/contact/art acceptance or pose correction.' };
for (let index = 0; index <= 40; index++) {
  const lean = -1 + index / 20, row = { index, lean };
  for (const [name, rider] of Object.entries(riders)) {
    const p = riderPoseAtLean(lean, makeRiderRigPose()), f = new FrameBuilder().frame;
    f.riderBody.present = true;
    f.riderBody.relX = p.com.x + BIKE_GEOMETRY_V2.chassisToAxle.x;
    f.riderBody.relY = p.com.y + BIKE_GEOMETRY_V2.chassisToAxle.y;
    f.riderBody.relAngle = p.torsoAngle - RIDER_TORSO_REST;
    f.rider.lean = lean; f.tSim = 3; f.dt = 1 / 60;
    const before = JSON.stringify(f); rider.update(f); assert.equal(JSON.stringify(f), before);
    const target = new THREE.Vector3().fromArray(rider.debug.anthropometry.requestedCOM);
    const measured = rider.toBike(measureAnthropometricCOM(rider, rider.anthropometry));
    row[name] = { measuredCOM: measured.toArray(), targetCOM: target.toArray(),
      residualXYZ: measured.clone().sub(target).toArray(), distanceM: measured.distanceTo(target),
      inverseXYResidualM: rider.debug.comResidual, spineFlexRadians: rider.debug.anthropometry.spineFlexRadians,
      gripErrM: [...rider.debug.gripErr], soleErrM: [...rider.debug.soleErr],
      candidates: structuredClone(rider.debug.anthropometry.candidates) };
  }
  result.rows.push(row);
}
result.summary = Object.fromEntries(Object.keys(riders).map(name => [name, {
  firstFailure: result.rows.find(row => row[name].distanceM >= 1e-5)?.index ?? null,
  failedIndices: result.rows.filter(row => row[name].distanceM >= 1e-5).map(row => row.index),
  maximumDistanceM: Math.max(...result.rows.map(row => row[name].distanceM)),
  maximumAbsZM: Math.max(...result.rows.map(row => Math.abs(row[name].residualXYZ[2]))),
}]));
const output = arg('out');
if (output) { assert(!fs.existsSync(output), 'Fresh diagnostic output required'); fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n'); }
console.log(JSON.stringify({ summary: result.summary, firstCoupledFailure: result.rows.find(row => row.coupled.distanceM >= 1e-5) ?? null }));
