import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
const [originalFile, trialFile, output] = process.argv.slice(2);
if (!originalFile || !trialFile || !output) throw new Error('Original/trial GLB and report required');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const originalBytes = fs.readFileSync(originalFile), trialBytes = fs.readFileSync(trialFile);
const parse = async b => new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '');
const original = await parse(originalBytes), trial = await parse(trialBytes);
original.scene.updateMatrixWorld(true); trial.scene.updateMatrixWorld(true);
const collect = scene => { const rows = []; scene.traverse(o => { if (o.isSkinnedMesh) rows.push(o); }); return rows; };
const before = collect(original.scene), after = collect(trial.scene);
if (after.length !== 3 || after.some(m => m.name.includes('boxer'))) throw new Error('Dressed selection must exclude boxers');
const arrayHash = a => sha(Buffer.from(a.buffer, a.byteOffset, a.byteLength));
const rows = after.map(mesh => {
  const reference = before.find(m => m.name === mesh.name);
  if (!reference) throw new Error('Unexpected mesh identity');
  const jointNames = mesh.skeleton.bones.map(b => b.name);
  if (jointNames.length !== 51 || JSON.stringify(jointNames) !== JSON.stringify(reference.skeleton.bones.map(b => b.name))) throw new Error('Joint order changed');
  const inverseError = Math.max(...mesh.skeleton.boneInverses.flatMap((m, i) => m.elements.map((v, j) => Math.abs(v - reference.skeleton.boneInverses[i].elements[j]))));
  if (inverseError > 1e-7) throw new Error('Inverse bind changed');
  const hierarchyUnchanged = mesh.skeleton.bones.every((b, i) => b.parent?.name === reference.skeleton.bones[i].parent?.name);
  if (!hierarchyUnchanged) throw new Error('Hierarchy changed');
  const body = mesh.name.startsWith('Canonical_');
  const hashes = Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([n, a]) => [n, arrayHash(a.array)]));
  const indexHash = arrayHash(mesh.geometry.index.array);
  if (body && (JSON.stringify(hashes) !== JSON.stringify(Object.fromEntries(Object.entries(reference.geometry.attributes).map(([n, a]) => [n, arrayHash(a.array)]))) || indexHash !== arrayHash(reference.geometry.index.array))) throw new Error('Body bytes changed');
  const { skinWeight, skinIndex } = mesh.geometry.attributes;
  let weightError = 0, maxInfluences = 0;
  for (let i = 0; i < skinWeight.count; i++) {
    let total = 0, influences = 0;
    for (let j = 0; j < 4; j++) {
      const w = skinWeight.array[i * 4 + j], index = skinIndex.array[i * 4 + j];
      if (!Number.isFinite(w) || w < 0 || index < 0 || index >= 51) throw new Error('Invalid weight/index');
      total += w; if (w > 0) influences++;
    }
    weightError = Math.max(weightError, Math.abs(total - 1)); maxInfluences = Math.max(maxInfluences, influences);
  }
  if (weightError > 1e-6) throw new Error('Weights not normalized');
  if (!body) for (const name of ['_pattern_id', '_source_tri', '_bary_a', '_bary_b', 'uv']) if (!mesh.geometry.attributes[name]) throw new Error('Missing pattern ancestry/UV');
  let declaration = mesh.parent;
  while (declaration && declaration.userData.rockhopRiderSkinConditioned !== 1) declaration = declaration.parent;
  if (!declaration) throw new Error('Missing authored-skin declaration');
  return { mesh: mesh.name, exportedRows: skinWeight.count, joints: jointNames.length, inverseBindMaxError: inverseError,
    hierarchyUnchanged, bodyAttributesAndIndicesByteIdentical: body ? true : null, maximumWeightSumError: weightError,
    maximumInfluences: maxInfluences, attributesSHA256: hashes, triangleIndicesSHA256: indexHash,
    declaration: declaration.name };
});
const report = { status: 'REJECTED directed attachment export conservation; no clearance/visual pass',
  originalSHA256: sha(originalBytes), trialSHA256: sha(trialBytes), rows,
  limits: ['Clothing topology/weights/rest position change deliberately; body/51 joint order/binds/hierarchy do not.',
    'Source pattern ancestry is recorded before rest projection; UVs interpolate across conforming triangles.',
    'Dressed selection excludes duplicate boxers; rejected candidate remains experimental.'] };
fs.mkdirSync(path.dirname(output), { recursive: true }); fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(rows.map(r => ({ mesh: r.mesh, rows: r.exportedRows, joints: r.joints, bodyUnchanged: r.bodyAttributesAndIndicesByteIdentical, weightError: r.maximumWeightSumError }))));
