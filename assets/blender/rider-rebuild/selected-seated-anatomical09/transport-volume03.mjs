/** Parent CPU2 only: append fresh native sculpt03 morphs to exact transport02.
 * node --import tsx transport-volume03.mjs --input=PINNED.json --out=FRESH
 * Source-only imports perform no native/model reads and launch no work.
 */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { AnimationMixer, LoopOnce, BufferGeometry, Float32BufferAttribute, Matrix4, Quaternion, Vector3, PropertyBinding, REVISION } from 'three';
import { unzipSync } from 'three/addons/libs/fflate.module.js';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { appendAnimation, rigIdentity, TIMES } from '../selected-seated-diagnostic08/append-clip.mjs';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
const BASE = 'harness/out/rider-rebuild/selected-seated-anatomical09/';
export const KEY = 'A09_SeatedVolume', CLIP = 'Anatomical09VolumeRestKey', STATUS = 'UNACCEPTED_POSED_VOLUME';
const OBJECTS = ['RiderBody', 'RiderJeans'], LIMIT = .0001;
const FIXED = {
  weightRider: { path: BASE+'transport02/rider.glb', sha256: 'ff9d78e2c5c40a4be1218b57611c5e71db10a2de7b636ec1589358176f907a0f' },
  weightContract: { path: BASE+'transport02/rider-contract.json', sha256: '98fc88c05d2ae45112f94aed28704a02867513bd10483fd86fdc5d60b03558ba' },
  weightReceipt: { path: BASE+'transport02/transport.json', sha256: '0497acb5edf34ca37e6d97b90bac51aaebe47920441568096778d895462166c5' },
};
async function sha(filename, range = {}) {
  const hash = crypto.createHash('sha256');
  for await (const block of fs.createReadStream(filename, range)) hash.update(block);
  return hash.digest('hex');
}
export function validateManifest(input) {
  assert.equal(input.accepted, false);
  assert.deepEqual(Object.keys(input).sort(), ['accepted', 'pins']);
  assert.deepEqual(Object.keys(input.pins).sort(), [...Object.keys(FIXED), 'native', 'nativeReceipt', 'shapeKey', 'posedSurfaces'].sort());
  for (const [name, pin] of Object.entries(input.pins)) {
    assert.deepEqual(Object.keys(pin).sort(), ['path', 'sha256']);
    assert(/^[a-f0-9]{64}$/.test(pin.sha256) && typeof pin.path === 'string');
    assert(!pin.path.includes('..') && !path.isAbsolute(pin.path));
    if (FIXED[name]) assert.deepEqual(pin, FIXED[name]);
    else assert(pin.path.startsWith(BASE+'sculpted03/'), 'Only actual fresh sculpt03 output is permitted');
  }
  for (const [name, filename] of Object.entries({ native: 'selected-anatomical09-posed-volume.blend', nativeReceipt: 'receipt.json', shapeKey: 'shape-key.json', posedSurfaces: 'posed-surface-samples.npz' })) {
    assert.equal(input.pins[name].path, BASE+'sculpted03/'+filename);
  }
  return input.pins;
}
async function checkPins(pins) {
  for (const pin of Object.values(pins)) assert.equal(await sha(path.join(ROOT, pin.path)), pin.sha256, pin.path);
}
async function bytes(filename, offset, count) {
  const fd = await fsp.open(filename, 'r');
  try {
    const data = Buffer.alloc(count); let done = 0;
    while (done < count) { const row = await fd.read(data, done, count-done, offset+done); assert(row.bytesRead); done += row.bytesRead; }
    return data;
  } finally { await fd.close(); }
}
async function glb(filename) {
  const h = await bytes(filename, 0, 20); assert.equal(h.toString('ascii', 0, 4), 'glTF');
  assert.equal(h.readUInt32LE(4), 2); assert.equal(h.readUInt32LE(16), 0x4e4f534a);
  const length = h.readUInt32LE(12); assert(length > 0 && length < 16*1024*1024 && length%4 === 0);
  const document = JSON.parse(await bytes(filename, 20, length)), bh = await bytes(filename, 20+length, 8);
  const binLength = bh.readUInt32LE(0), binOffset = 28+length;
  assert.equal(bh.readUInt32LE(4), 0x004e4942); assert.equal(binOffset+binLength, h.readUInt32LE(8));
  assert.equal((await fsp.stat(filename)).size, h.readUInt32LE(8));
  assert.equal(document.buffers.length, 1); assert(!document.buffers[0].uri && binLength%4 === 0);
  assert(binLength-document.buffers[0].byteLength >= 0 && binLength-document.buffers[0].byteLength <= 3);
  return { filename, document, binLength, binOffset };
}
async function accessor(source, index) {
  const a = source.document.accessors[index], v = source.document.bufferViews[a.bufferView];
  const width = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }[a.type];
  const [size, method] = { 5121: [1, 'readUInt8'], 5123: [2, 'readUInt16LE'], 5125: [4, 'readUInt32LE'], 5126: [4, 'readFloatLE'] }[a.componentType] ?? [];
  assert(width && size && !a.sparse && !a.normalized && !v.extensions && v.buffer === 0);
  const stride = v.byteStride ?? width*size, offset = a.byteOffset ?? 0, length = (a.count-1)*stride+width*size;
  assert(a.count > 0 && stride >= width*size && offset+length <= v.byteLength);
  assert((v.byteOffset ?? 0)+offset+length <= source.binLength);
  const raw = await bytes(source.filename, source.binOffset+(v.byteOffset ?? 0)+offset, length);
  const rows = Array.from({ length: a.count }, (_, i) => Array.from({ length: width }, (_, k) => raw[method](i*stride+k*size)));
  assert(rows.every(row => row.every(Number.isFinite))); return rows;
}

/** Preserve authored split normals while rotating by the actual face-field change.
 * Same primitive index/UV/native-ID topology; untouched one-rings yield zero.
 * This is a shading construction, not native custom-normal/GPU parity proof.
 */
export function morphFields(ids, positions, normals, indices, rows, tangents = null) {
  assert.equal(ids.length, positions.length); assert.equal(ids.length, normals.length);
  const moved = new Map();
  for (const row of rows) {
    assert(Number.isInteger(row.nativeID) && row.nativeID >= 0 && !moved.has(row.nativeID));
    assert(row.deltaGLTF.length === 3 && row.deltaGLTF.every(Number.isFinite));
    assert.deepEqual(row.deltaGLTF, [row.deltaBlender[0], row.deltaBlender[2], -row.deltaBlender[1]]);
    moved.set(row.nativeID, row.deltaGLTF.map(Math.fround));
  }
  const delta = ids.flatMap(id => moved.get(id) ?? [0, 0, 0]), flat = positions.flat();
  const before = new BufferGeometry(), after = new BufferGeometry();
  before.setAttribute('position', new Float32BufferAttribute(flat, 3)); before.setIndex(indices);
  after.setAttribute('position', new Float32BufferAttribute(flat.map((v, i) => v+delta[i]), 3)); after.setIndex(indices);
  before.computeVertexNormals(); after.computeVertexNormals();
  const normal = [], tangent = tangents ? [] : null; let maximumNormalRotationRadians = 0;
  for (let i = 0; i < ids.length; i++) {
    const a = new Vector3().fromBufferAttribute(before.attributes.normal, i), b = new Vector3().fromBufferAttribute(after.attributes.normal, i);
    const rotation = new Quaternion();
    if (a.lengthSq() && b.lengthSq()) rotation.setFromUnitVectors(a.normalize(), b.normalize());
    else assert.equal(a.lengthSq(), b.lengthSq(), 'Shape created or removed a degenerate normal');
    maximumNormalRotationRadians = Math.max(maximumNormalRotationRadians, rotation.angleTo(new Quaternion()));
    const authored = new Vector3().fromArray(normals[i]);
    normal.push(...authored.clone().applyQuaternion(rotation).sub(authored).toArray());
    if (tangent) { const t = new Vector3().fromArray(tangents[i]); tangent.push(...t.clone().applyQuaternion(rotation).sub(t).toArray()); }
  }
  before.dispose(); after.dispose();
  return { POSITION: delta, NORMAL: normal, ...(tangent ? { TANGENT: tangent } : {}), maximumNormalRotationRadians };
}
function surfaceArrays(filename) {
  const archive = unzipSync(fs.readFileSync(filename)), result = {};
  for (const bike of ['rookie', 'pro']) for (const frame of [1, 31, 61]) for (const name of OBJECTS) {
    const key = `${bike}_${frame}_${name}`, b = Buffer.from(archive[key+'.npy'] ?? []);
    assert.equal(b[0], 0x93); assert.equal(b.toString('ascii', 1, 6), 'NUMPY'); assert.equal(b[6], 1);
    const offset = 10+b.readUInt16LE(8), header = b.toString('ascii', 10, offset);
    assert(header.includes("'fortran_order': False"));
    const size = header.includes("'descr': '<f4'") ? 4 : header.includes("'descr': '<f8'") ? 8 : 0;
    assert(size, 'Native position arrays must be little-endian float32 or float64');
    const shape = /'shape': \(([^)]*)\)/.exec(header)[1].split(',').map(s => s.trim()).filter(Boolean).map(Number);
    assert(shape.length === 2 && shape[1] === 3 && shape[0] > 0); assert.equal(b.length-offset, shape[0]*3*size);
    result[key] = { count: shape[0], get: id => {
      assert(Number.isInteger(id) && id >= 0 && id < shape[0]);
      const p = [0, 1, 2].map(k => b[size === 4 ? 'readFloatLE' : 'readDoubleLE'](offset+(id*3+k)*size)); assert(p.every(Number.isFinite)); return p;
    } };
  }
  return result;
}
function operatorPosition(mesh, row) {
  const a = mesh.geometry.attributes, point = new Vector3().fromBufferAttribute(a.position, row);
  point.addScaledVector(new Vector3().fromBufferAttribute(mesh.geometry.morphAttributes.position[0], row), mesh.morphTargetInfluences[0]).applyMatrix4(mesh.bindMatrix);
  const result = new Vector3(), skin = new Matrix4();
  for (let k = 0; k < 4; k++) {
    const slot = a.skinIndex.getComponent(row, k), weight = a.skinWeight.getComponent(row, k);
    if (!weight) continue;
    skin.multiplyMatrices(mesh.skeleton.bones[slot].matrixWorld, mesh.skeleton.boneInverses[slot]);
    result.addScaledVector(point.clone().applyMatrix4(skin), weight);
  }
  return result.applyMatrix4(mesh.bindMatrixInverse).applyMatrix4(mesh.matrixWorld);
}
async function loadedProbe(filename, source, surfaces, authors, primitiveRows) {
  const loaded = await loadRigAt(pathToFileURL(filename), true), clip = loaded.animations.find(a => a.name === CLIP);
  assert(clip && clip.duration === 6); assert.equal(clip.tracks.filter(t => t.name.endsWith('.morphTargetInfluences')).length, 5);
  const meshes = [];
  for (const name of OBJECTS) loaded.scene.getObjectByName(name).traverse(mesh => {
    if (!mesh.isMesh) return; assert(mesh.isSkinnedMesh); meshes.push({ name, mesh });
    assert.deepEqual(mesh.morphTargetDictionary, { [KEY]: 0 });
    assert.equal(mesh.geometry.morphTargetsRelative, true);
    assert.equal(mesh.geometry.morphAttributes.position.length, 1); assert.equal(mesh.geometry.morphAttributes.normal.length, 1);
  });
  assert.equal(meshes.length, 5); assert.equal(meshes.reduce((n, {mesh}) => n+mesh.geometry.attributes.position.count, 0), primitiveRows);
  const rests = new Map(); loaded.scene.traverse(n => { if (n.isBone) rests.set(n.name, { p: n.position.clone(), q: n.quaternion.clone(), s: n.scale.clone() }); });
  const mixer = new AnimationMixer(loaded.scene), action = mixer.clipAction(clip); action.setLoop(LoopOnce, 1); action.clampWhenFinished = true; action.play();
  const samples = [], restBytes = new Map();
  const measure = (bike, stage, expectedWeight, frame) => {
    loaded.scene.updateMatrixWorld(true); const records = [];
    for (const { name, mesh } of meshes) {
      mesh.skeleton.update(); assert.equal(mesh.morphTargetInfluences[0], expectedWeight);
      const ids = mesh.geometry.attributes._native_id, points = Buffer.alloc(ids.count*24); let maximumNativeResidualM = 0, maximumOperatorResidualM = 0;
      for (let row = 0; row < ids.count; row++) {
        const actual = mesh.getVertexPosition(row, new Vector3()).applyMatrix4(mesh.matrixWorld);
        const independent = operatorPosition(mesh, row), operatorResidual = actual.distanceTo(independent);
        maximumOperatorResidualM = Math.max(maximumOperatorResidualM, operatorResidual); assert(operatorResidual < 1e-10);
        [actual.x, actual.y, actual.z].forEach((v, k) => points.writeDoubleLE(v, (row*3+k)*8));
        if (frame) {
          const target = surfaces[`${bike}_${frame}_${name}`].get(ids.getX(row));
          const native = [actual.x, -actual.z, actual.y], residual = Math.hypot(...native.map((v, k) => v-target[k]));
          maximumNativeResidualM = Math.max(maximumNativeResidualM, residual);
          assert(residual <= LIMIT, `${bike}/${stage}/${name}/${ids.getX(row)} native residual ${residual}`);
        }
      }
      const restKey = `${bike}/${mesh.uuid}`;
      if (stage === 'rest') restBytes.set(restKey, points);
      if (stage === 'return') assert(points.equals(restBytes.get(restKey)), `${bike}/${name} actual loaded rest/return differs`);
      records.push({ object: name, primitive: mesh.name, primitiveRows: ids.count, morphWeight: mesh.morphTargetInfluences[0], maximumNativeResidualM: frame ? maximumNativeResidualM : null, maximumOperatorResidualM,
        positionsSHA256: crypto.createHash('sha256').update(points).digest('hex') });
    }
    samples.push({ bike, stage, nativeFrame: frame ?? null, records });
  };
  for (const [time, stage, weight, frame] of [[0, 'rest', 0, 1], [1.5, 'ramp-up', .5], [2, 'key', 1, 31], [4.5, 'ramp-down', .5], [5, 'return', 0, 61], [6, 'end', 0, 61]]) {
    mixer.setTime(time); measure('rookie', stage, weight, frame);
  }
  action.stop();
  for (const [stage, frame] of [['rest', 1], ['key', 31], ['return', 61]]) {
    for (const [name, rest] of rests) { const bone = loaded.scene.getObjectByName(name); bone.position.copy(rest.p); bone.quaternion.copy(rest.q); bone.scale.copy(rest.s); }
    if (stage === 'key') for (const row of authors.pro.boneLocalTRS) {
      const bone = loaded.scene.getObjectByName(PropertyBinding.sanitizeNodeName(row.id)); assert(bone?.isBone);
      bone.position.fromArray(row.translation.map(Math.fround)); bone.quaternion.fromArray(row.rotationXYZW.map(Math.fround)); bone.scale.fromArray(row.scale.map(Math.fround));
    }
    for (const {mesh} of meshes) mesh.morphTargetInfluences[0] = stage === 'key' ? 1 : 0;
    measure('pro', stage, stage === 'key' ? 1 : 0, frame);
  }
  mixer.uncacheRoot(loaded.scene);
  return { accepted: false, threeRevision: REVISION, primitiveCount: meshes.length, samples, actualLoaderRestKeyReturn: true,
    actualFloat32ClipAndMorphs: true, restReturnByteIdentical: true, allExportedBodyJeansRowsChecked: true,
    independentLoadedSkinOperatorToleranceM: 1e-10, nativeEndpointToleranceM: LIMIT,
    nativeMidpointParity: 'UNMEASURED: native skeletal curves differ from this endpoint LINEAR clip',
    gpuVertexReadback: 'UNMEASURED', tangentMorphLoaderSupport: false,
    sourceBinaryBytes: source.binLength };
}

async function main() {
  const arg = name => process.argv.find(v => v.startsWith(`--${name}=`))?.slice(name.length+3);
  assert(arg('input') && arg('out')); const inputPath = path.resolve(arg('input')), out = path.resolve(arg('out'));
  assert(out.startsWith(path.resolve(ROOT, BASE)+path.sep) && !fs.existsSync(out), 'Fresh ignored output only');
  const input = JSON.parse(await fsp.readFile(inputPath, 'utf8')), pins = validateManifest(input); await checkPins(pins);
  const read = async pin => JSON.parse(await fsp.readFile(path.join(ROOT, pin.path), 'utf8'));
  const [contract, weightReport, native, shape] = await Promise.all(['weightContract', 'weightReceipt', 'nativeReceipt', 'shapeKey'].map(k => read(pins[k])));
  assert.equal(contract.accepted, false); assert.equal(contract.qualificationState, 'UNACCEPTED_WEIGHT_INTERVENTION');
  assert.equal(contract.glbSHA256, pins.weightRider.sha256); assert.deepEqual(weightReport.glb, pins.weightRider); assert.deepEqual(weightReport.contract, pins.weightContract);
  assert.deepEqual(contract.weightDerivative, weightReport.derivative); assert(!contract.corrective && !contract.shapeDerivative);
  assert.equal(native.accepted, false); assert.equal(native.shapeKey, KEY); assert.equal(native.basisWeightsRestUVMapsExact, true); assert.deepEqual(native.native, pins.native);
  assert.equal(native.status, 'UNACCEPTED_POSED_VOLUME_CONTACT_AND_MOVING_REVIEW_PENDING');
  assert.deepEqual(native.shapeAnimation.frames, [1, 31, 61]); assert.deepEqual(native.shapeAnimation.values, [0, 1, 0]); assert.equal(native.shapeAnimation.interpolation, 'LINEAR');
  assert.equal(shape.accepted, false); assert.equal(shape.relative, true); assert.equal(shape.name, KEY);
  assert.deepEqual(Object.keys(shape.deltas).sort(), [...OBJECTS].sort());
  assert.deepEqual(shape.sourceNative, contract.weightDerivative.native); assert.deepEqual(shape.sourceWeights, contract.weightDerivative.nativeReceipt);
  assert.deepEqual(native.sourcePins.native, shape.sourceNative); assert.deepEqual(native.sourcePins.nativeReceipt, shape.sourceWeights);
  assert.deepEqual(native.posePin, shape.posePin); assert.deepEqual(shape.posePin, contract.diagnosticMotion.sourcePins.author);
  await checkPins(native.sourcePins);
  assert.equal(await sha(path.join(ROOT, 'assets/blender/rider-rebuild/selected-seated-anatomical09/sculpt03.py')), native.recipeSHA256);
  assert.equal(await sha(path.join(ROOT, 'assets/blender/rider-rebuild/selected-seated-anatomical09/sculpt03.input.json')), native.inputSHA256);
  for (const name of OBJECTS) {
    assert.equal(shape.deltas[name].length, native.movedVertices[name]);
    assert(native.inverseChecks[name].sourceAffineM < .000002 && native.inverseChecks[name].posedTargetM < .000003 && native.inverseChecks[name].maximumInverseCondition < 50);
    assert(native.reopenedResidualM[name] < 1e-8);
  }
  const weightNative = await read(contract.weightDerivative.nativeReceipt), authors = {};
  for (const bike of ['rookie', 'pro']) { const pin = weightNative.diagnosticPoses[bike]; await checkPins({ [bike]: pin }); authors[bike] = await read(pin); }
  assert.deepEqual(authors.rookie, contract.diagnosticMotion.authorReceipt);
  const surfaces = surfaceArrays(path.join(ROOT, pins.posedSurfaces.path));
  const source = await glb(path.join(ROOT, pins.weightRider.path)), doc = source.document, original = structuredClone(doc);
  const identity = rigIdentity(doc, contract); let length = source.binLength, primitiveRows = 0, maximumMorphFloat32Residual = 0;
  const chunks = [], morphSummary = [], touched = [];
  const attribute = (values, type, width, vertex = false) => {
    assert(values.length%width === 0 && values.every(Number.isFinite)); const buffer = Buffer.alloc(values.length*4);
    values.forEach((v, i) => { buffer.writeFloatLE(v, i*4); maximumMorphFloat32Residual = Math.max(maximumMorphFloat32Residual, Math.abs(v-buffer.readFloatLE(i*4))); });
    const view = doc.bufferViews.length; doc.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: buffer.length, ...(vertex ? { target: 34962 } : {}) });
    const a = { bufferView: view, componentType: 5126, count: values.length/width, type };
    if (vertex && type === 'VEC3') { a.min = [Infinity, Infinity, Infinity]; a.max = [-Infinity, -Infinity, -Infinity];
      for (let i = 0; i < values.length; i++) { const v = buffer.readFloatLE(i*4), k = i%3; a.min[k] = Math.min(a.min[k], v); a.max[k] = Math.max(a.max[k], v); } }
    doc.accessors.push(a); chunks.push(buffer); length += buffer.length; return doc.accessors.length-1;
  };
  for (const name of OBJECTS) {
    const nodeIndex = doc.nodes.findIndex(n => n.name === name); assert(nodeIndex >= 0);
    const node = doc.nodes[nodeIndex], mesh = doc.meshes[node.mesh]; assert(!mesh.weights && !node.weights && !mesh.extras?.targetNames);
    touched.push({ nodeIndex, meshIndex: node.mesh }); const seen = new Set();
    for (const [ordinal, p] of mesh.primitives.entries()) {
      assert(!p.targets); const readAttribute = semantic => accessor(source, p.attributes[semantic]);
      const [nativeIDs, positions, normals, faces] = await Promise.all([readAttribute('_NATIVE_ID'), readAttribute('POSITION'), readAttribute('NORMAL'), accessor(source, p.indices)]);
      const ids = nativeIDs.flat(); assert(ids.every(id => Number.isInteger(id) && id >= 0)); ids.forEach(id => seen.add(id));
      const fields = morphFields(ids, positions, normals, faces.flat(), shape.deltas[name], p.attributes.TANGENT === undefined ? null : await readAttribute('TANGENT'));
      p.targets = [Object.fromEntries(['POSITION', 'NORMAL', 'TANGENT'].filter(k => fields[k]).map(k => [k, attribute(fields[k], 'VEC3', 3, true)]))];
      primitiveRows += ids.length; morphSummary.push({ object: name, primitive: ordinal, primitiveRows: ids.length, attributes: Object.keys(p.targets[0]), maximumNormalRotationRadians: fields.maximumNormalRotationRadians });
    }
    const absent = shape.deltas[name].filter(row => !seen.has(row.nativeID)); assert.equal(absent.length, 0, `${name}: native sculpt moved an unexported ID`);
    mesh.weights = [0]; mesh.extras = { ...mesh.extras, targetNames: [KEY] };
  }
  const morphBytes = length-source.binLength, appended = appendAnimation(doc, authors.rookie, identity, length);
  chunks.push(appended.tail); length += appended.tail.length; const animation = appended.animation;
  animation.name = CLIP; animation.extras = { accepted: false, qualification: STATUS, kind: 'native-posed-volume', shapeKey: KEY };
  const inputAccessor = animation.samplers[0].input, weightAccessor = attribute([0, 0, 1, 1, 0, 0], 'SCALAR', 1);
  for (const {nodeIndex} of touched) { const sampler = animation.samplers.length; animation.samplers.push({ input: inputAccessor, output: weightAccessor, interpolation: 'LINEAR' }); animation.channels.push({ sampler, target: { node: nodeIndex, path: 'weights' } }); }
  assert.equal(animation.channels.length, 227); doc.buffers[0].byteLength = length;
  const protectedCopy = structuredClone(doc);
  for (const {meshIndex} of touched) protectedCopy.meshes[meshIndex] = original.meshes[meshIndex];
  for (const [name, value] of Object.entries(original)) if (!['buffers', 'bufferViews', 'accessors', 'animations'].includes(name)) assert.deepEqual(protectedCopy[name], value, name);
  assert.deepEqual(doc.bufferViews.slice(0, original.bufferViews.length), original.bufferViews); assert.deepEqual(doc.accessors.slice(0, original.accessors.length), original.accessors);
  assert.deepEqual(doc.animations.slice(0, original.animations.length), original.animations);
  for (const {meshIndex} of touched) for (const [i, p] of doc.meshes[meshIndex].primitives.entries()) { const copy = structuredClone(p); delete copy.targets; assert.deepEqual(copy, original.meshes[meshIndex].primitives[i]); }
  const raw = Buffer.from(JSON.stringify(doc)), padded = Buffer.concat([raw, Buffer.alloc((4-raw.length%4)%4, 32)]), h = Buffer.alloc(20), bh = Buffer.alloc(8);
  h.write('glTF'); h.writeUInt32LE(2, 4); h.writeUInt32LE(28+padded.length+length, 8); h.writeUInt32LE(padded.length, 12); h.writeUInt32LE(0x4e4f534a, 16);
  bh.writeUInt32LE(length); bh.writeUInt32LE(0x004e4942, 4); await fsp.mkdir(out, {recursive: true}); const target = path.join(out, 'rider.glb');
  await fsp.writeFile(target, Buffer.concat([h, padded, bh]), {flag: 'wx'});
  await pipeline(fs.createReadStream(source.filename, {start: source.binOffset, end: source.binOffset+source.binLength-1}), fs.createWriteStream(target, {flags: 'a'}));
  for (const chunk of chunks) await fsp.appendFile(target, chunk);
  const originalBinarySHA256 = await sha(source.filename, {start: source.binOffset, end: source.binOffset+source.binLength-1});
  assert.equal(await sha(target, {start: 28+padded.length, end: 28+padded.length+source.binLength-1}), originalBinarySHA256);
  await glb(target); const probe = await loadedProbe(target, source, surfaces, authors, primitiveRows), targetSHA256 = await sha(target);
  const derivative = { accepted: false, kind: 'native-relative-shape-key', name: KEY, sourcePins: pins,
    native: pins.native, nativeReceipt: pins.nativeReceipt, shapeKey: pins.shapeKey, posedSurfaces: pins.posedSurfaces,
    exactNativeIDMapping: true, movedNativeVertices: native.movedVertices, originalBinarySHA256,
    originalBinaryBytesPreserved: source.binLength, originalRestWeightsMapsUVsAnd75InverseBindsExact: true,
    morphs: morphSummary, appendedMorphBytes: morphBytes, tangentMorphs: morphSummary.filter(r => r.attributes.includes('TANGENT')).length,
    shadingMethod: 'Rotate original authored split normals by new-versus-base triangle normals; native custom-normal and GPU parity unmeasured.',
    tangentScope: 'Pinned source has no base TANGENT attributes; none invented. Three morph tangent loading unsupported; normal-map tangent basis uses derivatives.',
    loadedProbe: probe };
  contract.qualificationState = STATUS; contract.glbSHA256 = targetSHA256; contract.previewClip = CLIP; contract.shapeDerivative = derivative;
  contract.diagnosticMotion = { accepted: false, kind: 'native-posed-volume', status: STATUS, previewClip: CLIP,
    outputSHA256: targetSHA256, sourcePins: {...pins, author: shape.posePin}, authorReceipt: authors.rookie,
    durationSeconds: 6, timesSeconds: TIMES, schedule: ['rest', 'rest', 'rejected-author04-key', 'rejected-author04-key', 'rest', 'rest'],
    jointChannels: 225, weightChannels: 2, loadedWeightTracks: 5, shapeKey: KEY, scalarWeights: [0, 0, 1, 1, 0, 0], interpolation: 'LINEAR',
    limits: ['Unaccepted native posed volume; selected posture, continuous native curves, full contacts, crossings, generic controls and played art remain unqualified.', 'Morph weights come from this diagnostic clip only; no pose-driven corrective helper. Actual GPU output and native shading parity remain unmeasured.'] };
  assert.deepEqual(contract.weightDerivative, weightReport.derivative); assert(!contract.corrective);
  const contractPath = path.join(out, 'rider-contract.json'); await fsp.writeFile(contractPath, JSON.stringify(contract, null, 2)+'\n');
  const report = { accepted: false, status: STATUS, recipeSHA256: await sha(fileURLToPath(import.meta.url)), input: {path: path.relative(ROOT, inputPath), sha256: await sha(inputPath)},
    sourcePins: pins, glb: {path: path.relative(ROOT, target), sha256: targetSHA256}, contract: {path: path.relative(ROOT, contractPath), sha256: await sha(contractPath)},
    maximumMorphFloat32Residual, maximumClipFloat32Residual: appended.maximumFloat32Residual, shapeDerivative: derivative, actualGaragePlayed: false };
  await fsp.writeFile(path.join(out, 'transport.json'), JSON.stringify(report, null, 2)+'\n'); await checkPins(pins);
  console.log(JSON.stringify({status: STATUS, glb: report.glb, contract: report.contract, morphs: morphSummary, allExportedRows: primitiveRows, restReturnByteIdentical: probe.restReturnByteIdentical}));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
