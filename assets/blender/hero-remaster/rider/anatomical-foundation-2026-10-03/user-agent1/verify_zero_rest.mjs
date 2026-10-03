// Check immutable successor defaults and controlled motion through actual GLTFLoader.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
const [parentFile, candidateFile, driverFile, expandedFile, output] = process.argv.slice(2);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const { loadRigAt } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const load = async file => {
  const gltf = await loadRigAt(pathToFileURL(path.resolve(file)));
  const meshes = [], bones = [];
  gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones.push(o); });
  gltf.scene.updateMatrixWorld(true);
  return { gltf, meshes, bones };
};
const parent = await load(parentFile), candidate = await load(candidateFile);
const driver = JSON.parse(fs.readFileSync(driverFile)), expanded = JSON.parse(fs.readFileSync(expandedFile));
if (parent.meshes.length !== 8 || candidate.meshes.length !== 8 || candidate.bones.length !== 51) throw Error('Unexpected admission inventory');
const a = new THREE.Vector3(), b = new THREE.Vector3();
const defaults = candidate.meshes.map((m, index) => {
  const old = parent.meshes[index];
  if (m.name !== old.name || m.geometry.attributes.position.count !== old.geometry.attributes.position.count) throw Error('Mesh ancestry changed');
  if (m.morphTargetInfluences?.some(v => v !== 0)) throw Error('Successor has nonzero default');
  m.skeleton.update(); let closure = 0;
  for (let i = 0; i < m.geometry.attributes.position.count; i++) {
    m.getVertexPosition(i, a); m.localToWorld(a); b.fromBufferAttribute(m.geometry.attributes.position, i);
    closure = Math.max(closure, a.distanceTo(b));
  }
  return { mesh: m.name, parentDefaults: old.morphTargetInfluences?.slice() ?? [], candidateDefaults: m.morphTargetInfluences?.slice() ?? [], restSkinClosureMaximumM: closure };
});
if (defaults.some(r => r.restSkinClosureMaximumM > 2e-6)) throw Error('Rest skin closure failed: ' + JSON.stringify(defaults));
const canonical = name => name.replace(/([a-zA-Z0-9_]+)([LR])$/, '$1.$2');
let maximum = 0, comparedVertices = 0;
for (const frame of driver.frames) {
  for (const loaded of [parent, candidate]) {
    for (const bone of loaded.bones) {
      const desired = new THREE.Matrix4().fromArray(frame.jointWorldColumnMajor[canonical(bone.name)]);
      bone.parent.updateWorldMatrix(true, false); bone.matrixAutoUpdate = false;
      bone.matrix.copy(bone.parent.matrixWorld).invert().multiply(desired);
      bone.matrixWorldNeedsUpdate = true; bone.updateWorldMatrix(false, false, true);
    }
    loaded.gltf.scene.updateMatrixWorld(true);
    for (const mesh of loaded.meshes) {
      if (!mesh.morphTargetInfluences) continue;
      mesh.morphTargetInfluences.fill(0);
      const region = mesh.morphTargetInfluences.length === 3 ? 'cloth' : 'jeans';
      for (const [key, value] of Object.entries(expanded.frames[frame.index].coefficients[region])) {
        const index = mesh.morphTargetDictionary[key];
        if (!Number.isInteger(index)) throw Error('Missing current primitive morph');
        mesh.morphTargetInfluences[index] = value;
      }
      mesh.skeleton.update();
    }
  }
  for (let mi = 0; mi < candidate.meshes.length; mi++) {
    const m = candidate.meshes[mi], old = parent.meshes[mi];
    if (!m.morphTargetInfluences) continue;
    for (let i = 0; i < m.geometry.attributes.position.count; i++) {
      m.getVertexPosition(i, a); m.localToWorld(a);
      old.getVertexPosition(i, b); old.localToWorld(b);
      maximum = Math.max(maximum, a.distanceTo(b)); comparedVertices++;
    }
  }
}
if (maximum !== 0) throw Error('Controlled geometry changed');
const report = { status: 'UNACCEPTED05 actual-loader zero rest and exact04 controlled-motion equivalence',
  parentGLBSHA256: sha(fs.readFileSync(parentFile)), candidateGLBSHA256: sha(fs.readFileSync(candidateFile)),
  poseDriverSHA256: sha(fs.readFileSync(driverFile)), expandedDriverSHA256: sha(fs.readFileSync(expandedFile)),
  verifierSHA256: sha(fs.readFileSync(new URL(import.meta.url))), threeRevision: THREE.REVISION,
  actualGLTFLoader: true, defaults, frames: driver.frames.length, comparedMorphVertices: comparedVertices,
  controlled04vs05MaximumM: maximum, all51Joints: true,
  limits: ['Images omitted only in memory for geometry verification.', 'Controlled04 native films remain04 evidence; no new05 capture, bike contact, art or device acceptance is claimed.'] };
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ frames: report.frames, comparedVertices, maximum, defaults }));
