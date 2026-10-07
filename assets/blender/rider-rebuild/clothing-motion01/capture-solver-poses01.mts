/** Numerical pose intake only: actual solver and frozen75 carrier, no browser/render. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { BIKE_GEOMETRY_V2 } from '../../../../src/render/hero/assetFrame.ts';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';
import { resetHumanoidPose } from '../../../../harness/rider-rebuild/new-humanoid-contract.mjs';

const root = process.cwd(), out = path.resolve(process.argv[2]);
assert.ok(!fs.existsSync(out));
const source = path.join(root, 'harness/out/rider-rebuild/construction01/combined04/rider.glb');
const sourceSHA = '58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc';
const metadataPath = path.join(path.dirname(source), 'rider-contract.json');
const calibrationPath = path.join(root, 'docs/evidence/rider-rebuild/runtime02/combined04-adaptive20-pose.json');
const sha = (p: string) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
assert.equal(sha(source), sourceSHA);
const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
const calibration = JSON.parse(fs.readFileSync(calibrationPath, 'utf8'));
assert.equal(sha(calibrationPath), '0b85504e221e33e63505a0cf18a7231ed7143f2730b4402a50994c40c4869cbc');
assert.equal(calibration.sourceSHA256, sourceSHA);
metadata.sourceSHA256 = sourceSHA;
metadata.driver.nearSimilarityTolerance = 1e-4;
delete metadata.driver.spineFlexTable;
Object.assign(metadata.driver, calibration.driver);
const gltf = await loadRigAt(pathToFileURL(source), true);
const Rider = createPrivateRiderClass(metadata), rider = new Rider(gltf, { complete() {} });
const bike = new THREE.Group();
bike.position.set(BIKE_GEOMETRY_V2.chassisToAxle.x, BIKE_GEOMETRY_V2.chassisToAxle.y, 0);
bike.updateWorldMatrix(true, true); rider.attach({ frame: bike });
assert.equal(rider.binding.byId.size, 75);
const nativeToGltf = new THREE.Matrix4().set(1,0,0,0, 0,0,1,0, 0,-1,0,0, 0,0,0,1);
const gltfToNative = nativeToGltf.clone().invert();
const authored = (bone: THREE.Bone) => rider.scene.matrixWorld.clone().invert().multiply(bone.matrixWorld);
resetHumanoidPose(rider.binding);
const rest = new Map([...rider.binding.byId].map(([id, bone]) => [id, authored(bone)]));
const restLocal = JSON.stringify([...rider.binding.byId].map(([id, bone]) => [id, bone.position.toArray(), bone.quaternion.toArray(), bone.scale.toArray()]));
const rows = [];
for (const lean of [-1, -.5, 0, .5, 1]) {
  const p = riderPoseAtLean(lean, makeRiderRigPose()), f = new FrameBuilder().frame;
  f.riderBody.present = true;
  f.riderBody.relX = p.com.x + bike.position.x; f.riderBody.relY = p.com.y + bike.position.y;
  f.riderBody.relAngle = p.torsoAngle - RIDER_TORSO_REST;
  f.rider.lean = lean; f.dt = 1/60; f.tSim = 3;
  const before = JSON.stringify(f); rider.update(f); assert.equal(JSON.stringify(f), before);
  assert.ok(rider.debug.allBoneFinite && rider.debug.physicalPose);
  const deltas = Object.fromEntries([...rider.binding.byId].map(([id, bone]) => {
    const delta = gltfToNative.clone().multiply(authored(bone)).multiply(rest.get(id)!.clone().invert()).multiply(nativeToGltf);
    assert.ok(delta.elements.every(Number.isFinite));
    return [id, delta.toArray()];
  }));
  const angles = Object.fromEntries(['L','R'].flatMap(side => ['shoulder','upper_arm','forearm'].map(stem => {
    const id = 'DEF-' + stem + '.' + side, bone = rider.binding.byId.get(id)!;
    const saved = rider.binding.rests.get(id)!;
    return [id, bone.quaternion.angleTo(new THREE.Quaternion().fromArray(saved.rotationXYZW))];
  })));
  rows.push({ name: lean === 0 ? 'seated' : lean < 0 ? `back${-lean}` : `forward${lean}`, lean,
    boneDeltaNativeColumnMajor: deltas, localJointRotationFromRestRadians: angles,
    gripM: [...rider.debug.gripErr], soleM: [...rider.debug.soleErr],
    COMResidualM: rider.debug.comResidual, spineFlexRadians: rider.debug.anthropometry.spineFlexRadians });
}
resetHumanoidPose(rider.binding);
assert.equal(JSON.stringify([...rider.binding.byId].map(([id, bone]) => [id, bone.position.toArray(), bone.quaternion.toArray(), bone.scale.toArray()])), restLocal);
assert.equal(sha(source), sourceSHA);
const report = { accepted: false, numericalOnly: true, source: { path: source, sha256: sourceSHA },
  metadata: { path: metadataPath, sha256: sha(metadataPath) }, calibration: { path: calibrationPath, sha256: sha(calibrationPath) },
  recipeSHA256: sha(new URL(import.meta.url).pathname), runtimeSHA256: sha(path.join(root,'harness/rider-rebuild/private-rider.mjs')),
  nativeRest: metadata.nativeRest, sourceAndRestPreserved: true, rows,
  limits: ['Five generic actual solver ride states; no browser, appearance presentation or recorded-input replay.',
    'Frozen source carrier supplies actual joint motion; final complete source/calibrated outfit remains separate.',
    'These matrices drive array-only native source measurements; no native pose or source file is rewritten.'] };
fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify({ poses: rows.length, jointCount: 75, maxGripM: Math.max(...rows.flatMap(r=>r.gripM)), maxSoleM: Math.max(...rows.flatMap(r=>r.soleM)), sourceAndRestPreserved: true }));
rider.dispose();
