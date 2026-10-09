/** Read-only five-snapshot local-TRS measurements against the original small rig GLB.
 * node .../compare-garage-clip.mjs --report=.../report.json --out=.../parity.json
 * No dense GLB read, pose/time injection, rendering or art-acceptance threshold.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { PropertyBinding, QuaternionKeyframeTrack, VectorKeyframeTrack, REVISION } from 'three';

const arg = (name, fallback = '') => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const root = process.cwd();
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = filename => {
  const absolute = path.resolve(root, filename), bytes = fs.readFileSync(absolute);
  return { path: absolute, sha256: hash(bytes), bytes };
};
const pinned = row => {
  const result = read(row.path); assert.equal(result.sha256, row.sha256, `Changed small source ${row.path}`); return result;
};
assert(arg('report') && arg('out'), 'Pass --report and a fresh --out JSON path');
const actualSource = read(arg('report')), actual = JSON.parse(actualSource.bytes);
assert(!actual.failure && actual.errors?.length === 0, 'Actual Garage capture must finish without failure');
assert(actual.requestedClip && actual.snapshots.length === 5, 'Exact requested action and five actual snapshots required');
const contractSource = pinned(actual.contract), contract = JSON.parse(contractSource.bytes);
const transportSource = read(arg('transport', path.join(path.dirname(contractSource.path), 'export.json')));
const transport = JSON.parse(transportSource.bytes);
assert.equal(transport.contract.sha256, contractSource.sha256, 'Actual contract matches animation transport');
assert.equal(transport.glb.sha256, contract.glbSHA256, 'Exact appended selected source identity');
assert(actual.loaded.some(row => row.sha256 === transport.glb.sha256), 'Actual capture served the appended selected source');
const configSource = read(arg('input', 'assets/blender/rider-rebuild/selected-garage-actions01/input.json'));
assert.equal(configSource.sha256, transport.inputSHA256, 'Exact corrected transport input');
const config = JSON.parse(configSource.bytes), rigSource = pinned(config.resumeInputs.rigGLB);
const originalReceiptSource = pinned(config.resumeInputs.rigReceipt);
assert.equal(originalReceiptSource.sha256, transport.originalRigExport.sha256, 'Original rig export receipt retained by transport');
assert.equal(config.resumeInputs.originalInputSHA256, transport.originalRigExport.inputSHA256);
const raw = rigSource.bytes;
assert.equal(raw.readUInt32LE(0), 0x46546c67); assert.equal(raw.readUInt32LE(4), 2);
assert.equal(raw.readUInt32LE(8), raw.length);
const jsonSize = raw.readUInt32LE(12); assert.equal(raw.readUInt32LE(16), 0x4e4f534a);
const gltf = JSON.parse(raw.subarray(20, 20 + jsonSize)), binHeader = 20 + jsonSize;
assert.equal(raw.readUInt32LE(binHeader + 4), 0x004e4942);
const bin = raw.subarray(binHeader + 8);
assert.equal(bin.length, raw.readUInt32LE(binHeader));
assert(!gltf.meshes?.length && !gltf.images?.length, 'Use only the small original rig/action export');
const clips = gltf.animations.filter(row => row.name === actual.requestedClip);
assert.equal(clips.length, 1, 'Exact requested source action exists once');
const clip = clips[0], tracks = new Map(), sourceNames = new Set();
const accessor = index => {
  const row = gltf.accessors[index], view = gltf.bufferViews[row.bufferView];
  assert.equal(row.componentType, 5126); assert.equal(view.buffer, 0);
  assert(!row.sparse && !row.normalized && !view.extensions);
  const width = { SCALAR: 1, VEC3: 3, VEC4: 4 }[row.type]; assert(width);
  const result = new Float32Array(row.count * width), start = (view.byteOffset ?? 0) + (row.byteOffset ?? 0);
  for (let item = 0; item < row.count; item++) {
    for (let component = 0; component < width; component++) {
      result[item * width + component] = bin.readFloatLE(start + item * (view.byteStride ?? width * 4) + component * 4);
    }
  }
  assert([...result].every(Number.isFinite)); return result;
};
let duration = 0;
for (const channel of clip.channels) {
  const sampler = clip.samplers[channel.sampler]; assert.equal(sampler.interpolation ?? 'LINEAR', 'LINEAR');
  const node = gltf.nodes[channel.target.node], property = channel.target.path;
  assert(['translation', 'rotation', 'scale'].includes(property));
  const identity = `${node.name}/${property}`; assert(!tracks.has(identity)); sourceNames.add(node.name);
  const times = accessor(sampler.input), values = accessor(sampler.output);
  assert(times.length > 1 && times.every((value, index) => index === 0 || value > times[index - 1]));
  duration = Math.max(duration, times.at(-1));
  // These are the same installed Three.js interpolants the runtime clip uses,
  // including float32 output rounding and shortest-path quaternion SLERP.
  const Track = property === 'rotation' ? QuaternionKeyframeTrack : VectorKeyframeTrack;
  const track = new Track(identity, times, values);
  tracks.set(identity, track.createInterpolant());
}
const declaredNames = Object.values(contract.specification.jointNames);
assert.equal(new Set(declaredNames).size, 75);
assert.deepEqual([...sourceNames].sort((a, b) => a < b ? -1 : a > b ? 1 : 0), [...declaredNames].sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
assert.equal(tracks.size, 225); assert(duration > 0);
const maximum = { translationComponentM: 0, translationEuclideanM: 0,
  quaternionComponentSignInvariant: 0, quaternionAngleRadians: 0, scaleComponent: 0 };
const snapshots = [];
for (const snapshot of actual.snapshots) {
  assert.equal(snapshot.debug.stageClip, actual.requestedClip);
  assert.equal(snapshot.clipDuration, duration);
  assert(Number.isFinite(snapshot.clipTime) && snapshot.clipTime >= 0 && snapshot.clipTime < duration);
  assert.equal(snapshot.boneLocalTRS.length, 75);
  const expectedLoopTime = ((snapshot.riderStageTime % duration) + duration) % duration;
  assert.equal(snapshot.clipTime, expectedLoopTime, 'Recorded time is the exact actual runtime evaluation time');
  const seen = new Set(), bones = [];
  for (const observed of snapshot.boneLocalTRS) {
    assert(!seen.has(observed.id)); seen.add(observed.id);
    const sourceName = contract.specification.jointNames[observed.id]; assert(sourceName);
    assert.equal(observed.name, PropertyBinding.sanitizeNodeName(sourceName), 'Exact canonical/runtime node identity');
    const translation = [...tracks.get(`${sourceName}/translation`).evaluate(snapshot.clipTime)];
    const rotation = [...tracks.get(`${sourceName}/rotation`).evaluate(snapshot.clipTime)];
    const scale = [...tracks.get(`${sourceName}/scale`).evaluate(snapshot.clipTime)];
    const delta = (left, right) => left.map((value, index) => value - right[index]);
    const dt = delta(observed.translation, translation), ds = delta(observed.scale, scale);
    const minus = delta(observed.rotationXYZW, rotation);
    const plus = observed.rotationXYZW.map((value, index) => value + rotation[index]);
    const quaternionComponent = Math.min(Math.max(...minus.map(Math.abs)), Math.max(...plus.map(Math.abs)));
    const qa = observed.rotationXYZW, dot = qa.reduce((sum, value, index) => sum + value * rotation[index], 0);
    const norm = Math.hypot(...qa) * Math.hypot(...rotation); assert(norm > 0);
    const residual = { translationComponentM: Math.max(...dt.map(Math.abs)), translationEuclideanM: Math.hypot(...dt),
      quaternionComponentSignInvariant: quaternionComponent,
      quaternionAngleRadians: quaternionComponent === 0 ? 0 : 2 * Math.acos(Math.min(1, Math.abs(dot) / norm)),
      scaleComponent: Math.max(...ds.map(Math.abs)) };
    assert(Object.values(residual).every(Number.isFinite));
    for (const [key, value] of Object.entries(residual)) maximum[key] = Math.max(maximum[key], value);
    bones.push({ id: observed.id, sourceName, runtimeName: observed.name, residual,
      expected: { translation, rotationXYZW: rotation, scale },
      actual: { translation: observed.translation, rotationXYZW: observed.rotationXYZW, scale: observed.scale } });
  }
  assert.deepEqual([...seen].sort((a, b) => a < b ? -1 : a > b ? 1 : 0), Object.keys(contract.specification.jointNames).sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
  snapshots.push({ name: snapshot.name, riderStageTime: snapshot.riderStageTime, clipTime: snapshot.clipTime,
    durationSeconds: duration, bones });
}
const output = { accepted: false, status: 'MEASURED_ACTUAL_GARAGE_LOCAL_TRS_AGAINST_ORIGINAL_RIG_ACTION',
  recipeSHA256: hash(fs.readFileSync(new URL(import.meta.url))), threeRevision: REVISION,
  actualReport: { path: actualSource.path, sha256: actualSource.sha256 },
  contract: { path: contractSource.path, sha256: contractSource.sha256 },
  transport: { path: transportSource.path, sha256: transportSource.sha256 },
  transportInput: { path: configSource.path, sha256: configSource.sha256 },
  originalRigGLB: { path: rigSource.path, sha256: rigSource.sha256 },
  originalRigReceipt: { path: originalReceiptSource.path, sha256: originalReceiptSource.sha256 },
  selectedSourceSHA256: contract.glbSHA256, clip: actual.requestedClip, durationSeconds: duration,
  snapshots: snapshots.length, bonesPerSnapshot: 75, channels: tracks.size, maximumResiduals: maximum,
  observations: snapshots, acceptanceThreshold: null,
  limits: ['Read-only measurements at five actual captured times; no threshold or rider acceptance invented.',
    'CPU local bone TRS compared with original small source clip using installed Three.js interpolants.',
    'No dense GLB read, native rerender, runtime pose/time injection, or geometry/material/weight change.',
    'Continuous played appearance, GPU-skinned deformation, contacts and device release remain parent gates.'] };
const destination = path.resolve(root, arg('out')); assert(!fs.existsSync(destination), 'Use a fresh evidence output');
fs.mkdirSync(path.dirname(destination), { recursive: true });
fs.writeFileSync(destination, JSON.stringify(output, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ out: destination, clip: output.clip, maximumResiduals: maximum, acceptanceThreshold: null }));
