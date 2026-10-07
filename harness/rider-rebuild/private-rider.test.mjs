import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../src/render/frame.ts';
import { BIKE_GEOMETRY_V2 } from '../../src/render/hero/assetFrame.ts';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from './private-rider.mjs';
import { privateEnginePlugin } from './private-engine-plugin.mjs';
import { measureAnthropometricCOM } from './anthropometric-inverse.mjs';
import { resetHumanoidPose } from './new-humanoid-contract.mjs';

const source = path.resolve(process.env.RIDER_REBUILD_SOURCE ?? 'harness/out/rider-rebuild/construction01/combined01/rider.glb');
const metadataPath = path.resolve(process.env.RIDER_REBUILD_CONTRACT ?? 'harness/out/rider-rebuild/construction01/combined01/rider-contract.json');
const available = fs.existsSync(source) && fs.existsSync(metadataPath);
const skip = !available ? 'External unaccepted assembly is absent' : false;
const metadata = available ? JSON.parse(fs.readFileSync(metadataPath)) : {};
if (available) metadata.sourceSHA256 = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
if (available) metadata.driver.nearSimilarityTolerance = 1e-4; // Explicit measured 16.5ppm native-rest residual, source TRS retained.
let loaded;
async function instance() {
  loaded ??= await loadRigAt(pathToFileURL(source), true); // CPU images omitted; no disk modification/material acceptance.
  const Rider = createPrivateRiderClass(metadata), rider = new Rider(loaded, { complete() {} });
  const frame = new THREE.Group(); frame.name = 'actual-bike-frame';
  frame.position.set(BIKE_GEOMETRY_V2.chassisToAxle.x, BIKE_GEOMETRY_V2.chassisToAxle.y, 0);
  frame.updateWorldMatrix(true, true);
  rider.attach({ frame });
  return { rider, frame };
}
const poseFrame = lean => {
  const p = riderPoseAtLean(lean, makeRiderRigPose()), f = new FrameBuilder().frame;
  f.riderBody.present = true;
  f.riderBody.relX = p.com.x + BIKE_GEOMETRY_V2.chassisToAxle.x;
  f.riderBody.relY = p.com.y + BIKE_GEOMETRY_V2.chassisToAxle.y;
  f.riderBody.relAngle = p.torsoAngle - RIDER_TORSO_REST;
  f.rider.lean = lean; f.tSim = 3; f.dt = 1 / 60;
  return f;
};
const snapshot = rider => JSON.stringify([...rider.binding.byId].map(([id, bone]) => [id, bone.position.toArray(), bone.quaternion.toArray(), bone.scale.toArray(), bone.matrixWorld.toArray()]));

test('private plugin replaces only rider adapter and scoped part merge', () => {
  const plugin = privateEnginePlugin({ driver: { assetToBikeQuaternionXYZW: [0, 0, 0, 1] } });
  assert.equal(plugin.transform('untouched', '/src/main.ts'), null);
  assert.match(plugin.transform('legacy', '/src/render/hero/gltfRider.ts').code, /createPrivateRiderClass/);
  assert.ok(!plugin.transform('  mergeSkinnedByMaterial(root);', '/src/render/hero/lod.ts').code.includes('mergeSkinnedByMaterial(root)'));
  assert.throws(() => plugin.transform('changed call', '/src/render/hero/lod.ts'), /call changed/);
  plugin.buildEnd();
});

test('actual exported assembly loads all explicitly declared objects and the complete shared skeleton', { skip }, async () => {
  const { rider } = await instance();
  assert.equal(rider.debug.bones, Object.keys(metadata.specification.jointNames).length);
  assert.deepEqual(rider.debug.candidate.authorMeshRoles, metadata.specification.meshNames);
  assert.ok(rider.binding.meshes.length >= Object.keys(metadata.specification.meshNames).length);
  assert.ok(rider.debug.candidate.visibleMeshes.some(mesh => mesh.name === 'RiderBuzzcut'));
  assert.ok(rider.debug.candidate.visibleMeshes.some(mesh => mesh.name === 'RiderGloves'));
  const originalWeights = new Map();
  loaded.scene.traverse(node => { if (node.isSkinnedMesh) originalWeights.set(node.name, [...node.geometry.attributes.skinWeight.array]); });
  for (const { mesh } of rider.binding.meshes) assert.deepEqual([...mesh.geometry.attributes.skinWeight.array], originalWeights.get(mesh.name));
});

test('actual forward/back/neutral targets retain finite full-hierarchy control and report real socket residuals', { skip }, async () => {
  const { rider } = await instance();
  for (let index = 0; index <= 40; index++) {
    const f = poseFrame(-1 + index / 20), before = JSON.stringify(f);
    rider.update(f); assert.equal(JSON.stringify(f), before, 'physics frame remains unchanged');
    assert.ok(rider.debug.allBoneFinite); assert.ok(rider.debug.physicalPose);
    for (const err of [...rider.debug.gripErr, ...rider.debug.soleErr]) assert.ok(Number.isFinite(err) && err >= 0);
    assert.ok(rider.debug.gripAngleErr.every(angle => angle < 1e-5));
    assert.ok(rider.debug.comResidual < 1e-5);
    const measured = rider.toBike(measureAnthropometricCOM(rider, rider.anthropometry));
    assert.ok(measured.distanceTo(new THREE.Vector3().fromArray(rider.debug.anthropometry.requestedCOM)) < 1e-5);
    for (const limb of rider.limbs.values()) {
      assert.ok(Math.abs(rider.position(limb.upper).distanceTo(rider.position(limb.lower)) - limb.lengths[0]) < 1e-5);
      assert.ok(Math.abs(rider.position(limb.lower).distanceTo(rider.position(limb.end)) - limb.lengths[1]) < 1e-5);
    }
  }
});

test('actual COM and socket errors remain bike-local at different world bike leans', { skip }, async () => {
  const { rider, frame } = await instance(), base = frame.position.clone();
  for (const lean of [-1, 0, 1]) {
    const f = poseFrame(lean); rider.update(f);
    const expected = [...rider.debug.gripErr, ...rider.debug.soleErr];
    for (const angle of [-0.7, 0.4, 1.1]) {
      frame.quaternion.setFromAxisAngle(new THREE.Vector3(0, 0, 1), angle);
      frame.position.copy(base).applyQuaternion(frame.quaternion); frame.updateWorldMatrix(true, true);
      f.bikeAngle = angle; rider.update(f);
      assert.ok(rider.debug.comResidual < 1e-5);
      [...rider.debug.gripErr, ...rider.debug.soleErr].forEach((error, i) => assert.ok(Math.abs(error - expected[i]) < 1e-5));
    }
    frame.quaternion.identity(); frame.position.copy(base); frame.updateWorldMatrix(true, true);
  }
});

test('anatomical upper-spine flex leaves the explicit physical pelvis carrier fixed', { skip }, async () => {
  const { rider } = await instance(), frame = poseFrame(0.4), p = rider.physicsTarget(frame);
  let expected;
  for (const flex of [0, -0.3, 0.3]) {
    resetHumanoidPose(rider.binding); rider.poseFromHips(frame, p, [p.hips.x, p.hips.y], flex);
    const actual = rider.bone(rider.role('pelvis')).getWorldQuaternion(new THREE.Quaternion()).toArray();
    if (expected) assert.deepEqual(actual, expected); else expected = actual;
  }
});

test('actual repeated frame is byte-identical after fingers/metacarpals were perturbed', { skip }, async () => {
  const { rider } = await instance(), frame = poseFrame(0.35);
  rider.update(frame); const expected = snapshot(rider);
  for (let n = 0; n < 40; n++) {
    for (const hand of Object.values(rider.binding.contract.hands)) {
      for (const id of Object.values(hand.digits).flat()) {
        rider.bone(id).position.x += 0.3; rider.bone(id).scale.setScalar(1.1); rider.bone(id).quaternion.multiply(new THREE.Quaternion(0, 0, 0.1, Math.sqrt(0.99)));
      }
    }
    rider.update(frame); assert.equal(snapshot(rider), expected);
  }
});

test('actual crash releases both contacts and restart restores the exact ride pose', { skip }, async () => {
  const { rider } = await instance(), frame = poseFrame(0);
  rider.update(frame); const expected = snapshot(rider);
  const pelvis = rider.bone(rider.role('pelvis')).getWorldPosition(new THREE.Vector3());
  frame.ragdoll = ['pelvis', 'torso', 'head', 'upperArm', 'forearm', 'thigh', 'shin'].map(id => ({ id, angle: 0, pos: { x: pelvis.x, y: pelvis.y } }));
  frame.crashed = true; rider.update(frame);
  assert.deepEqual(rider.debug.handOnGrip, [false, false]); assert.deepEqual(rider.debug.footOnPeg, [false, false]);
  frame.tSim += 0.3; frame.ragdoll.forEach(body => { body.angle += 0.2; body.pos.x += 0.1; }); rider.update(frame);
  assert.ok(rider.debug.allBoneFinite);
  frame.ragdoll = null; frame.crashed = false; frame.cut = true; frame.tSim = 3; rider.update(frame);
  assert.equal(snapshot(rider), expected);
});

test('actual named authored clip drives complete rig in Garage without stale contact claims', { skip }, async () => {
  const selected = loaded?.animations[0]?.name ?? (await loadRigAt(pathToFileURL(source), true)).animations[0].name;
  const Rider = createPrivateRiderClass({ ...metadata, previewClip: selected });
  const rider = new Rider(loaded, { complete() {} }), frame = new THREE.Group(); rider.attach({ frame }); rider.setStage(true);
  const f = poseFrame(0); rider.setStageTime(0.4); rider.update(f); const a = snapshot(rider);
  rider.setStageTime(1.1); rider.update(f); const b = snapshot(rider);
  assert.notEqual(a, b); assert.equal(rider.debug.stageClip, selected); assert.ok(rider.debug.allBoneFinite);
  rider.setStageTime(0.4); rider.update(f); assert.equal(snapshot(rider), a);
});
