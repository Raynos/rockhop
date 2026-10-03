// Diagnostic metadata derivative only: existing scoped loader contract, no source edit.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const [input, output, evidence] = process.argv.slice(2);
if (!input || !output || !evidence) throw new Error('Input GLB, new output GLB, evidence directory required');
if (fs.existsSync(output)) throw new Error('Preserve frozen derivative; use another leaf');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const source = fs.readFileSync(input), jsonLength = source.readUInt32LE(12);
const original = JSON.parse(source.subarray(20, 20 + jsonLength).toString('utf8'));
const document = structuredClone(original);
const roots = document.scenes[document.scene ?? 0].nodes;
if (roots.length !== 1) throw new Error('Expected one explicitly owned asset container');
const nodeIndex = roots[0], container = document.nodes[nodeIndex];
if (container.extras?.rockhopRiderSkinConditioned !== undefined) throw new Error('Existing declaration requires review');
container.extras = { ...container.extras, rockhopRiderSkinConditioned: 1 };
const encoded = Buffer.from(JSON.stringify(document));
const json = Buffer.concat([encoded, Buffer.alloc((4 - encoded.length % 4) % 4, 32)]);
const binChunk = source.subarray(20 + jsonLength);
const derived = Buffer.alloc(20 + json.length + binChunk.length);
source.copy(derived, 0, 0, 12);
derived.writeUInt32LE(derived.length, 8); derived.writeUInt32LE(json.length, 12);
derived.writeUInt32LE(0x4e4f534a, 16); json.copy(derived, 20); binChunk.copy(derived, 20 + json.length);
const stripped = structuredClone(document);
delete stripped.nodes[nodeIndex].extras.rockhopRiderSkinConditioned;
if (!original.nodes[nodeIndex].extras) delete stripped.nodes[nodeIndex].extras;
if (JSON.stringify(stripped) !== JSON.stringify(original)) throw new Error('Unexpected JSON change');
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.mkdirSync(evidence, { recursive: true });
const { conditionSleeveSkin } = await import(pathToFileURL(path.resolve('src/render/hero/sleeveSkin.ts')).href);
const { loadRig } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const { GltfRider } = await import(pathToFileURL(path.resolve('src/render/hero/gltfRider.ts')).href);
const parse = async raw => new GLTFLoader().parseAsync(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength), '');
const signature = geometry => sha(Buffer.concat(['position', 'normal', 'uv', 'skinIndex', 'skinWeight'].flatMap(name => {
  const a = geometry.getAttribute(name)?.array;
  return a ? [Buffer.from(a.buffer, a.byteOffset, a.byteLength)] : [];
})).subarray(0));
const tagged = await parse(derived);
const directRows = [];
tagged.scene.traverse(o => {
  if (!o.isSkinnedMesh) return;
  const originalGeometry = o.geometry, before = signature(originalGeometry);
  const release = conditionSleeveSkin(o);
  if (o.geometry !== originalGeometry || signature(o.geometry) !== before) throw new Error('Authored declaration not respected');
  directRows.push({ mesh: o.name, preserved: true, jointOrder: o.skeleton.bones.map(b => b.name), geometrySHA256: before });
  release();
});
const rider = new GltfRider(tagged, { complete() {} });
const cloneRows = [];
for (const stage of [true, false, true, false]) {
  rider.setStage(stage);
  rider.scene.traverse(o => {
    if (!o.isSkinnedMesh) return;
    const declared = directRows.find(r => r.mesh === o.name);
    if (signature(o.geometry) !== declared.geometrySHA256) throw new Error('Stage changed authored geometry');
    cloneRows.push({ stage: stage ? 'Garage' : 'riding', mesh: o.name, preserved: true });
  });
}
rider.dispose();

// Real shipped files through the current production decoder, textures omitted
// only in memory. A new declaring sibling must not affect their normal geometry.
const shipped = [];
for (const name of ['street-mustard', 'street-charcoal', 'street-openface', 'race-bluewhite', 'race-charcoalyellow']) {
  for (const suffix of ['', '-lod']) {
    const file = `rider-${name}${suffix}.glb`, disk = fs.readFileSync(path.join('public/models', file));
    const control = await loadRig(file);
    const first = [];
    control.scene.traverse(o => {
      if (!o.isSkinnedMesh) return;
      const originalGeometry = o.geometry;
      const release = conditionSleeveSkin(o);
      first.push({ mesh: o.name, rawSHA256: signature(originalGeometry), ridingSHA256: signature(o.geometry),
        authored: originalGeometry, release, object: o });
    });
    const parent = new THREE.Group();
    parent.add(control.scene, tagged.scene);
    const second = [];
    for (const row of first) {
      row.release(); row.object.geometry = row.authored;
      const release = conditionSleeveSkin(row.object);
      const current = signature(row.object.geometry);
      if (current !== row.ridingSHA256) throw new Error('Shipped sibling conditioning changed');
      second.push({ mesh: row.mesh, rawSHA256: row.rawSHA256, normalConditionedSHA256: current,
        taggedSiblingLeavesDefaultUnchanged: true });
      release();
    }
    if (sha(fs.readFileSync(path.join('public/models', file))) !== sha(disk)) throw new Error('Shipped disk file changed');
    shipped.push({ file, fileSHA256: sha(disk), geometry: second });
  }
}
fs.writeFileSync(output, derived);
const report = { status: 'UNACCEPTED authored-loader diagnostic; no garment/likeness pass',
  originalGLBSHA256: sha(source), derivativeGLBSHA256: sha(derived), identicalBINChunkSHA256: sha(binChunk),
  JSONChangeOnly: { nodeIndex, nodeName: container.name, key: 'rockhopRiderSkinConditioned', value: 1 },
  skinDefinitionsIdentical: JSON.stringify(original.skins) === JSON.stringify(document.skins),
  directRows, cloneRows, shipped,
  sourceHashes: Object.fromEntries(['src/render/hero/sleeveSkin.ts', 'src/render/hero/gltfRider.ts', 'src/render/hero/lod.ts'].map(file => [file, sha(fs.readFileSync(file))])),
  rationale: 'The explicit own-bind four-influence skin is the declared authoring contract; legacy spatial smoothing independently changes it up to28.100mm. Existing branch-scoped declaration preserves those authored weights.',
  limits: ['No new loader code, global optout or normal player asset edit.',
    'Pure metadata derivative does not repair garment contact, self-intersection or conditioning loss.',
    'Source/full versus four and raw versus legacy films remain separate evidence.',
    'Root alone judges moving shape and M0–M5; production promotion is not authorized.'] };
fs.writeFileSync(path.join(evidence, 'authored-declaration.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ derivativeGLBSHA256: report.derivativeGLBSHA256, identicalBINChunkSHA256: report.identicalBINChunkSHA256,
  JSONChangeOnly: report.JSONChangeOnly, verifiedMeshes: directRows.length, shippedControls: shipped.length }));
