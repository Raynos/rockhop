/** CPU-only integration checks. Header fixture checks control, never geometry/art. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import * as THREE from 'three';
import { privateEnginePlugin } from './private-engine-plugin.mjs';
import { resetHumanoidPose } from './new-humanoid-contract.mjs';
import { prepareSeatedCorrective } from '../../assets/blender/rider-rebuild/selected-seated-corrective06/apply-morph02.mjs';
import { appendAnimation, rigIdentity } from '../../assets/blender/rider-rebuild/selected-seated-diagnostic08/append-clip.mjs';

const runtime = path.resolve('harness/rider-rebuild/private-rider.mjs');
const original = fs.readFileSync(runtime, 'utf8');
const transformed = metadata => privateEnginePlugin(metadata).transform(original, runtime)?.code;

test('corrective source substitution is conditional and follows calibration and final bone pose', () => {
  assert.equal(transformed({}), undefined);
  const code = transformed({ corrective: {} });
  assert.match(code, /import \{ prepareSeatedCorrective \} from .*apply-morph02\.mjs/);
  assert.match(code, /this\.anthropometry = calibrateAnthropometry\(this, metadata\);\s+this\.applyPoseCorrective = prepareSeatedCorrective/);
  assert.match(code, /this\.scene\.updateWorldMatrix\(true, true\);\s+this\.debug\.correctiveWeight = this\.applyPoseCorrective\(true\);\s+this\.debug\.allBoneFinite/);
  assert.throws(() => privateEnginePlugin({ comparison: true, releaseBuild: false,
    qualificationState: 'FAILED_CORRECTIVE_GATES', corrective: {} }), /cannot enter the comparison/);
});

const source = path.resolve('harness/out/rider-rebuild/selected-seated-corrective06/constructed02/rider.glb');
const contractPath = path.resolve('harness/out/rider-rebuild/selected-seated-corrective06/constructed02/rider-contract.json');
const authorPath = path.resolve('harness/out/rider-rebuild/selected-seated-author04/authored01/rookie.json');
const available = [source, contractPath, authorPath].every(file => fs.existsSync(file));

test('actual native75 saved author key reaches runtime morph through appended TRS, then returns to zero', {
  skip: !available && 'Ignored diagnostic inputs absent; no full GLB read is required',
}, () => {
  // Read only the original GLB JSON header. No BIN, textures, vertex positions,
  // Blender, browser, construction or expensive decoder work belongs in this test.
  const fd = fs.openSync(source, 'r'); let document;
  try {
    const header = Buffer.alloc(20); assert.equal(fs.readSync(fd, header, 0, 20, 0), 20);
    assert.equal(header.toString('ascii', 0, 4), 'glTF');
    const length = header.readUInt32LE(12); assert(length < 16 * 1024 * 1024);
    const json = Buffer.alloc(length); assert.equal(fs.readSync(fd, json, 0, length, 20), length);
    document = JSON.parse(json);
  } finally { fs.closeSync(fd); }
  const metadata = JSON.parse(fs.readFileSync(contractPath)), author = JSON.parse(fs.readFileSync(authorPath));
  assert.equal(metadata.qualificationState, 'FAILED_CORRECTIVE_GATES');
  const identity = rigIdentity(document, metadata), jointSet = new Set(identity.map(row => row.nodeIndex));
  const nodes = document.nodes.map((row, index) => {
    const node = jointSet.has(index) ? new THREE.Bone() : new THREE.Group(); node.name = row.name;
    if (row.matrix) node.applyMatrix4(new THREE.Matrix4().fromArray(row.matrix));
    else {
      node.position.fromArray(row.translation ?? [0, 0, 0]);
      node.quaternion.fromArray(row.rotation ?? [0, 0, 0, 1]); node.scale.fromArray(row.scale ?? [1, 1, 1]);
    }
    return node;
  });
  document.nodes.forEach((row, index) => row.children?.forEach(child => nodes[index].add(nodes[child])));
  const scene = new THREE.Group(); document.scenes[document.scene ?? 0].nodes.forEach(index => scene.add(nodes[index]));
  const placement = new THREE.Group(); placement.quaternion.fromArray(metadata.driver.assetToBikeQuaternionXYZW); placement.add(scene);
  const byName = new Map(nodes.map(node => [node.name, node]));
  const byId = new Map(Object.entries(metadata.specification.jointNames).map(([id, name]) => [id, byName.get(name)]));
  const rests = new Map([...byId].map(([id, node]) => [id, { translation: node.position.toArray(),
    rotationXYZW: node.quaternion.toArray(), scale: node.scale.toArray() }]));
  const meshes = ['RiderJeans', ...Array.from({ length: 4 }, (_, i) => `RiderBody.primitive${i}`)].map(role => ({ role,
    mesh: { morphTargetDictionary: { SelectedSeatedCorrective06: 0 }, morphTargetInfluences: [0] } }));
  const { tail, animation } = appendAnimation(document, author, identity, document.buffers[0].byteLength);
  const read = index => {
    const accessor = document.accessors[index], view = document.bufferViews[accessor.bufferView];
    // appendAnimation starts at the supplied BIN length, before extending buffer metadata.
    const offset = view.byteOffset - (document.buffers[0].byteLength - tail.length);
    return Array.from({ length: view.byteLength / 4 }, (_, i) => tail.readFloatLE(offset + i * 4));
  };
  const properties = { translation: 'position', rotation: 'quaternion', scale: 'scale' };
  const tracks = animation.channels.map(channel => {
    const sampler = animation.samplers[channel.sampler], property = properties[channel.target.path];
    const Track = property === 'quaternion' ? THREE.QuaternionKeyframeTrack : THREE.VectorKeyframeTrack;
    const track = new Track('fixture.' + property, read(sampler.input), read(sampler.output));
    return { node: nodes[channel.target.node], property, interpolant: track.createInterpolant() };
  });
  // Evaluate the transformed actual class; dependencies outside update are not
  // exercised. Constructor/calibration ordering is checked separately above.
  const body = transformed(metadata).replace(/^import .*;\n/gm, '').replace(/^export function /gm, 'function ');
  const create = Function('THREE', 'resetHumanoidPose', 'prepareSeatedCorrective', body + '\nreturn createPrivateRiderClass;')(THREE, resetHumanoidPose, prepareSeatedCorrective);
  const rider = Object.create(create(metadata).prototype);
  Object.assign(rider, { bike: {}, release: null, stage: true, scene, roles: metadata.specification.roles,
    binding: { byId, order: [...byId], rests, root: scene, meshes }, clip: { name: animation.name, duration: 6 }, clipTracks: tracks,
    debug: { fullResetCount: 0, handOnGrip: [false, false], footOnPeg: [false, false] } });
  rider.applyPoseCorrective = prepareSeatedCorrective(rider, { activation: metadata.corrective });
  for (const [time, expected] of [[0, 0], [2, 1], [4, 1], [5, 0], [8, 1], [12, 0]]) {
    rider.stageTime = time; rider.update({});
    assert(Math.abs(rider.debug.correctiveWeight - expected) < 1e-5, `${time}s weight ${rider.debug.correctiveWeight}`);
    assert(rider.debug.allBoneFinite); assert.equal(rider.debug.stageClip, animation.name);
    assert.deepEqual(meshes.map(({ mesh }) => mesh.morphTargetInfluences[0]), Array(5).fill(rider.debug.correctiveWeight));
    assert.deepEqual(rider.debug.handOnGrip, [false, false]); assert.deepEqual(rider.debug.footOnPeg, [false, false]);
  }
  for (const track of tracks) track.node[track.property].fromArray(track.interpolant.evaluate(2));
  let refreshes = 0;
  const updateWorld = scene.updateWorldMatrix;
  scene.updateWorldMatrix = function (...args) { refreshes++; return updateWorld.apply(this, args); };
  assert(Math.abs(rider.applyPoseCorrective() - 1) < 1e-5, 'Standalone default refreshes newly changed TRS');
  assert.equal(refreshes, 1);
  assert(Math.abs(rider.applyPoseCorrective(true) - 1) < 1e-5);
  assert.equal(refreshes, 1, 'Already updated runtime pose requires no extra hierarchy traversal');
});
