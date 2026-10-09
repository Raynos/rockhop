// Attribute-aware reduction measurement. Selected dense garments only.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptSimplifier } from 'meshoptimizer/simplifier';
import { openGlb, accessorBytes, indexValues, fileSha, sha } from '../geometry01/glb.mjs';
const [input, outDir, mode = 'strict'] = process.argv.slice(2);
assert(input && outDir && ['strict', 'permissive', 'field'].includes(mode));
await MeshoptSimplifier.ready;
fs.mkdirSync(outDir, { recursive: true });
const glb = openGlb(input), started = performance.now();
const report = { schema: 'selected-attribute-reduction/v1', accepted: false,
  source: { path: input, sha256: fileSha(input) }, mode, meshes: [],
  errorMeaning: 'Meshopt aggregate quadric estimate, not a hard surface or deformation bound',
  settings: { targetErrorAbsoluteMeters: 0.0002, normalWeight: mode === 'field' ? 0.1 : 1, uvWeight: 8,
    skinWeightWeight: 4, targetTriangleRatio: { boots: 0.15, gloves: 0.25, hoodie: 0.1 },
    flags: ['ErrorAbsolute', 'LockBorder', 'Regularize', ...(mode !== 'strict' ? ['Permissive'] : [])],
    uvSeamPolicy: mode === 'field' ? 'Attribute-weighted only; must pass independent UV/appearance guard'
      : 'Explicit UV seam vertex locks' } };
for (const mi of [0, 1, 2, 3, 5]) {
  const start = performance.now(), mesh = glb.json.meshes[mi], p = mesh.primitives[0];
  const posBytes = await accessorBytes(glb, p.attributes.POSITION);
  const positions = new Float32Array(posBytes.buffer, posBytes.byteOffset, posBytes.length / 4);
  const count = positions.length / 3;
  const normalsBytes = await accessorBytes(glb, p.attributes.NORMAL);
  const normals = new Float32Array(normalsBytes.buffer, normalsBytes.byteOffset, normalsBytes.length / 4);
  const uvBytes = await accessorBytes(glb, p.attributes.TEXCOORD_0);
  const uvs = new Float32Array(uvBytes.buffer, uvBytes.byteOffset, uvBytes.length / 4);
  const jointBytes = await accessorBytes(glb, p.attributes.JOINTS_0);
  const joints = new Uint32Array(jointBytes.buffer, jointBytes.byteOffset, jointBytes.length / 4);
  const weightBytes = await accessorBytes(glb, p.attributes.WEIGHTS_0);
  const weights = new Float32Array(weightBytes.buffer, weightBytes.byteOffset, weightBytes.length / 4);
  const sourceIndices = indexValues(await accessorBytes(glb, p.indices), glb.json.accessors[p.indices]);
  const indices = new Uint32Array(sourceIndices);
  const attrs = new Float32Array(count * 9);
  for (let v = 0; v < count; v++) {
    attrs.set(normals.subarray(v * 3, v * 3 + 3), v * 9);
    attrs.set(uvs.subarray(v * 2, v * 2 + 2), v * 9 + 3);
    attrs.set(weights.subarray(v * 4, v * 4 + 4), v * 9 + 5);
  }
  const remap = MeshoptSimplifier.generatePositionRemap(positions, 3);
  const locks = new Uint8Array(count), uvSeams = new Uint8Array(count);
  const jointSeams = new Uint8Array(count), nonmanifold = new Uint8Array(count);
  for (let v = 0; v < count; v++) {
    const r = remap[v];
    if (joints[v] !== joints[r]) jointSeams[r] = 1;
    if (uvs[v * 2] !== uvs[r * 2] || uvs[v * 2 + 1] !== uvs[r * 2 + 1]) uvSeams[r] = 1;
  }
  // Lock every geometric vertex incident to an edge with differing JOINTS slots.
  for (let first = 0; first < indices.length; first += 3) {
    const t = [indices[first], indices[first + 1], indices[first + 2]];
    for (let k = 0; k < 3; k++) {
      const a = t[k], b = t[(k + 1) % 3];
      if (joints[a] !== joints[b]) { jointSeams[remap[a]] = 1; jointSeams[remap[b]] = 1; }
    }
  }
  // Detect geometric nonmanifold junctions explicitly and lock their endpoints.
  const edges = new BigUint64Array(indices.length);
  const edge = (a, b) => BigInt(Math.min(a, b)) | (BigInt(Math.max(a, b)) << 32n);
  for (let i = 0; i < indices.length; i += 3) {
    const a = remap[indices[i]], b = remap[indices[i + 1]], c = remap[indices[i + 2]];
    edges[i] = edge(a, b); edges[i + 1] = edge(b, c); edges[i + 2] = edge(c, a);
  }
  edges.sort();
  for (let first = 0; first < edges.length;) {
    let end = first + 1;
    while (end < edges.length && edges[end] === edges[first]) end++;
    if (end - first > 2 || end - first === 1) {
      nonmanifold[Number(edges[first] & 0xffffffffn)] = 1;
      nonmanifold[Number(edges[first] >> 32n)] = 1;
    }
    first = end;
  }
  for (let v = 0; v < count; v++) {
    const r = remap[v];
    locks[v] = jointSeams[r] || nonmanifold[r] ? 1
      : uvSeams[r] ? (mode === 'field' ? 0 : mode === 'permissive' ? 2 : 1) : 0;
  }
  const ratio = mi < 2 ? 0.15 : mi < 4 ? 0.25 : 0.1;
  const target = Math.floor(indices.length * ratio / 3) * 3;
  const [reduced, error] = MeshoptSimplifier.simplifyWithAttributes(indices, positions, 3,
    attrs, 9, [report.settings.normalWeight, report.settings.normalWeight,
      report.settings.normalWeight, 8, 8, 4, 4, 4, 4], locks, target, 0.0002,
    report.settings.flags);
  const output = path.join(outDir, `mesh${mi}-indices.u32`);
  fs.writeFileSync(output, reduced);
  const used = new Uint8Array(count);
  for (const index of reduced) used[index] = 1;
  const row = { mesh: mi, name: mesh.name, originalTriangles: indices.length / 3,
    targetTriangles: target / 3, triangles: reduced.length / 3,
    triangleReductionPercent: (1 - reduced.length / indices.length) * 100,
    referencedVertices: used.reduce((s, v) => s + v, 0), originalVertices: count,
    aggregateEstimatedErrorMeters: error,
    fullyLockedRows: locks.reduce((s, v) => s + (v === 1), 0),
    protectedSeamRows: locks.reduce((s, v) => s + (v === 2), 0),
    jointBoundaryPositions: jointSeams.reduce((s, v) => s + v, 0),
    borderOrNonmanifoldPositions: nonmanifold.reduce((s, v) => s + v, 0),
    indices: { path: output, sha256: sha(reduced), bytes: reduced.byteLength },
    elapsedSeconds: (performance.now() - start) / 1000 };
  report.meshes.push(row); console.log(JSON.stringify(row));
}
report.elapsedSeconds = (performance.now() - started) / 1000;
report.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.closeSync(glb.fd); fs.writeFileSync(path.join(outDir, 'reduction.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ elapsedSeconds: report.elapsedSeconds, peakRssBytes: report.peakRssBytes }));
