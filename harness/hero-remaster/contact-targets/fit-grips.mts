/** Explicit source component review aid. Does not create a runtime contact mapping. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Vector3 } from 'three';
import { pointPrimitiveDistance } from '../surface-contacts.mjs';
import type { ComponentSpec, DecodedSpec, ViewSpec, AccessorSpec } from './source-types.mjs';

const [decodedPath, outputPath] = process.argv.slice(2);
assert(decodedPath && outputPath);
assert(!fs.existsSync(outputPath), 'fresh output required');
fs.mkdirSync(outputPath, { recursive: true });
const sha = (b: Buffer) => crypto.createHash('sha256').update(b).digest('hex');
const reports = [];
for (const name of ['bike-rookie.glb', 'bike-rookie-lod.glb', 'bike-pro.glb', 'bike-pro-lod.glb']) {
  const geometry = JSON.parse(fs.readFileSync(path.join(decodedPath, `${name}.decoded.json`), 'utf8')) as DecodedSpec;
  const components = JSON.parse(fs.readFileSync(path.join(decodedPath, `${name}.components.json`), 'utf8')) as { components: ComponentSpec[] };
  const grips = [0, 3].map((component, sideIndex) => {
    const patch = components.components.find(c => c.component === component);
    assert(patch, 'explicitly inspected components0/3 required');
    const unique = new Map<string, Vector3>();
    for (const vertex of patch.sourceVertexIndices) {
      const p = new Vector3().fromArray(geometry.fileFramePositions[vertex]!);
      unique.set(p.toArray().map(n => Math.round(n * 1e6)).join(','), p);
    }
    const points = [...unique.values()], center = points.reduce((sum, p) => sum.add(p), new Vector3()).divideScalar(points.length);
    const sign = sideIndex === 0 ? 1 : -1, axis = new Vector3(0, 0, sign);
    for (let step = 0; step < 24; step++) {
      const next = new Vector3();
      for (const p of points) { const q = p.clone().sub(center); next.addScaledVector(q, q.dot(axis)); }
      axis.copy(next.normalize());
    }
    const projections = points.map(p => p.clone().sub(center).dot(axis));
    const ends = [-1, 1].map(s => points.filter((_, i) => projections[i]! * s >= 0));
    const ringCenters = ends.map(group => {
      const origin = group.reduce((sum, p) => sum.add(p), new Vector3()).divideScalar(group.length);
      const u = new Vector3(1, 0, 0).cross(axis).normalize(), v = axis.clone().cross(u).normalize();
      const normal = Array.from({ length: 3 }, () => [0, 0, 0]), rhs = [0, 0, 0];
      for (const p of group) {
        const d = p.clone().sub(origin), x = d.dot(u), y = d.dot(v), row = [2 * x, 2 * y, 1], q = x * x + y * y;
        for (let i = 0; i < 3; i++) { rhs[i]! += row[i]! * q; for (let j = 0; j < 3; j++) normal[i]![j]! += row[i]! * row[j]!; }
      }
      const matrix = normal.map((row, i) => [...row, rhs[i]!]);
      for (let k = 0; k < 3; k++) {
        let pivot = k;
        for (let i = k + 1; i < 3; i++) if (Math.abs(matrix[i]![k]!) > Math.abs(matrix[pivot]![k]!)) pivot = i;
        [matrix[k], matrix[pivot]] = [matrix[pivot]!, matrix[k]!];
        const divisor = matrix[k]![k]!; assert(Math.abs(divisor) > 1e-12, 'ring circle fit is nonsingular');
        for (let j = k; j < 4; j++) matrix[k]![j]! /= divisor;
        for (let i = 0; i < 3; i++) if (i !== k) {
          const factor = matrix[i]![k]!;
          for (let j = k; j < 4; j++) matrix[i]![j]! -= factor * matrix[k]![j]!;
        }
      }
      return origin.addScaledVector(u, matrix[0]![3]!).addScaledVector(v, matrix[1]![3]!);
    });
    const fittedAxis = ringCenters[1]!.clone().sub(ringCenters[0]!).normalize();
    const radii = ends.map((group, i) => group.map(p => {
      const delta = p.clone().sub(ringCenters[i]!); return delta.addScaledVector(fittedAxis, -delta.dot(fittedAxis)).length();
    }));
    const ringStats = radii.map(values => ({ count: values.length, minimumRadiusM: Math.min(...values), maximumRadiusM: Math.max(...values),
      meanRadiusM: values.reduce((sum, n) => sum + n, 0) / values.length, radiusRangeM: Math.max(...values) - Math.min(...values) }));
    const length = ringCenters[0]!.distanceTo(ringCenters[1]!);
    const frameOrigin = new Vector3().fromArray(geometry.bikeFrameOriginFileFrame);
    const marker = geometry.gripMarkersFileFrame.find(g => g.side === (sideIndex === 0 ? 'L' : 'R'))!;
    const markerPosition = new Vector3().fromArray(marker.fileFrame), markerDelta = markerPosition.clone().sub(ringCenters[0]!);
    const markerAlong = markerDelta.dot(fittedAxis), markerRadial = markerDelta.addScaledVector(fittedAxis, -markerAlong).length();
    let degenerate = 0, inward = 0, sideFaces = 0, capFaces = 0;
    const edges = new Map<string, { count: number; balance: number }>();
    for (const t of patch.sourceTriangleOrdinals) {
      const ids = geometry.indices.slice(t * 3, t * 3 + 3) as number[];
      const tri = ids.map(i => new Vector3().fromArray(geometry.fileFramePositions[i]!));
      const normal = tri[1]!.clone().sub(tri[0]!).cross(tri[2]!.clone().sub(tri[0]!));
      if (normal.lengthSq() < 1e-18) { degenerate++; continue; }
      normal.normalize();
      const centroid = tri.reduce((sum, p) => sum.add(p), new Vector3()).multiplyScalar(1 / 3);
      const relative = centroid.clone().sub(center), along = relative.dot(fittedAxis);
      const radial = relative.clone().addScaledVector(fittedAxis, -along);
      if (Math.abs(normal.dot(fittedAxis)) > .9) {
        capFaces++; if (normal.dot(fittedAxis) * along < 0) inward++;
      } else { sideFaces++; if (normal.dot(radial) < 0) inward++; }
      const keys = tri.map(p => p.toArray().map(n => Math.round(n * 1e6)).join(','));
      for (let i = 0; i < 3; i++) {
        const a = keys[i]!, b = keys[(i + 1) % 3]!, key = a < b ? `${a}|${b}` : `${b}|${a}`;
        const e = edges.get(key) ?? { count: 0, balance: 0 }; e.count++; e.balance += a < b ? 1 : -1; edges.set(key, e);
      }
    }
    // Quantify constant-radius proxy error; source is tapered/faceted, especially after LOD.
    const proxyRadius = Math.max(...ringStats.map(r => r.maximumRadiusM));
    const radialDeficitMax = Math.max(...radii.flat().map(r => proxyRadius - r));
    let primitiveMismatchMax = 0;
    for (const t of patch.sourceTriangleOrdinals) {
      const tri = geometry.indices.slice(t * 3, t * 3 + 3).map((i: number) => new Vector3().fromArray(geometry.fileFramePositions[i]!));
      for (let i = 0; i <= 4; i++) for (let j = 0; j <= 4 - i; j++) {
        const point = tri[0]!.clone().multiplyScalar(1 - (i + j) / 4).addScaledVector(tri[1]!, i / 4).addScaledVector(tri[2]!, j / 4);
        primitiveMismatchMax = Math.max(primitiveMismatchMax, Math.abs(pointPrimitiveDistance(point, ringCenters[0]!, ringCenters[1]!, proxyRadius, 'cylinder').signedDistanceM));
      }
    }
    return { side: sideIndex === 0 ? 'L' : 'R', sourceComponent: component, sourceSHA256: geometry.sourceSHA256,
      nodeIndex: geometry.nodeIndex, sourceMeshIndex: geometry.sourceMeshIndex, primitiveIndex: 0,
      sourceTriangleOrdinals: patch.sourceTriangleOrdinals, sourceVertexIndices: patch.sourceVertexIndices,
      innerRingCenterFileFrame: ringCenters[0]!.toArray(), outerRingCenterFileFrame: ringCenters[1]!.toArray(),
      bikeFrameOriginFileFrame: frameOrigin.toArray(),
      innerRingCenterBikeFrame: ringCenters[0]!.clone().sub(frameOrigin).toArray(),
      outerRingCenterBikeFrame: ringCenters[1]!.clone().sub(frameOrigin).toArray(),
      sourceGripMarkerFileFrame: markerPosition.toArray(), sourceGripMarkerBikeFrame: markerPosition.clone().sub(frameOrigin).toArray(),
      sourceGripMarkerAxisOffsetM: markerRadial, sourceGripMarkerDistanceAlongAxisM: markerAlong,
      outwardAxisFileFrame: fittedAxis.toArray(), axisLengthM: length, endRings: ringStats,
      circleFit: 'least-squares ring circle centres in transverse plane; avoids uneven LOD vertex sampling shifting the centre',
      maximumVertexDiameterM: proxyRadius * 2, constantRadiusProxyVertexOverestimateMaxM: radialDeficitMax,
      constantRadiusProxyTriangleLatticeMismatchMaxM: primitiveMismatchMax, proxyMismatchSubdivisions: 4,
      geometryWinding: { degenerateFaces: degenerate, inwardFaces: inward, sideFaces, capFaces,
        boundaryEdges: [...edges.values()].filter(e => e.count === 1).length,
        nonmanifoldEdges: [...edges.values()].filter(e => e.count > 2).length,
        inconsistentWindingEdges: [...edges.values()].filter(e => e.count === 2 && e.balance !== 0).length },
      runtimeMappingAccepted: false, note: 'explicit source patch selection; PBR isolation still requires parent visual judgement; finite cylinder is approximate tapered/faceted source' };
  });
  // Export the explicit two source patches, retaining the original UVs, normals and PBR images.
  const selected = [...new Set(grips.flatMap(g => g.sourceTriangleOrdinals))] as number[];
  const vertices = [...new Set(selected.flatMap(t => geometry.indices.slice(t * 3, t * 3 + 3)))] as number[];
  const remap = new Map(vertices.map((v, i) => [v, i]));
  const chunks: Buffer[] = [], views: ViewSpec[] = [], accessors: (AccessorSpec & { min?: number[]; max?: number[] })[] = [];
  let total = 0;
  function add(bytes: Buffer, target?: number): number {
    const padding = (4 - total % 4) % 4;
    if (padding) { chunks.push(Buffer.alloc(padding)); total += padding; }
    const index = views.length; views.push({ buffer: 0, byteOffset: total, byteLength: bytes.length, ...(target ? { target } : {}) });
    chunks.push(bytes); total += bytes.length; return index;
  }
  const attrs: Record<string, number> = {};
  for (const [semantic, field, width] of [['POSITION', 'localPositions', 3], ['NORMAL', 'normals', 3], ['TEXCOORD_0', 'uv', 2]] as const) {
    const values = new Float32Array(vertices.flatMap(v => geometry[field][v]!));
    attrs[semantic] = accessors.length;
    const selectedValues = vertices.map(v => geometry[field][v]!);
    accessors.push({ bufferView: add(Buffer.from(values.buffer), 34962), componentType: 5126, count: vertices.length, type: width === 3 ? 'VEC3' : 'VEC2',
      ...(semantic === 'POSITION' ? { min: [0, 1, 2].map(k => Math.min(...selectedValues.map(v => v[k]!))), max: [0, 1, 2].map(k => Math.max(...selectedValues.map(v => v[k]!))) } : {}) });
  }
  const index = accessors.length, indexValues = new Uint32Array(selected.flatMap(t => geometry.indices.slice(t * 3, t * 3 + 3).map((v: number) => remap.get(v)!)));
  accessors.push({ bufferView: add(Buffer.from(indexValues.buffer), 34963), componentType: 5125, count: indexValues.length, type: 'SCALAR' });
  const images = geometry.images.map((image, i) => ({ ...image, bufferView: add(fs.readFileSync(path.join(decodedPath, `${name}.image${i}.jpg`))) }));
  const bin = Buffer.concat(chunks), document = { asset: { version: '2.0', generator: 'read-only source grip isolation' },
    scene: 0, scenes: [{ nodes: [0] }], nodes: [{ name: 'source_grips_isolation', mesh: 0, matrix: geometry.sourceNodeMatrix }],
    meshes: [{ primitives: [{ attributes: attrs, indices: index, material: 0 }] }], materials: [geometry.material],
    images, textures: geometry.textures, samplers: geometry.samplers, buffers: [{ byteLength: bin.length }], bufferViews: views, accessors };
  const json = Buffer.from(JSON.stringify(document)), jsonPadded = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]);
  const binPadded = Buffer.concat([bin, Buffer.alloc((4 - bin.length % 4) % 4)]), header = Buffer.alloc(12), jh = Buffer.alloc(8), bh = Buffer.alloc(8);
  header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4); header.writeUInt32LE(12 + 8 + jsonPadded.length + 8 + binPadded.length, 8);
  jh.writeUInt32LE(jsonPadded.length, 0); jh.writeUInt32LE(0x4e4f534a, 4); bh.writeUInt32LE(binPadded.length, 0); bh.writeUInt32LE(0x004e4942, 4);
  const isolated = Buffer.concat([header, jh, jsonPadded, bh, binPadded]);
  fs.writeFileSync(path.join(outputPath, `${name}.grips-only.glb`), isolated);
  const report = { logical: geometry.logical, sourceSHA256: geometry.sourceSHA256, grips, isolationSHA256: sha(isolated), sourcePrimitiveMaterial: geometry.material };
  fs.writeFileSync(path.join(outputPath, `${name}.fit.json`), JSON.stringify(report, null, 2)+'\n'); reports.push(report);
}
fs.writeFileSync(path.join(outputPath, 'summary.json'), JSON.stringify({ status: 'source geometry measurement only; not accepted runtime primitives or contact fit',
  sourceSHA256: sha(fs.readFileSync('harness/hero-remaster/contact-targets/fit-grips.mts')), reports }, null, 2)+'\n');
console.log(JSON.stringify(reports.map(r => ({ logical: r.logical, sha256: r.sourceSHA256, grips: r.grips.map(g => ({ side: g.side,
  lengthM: g.axisLengthM, rings: g.endRings, axis: g.outwardAxisFileFrame, winding: g.geometryWinding })) })), null, 2));
