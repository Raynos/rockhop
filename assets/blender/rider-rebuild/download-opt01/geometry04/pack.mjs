// Reusable meshopt storage repack: only Float32 skin weights become UNORM16.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptEncoder } from 'meshoptimizer/encoder';
import { MeshoptDecoder } from 'meshoptimizer/decoder';
import { openGlb, viewBytes, stride, fileSha, readAt, sha } from '../geometry01/glb.mjs';
import { quantizeWeights } from './skin-envelope.mjs';
const [input, output, receiptPath] = process.argv.slice(2);
assert(input && output && receiptPath);
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const start = performance.now(), glb = openGlb(input), doc = structuredClone(glb.json);
const weights = new Map(), indices = new Set(), uses = new Map();
for (const [mesh, m] of doc.meshes.entries()) for (const [primitive, p] of m.primitives.entries()) {
  weights.set(doc.accessors[p.attributes.WEIGHTS_0].bufferView, { mesh, primitive, accessor: p.attributes.WEIGHTS_0 });
  indices.add(doc.accessors[p.indices].bufferView);
  assert.equal(doc.accessors[p.attributes.JOINTS_0].componentType, 5121, 'Joint indices must already be exact Uint8');
}
for (const [i, a] of doc.accessors.entries()) {
  assert(!uses.has(a.bufferView), 'Shared views require a separate implementation'); uses.set(a.bufferView, i);
}
const imageViews = new Set(doc.images.map(image => image.bufferView));
fs.mkdirSync(path.dirname(output), { recursive: true });
const binPath = `${output}.bin.tmp`, binFd = fs.openSync(binPath, 'w');
let binLength = 0, fallbackLength = 0;
const views = [], weightReceipts = [];
function append(bytes) {
  const padding = (4 - binLength % 4) % 4;
  if (padding) { fs.writeSync(binFd, Buffer.alloc(padding)); binLength += padding; }
  const offset = binLength; fs.writeSync(binFd, bytes); binLength += bytes.length; return offset;
}
for (const [viewIndex, v] of doc.bufferViews.entries()) {
  const sourceBytes = await viewBytes(glb, viewIndex);
  let bytes = sourceBytes;
  delete v.extensions?.EXT_meshopt_compression;
  if (v.extensions && Object.keys(v.extensions).length === 0) delete v.extensions;
  if (imageViews.has(viewIndex)) {
    v.buffer = 0; v.byteOffset = append(bytes); v.byteLength = bytes.length; continue;
  }
  const ai = uses.get(viewIndex); assert(ai !== undefined);
  const a = doc.accessors[ai]; assert(!a.sparse && !(a.byteOffset ?? 0));
  let size = v.byteStride ?? stride(a);
  if (weights.has(viewIndex)) {
    assert.equal(a.componentType, 5126); assert.equal(a.type, 'VEC4'); assert.equal(size, 16);
    bytes = Buffer.alloc(a.count * 8);
    const q = new Uint16Array(bytes.buffer, bytes.byteOffset, a.count * 4);
    const original = new Float32Array(sourceBytes.buffer, sourceBytes.byteOffset, a.count * 4);
    let maxComponentError = 0, maxL1Error = 0;
    for (let i = 0; i < a.count; i++) {
      const values = Array.from(original.subarray(i * 4, i * 4 + 4));
      const result = quantizeWeights(values); q.set(result, i * 4);
      const sum = values.reduce((s, w) => s + w, 0);
      let l1 = 0;
      for (let slot = 0; slot < 4; slot++) {
        const error = Math.abs(Math.fround(result[slot] / 65535) - Math.fround(values[slot] / sum));
        maxComponentError = Math.max(maxComponentError, error); l1 += error;
      }
      maxL1Error = Math.max(maxL1Error, l1);
    }
    a.componentType = 5123; a.normalized = true; size = 8;
    if (v.byteStride) v.byteStride = 8;
    delete a.min; delete a.max;
    weightReceipts.push({ ...weights.get(viewIndex), vertices: a.count,
      sourceBytes: sourceBytes.length, decodedBytes: bytes.length,
      sourceSha256: sha(sourceBytes), decodedSha256: sha(bytes),
      maxNormalizedComponentError: maxComponentError, maxNormalizedL1Error: maxL1Error,
      integerSumAlways65535: true });
  }
  assert.equal(bytes.length, size * a.count);
  const mode = indices.has(viewIndex) ? 'INDICES' : 'ATTRIBUTES';
  const encoded = MeshoptEncoder.encodeGltfBuffer(bytes, a.count, size, mode, 0);
  const roundtrip = Buffer.alloc(bytes.length);
  MeshoptDecoder.decodeGltfBuffer(roundtrip, a.count, size, encoded, mode);
  assert(bytes.equals(roundtrip));
  if (encoded.length < bytes.length) {
    v.buffer = 1; v.byteOffset = fallbackLength; fallbackLength += bytes.length;
    v.byteLength = bytes.length;
    v.extensions = { ...(v.extensions ?? {}), EXT_meshopt_compression: { buffer: 0,
      byteOffset: append(encoded), byteLength: encoded.length, byteStride: size,
      count: a.count, mode, filter: 'NONE' } };
  } else { v.buffer = 0; v.byteOffset = append(bytes); v.byteLength = bytes.length; }
  views.push({ view: viewIndex, sourceDecodedBytes: sourceBytes.length,
    runtimeDecodedBytes: bytes.length, encodedBytes: Math.min(bytes.length, encoded.length) });
}
const padding = (4 - binLength % 4) % 4;
if (padding) { fs.writeSync(binFd, Buffer.alloc(padding)); binLength += padding; }
fs.closeSync(binFd);
doc.buffers = [{ byteLength: binLength }, { byteLength: fallbackLength,
  extensions: { EXT_meshopt_compression: { fallback: true } } }];
doc.extensionsUsed = [...new Set([...(doc.extensionsUsed ?? []), 'EXT_meshopt_compression'])];
doc.extensionsRequired = [...new Set([...(doc.extensionsRequired ?? []), 'EXT_meshopt_compression'])];
let json = Buffer.from(JSON.stringify(doc));
json = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]);
const header = Buffer.alloc(20); header.writeUInt32LE(0x46546c67);
header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + json.length + binLength, 8);
header.writeUInt32LE(json.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
const binHeader = Buffer.alloc(8); binHeader.writeUInt32LE(binLength); binHeader.writeUInt32LE(0x004e4942, 4);
const outputFd = fs.openSync(output, 'w');
fs.writeSync(outputFd, header); fs.writeSync(outputFd, json); fs.writeSync(outputFd, binHeader);
const temp = fs.openSync(binPath, 'r');
for (let first = 0; first < binLength; first += 1024 * 1024)
  fs.writeSync(outputFd, readAt(temp, Math.min(1024 * 1024, binLength - first), first));
fs.closeSync(temp); fs.closeSync(outputFd); fs.closeSync(glb.fd); fs.unlinkSync(binPath);
const receipt = { schema: 'rider-normalized-weight-pack/v1', accepted: false,
  source: { path: input, sha256: fileSha(input), bytes: fs.statSync(input).size },
  output: { path: output, sha256: fileSha(output), bytes: fs.statSync(output).size },
  encoder: { package: 'meshoptimizer', version: '1.1.1', bitstreamVersion: 0, filters: 'NONE', indexMode: 'INDICES' },
  weights: weightReceipts, views,
  policy: { positionNormalUvTriangleBytesUnchanged: true, jointUint8Exact: true,
    weightFormat: 'normalized UINT16 VEC4; largest remainder, integer sum65535',
    noVertexDedupOrReorder: true, noTopologyReduction: true, noImageChanges: true,
    nativeMetadataAnimationsInverseBindsExact: true },
  elapsedSeconds: (performance.now() - start) / 1000,
  peakRssBytes: process.resourceUsage().maxRSS * 1024 };
fs.mkdirSync(path.dirname(receiptPath), { recursive: true });
fs.writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
console.log(JSON.stringify({ output: receipt.output, elapsedSeconds: receipt.elapsedSeconds,
  peakRssBytes: receipt.peakRssBytes }));
