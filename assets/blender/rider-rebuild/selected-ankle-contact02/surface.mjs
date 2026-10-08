/** Actual GLB triangles and finite projected contact, without images or mesh edits. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Matrix4, Quaternion, Vector3, Triangle } from 'three';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
export const V = values => new Vector3().fromArray(values);
export const M = () => new Matrix4();
export const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export function pinned(row) {
  const bytes = fs.readFileSync(row.path); assert.equal(sha(bytes), row.sha256, row.path); return bytes;
}
export async function load(row) {
  await MeshoptDecoder.ready;
  const bytes = pinned(row), length = bytes.readUInt32LE(12), document = JSON.parse(bytes.subarray(20, 20 + length));
  assert.equal(bytes.toString('ascii', 0, 4), 'glTF');
  const binary = bytes.subarray(28 + length), cache = new Map(), worlds = [];
  const view = index => {
    if (cache.has(index)) return cache.get(index);
    const descriptor = document.bufferViews[index], compressed = descriptor.extensions?.EXT_meshopt_compression;
    let raw;
    if (compressed) {
      raw = new Uint8Array(compressed.count * compressed.byteStride);
      MeshoptDecoder.decodeGltfBuffer(raw, compressed.count, compressed.byteStride,
        binary.subarray(compressed.byteOffset, compressed.byteOffset + compressed.byteLength), compressed.mode, compressed.filter);
    } else raw = binary.subarray(descriptor.byteOffset ?? 0, (descriptor.byteOffset ?? 0) + descriptor.byteLength);
    const result = new DataView(raw.buffer, raw.byteOffset, raw.byteLength); cache.set(index, result); return result;
  };
  const read = index => {
    const accessor = document.accessors[index], descriptor = document.bufferViews[accessor.bufferView]; assert(!accessor.sparse);
    const components = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }[accessor.type];
    const [method, width, divisor] = { 5121: ['getUint8', 1, 255], 5123: ['getUint16', 2, 65535],
      5125: ['getUint32', 4, 4294967295], 5126: ['getFloat32', 4, 1] }[accessor.componentType];
    const data = view(accessor.bufferView);
    return { count: accessor.count, get: (row, axis = 0) => data[method]((accessor.byteOffset ?? 0)
      + row * (descriptor.byteStride ?? width * components) + axis * width, true) / (accessor.normalized ? divisor : 1),
    row(row) { return Array.from({ length: components }, (_, axis) => this.get(row, axis)); } };
  };
  const walk = (index, parent = M()) => {
    const node = document.nodes[index], local = node.matrix ? M().fromArray(node.matrix)
      : M().compose(V(node.translation ?? [0, 0, 0]), new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]), V(node.scale ?? [1, 1, 1]));
    worlds[index] = parent.clone().multiply(local);
    for (const child of node.children ?? []) walk(child, worlds[index]);
  };
  for (const index of document.scenes[document.scene ?? 0].nodes) walk(index);
  const node = name => {
    const indices = document.nodes.flatMap((node, index) => node.name === name ? [index] : []); assert.equal(indices.length, 1, name);
    const index = indices[0]; return { index, value: document.nodes[index], world: worlds[index], point: new Vector3().setFromMatrixPosition(worlds[index]) };
  };
  return { document, read, node };
}
export function mesh(glb, name, transform = M()) {
  const node = glb.node(name), primitives = glb.document.meshes[node.value.mesh].primitives; assert.equal(primitives.length, 1);
  const primitive = primitives[0], attributes = primitive.attributes, position = glb.read(attributes.POSITION), indices = glb.read(primitive.indices);
  const native = attributes._NATIVE_ID === undefined ? null : glb.read(attributes._NATIVE_ID);
  const joints = attributes.JOINTS_0 === undefined ? null : glb.read(attributes.JOINTS_0);
  const weights = attributes.WEIGHTS_0 === undefined ? null : glb.read(attributes.WEIGHTS_0);
  const names = glb.document.skins?.[node.value.skin]?.joints.map(index => glb.document.nodes[index].name);
  const world = transform.clone().multiply(node.world);
  return { name, position, indices, point: index => V(position.row(index)).applyMatrix4(world), nativeID: index => native?.get(index) ?? index,
    fields: index => joints ? Array.from({ length: 4 }, (_, axis) => [names[joints.get(index, axis)], weights.get(index, axis)]).filter(([, weight]) => weight > 0) : [] };
}
export function triangle(vertices, ids, row) {
  const points = ids.map(index => vertices[index]), shape = new Triangle(...points);
  return { row, ids, points, shape, normal: shape.getNormal(new Vector3()),
    minX: Math.min(...points.map(point => point.x)), maxX: Math.max(...points.map(point => point.x)),
    minZ: Math.min(...points.map(point => point.z)), maxZ: Math.max(...points.map(point => point.z)) };
}
const cross = (a, b, point) => (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0]);
function overlap(a, b) {
  const clip = b.points.map(point => [point.x, point.z]), orientation = Math.sign(cross(...clip));
  let polygon = a.points.map(point => [point.x, point.z]);
  for (let edge = 0; edge < 3 && polygon.length; edge++) {
    const start = clip[edge], end = clip[(edge + 1) % 3], input = polygon; polygon = [];
    for (let index = 0; index < input.length; index++) {
      const p = input[index], q = input[(index + 1) % input.length];
      const dp = orientation * cross(start, end, p), dq = orientation * cross(start, end, q);
      if (dp >= 0) polygon.push(p);
      if ((dp < 0) !== (dq < 0)) {
        const ratio = dp / (dp - dq); polygon.push([p[0] + ratio * (q[0] - p[0]), p[1] + ratio * (q[1] - p[1])]);
      }
    }
  }
  return polygon;
}
const height = (surface, x, z) => surface.points[0].y - (surface.normal.x * (x - surface.points[0].x)
  + surface.normal.z * (z - surface.points[0].z)) / surface.normal.y;
/** Linear height differences attain their extrema at clipped polygon vertices.
 * Thus this checks complete triangle footprints, rather than arbitrary sample rays.
 */
export function finiteSupport(boot, vertices, rigid, pegs) {
  let minimum = null, compared = 0, downwardRigidTriangles = 0;
  for (let row = 0; row < boot.indices.count / 3; row++) {
    const ids = [0, 1, 2].map(axis => boot.indices.get(row * 3 + axis));
    if (!ids.every(index => rigid[index])) continue;
    const sole = triangle(vertices, ids, row);
    if (sole.normal.y >= -1e-9) continue; // Numerical projection degeneracy, not a pose bound.
    downwardRigidTriangles++;
    for (const peg of pegs) {
      if (sole.maxX < peg.minX || peg.maxX < sole.minX || sole.maxZ < peg.minZ || peg.maxZ < sole.minZ) continue;
      const polygon = overlap(sole, peg); if (!polygon.length) continue; compared++;
      for (const [x, z] of polygon) {
        const bootPoint = new Vector3(x, height(sole, x, z), z), pegPoint = new Vector3(x, height(peg, x, z), z);
        const gapM = bootPoint.y - pegPoint.y;
        if (!minimum || gapM < minimum.gapM) minimum = { gapM, bootTriangleRow: row, bootVertexRows: ids,
          bootNativeIDs: ids.map(index => boot.nativeID(index)), bootBarycentric: sole.shape.getBarycoord(bootPoint, new Vector3()).toArray(),
          bootPoint: bootPoint.toArray(), bootNormal: sole.normal.toArray(), pegTriangleRow: peg.row, pegVertexRows: peg.ids,
          pegBarycentric: peg.shape.getBarycoord(pegPoint, new Vector3()).toArray(), pegPoint: pegPoint.toArray(), pegNormal: peg.normal.toArray() };
      }
    }
  }
  assert(minimum, 'Actual rigid sole and finite peg footprints do not overlap');
  return { minimum, compared, downwardRigidTriangles };
}
