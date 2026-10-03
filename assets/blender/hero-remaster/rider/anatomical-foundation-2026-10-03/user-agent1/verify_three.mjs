import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const [file, directory] = process.argv.slice(2);
if (!file || !directory) throw new Error('Usage: verify_three.mjs GLB diagnostic-evidence');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const raw = fs.readFileSync(file);
const driverBytes = fs.readFileSync(path.join(directory, 'driver.json'));
const driver = JSON.parse(driverBytes);
if (sha(raw) !== driver.conditionedGLBSHA256) throw new Error('Export pin mismatch');
const definition = JSON.parse(raw.subarray(20, 20 + raw.readUInt32LE(12)).toString('utf8'));
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(
  raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength), '', resolve, reject));
gltf.scene.updateMatrixWorld(true);
const meshes = [], bones = new Map();
const canonical = name => name.replace(/([a-zA-Z0-9_]+)([LR])$/, '$1.$2');
gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones.set(canonical(o.name), o); });
if (bones.size !== driver.jointOrderNative.length) throw new Error('Complete joint count mismatch');
const weights = JSON.parse(fs.readFileSync(path.join(directory, 'weights.json')));
const { conditionSleeveSkin } = await import(pathToFileURL(path.resolve('src/render/hero/sleeveSkin.ts')).href);
const entries = driver.meshRows.map(row => {
  const mesh = meshes.find(m => m.name === THREE.PropertyBinding.sanitizeNodeName(row.exportName));
  if (!mesh) throw new Error('No exported mesh ' + row.exportName);
  const idAttr = mesh.geometry.getAttribute('_source_id');
  if (!idAttr) throw new Error('Explicit source ID missing: ' + mesh.name);
  const ids = Array.from(idAttr.array);
  if (!ids.every(n => Number.isInteger(n) && n >= 0 && n < row.vertices)) throw new Error('Invalid source ID');
  const seen = new Set(ids);
  const sourceWeights = weights.rows.find(r => r.region === row.region);
  const iw = mesh.geometry.getAttribute('skinWeight'), ii = mesh.geometry.getAttribute('skinIndex');
  let maxWeightError = 0, wrongJointRows = 0;
  for (let i = 0; i < ids.length; i++) {
    const actual = new Map();
    for (let k = 0; k < 4; k++) if (iw.getComponent(i, k) > 0) actual.set(
      canonical(mesh.skeleton.bones[ii.getComponent(i, k)].name), iw.getComponent(i, k));
    const intended = new Map(sourceWeights.conditionedSparseWeights[ids[i]]);
    for (const name of new Set([...actual.keys(), ...intended.keys()])) {
      maxWeightError = Math.max(maxWeightError, Math.abs((actual.get(name) ?? 0) - (intended.get(name) ?? 0)));
      if (!actual.has(name) || !intended.has(name)) wrongJointRows++;
    }
  }
  if (wrongJointRows || maxWeightError > 2e-7) throw new Error('Exported weight mismatch');
  const sources = {};
  for (const kind of ['native-full', 'native-four']) {
    const name = `${row.region}-${kind}.f64`, buf = fs.readFileSync(path.join(directory, name));
    if (sha(buf) !== driver.pins[name].sha256 || buf.length !== driver.frames.length * row.vertices * 3 * 8) throw new Error('Sample pin/shape mismatch');
    sources[kind] = new Float64Array(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  }
  const authoredGeometry = mesh.geometry;
  const release = conditionSleeveSkin(mesh), runtimeGeometry = mesh.geometry;
  mesh.geometry = authoredGeometry;
  return { row, mesh, ids, sources, authoredGeometry, runtimeGeometry, release,
    coverage: { uniqueNativeIDs: seen.size, nativeVertices: row.vertices,
      missingNativeIDs: Array.from({ length: row.vertices }, (_, i) => i).filter(i => !seen.has(i)),
      exportedRows: ids.length, duplicatedRows: ids.length - seen.size, maxWeightError, wrongJointRows,
      sourceIDAttribute: '_source_id', skinJointOrder: mesh.skeleton.bones.map(b => canonical(b.name)),
      inverseBindColumnMajor: mesh.skeleton.boneInverses.map(m => m.toArray()),
      bindMatrixColumnMajor: mesh.bindMatrix.toArray(), meshWorldColumnMajor: mesh.matrixWorld.toArray(),
      runtimeChangesGeometry: runtimeGeometry !== authoredGeometry } };
});
const v = new THREE.Vector3();
const desired = new Map();
const rows = [];
const orderedBones = [];
gltf.scene.traverse(o => { if (o.isBone) orderedBones.push(o); });
const metrics = () => ({ maximumM: 0, sumSquaresM2: 0, count: 0, verticesAbove100um: 0,
  verticesAbove1mm: 0, worst: null });
function add(m, distance, exportRow, nativeID, original, actual) {
  m.count++; m.sumSquaresM2 += distance * distance;
  m.verticesAbove100um += distance > 1e-4; m.verticesAbove1mm += distance > 1e-3;
  if (distance > m.maximumM) { m.maximumM = distance; m.worst = { exportRow, nativeID, original, actual }; }
}
for (const frame of driver.frames) {
  for (const [name, matrix] of Object.entries(frame.jointWorldColumnMajor)) desired.set(name, new THREE.Matrix4().fromArray(matrix));
  // Parents precede children, including all finger and foot bones.
  for (const bone of orderedBones) {
    const wanted = desired.get(canonical(bone.name));
    if (!wanted) throw new Error('Unposed exported joint ' + bone.name);
    bone.parent.updateWorldMatrix(true, false);
    const local = bone.parent.matrixWorld.clone().invert().multiply(wanted);
    local.decompose(bone.position, bone.quaternion, bone.scale);
    bone.updateMatrix(); bone.updateWorldMatrix(false, false);
  }
  gltf.scene.updateMatrixWorld(true);
  for (const entry of entries) {
    const { mesh, ids, sources, row } = entry;
    mesh.skeleton.update();
    const result = { frame: frame.index, timeS: frame.timeS, endpoint: frame.endpoint, region: row.region,
      nativeFullVsNativeFour: metrics(), nativeFourVsExport: metrics(), nativeFullVsExport: metrics(),
      authoredExportVsRuntime: metrics() };
    mesh.geometry = entry.authoredGeometry;
    const position = mesh.geometry.getAttribute('position');
    for (let i = 0; i < ids.length; i++) {
      const offset = (frame.index * row.vertices + ids[i]) * 3;
      const full = sources['native-full'].slice(offset, offset + 3);
      const four = sources['native-four'].slice(offset, offset + 3);
      v.fromBufferAttribute(position, i); mesh.applyBoneTransform(i, v); mesh.localToWorld(v);
      const actual = v.toArray();
      if (!actual.every(Number.isFinite)) throw new Error('Nonfinite export');
      const distance = (x, y) => Math.hypot(...x.map((n, k) => n - y[k]));
      add(result.nativeFullVsNativeFour, distance(full, four), i, ids[i], [...full], [...four]);
      add(result.nativeFourVsExport, distance(four, actual), i, ids[i], [...four], actual);
      add(result.nativeFullVsExport, distance(full, actual), i, ids[i], [...full], actual);
      mesh.geometry = entry.runtimeGeometry;
      v.fromBufferAttribute(position, i); mesh.applyBoneTransform(i, v); mesh.localToWorld(v);
      add(result.authoredExportVsRuntime, distance(actual, v.toArray()), i, ids[i], actual, v.toArray());
      mesh.geometry = entry.authoredGeometry;
    }
    for (const key of ['nativeFullVsNativeFour', 'nativeFourVsExport', 'nativeFullVsExport', 'authoredExportVsRuntime']) {
      result[key].rmsM = Math.sqrt(result[key].sumSquaresM2 / result[key].count);
      delete result[key].sumSquaresM2;
    }
    rows.push(result);
  }
}
const summary = Object.fromEntries(['nativeFullVsNativeFour', 'nativeFourVsExport', 'nativeFullVsExport', 'authoredExportVsRuntime'].map(key => {
  const worst = rows.reduce((a, b) => a[key].maximumM > b[key].maximumM ? a : b);
  return [key, { maximumM: worst[key].maximumM, worstFrame: worst.frame, timeS: worst.timeS,
    region: worst.region, witness: worst[key].worst,
    sampleRowsAbove100um: rows.filter(r => r[key].verticesAbove100um > 0).length }];
}));
const report = { status: 'UNACCEPTED sampled weight diagnostic; no construction/bike/likeness pass',
  GLBSHA256: sha(raw), driverSHA256: sha(driverBytes), samplerSHA256: sha(fs.readFileSync(import.meta.filename)),
  threeVersion: THREE.REVISION, actualGLTFLoader: true, frameCount: driver.frames.length,
  coordinateFrame: driver.axes, wrapper: driver.runtimeWrapper, driver: driver.sampling,
  skinDefinitions: definition.skins.map(s => ({ jointOrder: s.joints.map(i => definition.nodes[i].name),
    inverseBindAccessor: s.inverseBindMatrices })),
  roots: gltf.scene.children.map(o => ({ name: o.name, matrixWorldColumnMajor: o.matrixWorld.toArray() })),
  coverage: entries.map(e => ({ region: e.row.region, ...e.coverage })), summary, rows,
  limits: driver.limits };
fs.writeFileSync(path.join(directory, 'three-way-parity.json'), JSON.stringify(report, null, 2) + '\n');
entries.forEach(e => e.release());
console.log(JSON.stringify({ GLBSHA256: report.GLBSHA256, frames: report.frameCount, summary }, null, 2));
