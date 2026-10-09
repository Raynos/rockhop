/** Exact-ancestry CPU normal census and monotone original-fan constraints. */
import assert from 'node:assert/strict';

export const MINIMUM_NORMAL_DOT = 0.25;
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const minus = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const sorted = values => [...new Set(values)].sort((a, b) => a - b);

export function normalCensus(a, originalIndices) {
  const n = a.positions.length / 3, sums = new Float64Array(n * 3), used = new Uint8Array(n);
  assert.equal(a.normals.length, a.positions.length); assert.equal(originalIndices.length % 3, 0);
  for (let i = 0; i < originalIndices.length; i += 3) {
    const ids = originalIndices.subarray(i, i + 3);
    assert(ids.every(v => Number.isInteger(v) && v >= 0 && v < n));
    const p = Array.from(ids, v => Array.from(a.positions.subarray(3 * v, 3 * v + 3)));
    const c = cross(minus(p[1], p[0]), minus(p[2], p[0])), length = Math.hypot(...c);
    assert(Number.isFinite(length) && length > 0, `Degenerate candidate face ${i / 3}`);
    const normal = c.map(value => value / length);
    for (let corner = 0; corner < 3; corner++) {
      const u = minus(p[(corner + 1) % 3], p[corner]), v = minus(p[(corner + 2) % 3], p[corner]);
      const angle = Math.atan2(Math.hypot(...cross(u, v)), dot(u, v)), id = ids[corner]; used[id] = 1;
      for (let j = 0; j < 3; j++) sums[3 * id + j] += angle * normal[j];
    }
  }
  const failures = []; let targetVertexId = 0, minimum = Infinity, undefinedNormals = 0;
  for (let originalVertexId = 0; originalVertexId < n; originalVertexId++) {
    if (!used[originalVertexId]) continue;
    const sum = sums.subarray(3 * originalVertexId, 3 * originalVertexId + 3), length = Math.hypot(...sum);
    let normalDot = null;
    if (Number.isFinite(length) && length > 0) {
      normalDot = dot(Array.from(sum, value => value / length), a.normals.subarray(3 * originalVertexId, 3 * originalVertexId + 3));
      assert(Number.isFinite(normalDot), 'Nonfinite donor/candidate normal comparison');
      minimum = Math.min(minimum, normalDot);
    } else undefinedNormals++;
    if (normalDot === null || normalDot < MINIMUM_NORMAL_DOT) failures.push({ targetVertexId, originalVertexId, normalDot });
    targetVertexId++;
  }
  assert(targetVertexId > 0);
  return { verticesExamined: targetVertexId, trianglesExamined: originalIndices.length / 3,
    minimumNormalDot: Number.isFinite(minimum) ? minimum : null, threshold: MINIMUM_NORMAL_DOT,
    undefinedNormals, failingVertices: failures.length, failures, passed: failures.length === 0,
    method: 'Float64 geometric face normals and atan2 corner-angle vertex weighting; compare to native donor vertex normal at exact original index. CPU proxy only; unchanged native gate still required.' };
}

export function fanClosure(a, centerIds) {
  const n = a.positions.length / 3, centers = sorted(centerIds);
  assert(centers.length > 0 && centers.every(v => Number.isInteger(v) && v >= 0 && v < n));
  const mask = new Uint8Array(n); centers.forEach(v => { mask[v] = 1; });
  const faces = [], vertices = [], edges = [];
  for (let i = 0; i < a.triangles.length; i += 3) {
    const tri = a.triangles.subarray(i, i + 3); if (!tri.some(v => mask[v])) continue;
    faces.push(i / 3); vertices.push(...tri);
    for (let j = 0; j < 3; j++) edges.push(Math.min(tri[j], tri[(j + 1) % 3]) * n + Math.max(tri[j], tri[(j + 1) % 3]));
  }
  return { centerOriginalVertexIds: Uint32Array.from(centers), lockedOriginalVertexIds: Uint32Array.from(sorted(vertices)),
    requiredSourceFaceIds: Uint32Array.from(faces),
    requiredEdgesOriginal: Uint32Array.from(sorted(edges).flatMap(key => [Math.floor(key / n), key % n])) };
}

export function augment(a, protection, census) {
  assert(!census.passed && census.failures.length > 0, 'No failing fans to augment');
  const centers = new Set(protection.centerOriginalVertexIds), added = [];
  for (const failure of census.failures) {
    const v = failure.originalVertexId;
    assert(failure.normalDot === null || failure.normalDot < MINIMUM_NORMAL_DOT);
    assert(Number.isInteger(v) && v >= 0 && v < a.positions.length / 3);
    if (!centers.has(v)) { centers.add(v); added.push(v); }
  }
  assert(added.length > 0, 'Fixed-point rejected: no new original fan can be protected');
  const next = fanClosure(a, centers);
  const locks = new Set(next.lockedOriginalVertexIds), faces = new Set(next.requiredSourceFaceIds);
  assert([...protection.lockedOriginalVertexIds].every(v => locks.has(v)), 'Protection lost a prior locked vertex');
  assert([...protection.requiredSourceFaceIds].every(v => faces.has(v)), 'Protection lost a prior source face');
  return { next, addedCenters: added.sort((a, b) => a - b) };
}
