/** Independent current outsole ancestry and private socket derivative. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3, Quaternion, Matrix4 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
import { GltfRider } from '../../../src/render/hero/gltfRider.ts';
import { readGlbChunks } from './metadata.mjs';

const [sourceFile, inventoryFile, nativeFile, palmsFile, outFile, receiptFile] = process.argv.slice(2);
assert(receiptFile && !fs.existsSync(outFile) && !fs.existsSync(receiptFile));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(sourceFile), inventoryBytes = fs.readFileSync(inventoryFile);
const nativeBytes = fs.readFileSync(nativeFile), palmBytes = fs.readFileSync(palmsFile);
assert.equal(sha(bytes), '780983f4887f66b18dbf7a4643cb3a80f5241071124129bab3cf9e5d4b0abb8e');
assert.equal(sha(inventoryBytes), 'a987b49de0a7672e80794abec674b43d731eb0189be727e82ad40c758f119c78');
assert.equal(sha(nativeBytes), '5e36f665d8d80bff522abb970512d1ccc126a9b497ed3eda3411cab2b2b3da24');
const inventory = JSON.parse(inventoryBytes), native = JSON.parse(nativeBytes), palms = JSON.parse(palmBytes);
assert.equal(palms.sourceSHA256, 'ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181');
const { json, bin } = readGlbChunks(bytes), expected = structuredClone(json);
const load = async file => { const g = await loadRigAt(pathToFileURL(path.resolve(file)), true); g.scene.updateMatrixWorld(true); return g; };
const g = await load(sourceFile), meshes = [];
g.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
const sole = meshes.find(m => m.material.name === 'Rubber outsole separate volume');
assert(sole); assert.deepEqual(g.parser.associations.get(sole), inventory.primitive.association);
assert.equal(sole.geometry.attributes.position.count, 466); assert.equal(sole.geometry.index.count, 984);
assert.deepEqual(sole.skeleton.bones.map(b => b.name), inventory.jointOrder);
sole.skeleton.update();
let maxRowResidualM = 0, maxNativeResidualM = 0, maxWeightSumError = 0;
const actualPoints = [];
for (const row of inventory.rows) {
  const i = row.exportedRow, weights = {};
  const raw = new Vector3().fromBufferAttribute(sole.geometry.attributes.position, i);
  const actual = sole.localToWorld(sole.getVertexPosition(i, new Vector3())); actualPoints.push(actual);
  assert.deepEqual(raw.toArray(), row.restFileWorldM);
  maxRowResidualM = Math.max(maxRowResidualM, actual.distanceTo(new Vector3(...row.actualLoadedRestWorldM)));
  const p = [raw.x - .65, -raw.z, raw.y];
  const matches = native.vertices.filter(v => Math.hypot(...p.map((a, k) => a - v.restNativeM[k])) < 2e-6);
  assert.equal(matches.length, 1); assert.equal(matches[0].nativeVertexID, row.nativeBootVertexID);
  maxNativeResidualM = Math.max(maxNativeResidualM, Math.hypot(...p.map((a, k) => a - matches[0].restNativeM[k])));
  for (let k = 0; k < 4; k++) {
    const w = sole.geometry.attributes.skinWeight.array[i * 4 + k];
    if (w > 0) { const name = sole.skeleton.bones[sole.geometry.attributes.skinIndex.array[i * 4 + k]].name; weights[name] = (weights[name] ?? 0) + w; }
  }
  assert.deepEqual(weights, row.actualLoaderNormalizedWeights);
  maxWeightSumError = Math.max(maxWeightSumError, Math.abs(Object.values(weights).reduce((a, b) => a + b, 0) - 1));
  assert.deepEqual(row.sourceToken, { GLBSHA256: sha(bytes), mesh: 0, primitive: 1, row: i });
}
assert(maxRowResidualM < 1e-12); assert(maxWeightSumError < 1e-7);
const triangles = inventory.triangles.map(t => {
  const ids = [0, 1, 2].map(k => sole.geometry.index.getX(t.exportedTriangleID * 3 + k));
  assert.deepEqual(ids, t.exportedRows);
  const nativeIDs = ids.map(i => inventory.rows[i].nativeBootVertexID);
  assert.deepEqual(nativeIDs, t.nativeBootVertexIDs);
  const key = a => a.slice().sort((a, b) => a - b).join(',');
  const matches = native.triangles.filter(n => n.materialSlot === 1 && key(n.nativeVertexIDs) === key(nativeIDs));
  assert.equal(matches.length, 1); assert.equal(matches[0].nativeTriangleID, t.nativeBootTriangleID);
  assert.equal(matches[0].nativePolygonID, t.nativeBootPolygonID);
  const points = ids.map(i => actualPoints[i]);
  const cross = points[1].clone().sub(points[0]).cross(points[2].clone().sub(points[0]));
  const area = cross.length() / 2, center = points[0].clone().add(points[1]).add(points[2]).multiplyScalar(1 / 3);
  assert(Math.abs(area - t.areaM2) < 1e-14); assert(center.distanceTo(new Vector3(...t.restWorldCentroidM)) < 1e-12);
  return { ids, area, center, normal: cross.normalize() };
});
const source05 = sourceFile.replace('/appearance09/', '/appearance05/'), old = await load(source05), protectedFields = [];
const oldMeshes = []; old.scene.traverse(o => { if (o.isSkinnedMesh && !o.name.startsWith('Registered_boots')) oldMeshes.push(o); });
const hashArray = a => sha(Buffer.from(a.buffer, a.byteOffset, a.byteLength));
assert.equal(oldMeshes.length, 7);
for (const m of oldMeshes) {
  const next = meshes.find(n => n.name === m.name); assert(next);
  for (const [name, attr] of Object.entries(m.geometry.attributes)) assert.equal(hashArray(attr.array), hashArray(next.geometry.attributes[name].array));
  assert.equal(hashArray(m.geometry.index.array), hashArray(next.geometry.index.array));
  assert.deepEqual(m.skeleton.boneInverses.map(a => a.elements), next.skeleton.boneInverses.map(a => a.elements));
  assert.deepEqual(m.skeleton.bones.map(b => [b.name, b.parent?.name]), next.skeleton.bones.map(b => [b.name, b.parent?.name]));
  protectedFields.push({ name: m.name, exactGeometryWeightsHierarchyInverseBinds: true });
}
const bindings = new Map();
for (const [o, association] of g.parser.associations) if (o.isBone && association.nodes !== undefined) bindings.set(o.name, { object: o, node: association.nodes });
assert.equal(bindings.size, 51);
const rows = [], patchChecks = [];
for (const side of ['L', 'R']) {
  const desc = inventory.sides[side], arch = desc.proposedArchTriangleIDs.map(i => triangles[i]);
  assert.equal(desc.completeOutsoleBottomTriangleIDs.length, 40); assert.equal(arch.length, 7);
  assert(desc.proposedArchTriangleIDs.every(i => desc.completeOutsoleBottomTriangleIDs.includes(i)));
  const area = arch.reduce((sum, t) => sum + t.area, 0), center = new Vector3();
  for (const t of arch) center.addScaledVector(t.center, t.area / area);
  const marker = desc.proposedMarker, parent = bindings.get(marker.parentBone); assert(parent);
  assert(center.distanceTo(new Vector3(...marker.restFileWorldPositionM)) < 1e-12);
  const local = new Vector3(...marker.footParentLocalPositionM), q = new Quaternion(...marker.footParentLocalQuaternionXYZW);
  const world = parent.object.matrixWorld.clone().multiply(new Matrix4().compose(local, q, new Vector3(1, 1, 1)));
  const closure = new Vector3().setFromMatrixPosition(world).distanceTo(center);
  assert(closure < 1e-12);
  const worldQ = new Quaternion(); world.decompose(new Vector3(), worldQ, new Vector3());
  patchChecks.push({ side, areaM2: area, closureResidualM: closure, worldRotationFromPreferredIdentityRad: worldQ.angleTo(new Quaternion()), sourceArchTriangleIDs: desc.proposedArchTriangleIDs });
  const palm = palms.rows.find(r => r.name === `gripSocket.${side}`); assert(palm);
  for (const [name, parentName, translation, rotation, proposal, ancestry] of [
    [`soleSocket.${side}`, marker.parentBone, local.toArray(), q.toArray(), center.toArray(), { sourceGLBSHA256: sha(bytes), inventorySHA256: sha(inventoryBytes), archTriangleIDs: desc.proposedArchTriangleIDs }],
    [`gripSocket.${side}`, `hand${side}`, palm.localTranslationM, null, palm.fileWorldProposalM, { sourceGLBSHA256: palms.sourceSHA256, receiptSHA256: sha(palmBytes), sourcePatch: palm.sourcePatch }]
  ]) {
    const p = bindings.get(parentName); assert(p && !json.nodes.some(n => n.name === name));
    const node = json.nodes.length, addition = { name, translation, extras: { rockhopPrivateContract: 'UNACCEPTED actual constructed09 sole / protected body palm proposal' } };
    if (rotation) addition.rotation = rotation;
    json.nodes.push(addition); (json.nodes[p.node].children ??= []).push(node);
    expected.nodes.push(structuredClone(addition)); (expected.nodes[p.node].children ??= []).push(node);
    rows.push({ name, parentName, node, translation, rotation, fileWorldProposalM: proposal, ancestry });
  }
}
const jb = Buffer.from(JSON.stringify(json)), jsonBytes = Buffer.concat([jb, Buffer.alloc((4 - jb.length % 4) % 4, 32)]);
const header = Buffer.alloc(20), binaryHeader = Buffer.alloc(8);
header.writeUInt32LE(0x46546c67); header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + jsonBytes.length + bin.length, 8);
header.writeUInt32LE(jsonBytes.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
binaryHeader.writeUInt32LE(bin.length); binaryHeader.writeUInt32LE(0x004e4942, 4);
const derivative = Buffer.concat([header, jsonBytes, binaryHeader, bin]), result = readGlbChunks(derivative);
assert(result.bin.equals(bin)); assert.deepEqual(result.json, expected);
fs.mkdirSync(path.dirname(outFile), { recursive: true }); fs.writeFileSync(outFile, derivative);
const loaded = await load(outFile), markerChecks = rows.map(row => {
  const node = loaded.scene.getObjectByName(row.name.replaceAll('.', '')); assert(node);
  const residual = node.getWorldPosition(new Vector3()).distanceTo(new Vector3(...row.fileWorldProposalM)); assert(residual < 1e-12);
  return { name: row.name, restWorldResidualM: residual };
});
await prepareHero(loaded); const rider = new GltfRider(loaded, { complete() {} });
assert(rider.gripSockets.every(Boolean) && rider.soleSockets.every(Boolean));
const report = { status: 'UNACCEPTED_SOURCE09_PRIVATE_CONSTRUCTED_SOLE_CONTRACT_ONLY', sourceSHA256: sha(bytes), inventorySHA256: sha(inventoryBytes), nativeSHA256: sha(nativeBytes),
  derivativeSHA256: sha(derivative), identicalBINSHA256: sha(bin), codeSHA256: sha(fs.readFileSync(new URL(import.meta.url))), protectedFields,
  rows, patchChecks, markerChecks, maxRowResidualM, maxNativeResidualM, maxWeightSumError, constructorRecognizesFourSockets: true,
  onlyJSONChanges: 'Four appended hand/foot child markers and parent child references; all original JSON and BIN exact.',
  limits: ['Rest ancestry/frame qualification only. Current09 wedge shape remains unaccepted.', 'Arch area centroid and rigid foot marker are proposals; actual skinned surface follows normalized foot/ball/shin weights and must be measured in motion.',
    '435 nonunit native weights preserved; no weight cleaning or pure barycentric claim.', 'No consumed IK/collision response, moving fit, mobile performance or player promotion established. Root alone judges.'] };
fs.mkdirSync(path.dirname(receiptFile), { recursive: true }); fs.writeFileSync(receiptFile, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ derivativeSHA256: report.derivativeSHA256, maxRowResidualM, maxNativeResidualM, maxWeightSumError, patchChecks }));
