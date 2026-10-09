// Lossless exact dedup + meshopt v0. Sequential, file-backed, no image changes.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptEncoder } from 'meshoptimizer/encoder';
import { MeshoptDecoder } from 'meshoptimizer/decoder';
import { openGlb, accessorBytes, viewBytes, indexValues, stride, fileSha } from './glb.mjs';

const [input, output, receiptPath] = process.argv.slice(2);
assert(input && output && receiptPath, 'Usage: pack.mjs input.glb output.glb receipt.json');
const expectedSha = '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649';
assert.equal(fileSha(input), expectedSha, 'Wrong selected rider source');
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const started = performance.now();
const source = openGlb(input);
const j = structuredClone(source.json);
assert.deepEqual(j.buffers, [{ byteLength: 358320904 }]);
assert(!j.extensionsUsed?.includes('EXT_meshopt_compression'));
const uses = new Map();
for (const [i, a] of j.accessors.entries()) {
  assert(!uses.has(a.bufferView), 'Shared views unsupported in this selected-only recipe');
  uses.set(a.bufferView, i);
}
const imageViews = new Set(j.images.map(i => i.bufferView));
fs.mkdirSync(path.dirname(output), { recursive: true });
const binPath = `${output}.bin.tmp`;
const binFd = fs.openSync(binPath, 'w');
let binLength = 0;
let fallbackLength = 0;
let decodedBefore = 0;
let decodedAfter = 0;
const processedViews = new Set();
const viewReceipts = [];
const primitiveReceipts = [];
function append(bytes) {
  const padding = (4 - binLength % 4) % 4;
  if (padding) { fs.writeSync(binFd, Buffer.alloc(padding)); binLength += padding; }
  const offset = binLength;
  fs.writeSync(binFd, bytes);
  binLength += bytes.length;
  return offset;
}
function store(viewIndex, bytes, count, size, mode, oldSize) {
  assert(!processedViews.has(viewIndex));
  processedViews.add(viewIndex);
  const view = j.bufferViews[viewIndex];
  // INDICES retains exact corner order; TRIANGLES can cyclically rotate corners.
  const encoded = MeshoptEncoder.encodeGltfBuffer(bytes, count, size, mode, 0);
  const decoded = Buffer.alloc(bytes.length);
  MeshoptDecoder.decodeGltfBuffer(decoded, count, size, encoded, mode);
  assert(bytes.equals(decoded), `Codec changed bytes in view ${viewIndex}`);
  decodedBefore += oldSize;
  decodedAfter += bytes.length;
  if (encoded.length < bytes.length) {
    const offset = append(encoded);
    view.buffer = 1;
    view.byteOffset = fallbackLength;
    fallbackLength += bytes.length;
    view.byteLength = bytes.length;
    view.extensions = { ...(view.extensions ?? {}), EXT_meshopt_compression: {
      buffer: 0, byteOffset: offset, byteLength: encoded.length,
      byteStride: size, count, mode, filter: 'NONE',
    } };
  } else {
    view.buffer = 0;
    view.byteOffset = append(bytes);
    view.byteLength = bytes.length;
  }
  viewReceipts.push({ view: viewIndex, before: oldSize, deduplicated: bytes.length,
    stored: Math.min(bytes.length, encoded.length), mode, losslessDecode: true });
}
function exactDedup(attrs, count) {
  const words = attrs.map(a => {
    assert.equal(a.size % 4, 0, 'Selected attributes must have 4-byte strides');
    return { words: new Uint32Array(a.bytes.buffer, a.bytes.byteOffset, a.bytes.length / 4),
      stride: a.size / 4 };
  });
  let capacity = 1;
  while (capacity < count * 2) capacity *= 2;
  const table = new Uint32Array(capacity);
  const remap = new Uint32Array(count);
  const representatives = new Uint32Array(count);
  let unique = 0;
  let collisions = 0;
  function equal(a, b) {
    for (const stream of words) {
      for (let k = 0; k < stream.stride; k++) {
        if (stream.words[a * stream.stride + k] !== stream.words[b * stream.stride + k]) return false;
      }
    }
    return true;
  }
  for (let vertex = 0; vertex < count; vertex++) {
    let hash = 2166136261;
    for (const stream of words) {
      for (let k = 0; k < stream.stride; k++) {
        hash = Math.imul(hash ^ stream.words[vertex * stream.stride + k], 16777619);
      }
    }
    // Avalanche before probing; equality always checks every attribute bit.
    hash ^= hash >>> 16;
    hash = Math.imul(hash, 0x85ebca6b);
    hash ^= hash >>> 13;
    let slot = hash & (capacity - 1);
    while (table[slot] && !equal(vertex, table[slot] - 1)) {
      collisions++;
      slot = (slot + 1) & (capacity - 1);
    }
    if (table[slot]) remap[vertex] = remap[table[slot] - 1];
    else {
      table[slot] = vertex + 1;
      remap[vertex] = unique;
      representatives[unique++] = vertex;
    }
  }
  return { remap, representatives: representatives.subarray(0, unique), unique, collisions };
}
for (const [meshIndex, mesh] of j.meshes.entries()) {
  for (const [primitiveIndex, primitive] of mesh.primitives.entries()) {
    assert.equal(primitive.mode ?? 4, 4);
    assert(!primitive.targets, 'Morph targets require a separate explicit implementation');
    const attrs = [];
    const count = j.accessors[primitive.attributes.POSITION].count;
    for (const [semantic, accessorIndex] of Object.entries(primitive.attributes)) {
      const a = j.accessors[accessorIndex];
      assert.equal(a.count, count);
      attrs.push({ semantic, accessorIndex, size: stride(a), bytes: await accessorBytes(source, accessorIndex) });
    }
    const { remap, representatives, unique, collisions } = exactDedup(attrs, count);
    for (const attr of attrs) {
      const a = j.accessors[attr.accessorIndex];
      let bytes = attr.bytes;
      if (unique !== count) {
        bytes = Buffer.alloc(unique * attr.size);
        for (let i = 0; i < unique; i++) {
          attr.bytes.copy(bytes, i * attr.size,
            representatives[i] * attr.size, (representatives[i] + 1) * attr.size);
        }
      }
      a.count = unique;
      store(a.bufferView, bytes, unique, attr.size, 'ATTRIBUTES', attr.bytes.length);
    }
    const ia = j.accessors[primitive.indices];
    const originalIndices = await accessorBytes(source, primitive.indices);
    const indices = indexValues(originalIndices, ia);
    const result = Buffer.alloc(originalIndices.length);
    const newIndices = indexValues(result, ia);
    let min = Infinity, max = -Infinity;
    for (let i = 0; i < indices.length; i++) {
      assert(indices[i] < count);
      newIndices[i] = remap[indices[i]];
      min = Math.min(min, newIndices[i]);
      max = Math.max(max, newIndices[i]);
    }
    if (ia.min) ia.min = [min];
    if (ia.max) ia.max = [max];
    store(ia.bufferView, result, ia.count, stride(ia), 'INDICES', originalIndices.length);
    primitiveReceipts.push({ mesh: meshIndex, primitive: primitiveIndex, name: mesh.name,
      attributes: attrs.map(a => a.semantic), originalVertices: count,
      uniqueVertices: unique, mergedVertices: count - unique,
      indexCount: ia.count, hashProbeCollisions: collisions });
    console.log(JSON.stringify(primitiveReceipts.at(-1)));
  }
}
// Animation inputs/outputs and inverse binds are compressed without editing bytes.
for (const [viewIndex, accessorIndex] of uses) {
  if (processedViews.has(viewIndex)) continue;
  const a = j.accessors[accessorIndex];
  const bytes = await accessorBytes(source, accessorIndex);
  assert.equal(stride(a) % 4, 0);
  store(viewIndex, bytes, a.count, stride(a), 'ATTRIBUTES', bytes.length);
}
for (const [viewIndex, view] of j.bufferViews.entries()) {
  if (processedViews.has(viewIndex)) continue;
  assert(imageViews.has(viewIndex), 'Unknown non-accessor view');
  const bytes = await viewBytes(source, viewIndex);
  view.buffer = 0;
  view.byteOffset = append(bytes);
}
const pad = (4 - binLength % 4) % 4;
if (pad) { fs.writeSync(binFd, Buffer.alloc(pad)); binLength += pad; }
fs.closeSync(binFd);
j.buffers = [{ byteLength: binLength }, { byteLength: fallbackLength,
  extensions: { EXT_meshopt_compression: { fallback: true } } }];
j.extensionsUsed = [...new Set([...(j.extensionsUsed ?? []), 'EXT_meshopt_compression'])];
j.extensionsRequired = [...new Set([...(j.extensionsRequired ?? []), 'EXT_meshopt_compression'])];
let json = Buffer.from(JSON.stringify(j));
json = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]);
const header = Buffer.alloc(20);
header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4);
header.writeUInt32LE(28 + json.length + binLength, 8);
header.writeUInt32LE(json.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
const binHeader = Buffer.alloc(8);
binHeader.writeUInt32LE(binLength); binHeader.writeUInt32LE(0x004e4942, 4);
const outputFd = fs.openSync(output, 'w');
fs.writeSync(outputFd, header); fs.writeSync(outputFd, json); fs.writeSync(outputFd, binHeader);
const inputBinFd = fs.openSync(binPath, 'r');
const chunk = Buffer.alloc(1024 * 1024);
let n;
while ((n = fs.readSync(inputBinFd, chunk))) fs.writeSync(outputFd, chunk.subarray(0, n));
fs.closeSync(inputBinFd); fs.closeSync(outputFd); fs.closeSync(source.fd);
fs.unlinkSync(binPath);
const receipt = { schema: 'rider-lossless-geometry-pack/v1', source: { path: input,
  sha256: expectedSha, bytes: fs.statSync(input).size }, output: { path: output,
  sha256: fileSha(output), bytes: fs.statSync(output).size },
  encoder: { package: 'meshoptimizer', version: '1.1.1', bitstreamVersion: 0,
    attributeFilter: 'NONE', indexMode: 'INDICES', workers: 0 },
  policy: { fullAttributeBitwiseDedup: true, quantization: false,
    triangleReorder: false, unreferencedVertexPrune: false,
    animationResample: false, imageReencode: false },
  originalAccessorBytes: decodedBefore, deduplicatedAccessorBytes: decodedAfter,
  compressedAccessorBytes: viewReceipts.reduce((s, v) => s + v.stored, 0),
  primitives: primitiveReceipts, views: viewReceipts,
  elapsedSeconds: (performance.now() - started) / 1000,
  peakRssBytes: process.resourceUsage().maxRSS * 1024,
  unsupportedInputCases: ['External buffers', 'Sparse accessors', 'Interleaved views',
    'Shared accessor views', 'Morph targets', 'Non-triangle mesh primitives',
    'Attribute strides not divisible by four', 'Unsigned-byte indices'] };
fs.mkdirSync(path.dirname(receiptPath), { recursive: true });
fs.writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
console.log(JSON.stringify({ output: receipt.output, elapsedSeconds: receipt.elapsedSeconds,
  peakRssBytes: receipt.peakRssBytes }));
