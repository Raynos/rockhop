// Exact storage helpers for the selected rider. No glTF scene transforms.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { MeshoptDecoder } from 'meshoptimizer/decoder';

export const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export function fileSha(path) {
  const hash = crypto.createHash('sha256');
  const fd = fs.openSync(path, 'r');
  const chunk = Buffer.alloc(1024 * 1024);
  let n;
  while ((n = fs.readSync(fd, chunk))) hash.update(chunk.subarray(0, n));
  fs.closeSync(fd);
  return hash.digest('hex');
}
export function readAt(fd, length, offset) {
  const result = Buffer.alloc(length);
  let n = 0;
  while (n < length) {
    const got = fs.readSync(fd, result, n, length - n, offset + n);
    assert(got > 0, 'Unexpected EOF');
    n += got;
  }
  return result;
}
export function openGlb(path) {
  const fd = fs.openSync(path, 'r');
  const header = readAt(fd, 20, 0);
  assert.equal(header.readUInt32LE(0), 0x46546c67);
  assert.equal(header.readUInt32LE(4), 2);
  assert.equal(header.readUInt32LE(8), fs.statSync(path).size);
  assert.equal(header.readUInt32LE(16), 0x4e4f534a);
  const jsonLength = header.readUInt32LE(12);
  const json = JSON.parse(readAt(fd, jsonLength, 20));
  const binHeader = readAt(fd, 8, 20 + jsonLength);
  assert.equal(binHeader.readUInt32LE(4), 0x004e4942);
  return { fd, json, binOffset: 28 + jsonLength };
}
export async function viewBytes(glb, index) {
  const view = glb.json.bufferViews[index];
  const ext = view.extensions?.EXT_meshopt_compression;
  if (ext) {
    assert.equal(ext.buffer, 0);
    assert.equal(ext.filter ?? 'NONE', 'NONE');
    await MeshoptDecoder.ready;
    const bytes = Buffer.alloc(view.byteLength);
    MeshoptDecoder.decodeGltfBuffer(bytes, ext.count, ext.byteStride,
      readAt(glb.fd, ext.byteLength, glb.binOffset + (ext.byteOffset ?? 0)),
      ext.mode, ext.filter);
    return bytes;
  }
  assert.equal(view.buffer, 0);
  return readAt(glb.fd, view.byteLength, glb.binOffset + (view.byteOffset ?? 0));
}
const components = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
const sizes = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 };
export function stride(accessor) {
  const n = components[accessor.type] * sizes[accessor.componentType];
  assert(Number.isInteger(n) && n > 0, 'Unsupported accessor format');
  return n;
}
export async function accessorBytes(glb, index) {
  const accessor = glb.json.accessors[index];
  assert(!accessor.sparse, 'Sparse accessors unsupported');
  assert.equal(accessor.byteOffset ?? 0, 0);
  const view = glb.json.bufferViews[accessor.bufferView];
  assert(!view.byteStride || view.byteStride === stride(accessor));
  const bytes = await viewBytes(glb, accessor.bufferView);
  assert.equal(bytes.length, accessor.count * stride(accessor));
  return bytes;
}
export function indexValues(bytes, accessor) {
  assert.equal(accessor.type, 'SCALAR');
  assert([5123, 5125].includes(accessor.componentType));
  return accessor.componentType === 5123
    ? new Uint16Array(bytes.buffer, bytes.byteOffset, accessor.count)
    : new Uint32Array(bytes.buffer, bytes.byteOffset, accessor.count);
}
