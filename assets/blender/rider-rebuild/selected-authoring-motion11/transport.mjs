/** Parent CPU2 guard only; no Blender, renderer, server, or player-asset writes.
 * node --import tsx transport.mjs INPUT.json FRESH_OUTPUT_DIRECTORY
 * Append six successful native actions to the exact parent-selected dressed GLB.
 */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Matrix4, Quaternion, Vector3, PropertyBinding, VectorKeyframeTrack, QuaternionKeyframeTrack, REVISION } from 'three';
import { unzipSync } from 'three/addons/libs/fflate.module.js';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
const STATUS = 'UNACCEPTED_NATIVE_ACTION_LIBRARY', LIMIT = .0001;
const ACTIONS = { RiderIdle: 3, RiderWalk: 1.25, RiderJog: .75, RiderTurn90: 3, RiderJumpLand: 2.5, RiderRangeOfMotion: 12 };
const PAIRS = { 'DEF-pelvis.L': 'DEF-spine', 'DEF-pelvis.R': 'DEF-spine',
  'DEF-thigh.L.001': 'DEF-thigh.L', 'DEF-thigh.R.001': 'DEF-thigh.R' };
const C = new Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
const identity = () => new Matrix4();

async function sha(filename, range = {}) {
  const hash = crypto.createHash('sha256');
  for await (const block of fs.createReadStream(filename, range)) hash.update(block);
  return hash.digest('hex');
}
async function pin(row) {
  assert(row && /^[a-f0-9]{64}$/.test(row.sha256) && typeof row.path === 'string', 'A real file/SHA pin is required');
  const filename = path.resolve(ROOT, row.path); assert(filename.startsWith(ROOT));
  assert.equal(await sha(filename), row.sha256, `Changed input ${row.path}`); return filename;
}
async function bytes(filename, offset, count) {
  const fd = await fsp.open(filename, 'r');
  try {
    const result = Buffer.alloc(count); let done = 0;
    while (done < count) { const r = await fd.read(result, done, count - done, offset + done); assert(r.bytesRead); done += r.bytesRead; }
    return result;
  } finally { await fd.close(); }
}
async function glb(filename) {
  const head = await bytes(filename, 0, 20), size = (await fsp.stat(filename)).size;
  assert.equal(head.toString('ascii', 0, 4), 'glTF'); assert.equal(head.readUInt32LE(4), 2);
  assert.equal(head.readUInt32LE(8), size); assert.equal(head.readUInt32LE(16), 0x4e4f534a);
  const n = head.readUInt32LE(12); assert(n > 0 && n < 16 * 1024 * 1024 && n % 4 === 0);
  const document = JSON.parse(await bytes(filename, 20, n)), bin = await bytes(filename, 20 + n, 8);
  const binLength = bin.readUInt32LE(0), binOffset = 28 + n;
  assert.equal(bin.readUInt32LE(4), 0x004e4942); assert.equal(binOffset + binLength, size);
  assert.equal(document.buffers.length, 1); assert(!document.buffers[0].uri);
  assert(binLength % 4 === 0 && binLength - document.buffers[0].byteLength >= 0 && binLength - document.buffers[0].byteLength <= 3);
  return { filename, document, binOffset, binLength };
}
async function accessor(source, index) {
  const a = source.document.accessors[index], v = source.document.bufferViews[a.bufferView];
  assert(a && v && a.componentType === 5126 && !a.sparse && !a.normalized && !v.extensions && v.buffer === 0);
  const width = { SCALAR: 1, VEC3: 3, VEC4: 4, MAT4: 16 }[a.type]; assert(width && a.count > 0);
  const stride = v.byteStride ?? width * 4, offset = (v.byteOffset ?? 0) + (a.byteOffset ?? 0);
  const length = (a.count - 1) * stride + width * 4;
  assert(stride >= width * 4 && offset + length <= source.binLength);
  assert((a.byteOffset ?? 0) + length <= v.byteLength);
  const data = await bytes(source.filename, source.binOffset + offset, length);
  const values = Array.from({ length: a.count }, (_, i) => Array.from({ length: width }, (_, j) => data.readFloatLE(i * stride + j * 4)));
  assert(values.flat().every(Number.isFinite)); return values;
}
function graph(doc) {
  const names = new Map(), parents = new Map();
  doc.nodes.forEach((n, i) => { assert(n.name && !names.has(n.name)); names.set(n.name, i);
    for (const child of n.children ?? []) { assert(!parents.has(child)); parents.set(child, i); } });
  return { names, parents };
}
function local(node) {
  if (node.matrix) { assert(!node.translation && !node.rotation && !node.scale); return new Matrix4().fromArray(node.matrix); }
  return new Matrix4().compose(new Vector3().fromArray(node.translation ?? [0, 0, 0]),
    new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]), new Vector3().fromArray(node.scale ?? [1, 1, 1]));
}
function worlds(doc, g, overrides = new Map()) {
  const cache = new Map(), active = new Set();
  function get(index) {
    if (cache.has(index)) return cache.get(index); assert(!active.has(index), 'Cyclic node graph'); active.add(index);
    const matrix = (g.parents.has(index) ? get(g.parents.get(index)).clone() : identity()).multiply(local(overrides.get(index) ?? doc.nodes[index]));
    cache.set(index, matrix); active.delete(index); return matrix;
  }
  return new Map([...g.names].map(([name, index]) => [name, get(index)]));
}
function bound(a, b) {
  const delta = a.elements.map((v, i) => v - b.elements[i]);
  return 2 * Math.hypot(...[0, 1, 2, 4, 5, 6, 8, 9, 10].map(i => delta[i])) + Math.hypot(delta[12], delta[13], delta[14]);
}
function npy(raw) {
  assert(raw, 'Missing native array'); const b = Buffer.from(raw);
  assert.equal(b[0], 0x93); assert.equal(b.toString('ascii', 1, 6), 'NUMPY'); assert.equal(b[6], 1);
  const offset = 10 + b.readUInt16LE(8), header = b.toString('ascii', 10, offset);
  assert(header.includes("'fortran_order': False"));
  const shape = /'shape': \(([^)]*)\)/.exec(header)[1].split(',').map(s => s.trim()).filter(Boolean).map(Number);
  assert(shape.every(v => Number.isInteger(v) && v > 0)); return { b, offset, header, shape };
}
function nativeArrays(filename, records, names) {
  const archive = unzipSync(fs.readFileSync(filename)), ns = npy(archive['boneNames.npy']);
  const width = Number(/'descr': '<U(\d+)'/.exec(ns.header)?.[1]); assert(width > 0 && width < 256);
  assert.deepEqual(ns.shape, [75]); assert.equal(ns.b.length - ns.offset, 75 * width * 4);
  const actualNames = Array.from({ length: 75 }, (_, i) => Array.from({ length: width }, (_, j) => ns.b.readUInt32LE(ns.offset + (i * width + j) * 4))
    .filter(Boolean).map(c => String.fromCodePoint(c)).join(''));
  assert.deepEqual(actualNames, names);
  return new Map(records.map((record, index) => {
    const array = npy(archive[`pose${index}.npy`]), count = record.frameRange[1];
    assert(array.header.includes("'descr': '<f8'")); assert.deepEqual(array.shape, [count, 75, 4, 4]);
    assert.equal(array.b.length - array.offset, count * 75 * 16 * 8);
    return [record.name, frame => new Map(names.map((name, joint) => {
      const values = Array.from({ length: 16 }, (_, k) => array.b.readDoubleLE(array.offset + ((frame * 75 + joint) * 16 + k) * 8));
      assert(values.every(Number.isFinite)); return [name, C.clone().multiply(new Matrix4().fromArray(values).transpose())];
    }))];
  }));
}
function regional(world, binds, corners) {
  let maximum = 0;
  for (const [from, to] of Object.entries(PAIRS)) {
    const a = world.get(from).clone().multiply(binds.get(from)), b = world.get(to).clone().multiply(binds.get(to));
    for (const p of corners) maximum = Math.max(maximum, p.clone().applyMatrix4(a).distanceTo(p.clone().applyMatrix4(b)));
  }
  return maximum;
}
async function decodeActions(source, g, records, names) {
  assert.deepEqual(source.document.animations.map(a => a.name).sort(), Object.keys(ACTIONS).sort());
  const result = new Map();
  for (const animation of source.document.animations) {
    const record = records.find(r => r.name === animation.name), tracks = [], seen = new Set();
    for (const channel of animation.channels) {
      assert.deepEqual(Object.keys(channel.target).sort(), ['node', 'path']); assert(!channel.extensions);
      const name = source.document.nodes[channel.target.node].name, property = channel.target.path;
      assert(names.includes(name) && ['translation', 'rotation', 'scale'].includes(property));
      const key = name + '/' + property; assert(!seen.has(key)); seen.add(key);
      const sampler = animation.samplers[channel.sampler]; assert.equal(sampler.interpolation ?? 'LINEAR', 'LINEAR');
      const times = (await accessor(source, sampler.input)).flat(), values = await accessor(source, sampler.output);
      assert.equal(times.length, record.frameRange[1]); assert.equal(values.length, times.length);
      assert(times.every((t, i) => Math.abs(t - i / 24) < 5e-7));
      assert(values.every(row => row.length === (property === 'rotation' ? 4 : 3)));
      if (property === 'rotation') assert(values.every(q => Math.abs(Math.hypot(...q) - 1) < 2e-5));
      const Track = property === 'rotation' ? QuaternionKeyframeTrack : VectorKeyframeTrack;
      tracks.push({ node: channel.target.node, property, times, interpolant: new Track('probe', times, values.flat()).createInterpolant() });
    }
    assert.equal(seen.size, 225);
    const times = tracks[0].times; assert(tracks.every(t => JSON.stringify(t.times) === JSON.stringify(times)));
    result.set(animation.name, { animation, keys: times, samples: times.flatMap((t, i) => i ? [(times[i - 1] + t) / 2, t] : [t]),
      evaluate(time) {
        const overrides = new Map();
        for (const track of tracks) {
          if (!overrides.has(track.node)) overrides.set(track.node, { ...source.document.nodes[track.node] });
          overrides.get(track.node)[track.property] = [...track.interpolant.evaluate(time)];
        }
        return worlds(source.document, g, overrides);
      } });
  }
  return result;
}
async function loadedParity(filename, decoded, native, names, binds, corners, expectedRest, rawGraph, rawDocument) {
  // Actual complete dressed output through the production loader. CPU test drops
  // texture references only in memory; original on-disk images remain byte exact.
  const gltf = await loadRigAt(pathToFileURL(filename), true), bones = new Map();
  for (const name of names) {
    const found = gltf.scene.getObjectsByProperty('name', PropertyBinding.sanitizeNodeName(name));
    assert.equal(found.length, 1); assert(found[0].isBone); bones.set(name, found[0]);
  }
  gltf.scene.updateMatrixWorld(true);
  let restBound = 0, skinnedMeshes = 0;
  for (const [name, bone] of bones) {
    const rawParent = rawGraph.parents.get(rawGraph.names.get(name));
    if (rawParent !== undefined) assert.equal(bone.parent.name, PropertyBinding.sanitizeNodeName(rawDocument.nodes[rawParent].name));
    restBound = Math.max(restBound, bound(bone.matrixWorld.clone().multiply(binds.get(name)), expectedRest.get(name).clone().multiply(binds.get(name))));
  }
  assert(restBound < LIMIT, 'Loaded source rest changed');
  gltf.scene.traverse(node => {
    if (!node.isSkinnedMesh) return; skinnedMeshes++;
    assert.equal(node.skeleton.bones.length, 75);
    for (const [index, bone] of node.skeleton.bones.entries()) {
      const name = names.find(n => PropertyBinding.sanitizeNodeName(n) === bone.name); assert(name);
      assert.deepEqual(node.skeleton.boneInverses[index].elements, binds.get(name).elements, `Loaded inverse bind ${name}`);
    }
  });
  assert(skinnedMeshes >= 7, 'Actual complete dressed meshes must be loaded');
  const records = [];
  try {
    for (const [name, raw] of decoded) {
      const clip = gltf.animations.find(a => a.name === name); assert(clip); assert.equal(clip.tracks.length, 225);
      assert(Math.abs(clip.duration - ACTIONS[name]) < 1e-6);
      const tracks = clip.tracks.map(track => {
        const parsed = PropertyBinding.parseTrackName(track.name);
        const bone = [...bones.values()].find(b => b.name === parsed.nodeName); assert(bone);
        assert(['position', 'quaternion', 'scale'].includes(parsed.propertyName));
        return { bone, property: parsed.propertyName, interpolant: track.createInterpolant() };
      });
      let decodedBound = 0, nativeBound = 0, regionBound = 0, pointBound = 0;
      for (const [sample, time] of raw.samples.entries()) {
        for (const t of tracks) t.bone[t.property].fromArray(t.interpolant.evaluate(time));
        gltf.scene.updateMatrixWorld(true);
        const actual = new Map([...bones].map(([n, b]) => [n, b.matrixWorld.clone()])), wanted = raw.evaluate(time);
        const nativeKey = sample % 2 === 0 ? native.get(name)(sample / 2) : null;
        for (const n of names) {
          const skin = actual.get(n).clone().multiply(binds.get(n)), expectedSkin = wanted.get(n).clone().multiply(binds.get(n));
          decodedBound = Math.max(decodedBound, bound(skin, expectedSkin));
          for (const p of corners) pointBound = Math.max(pointBound, p.clone().applyMatrix4(skin).distanceTo(p.clone().applyMatrix4(expectedSkin)));
          if (nativeKey) nativeBound = Math.max(nativeBound, bound(skin, nativeKey.get(n).clone().multiply(binds.get(n))));
        }
        regionBound = Math.max(regionBound, regional(actual, binds, corners));
      }
      assert(Math.max(decodedBound, nativeBound, regionBound, pointBound) < LIMIT, `Loaded ${name} parity/support failed: ${decodedBound},${nativeBound},${regionBound},${pointBound}`);
      records.push({ name, keys: raw.keys.length, runtimeKeysAndMidpoints: raw.samples.length,
        loadedDecodedMaximumSkinAffineBoundWithin2mM: decodedBound, loadedNativeKeyMaximumSkinAffineBoundWithin2mM: nativeBound,
        all75LoadedDecodedCornerMaximumM: pointBound, loadedRegionalCornerMaximumM: regionBound });
    }
  } finally {
    const geometry = new Set(), materials = new Set();
    gltf.scene.traverse(n => { if (n.geometry) geometry.add(n.geometry); for (const m of Array.isArray(n.material) ? n.material : n.material ? [n.material] : []) materials.add(m); });
    for (const g of geometry) g.dispose(); for (const m of materials) m.dispose();
  }
  return { skinnedMeshes, original75RestMaximumSkinAffineBoundWithin2mM: restBound,
    original75NamedHierarchyAndInverseBindsExact: true, actions: records };
}

async function main() {
  assert.equal(process.argv.length, 4, 'transport.mjs INPUT.json FRESH_OUTPUT_DIRECTORY');
  const inputPath = path.resolve(process.argv[2]), input = JSON.parse(await fsp.readFile(inputPath));
  const out = path.resolve(process.argv[3]); assert(out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-authoring-motion11/')) && !fs.existsSync(out));
  assert(input.ready === true && input.accepted === false && input.previewClip === 'RiderIdle');
  assert.deepEqual(input.presentationOffsetBike, [-.6, -.34, .65]);
  assert.equal(await sha(fileURLToPath(import.meta.url)), input.recipeSHA256);
  const required = ['sourceGLB', 'sourceContract', 'nativeReceipt', 'nativeMatrices', 'rigGLB', 'controlNative', 'bakedNative', 'nativeContract', 'regionalEnvelope', 'loader', 'packageLock'];
  assert.deepEqual(Object.keys(input.pins).sort(), required.sort());
  const files = {}; for (const [name, p] of Object.entries(input.pins)) files[name] = await pin(p);
  assert.equal(files.loader, path.join(ROOT, 'src/render/hero/gltfTestUtils.ts')); assert.equal(files.packageLock, path.join(ROOT, 'pnpm-lock.yaml'));
  const receipt = JSON.parse(await fsp.readFile(files.nativeReceipt)), contract = JSON.parse(await fsp.readFile(files.sourceContract));
  const nativeContract = JSON.parse(await fsp.readFile(files.nativeContract));
  assert(receipt.accepted === false && receipt.status === 'NATIVE_CONTROL_ACTION_PACKAGE_UNACCEPTED', 'Successful native construction receipt required');
  for (const key of ['controlNative', 'bakedNative', 'rigGLB']) assert.deepEqual(receipt[key], input.pins[key]);
  assert.deepEqual(receipt.source.contract, input.pins.nativeContract);
  assert.equal(path.dirname(files.nativeMatrices), path.dirname(files.nativeReceipt));
  assert.equal(path.basename(files.nativeMatrices), 'native-action-matrices.npz');
  assert(receipt.sourceRestResidualM < LIMIT && receipt.neutralMaximumAffineBoundWithin2mM < LIMIT);
  assert.equal(receipt.neutral75BeforeActions.length, 75);
  assert(receipt.neutral75BeforeActions.every(r => r.affineDisplacementBoundWithin2mM < LIMIT));
  assert(receipt.addedRestBeforeConstraints.length > 0 && receipt.addedRestBeforeConstraints.every(r => Math.max(r.affineDisplacementBoundWithin2mM, r.lengthResidualM) < LIMIT));
  assert.deepEqual(receipt.actions.map(a => a.name).sort(), Object.keys(ACTIONS).sort());
  for (const r of receipt.actions) {
    assert.equal(r.fps, 24); assert.equal(r.seconds, ACTIONS[r.name]); assert.deepEqual(r.frameRange, [1, Math.round(r.seconds * 24) + 1]);
    assert(Math.max(r.soleTargetMaximumM, r.regionalOperatorBoundWithin2mM, r.bakeMaximumAffineBoundWithin2mM) < LIMIT);
  }
  assert.equal(contract.glbSHA256, input.pins.sourceGLB.sha256); assert.deepEqual(contract.nativeRest, nativeContract.nativeRest);
  const names = contract.nativeRest.bones.map(b => b.name); assert.equal(new Set(names).size, 75);
  const base = await glb(files.sourceGLB), small = await glb(files.rigGLB), bg = graph(base.document), sg = graph(small.document);
  assert.equal(base.document.skins.length, 1); assert.equal(small.document.skins.length, 1);
  assert(!small.document.extensionsRequired?.length);
  for (const key of ['meshes', 'materials', 'images', 'textures']) assert(!small.document[key]?.length, 'Rig-only export contains appearance');
  assert.deepEqual([...sg.names.keys()].sort(), [...names, 'RiderSkeleton'].sort());
  assert(base.document.images?.length > 0 && base.document.textures?.length > 0 && base.document.materials?.length > 0);
  for (const role of ['RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R']) {
    assert(Object.values(contract.specification.meshNames).includes(role) && bg.names.has(role), `Complete selected outfit role ${role}`);
  }
  const bs = base.document.skins[0], ss = small.document.skins[0];
  for (const [source, skin] of [[base, bs], [small, ss]]) {
    assert.equal(skin.joints.length, 75); assert.deepEqual(skin.joints.map(i => source.document.nodes[i].name).sort(), [...names].sort());
  }
  const baseBinds = await accessor(base, bs.inverseBindMatrices), smallBinds = await accessor(small, ss.inverseBindMatrices);
  const binds = new Map(bs.joints.map((node, i) => [base.document.nodes[node].name, new Matrix4().fromArray(baseBinds[i])]));
  ss.joints.forEach((node, i) => assert.deepEqual(smallBinds[i], binds.get(small.document.nodes[node].name).toArray(), 'Named inverse bind changed'));
  const baseWorlds = worlds(base.document, bg), rigWorlds = worlds(small.document, sg); let restBound = 0, nativeRestBound = 0;
  for (const [name, index] of sg.names) {
    const target = bg.names.get(name); assert(target !== undefined);
    const parent = sg.parents.has(index) ? small.document.nodes[sg.parents.get(index)].name : null;
    const targetParent = bg.parents.has(target) ? base.document.nodes[bg.parents.get(target)].name : null;
    assert.equal(parent, targetParent, `Exact hierarchy ${name}`);
    const inverse = binds.get(name) ?? identity();
    restBound = Math.max(restBound, bound(rigWorlds.get(name).clone().multiply(inverse), baseWorlds.get(name).clone().multiply(inverse)));
  }
  assert(restBound < LIMIT, `Serialized source rest physical mismatch ${restBound}`);
  for (const bone of nativeContract.nativeRest.bones) {
    const index = bg.names.get(bone.name), parent = bg.parents.get(index);
    assert.equal(base.document.nodes[parent]?.name, bone.parent ?? 'RiderSkeleton', `Native hierarchy ${bone.name}`);
    const nativeRest = C.clone().multiply(new Matrix4().fromArray(bone.matrix.flat()).transpose());
    nativeRestBound = Math.max(nativeRestBound, bound(baseWorlds.get(bone.name).clone().multiply(binds.get(bone.name)), nativeRest.multiply(binds.get(bone.name))));
  }
  assert(nativeRestBound < LIMIT, `Original 75 native rest mismatch ${nativeRestBound}`);
  const envelope = JSON.parse(await fsp.readFile(files.regionalEnvelope)); assert.deepEqual(envelope.coalesce, PAIRS);
  assert.equal(envelope.status, 'FINITE_SUPPORT_EQUIVALENCE_PASS'); assert.equal(envelope.toleranceM, LIMIT);
  const bounds = envelope.selectedAABBGltf; assert(bounds.length === 3 && bounds.every(r => r.length === 2 && r.every(Number.isFinite) && r[0] < r[1]));
  const corners = Array.from({ length: 8 }, (_, i) => new Vector3(...bounds.map((r, k) => r[(i >> k) & 1])));
  const native = nativeArrays(files.nativeMatrices, receipt.actions, names), decoded = await decodeActions(small, sg, receipt.actions, names), rawChecks = [];
  for (const [name, action] of decoded) {
    let nativeBound = 0, nativeRegion = 0, runtimeRegion = 0;
    for (const [frame, time] of action.keys.entries()) {
      const wanted = native.get(name)(frame), actual = action.evaluate(time);
      for (const n of names) nativeBound = Math.max(nativeBound, bound(actual.get(n).clone().multiply(binds.get(n)), wanted.get(n).clone().multiply(binds.get(n))));
      nativeRegion = Math.max(nativeRegion, regional(wanted, binds, corners));
    }
    for (const time of action.samples) runtimeRegion = Math.max(runtimeRegion, regional(action.evaluate(time), binds, corners));
    assert(Math.max(nativeBound, nativeRegion, runtimeRegion) < LIMIT, `Raw ${name} native/support mismatch`);
    rawChecks.push({ name, nativeKeySkinAffineBoundWithin2mM: nativeBound, nativeKeyRegionalMaximumM: nativeRegion, runtimeRegionalMaximumM: runtimeRegion });
  }
  const merged = structuredClone(base.document), oldViews = merged.bufferViews.length, oldAccessors = merged.accessors.length;
  const oldAnimations = merged.animations?.length ?? 0; merged.animations ??= [];
  assert(!merged.animations.some(a => ACTIONS[a.name]), 'Refuse duplicate action names');
  const accessorIDs = new Set([...decoded.values()].flatMap(a => a.animation.samplers.flatMap(s => [s.input, s.output])));
  const viewIDs = [...new Set([...accessorIDs].map(i => small.document.accessors[i].bufferView))].sort((a, b) => a - b);
  const viewMap = new Map(), accessorMap = new Map(), chunks = []; let length = base.binLength;
  for (const i of viewIDs) {
    const view = small.document.bufferViews[i]; assert(view.buffer === 0 && !view.extensions && view.byteLength % 4 === 0);
    viewMap.set(i, merged.bufferViews.length); merged.bufferViews.push({ ...structuredClone(view), byteOffset: length });
    chunks.push(await bytes(small.filename, small.binOffset + (view.byteOffset ?? 0), view.byteLength)); length += view.byteLength;
  }
  for (const i of [...accessorIDs].sort((a, b) => a - b)) {
    const a = small.document.accessors[i]; assert(!a.sparse && viewMap.has(a.bufferView));
    accessorMap.set(i, merged.accessors.length); merged.accessors.push({ ...structuredClone(a), bufferView: viewMap.get(a.bufferView) });
  }
  for (const { animation } of decoded.values()) {
    const copy = structuredClone(animation);
    for (const s of copy.samplers) { s.input = accessorMap.get(s.input); s.output = accessorMap.get(s.output); }
    for (const c of copy.channels) c.target.node = bg.names.get(small.document.nodes[c.target.node].name);
    merged.animations.push(copy);
  }
  merged.buffers[0].byteLength = length;
  for (const [key, value] of Object.entries(base.document)) if (!['buffers', 'bufferViews', 'accessors', 'animations'].includes(key)) assert.deepEqual(merged[key], value);
  assert.deepEqual(merged.bufferViews.slice(0, oldViews), base.document.bufferViews); assert.deepEqual(merged.accessors.slice(0, oldAccessors), base.document.accessors);
  assert.deepEqual(merged.animations.slice(0, oldAnimations), base.document.animations ?? []);
  const json = Buffer.from(JSON.stringify(merged)), padded = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]);
  const header = Buffer.alloc(20), binHeader = Buffer.alloc(8); header.write('glTF'); header.writeUInt32LE(2, 4);
  header.writeUInt32LE(28 + padded.length + length, 8); header.writeUInt32LE(padded.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  binHeader.writeUInt32LE(length); binHeader.writeUInt32LE(0x004e4942, 4);
  await fsp.mkdir(out, { recursive: true }); const target = path.join(out, 'rider.glb');
  await fsp.writeFile(target, Buffer.concat([header, padded, binHeader]), { flag: 'wx' });
  await pipeline(fs.createReadStream(base.filename, { start: base.binOffset, end: base.binOffset + base.binLength - 1 }), fs.createWriteStream(target, { flags: 'a' }));
  for (const chunk of chunks) await fsp.appendFile(target, chunk);
  const originalBIN = await sha(base.filename, { start: base.binOffset, end: base.binOffset + base.binLength - 1 });
  const readback = await glb(target); assert.deepEqual(readback.document, merged);
  assert.equal(await sha(target, { start: readback.binOffset, end: readback.binOffset + base.binLength - 1 }), originalBIN);
  assert.equal(await sha(target, { start: readback.binOffset + base.binLength, end: readback.binOffset + length - 1 }),
    crypto.createHash('sha256').update(Buffer.concat(chunks)).digest('hex'));
  const loaderChecks = await loadedParity(target, decoded, native, names, binds, corners, baseWorlds, bg, base.document), outputSHA = await sha(target);
  const actions = Object.fromEntries(receipt.actions.map(r => [r.name, { name: r.name, fps: 24, frameRange: r.frameRange,
    durationSeconds: r.seconds, channels: 225, sampleCountPerChannel: r.frameRange[1], sourceSlot: r.bakedSlot,
    loop: r.name === 'RiderIdle', playback: r.name === 'RiderIdle' ? 'LOOP' : 'ONCE', leadInSeconds: 2,
    rootForwardM: r.rootForwardM, authoredCycle: r.loop, sourceControlAction: r.controlAction }]));
  const originalContract = structuredClone(contract), priorQualification = contract.qualificationState ?? null;
  contract.accepted = false; contract.glbSHA256 = contract.sourceSHA256 = outputSHA; contract.previewClip = input.previewClip;
  contract.genericActions = { ...contract.genericActions, ...actions }; contract.qualificationState = STATUS;
  contract.nativeAuthoringMotion = { accepted: false, kind: 'native-control-action-library',
    sourcePins: { nativeReceipt: input.pins.nativeReceipt, controlNative: input.pins.controlNative, bakedNative: input.pins.bakedNative,
      rigGLB: input.pins.rigGLB, nativeMatrices: input.pins.nativeMatrices, selectedRider: input.pins.sourceGLB, selectedContract: input.pins.sourceContract },
    actions: structuredClone(receipt.actions), priorQualification,
    presentation: { positionBike: input.presentationOffsetBike,
      meaning: 'Generic action inspection beside bike using existing standing-clip Garage presentation; not normal Garage seated riding' },
    playbackEpoch: 'First native rendered stage update after the selected rider is ready; reset on stage entry',
    regionalEnvelope: input.pins.regionalEnvelope, normalPlayerPromotionAllowed: false,
    limits: ['Successful native construction and exact dressed action transport only; complete played art, contact, GPU and device acceptance remain open.',
      'Native keys compared independently. Runtime midpoint checks prove decoded/loaded interpolation and regional support, not Blender subframe F-curve identity.',
      'Walk/jog play once with authored root displacement; repeating requires separately implemented accumulated root motion.',
      'Loader test omits textures in CPU memory only; full selected on-disk meshes, weights, maps and image bytes are preserved.'] };
  for (const [key, value] of Object.entries(originalContract)) {
    if (!['accepted', 'glbSHA256', 'sourceSHA256', 'previewClip', 'genericActions', 'qualificationState'].includes(key)) assert.deepEqual(contract[key], value, `Base contract preserved ${key}`);
  }
  const contractPath = path.join(out, 'rider-contract.json');
  await fsp.writeFile(contractPath, JSON.stringify(contract, null, 2) + '\n', { flag: 'wx' });
  const report = { accepted: false, status: STATUS, sourcePins: input.pins, recipeSHA256: input.recipeSHA256,
    input: { path: path.relative(ROOT, inputPath), sha256: await sha(inputPath) },
    glb: { path: path.relative(ROOT, target), sha256: outputSHA }, contract: { path: path.relative(ROOT, contractPath), sha256: await sha(contractPath) },
    nativeRestExactlySame: true, namedInverseBindsExactlySame: true, originalHierarchyExactlySame: true, serializedRestMaximumSkinAffineBoundWithin2mM: restBound,
    sourceNativeRestMaximumSkinAffineBoundWithin2mM: nativeRestBound,
    originalBINBytes: base.binLength, originalBINSHA256: originalBIN, originalJSONAndAccessorPrefixesExact: true,
    appendedActionPayloadBytes: length - base.binLength, existingAnimationsPreserved: oldAnimations,
    actions, rawChecks, loaderChecks, regionalEnvelopePin: input.pins.regionalEnvelope,
    actualDressedProductionLoader: true, threeRevision: REVISION, actualGaragePlayed: false, nativeGpuParity: 'UNMEASURED', deviceAcceptance: 'UNMEASURED' };
  for (const p of Object.values(input.pins)) await pin(p);
  await fsp.writeFile(path.join(out, 'transport.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: STATUS, glb: report.glb, contract: report.contract, rawChecks, loaderChecks }));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
