/** Read-only finite motion proof for named anatomical support coalescing. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Matrix4, Vector3, Quaternion, VectorKeyframeTrack, QuaternionKeyframeTrack } from 'three';
import { unzipSync } from 'three/addons/libs/fflate.module.js';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
export const COALESCE = {
  'DEF-pelvis.L': 'DEF-spine', 'DEF-pelvis.R': 'DEF-spine',
  'DEF-thigh.L.001': 'DEF-thigh.L', 'DEF-thigh.R.001': 'DEF-thigh.R',
};
const TOLERANCE = .0001;
const pins = {};
function pinned(filename) {
  const bytes = fs.readFileSync(path.join(ROOT, filename));
  pins[filename] = crypto.createHash('sha256').update(bytes).digest('hex'); return bytes;
}
function glb(filename, pin = true) {
  const fd = fs.openSync(path.join(ROOT, filename), 'r');
  const read = (start, length) => { const b = Buffer.alloc(length); assert.equal(fs.readSync(fd, b, 0, length, start), length); return b; };
  const h = read(0, 20), n = h.readUInt32LE(12); assert.equal(h.toString('ascii', 0, 4), 'glTF');
  const doc = JSON.parse(read(20, n));
  if (pin) pinned(filename);
  function accessor(index) {
    const a = doc.accessors[index], v = doc.bufferViews[a.bufferView];
    const width = { SCALAR: 1, VEC3: 3, VEC4: 4, MAT4: 16 }[a.type];
    const [size, method] = {5121: [1, 'readUInt8'], 5123: [2, 'readUInt16LE'], 5125: [4, 'readUInt32LE'], 5126: [4, 'readFloatLE']}[a.componentType];
    assert(width && !a.sparse && !a.normalized && !v.extensions);
    const stride = v.byteStride ?? size*width, raw = read(28+n+(v.byteOffset ?? 0)+(a.byteOffset ?? 0), (a.count-1)*stride+width*size);
    return Array.from({length: a.count}, (_, i) => Array.from({length: width}, (_, j) => raw[method](i*stride+j*size)));
  }
  return {doc, accessor, close: () => fs.closeSync(fd)};
}
const local = n => new Matrix4().compose(new Vector3().fromArray(n.translation ?? [0, 0, 0]),
  new Quaternion().fromArray(n.rotation ?? [0, 0, 0, 1]), new Vector3().fromArray(n.scale ?? [1, 1, 1]));
function worlds(doc, overrides = new Map()) {
  const parents = new Map(doc.nodes.flatMap((n, i) => (n.children ?? []).map(c => [c, i]))), result = new Map();
  function get(i) { if (!result.has(i)) result.set(i, (parents.has(i) ? get(parents.get(i)).clone() : new Matrix4()).multiply(local(overrides.get(i) ?? doc.nodes[i]))); return result.get(i); }
  doc.nodes.forEach((_, i) => get(i));
  return new Map(doc.nodes.map((n, i) => [n.name, result.get(i)]));
}
function npy(raw) {
  const b = Buffer.from(raw); assert.equal(b.toString('ascii', 1, 6), 'NUMPY'); assert.equal(b[6], 1);
  const offset = 10+b.readUInt16LE(8), header = b.toString('ascii', 10, offset);
  assert(header.includes("'fortran_order': False"));
  const shape = /'shape': \(([^)]*)\)/.exec(header)[1].split(',').map(s => s.trim()).filter(Boolean).map(Number);
  return {b, offset, header, shape};
}

const selectionFile = 'assets/blender/rider-rebuild/selected-seated-anatomical09/selection.json';
const selection = JSON.parse(pinned(selectionFile));
const source = glb(selection.sourcePins.glb.path, false); // Large immutable source already SHA-guarded by native author.
const skin = source.doc.skins[0], names = skin.joints.map(i => source.doc.nodes[i].name);
const binds = new Map(source.accessor(skin.inverseBindMatrices).map((m, i) => [names[i], new Matrix4().fromArray(m)]));
const ids = new Set(selection.jeans.influence.map(([id]) => id)), points = new Map();
const node = source.doc.nodes.find(n => n.name === 'RiderJeans');
for (const p of source.doc.meshes[node.mesh].primitives) {
  const ns = source.accessor(p.attributes._NATIVE_ID), ps = source.accessor(p.attributes.POSITION);
  ns.forEach(([id], i) => { if (ids.has(id)) points.set(id, ps[i]); });
}
assert.equal(points.size, ids.size);
const bounds = [0, 1, 2].map(k => [Math.min(...[...points.values()].map(p => p[k])), Math.max(...[...points.values()].map(p => p[k]))]);
const corners = Array.from({length: 8}, (_, i) => new Vector3(...bounds.map((p, k) => p[(i >> k)&1])));
const samples = [], maxima = Object.fromEntries(Object.keys(COALESCE).map(name => [name, {maximumM: 0}]));
function measure(pose, label, count) {
  const result = {label, sampleCount: count, maximumM: 0};
  const observe = (world, sample) => {
    for (const [from, to] of Object.entries(COALESCE)) {
      const a = world.get(from).clone().multiply(binds.get(from)), b = world.get(to).clone().multiply(binds.get(to));
      const value = Math.max(...corners.map(p => p.clone().applyMatrix4(a).distanceTo(p.clone().applyMatrix4(b))));
      result.maximumM = Math.max(result.maximumM, value);
      if (value > maxima[from].maximumM) maxima[from] = {maximumM: value, label, sample};
    }
  };
  pose(observe); samples.push(result);
}
for (const [folder, nativeCounts] of [
  ['harness/out/rider-rebuild/selected-garage-actions01/export01', [145, 193]],
  ['harness/out/rider-rebuild/selected-deep-crouch03/rig-export01', [217]],
]) {
  const archive = unzipSync(pinned(folder+'/native-action-matrices.npz')), ns = npy(archive['boneNames.npy']);
  const width = Number(/'descr': '<U(\d+)'/.exec(ns.header)[1]);
  const nativeNames = Array.from({length: ns.shape[0]}, (_, i) => Array.from({length: width}, (_, j) => ns.b.readUInt32LE(ns.offset+(i*width+j)*4)).filter(Boolean).map(c => String.fromCodePoint(c)).join(''));
  nativeCounts.forEach((count, index) => {
    const data = npy(archive[`pose${index}.npy`]); assert(data.header.includes("'descr': '<f8'")); assert.deepEqual(data.shape, [count, 75, 4, 4]);
    measure(observe => { for (let f = 0; f < count; f++) {
      const pose = new Map(nativeNames.map((name, i) => [name, new Matrix4().fromArray(Array.from({length: 16}, (_, k) => data.b.readDoubleLE(data.offset+((f*75+i)*16+k)*8))).transpose()]));
      observe(pose, f+1);
    } }, `native-${count}`, count);
  });
  const clip = glb(folder+'/rig-actions.glb');
  for (const action of clip.doc.animations) {
    const tracks = action.channels.map(c => {
      const s = action.samplers[c.sampler]; assert.equal(s.interpolation, 'LINEAR');
      const times = clip.accessor(s.input).flat(), values = clip.accessor(s.output).flat();
      const Track = c.target.path === 'rotation' ? QuaternionKeyframeTrack : VectorKeyframeTrack;
      return {node: c.target.node, property: c.target.path, times, interpolant: new Track('x', times, values).createInterpolant()};
    });
    const keys = [...new Set(tracks.flatMap(t => t.times))].sort((a, b) => a-b), times = keys.flatMap((t, i) => i ? [(keys[i-1]+t)/2, t] : [t]);
    measure(observe => { for (const time of times) {
      const overrides = new Map();
      for (const track of tracks) { if (!overrides.has(track.node)) overrides.set(track.node, {...clip.doc.nodes[track.node]}); overrides.get(track.node)[track.property] = [...track.interpolant.evaluate(time)]; }
      observe(worlds(clip.doc, overrides), time);
    } }, `runtime-${action.name}-keys-and-midpoints`, times.length);
  }
  clip.close();
}
for (const bike of ['rookie', 'pro']) {
  const receipt = JSON.parse(pinned(`harness/out/rider-rebuild/selected-seated-author04/authored01/${bike}.json`));
  const overrides = new Map(receipt.boneLocalTRS.map(r => [source.doc.nodes.findIndex(n => n.name === r.id), {translation: r.translation, rotation: r.rotationXYZW, scale: r.scale}]));
  measure(observe => observe(worlds(source.doc, overrides), 1), `${bike}-rejected-key`, 1);
  for (const side of ['L', 'R']) {
    const asym = new Map(overrides), root = source.doc.nodes.findIndex(n => n.name === `DEF-thigh.${side}`);
    function reset(i) { asym.set(i, source.doc.nodes[i]); for (const c of source.doc.nodes[i].children ?? []) reset(c); }
    reset(root);
    measure(observe => observe(worlds(source.doc, asym), 1), `${bike}-diagnostic-${side}-thigh-subtree-rest-not-art-pose`, 1);
  }
}
source.close();
const maximumM = Math.max(...Object.values(maxima).map(r => r.maximumM));
const out = process.argv.find(v => v.startsWith('--out='))?.slice(6); assert(out && !fs.existsSync(out));
const report = {accepted: false, status: maximumM <= TOLERANCE ? 'FINITE_SUPPORT_EQUIVALENCE_PASS' : 'FAIL',
  coalesce: COALESCE, toleranceM: TOLERANCE, maximumM, pairs: maxima, samples, sourcePins: pins,
  originalEnginePin: selection.sourcePins.glb, editedVertexCount: ids.size, selectedAABBGltf: bounds,
  proof: 'Eight AABB corners bound the norm of the affine operator difference at every enclosed mesh point. Native saved samples and runtime keys/midpoints only; not unsampled motion or art acceptance.',
  requiredFutureEnvelope: 'Motion11 must independently assert every baked key and runtime midpoint, including asymmetric legs/deep crouch. No independent pelvis-wing or thigh split twist is covered.',
};
fs.writeFileSync(out, JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify({status: report.status, maximumM, pairs: maxima, samples}));
assert.equal(report.status, 'FINITE_SUPPORT_EQUIVALENCE_PASS');
