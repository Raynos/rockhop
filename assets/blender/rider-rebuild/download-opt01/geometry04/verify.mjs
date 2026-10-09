// Complete weight-only derivative proof, with a conservative native-pose bound.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptDecoder as ThreeDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { openGlb, viewBytes, accessorBytes, fileSha, sha, readAt } from '../geometry01/glb.mjs';
import { buildSkinEnvelope, quantizeWeights } from './skin-envelope.mjs';
const [input, output, packPath, proofPath] = process.argv.slice(2);
assert(input && output && packPath && proofPath);
const start = performance.now(), source = openGlb(input), packed = openGlb(output);
const a = source.json, b = packed.json, pack = JSON.parse(fs.readFileSync(packPath));
assert.equal(fileSha(input), pack.source.sha256); assert.equal(fileSha(output), pack.output.sha256);
const envelope = await buildSkinEnvelope(source);
const weightIndices = new Set(pack.weights.map(row => row.accessor));
const proof = { schema: 'rider-normalized-weight-parity/v1', pass: false,
  source: pack.source, output: pack.output, metadata: {}, weights: [],
  unchangedAccessors: [], images: [], productionDecoderViews: [],
  nativeEnvelope: envelope.receipt };
for (const key of Object.keys(a).filter(k => !['buffers', 'bufferViews', 'accessors'].includes(k))) {
  assert.deepEqual(a[key], b[key], `Metadata changed: ${key}`);
  proof.metadata[key] = { exact: true, sha256: sha(Buffer.from(JSON.stringify(a[key]))) };
}
assert.equal(a.accessors.length, b.accessors.length);
assert.equal(a.bufferViews.length, b.bufferViews.length);
for (const [i, beforeAc] of a.accessors.entries()) {
  const afterAc = b.accessors[i];
  if (weightIndices.has(i)) {
    const expected = { ...beforeAc, componentType: 5123, normalized: true };
    delete expected.min; delete expected.max;
    assert.deepEqual(expected, afterAc);
    continue;
  }
  assert.deepEqual(beforeAc, afterAc);
  const before = await viewBytes(source, beforeAc.bufferView), after = await viewBytes(packed, afterAc.bufferView);
  assert(before.equals(after), `Unchanged accessor changed: ${i}`);
  proof.unchangedAccessors.push({ accessor: i, bytes: before.length, sha256: sha(before), exact: true });
}
let worst = 0, allVertices = 0;
for (const row of pack.weights) {
  const primitive = a.meshes[row.mesh].primitives[row.primitive];
  const positionsBytes = await accessorBytes(source, primitive.attributes.POSITION);
  const positions = new Float32Array(positionsBytes.buffer, positionsBytes.byteOffset, positionsBytes.length / 4);
  const joints = await accessorBytes(source, primitive.attributes.JOINTS_0);
  const beforeBytes = await accessorBytes(source, row.accessor);
  const before = new Float32Array(beforeBytes.buffer, beforeBytes.byteOffset, beforeBytes.length / 4);
  const afterBytes = await accessorBytes(packed, row.accessor);
  const after = new Uint16Array(afterBytes.buffer, afterBytes.byteOffset, afterBytes.length / 2);
  let maxBound = 0, maxComponent = 0, maxL1 = 0, worstVertex = -1;
  let nonzeroSlotDrops = 0;
  for (let v = 0; v < row.vertices; v++) {
    const original = Array.from(before.subarray(v * 4, v * 4 + 4));
    const expected = quantizeWeights(original);
    const q = Array.from(after.subarray(v * 4, v * 4 + 4));
    assert.deepEqual(q, expected); assert.equal(q.reduce((sum, w) => sum + w, 0), 65535);
    const sum = original.reduce((sum, w) => sum + w, 0);
    // Effective Float32 shader inputs after actual GLTFLoader normalization.
    const normalizedBefore = original.map(w => Math.fround(w / sum));
    const normalizedAfter = q.map(w => Math.fround(w / 65535));
    let l1 = 0;
    for (let slot = 0; slot < 4; slot++) {
      const error = Math.abs(normalizedAfter[slot] - normalizedBefore[slot]);
      maxComponent = Math.max(maxComponent, error); l1 += error;
      nonzeroSlotDrops += original[slot] > 0 && q[slot] === 0;
    }
    maxL1 = Math.max(maxL1, l1);
    const bound = envelope.weightErrorBound(Array.from(positions.subarray(v * 3, v * 3 + 3)),
      Array.from(joints.subarray(v * 4, v * 4 + 4)), normalizedBefore, normalizedAfter);
    if (bound > maxBound) { maxBound = bound; worstVertex = v; }
  }
  assert(maxBound < 0.0001, 'Weight-only native deformation bound exceeded 0.1mm');
  const receipt = { mesh: row.mesh, primitive: row.primitive, name: a.meshes[row.mesh].name,
    vertices: row.vertices, everyVertexChecked: true, integerSumAlways65535: true,
    maxEffectiveFloat32ComponentError: maxComponent, maxEffectiveFloat32L1Error: maxL1,
    maxWeightOnlyDeformationBoundMeters: maxBound, worstVertex, nonzeroSlotDrops,
    unchangedUint8Joints: true, noTriUvPositionNormalChanges: true };
  proof.weights.push(receipt); allVertices += row.vertices; worst = Math.max(worst, maxBound);
  console.log(JSON.stringify(receipt));
}
for (const [i, image] of a.images.entries()) {
  const before = await viewBytes(source, image.bufferView), after = await viewBytes(packed, b.images[i].bufferView);
  assert(before.equals(after)); proof.images.push({ image: i, bytes: before.length, sha256: sha(before), exact: true });
}
await ThreeDecoder.ready;
for (const [i, view] of b.bufferViews.entries()) {
  const ext = view.extensions?.EXT_meshopt_compression;
  if (!ext) continue;
  const expected = await viewBytes(packed, i), decoded = Buffer.alloc(view.byteLength);
  ThreeDecoder.decodeGltfBuffer(decoded, ext.count, ext.byteStride,
    readAt(packed.fd, ext.byteLength, packed.binOffset + ext.byteOffset), ext.mode, ext.filter);
  assert(expected.equals(decoded)); proof.productionDecoderViews.push({ view: i, bytes: view.byteLength, exact: true });
}
proof.allVertices = allVertices;
proof.maxWeightOnlyDeformationBoundMeters = worst;
proof.pass = true; proof.elapsedSeconds = (performance.now() - start) / 1000;
proof.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.closeSync(source.fd); fs.closeSync(packed.fd);
fs.writeFileSync(proofPath, `${JSON.stringify(proof, null, 2)}\n`);
console.log(JSON.stringify({ pass: true, weightOnlyBoundMeters: worst,
  elapsedSeconds: proof.elapsedSeconds, peakRssBytes: proof.peakRssBytes }));
