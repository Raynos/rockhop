/** Independently separate faithful exported skin from installed four-slot loading. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { conditionSleeveSkin } from '../../../src/render/hero/sleeveSkin.ts';
import { readGlbChunks } from './metadata.mjs';
import { acc, rig, primitiveSignature, material } from './fidelity-utils.mjs';

const [candidateFile, rawFile, baselineFile, nativeFile, outFile] = process.argv.slice(2);
assert(outFile && !fs.existsSync(outFile));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const files = [candidateFile, rawFile, baselineFile, nativeFile];
const bytes = files.map(f => fs.readFileSync(f)), [candidate, raw, baseline] = bytes.slice(0, 3).map(readGlbChunks);
assert.equal(sha(bytes[0]), '6042207a828883322df0ff5305eefb33fd3ecb26b0ed8fa5a13642e84b3317ad');
assert.equal(sha(bytes[1]), '33c93dac87830b8d993b7260deb3667c2cbd9dd437e7090993345c46fb6fe074');
assert.equal(sha(bytes[2]), '780983f4887f66b18dbf7a4643cb3a80f5241071124129bab3cf9e5d4b0abb8e');
const native = JSON.parse(bytes[3]);
assert.equal(native.sourceSHA256, 'd3f05ff00755c0fb9e4245465092333ace538098e86eb44e4ad057e4c68d8996');
assert.deepEqual(candidate.json, raw.json);
const p = candidate.json.meshes[0].primitives[0], names = rig(candidate).names;
assert.equal(candidate.json.meshes.length, 1); assert.equal(candidate.json.skins.length, 1);
assert.deepEqual(rig(candidate), rig(baseline));
const skinRanges = ['JOINTS_0', 'JOINTS_1', 'WEIGHTS_0', 'WEIGHTS_1'].map(k => {
  const a = candidate.json.accessors[p.attributes[k]], v = candidate.json.bufferViews[a.bufferView];
  assert([5121, 5123, 5126].includes(a.componentType)); assert.equal(a.type, 'VEC4'); assert(!v.byteStride);
  return [(v.byteOffset ?? 0) + (a.byteOffset ?? 0), a.count * 4 * ({5121:1,5123:2,5126:4}[a.componentType])];
});
let changedSkinBytes = 0;
for (let i = 0; i < candidate.bin.length; i++) if (candidate.bin[i] !== raw.bin[i]) {
  assert(skinRanges.some(([start, length]) => i >= start && i < start + length)); changedSkinBytes++;
}
assert.equal(candidate.bin.length, raw.bin.length);
assert.equal(changedSkinBytes, 2517);
const fields = Object.fromEntries(Object.entries(p.attributes).map(([k, v]) => [k, acc(candidate, v)]));
const restFile = candidateFile.replace('/selected-hoodie14/garment-rig.glb', '/selected-hoodie13/garment-rest.glb');
assert.notEqual(restFile, candidateFile);
const restBytes = fs.readFileSync(restFile), restDocument = readGlbChunks(restBytes), restPrimitive = restDocument.json.meshes[0].primitives[0];
assert.equal(sha(restBytes), 'deb7c56fdb4a8f0c16d083ad84dbe7e8f2fc5bfea2717acb8544195d8cb50f58');
assert.deepEqual(material(candidate, p.material), material(restDocument, restPrimitive.material));
assert.deepEqual(fields.TEXCOORD_0, acc(restDocument, restPrimitive.attributes.TEXCOORD_0));
const source13Normals = acc(restDocument, restPrimitive.attributes.NORMAL);
let maximumSource13NormalComponentDifference = 0, source13ChangedNormalRows = 0, maximumSource13NormalDirectionCross = 0;
for (let row = 0; row < fields.NORMAL.length; row++) {
  const difference = Math.max(...fields.NORMAL[row].map((v, k) => Math.abs(v - source13Normals[row][k])));
  maximumSource13NormalComponentDifference = Math.max(maximumSource13NormalComponentDifference, difference);
  if (difference > 0) source13ChangedNormalRows++;
  maximumSource13NormalDirectionCross = Math.max(maximumSource13NormalDirectionCross,
    new Vector3(...fields.NORMAL[row]).normalize().cross(new Vector3(...source13Normals[row]).normalize()).length());
}
assert(maximumSource13NormalComponentDifference < 2e-7 && maximumSource13NormalDirectionCross < 2e-7,
  'Rest exports show more than measured Float32 normal variation');
assert.deepEqual(acc(candidate, p.indices), acc(restDocument, restPrimitive.indices));
const restLoaded = await loadRigAt(pathToFileURL(path.resolve(restFile)), true), restMeshes = [];
restLoaded.scene.updateMatrixWorld(true); restLoaded.scene.traverse(o => { if (o.isMesh) restMeshes.push(o); });
assert.equal(restMeshes.length, 1); const restMesh = restMeshes[0]; assert(!restMesh.isSkinnedMesh);
let maximumSource13RestWorldResidualM = 0;
for (let row = 0; row < fields.POSITION.length; row++) maximumSource13RestWorldResidualM = Math.max(maximumSource13RestWorldResidualM,
  restMesh.localToWorld(new Vector3().fromBufferAttribute(restMesh.geometry.attributes.position, row)).distanceTo(new Vector3(...fields.POSITION[row])));
assert(maximumSource13RestWorldResidualM < 2e-7);
const mapping = [], seen = new Set(), secondSetRows = [], loaderRows = [];
let maximumRestResidualM = 0, maximumNativeWeightDifference = 0, maximumSecondWeightSum = 0, maximumWeightSumError = 0;
const loaded = await loadRigAt(pathToFileURL(path.resolve(candidateFile)), true), meshes = [];
loaded.scene.updateMatrixWorld(true); loaded.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
assert.equal(meshes.length, 1); const mesh = meshes[0], a = mesh.geometry.attributes;
assert.equal(a.position.count, 7123); assert.equal(mesh.geometry.index.count, 11840 * 3);
const attrBefore = Object.fromEntries(Object.entries(a).map(([k, v]) => [k, sha(Buffer.from(v.array.buffer, v.array.byteOffset, v.array.byteLength))]));
const geometryBefore = mesh.geometry, release = conditionSleeveSkin(mesh);
assert.equal(mesh.geometry, geometryBefore, 'Explicit owner flag failed to preserve authored field');
assert.deepEqual(Object.fromEntries(Object.entries(a).map(([k, v]) => [k, sha(Buffer.from(v.array.buffer, v.array.byteOffset, v.array.byteLength))])), attrBefore);
release(); mesh.skeleton.update();
assert.deepEqual(mesh.skeleton.bones.map(b => b.name), names.map(n => n.replaceAll('.', '')));
for (let row = 0; row < a.position.count; row++) {
  const pos = fields.POSITION[row], matches = native.vertices.map(v => ({ v,
    gap: Math.hypot(pos[0] - v.worldM[0], pos[1] - v.worldM[2], pos[2] + v.worldM[1]) })).filter(v => v.gap < 2e-6);
  assert.equal(matches.length, 1, 'Ambiguous native rest ancestry');
  const { v, gap } = matches[0]; mapping.push(v.id); seen.add(v.id); maximumRestResidualM = Math.max(maximumRestResidualM, gap);
  const expected = Object.fromEntries(v.weights), actual = {};
  for (let set = 0; set < 2; set++) for (let k = 0; k < 4; k++) {
    const weight = fields['WEIGHTS_' + set][row][k], name = names[fields['JOINTS_' + set][row][k]];
    assert(name !== undefined && Number.isFinite(weight) && weight >= 0);
    if (weight > 0) actual[name] = (actual[name] ?? 0) + weight;
  }
  for (const n of new Set([...Object.keys(expected), ...Object.keys(actual)]))
    maximumNativeWeightDifference = Math.max(maximumNativeWeightDifference, Math.abs((actual[n] ?? 0) - (expected[n] ?? 0)));
  const sum = Object.values(actual).reduce((x, y) => x + y, 0), second = fields.WEIGHTS_1[row].reduce((x, y) => x + y, 0);
  maximumWeightSumError = Math.max(maximumWeightSumError, Math.abs(sum - 1)); maximumSecondWeightSum = Math.max(maximumSecondWeightSum, second);
  if (second > 0) secondSetRows.push({ row, nativeVertexID: v.id, exportedSecondWeightSum: second });
  const first = fields.WEIGHTS_0[row].reduce((x, y) => x + y, 0), actualFirst = Array.from({ length: 4 }, (_, k) => a.skinWeight.getComponent(row, k));
  const normError = Math.max(...actualFirst.map((w, k) => Math.abs(w - fields.WEIGHTS_0[row][k] / first)));
  assert(normError < 6e-8, 'Loader primary weight normalization is unexplained');
  const before = new Vector3(...pos), rest = mesh.getVertexPosition(row, new Vector3()).applyMatrix4(mesh.matrixWorld);
  loaderRows.push({ row, nativeVertexID: v.id, restResidualM: rest.distanceTo(before), primaryNormalizationError: normError });
}
assert.equal(seen.size, 6046); assert.equal(maximumNativeWeightDifference, 0);
const exportedFaces = acc(candidate, p.indices).flat();
const compareKeys = (a, b) => a.localeCompare(b);
const cycles = f => [f, [f[1], f[2], f[0]], [f[2], f[0], f[1]]].map(x => x.join(',')).sort(compareKeys)[0];
const nativeKeys = native.triangles.map(cycles).sort(compareKeys), exportKeys = Array.from({ length: 11840 }, (_, i) => cycles(exportedFaces.slice(i * 3, i * 3 + 3).map(row => mapping[row]))).sort(compareKeys);
assert.deepEqual(exportKeys, nativeKeys);
const shader = fs.readFileSync('node_modules/three/src/renderers/shaders/ShaderChunk/skinning_vertex.glsl.js', 'utf8');
assert.equal((shader.match(/skinned \+=/g) ?? []).length, 4); assert(!shader.includes('weights_1'));
const report = { status: 'UNACCEPTED_FAITHFUL_SOURCE14_EXPORT_INSTALLED_ENGINE_ONLY_CONSUMES_PRIMARY_FOUR_WEIGHTS',
  pins: Object.fromEntries(files.map((f, i) => [f, sha(bytes[i])])), codeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  rows: 7123, nativeVertices: 6046, triangles: 11840, joints: names,
  nativeMapping: mapping, nativeFaces: native.triangles, secondSetRows, loaderRows,
  original51RigAndInverseBindsExact: true, orientedNativeTriangleCyclesExact: true,
  onlyChangedRawExportBytes: changedSkinBytes, maximumRestResidualM, maximumNativeWeightDifference, maximumWeightSumError,
  source13RestSHA256: sha(restBytes), source13UVOrientedIndicesEmbeddedPBRExact: true, maximumSource13RestWorldResidualM,
  source13ChangedNormalRows, maximumSource13NormalComponentDifference, maximumSource13NormalDirectionCross,
  actualLoaderAttributeNames: Object.keys(a), explicitOwnerFlagPreservesSkinField: true,
  secondarySetRows: secondSetRows.length, secondarySetNativeVertices: new Set(secondSetRows.map(x => x.nativeVertexID)).size,
  maximumSecondWeightSum, maximumLoaderRestResidualM: Math.max(...loaderRows.map(x => x.restResidualM)),
  nonSkinSignature: primitiveSignature(candidate, p), material: material(candidate, p.material),
  installedShaderSHA256: sha(Buffer.from(shader)),
  installedLoaderSHA256: sha(fs.readFileSync('node_modules/three/examples/jsm/loaders/GLTFLoader.js')),
  limits: ['Actual disk export preserves all native memberships; installed loader normalizes primary WEIGHTS_0 while shader/readback consume four slots.',
    'Secondary accessor retention is not secondary influence consumption. Actual posed discrepancy is measured in the following engine unit.',
    'Source13 rest-export NORMAL rows have explicitly measured Float32 variation; no byte-exact normal preservation claim across rest and rigged exports.',
    'Node loader omits image decoding only; raw embedded image/material signatures remain separately pinned, no art judgment.',
    'No candidate/source/weight/shader modification or normal-player promotion. Native moving wearing failure remains separate.'] };
fs.mkdirSync(path.dirname(outFile), { recursive: true }); fs.writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ rows: report.rows, maximumRestResidualM, maximumNativeWeightDifference,
  secondarySetRows: report.secondarySetRows, secondarySetNativeVertices: report.secondarySetNativeVertices,
  maximumSecondWeightSum, actualLoaderAttributeNames: report.actualLoaderAttributeNames }));
