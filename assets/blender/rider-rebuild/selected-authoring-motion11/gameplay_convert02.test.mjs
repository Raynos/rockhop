/** Coordinate regression only; synthetic fixtures never count as played poses. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { Matrix4, Quaternion, Vector3, PropertyBinding } from 'three';
import { convertSample, affineBound } from './gameplay_convert02.mjs';

const contract = JSON.parse(fs.readFileSync(new URL('../../../../harness/out/rider-rebuild/selected-seated-anatomical09/transport02/rider-contract.json', import.meta.url)));
const C = new Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
const fromRows = rows => new Matrix4().fromArray(rows.flat()).transpose();
function fixture() {
  const bike = new Matrix4().compose(new Vector3(2, 3, 0), new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), .23), new Vector3(1, 1, 1));
  const skeleton = bike.clone().multiply(new Matrix4().makeRotationY(.61));
  const native = new Map(contract.nativeRest.bones.map(b => [b.name, fromRows(b.matrix)]));
  const gltf = new Map([...native].map(([n, m]) => [n, C.clone().multiply(m)]));
  const joints = contract.nativeRest.bones.map(b => {
    const local = b.parent ? gltf.get(b.parent).clone().invert().multiply(gltf.get(b.name)) : gltf.get(b.name);
    const p = new Vector3(), q = new Quaternion(), s = new Vector3(); local.decompose(p, q, s);
    return { id: b.name, name: PropertyBinding.sanitizeNodeName(b.name), position: p.toArray(), quaternion: q.toArray(), scale: s.toArray(),
      worldMatrix: skeleton.clone().multiply(gltf.get(b.name)).toArray() };
  });
  return { native, sample: { tick: 0, timeSeconds: 0, phase: 'neutral', input: { lean: 0 },
    frame: { bikeX: 2, bikeY: 3, bikeAngle: .23, rider: { lean: 0 }, riderBody: { present: true, relX: .1, relY: .9, relAngle: 0 } },
    debug: { physicalPose: true, stageClip: null, allBoneFinite: true,
      anthropometry: { requestedCOM: [.1, .9, 0], carrierAngle: 65*Math.PI/180 }, gripErr: [0, 0], soleErr: [0, 0] },
    joints, bikeFrameWorld: bike.toArray(), skeletonWorld: skeleton.toArray() } };
}
test('removes actual transformed skeleton parent and glTF conversion once', () => {
  const { native, sample } = fixture(), result = convertSample(sample, contract);
  assert(result.hierarchyBound < .0001);
  contract.nativeRest.bones.forEach((b, i) => assert(affineBound(fromRows(result.native[i]), native.get(b.name)) < 1e-12));
});
test('rejects world/local hierarchy mismatch', () => {
  const { sample } = fixture(); sample.joints[22].worldMatrix[12] += .001;
  assert.throws(() => convertSample(sample, contract), /Captured hierarchy differs/);
});
test('rejects stage pose and COM authority mismatch', () => {
  const { sample } = fixture(); sample.debug.stageClip = 'RiderIdle';
  assert.throws(() => convertSample(sample, contract));
  sample.debug.stageClip = null; sample.debug.anthropometry.requestedCOM[1] += .001;
  assert.throws(() => convertSample(sample, contract), /actual physical authority/);
});
