// Actual GLTFLoader geometry-format probe; no browser, renderer, or image decode.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { openGlb, readAt, fileSha, sha, viewBytes } from '../geometry01/glb.mjs';
const [input, reportPath] = process.argv.slice(2);
assert(input && reportPath);
const glb = openGlb(input), doc = structuredClone(glb.json);
const expectedWeightHashes = [];
for (const m of doc.meshes) for (const p of m.primitives) {
  const a = doc.accessors[p.attributes.WEIGHTS_0];
  expectedWeightHashes.push(sha(await viewBytes(glb, a.bufferView)));
}
const loadedWeightHashes = [];
// Material texture references are excluded only in this ignored parser probe.
// The real candidate and independent material/image identity proof stay intact.
function omitTextures(value) {
  if (!value || typeof value !== 'object') return;
  for (const key of Object.keys(value)) {
    if (key.endsWith('Texture')) delete value[key]; else omitTextures(value[key]);
  }
}
doc.materials.forEach(omitTextures);
doc.images = []; doc.textures = []; doc.samplers = [];
let json = Buffer.from(JSON.stringify(doc));
json = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]);
const binLength = glb.json.buffers[0].byteLength;
const probe = Buffer.alloc(28 + json.length + binLength);
probe.writeUInt32LE(0x46546c67); probe.writeUInt32LE(2, 4); probe.writeUInt32LE(probe.length, 8);
probe.writeUInt32LE(json.length, 12); probe.writeUInt32LE(0x4e4f534a, 16);
json.copy(probe, 20); probe.writeUInt32LE(binLength, 20 + json.length);
probe.writeUInt32LE(0x004e4942, 24 + json.length);
for (let first = 0; first < binLength; first += 1024 * 1024) {
  readAt(glb.fd, Math.min(1024 * 1024, binLength - first), glb.binOffset + first)
    .copy(probe, 28 + json.length + first);
}
fs.closeSync(glb.fd);
await MeshoptDecoder.ready;
const loaded = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
  .parseAsync(probe.buffer, '');
const meshes = [];
loaded.scene.traverse(node => {
  if (!node.isMesh) return;
  assert(node.isSkinnedMesh);
  const attrs = node.geometry.attributes;
  assert(attrs.position.array instanceof Float32Array);
  if (attrs.normal.isInterleavedBufferAttribute) {
    assert(attrs.normal.data.array instanceof Int16Array);
    assert.equal(attrs.normal.data.stride, 4); assert.equal(attrs.normal.normalized, true);
  } else assert(attrs.normal.array instanceof Float32Array);
  assert(attrs.skinIndex.array instanceof Uint8Array);
  assert(attrs.skinWeight.array instanceof Uint16Array);
  assert.equal(attrs.skinWeight.normalized, true);
  loadedWeightHashes.push(sha(attrs.skinWeight.array));
  for (let v = 0; v < attrs.skinWeight.count; v++) {
    const q = attrs.skinWeight.array;
    assert.equal(q[v * 4] + q[v * 4 + 1] + q[v * 4 + 2] + q[v * 4 + 3], 65535);
  }
  assert(!attrs._native_id && !attrs._source_vertex_id && !attrs._region_id);
  for (let i = 0; i < Math.min(10, attrs.normal.count); i++) {
    assert(Number.isFinite(attrs.normal.getX(i)) && Math.abs(attrs.normal.getX(i)) <= 1);
  }
  meshes.push({ name: node.name, vertices: attrs.position.count,
    triangles: node.geometry.index.count / 3,
    positionArray: attrs.position.array.constructor.name,
    normalArray: (attrs.normal.data?.array ?? attrs.normal.array).constructor.name,
    normalStrideElements: attrs.normal.data?.stride ?? attrs.normal.itemSize,
    normalNormalized: attrs.normal.normalized,
    weightArray: attrs.skinWeight.array.constructor.name, weightNormalized: attrs.skinWeight.normalized,
    uvArray: attrs.uv.array.constructor.name, uvNormalized: attrs.uv.normalized,
    joints: node.skeleton.bones.length });
});
assert.equal(meshes.length, 10);
assert.deepEqual(loadedWeightHashes.sort(), expectedWeightHashes.sort(), 'GLTFLoader normalization changed weight integers');
assert.equal(loaded.animations.length, 1);
const result = { pass: true, candidateSha256: fileSha(input),
  scope: 'Real Three GLTFLoader geometry/skin/animation parse; texture references omitted in memory only, no art judgment',
  meshes, weightIntegersUnchangedByLoaderNormalization: true, clip: { name: loaded.animations[0].name, tracks: loaded.animations[0].tracks.length },
  peakRssBytes: process.resourceUsage().maxRSS * 1024 };
fs.writeFileSync(reportPath, `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify({ pass: true, meshCount: meshes.length, peakRssBytes: result.peakRssBytes }));
