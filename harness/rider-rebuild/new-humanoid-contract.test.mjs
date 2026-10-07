import test from 'node:test';
import assert from 'node:assert/strict';
import {
  Bone, BufferGeometry, Float32BufferAttribute, Group, Matrix4, MeshStandardMaterial,
  Object3D, Quaternion, Skeleton, SkinnedMesh, Uint16BufferAttribute, Vector3,
} from 'three';
import { clone as cloneSkeleton } from 'three/addons/utils/SkeletonUtils.js';
import {
  bindHumanoidContract, captureHumanoidContract, resetHumanoidPose,
  setJointWorldQuaternion, solvePalmSocketTarget,
} from './new-humanoid-contract.mjs';

const digits = ['thumb', 'index', 'middle', 'ring', 'pinky'];
const rotate = (x, y, z) => new Quaternion().setFromAxisAngle(new Vector3(x, y, z).normalize(), 0.43);
const maxError = (a, b) => Math.max(...a.map((x, i) => Math.abs(x - b[i])));

// Intentionally opaque node names: anatomical roles come ONLY from this author mapping.
// The extra spine, forearm twist, and five metacarpals are outside physics role lists.
function fixture() {
  const root = new Group(); root.name = 'asset-frame';
  root.position.set(0.7, 0.2, -0.3); root.quaternion.copy(rotate(1, 2, 3));
  const bones = new Map(); let serial = 0;
  const joint = (id, parent, xyz) => {
    const bone = new Bone(); bone.name = `node-${++serial}`; bone.position.fromArray(xyz);
    parent.add(bone); bones.set(id, bone); return bone;
  };
  const hips = joint('hips', root, [0, 1, 0]);
  const spine = joint('spine-extra', hips, [0, 0.12, 0]);
  const torso = joint('thorax', spine, [0, 0.2, 0]);
  const arm = joint('upper-arm', torso, [0.2, 0.15, 0]);
  const twist = joint('forearm-twist', arm, [0.2, 0, 0]);
  const forearm = joint('forearm', twist, [0.1, 0, 0]);
  const wrist = joint('wrist', forearm, [0.2, 0, 0]);
  const digitChains = {};
  digits.forEach((digit, index) => {
    const metacarpal = joint(`${digit}-meta`, wrist, [0.08, 0.04 - index * 0.02, 0]);
    const proximal = joint(`${digit}-prox`, metacarpal, [0.035, 0, 0]);
    joint(`${digit}-distal`, proximal, [0.025, 0, 0]);
    digitChains[digit] = [`${digit}-meta`, `${digit}-prox`, `${digit}-distal`];
  });
  const socket = new Object3D(); socket.name = 'author-palm-socket';
  socket.position.set(0.055, 0.013, -0.019); socket.quaternion.copy(rotate(1, -2, 1));
  wrist.add(socket); root.updateWorldMatrix(true, true);
  const skeleton = new Skeleton([...bones.values()]);
  const mesh = (name, color) => {
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new Float32BufferAttribute([0.9, 1.47, 0, 0.94, 1.47, 0, 0.91, 1.49, 0], 3));
    geometry.setAttribute('skinIndex', new Uint16BufferAttribute(Array(3).fill([6, 0, 0, 0]).flat(), 4));
    geometry.setAttribute('skinWeight', new Float32BufferAttribute(Array(3).fill([1, 0, 0, 0]).flat(), 4));
    const skin = new SkinnedMesh(geometry, new MeshStandardMaterial({ color })); skin.name = name;
    root.add(skin); skin.bind(skeleton, new Matrix4()); return skin;
  };
  const body = mesh('body-surface', 0xa67860), glove = mesh('black-glove-surface', 0x101010);
  const spec = {
    units: 'metres', frame: 'gltf-y-up',
    jointNames: Object.fromEntries([...bones].map(([id, bone]) => [id, bone.name])),
    roles: { pelvis: 'hips', trunk: ['spine-extra', 'thorax'], upperArmLeft: 'upper-arm', forearmLeft: 'forearm', wristLeft: 'wrist' },
    meshNames: { body: body.name, gloveLeft: glove.name },
    hands: { left: {
      wristJointId: 'wrist', socketNodeName: socket.name, digits: digitChains,
      forwardJointId: 'middle-meta', radialJointId: 'index-meta', ulnarJointId: 'pinky-meta', normalSign: 1,
    } },
  };
  const contract = captureHumanoidContract(root, spec);
  return { root, bones, body, glove, spec, contract, binding: bindHumanoidContract(root, contract) };
}

test('serialized rest contract survives a real SkeletonUtils clone with one wearer skeleton', () => {
  const { root, contract } = fixture();
  assert.equal(contract.jointCount, 22);
  assert.equal(contract.joints.find(row => row.id === 'forearm').parentJointId, 'forearm-twist');
  assert.equal(contract.joints.find(row => row.id === 'middle-prox').parentJointId, 'middle-meta');
  const copied = cloneSkeleton(root);
  const binding = bindHumanoidContract(copied, JSON.parse(JSON.stringify(contract)));
  const body = binding.meshes.find(row => row.role === 'body').mesh;
  const glove = binding.meshes.find(row => row.role === 'gloveLeft').mesh;
  assert.notEqual(binding.byId.get('wrist'), root.getObjectByName(contract.jointNames.wrist));
  assert.equal(body.skeleton.bones[6], binding.byId.get('wrist'));
  assert.equal(glove.skeleton.bones[6], binding.byId.get('wrist'));
  const axes = contract.hands.left.axesInWrist;
  assert.ok(maxError(axes.forward, [1, 0, 0]) < 1e-12);
  assert.ok(maxError(axes.radial, [0, 1, 0]) < 1e-12);
  assert.ok(maxError(axes.normal, [0, 0, 1]) < 1e-12);
});

test('world orientation uses actual extra spine, twist and metacarpal parents', () => {
  const { binding, bones } = fixture();
  for (const id of ['spine-extra', 'forearm-twist', 'middle-meta']) bones.get(id).quaternion.copy(rotate(2, -1, 3));
  binding.root.updateWorldMatrix(true, true);
  const target = rotate(-3, 2, 1), untouched = target.toArray();
  for (const id of ['thorax', 'forearm', 'middle-prox']) {
    setJointWorldQuaternion(binding, id, target);
    assert.ok(bones.get(id).getWorldQuaternion(new Quaternion()).angleTo(target) < 1e-7, id);
  }
  assert.deepEqual(target.toArray(), untouched);
});

test('identical frames reset all joint TRS and produce identical skin deformation without drift', () => {
  const { binding, bones, body, glove } = fixture();
  const delta = rotate(1, 1, -1);
  const frame = () => {
    resetHumanoidPose(binding);
    for (const id of ['spine-extra', 'forearm-twist', 'middle-meta', 'middle-prox', 'middle-distal']) {
      bones.get(id).quaternion.multiply(delta);
    }
    setJointWorldQuaternion(binding, 'wrist', rotate(1, 2, -1));
    binding.root.updateWorldMatrix(true, true); body.skeleton.update(); glove.skeleton.update();
    return JSON.stringify({
      joints: [...bones].map(([id, bone]) => [id, bone.position.toArray(), bone.quaternion.toArray(), bone.scale.toArray(), bone.matrixWorld.toArray()]),
      body: body.applyBoneTransform(0, new Vector3().fromBufferAttribute(body.geometry.attributes.position, 0)).toArray(),
      glove: glove.applyBoneTransform(0, new Vector3().fromBufferAttribute(glove.geometry.attributes.position, 0)).toArray(),
      skinMatrices: [...body.skeleton.boneMatrices],
    });
  };
  const expected = frame();
  for (let index = 0; index < 60; index++) {
    // Simulate earlier clips/IK mutating nonphysics fingers and body transforms.
    bones.get('middle-distal').position.set(9, 8, 7); bones.get('middle-meta').scale.setScalar(1.2);
    bones.get('forearm-twist').quaternion.multiply(delta);
    assert.equal(frame(), expected, `frame ${index}`);
  }
  resetHumanoidPose(binding);
  for (const row of binding.contract.joints) {
    const bone = bones.get(row.id);
    assert.deepEqual(bone.position.toArray(), row.restLocal.translation);
    assert.deepEqual(bone.quaternion.toArray(), row.restLocal.rotationXYZW);
    assert.deepEqual(bone.scale.toArray(), row.restLocal.scale);
  }
});

test('wrist target rotates the calibrated palm offset AND the palm orientation', () => {
  const { binding } = fixture();
  const local = new Matrix4().fromArray(binding.contract.hands.left.socketInWrist);
  const target = new Matrix4().compose(new Vector3(0.27, 0.78, 0.33), rotate(1, 0, 2), new Vector3(1, 1, 1));
  const untouched = target.toArray();
  const wrist = solvePalmSocketTarget(binding, 'left', target);
  assert.ok(maxError(wrist.clone().multiply(local).toArray(), target.toArray()) < 1e-12);
  assert.deepEqual(target.toArray(), untouched);
  const unrotatedOffset = new Vector3().setFromMatrixPosition(target).sub(new Vector3().setFromMatrixPosition(local));
  assert.ok(unrotatedOffset.distanceTo(new Vector3().setFromMatrixPosition(wrist)) > 0.01);
});

test('missing joints, ambiguous names, detached glove skeleton and bad anatomical landmarks fail intake', () => {
  {
    const { root, spec } = fixture(); delete spec.jointNames['forearm-twist'];
    assert.throws(() => captureHumanoidContract(root, spec), /Declare every actual joint/);
  }
  {
    const { root, spec } = fixture(); const duplicate = new Object3D(); duplicate.name = spec.jointNames.wrist; root.add(duplicate);
    assert.throws(() => captureHumanoidContract(root, spec), /Ambiguous\/missing exact node/);
  }
  {
    const { root, spec, glove } = fixture();
    glove.skeleton = new Skeleton(glove.skeleton.bones.map(bone => bone.clone(false)), glove.skeleton.boneInverses);
    assert.throws(() => captureHumanoidContract(root, spec), /share the actual joint objects/);
  }
  {
    const { root, spec } = fixture(); spec.hands.left.radialJointId = 'middle-meta'; spec.hands.left.ulnarJointId = 'middle-prox';
    assert.throws(() => captureHumanoidContract(root, spec), /Collinear palm landmarks/);
  }
});

test('source rest, inverse binds, hand axes and socket calibration are checked on binding', () => {
  for (const kind of ['rest', 'inverse', 'axis', 'socket', 'parent']) {
    const { root, contract, bones } = fixture();
    if (kind === 'rest') bones.get('middle-meta').position.x += 0.01;
    if (kind === 'inverse') contract.joints[0].inverseBind[12] += 0.01;
    if (kind === 'axis') contract.hands.left.axesInWrist.forward = [0, 1, 0];
    if (kind === 'socket') root.getObjectByName('author-palm-socket').position.z += 0.01;
    if (kind === 'parent') bones.get('upper-arm').add(bones.get('forearm'));
    assert.throws(() => bindHumanoidContract(root, contract), /source rest|inverse bind|calibration changed|hierarchy changed/, kind);
  }
});

test('world-quaternion solve explicitly rejects nonuniform or reflected parent scales', () => {
  for (const scale of [[1, 2, 1], [-1, 1, 1]]) {
    const { binding, bones } = fixture(); bones.get('middle-meta').scale.fromArray(scale);
    assert.throws(() => setJointWorldQuaternion(binding, 'middle-prox', rotate(1, 2, 3)), /nonreflected similarity parent/);
  }
});

test('actual 16.45ppm export residual needs explicit bounded admission and leaves source scales intact', () => {
  const { binding, bones } = fixture(), parent = bones.get('middle-meta');
  parent.scale.set(1.0000164508819593, 0.9999999403953558, 1.0000002384185798);
  const sourceScale = parent.scale.toArray(), target = rotate(1, -3, 2);
  assert.throws(() => setJointWorldQuaternion(binding, 'middle-prox', target), /nonreflected similarity/);
  setJointWorldQuaternion(binding, 'middle-prox', target, 1e-4);
  assert.deepEqual(parent.scale.toArray(), sourceScale);
  assert.ok(bones.get('middle-prox').getWorldQuaternion(new Quaternion()).normalize().angleTo(target) < 1e-5);
  assert.throws(() => setJointWorldQuaternion(binding, 'middle-prox', target, 1e-3), /tolerance must be/);
  parent.matrixAutoUpdate = false; parent.matrix.identity(); parent.matrix.elements[4] = 0.05;
  parent.matrixWorldNeedsUpdate = true;
  assert.throws(() => setJointWorldQuaternion(binding, 'middle-prox', target, 1e-4), /nonreflected similarity/);
});
