/** Read-only CPU geometry audit of the actual compressed bike bytes. No visual acceptance. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Matrix4, Quaternion, Vector3 } from 'three';
import { MeshoptDecoder } from 'meshoptimizer';
import type { GltfSpec } from './source-types.mjs';

const [buildPath, outputPath] = process.argv.slice(2);
assert(buildPath && outputPath, 'frozen build directory and fresh output directory required');
assert(!fs.existsSync(outputPath), 'never overwrite a geometry audit');
fs.mkdirSync(outputPath, { recursive: true });
await MeshoptDecoder.ready;
const sha = (bytes: Buffer) => crypto.createHash('sha256').update(bytes).digest('hex');
const catalog = JSON.parse(fs.readFileSync(path.join(buildPath, 'model-catalog.json'), 'utf8'));
const reports = [];
for (const name of ['bike-rookie.glb', 'bike-rookie-lod.glb', 'bike-pro.glb', 'bike-pro-lod.glb']) {
  const entry = catalog.models.find((m: { logical: string }) => m.logical === `models/${name}`);
  assert(entry, `catalog has ${name}`);
  const bytes: Buffer = fs.readFileSync(path.join(buildPath, entry.url));
  assert.equal(sha(bytes), entry.sha256, 'actual frozen build bytes match catalog');
  const publicBytes = fs.readFileSync(path.join('public/models', name));
  assert.equal(sha(publicBytes), sha(bytes), 'public bike bytes equal consumed-build bytes');
  assert.equal(bytes.readUInt32LE(0), 0x46546c67);
  assert.equal(bytes.readUInt32LE(4), 2);
  assert.equal(bytes.readUInt32LE(8), bytes.length);
  let gltf: GltfSpec | undefined, bin: Buffer | undefined;
  for (let offset = 12; offset < bytes.length;) {
    const size = bytes.readUInt32LE(offset), type = bytes.readUInt32LE(offset + 4);
    const chunk = bytes.subarray(offset + 8, offset + 8 + size);
    if (type === 0x4e4f534a) gltf = JSON.parse(chunk.toString('utf8'));
    if (type === 0x004e4942) bin = chunk;
    offset += size + 8;
  }
  assert(gltf && bin, 'JSON and BIN chunks required');
  const views = new Map<number, Uint8Array>();
  function view(index: number): Uint8Array {
    if (views.has(index)) return views.get(index)!;
    const v = gltf!.bufferViews[index]!, ext = v.extensions?.EXT_meshopt_compression;
    let decoded: Uint8Array;
    if (ext) {
      assert.equal(ext.buffer, 0, 'compressed view uses embedded BIN');
      decoded = new Uint8Array(ext.count * ext.byteStride);
      MeshoptDecoder.decodeGltfBuffer(decoded, ext.count, ext.byteStride,
        bin!.subarray(ext.byteOffset ?? 0, (ext.byteOffset ?? 0) + ext.byteLength), ext.mode, ext.filter);
    } else {
      assert.equal(v.buffer, 0, 'uncompressed view uses embedded BIN');
      decoded = bin!.subarray(v.byteOffset ?? 0, (v.byteOffset ?? 0) + v.byteLength);
    }
    views.set(index, decoded); return decoded;
  }
  function accessor(index: number): number[][] {
    const a = gltf!.accessors[index]!;
    assert(!a.sparse, 'sparse accessors require a separate implementation');
    const width = ({ SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 } as Record<string, number>)[a.type];
    assert(width, 'scalar/vector accessor required');
    const componentBytes = ({ 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 } as Record<number, number>)[a.componentType];
    assert(componentBytes, 'supported component type required');
    const v = view(a.bufferView), dv = new DataView(v.buffer, v.byteOffset, v.byteLength);
    const stride = gltf!.bufferViews[a.bufferView]!.byteStride ?? componentBytes * width;
    const read = (offset: number): number => {
      let n: number;
      switch (a.componentType) {
        case 5120: n = dv.getInt8(offset); break;
        case 5121: n = dv.getUint8(offset); break;
        case 5122: n = dv.getInt16(offset, true); break;
        case 5123: n = dv.getUint16(offset, true); break;
        case 5125: n = dv.getUint32(offset, true); break;
        case 5126: n = dv.getFloat32(offset, true); break;
        default: throw new Error('unsupported component');
      }
      if (!a.normalized) return n;
      if (a.componentType === 5120) return Math.max(-1, n / 127);
      if (a.componentType === 5121) return n / 255;
      if (a.componentType === 5122) return Math.max(-1, n / 32767);
      if (a.componentType === 5123) return n / 65535;
      throw new Error('unsupported normalized component');
    };
    return Array.from({ length: a.count }, (_, i) => Array.from({ length: width }, (_, j) => read((a.byteOffset ?? 0) + i * stride + j * componentBytes)));
  }
  const parents = new Map<number, number>();
  gltf.nodes.forEach((n, i) => (n.children ?? []).forEach(child => parents.set(child, i)));
  function nodeWorld(index: number): Matrix4 {
    const n = gltf!.nodes[index]!;
    const m = n.matrix ? new Matrix4().fromArray(n.matrix) : new Matrix4().compose(
      new Vector3().fromArray(n.translation ?? [0, 0, 0]), new Quaternion().fromArray(n.rotation ?? [0, 0, 0, 1]), new Vector3().fromArray(n.scale ?? [1, 1, 1]));
    return parents.has(index) ? nodeWorld(parents.get(index)!).multiply(m) : m;
  }
  const nodeIndex = gltf.nodes.findIndex(n => n.name === 'handlebar');
  assert(nodeIndex >= 0);
  const node = gltf.nodes[nodeIndex]!;
  assert(node.mesh !== undefined);
  const primitives = gltf.meshes[node.mesh]!.primitives;
  assert.equal(primitives.length, 1, 'current handlebar has one atlas primitive');
  const primitive = primitives[0]!;
  assert.equal(primitive.mode ?? 4, 4, 'triangle list required');
  const localPositions = accessor(primitive.attributes.POSITION!), worldMatrix = nodeWorld(nodeIndex);
  const points = localPositions.map(p => new Vector3().fromArray(p).applyMatrix4(worldMatrix));
  const indices = accessor(primitive.indices).flat(), uv = accessor(primitive.attributes.TEXCOORD_0!), normals = accessor(primitive.attributes.NORMAL!);
  assert.equal(indices.length % 3, 0);
  const welded = new Map<string, number>(), vertexIds: number[] = [];
  for (const p of points) {
    const key = p.toArray().map(n => Math.round(n * 1e6)).join(',');
    if (!welded.has(key)) welded.set(key, welded.size);
    vertexIds.push(welded.get(key)!);
  }
  const dsu = Array.from({ length: welded.size }, (_, i) => i);
  function find(i: number): number { while (dsu[i] !== i) { dsu[i] = dsu[dsu[i]!]!; i = dsu[i]!; } return i; }
  function union(a: number, b: number): void { dsu[find(a)] = find(b); }
  for (let i = 0; i < indices.length; i += 3) {
    const ids = indices.slice(i, i + 3).map(v => { assert(v >= 0 && v < points.length); return vertexIds[v]!; });
    union(ids[0]!, ids[1]!); union(ids[1]!, ids[2]!);
  }
  const components = new Map<number, number[]>();
  for (let t = 0; t < indices.length / 3; t++) {
    const key = find(vertexIds[indices[t * 3]!]!);
    if (!components.has(key)) components.set(key, []);
    components.get(key)!.push(t);
  }
  const grips = ['L', 'R'].map(side => {
    const i = gltf!.nodes.findIndex(n => n.name === `attach_grip_${side}`);
    assert(i >= 0); return { side, sourceNode: i, fileFrame: new Vector3().applyMatrix4(nodeWorld(i)).toArray() };
  });
  const frameOriginIndex = gltf.nodes.findIndex(n => n.name === 'attach_frame_origin');
  assert(frameOriginIndex >= 0);
  const frameOrigin = new Vector3().applyMatrix4(nodeWorld(frameOriginIndex)).toArray();
  const componentReports = [...components.values()].map((triangles, component) => {
    const vertices = [...new Set(triangles.flatMap(t => indices.slice(t * 3, t * 3 + 3)))];
    const min = [0, 1, 2].map(k => Math.min(...vertices.map(v => points[v]!.getComponent(k))));
    const max = [0, 1, 2].map(k => Math.max(...vertices.map(v => points[v]!.getComponent(k))));
    const center = min.map((n, k) => (n + max[k]!) / 2);
    return { component, triangleCount: triangles.length, vertexCount: vertices.length, weldedVertexCount: new Set(vertices.map(v => vertexIds[v])).size,
      minFileFrame: min, maxFileFrame: max, aabbCenter: center, sizeM: min.map((n, k) => max[k]! - n),
      distanceToGripsM: grips.map(g => ({ side: g.side, distance: new Vector3().fromArray(center).distanceTo(new Vector3().fromArray(g.fileFrame)) })),
      sourceTriangleOrdinals: triangles, sourceVertexIndices: vertices };
  });
  const geometry = { sourceSHA256: sha(bytes), logical: entry.logical, url: entry.url, nodeIndex, sourceMeshIndex: node.mesh,
    primitiveIndex: 0, material: gltf.materials[primitive.material], localPositions, fileFramePositions: points.map(p => p.toArray()), indices, uv, normals,
    bikeFrameOriginFileFrame: frameOrigin, gripMarkersFileFrame: grips,
    sourceNodeMatrix: worldMatrix.toArray(), images: gltf.images.slice(0, 3), textures: gltf.textures.slice(0, 3), samplers: gltf.samplers };
  for (let image = 0; image < 3; image++) {
    const item = gltf.images[image]!, imageBytes = view(item.bufferView);
    fs.writeFileSync(path.join(outputPath, `${name}.image${image}.jpg`), imageBytes);
  }
  fs.writeFileSync(path.join(outputPath, `${name}.decoded.json`), JSON.stringify(geometry)+'\n');
  const report = { source: entry, publicSourceSHA256: sha(publicBytes), sourceNode: { index: nodeIndex, name: node.name, matrix: worldMatrix.toArray() },
    sourceMesh: node.mesh, positionAccessor: primitive.attributes.POSITION, indexAccessor: primitive.indices,
    triangleCount: indices.length / 3, vertexCount: points.length, weldedVertexCount: welded.size,
    weldPrecisionM: 1e-6, material: gltf.materials[primitive.material]!.name, bikeFrameOriginFileFrame: frameOrigin, grips, components: componentReports,
    interpretation: 'connected component candidates only; rubber identity and fit require explicit source patch review; no contact mapping accepted' };
  fs.writeFileSync(path.join(outputPath, `${name}.components.json`), JSON.stringify(report, null, 2)+'\n');
  // Footpegs are separate rounded-box/support meshes. Retain exact source surfaces;
  // never turn their AABBs into a passing cylindrical contact approximation.
  const pegNodeIndex = gltf.nodes.findIndex(n => n.name === 'pegs');
  assert(pegNodeIndex >= 0);
  const pegNode = gltf.nodes[pegNodeIndex]!; assert(pegNode.mesh !== undefined);
  const pegPrimitive = gltf.meshes[pegNode.mesh]!.primitives[0]!;
  const pegLocal = accessor(pegPrimitive.attributes.POSITION!), pegMatrix = nodeWorld(pegNodeIndex);
  const pegPoints = pegLocal.map(p => new Vector3().fromArray(p).applyMatrix4(pegMatrix));
  const pegIndices = accessor(pegPrimitive.indices).flat(), incident = new Map<string, Set<number>>();
  const pegKeys = pegPoints.map(p => p.toArray().map(n => Math.round(n * 1e6)).join(','));
  for (let t = 0; t < pegIndices.length / 3; t++) for (const v of pegIndices.slice(t * 3, t * 3 + 3)) {
    const k = pegKeys[v]!; if (!incident.has(k)) incident.set(k, new Set()); incident.get(k)!.add(t);
  }
  const visited = new Set<number>(), pegComponents = [];
  for (let seed = 0; seed < pegIndices.length / 3; seed++) {
    if (visited.has(seed)) continue;
    const queue = [seed], triangles: number[] = []; visited.add(seed);
    for (let q = 0; q < queue.length; q++) {
      const t = queue[q]!; triangles.push(t);
      for (const v of pegIndices.slice(t * 3, t * 3 + 3)) for (const next of incident.get(pegKeys[v]!)!)
        if (!visited.has(next)) { visited.add(next); queue.push(next); }
    }
    const vertices = [...new Set(triangles.flatMap(t => pegIndices.slice(t * 3, t * 3 + 3)))];
    const min = [0, 1, 2].map(k => Math.min(...vertices.map(v => pegPoints[v]!.getComponent(k))));
    const max = [0, 1, 2].map(k => Math.max(...vertices.map(v => pegPoints[v]!.getComponent(k))));
    const edges = new Map<string, { count: number; balance: number }>();
    let degenerate = 0;
    for (const t of triangles) {
      const ids = pegIndices.slice(t * 3, t * 3 + 3), a = pegPoints[ids[0]!]!, b = pegPoints[ids[1]!]!, c = pegPoints[ids[2]!]!;
      if (b.clone().sub(a).cross(c.clone().sub(a)).lengthSq() < 1e-18) degenerate++;
      for (let i = 0; i < 3; i++) {
        const x = pegKeys[ids[i]!]!, y = pegKeys[ids[(i + 1) % 3]!]!, key = x < y ? `${x}|${y}` : `${y}|${x}`;
        const e = edges.get(key) ?? { count: 0, balance: 0 }; e.count++; e.balance += x < y ? 1 : -1; edges.set(key, e);
      }
    }
    pegComponents.push({ component: pegComponents.length, triangleCount: triangles.length,
      sourceTriangleOrdinals: triangles, sourceVertexIndices: vertices, minFileFrame: min, maxFileFrame: max,
      sizeM: min.map((n, k) => max[k]! - n), minBikeFrame: min.map((n, k) => n - frameOrigin[k]!), maxBikeFrame: max.map((n, k) => n - frameOrigin[k]!),
      geometry: { degenerateFaces: degenerate, boundaryEdges: [...edges.values()].filter(e => e.count === 1).length,
        nonmanifoldEdges: [...edges.values()].filter(e => e.count > 2).length,
        inconsistentWindingEdges: [...edges.values()].filter(e => e.count === 2 && e.balance !== 0).length } });
  }
  const pegReport = { sourceSHA256: sha(bytes), logical: entry.logical, sourceNodeIndex: pegNodeIndex, sourceMeshIndex: pegNode.mesh, primitiveIndex: 0,
    sourceNodeMatrix: pegMatrix.toArray(), localPositions: pegLocal, fileFramePositions: pegPoints.map(p => p.toArray()),
    indices: pegIndices, normals: accessor(pegPrimitive.attributes.NORMAL!), uv: accessor(pegPrimitive.attributes.TEXCOORD_0!),
    material: gltf.materials[pegPrimitive.material], bikeFrameOriginFileFrame: frameOrigin, components: pegComponents,
    interpretation: 'actual rounded-box footrest/support source surfaces; no accepted source patch selection or runtime mapping; cylinder/capsule must not claim these exact surfaces' };
  fs.writeFileSync(path.join(outputPath, `${name}.pegs.json`), JSON.stringify(pegReport, null, 2)+'\n');
  reports.push(report);
}
const summary = { method: 'actual frozen-build/public-identical GLB bytes; installed MeshoptDecoder incl EXPONENTIAL filter; source node world transforms; position-weld connected components',
  sourceSHA256: sha(fs.readFileSync('harness/hero-remaster/contact-targets/measure-grips.mts')), reports };
fs.writeFileSync(path.join(outputPath, 'summary.json'), JSON.stringify(summary, null, 2)+'\n');
console.log(JSON.stringify(reports.map(r => ({ logical: r.source.logical, sha256: r.source.sha256, triangles: r.triangleCount, components: r.components.length,
  nearGrips: r.components.filter(c => c.distanceToGripsM.some(g => g.distance < .09)).map(c => ({ component: c.component, triangles: c.triangleCount, sizeM: c.sizeM, center: c.aabbCenter, distance: c.distanceToGripsM })) })), null, 2));
