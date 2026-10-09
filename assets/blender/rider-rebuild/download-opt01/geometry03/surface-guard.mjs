// Independent deterministic original-face centroid to reduced-surface probes.
// Requires isolated /tmp tooling; repository packages are never modified.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { BufferGeometry, BufferAttribute, Vector3, Triangle } from '/tmp/rockhop-geometry03-tooling/node_modules/three/build/three.module.js';
import { MeshBVH } from '/tmp/rockhop-geometry03-tooling/node_modules/three-mesh-bvh/src/index.js';
import { openGlb, accessorBytes, indexValues, sha } from '../geometry01/glb.mjs';
const [input, reductionDir, output, sampleLimit = '100000'] = process.argv.slice(2);
const start = performance.now(), glb = openGlb(input);
const reduction = JSON.parse(fs.readFileSync(path.join(reductionDir, 'reduction.json')));
const report = { accepted: false, input: reduction.source, mode: reduction.mode,
  limits: 'Deterministic centroid samples, not exhaustive Hausdorff or moving-art acceptance', meshes: [] };
for (const row of reduction.meshes) {
  const p = glb.json.meshes[row.mesh].primitives[0];
  const floats = async i => { const bytes = await accessorBytes(glb, i);
    return new Float32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4); };
  const positions = await floats(p.attributes.POSITION), normals = await floats(p.attributes.NORMAL);
  const uvs = await floats(p.attributes.TEXCOORD_0), weights = await floats(p.attributes.WEIGHTS_0);
  const joints = await accessorBytes(glb, p.attributes.JOINTS_0);
  const indices = indexValues(await accessorBytes(glb, p.indices), glb.json.accessors[p.indices]);
  const bytes = fs.readFileSync(row.indices.path);
  assert.equal(sha(bytes), row.indices.sha256);
  const reduced = new Uint32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4);
  const geo = new BufferGeometry();
  geo.setAttribute('position', new BufferAttribute(positions, 3));
  geo.setIndex(new BufferAttribute(reduced, 1));
  // indirect preserves candidate index order and the original source references.
  const bvh = new MeshBVH(geo, { indirect: true, maxLeafSize: 8 });
  const point = new Vector3(), target = { point: new Vector3() }, bary = new Vector3();
  const triangle = new Triangle(), nA = new Vector3(), nB = new Vector3();
  const sourceTris = indices.length / 3, step = Math.max(1, Math.floor(sourceTris / Number(sampleLimit)));
  let samples = 0, maxDistance = 0, maxNormal = 0, maxUv = 0, maxWeightL1 = 0;
  let geoFailures = 0, normalFailures = 0, uvFailures = 0;
  let distanceSum = 0, uvSum = 0, normalSum = 0;
  const worst = {};
  for (let tri = 0; tri < sourceTris; tri += step) {
    const src = [indices[tri * 3], indices[tri * 3 + 1], indices[tri * 3 + 2]];
    point.set(0, 0, 0);
    for (const v of src) for (let k = 0; k < 3; k++) point.setComponent(k, point.getComponent(k) + positions[v * 3 + k] / 3);
    assert(bvh.closestPointToPoint(point, target));
    const face = target.faceIndex;
    const dst = [reduced[face * 3], reduced[face * 3 + 1], reduced[face * 3 + 2]];
    triangle.a.fromArray(positions, dst[0] * 3); triangle.b.fromArray(positions, dst[1] * 3);
    triangle.c.fromArray(positions, dst[2] * 3); triangle.getBarycoord(target.point, bary);
    const bc = bary.toArray();
    if (!bc.every(Number.isFinite)) continue; // Original zero-area faces are counted separately by topology, not interpreted as fields.
    nA.set(0, 0, 0); nB.set(0, 0, 0);
    const uvA = [0, 0], uvB = [0, 0], wA = new Float64Array(75), wB = new Float64Array(75);
    for (let corner = 0; corner < 3; corner++) {
      for (let k = 0; k < 3; k++) {
        nA.setComponent(k, nA.getComponent(k) + normals[src[corner] * 3 + k] / 3);
        nB.setComponent(k, nB.getComponent(k) + normals[dst[corner] * 3 + k] * bc[corner]);
      }
      for (let k = 0; k < 2; k++) {
        uvA[k] += uvs[src[corner] * 2 + k] / 3; uvB[k] += uvs[dst[corner] * 2 + k] * bc[corner];
      }
      for (let slot = 0; slot < 4; slot++) {
        wA[joints[src[corner] * 4 + slot]] += weights[src[corner] * 4 + slot] / 3;
        wB[joints[dst[corner] * 4 + slot]] += weights[dst[corner] * 4 + slot] * bc[corner];
      }
    }
    const angle = nA.angleTo(nB) * 180 / Math.PI, uvError = Math.hypot(uvA[0] - uvB[0], uvA[1] - uvB[1]) * 4096;
    let weightL1 = 0;
    for (let joint = 0; joint < 75; joint++) weightL1 += Math.abs(wA[joint] - wB[joint]);
    if (target.distance > maxDistance) worst.geometry = { sourceTriangle: tri, candidateTriangle: face, meters: target.distance };
    if (angle > maxNormal) worst.normal = { sourceTriangle: tri, candidateTriangle: face, degrees: angle };
    if (uvError > maxUv) worst.uv = { sourceTriangle: tri, candidateTriangle: face, texels4096: uvError };
    maxDistance = Math.max(maxDistance, target.distance); maxNormal = Math.max(maxNormal, angle);
    maxUv = Math.max(maxUv, uvError); maxWeightL1 = Math.max(maxWeightL1, weightL1);
    geoFailures += target.distance > 0.0002; normalFailures += angle > 0.1; uvFailures += uvError > 0.25;
    distanceSum += target.distance; normalSum += angle; uvSum += uvError; samples++;
  }
  const result = { mesh: row.mesh, name: row.name, samples, sourceTriangles: sourceTris,
    candidateTriangles: reduced.length / 3, triangleStep: step,
    maxSurfaceDistanceMeters: maxDistance, meanSurfaceDistanceMeters: distanceSum / samples,
    maxNormalAngleDegrees: maxNormal, meanNormalAngleDegrees: normalSum / samples,
    maxUvTexels4096: maxUv, meanUvTexels4096: uvSum / samples,
    maxInterpolatedNativeJointWeightL1: maxWeightL1,
    thresholds: { geometryMeters: 0.0002, normalDegrees: 0.1, uvTexels4096: 0.25 },
    failures: { geometry: geoFailures, normal: normalFailures, uv: uvFailures }, worst,
    caveat: 'Closest geometry at coincident layered surfaces/chart seams can select another source sheet; failures need witnesses, never silent acceptance' };
  report.meshes.push(result); console.log(JSON.stringify(result));
  geo.dispose();
}
report.passStrictProbes = report.meshes.every(row => Object.values(row.failures).every(v => v === 0));
report.elapsedSeconds = (performance.now() - start) / 1000;
report.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.closeSync(glb.fd); fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ passStrictProbes: report.passStrictProbes, elapsedSeconds: report.elapsedSeconds }));
