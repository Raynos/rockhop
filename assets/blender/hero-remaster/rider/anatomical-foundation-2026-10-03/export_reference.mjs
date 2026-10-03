/** Exact action-off geometry reference. The gray stock face is a fitting control. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const [file, manifestFile, directory] = process.argv.slice(2);
if (!directory) throw new Error('Usage: export_reference.mjs boxer.glb manifest.json out');
fs.mkdirSync(directory, { recursive: true });
const raw = fs.readFileSync(file);
const gltf = await new Promise((resolve, reject) => new GLTFLoader().parse(
  raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.length), '', resolve, reject));
const manifest = JSON.parse(fs.readFileSync(manifestFile, 'utf8'));
const normalize = n => n.replace(/([a-zA-Z]+)([LR])$/, '$1.$2');
const bones = new Map(), meshes = [];
gltf.scene.traverse(o => {
  if (o.isBone) bones.set(normalize(o.name), o);
  if (o.isSkinnedMesh) meshes.push(o);
});
const result = {
  status: 'UNACCEPTED canonical fitting reference; stock gray face is NOT approved identity',
  sourceGLBSHA256: crypto.createHash('sha256').update(raw).digest('hex'),
  independentPoseManifestSHA256: crypto.createHash('sha256').update(fs.readFileSync(manifestFile)).digest('hex'),
  heightM: 1.822571873664856,
  pose: 'True straight-arm45degree A; local TRS measured on independent exported bind; no action/morph/corrective',
  rootAdapter: 'OBJ points subtract explicit file-root x0.65. OBJ is centred atx0; GLB retainsx0.65.',
  referenceOnly: 'Proportion matching to approved original remains pending; generation must not silently define a new skeleton.',
  actualApprovedHeadDonor: {
    path: '/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb',
    sha256: 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754',
    mesh: 'textured', vertices: 61393, instruction: 'Preserve exact generated head/materials; do not replace with gray native fitting face.',
  },
  outputs: [],
};
for (const pose of ['A', 'T', 'neutral']) {
  const trs = manifest.actionOffPoses[pose].localTRS;
  for (const [name, b] of bones) {
    const row = trs[name];
    if (!row) throw new Error(`Missing independent bone ${name}`);
    b.position.fromArray(row.position); b.quaternion.fromArray(row.quaternionXYZW); b.scale.fromArray(row.scale);
  }
  gltf.scene.updateMatrixWorld(true);
  const data = [];
  for (const mesh of meshes) {
    mesh.skeleton.update();
    const attributes = mesh.geometry.attributes, vertices = [];
    for (let i = 0; i < attributes.position.count; i++) {
      const v = new THREE.Vector3().fromBufferAttribute(attributes.position, i);
      mesh.applyBoneTransform(i, v); mesh.localToWorld(v); v.x -= 0.65;
      vertices.push(v.toArray());
    }
    data.push({ name: mesh.name, vertices, triangles: [...mesh.geometry.index.array] });
  }
  for (const coordinate of ['yup', 'zup']) {
    let count = 0;
    const lines = [`# ${pose} independent anatomy plus opaque boxers; metres; ${coordinate}; centredx0`,
      '# Fitting control only. Preserve approved generated head. No generation/appearance acceptance.'];
    for (const row of data) {
      lines.push(`o ${row.name}`);
      for (const v of row.vertices) {
        const p = coordinate === 'yup' ? v : [v[0], -v[2], v[1]];
        lines.push(`v ${p.map(x => x.toFixed(9)).join(' ')}`);
      }
      for (let i = 0; i < row.triangles.length; i += 3) {
        lines.push(`f ${row.triangles.slice(i, i + 3).map(v => v + count + 1).join(' ')}`);
      }
      count += row.vertices.length;
    }
    const output = path.join(directory, `${pose}-body-boxers-${coordinate}.obj`);
    fs.writeFileSync(output, lines.join('\n') + '\n');
    const bytes = fs.readFileSync(output);
    result.outputs.push({ path: path.resolve(output), pose, coordinate, bytes: bytes.length,
      sha256: crypto.createHash('sha256').update(bytes).digest('hex'), vertices: count });
  }
}
result.AWorldDirections = manifest.actionOffPoses.A.worldDirections;
result.nativeRuntimeFourWeightParity = 'Source/control01 full native weights differ up to7.65mm body and4.72mm garment in held-out raised stress; this OBJ matches exported LBS, not full-weight source.';
fs.writeFileSync(path.join(directory, 'reference-contract.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
