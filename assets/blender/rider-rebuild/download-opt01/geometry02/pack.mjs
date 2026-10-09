// Runtime-only bounded precision derivative. Exact skin/animation; no topology reduction.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptEncoder } from 'meshoptimizer/encoder';
import { MeshoptDecoder } from 'meshoptimizer/decoder';
import { openGlb, accessorBytes, viewBytes, indexValues, stride, fileSha, sha } from '../geometry01/glb.mjs';

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
const removedAccessors = new Set();
const removedViews = new Set();
const provenance = [];
for (const [meshIndex, mesh] of j.meshes.entries()) {
  for (const [primitiveIndex, primitive] of mesh.primitives.entries()) {
    for (const [semantic, accessorIndex] of Object.entries(primitive.attributes)) {
      if (!['_NATIVE_ID', '_SOURCE_VERTEX_ID', '_REGION_ID'].includes(semantic)) continue;
      const bytes = await accessorBytes(source, accessorIndex);
      provenance.push({ meshIndex, primitiveIndex, semantic, accessorIndex,
        bytes: bytes.length, sha256: sha(bytes) });
      removedAccessors.add(accessorIndex);
      removedViews.add(j.accessors[accessorIndex].bufferView);
      delete primitive.attributes[semantic];
    }
  }
}
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
    const exactOriginal = exactDedup(attrs, count);
    const precision = [];
    for (const attr of attrs) {
      const a = j.accessors[attr.accessorIndex];
      const originalBytes = attr.bytes;
      attr.originalBytes = originalBytes.length;
      if (!['POSITION', 'NORMAL', 'TEXCOORD_0'].includes(attr.semantic)) continue;
      assert.equal(a.componentType, 5126);
      const floats = new Float32Array(originalBytes.buffer, originalBytes.byteOffset, originalBytes.length / 4);
      let maxError = 0;
      if (attr.semantic === 'NORMAL') {
        const quant = Buffer.alloc(count * 8);
        const values = new Int16Array(quant.buffer, quant.byteOffset, count * 4);
        for (let i = 0; i < count; i++) {
          let dot = 0, beforeNorm = 0, afterNorm = 0;
          for (let k = 0; k < 3; k++) {
            const v = floats[i * 3 + k];
            assert(Number.isFinite(v) && Math.abs(v) <= 1.000001);
            values[i * 4 + k] = Math.round(Math.max(-1, Math.min(1, v)) * 32767);
            const decoded = values[i * 4 + k] / 32767;
            dot += v * decoded; beforeNorm += v * v; afterNorm += decoded * decoded;
          }
          if (beforeNorm > 0 && afterNorm > 0) {
            maxError = Math.max(maxError, Math.acos(Math.min(1, Math.max(-1,
              dot / Math.sqrt(beforeNorm * afterNorm)))) * 180 / Math.PI);
          } else assert.equal(beforeNorm, afterNorm);
        }
        assert(maxError < 0.1, 'Normal angular error exceeded 0.1 degrees');
        attr.bytes = quant; attr.size = 8;
        a.componentType = 5122; a.normalized = true;
        j.bufferViews[a.bufferView].byteStride = 8;
        delete a.min; delete a.max;
        precision.push({ semantic: attr.semantic, format: 'SNORM16 VEC3 padded stride8', maxAngleDegrees: maxError });
      } else {
        let minValue = Infinity, maxValue = -Infinity;
        for (const v of floats) { assert(Number.isFinite(v)); minValue = Math.min(minValue, v); maxValue = Math.max(maxValue, v); }
        const uvNormalized = attr.semantic === 'TEXCOORD_0' && minValue >= 0 && maxValue <= 1;
        const quant = Buffer.alloc(count * (uvNormalized ? 4 : attr.size));
        const values = uvNormalized ? new Uint16Array(quant.buffer, quant.byteOffset, count * 2)
          : new Float32Array(quant.buffer, quant.byteOffset, floats.length);
        const components = attr.semantic === 'POSITION' ? 3 : 2;
        const min = Array(components).fill(Infinity), max = Array(components).fill(-Infinity);
        for (let i = 0; i < count; i++) {
          let errorSquared = 0;
          for (let k = 0; k < components; k++) {
            const v = floats[i * components + k];
            values[i * components + k] = Math.round(v * (uvNormalized ? 65535 : 65536));
            if (!uvNormalized) values[i * components + k] /= 65536;
            const decoded = uvNormalized ? values[i * components + k] / 65535 : values[i * components + k];
            const error = decoded - v;
            errorSquared += error * error;
            min[k] = Math.min(min[k], decoded); max[k] = Math.max(max[k], decoded);
          }
          maxError = Math.max(maxError, Math.sqrt(errorSquared));
        }
        if (attr.semantic === 'POSITION') assert(maxError < 0.00005, 'Position error exceeded 0.05mm');
        else assert(maxError * 4096 < 0.25, 'UV error exceeded 0.25 texel at 4K');
        attr.bytes = quant;
        if (uvNormalized) { attr.size = 4; a.componentType = 5123; a.normalized = true; }
        if (a.min) a.min = min;
        if (a.max) a.max = max;
        precision.push({ semantic: attr.semantic, format: uvNormalized ? 'UNORM16 VEC2' : 'FLOAT32 grid2^-16',
          sourceRange: [minValue, maxValue], maxEuclideanError: maxError,
          ...(attr.semantic === 'TEXCOORD_0' ? { maxTexelErrorAt4096: maxError * 4096 } : {}) });
      }
    }
    const { remap, representatives, unique, collisions } = exactDedup(attrs, count);
    const mapName = `mesh${meshIndex}-primitive${primitiveIndex}-source-remap.u32`;
    const representativesName = `mesh${meshIndex}-primitive${primitiveIndex}-representatives.u32`;
    fs.writeFileSync(path.join(path.dirname(output), mapName), remap);
    fs.writeFileSync(path.join(path.dirname(output), representativesName), representatives);
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
      store(a.bufferView, bytes, unique, attr.size, 'ATTRIBUTES', attr.originalBytes ?? attr.bytes.length);
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
      indexCount: ia.count, exactRuntimeVerticesBeforeQuantization: exactOriginal.unique,
      quantizedRuntimeVertices: unique, hashProbeCollisions: collisions, precision,
      sourceRemap: { file: mapName, sha256: sha(remap), count: remap.length },
      representatives: { file: representativesName, sha256: sha(representatives), count: representatives.length } });
    console.log(JSON.stringify(primitiveReceipts.at(-1)));
  }
}
// Animation inputs/outputs and inverse binds are compressed without editing bytes.
for (const [viewIndex, accessorIndex] of uses) {
  if (processedViews.has(viewIndex) || removedViews.has(viewIndex)) continue;
  const a = j.accessors[accessorIndex];
  const bytes = await accessorBytes(source, accessorIndex);
  assert.equal(stride(a) % 4, 0);
  store(viewIndex, bytes, a.count, stride(a), 'ATTRIBUTES', bytes.length);
}
for (const [viewIndex, view] of j.bufferViews.entries()) {
  if (processedViews.has(viewIndex) || removedViews.has(viewIndex)) continue;
  assert(imageViews.has(viewIndex), 'Unknown non-accessor view');
  const bytes = await viewBytes(source, viewIndex);
  view.buffer = 0;
  view.byteOffset = append(bytes);
}
const pad = (4 - binLength % 4) % 4;
if (pad) { fs.writeSync(binFd, Buffer.alloc(pad)); binLength += pad; }
fs.closeSync(binFd);
const accessorMap = new Map(), viewMap = new Map();
const accessors = [], views = [];
for (const [i, a] of j.accessors.entries()) {
  if (removedAccessors.has(i)) continue;
  accessorMap.set(i, accessors.length); accessors.push(a);
}
for (const [i, v] of j.bufferViews.entries()) {
  if (removedViews.has(i)) continue;
  viewMap.set(i, views.length); views.push(v);
}
for (const a of accessors) a.bufferView = viewMap.get(a.bufferView);
for (const m of j.meshes) for (const p of m.primitives) {
  p.indices = accessorMap.get(p.indices);
  for (const key of Object.keys(p.attributes)) p.attributes[key] = accessorMap.get(p.attributes[key]);
}
for (const skin of j.skins) skin.inverseBindMatrices = accessorMap.get(skin.inverseBindMatrices);
for (const animation of j.animations) for (const sampler of animation.samplers) {
  sampler.input = accessorMap.get(sampler.input); sampler.output = accessorMap.get(sampler.output);
}
for (const image of j.images) image.bufferView = viewMap.get(image.bufferView);
j.accessors = accessors; j.bufferViews = views;
j.extensionsUsed = [...new Set([...(j.extensionsUsed ?? []), 'KHR_mesh_quantization'])];
j.extensionsRequired = [...new Set([...(j.extensionsRequired ?? []), 'KHR_mesh_quantization'])];
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
const receipt = { schema: 'rider-runtime-bounded-pack/v1', source: { path: input,
  sha256: expectedSha, bytes: fs.statSync(input).size }, output: { path: output,
  sha256: fileSha(output), bytes: fs.statSync(output).size },
  encoder: { package: 'meshoptimizer', version: '1.1.1', bitstreamVersion: 0,
    attributeFilter: 'NONE', indexMode: 'INDICES', workers: 0 },
  policy: { runtimeAttributeBitwiseDedup: true, quantization: true,
    triangleReorder: false, unreferencedVertexPrune: false,
    animationResample: false, imageReencode: false },
  originalAccessorBytes: decodedBefore, deduplicatedAccessorBytes: decodedAfter,
  compressedAccessorBytes: viewReceipts.reduce((s, v) => s + v.stored, 0),
  primitives: primitiveReceipts, views: viewReceipts, provenance,
  accessorMap: Object.fromEntries(accessorMap), viewMap: Object.fromEntries(viewMap),
  sourceUnits: 'meters; exact source selected rider coordinates',
  provenanceRuntimeUse: 'rg found zero matches in src for _NATIVE_ID, _SOURCE_VERTEX_ID, _REGION_ID',
  constraints: { positionErrorMeters: 0.00005, normalErrorDegrees: 0.1, uvErrorTexels4096: 0.25,
    jointWeightBytesExact: true, animationBytesExact: true, inverseBindBytesExact: true,
    restNodeMetadataExact: true, topologySimplification: false },
  elapsedSeconds: (performance.now() - started) / 1000,
  peakRssBytes: process.resourceUsage().maxRSS * 1024,
  unsupportedInputCases: ['External buffers', 'Sparse accessors', 'Interleaved views',
    'Shared accessor views', 'Morph targets', 'Non-triangle mesh primitives',
    'Attribute strides not divisible by four', 'Unsigned-byte indices'] };
fs.mkdirSync(path.dirname(receiptPath), { recursive: true });
fs.writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
console.log(JSON.stringify({ output: receipt.output, elapsedSeconds: receipt.elapsedSeconds,
  peakRssBytes: receipt.peakRssBytes }));
