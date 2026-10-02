// Independent CPU meshopt decode of the source bike GLB; no renderer or GPU.
import fs from 'node:fs';
import { MeshoptDecoder } from 'meshoptimizer';
const repo = '/Users/raynos/projects/games/rockhop';
const output = '/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/saddle-surface165';
const file = fs.readFileSync(`${repo}/public/models/bike-rookie.glb`);
const jsonLength = file.readUInt32LE(12);
const json = JSON.parse(file.subarray(20, 20 + jsonLength));
const binary = file.subarray(28 + jsonLength);
await MeshoptDecoder.ready;
function accessor(index) {
  const a = json.accessors[index], view = json.bufferViews[a.bufferView];
  const ext = view.extensions?.EXT_meshopt_compression;
  let bytes;
  if (ext) {
    bytes = new Uint8Array(ext.count * ext.byteStride);
    MeshoptDecoder.decodeGltfBuffer(bytes, ext.count, ext.byteStride,
      binary.subarray(ext.byteOffset, ext.byteOffset + ext.byteLength), ext.mode, ext.filter);
  } else bytes = binary.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength);
  const width = { SCALAR: 1, VEC3: 3 }[a.type];
  const size = { 5123: 2, 5125: 4, 5126: 4 }[a.componentType];
  const stride = view.byteStride ?? width * size;
  const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const result = new Float64Array(a.count * width);
  for (let i = 0; i < a.count; i++) for (let k = 0; k < width; k++) {
    const o = (a.byteOffset ?? 0) + i * stride + k * size;
    result[i * width + k] = a.componentType === 5126 ? v.getFloat32(o, true)
      : a.componentType === 5125 ? v.getUint32(o, true) : v.getUint16(o, true);
  }
  return Buffer.from(result.buffer);
}
const node = json.nodes.find(n => n.name === 'bodywork');
const p = json.meshes[node.mesh].primitives[0];
fs.writeFileSync(`${output}/bike-decoded-position.f64`, accessor(p.attributes.POSITION));
fs.writeFileSync(`${output}/bike-decoded-triangles.f64`, accessor(p.indices));
