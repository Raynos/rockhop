/** Independently replay Agent 1's exact world matrices through GLTFLoader. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Matrix4, Vector3 } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { compareThreeWays, compareMappedPositions } from './compare.mjs';
import { conditionSleeveSkin } from '../../../src/render/hero/sleeveSkin.ts';

const [glbFile, driverFile, outputFile] = process.argv.slice(2);
assert(outputFile, 'Usage: measure.mjs candidate.glb driver.json new-report.json');
assert(!fs.existsSync(outputFile), 'Refuse to overwrite a measurement');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(glbFile), driverBytes = fs.readFileSync(driverFile);
const driver = JSON.parse(driverBytes);
assert.equal(hash(bytes), driver.conditionedGLBSHA256);
const json = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const gltf = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
gltf.scene.updateMatrixWorld(true);
const byNode = new Map();
for (const [object, association] of gltf.parser.associations)
  if (association.nodes !== undefined) byNode.set(association.nodes, object);
const bones = new Map();
for (const skin of json.skins) for (const node of skin.joints) {
  assert(byNode.get(node)?.isBone, 'Actual skin node missing from loader');
  bones.set(json.nodes[node].name, byNode.get(node));
}
assert.deepEqual([...bones.keys()].sort((a, b) => a.localeCompare(b)), [...driver.jointOrderNative].sort((a, b) => a.localeCompare(b)), 'Complete joint coverage differs');
const meshObjects = [];
gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshObjects.push(o); });
assert.equal(meshObjects.length, driver.meshRows.length, 'Missing exported primitive/mesh');
const regionMeshes = driver.meshRows.map(row => {
  const candidates = meshObjects.filter(m => {
    const node = gltf.parser.associations.get(m)?.nodes;
    return node !== undefined && json.nodes[node].name === row.exportName;
  });
  assert.equal(candidates.length, 1, 'Ambiguous/missing declared export mesh');
  const mesh = candidates[0], idAttribute = mesh.geometry.getAttribute('_source_id');
  assert(idAttribute && idAttribute.itemSize === 1 && !idAttribute.normalized, 'Missing exact source IDs');
  assert.equal(idAttribute.count, mesh.geometry.getAttribute('position').count);
  const ids = Array.from({ length: idAttribute.count }, (_, i) => idAttribute.getX(i));
  const streams = {};
  for (const kind of ['native-full', 'native-four']) {
    const name = `${row.region}-${kind}.f64`, pin = driver.pins[name];
    const raw = fs.readFileSync(path.join(path.dirname(driverFile), name));
    assert.equal(raw.length, driver.frames.length * row.vertices * 3 * 8);
    assert.equal(raw.length, pin.bytes); assert.equal(hash(raw), pin.sha256);
    // DataView reads explicit little endian, independent of host alignment/endian.
    streams[kind] = new DataView(raw.buffer, raw.byteOffset, raw.byteLength);
  }
  const authored = mesh.geometry;
  mesh.skeleton.update();
  const restWorld = new Float64Array(ids.length * 3), restPoint = new Vector3();
  for (let i = 0; i < ids.length; i++) {
    mesh.getVertexPosition(i, restPoint); restPoint.applyMatrix4(mesh.matrixWorld);
    restPoint.toArray(restWorld, i * 3);
  }
  const release = conditionSleeveSkin(mesh), runtime = mesh.geometry;
  const weightWitness = i => {
    const from = geometry => Array.from({ length: 4 }, (_, k) => ({
      joint: mesh.skeleton.bones[geometry.getAttribute('skinIndex').getComponent(i, k)].name,
      weight: geometry.getAttribute('skinWeight').getComponent(i, k),
    }));
    const restWorldM = Array.from(restWorld.slice(i * 3, i * 3 + 3));
    return { restWorldM, authored: from(authored), runtime: from(runtime) };
  };
  const changedRows = ids.filter((_, i) => {
    const a = weightWitness(i);
    return JSON.stringify(a.authored) !== JSON.stringify(a.runtime);
  }).length;
  mesh.geometry = authored;
  return { row, mesh, ids, streams, authored, runtime, release, weightWitness, changedRows };
});
const bind = meshObjects.map(m => ({ name: m.name, bindMode: m.bindMode,
  jointOrder: m.skeleton.bones.map(b => b.name),
  inverseBindsColumnMajor: m.skeleton.boneInverses.map(m => m.toArray()),
  bindMatrixColumnMajor: m.bindMatrix.toArray(), meshWorldColumnMajor: m.matrixWorld.toArray() }));
const roots = gltf.scene.children.map(o => ({ name: o.name, matrixWorldColumnMajor: o.matrixWorld.toArray() }));
const rows = [], scratch = new Vector3();
let matrixMaxError = 0;
for (const frame of driver.frames) {
  assert.equal(frame.index, rows.length, 'Frame ordering/gap differs');
  assert.deepEqual(Object.keys(frame.jointWorldColumnMajor).sort((a, b) => a.localeCompare(b)), [...bones.keys()].sort((a, b) => a.localeCompare(b)));
  const wanted = new Map([...bones].map(([name, bone]) => [bone, new Matrix4().fromArray(frame.jointWorldColumnMajor[name])]));
  for (const [bone, matrix] of wanted) {
    assert(matrix.elements.every(Number.isFinite));
    const parent = wanted.get(bone.parent) ?? bone.parent.matrixWorld;
    bone.matrixAutoUpdate = false;
    bone.matrix.copy(parent.clone().invert().multiply(matrix));
  }
  gltf.scene.updateMatrixWorld(true);
  for (const [bone, matrix] of wanted) {
    const residual = Math.max(...bone.matrixWorld.elements.map((v, i) => Math.abs(v - matrix.elements[i])));
    matrixMaxError = Math.max(matrixMaxError, residual);
    assert(residual < 1e-5, 'Replayed bone matrix differs from driver');
  }
  const comparisons = [];
  for (const { row, mesh, ids, streams, authored, runtime, weightWitness } of regionMeshes) {
    mesh.skeleton.update();
    mesh.geometry = authored;
    const exported = new Float64Array(ids.length * 3);
    for (let i = 0; i < ids.length; i++) {
      mesh.getVertexPosition(i, scratch); scratch.applyMatrix4(mesh.matrixWorld);
      scratch.toArray(exported, i * 3);
    }
    const native = {};
    for (const kind of ['native-full', 'native-four']) {
      const view = streams[kind], count = row.vertices * 3;
      native[kind] = Float64Array.from({ length: count }, (_, i) => view.getFloat64((frame.index * count + i) * 8, true));
    }
    mesh.geometry = runtime;
    const runtimeExported = new Float64Array(exported.length);
    for (let i = 0; i < ids.length; i++) {
      mesh.getVertexPosition(i, scratch); scratch.applyMatrix4(mesh.matrixWorld);
      scratch.toArray(runtimeExported, i * 3);
    }
    const runtimeToExport = compareMappedPositions(exported, runtimeExported, ids.map((_, i) => i));
    runtimeToExport.indexSpace = 'Both arrays use export-row indices; original source ID attached separately';
    runtimeToExport.worst.sourceVertexID = ids[runtimeToExport.worst.exportVertexID];
    runtimeToExport.worst.weights = weightWitness(runtimeToExport.worst.exportVertexID);
    comparisons.push({ region: row.region, mesh: mesh.name,
      ...compareThreeWays(native['native-full'], native['native-four'], exported, ids), runtimeToExport,
      fullToRuntime: compareMappedPositions(native['native-full'], runtimeExported, ids) });
  }
  rows.push({ index: frame.index, timeS: frame.timeS, segment: frame.segment,
    endpoint: frame.endpoint, comparisons });
}
const summary = driver.meshRows.map(({ region }) => ({ region,
  pairings: Object.fromEntries(['fullToConditioned', 'fullToExport', 'conditionedToExport', 'runtimeToExport', 'fullToRuntime'].map(key => {
    const ranked = rows.map(frame => ({ index: frame.index, timeS: frame.timeS, segment: frame.segment,
      ...frame.comparisons.find(c => c.region === region)[key] })).sort((a, b) => b.maxM - a.maxM);
    return [key, { maxM: ranked[0].maxM, maximumRowsAboveDiagnostic: Math.max(...ranked.map(r => r.rowsAboveDiagnostic)),
      witnesses: ranked.slice(0, 3) }];
  })) }));
const report = { status: 'SAMPLED_THREE_WAY_MEASURED_UNACCEPTED',
  glbSHA256: hash(bytes), driverSHA256: hash(driverBytes), inputPins: driver.pins,
  fileWorldMetres: true, gameplayWrapperApplied: false, runtimeConditioningApplied: true,
  runtimeConditioningSourceSHA256: hash(fs.readFileSync('src/render/hero/sleeveSkin.ts')),
  changedWeightRows: regionMeshes.map(r => ({ region: r.row.region, rows: r.changedRows })),
  skinJointOrders: json.skins.map(s => s.joints.map(i => ({ nodeIndex: i, name: json.nodes[i].name }))),
  bind, roots, matrixMaxError, frames: rows.length, summary, rows,
  limits: ['Finite samples do not prove continuous interval parity.',
    'Raw GLTFLoader and default sleeve conditioning sampled independently; actual Garage capture still required.',
    'FK riding stress is not bike support or physics-driven riding.',
    'No clearance, likeness, art, device or M0-M5 acceptance.'] };
fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(report, null, 2) + '\n');
regionMeshes.forEach(r => r.release());
console.log(JSON.stringify({ status: report.status, frames: rows.length, matrixMaxError,
  summary: summary.map(r => ({ region: r.region, maxM: Object.fromEntries(Object.entries(r.pairings).map(([k, v]) => [k, v.maxM])) })) }));
