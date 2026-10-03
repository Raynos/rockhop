/** Exercise actual preparation/cloning and keep shipped conditioning isolated. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
import { GltfRider } from '../../../src/render/hero/gltfRider.ts';
import { verifyMetadataDerivative } from './metadata.mjs';

const [originalFile, derivativeFile, ownerArg, outputFile] = process.argv.slice(2);
assert(outputFile && !fs.existsSync(outputFile), 'Usage: controls.mjs original.glb derivative.glb owner-node fresh-report');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const proof = verifyMetadataDerivative(fs.readFileSync(originalFile), fs.readFileSync(derivativeFile), Number(ownerArg));
const signature = mesh => {
  const attrs = Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([name, attr]) => {
    const values = Float64Array.from({ length: attr.count * attr.itemSize }, (_, i) => attr.getComponent(Math.floor(i / attr.itemSize), i % attr.itemSize));
    return [name, { itemSize: attr.itemSize, count: attr.count, normalized: attr.normalized,
      sha256: sha(Buffer.from(values.buffer)) }];
  }));
  return { attrs, indexSHA256: sha(Buffer.from(mesh.geometry.index.array.buffer,
    mesh.geometry.index.array.byteOffset, mesh.geometry.index.array.byteLength)),
    jointOrder: mesh.skeleton.bones.map(b => b.name),
    inverseBinds: mesh.skeleton.boneInverses.map(m => m.toArray()), bindMatrix: mesh.bindMatrix.toArray() };
};
const snapshot = scene => {
  const entries = [];
  scene.traverse(o => { if (o.isSkinnedMesh) entries.push({ mesh: o.name, signature: signature(o) }); });
  return entries;
};
async function throughRider(file) {
  const beforeHash = sha(fs.readFileSync(file));
  // Exact source BIN/decoded geometry; omit images in memory for Node execution.
  const gltf = await loadRigAt(pathToFileURL(path.resolve(file)), true);
  await prepareHero(gltf);
  const source = snapshot(gltf.scene);
  const rider = new GltfRider(gltf, { complete() {} });
  const riding = snapshot(rider.scene);
  rider.setStage(true); const garage = snapshot(rider.scene);
  rider.setStage(false); const ridingAgain = snapshot(rider.scene);
  assert.deepEqual(ridingAgain, riding, 'Stage toggling changes conditioning');
  assert.deepEqual(snapshot(gltf.scene), source, 'Actual rider changed source geometry');
  const result = { file, fileSHA256: beforeHash, source, riding, garage,
    signatures: Object.fromEntries(Object.entries({ source, riding, garage }).map(([k, v]) => [k, sha(Buffer.from(JSON.stringify(v)))])) };
  rider.dispose(); assert.equal(sha(fs.readFileSync(file)), beforeHash);
  return result;
}
const files = ['street-mustard', 'street-charcoal', 'street-openface', 'race-bluewhite', 'race-charcoalyellow']
  .flatMap(name => [`public/models/rider-${name}.glb`, `public/models/rider-${name}-lod.glb`]);
const before = [];
for (const file of files) before.push(await throughRider(file));
const raw = await throughRider(originalFile), tagged = await throughRider(derivativeFile);
assert.deepEqual(tagged.source, raw.source, 'Tagged derived geometry differs after actual preparation');
assert.deepEqual(tagged.riding, tagged.source, 'Normal tagged riding changed artist weights');
assert.deepEqual(tagged.garage, tagged.source, 'Normal tagged Garage changed artist weights');
assert.notDeepEqual(raw.riding, raw.source, 'Raw control no longer demonstrates default conditioning');
const after = [];
for (const file of files) after.push(await throughRider(file));
assert.deepEqual(after, before, 'Tagged asset changed shipped control signatures');
const loaderPins = Object.fromEntries(['src/render/hero/gltfRider.ts', 'src/render/hero/sleeveSkin.ts',
  'src/render/hero/gltf.ts', 'src/render/hero/lod.ts'].map(f => [f, sha(fs.readFileSync(f))]));
const report = { status: 'ACTUAL_PREPARATION_CLONE_SCOPE_VERIFIED_UNACCEPTED', proof, loaderPins,
  raw, tagged, shippedControls: before,
  results: { shippedControls: files.length, unchangedBeforeAfterTagged: true,
    completeTaggedGeometryAndSkinPreserved: true, sourceFilesImmutable: true },
  limits: ['Node geometry decoder omits images in memory; no material, browser or device acceptance.',
    'Actual production preparation, rider cloning and stage toggles measured; no physics pose/contact proof.'] };
fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ status: report.status, results: report.results,
  originalSHA256: proof.originalSHA256, derivativeSHA256: proof.derivativeSHA256 }));
