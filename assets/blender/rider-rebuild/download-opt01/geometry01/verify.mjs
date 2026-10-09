// Independent output reread: exact ordered triangle expansion and untouched data.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { MeshoptDecoder as ThreeDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { openGlb, accessorBytes, viewBytes, indexValues, stride, fileSha, sha, readAt } from './glb.mjs';

const [originalPath, packedPath, proofPath] = process.argv.slice(2);
assert(originalPath && packedPath && proofPath,
  'Usage: verify.mjs original.glb packed.glb proof.json');
const start = performance.now();
const original = openGlb(originalPath);
const packed = openGlb(packedPath);
const a = original.json, b = packed.json;
const proof = { schema: 'rider-decoded-parity/v1', source: {
  path: originalPath, sha256: fileSha(originalPath), bytes: fs.statSync(originalPath).size },
  output: { path: packedPath, sha256: fileSha(packedPath), bytes: fs.statSync(packedPath).size },
  pass: false, metadata: {}, primitives: [], unchangedAccessors: [], images: [],
  geometryAccessorStorage: [], productionDecoderViews: [] };
assert.equal(proof.source.sha256,
  '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');
// Everything except physical storage and deduplicated accessor counts/bounds
// is required to be identical, including semantic names and sampler refs.
const storageKeys = new Set(['buffers', 'bufferViews', 'accessors',
  'extensionsUsed', 'extensionsRequired']);
assert.deepEqual(Object.keys(a).filter(k => !storageKeys.has(k)).sort(),
  Object.keys(b).filter(k => !storageKeys.has(k)).sort());
for (const key of Object.keys(a).filter(k => !storageKeys.has(k))) {
  assert.deepEqual(a[key], b[key], `Metadata changed: ${key}`);
  proof.metadata[key] = { identical: true, sha256: sha(Buffer.from(JSON.stringify(a[key]))) };
}
assert.deepEqual(b.extensionsUsed, [...new Set([...a.extensionsUsed, 'EXT_meshopt_compression'])]);
assert.deepEqual(b.extensionsRequired, [...new Set([...(a.extensionsRequired ?? []), 'EXT_meshopt_compression'])]);
assert.equal(a.accessors.length, b.accessors.length);
assert.equal(a.bufferViews.length, b.bufferViews.length);
const geometryAccessors = new Set();
for (const [mi, mesh] of a.meshes.entries()) {
  for (const [pi, primitive] of mesh.primitives.entries()) {
    const packedPrimitive = b.meshes[mi].primitives[pi];
    const indexA = await accessorBytes(original, primitive.indices);
    const indexB = await accessorBytes(packed, packedPrimitive.indices);
    const ia = a.accessors[primitive.indices], ib = b.accessors[packedPrimitive.indices];
    assert.equal(ia.count, ib.count, 'Triangle count changed');
    const ixA = indexValues(indexA, ia), ixB = indexValues(indexB, ib);
    const p = { mesh: mi, primitive: pi, name: mesh.name,
      triangleCount: ixA.length / 3, orderedExpandedAttributes: [] };
    if (indexA.equals(indexB)) proof.geometryAccessorStorage.push({
      accessor: primitive.indices, bytes: indexA.length,
      exactByteEquality: true, sha256: sha(indexA), kind: 'indices' });
    assert.equal(ixA.length % 3, 0);
    geometryAccessors.add(primitive.indices);
    for (const [semantic, accessorIndex] of Object.entries(primitive.attributes)) {
      geometryAccessors.add(accessorIndex);
      const attrA = await accessorBytes(original, accessorIndex);
      const attrB = await accessorBytes(packed, packedPrimitive.attributes[semantic]);
      const acA = a.accessors[accessorIndex], acB = b.accessors[packedPrimitive.attributes[semantic]];
      assert.equal(stride(acA), stride(acB));
      assert.deepEqual(acA.min, acB.min);
      assert.deepEqual(acA.max, acB.max);
      if (acA.count === acB.count) {
        assert(attrA.equals(attrB), `Unmerged geometry accessor changed: ${accessorIndex}`);
        proof.geometryAccessorStorage.push({ accessor: accessorIndex,
          bytes: attrA.length, exactByteEquality: true, sha256: sha(attrA), kind: semantic });
      }
      const width = stride(acA);
      const hashA = crypto.createHash('sha256'), hashB = crypto.createHash('sha256');
      // Bounded chunk expansion preserves triangles, corners, float bits,
      // skin joint slots/weights, UV seam splits, and provenance attributes.
      const chunkA = Buffer.alloc(4096 * width), chunkB = Buffer.alloc(4096 * width);
      for (let first = 0; first < ixA.length; first += 4096) {
        const count = Math.min(4096, ixA.length - first);
        for (let k = 0; k < count; k++) {
          const vA = ixA[first + k], vB = ixB[first + k];
          assert(vA < acA.count && vB < acB.count, 'Invalid index');
          attrA.copy(chunkA, k * width, vA * width, (vA + 1) * width);
          attrB.copy(chunkB, k * width, vB * width, (vB + 1) * width);
        }
        assert(chunkA.subarray(0, count * width).equals(chunkB.subarray(0, count * width)),
          `Expanded bytes differ: mesh ${mi} primitive ${pi} ${semantic} corner ${first}`);
        hashA.update(chunkA.subarray(0, count * width));
        hashB.update(chunkB.subarray(0, count * width));
      }
      const originalSha = hashA.digest('hex'), outputSha = hashB.digest('hex');
      assert.equal(originalSha, outputSha);
      p.orderedExpandedAttributes.push({ semantic, componentType: acA.componentType,
        type: acA.type, normalized: acA.normalized ?? false,
        expandedBytes: ixA.length * width, originalSha256: originalSha,
        outputSha256: outputSha, exactByteEquality: true });
    }
    proof.primitives.push(p);
    console.log(JSON.stringify({ verifiedMesh: mi, primitive: pi, name: mesh.name }));
  }
}
for (const [i, acA] of a.accessors.entries()) {
  const acB = b.accessors[i];
  const strippedA = { ...acA }, strippedB = { ...acB };
  if (geometryAccessors.has(i)) {
    delete strippedA.count; delete strippedB.count;
    delete strippedA.min; delete strippedB.min;
    delete strippedA.max; delete strippedB.max;
  }
  assert.deepEqual(strippedA, strippedB, `Accessor metadata changed: ${i}`);
  if (geometryAccessors.has(i)) continue;
  const bytesA = await accessorBytes(original, i), bytesB = await accessorBytes(packed, i);
  assert(bytesA.equals(bytesB), `Unchanged accessor differs: ${i}`);
  proof.unchangedAccessors.push({ accessor: i, bytes: bytesA.length,
    sha256: sha(bytesA), exactByteEquality: true });
}
for (const [i, image] of a.images.entries()) {
  assert.deepEqual(image, b.images[i]);
  const bytesA = await viewBytes(original, image.bufferView);
  const bytesB = await viewBytes(packed, b.images[i].bufferView);
  assert(bytesA.equals(bytesB), `Image bytes changed: ${i}`);
  proof.images.push({ image: i, name: image.name, mimeType: image.mimeType,
    bytes: bytesA.length, sha256: sha(bytesA), exactByteEquality: true });
}
// Runtime's bundled decoder must reconstruct the same bytes as meshoptimizer.
await ThreeDecoder.ready;
for (const [viewIndex, view] of b.bufferViews.entries()) {
  const ext = view.extensions?.EXT_meshopt_compression;
  if (!ext) continue;
  const expected = await viewBytes(packed, viewIndex);
  const decoded = Buffer.alloc(view.byteLength);
  ThreeDecoder.decodeGltfBuffer(decoded, ext.count, ext.byteStride,
    readAt(packed.fd, ext.byteLength, packed.binOffset + ext.byteOffset), ext.mode, ext.filter);
  assert(expected.equals(decoded), `Production decoder changed view: ${viewIndex}`);
  proof.productionDecoderViews.push({ view: viewIndex, bytes: view.byteLength,
    exactByteEquality: true });
}
proof.skinAndAnimation = {
  skinCount: a.skins.length,
  jointOrderExact: true,
  inverseBindAccessor: a.skins[0].inverseBindMatrices,
  inverseBindBytesExact: true,
  restNodeTransformsExact: true,
  animationCount: a.animations.length,
  channelCount: a.animations.reduce((n, animation) => n + animation.channels.length, 0),
  samplerCount: a.animations.reduce((n, animation) => n + animation.samplers.length, 0),
  animationTimesAndValuesExact: true,
};
proof.pass = true;
proof.elapsedSeconds = (performance.now() - start) / 1000;
proof.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.mkdirSync(path.dirname(proofPath), { recursive: true });
fs.writeFileSync(proofPath, `${JSON.stringify(proof, null, 2)}\n`);
fs.closeSync(original.fd); fs.closeSync(packed.fd);
console.log(JSON.stringify({ pass: true, elapsedSeconds: proof.elapsedSeconds,
  peakRssBytes: proof.peakRssBytes, proofPath }));
