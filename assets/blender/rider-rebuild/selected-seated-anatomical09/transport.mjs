/** Parent CPU2 only: append actual saved anatomical09 FOUR and a weight-only clip.
 * node --import tsx transport.mjs --out=FRESH_IGNORED_DIRECTORY
 * No Blender, shape changes, old corrective deltas, or normal-player asset writes.
 */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pipeline } from 'node:stream/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Matrix4, PropertyBinding, Vector3, REVISION } from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { rigIdentity, appendAnimation } from '../selected-seated-diagnostic08/append-clip.mjs';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
const HERE = path.dirname(fileURLToPath(import.meta.url));
const CLIP = 'Anatomical09WeightRestKey';
const STATUS = 'UNACCEPTED_WEIGHT_INTERVENTION';
const POSITION_TOLERANCE = .0001;
const PINS = {
  engineRider: ['harness/out/rider-rebuild/selected-complete-engine01/engine05/rider.glb', '72b90e8790f8490743a75f8b70791aa21edfee6234cec609093e9b62e08d4bfd'],
  engineContract: ['harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-contract.json', '2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728'],
  native: ['harness/out/rider-rebuild/selected-seated-anatomical09/authored01/selected-anatomical09-weight-only.blend', 'd42ff6349a520259e86c8f6eeee889979a23413305efe20742a06b1d34afedf9'],
  nativeReceipt: ['harness/out/rider-rebuild/selected-seated-anatomical09/authored01/receipt.json', '25025f3c0e6303e0a7b4c3a6e6dab36497a3492aa97c5e9fc23cfcd96702d940'],
  weights: ['harness/out/rider-rebuild/selected-seated-anatomical09/authored01/authored-weight-rows.json', '3af8d3ddd719f47a7f2e5073a5ab0dda00aa9ce2a25fa471c00b9718093bf4bf'],
  author: ['harness/out/rider-rebuild/selected-seated-author04/authored01/rookie.json', '9d59ba63e99c8d017e7f8c8c4dfbfde0859aafd3ea6d2383c734dec259ec5f8a'],
};
async function sha(filename, range = {}) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(filename, range)) hash.update(chunk);
  return hash.digest('hex');
}
async function bytes(filename, start, length) {
  const file = await fsp.open(filename, 'r');
  try {
    const result = Buffer.alloc(length); let read = 0;
    while (read < length) { const row = await file.read(result, read, length-read, start+read); assert(row.bytesRead); read += row.bytesRead; }
    return result;
  } finally { await file.close(); }
}
async function openGLB(filename) {
  const header = await bytes(filename, 0, 20); assert.equal(header.toString('ascii', 0, 4), 'glTF');
  assert.equal(header.readUInt32LE(4), 2); assert.equal(header.readUInt32LE(16), 0x4e4f534a);
  assert.equal(header.readUInt32LE(8), (await fsp.stat(filename)).size);
  const jsonLength = header.readUInt32LE(12), document = JSON.parse(await bytes(filename, 20, jsonLength));
  const binary = await bytes(filename, 20+jsonLength, 8), binLength = binary.readUInt32LE(0);
  assert.equal(binary.readUInt32LE(4), 0x004e4942); assert.equal(binLength%4, 0);
  assert.equal(document.buffers.length, 1); assert(!document.buffers[0].uri);
  assert.equal(28+jsonLength+binLength, header.readUInt32LE(8));
  return { filename, document, binOffset: 28+jsonLength, binLength };
}
async function accessor(source, index) {
  const row = source.document.accessors[index], view = source.document.bufferViews[row.bufferView];
  const width = { SCALAR: 1, VEC4: 4 }[row.type];
  const [reader, size] = { 5121: ['readUInt8', 1], 5126: ['readFloatLE', 4] }[row.componentType] ?? [];
  assert(width && reader && !row.sparse && !row.normalized && !view.extensions && view.buffer === 0);
  const stride = view.byteStride ?? size*width, offset = row.byteOffset ?? 0;
  assert(offset+(row.count-1)*stride+width*size <= view.byteLength);
  const data = await bytes(source.filename, source.binOffset+(view.byteOffset ?? 0), view.byteLength);
  return Array.from({ length: row.count }, (_, i) => Array.from({ length: width }, (_, c) => data[reader](offset+i*stride+c*size)));
}
const entries = row => Object.entries(row).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
const named = (joints, weights, names) => Object.fromEntries(joints.map((j, k) => [names[j], weights[k]]).filter(([, w]) => w > 0));
const bits = value => { const b = Buffer.alloc(4); b.writeFloatLE(value); return b.readUInt32LE(); };

const percentile = (values, fraction) => { const sorted = [...values].sort((a, b) => a-b); return sorted[Math.ceil((sorted.length-1)*fraction)]; };
function pruningProbe(gltf, mesh, nativeRows, expectedRows, edits, authors, rests) {
  const index = mesh.geometry.index, ids = mesh.geometry.attributes._native_id, edgeMap = new Map();
  for (let k = 0; k < index.count; k += 3) {
    const face = [0, 1, 2].map(c => ids.getX(index.getX(k+c)));
    for (let c = 0; c < 3; c++) {
      const pair = [face[c], face[(c+1)%3]].sort((a, b) => a-b);
      if (pair[0] !== pair[1] && pair.some(id => edits.has(id))) edgeMap.set(pair.join(','), pair);
    }
  }
  const edges = [...edgeMap.values()], needed = new Set(edges.flat()), samples = [];
  const original = id => edits.get(id)?.fullAuthored ?? expectedRows.get(id);
  const support = row => new Set(entries(row).filter(([, v]) => v > .0001).map(([name]) => name));
  const difference = (a, b) => [...a].filter(k => !b.has(k));
  const switches = edges.map(pair => {
    const full = pair.map(id => support(original(id))), four = pair.map(id => support(expectedRows.get(id)));
    const oldDifference = new Set([...difference(full[0], full[1]), ...difference(full[1], full[0])]);
    const newDifference = new Set([...difference(four[0], four[1]), ...difference(four[1], four[0])]);
    return { nativeIDs: pair, removedAtEndpoints: pair.map((id, i) => difference(full[i], four[i])),
      introducedSupportDifferences: difference(newDifference, oldDifference) };
  });
  for (const kind of ['rejected-rookie-key', 'diagnostic-right-thigh-subtree-rest']) {
    for (const row of authors.rookie.boneLocalTRS) {
      const bone = gltf.scene.getObjectByName(PropertyBinding.sanitizeNodeName(row.id));
      bone.position.fromArray(row.translation); bone.quaternion.fromArray(row.rotationXYZW); bone.scale.fromArray(row.scale);
    }
    const resetNames = [];
    if (kind.includes('subtree')) {
      const thigh = gltf.scene.getObjectByName(PropertyBinding.sanitizeNodeName('DEF-thigh.R')); assert(thigh?.isBone);
      thigh.traverse(bone => { if (!bone.isBone) return; const rest = rests.get(bone.name); assert(rest);
        bone.position.copy(rest.position); bone.quaternion.copy(rest.quaternion); bone.scale.copy(rest.scale); resetNames.push(bone.name); });
    }
    gltf.scene.updateMatrixWorld(true); mesh.skeleton.update();
    const skin = new Map(mesh.skeleton.bones.map((bone, i) => [bone.name,
      new Matrix4().multiplyMatrices(bone.matrixWorld, mesh.skeleton.boneInverses[i])]));
    const positions = new Map();
    for (const id of needed) {
      const point = new Vector3().fromBufferAttribute(mesh.geometry.attributes.position, nativeRows.get(id)).applyMatrix4(mesh.bindMatrix);
      const deform = field => {
        const value = new Vector3();
        for (const [name, weight] of entries(field)) {
          const matrix = skin.get(PropertyBinding.sanitizeNodeName(name)); assert(matrix);
          value.addScaledVector(point.clone().applyMatrix4(matrix), weight);
        }
        return value.applyMatrix4(mesh.bindMatrixInverse).applyMatrix4(mesh.matrixWorld);
      };
      const full = deform(original(id)), four = deform(expectedRows.get(id));
      positions.set(id, { full, four, displacement: four.clone().sub(full) });
    }
    const vertices = [...edits].map(([id, edit]) => ({ nativeID: id,
      displacementM: positions.get(id).displacement.length(), removedMass: edit.removedMass,
      fullAuthored: edit.fullAuthored, nativeSavedFour: edit.finalFour }));
    const gradients = switches.map(row => {
      const [a, b] = row.nativeIDs.map(id => positions.get(id));
      return { ...row, displacementJumpM: a.displacement.distanceTo(b.displacement),
        fullEdgeM: a.full.distanceTo(b.full), fourEdgeM: a.four.distanceTo(b.four) };
    });
    samples.push({ kind, accepted: false, resetSubtreeBoneNames: resetNames,
      poseDefinition: 'Full saved Rookie local75 key; asymmetric case restores only right thigh and descendants to original local rest under the still-keyed pelvis. Diagnostic, not authored anatomy/contact.',
      changedVertices: vertices.length, maximumDisplacementM: Math.max(...vertices.map(v => v.displacementM)),
      p95DisplacementM: percentile(vertices.map(v => v.displacementM), .95),
      worstVertices: vertices.sort((a, b) => b.displacementM-a.displacementM).slice(0, 20),
      neighborEdges: gradients.length, maximumDisplacementJumpM: Math.max(...gradients.map(v => v.displacementJumpM)),
      p95DisplacementJumpM: percentile(gradients.map(v => v.displacementJumpM), .95),
      introducedSupportSwitchEdges: gradients.filter(v => v.introducedSupportDifferences.length).length,
      worstNeighborEdges: gradients.sort((a, b) => b.displacementJumpM-a.displacementJumpM).slice(0, 20) });
  }
  return { accepted: false, scope: 'One full-authored versus final native FOUR comparison on actual decoded triangle topology, including exporter diagonals. Four-field rounding and actual loader normalization are reported separately.',
    maximumRemovedMass: Math.max(...[...edits.values()].map(row => row.removedMass)),
    removedMassOverOnePercent: [...edits.values()].filter(row => row.removedMass > .01).length,
    removedMassOverFivePercent: [...edits.values()].filter(row => row.removedMass > .05).length,
    supportReportingCutoff: .0001, samples };
}

async function loadedProbe(filename, expectedRows, native, authors, edits) {
  // The production GLTFLoader runs, including its unconditional normalization.
  // Only this CPU test's in-memory texture references are omitted; disk bytes
  // and the actual Garage's original 4K materials remain fully preserved.
  const gltf = await loadRigAt(pathToFileURL(filename), true);
  const mesh = gltf.scene.getObjectByName('RiderJeans'); assert(mesh?.isSkinnedMesh);
  const attrs = mesh.geometry.attributes, nativeRows = new Map();
  let changedComponents = 0, changedRows = 0, maximumULP = 0, maximumAbsolute = 0;
  const changes = [];
  for (let row = 0; row < attrs._native_id.count; row++) {
    const id = attrs._native_id.getX(row); if (!nativeRows.has(id)) nativeRows.set(id, row);
    const wanted = expectedRows.get(id); assert(wanted);
    const actual = {};
    for (let c = 0; c < 4; c++) {
      const value = attrs.skinWeight.getComponent(row, c);
      if (value > 0) actual[mesh.skeleton.bones[attrs.skinIndex.getComponent(row, c)].name] = value;
    }
    assert.deepEqual(Object.keys(actual).sort(), Object.keys(wanted).map(PropertyBinding.sanitizeNodeName).sort());
    let changed = false;
    for (const [name, value] of entries(wanted)) {
      const loaded = actual[PropertyBinding.sanitizeNodeName(name)], ulp = Math.abs(bits(value)-bits(loaded));
      const delta = Math.abs(value-loaded); maximumULP = Math.max(maximumULP, ulp); maximumAbsolute = Math.max(maximumAbsolute, delta);
      if (ulp) { changedComponents++; changed = true; changes.push({ nativeID: id, primitiveRow: row, joint: name, nativeExact: value, loaded, ulp }); }
    }
    if (changed) changedRows++;
  }
  const rests = new Map(); gltf.scene.traverse(node => { if (node.isBone) rests.set(node.name,
    { position: node.position.clone(), quaternion: node.quaternion.clone(), scale: node.scale.clone() }); });
  const samples = [];
  for (const bike of ['rookie', 'pro']) for (const stage of ['rest', 'key', 'return']) {
    for (const [name, rest] of rests) { const bone = gltf.scene.getObjectByName(name); bone.position.copy(rest.position); bone.quaternion.copy(rest.quaternion); bone.scale.copy(rest.scale); }
    if (stage === 'key') for (const row of authors[bike].boneLocalTRS) {
      const bone = gltf.scene.getObjectByName(PropertyBinding.sanitizeNodeName(row.id)); assert(bone?.isBone);
      bone.position.fromArray(row.translation); bone.quaternion.fromArray(row.rotationXYZW); bone.scale.fromArray(row.scale);
    }
    gltf.scene.updateMatrixWorld(true); mesh.skeleton.update();
    const expected = native.savedActionSamples[bike][stage === 'key' ? 31 : stage === 'return' ? 61 : 1];
    const witnesses = expected.edges.flatMap(edge => edge.ids.map((id, k) => {
      const p = mesh.getVertexPosition(nativeRows.get(id), new Vector3()).applyMatrix4(mesh.matrixWorld);
      const blender = [p.x, -p.z, p.y], target = edge.pointsBlender[k], residualM = Math.hypot(...blender.map((v, axis) => v-target[axis]));
      assert(residualM <= POSITION_TOLERANCE, `Native/Three positional witness ${bike}/${stage}/${id}: ${residualM}`);
      return { nativeID: id, nativeBlender: target, threeBlender: blender, residualM };
    }));
    samples.push({ bike, stage, witnesses, maximumResidualM: Math.max(...witnesses.map(row => row.residualM)) });
  }
  const pruning = pruningProbe(gltf, mesh, nativeRows, expectedRows, edits, authors, rests);
  return { pruning, receipt: { threeRevision: REVISION, decodedChangedNativeFieldsExact: true, loadedNormalization: {
    primitiveRows: attrs._native_id.count, changedRows, changedComponents, maximumULP, maximumAbsolute },
    positionalToleranceM: POSITION_TOLERANCE, samples, gpuVertexReadback: 'UNMEASURED',
    scope: 'Actual installed GLTFLoader and Three CPU skinning at four witness IDs for both saved bike keys and rest/return. Native action midpoint curves and actual GPU output are not qualified.' }, changes };
}

async function main() {
  const output = process.argv.find(v => v.startsWith('--out=')); assert(output);
  const out = path.resolve(output.slice(6));
  assert(out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-seated-anatomical09')+path.sep) && !fs.existsSync(out));
  for (const [filename, digest] of Object.values(PINS)) assert.equal(await sha(path.join(ROOT, filename)), digest, filename);
  const read = async key => JSON.parse(await fsp.readFile(path.join(ROOT, PINS[key][0]), 'utf8'));
  const [contract, native, authored, author] = await Promise.all(['engineContract', 'nativeReceipt', 'weights', 'author'].map(read));
  assert.equal(native.accepted, false); assert.equal(native.native.sha256, PINS.native[1]);
  assert.equal(native.native75RestExact, true); assert.equal(native.outsideWeightsExact, true);
  assert.equal(native.editedJeansVertices, authored.length); assert.equal(authored.length, 2356);
  const edits = new Map(authored.map(row => [row.nativeID, row])); assert.equal(edits.size, authored.length);
  const source = await openGLB(path.join(ROOT, PINS.engineRider[0])); const doc = source.document, original = structuredClone(doc);
  const identity = rigIdentity(doc, contract), jointNames = doc.skins[0].joints.map(i => doc.nodes[i].name);
  const slot = new Map(jointNames.map((name, i) => [name, i])); assert.equal(slot.size, 75);
  const node = doc.nodes.find(n => n.name === 'RiderJeans'), mesh = doc.meshes[node.mesh];
  assert.equal(mesh.primitives.length, 1); assert(!mesh.weights && !mesh.primitives[0].targets && !contract.corrective);
  const primitive = mesh.primitives[0], ids = (await accessor(source, primitive.attributes._NATIVE_ID)).map(row => row[0]);
  const oldJoints = await accessor(source, primitive.attributes.JOINTS_0), oldWeights = await accessor(source, primitive.attributes.WEIGHTS_0);
  assert.equal(ids.length, 26474); assert.equal(oldJoints.length, ids.length); assert.equal(oldWeights.length, ids.length);
  const joints = Buffer.alloc(ids.length*4), weights = Buffer.alloc(ids.length*16), expectedRows = new Map(), seenEdits = new Set();
  const baselineRounding = { changedPrimitiveRows: 0, changedComponents: 0, maximumULP: 0, maximumAbsolute: 0,
    meaning: 'Existing pinned engine05 raw exported rows versus its saved native before fields, before this intervention.' };
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i]; assert(Number.isInteger(id)); const edit = edits.get(id);
    let palette = oldJoints[i], row = oldWeights[i];
    if (edit) {
      seenEdits.add(id); const before = named(palette, row, jointNames);
      assert.deepEqual(Object.keys(before).sort(), Object.keys(edit.before).sort(), `Original named native support ${id}`);
      let rounded = false;
      for (const [name, value] of entries(before)) {
        const expected = edit.before[name], ulp = Math.abs(bits(value)-bits(expected));
        assert(ulp <= 2, `Pinned original engine05 native/export rounding ${id}/${name}`);
        if (ulp) { baselineRounding.changedComponents++; rounded = true; }
        baselineRounding.maximumULP = Math.max(baselineRounding.maximumULP, ulp);
        baselineRounding.maximumAbsolute = Math.max(baselineRounding.maximumAbsolute, Math.abs(value-expected));
      }
      if (rounded) baselineRounding.changedPrimitiveRows++;
      const chosen = entries(edit.finalFour); assert(chosen.length > 0 && chosen.length <= 4);
      assert(chosen.every(([name, value]) => slot.has(name) && value > .0001 && Math.fround(value) === value));
      assert(Math.abs(chosen.reduce((sum, [, v]) => sum+v, 0)-1) < 2e-6);
      palette = chosen.map(([name]) => slot.get(name)); row = chosen.map(([, v]) => v);
      while (row.length < 4) { palette.push(0); row.push(0); }
    }
    for (let c = 0; c < 4; c++) { joints.writeUInt8(palette[c], i*4+c); weights.writeFloatLE(row[c], i*16+c*4); }
    const field = named(palette, row, jointNames);
    if (expectedRows.has(id)) assert.deepEqual(entries(field), entries(expectedRows.get(id)), 'Split native identity field differs');
    expectedRows.set(id, field);
  }
  assert.equal(seenEdits.size, edits.size);
  let length = source.binLength;
  for (const [semantic, buffer, componentType] of [['JOINTS_0', joints, 5121], ['WEIGHTS_0', weights, 5126]]) {
    const bufferView = doc.bufferViews.length; doc.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: buffer.length, target: 34962 });
    const index = doc.accessors.length; doc.accessors.push({ bufferView, componentType, count: ids.length, type: 'VEC4' });
    primitive.attributes[semantic] = index; length += buffer.length;
  }
  const animated = appendAnimation(doc, author, identity, length);
  animated.animation.name = CLIP;
  animated.animation.extras = { accepted: false, qualification: STATUS, kind: 'native-weight-only',
    diagnostic: 'Original rest / exact rejected author04 Rookie local75 TRS / return. Authored anatomical09 weights only; no corrective morph.' };
  const protectedCopy = structuredClone(doc); protectedCopy.meshes[node.mesh].primitives[0].attributes.JOINTS_0 = original.meshes[node.mesh].primitives[0].attributes.JOINTS_0;
  protectedCopy.meshes[node.mesh].primitives[0].attributes.WEIGHTS_0 = original.meshes[node.mesh].primitives[0].attributes.WEIGHTS_0;
  for (const [key, value] of Object.entries(original)) if (!['buffers', 'bufferViews', 'accessors', 'animations'].includes(key)) assert.deepEqual(protectedCopy[key], value, key);
  assert.deepEqual(doc.bufferViews.slice(0, original.bufferViews.length), original.bufferViews);
  assert.deepEqual(doc.accessors.slice(0, original.accessors.length), original.accessors);
  assert.deepEqual((doc.animations ?? []).slice(0, original.animations?.length ?? 0), original.animations ?? []);
  const rawJSON = Buffer.from(JSON.stringify(doc)), padded = Buffer.concat([rawJSON, Buffer.alloc((4-rawJSON.length%4)%4, 32)]);
  const tail = Buffer.concat([joints, weights, animated.tail]), header = Buffer.alloc(20), binHeader = Buffer.alloc(8);
  header.write('glTF'); header.writeUInt32LE(2, 4); header.writeUInt32LE(28+padded.length+source.binLength+tail.length, 8);
  header.writeUInt32LE(padded.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  binHeader.writeUInt32LE(source.binLength+tail.length); binHeader.writeUInt32LE(0x004e4942, 4);
  await fsp.mkdir(out, { recursive: true }); const target = path.join(out, 'rider.glb');
  await fsp.writeFile(target, Buffer.concat([header, padded, binHeader]), { flag: 'wx' });
  await pipeline(fs.createReadStream(source.filename, { start: source.binOffset, end: source.binOffset+source.binLength-1 }), fs.createWriteStream(target, { flags: 'a' }));
  await fsp.appendFile(target, tail);
  const originalBinarySHA256 = await sha(source.filename, { start: source.binOffset, end: source.binOffset+source.binLength-1 });
  assert.equal(await sha(target, { start: 28+padded.length, end: 28+padded.length+source.binLength-1 }), originalBinarySHA256);
  const actual = await openGLB(target), decodedJ = await accessor(actual, primitive.attributes.JOINTS_0), decodedW = await accessor(actual, primitive.attributes.WEIGHTS_0);
  for (let i = 0; i < ids.length; i++) assert.deepEqual(entries(named(decodedJ[i], decodedW[i], jointNames)), entries(expectedRows.get(ids[i])));
  const authors = { rookie: author };
  const proPin = native.diagnosticPoses.pro; assert.equal(await sha(path.join(ROOT, proPin.path)), proPin.sha256);
  authors.pro = JSON.parse(await fsp.readFile(path.join(ROOT, proPin.path), 'utf8'));
  const probe = await loadedProbe(target, expectedRows, native, authors, edits), targetSHA = await sha(target);
  const sourcePins = Object.fromEntries(Object.entries(PINS).map(([k, [p, h]]) => [k, { path: p, sha256: h }]));
  const derivative = { accepted: false, kind: 'native-regional-weight-only',
    sourcePins: { native: sourcePins.native, nativeReceipt: sourcePins.nativeReceipt, authoredRows: sourcePins.weights, engineRider: sourcePins.engineRider }, native: sourcePins.native,
    nativeReceipt: sourcePins.nativeReceipt, authoredWeights: sourcePins.weights, source: sourcePins.engineRider,
    object: 'RiderJeans', changedNativeVertices: edits.size, primitiveRows: ids.length,
    sourceNativeFieldsPreserved: false, decodedChangedFieldsExactlyNewSavedNative: true,
    untouchedGLBFieldsExactlyOriginal: true, baselineNativeExportRounding: baselineRounding,
    maximumFourRemovedMass: native.maximumFourRemovedMass, originalBinarySHA256,
    protectedRestGeometryUVMapsAnd75InverseBindsExact: true, nativeLoadedParity: probe.receipt,
    fourPruningDiagnostic: probe.pruning };
  contract.accepted = false; contract.qualificationState = STATUS; contract.glbSHA256 = targetSHA;
  contract.weightDerivative = derivative; contract.previewClip = CLIP; contract.driver.garagePositionBike = [0, 0, 0];
  contract.diagnosticMotion = { accepted: false, kind: 'native-weight-only', status: STATUS, previewClip: CLIP,
    outputSHA256: targetSHA, sourcePins, authorReceipt: author, durationSeconds: 6,
    timesSeconds: [0, 1, 2, 4, 5, 6], schedule: ['rest', 'rest', 'rejected-author04-key', 'rejected-author04-key', 'rest', 'rest'],
    jointChannels: 225, weightChannels: 0, correctiveMorphs: 0,
    nativeActionScope: 'Saved native key endpoints measured; this glTF LINEAR diagnostic does not claim Blender F-curve midpoint identity.',
    limits: ['Weight result remains unaccepted; maximum FOUR discarded mass15.2225% remains visible.',
      'Four native positional witnesses per bike key/rest/return are bounded by0.1mm. Actual GPU vertex readback, continuous native/action parity, full-surface geometry/contact and moving art remain open.'] };
  assert(!contract.corrective && doc.meshes.every(m => !m.weights && m.primitives.every(p => !p.targets)));
  const outputContract = path.join(out, 'rider-contract.json');
  await fsp.writeFile(outputContract, JSON.stringify(contract, null, 2)+'\n');
  await fsp.writeFile(path.join(out, 'loaded-weight-changes.json'), JSON.stringify(probe.changes)+'\n');
  await fsp.writeFile(path.join(out, 'four-pruning-diagnostic.json'), JSON.stringify(probe.pruning, null, 2)+'\n');
  const report = { accepted: false, status: STATUS, sourcePins, recipeSHA256: await sha(fileURLToPath(import.meta.url)),
    glb: { path: path.relative(ROOT, target), sha256: targetSHA },
    contract: { path: path.relative(ROOT, outputContract), sha256: await sha(outputContract) },
    originalBinaryBytesPreserved: source.binLength, appendedWeightBytes: joints.length+weights.length,
    appendedAnimationBytes: animated.tail.length, maximumClipFloat32Residual: animated.maximumFloat32Residual,
    derivative, actualGaragePlayed: false, gpuVertexReadback: 'UNMEASURED' };
  await fsp.writeFile(path.join(out, 'transport.json'), JSON.stringify(report, null, 2)+'\n');
  for (const [p, h] of Object.values(PINS)) assert.equal(await sha(path.join(ROOT, p)), h);
  console.log(JSON.stringify({ status: STATUS, glb: report.glb, contract: report.contract,
    loadedNormalization: probe.receipt.loadedNormalization, positionalSamples: probe.receipt.samples.map(({ bike, stage, maximumResidualM }) => ({ bike, stage, maximumResidualM })),
    pruningSamples: probe.pruning.samples.map(({ kind, maximumDisplacementM, p95DisplacementM, maximumDisplacementJumpM }) => ({ kind, maximumDisplacementM, p95DisplacementM, maximumDisplacementJumpM })) }));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
