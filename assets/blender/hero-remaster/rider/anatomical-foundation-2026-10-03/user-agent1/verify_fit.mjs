import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
const [originalFile, trialFile, output] = process.argv.slice(2);
if (!originalFile || !trialFile || !output) throw new Error('Original GLB, trial GLB, report required');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(originalFile), trialBytes = fs.readFileSync(trialFile);
const parse = async b => new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '');
const original = await parse(bytes), trial = await parse(trialBytes);
original.scene.updateMatrixWorld(true); trial.scene.updateMatrixWorld(true);
const collect = scene => { const rows = []; scene.traverse(o => { if (o.isSkinnedMesh) rows.push(o); }); return rows; };
const before = collect(original.scene), after = collect(trial.scene);
if (after.length !== 3 || after.some(m => m.name.includes('boxer'))) throw new Error('Dressed selection must exclude boxers');
const arrayHash = a => sha(Buffer.from(a.buffer, a.byteOffset, a.byteLength));
const reportRows = after.map(mesh => {
  const reference = before.find(m => m.name === mesh.name);
  if (!reference) throw new Error('Unexpected garment/body identity');
  if (JSON.stringify(mesh.skeleton.bones.map(b => b.name)) !== JSON.stringify(reference.skeleton.bones.map(b => b.name))) throw new Error('Skin joint order changed');
  const inverseError = Math.max(...mesh.skeleton.boneInverses.flatMap((m, i) =>
    m.elements.map((v, j) => Math.abs(v - reference.skeleton.boneInverses[i].elements[j]))));
  if (inverseError > 1e-7) throw new Error('Bind unexpectedly changed');
  const attributes = Object.fromEntries(Object.keys(mesh.geometry.attributes).map(name => [name, {
    original: arrayHash(reference.geometry.attributes[name].array), trial: arrayHash(mesh.geometry.attributes[name].array) }]));
  if (mesh.name.startsWith('Canonical_') && Object.values(attributes).some(r => r.original !== r.trial)) throw new Error('Body data changed');
  for (const key of ['_source_id', 'skinIndex', 'skinWeight', 'uv']) if (attributes[key].original !== attributes[key].trial) throw new Error('Source identity/weights/UV changed');
  return { mesh: mesh.name, exportedRows: mesh.geometry.attributes.position.count,
    completeJoints: mesh.skeleton.bones.length, inverseBindMaximumError: inverseError, attributes,
    triangleIndexArrayUnchanged: arrayHash(reference.geometry.index.array) === arrayHash(mesh.geometry.index.array) };
});
const report = { status: 'REJECTED fit trial conservation proof; no clearance/visual pass',
  originalSHA256: sha(bytes), trialSHA256: sha(trialBytes), rows: reportRows,
  limits: ['Garment rest positions/normals change; body/weights/UV/sourceIDs/binds do not.',
    'Source polygon topology is unchanged; export triangulation may follow altered quad geometry.',
    'Boxers excluded from dressed diagnostic, preserved in independent fitting variant.'] };
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(reportRows.map(r => ({ mesh: r.mesh, joints: r.completeJoints,
  inverseError: r.inverseBindMaximumError, indicesUnchanged: r.triangleIndexArrayUnchanged }))));
