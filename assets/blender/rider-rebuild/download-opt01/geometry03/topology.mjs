// Narrow exact position / seam / topological border inventory before reduction.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { MeshoptSimplifier } from 'meshoptimizer/simplifier';
import { openGlb, accessorBytes, indexValues, fileSha } from '../geometry01/glb.mjs';
const [input, reportPath] = process.argv.slice(2);
assert(input && reportPath);
await MeshoptSimplifier.ready;
const glb = openGlb(input), report = { source: { path: input, sha256: fileSha(input) }, meshes: [] };
for (const meshIndex of [0, 1, 2, 3, 5]) {
  const mesh = glb.json.meshes[meshIndex], p = mesh.primitives[0];
  assert.equal(mesh.primitives.length, 1);
  const count = glb.json.accessors[p.attributes.POSITION].count;
  const posBytes = await accessorBytes(glb, p.attributes.POSITION);
  const positions = new Float32Array(posBytes.buffer, posBytes.byteOffset, posBytes.length / 4);
  const remap = MeshoptSimplifier.generatePositionRemap(positions, 3);
  const normals = await accessorBytes(glb, p.attributes.NORMAL);
  const normalWords = new Uint32Array(normals.buffer, normals.byteOffset, normals.length / 4);
  const uvs = await accessorBytes(glb, p.attributes.TEXCOORD_0);
  const uvWords = new Uint32Array(uvs.buffer, uvs.byteOffset, uvs.length / 4);
  const joints = await accessorBytes(glb, p.attributes.JOINTS_0);
  const jointWords = new Uint32Array(joints.buffer, joints.byteOffset, joints.length / 4);
  const weights = await accessorBytes(glb, p.attributes.WEIGHTS_0);
  const weightWords = new Uint32Array(weights.buffer, weights.byteOffset, weights.length / 4);
  const flags = new Uint8Array(count);
  let uniquePositions = 0, duplicatedNormalRows = 0, duplicatedUvRows = 0;
  let duplicatedJointRows = 0, duplicatedWeightRows = 0;
  for (let v = 0; v < count; v++) {
    const r = remap[v];
    if (r === v) { uniquePositions++; continue; }
    let normal = false, uv = false, weight = false;
    for (let k = 0; k < 3; k++) normal ||= normalWords[v * 3 + k] !== normalWords[r * 3 + k];
    for (let k = 0; k < 2; k++) uv ||= uvWords[v * 2 + k] !== uvWords[r * 2 + k];
    for (let k = 0; k < 4; k++) weight ||= weightWords[v * 4 + k] !== weightWords[r * 4 + k];
    if (normal) { duplicatedNormalRows++; flags[r] |= 1; }
    if (uv) { duplicatedUvRows++; flags[r] |= 2; }
    if (jointWords[v] !== jointWords[r]) { duplicatedJointRows++; flags[r] |= 4; }
    if (weight) { duplicatedWeightRows++; flags[r] |= 8; }
  }
  const indices = indexValues(await accessorBytes(glb, p.indices), glb.json.accessors[p.indices]);
  const edges = new BigUint64Array(indices.length);
  const geometricBorder = new Uint8Array(count);
  function edge(a, b) {
    return BigInt(Math.min(a, b)) | (BigInt(Math.max(a, b)) << 32n);
  }
  for (let i = 0; i < indices.length; i += 3) {
    const a = remap[indices[i]], b = remap[indices[i + 1]], c = remap[indices[i + 2]];
    edges[i] = edge(a, b); edges[i + 1] = edge(b, c); edges[i + 2] = edge(c, a);
  }
  edges.sort();
  let borderEdges = 0, manifoldEdges = 0, nonmanifoldEdges = 0;
  for (let first = 0; first < edges.length;) {
    let end = first + 1;
    while (end < edges.length && edges[end] === edges[first]) end++;
    if (end - first === 1) {
      borderEdges++;
      geometricBorder[Number(edges[first] & 0xffffffffn)] = 1;
      geometricBorder[Number(edges[first] >> 32n)] = 1;
    } else if (end - first === 2) manifoldEdges++; else nonmanifoldEdges++;
    first = end;
  }
  const seamGroups = { normal: 0, uv: 0, jointTuple: 0, weights: 0 };
  for (const bits of flags) {
    seamGroups.normal += !!(bits & 1); seamGroups.uv += !!(bits & 2);
    seamGroups.jointTuple += !!(bits & 4); seamGroups.weights += !!(bits & 8);
  }
  const row = { meshIndex, name: mesh.name, vertices: count, triangles: indices.length / 3,
    exactUniquePositions: uniquePositions, duplicatePositionRows: count - uniquePositions,
    duplicateRowsWithDifferentNormals: duplicatedNormalRows,
    duplicateRowsWithDifferentUvs: duplicatedUvRows,
    duplicateRowsWithDifferentJointTuples: duplicatedJointRows,
    duplicateRowsWithDifferentWeights: duplicatedWeightRows, seamGroups,
    geometricBorderEdges: borderEdges, manifoldEdges, nonmanifoldEdges,
    geometricBorderPositions: geometricBorder.reduce((sum, v) => sum + v, 0) };
  report.meshes.push(row); console.log(JSON.stringify(row));
}
report.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.closeSync(glb.fd); fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
