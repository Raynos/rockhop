/** Independent exact GLB-channel and matched-camera checks of saved engine captures. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { Matrix4, Quaternion, Vector3 } from 'three';

const base = path.resolve(process.argv[2] ?? 'harness/out/rider-contact-diagnostic-2026-10-03');
const report = JSON.parse(fs.readFileSync(path.join(base, 'capture06/report.json')));
const bytes = fs.readFileSync(path.join(base, 'source/Rockhop-supported-rider-contact-diagnostic.glb'));
const jsonLength = bytes.readUInt32LE(12), gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength));
const binStart = 28 + jsonLength;
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(bytes), '7adc07e7ee97278013af3f79d201e349fb0094f826aa7f25d02a550412e10cee');
assert.equal(report.samples.length, 157); assert.deepEqual(report.errors, []);
const pairs = new Map(report.samples.filter(s => s.variant === 'repaired' && s.pose !== 'STEP').map(s => [s.family + '/' + (s.frame ?? s.view), s]));
for (const raw of report.samples.filter(s => s.variant === 'raw-body11')) {
  const repaired = pairs.get(raw.family + '/' + (raw.frame ?? raw.view));
  assert.deepEqual(raw.camera, repaired.camera); assert.deepEqual(raw.bones, repaired.bones);
  for (const row of [raw, repaired]) assert(row.meshes.every(m => (m.morphWeights ?? []).every(w => w === 0)));
}
for (const s of report.samples) { assert(s.webdriver && s.garage.on); assert.equal(s.audioContexts, 0); assert(s.cloudPoseMatrixMaxError < 1e-5); assert(fs.statSync(s.image).size > 10000); }
const sizes = { SCALAR: 1, VEC3: 3, VEC4: 4 };
const accessor = i => {
  const a = gltf.accessors[i], view = gltf.bufferViews[a.bufferView]; assert.equal(a.componentType, 5126);
  const width = sizes[a.type]; assert(width);
  return Array.from({ length: a.count }, (_, row) => Array.from({ length: width }, (_, k) => bytes.readFloatLE(binStart + view.byteOffset + (a.byteOffset ?? 0) + row * (view.byteStride ?? width * 4) + k * 4)));
};
const clip = gltf.animations.find(a => a.name === 'diagnostic_contact_observations_STEP');
assert(clip && clip.channels.length === 61 && clip.samplers.every(s => s.interpolation === 'STEP'));
const parents = new Map(); gltf.nodes.forEach((n, i) => n.children?.forEach(c => parents.set(c, i)));
let matrixMaxError = 0, morphMaxError = 0;
const contactRows = [];
for (const sample of report.samples.filter(s => s.pose === 'STEP')) {
  const nodes = structuredClone(gltf.nodes);
  for (const channel of clip.channels) {
    const s = clip.samplers[channel.sampler], times = accessor(s.input).flat(), values = accessor(s.output);
    const index = times.findLastIndex(t => t <= sample.time); assert(index >= 0);
    const key = channel.target.path;
    if (key === 'weights') {
      const count = gltf.meshes[nodes[channel.target.node].mesh].primitives[0].targets.length;
      const expected = values.slice(index * count, (index + 1) * count).flat();
      for (const m of sample.meshes.filter(m => m.morphWeights?.length === count)) expected.forEach((v, i) => { morphMaxError = Math.max(morphMaxError, Math.abs(v - m.morphWeights[i])); });
    } else nodes[channel.target.node][key] = values[index];
  }
  const cache = new Map();
  const world = i => {
    if (cache.has(i)) return cache.get(i);
    const n = nodes[i], local = new Matrix4().compose(new Vector3().fromArray(n.translation ?? [0, 0, 0]), new Quaternion().fromArray(n.rotation ?? [0, 0, 0, 1]), new Vector3().fromArray(n.scale ?? [1, 1, 1]));
    const m = parents.has(i) ? world(parents.get(i)).clone().multiply(local) : local; cache.set(i, m); return m;
  };
  const wrapperInverse = new Matrix4().fromArray(sample.sceneMatrix).invert();
  for (const i of gltf.skins[0].joints) {
    const name = nodes[i].name.replace(/[[\].:/]/g, ''), actual = wrapperInverse.clone().multiply(new Matrix4().fromArray(sample.bones[name].world));
    world(i).elements.forEach((v, k) => { matrixMaxError = Math.max(matrixMaxError, Math.abs(v - actual.elements[k])); });
  }
  const wrapper = new Matrix4().fromArray(sample.sceneMatrix);
  const points = {};
  for (const name of ['gripSocket.L', 'gripSocket.R', 'soleSocket.L', 'soleSocket.R']) {
    const i = nodes.findIndex(n => n.name === name); points[name] = new Vector3().setFromMatrixPosition(wrapper.clone().multiply(world(i))).toArray();
  }
  contactRows.push({ sourceTime: sample.time, engineWorldRiderSockets: points });
}
assert(matrixMaxError < 1e-5); assert(morphMaxError < 1e-6);
assert.equal(new Set(report.samples.filter(s => s.pose === 'STEP').map(s => JSON.stringify(s.bones))).size, 17);
const fixture = report.samples[0].fixture;
const bikeMarks = Object.fromEntries(fixture.bikeRuntimeNodes.filter(n => /^attach_(grip|peg|frame_origin|chassis_com)/.test(n.name)).map(n => [n.name, new Vector3().setFromMatrixPosition(new Matrix4().fromArray(n.world)).toArray()]));
const qa = { status: 'EXACT_CAPTURE_VERIFIED_UNACCEPTED', repoSHA: report.repoSHA, frames: 157, pairedArmsOutFrames: 140, distinctSTEPPoseKeys: 17, clip: clip.name, sourceTimes: '0..2s at 1/8s; held 1/4s per movie frame', sourceSHA256: hash(bytes), sourceBytes: bytes.length,
  poseManifestSHA256: hash(fs.readFileSync(path.join(base, 'source/diagnostic-poses.json'))), cloudPoseMatrixMaxError: Math.max(...report.samples.map(s => s.cloudPoseMatrixMaxError)), independentGLBWorldMatrixMaxError: matrixMaxError, independentMorphMaxError: morphMaxError,
  identicalPairedCamerasAndBoneMatrices: true, pairedMorphsAllZero: true, audioContexts: 0, errors: [], frozenPhysicsHash: report.samples[0].stateHash,
  captureReportSHA256: hash(fs.readFileSync(path.join(base, 'capture06/report.json'))), captureReportTailFailure: report.failure,
  note: 'Original final validation accessed optional raw-head morph weights; all157actual captures independently verified here. Capture code now handles absent weights.',
  browser: report.browser, device: report.device, launchURL: report.launchURL, visualLimits: ['T/A underarm webs remain in raw and repaired.', 'STEP hands/feet/saddle do not align with current engine bike/wrapper contract.', 'No continuous interpolation, physics-driven riding, normals, art or physical-device acceptance.'] };
fs.writeFileSync(path.join(base, 'verified-qa.json'), JSON.stringify(qa, null, 2) + '\n');
fs.writeFileSync(path.join(base, 'engine-fixture.json'), JSON.stringify({ ...qa, bikeSHA256: hash(fs.readFileSync('public/models/bike-rookie.glb')), fixture, bikeRuntimeContactMarks: bikeMarks, riderContactsBySTEPTime: contactRows }, null, 2) + '\n');
console.log(JSON.stringify(qa));
