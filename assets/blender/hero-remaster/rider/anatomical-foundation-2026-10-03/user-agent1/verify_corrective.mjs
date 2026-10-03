import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { correctiveCoefficients } from './corrective_controller.mjs';
const [originalFile, candidateFile, driverFile, streamDirectory, prototypeReport, output] = process.argv.slice(2);
if (!output) throw new Error('original candidate driver streamdirectory prototypereport output required');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(candidateFile), originalBytes = fs.readFileSync(originalFile);
const driverBytes = fs.readFileSync(driverFile), driver = JSON.parse(driverBytes);
const expandedBytes = fs.readFileSync(path.join(streamDirectory, 'expanded-driver.json')), expanded = JSON.parse(expandedBytes);
const authored = JSON.parse(fs.readFileSync(prototypeReport));
if (sha(bytes) !== expanded.GLBSHA256 || sha(driverBytes) !== expanded.poseDriverSHA256) throw new Error('Pin mismatch');
const parse = async b => new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '');
const original = await parse(originalBytes), candidate = await parse(bytes);
original.scene.updateMatrixWorld(true); candidate.scene.updateMatrixWorld(true);
const collect = scene => { const meshes = [], bones = []; scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones.push(o); }); return { meshes, bones }; };
const before = collect(original.scene), after = collect(candidate.scene);
if (after.meshes.length !== 3 || after.bones.length !== 51) throw new Error('Dressed selection/joints changed');
const hashArray = a => sha(Buffer.from(a.buffer, a.byteOffset, a.byteLength));
const conservation = after.meshes.map(mesh => {
  const reference = before.meshes.find(m => m.name === mesh.name);
  if (!reference || JSON.stringify(mesh.skeleton.bones.map(b => [b.name, b.parent?.name])) !== JSON.stringify(reference.skeleton.bones.map(b => [b.name, b.parent?.name]))) throw new Error('Bone hierarchy/order changed');
  if (mesh.skeleton.boneInverses.some((m, i) => m.elements.some((x, j) => x !== reference.skeleton.boneInverses[i].elements[j]))) throw new Error('Inverse bind changed');
  const normalRecalculation = [];
  const attributes = Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([name, a]) => {
    const old = reference.geometry.attributes[name].array;
    if (hashArray(a.array) !== hashArray(old)) {
      const changed = [], maximum = a.array.reduce((m, value, i) => {
        const delta = Math.abs(value - old[i]); if (delta) changed.push(i); return Math.max(m, delta);
      }, 0);
      if (name !== 'normal' || !mesh.name.startsWith('Separate_fitted_sweatshirt') || maximum > 1e-3) throw new Error('Base attribute changed: ' + mesh.name + '/' + name);
      normalRecalculation.push({ attribute: name, changedComponents: changed.length, maximumComponentDelta: maximum,
        firstChangedComponents: changed.slice(0, 12).map(i => ({ index: i, original: old[i], candidate: a.array[i] })) });
    }
    return [name, hashArray(a.array)];
  }));
  if (hashArray(mesh.geometry.index.array) !== hashArray(reference.geometry.index.array)) throw new Error('Base index changed');
  return { mesh: mesh.name, rows: mesh.geometry.attributes.position.count, baseAttributeHashes: attributes,
    indicesSHA256: hashArray(mesh.geometry.index.array), normalRecalculation, all51JointOrderHierarchyBindsIdentical: true };
});
const entries = expanded.configs.map(config => {
  const source = driver.meshRows.find(r => r.region === config.region);
  const mesh = after.meshes.find(m => m.name === THREE.PropertyBinding.sanitizeNodeName(source.exportName));
  const ids = Array.from(mesh.geometry.attributes._source_id.array);
  const native = {};
  for (const kind of ['native-full', 'native-four']) {
    const filename = `${config.region}-corrective-${kind}.f64`, data = fs.readFileSync(path.join(streamDirectory, filename));
    if (sha(data) !== expanded.pins[filename].sha256 || data.length !== driver.frames.length * source.vertices * 24) throw new Error('Stream pin/size');
    native[kind] = new Float64Array(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
  }
  const targets = config.keys.map(name => {
    const index = mesh.morphTargetDictionary[name];
    if (!Number.isInteger(index) || !mesh.geometry.morphTargetsRelative) throw new Error('Missing relative morph: ' + name);
    const positions = mesh.geometry.morphAttributes.position[index];
    const row = authored.construction.find(r => r.key === name);
    const actualSupport = new Set(); let maximumNativeDeltaErrorM = 0;
    for (let i = 0; i < ids.length; i++) {
      const a = [positions.getX(i), positions.getY(i), positions.getZ(i)];
      const d = row.deltasNativeM[ids[i]], expected = [d[0], d[2], -d[1]];
      maximumNativeDeltaErrorM = Math.max(maximumNativeDeltaErrorM, Math.hypot(...a.map((x, j) => x - expected[j])));
      if (Math.hypot(...a) > 1e-8) actualSupport.add(ids[i]);
    }
    if (maximumNativeDeltaErrorM > 1e-6 || JSON.stringify([...actualSupport].sort((a, b) => a - b)) !== JSON.stringify(config.supportIDs)) throw new Error('Morph source support/delta mismatch');
    return { name, index, nativeSupportVertices: actualSupport.size, maximumNativeDeltaErrorM };
  });
  return { config, source, mesh, ids, native, targets, metrics: { nativeFourVsLoadedMaximumM: 0, nativeFullVsFourMaximumM: 0, worst: null } };
});
const canonical = name => name.replace(/([a-zA-Z0-9_]+)([LR])$/, '$1.$2');
let maxCoefficientError = 0, maxMatrixError = 0;
const position = new THREE.Vector3();
const frameMetrics = [];
for (const frame of driver.frames) {
  for (const bone of after.bones) {
    const desired = new THREE.Matrix4().fromArray(frame.jointWorldColumnMajor[canonical(bone.name)]);
    bone.parent.updateWorldMatrix(true, false); bone.matrixAutoUpdate = false;
    bone.matrix.copy(bone.parent.matrixWorld).invert().multiply(desired); bone.matrixWorldNeedsUpdate = true; bone.updateWorldMatrix(false, false, true);
    maxMatrixError = Math.max(maxMatrixError, ...bone.matrixWorld.elements.map((x, i) => Math.abs(x - desired.elements[i])));
  }
  candidate.scene.updateMatrixWorld(true);
  for (const entry of entries) {
    const values = correctiveCoefficients(frame.poseBasisBlender, entry.config, expanded.centers[entry.config.region]);
    entry.mesh.morphTargetInfluences.fill(0);
    entry.targets.forEach((target, i) => {
      const recorded = expanded.frames[frame.index].coefficients[entry.config.region][target.name];
      maxCoefficientError = Math.max(maxCoefficientError, Math.abs(values[i] - recorded));
      entry.mesh.morphTargetInfluences[target.index] = values[i];
    });
    if (frame.index === 0 && values.some(v => v !== 0)) throw new Error('Rest corrective not exactly zero');
    entry.mesh.skeleton.update(); let maximum = 0;
    for (let i = 0; i < entry.ids.length; i++) {
      const offset = (frame.index * entry.source.vertices + entry.ids[i]) * 3;
      entry.mesh.getVertexPosition(i, position); entry.mesh.localToWorld(position);
      const four = entry.native['native-four'], full = entry.native['native-full'];
      const residual = Math.hypot(position.x - four[offset], position.y - four[offset + 1], position.z - four[offset + 2]);
      const loss = Math.hypot(full[offset] - four[offset], full[offset + 1] - four[offset + 1], full[offset + 2] - four[offset + 2]);
      maximum = Math.max(maximum, residual); entry.metrics.nativeFullVsFourMaximumM = Math.max(entry.metrics.nativeFullVsFourMaximumM, loss);
      if (residual > entry.metrics.nativeFourVsLoadedMaximumM) {
        entry.metrics.nativeFourVsLoadedMaximumM = residual; entry.metrics.worst = { frame: frame.index, nativeID: entry.ids[i], exportedRow: i };
      }
    }
    frameMetrics.push({ frame: frame.index, region: entry.config.region, nativeFourVsLoadedMaximumM: maximum });
  }
}
console.log(JSON.stringify({ diagnosticCoefficientError: maxCoefficientError, diagnosticMatrixError: maxMatrixError, regions: entries.map(e => ({ region: e.config.region, ...e.metrics })) }));
if (maxCoefficientError > 1e-8 || entries.some(e => e.metrics.nativeFourVsLoadedMaximumM > 1e-4)) throw new Error('Corrective controller/runtime parity failed');
const report = { status: 'UNACCEPTED local corrective base/support/controller/native runtime parity; moving/art/fit gates open',
  candidateSHA256: sha(bytes), originalSHA256: sha(originalBytes), driverSHA256: sha(driverBytes), expandedDriverSHA256: sha(expandedBytes),
  controllerImplementationSHA256: sha(fs.readFileSync(new URL('./corrective_controller.mjs', import.meta.url))),
  verifierSHA256: sha(fs.readFileSync(import.meta.filename)), frames: driver.frames.length, conservation,
  exactRestZero: true, maximumCoefficientError: maxCoefficientError, maximumJointWorldMatrixResidual: maxMatrixError,
  regions: entries.map(e => ({ region: e.config.region, targets: e.targets, ...e.metrics })), frameMetrics,
  limits: ['Body and garment base positions/UV/sourceIDs/weights/indices/51joint hierarchy/order/binds unchanged; tiny shirt base normal recalculation explicitly recorded; morphs deliberately alter only117shirt/55jeans source vertices.',
    'ActualGLTFLoader and getVertexPosition apply morph then skin; exact same shared matrices and recorded controller.',
    'Full/four source-weight loss remains separate; no legacy runtime conditioning or normalplayer integration claimed.',
    'Native local rays improve but remaining local/global contacts and held-out regressions remain; not fit/art acceptance.'] };
fs.mkdirSync(path.dirname(output), { recursive: true }); fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ frames: report.frames, coefficients: maxCoefficientError, regions: report.regions }, null, 2));
