// Read-only exact head donor registration; preserve raw versus imported bind spaces.
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
const [file, output] = process.argv.slice(2);
if (!file || !output) throw new Error('Exact donor file and new report path required');
if (fs.existsSync(output)) throw new Error('Preserve frozen donor report');
const raw = fs.readFileSync(file);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
if (sha(raw) !== 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754') throw new Error('Wrong exact donor lineage');
const { loadRigAt } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const gltf = await loadRigAt(pathToFileURL(path.resolve(file)), true);
gltf.scene.updateMatrixWorld(true);
const rows = [];
gltf.scene.traverse(mesh => {
  if (!mesh.isSkinnedMesh || !mesh.name.startsWith('textured')) return;
  mesh.skeleton.update();
  const position = mesh.geometry.getAttribute('position');
  const v = new THREE.Vector3(), rawBox = new THREE.Box3(), bindBox = new THREE.Box3();
  const skinJointMass = new Map();
  const weights = mesh.geometry.getAttribute('skinWeight'), indices = mesh.geometry.getAttribute('skinIndex');
  for (let i = 0; i < position.count; i++) {
    v.fromBufferAttribute(position, i); rawBox.expandByPoint(v);
    mesh.applyBoneTransform(i, v); mesh.localToWorld(v); bindBox.expandByPoint(v);
    for (let k = 0; k < 4; k++) {
      const w = weights.getComponent(i, k);
      if (w > 0) {
        const name = mesh.skeleton.bones[indices.getComponent(i, k)].name;
        skinJointMass.set(name, (skinJointMass.get(name) ?? 0) + w);
      }
    }
  }
  rows.push({ mesh: mesh.name, vertices: position.count,
    rawGLTFPositionBoundsM: [rawBox.min.toArray(), rawBox.max.toArray()],
    actualImportedRestBoundsM: [bindBox.min.toArray(), bindBox.max.toArray()],
    meshWorldColumnMajor: mesh.matrixWorld.toArray(), bindMatrixColumnMajor: mesh.bindMatrix.toArray(),
    inverseBindColumnMajor: mesh.skeleton.boneInverses.map(m => m.toArray()),
    skinJointOrder: mesh.skeleton.bones.map(b => b.name), skinJointMass: Object.fromEntries(skinJointMass),
    rawPositionSHA256: sha(Buffer.from(position.array.buffer, position.array.byteOffset, position.array.byteLength)),
    uvSHA256: sha(Buffer.from(mesh.geometry.attributes.uv.array.buffer,
      mesh.geometry.attributes.uv.array.byteOffset, mesh.geometry.attributes.uv.array.byteLength)),
    materialName: mesh.material.name });
});
const report = { status: 'READ-ONLY exact head donor registration; no graft or acceptance',
  file, sha256: sha(raw), rows,
  roots: gltf.scene.children.map(o => ({ name: o.name, matrixWorldColumnMajor: o.matrixWorld.toArray(), userData: o.userData })),
  limits: ['Source images are omitted only in memory for this geometry/bind report; disk materials/textures unchanged.',
    'Raw runtime POSITION and imported bind-rest geometry are distinct spaces.',
    'No old skin weights/inverse binds/correctives copied into the new 51-joint rig.',
    'Cloud derivative6fd9 remains distinct from exact local b7 bytes.'] };
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(rows.map(r => ({ mesh: r.mesh, vertices: r.vertices,
  raw: r.rawGLTFPositionBoundsM, imported: r.actualImportedRestBoundsM, mass: r.skinJointMass })), null, 2));
