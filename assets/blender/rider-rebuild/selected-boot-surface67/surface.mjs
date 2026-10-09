/** Immutable-source nearest triangles and complete face census; CPU only. */
import assert from 'node:assert/strict';

export const NORMAL_LIMIT = .25, DISTANCE_LIMIT = .001;
export const faceKey = (a, b, c) => a < b && a < c ? `${a},${b},${c}` : b < c ? `${b},${c},${a}` : `${c},${a},${b}`;
const point = (p, i) => [p[3 * i], p[3 * i + 1], p[3 * i + 2]];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const minus = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export function geometricNormal(a, b, c) {
  const n = cross(minus(b, a), minus(c, a)), length = Math.sqrt(dot(n, n));
  assert(Number.isFinite(length) && length > 0, 'Degenerate geometric triangle');
  return n.map(v => v / length);
}

export function closestTriangle(q, a, b, c) {
  const ab = minus(b, a), ac = minus(c, a), aq = minus(q, a);
  const scale = Math.max(...ab.map(Math.abs), ...ac.map(Math.abs));
  assert(Number.isFinite(scale) && scale > 0, 'Degenerate geometric triangle');
  const u = ab.map(v => v / scale), v = ac.map(v => v / scale), w = aq.map(v => v / scale);
  const n = cross(u, v), denominator = dot(n, n);
  assert(Number.isFinite(denominator) && denominator > 0, 'Degenerate geometric triangle');
  const beta = dot(cross(w, v), n) / denominator, gamma = dot(cross(u, w), n) / denominator;
  let best = Infinity, hit, feature;
  // All arithmetic is translated/scaled; no absolute Gram determinant cutoff.
  const consider = (relative, candidateFeature) => {
    const delta = relative.map((v, j) => v - aq[j]), distanceSq = dot(delta, delta);
    assert(Number.isFinite(distanceSq));
    if (distanceSq < best || (distanceSq === best && candidateFeature.length < feature.length)) { best = distanceSq; hit = relative.map((v, j) => a[j] + v); feature = candidateFeature; }
  };
  if (beta >= 0 && gamma >= 0 && beta + gamma <= 1) {
    const coefficients = [1 - beta - gamma, beta, gamma];
    consider(ab.map((v, j) => beta * v + gamma * ac[j]), coefficients.flatMap((value, i) => value === 0 ? [] : [i]));
  }
  for (const [begin, end, startId, endId] of [[[0, 0, 0], ab, 0, 1], [ab, ac, 1, 2], [ac, [0, 0, 0], 2, 0]]) {
    const edge = minus(end, begin), lengthSq = dot(edge, edge); assert(lengthSq > 0);
    const t = Math.max(0, Math.min(1, dot(minus(aq, begin), edge) / lengthSq));
    consider(begin.map((v, j) => v + t * edge[j]), t === 0 ? [startId] : t === 1 ? [endId] : [startId, endId]);
  }
  return { distanceSq: best, point: hit, feature };
}

export class SourceTree {
  constructor(positions, triangles) {
    assert(positions.length % 3 === 0 && triangles.length % 3 === 0 && triangles.length > 0);
    this.positions = positions; this.triangles = triangles; this.count = triangles.length / 3;
    this.ids = Uint32Array.from({ length: this.count }, (_, i) => i);
    this.faceBounds = new Float64Array(this.count * 6); this.normals = new Float64Array(this.count * 3);
    this.ancestry = new Map(); this.nodes = [];
    for (let i = 0; i < this.count; i++) {
      const ids = triangles.subarray(3 * i, 3 * i + 3);
      assert(ids.every(v => Number.isInteger(v) && v >= 0 && v < positions.length / 3));
      assert(new Set(ids).size === 3);
      const p = Array.from(ids, id => point(positions, id));
      assert(p.flat().every(Number.isFinite));
      for (let j = 0; j < 3; j++) {
        this.faceBounds[6 * i + j] = Math.min(...p.map(v => v[j]));
        this.faceBounds[6 * i + 3 + j] = Math.max(...p.map(v => v[j]));
      }
      this.normals.set(geometricNormal(...p), 3 * i);
      const key = faceKey(...ids); assert(!this.ancestry.has(key), 'Duplicate oriented source triangle'); this.ancestry.set(key, i);
    }
    this.incidentOffsets = new Uint32Array(positions.length / 3 + 1);
    for (const v of triangles) this.incidentOffsets[v + 1]++;
    for (let i = 1; i < this.incidentOffsets.length; i++) this.incidentOffsets[i] += this.incidentOffsets[i - 1];
    const cursor = this.incidentOffsets.slice(); this.incidentFaces = new Uint32Array(triangles.length);
    for (let i = 0; i < triangles.length; i++) this.incidentFaces[cursor[triangles[i]]++] = Math.floor(i / 3);
    this.root = this.build(0, this.count);
  }
  split(start, end, middle, axis) {
    const center = id => this.faceBounds[6 * id + axis] + this.faceBounds[6 * id + 3 + axis];
    const before = (a, b) => center(a) < center(b) || (center(a) === center(b) && a < b);
    let left = start, right = end - 1;
    while (left < right) {
      const pivot = this.ids[(left + right) >>> 1]; let i = left, j = right;
      while (i <= j) {
        while (before(this.ids[i], pivot)) i++;
        while (before(pivot, this.ids[j])) j--;
        if (i <= j) { const tmp = this.ids[i]; this.ids[i++] = this.ids[j]; this.ids[j--] = tmp; }
      }
      if (middle <= j) right = j; else if (middle >= i) left = i; else break;
    }
  }
  build(start, end) {
    const bounds = [Infinity, Infinity, Infinity, -Infinity, -Infinity, -Infinity];
    for (let i = start; i < end; i++) for (let j = 0; j < 3; j++) {
      bounds[j] = Math.min(bounds[j], this.faceBounds[6 * this.ids[i] + j]);
      bounds[j + 3] = Math.max(bounds[j + 3], this.faceBounds[6 * this.ids[i] + j + 3]);
    }
    const index = this.nodes.length, node = { bounds, start, end, left: -1, right: -1 }; this.nodes.push(node);
    // Leaf size controls work only; traversal never skips a potentially nearer face.
    if (end - start > 12) {
      const size = bounds.slice(3).map((v, j) => v - bounds[j]), axis = size.indexOf(Math.max(...size));
      const middle = (start + end) >>> 1; this.split(start, end, middle, axis);
      node.left = this.build(start, middle); node.right = this.build(middle, end);
    }
    return index;
  }
  boundDistance(q, node) {
    const b = node.bounds; let sum = 0;
    for (let j = 0; j < 3; j++) { const d = Math.max(b[j] - q[j], 0, q[j] - b[j + 3]); sum += d * d; }
    return sum;
  }
  closestFace(q, faceId) {
    const t = this.triangles.subarray(3 * faceId, 3 * faceId + 3);
    return closestTriangle(q, ...Array.from(t, id => point(this.positions, id)));
  }
  boundaryFaces(faceId, feature) {
    if (feature.length === 3) return [faceId];
    const vertices = feature.map(i => this.triangles[3 * faceId + i]);
    const out = [];
    for (let i = this.incidentOffsets[vertices[0]]; i < this.incidentOffsets[vertices[0] + 1]; i++) {
      const face = this.incidentFaces[i], ids = this.triangles.subarray(3 * face, 3 * face + 3);
      if (vertices.every(v => ids.includes(v))) out.push(face);
    }
    assert(out.includes(faceId)); return out;
  }
  nearest(q) {
    assert(q.length === 3 && q.every(Number.isFinite));
    let best = Infinity, faceId = -1, hit, testedFaces = 0, exactTieFaces = [], features = new Map();
    const visit = index => {
      const node = this.nodes[index]; if (this.boundDistance(q, node) > best) return;
      if (node.left < 0) {
        for (let i = node.start; i < node.end; i++) {
          const id = this.ids[i], row = this.closestFace(q, id); testedFaces++;
          if (row.distanceSq < best) { best = row.distanceSq; faceId = id; hit = row.point; exactTieFaces = [id]; features = new Map([[id, row.feature]]); }
          else if (row.distanceSq === best) {
            exactTieFaces.push(id); features.set(id, row.feature); if (id < faceId) { faceId = id; hit = row.point; }
          }
        }
      } else {
        const first = this.boundDistance(q, this.nodes[node.left]), second = this.boundDistance(q, this.nodes[node.right]);
        if (first <= second) { visit(node.left); visit(node.right); } else { visit(node.right); visit(node.left); }
      }
    };
    visit(this.root); assert(faceId >= 0 && Number.isFinite(best));
    const bearingFaces = new Set();
    for (const [id, feature] of features) for (const face of this.boundaryFaces(id, feature)) bearingFaces.add(face);
    return { sourceFaceId: faceId, distanceM: Math.sqrt(best), point: hit,
      exactTieFaces: exactTieFaces.sort((a, b) => a - b),
      bearingSourceFaceIds: [...bearingFaces].sort((a, b) => a - b),
      closestBoundaryFeatureOriginalVertices: features.get(faceId).map(i => this.triangles[3 * faceId + i]), testedFaces };
  }
}

export function faceCensus(a, originalIndices, tree) {
  assert(originalIndices.length % 3 === 0);
  const failures = [], details = []; let inherited = 0, minimum = Infinity, maximum = 0, ties = 0;
  const faceIds = new Int32Array(originalIndices.length / 3), distances = new Float32Array(faceIds.length), dots = new Float32Array(faceIds.length);
  for (let i = 0; i < originalIndices.length; i += 3) {
    const ids = originalIndices.subarray(i, i + 3), p = Array.from(ids, id => point(a.positions, id));
    const normal = geometricNormal(...p), exact = tree.ancestry.get(faceKey(...ids));
    const query = [0, 1, 2].map(j => Math.fround((p[0][j] + p[1][j] + p[2][j]) / 3));
    // Exact oriented ancestry is a geometric identity, never normal-based selection.
    const bearing = exact === undefined ? tree.nearest(query) : { sourceFaceId: exact, distanceM: 0, exactTieFaces: [], bearingSourceFaceIds: [exact] };
    if (exact !== undefined) inherited++;
    if (bearing.bearingSourceFaceIds.length > 1) { ties++; details.push({ targetFaceId: i / 3, bearingSourceFaceIds: bearing.bearingSourceFaceIds, exactTieFaces: bearing.exactTieFaces }); }
    const value = Math.min(...bearing.bearingSourceFaceIds.map(id => dot(normal, tree.normals.subarray(3 * id, 3 * id + 3))));
    assert(Number.isFinite(value)); minimum = Math.min(minimum, value); maximum = Math.max(maximum, bearing.distanceM);
    faceIds[i / 3] = bearing.sourceFaceId; distances[i / 3] = bearing.distanceM; dots[i / 3] = value;
    if (value < NORMAL_LIMIT || bearing.distanceM > DISTANCE_LIMIT) failures.push({ targetFaceId: i / 3,
      originalVertexIds: Array.from(ids), sourceFaceId: bearing.sourceFaceId,
      sourceBearingOriginalVertexIds: [...new Set(bearing.bearingSourceFaceIds.flatMap(id => Array.from(a.triangles.subarray(3 * id, 3 * id + 3))))].sort((a, b) => a - b),
      bearingSourceFaceIds: bearing.bearingSourceFaceIds,
      exactInheritedSourceFace: exact !== undefined, normalDot: value, distanceM: bearing.distanceM });
  }
  return { report: { samples: faceIds.length, exactInheritedFaces: inherited, newFaces: faceIds.length - inherited,
    minimumNormalDot: minimum, maximumDistanceM: maximum, minimumNormalDotRequired: NORMAL_LIMIT,
    maximumDistanceRequiredM: DISTANCE_LIMIT, failures, failingFaces: failures.length,
    multipleGeometricBearingQueries: ties, boundaryAndExactTies: details, passed: failures.length === 0,
    limits: 'All faces incident on the actual closest edge/vertex and all exactly equal-distance faces must pass; no normal-based bearing choice or numeric tie tolerance. CPU geometric face census. Exact face ancestry policy needs native67 proof before any native policy change. Independent native surface/skin/contact gates remain.' },
    arrays: { sourceFaceId: faceIds, distanceM: distances, normalDot: dots } };
}
