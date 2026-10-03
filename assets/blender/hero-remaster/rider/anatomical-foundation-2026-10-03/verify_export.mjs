import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const [file, directory] = process.argv.slice(2);
if (!file || !directory) throw new Error('Usage: verify_export.mjs GLB evidence-directory');
fs.mkdirSync(directory, { recursive: true });
const raw = fs.readFileSync(file);
const jsonSize = raw.readUInt32LE(12);
const definition = JSON.parse(raw.subarray(20, 20 + jsonSize).toString('utf8'));
const array = raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength);
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(array, '', resolve, reject));
const sha256 = crypto.createHash('sha256').update(raw).digest('hex');
gltf.scene.updateMatrixWorld(true);
const meshes = [];
const bones = new Map();
gltf.scene.traverse(object => {
  if (object.isBone) bones.set(object.name.replace(/([a-zA-Z]+)([LR])$/, '$1.$2'), object);
  if (object.isSkinnedMesh) meshes.push(object);
});
const output = {
  status: 'UNACCEPTED independent export measurement; no visual/contact pass',
  file: path.resolve(file), sha256, bytes: raw.length,
  coordinateContract: {
    units: 'metres', axes: '+Xforward,+Yup,+Zgame-left',
    fileNonboneRootX: 0.65, ordinaryRuntimeWrapperX: -0.65,
    rootContract: 'Root is explicit, not donor inverse-bind offset; normal wrapper cancels x0.65',
    runtimeConditioningOptout: false,
  },
  namedRuntime19: ['pelvis', 'spine', 'chest', 'neck', 'head',
    ...['L', 'R'].flatMap(side => ['shoulder', 'upperArm', 'forearm', 'hand'].map(n => `${n}.${side}`)),
    ...['L', 'R'].flatMap(side => ['thigh', 'shin', 'foot'].map(n => `${n}.${side}`))],
  clips: gltf.animations.map(c => ({ name: c.name, durationS: c.duration, tracks: c.tracks.length })),
  nonboneRoots: gltf.scene.children.map(o => ({ name: o.name,
    position: o.position.toArray(), quaternionXYZW: o.quaternion.toArray(), scale: o.scale.toArray(),
    matrixWorldColumnMajor: o.matrixWorld.toArray() })),
  meshRest: [],
  inverseBinds: definition.skins.map(s => ({
    jointOrder: s.joints.map(i => ({ nodeIndex: i, name: definition.nodes[i].name })),
    originalAccessor: s.inverseBindMatrices,
  })),
  bones: Object.fromEntries([...bones].map(([name, b]) => [name, {
    parent: b.parent?.isBone ? b.parent.name : null,
    localPosition: b.position.toArray(), localQuaternionXYZW: b.quaternion.toArray(),
    localScale: b.scale.toArray(), matrixWorldColumnMajor: b.matrixWorld.toArray(),
  }])),
};
if (!output.namedRuntime19.every(n => bones.has(n))) throw new Error('Missing runtime role');
const scratch = new THREE.Vector3();
for (const m of meshes) {
  m.skeleton.update();
  let cancellationMaxM = 0;
  const v = m.geometry.attributes.position;
  for (let i = 0; i < v.count; i++) {
    scratch.fromBufferAttribute(v, i);
    const base = scratch.clone().applyMatrix4(m.bindMatrix).applyMatrix4(m.bindMatrixInverse);
    m.applyBoneTransform(i, scratch);
    cancellationMaxM = Math.max(cancellationMaxM, scratch.distanceTo(base));
  }
  output.meshRest.push({ name: m.name, vertices: v.count,
    triangles: m.geometry.index.count / 3, restCancellationMaxM: cancellationMaxM,
    cancellationSpace: 'mesh local after bindMatrixInverse; geometry is exported in file frame, not mesh-local origin',
    inverseBindJointOrder: m.skeleton.bones.map(b => b.name),
    originalInverseBindColumnMajor: m.skeleton.boneInverses.map(x => x.toArray()),
    bindMatrixColumnMajor: m.bindMatrix.toArray(),
    bindMatrixInverseColumnMajor: m.bindMatrixInverse.toArray(),
    meshWorldColumnMajor: m.matrixWorld.toArray() });
}
// True T/A action-off fixtures derive exact world directions from this rig.
const restLocal = new Map([...bones].map(([n, b]) => [n, {
  p: b.position.clone(), q: b.quaternion.clone(), s: b.scale.clone(),
}]));
function reset() {
  for (const [name, row] of restLocal) {
    const b = bones.get(name); b.position.copy(row.p); b.quaternion.copy(row.q); b.scale.copy(row.s);
  }
  gltf.scene.updateMatrixWorld(true);
}
function aim(name, direction) {
  const b = bones.get(name);
  gltf.scene.updateMatrixWorld(true);
  const world = b.getWorldQuaternion(new THREE.Quaternion());
  const restDirection = new THREE.Vector3(0, 1, 0).applyQuaternion(world);
  const desired = new THREE.Quaternion().setFromUnitVectors(restDirection, direction.clone().normalize()).multiply(world);
  const parent = b.parent.getWorldQuaternion(new THREE.Quaternion());
  b.quaternion.copy(parent.invert().multiply(desired));
  gltf.scene.updateMatrixWorld(true);
}
output.actionOffPoses = {};
for (const [label, down] of [['T', 0], ['A', -0.7071067811865476], ['neutral', -0.984807753012208]]) {
  reset();
  for (const side of ['L', 'R']) {
    const lateral = Math.sqrt(1 - down * down) * (side === 'L' ? 1 : -1);
    const dir = new THREE.Vector3(0, down, lateral);
    for (const role of ['upperArm', 'forearm', 'hand']) aim(`${role}.${side}`, dir);
  }
  output.actionOffPoses[label] = {
    action: null, morphs: 0, correctives: 0,
    localTRS: Object.fromEntries([...bones].map(([n, b]) => [n, {
      position: b.position.toArray(), quaternionXYZW: b.quaternion.toArray(), scale: b.scale.toArray(),
    }])),
    worldDirections: Object.fromEntries(['L', 'R'].flatMap(side => ['upperArm', 'forearm'].map(role => {
      const b = bones.get(`${role}.${side}`);
      return [`${role}.${side}`, new THREE.Vector3(0, 1, 0).applyQuaternion(b.getWorldQuaternion(new THREE.Quaternion())).toArray()];
    }))),
  };
}
reset();
const mixer = new THREE.AnimationMixer(gltf.scene);
const clip = gltf.animations.find(c => c.name === 'foundation_stress');
if (!clip) throw new Error('Missing stress animation');
output.clipTimeline = { firstKeyS: clip.tracks[0].times[0],
  lastKeyS: clip.tracks[0].times.at(-1), durationS: clip.duration };
mixer.clipAction(clip).setLoop(THREE.LoopOnce, 1).play();
let first = null;
output.playback = [];
const sampledPositions = {};
for (let frame = 0; frame <= 192; frame++) {
  mixer.setTime(frame / 24 + output.clipTimeline.firstKeyS);
  gltf.scene.updateMatrixWorld(true);
  const row = { timeS: frame / 24, actualGLTFKeyTimeS: frame / 24 + output.clipTimeline.firstKeyS, mesh: [] };
  for (const mesh of meshes) {
    mesh.skeleton.update();
    const positions = mesh.geometry.attributes.position;
    const vv = new Float64Array(positions.count * 3);
    for (let i = 0; i < positions.count; i++) {
      scratch.fromBufferAttribute(positions, i);
      mesh.applyBoneTransform(i, scratch); mesh.localToWorld(scratch);
      scratch.toArray(vv, i * 3);
    }
    if (![...vv].every(Number.isFinite)) throw new Error('Nonfinite moving vertex');
    if (!first) first = new Map();
    if (frame === 0) first.set(mesh.name, vv.slice());
    const start = first.get(mesh.name);
    let displacementMaxM = 0;
    for (let i = 0; i < vv.length; i += 3) {
      displacementMaxM = Math.max(displacementMaxM,
        Math.hypot(vv[i] - start[i], vv[i + 1] - start[i + 1], vv[i + 2] - start[i + 2]));
    }
    row.mesh.push({ name: mesh.name, displacementMaxM });
    if ([0, 24, 48, 96, 120, 144, 168].includes(frame)) {
      const key = frame / 24;
      sampledPositions[key] ??= {};
      sampledPositions[key][mesh.name] = [...vv];
    }
  }
  output.playback.push(row);
}
output.limits = ['No sourceA/C19 field transferred.',
  'Generic stress clip is not bike-support choreography.',
  'Body/garment interpenetration and stock pattern likeness need separate measurements/review.',
  'Do not set runtime skin-conditioning optout from this export cancellation check alone.'];
fs.writeFileSync(path.join(directory, 'export-manifest.json'), JSON.stringify(output, null, 2) + '\n');
fs.writeFileSync(path.join(directory, 'export-sampled-positions.json'), JSON.stringify(sampledPositions));
console.log(JSON.stringify({ sha256, bones: bones.size, clips: output.clips,
  cancellation: output.meshRest.map(m => ({ name: m.name, maxM: m.restCancellationMaxM })),
  actionOffPoses: Object.keys(output.actionOffPoses), sampledFrames: output.playback.length }));
