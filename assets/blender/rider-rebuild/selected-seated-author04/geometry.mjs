/** Offline finite surface diagnostics. No renderer, mesh writes, or runtime import. */
import { Box3, Triangle, Vector3 } from 'three';

export const EPS = 1e-12;
const cross = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
export const xz = p => [p.x, p.z];
export function clip(polygon, distance) {
  const out = [];
  for (let i = 0; i < polygon.length; i++) {
    const p = polygon[i], q = polygon[(i + 1) % polygon.length], a = distance(p), b = distance(q);
    if (a >= 0) out.push(p);
    if ((a < 0) !== (b < 0)) { const t = a / (a - b); out.push(p.map((v, k) => v + t * (q[k] - v))); }
  }
  return out;
}
export function overlap(a, b) {
  let polygon = a.points.map(xz);
  const target = b.points.map(xz), sign = Math.sign(cross(...target));
  if (!sign) return [];
  for (let k = 0; k < 3; k++) polygon = clip(polygon, p => sign * cross(target[k], target[(k + 1) % 3], p));
  return polygon;
}
export function moment(polygon, field = () => 0) {
  let area = 0, x = 0, z = 0, integral = 0;
  for (let i = 1; i + 1 < polygon.length; i++) {
    const t = [polygon[0], polygon[i], polygon[i + 1]], a = Math.abs(cross(...t)) / 2;
    area += a; x += a * t.reduce((s, p) => s + p[0], 0) / 3;
    z += a * t.reduce((s, p) => s + p[1], 0) / 3;
    integral += a * t.reduce((s, p) => s + field(p), 0) / 3;
  }
  return { area, centroid: area > EPS ? [x / area, z / area] : null, integral };
}
export function surface(points, info = {}) {
  const shape = new Triangle(...points), normal = shape.getNormal(new Vector3());
  return { ...info, points, shape, normal, box: new Box3().setFromPoints(points), area: shape.getArea() };
}
export const height = (t, p) => t.points[0].y - (t.normal.x * (p[0] - t.points[0].x)
  + t.normal.z * (p[1] - t.points[0].z)) / t.normal.y;
const footprintOverlaps = (a, b) => a.box.max.x >= b.box.min.x && b.box.max.x >= a.box.min.x
  && a.box.max.z >= b.box.min.z && b.box.max.z >= a.box.min.z;
export function nearest(point, targets) {
  let best = null;
  for (const t of targets) {
    const p = t.shape.closestPointToPoint(point, new Vector3()), d = p.distanceToSquared(point);
    if (!best || d < best.distanceSq) best = { point: p, distanceSq: d, triangle: t };
  }
  return best;
}

function insideUnion(p, triangles) {
  // Internal triangulation edges are allowed; only the union boundary is excluded.
  const boundary = new Map(); let contained = false;
  const key = p => p.map(v => v.toPrecision(14)).join(',');
  for (const t of triangles) {
    const points = t.points.map(xz), sign = Math.sign(cross(...points));
    if (sign && points.every((a, i) => sign * cross(a, points[(i + 1) % 3], p) >= -EPS)) contained = true;
    for (let i = 0; i < 3; i++) {
      const edge = [points[i], points[(i + 1) % 3]], k = edge.map(key).sort().join('|');
      if (boundary.has(k)) boundary.delete(k); else boundary.set(k, edge);
    }
  }
  if (!contained) return false;
  return [...boundary.values()].every(([a, b]) => {
    const dx = b[0] - a[0], dz = b[1] - a[1], len2 = dx * dx + dz * dz;
    if (!len2) return true;
    const u = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / len2));
    return Math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dz) > 1e-9;
  });
}

export function support(core, saddle, band) {
  let footprintArea = 0, downwardArea = 0, area = 0, bandArea = 0, gapIntegral = 0;
  let min = null, max = null, centroid = [0, 0], bandCentroid = [0, 0], projectedFoldArea = 0;
  const cells = [];
  for (let i = 0; i < core.length; i++) {
    const a = core[i], projected = moment(a.points.map(xz)).area;
    footprintArea += projected;
    for (let j = 0; j < i; j++) if (footprintOverlaps(a, core[j])) projectedFoldArea += moment(overlap(a, core[j])).area;
    if (a.normal.y >= -1e-9) continue;
    downwardArea += projected;
    for (const b of saddle) {
      if (!footprintOverlaps(a, b)) continue;
      const polygon = overlap(a, b), gap = p => height(a, p) - height(b, p), m = moment(polygon, gap);
      if (m.area <= EPS) continue;
      const inBand = clip(clip(polygon, p => gap(p)), p => band - gap(p)), n = moment(inBand);
      area += m.area; bandArea += n.area; gapIntegral += m.integral;
      centroid = centroid.map((v, k) => v + m.area * m.centroid[k]);
      if (n.centroid) bandCentroid = bandCentroid.map((v, k) => v + n.area * n.centroid[k]);
      const cell = { jeansRow: a.row, nativeIDs: a.nativeIDs, sourcePolygon: a.sourcePolygon,
        saddleRow: b.row, areaM2: m.area, bandAreaM2: n.area, polygonXZ: polygon };
      cells.push(cell);
      for (const p of polygon) {
        const g = gap(p), witness = { gapM: g, jeansRow: a.row, nativeIDs: a.nativeIDs,
          sourcePolygon: a.sourcePolygon, saddleRow: b.row, pointBike: [p[0], height(a, p), p[1]] };
        if (!min || g < min.gapM) min = witness;
        if (!max || g > max.gapM) max = witness;
      }
    }
  }
  const center = area > EPS ? centroid.map(v => v / area) : null;
  const contactCenter = bandArea > EPS ? bandCentroid.map(v => v / bandArea) : null;
  // Components use positive-length shared cell boundaries, never point adjacency.
  const adjacent = (a, b) => a.some((p, i) => b.some((q, j) => {
    const r = a[(i + 1) % a.length], s = b[(j + 1) % b.length], dx = r[0] - p[0], dz = r[1] - p[1], len = Math.hypot(dx, dz);
    if (len < 1e-9 || Math.abs(cross(p, r, q)) > 1e-9 * len || Math.abs(cross(p, r, s)) > 1e-9 * len) return false;
    const u = v => ((v[0] - p[0]) * dx + (v[1] - p[1]) * dz) / len;
    return Math.min(len, Math.max(u(q), u(s))) - Math.max(0, Math.min(u(q), u(s))) > 1e-9;
  }));
  const remaining = new Set(cells.map((_, i) => i)), components = [];
  while (remaining.size) {
    const queue = [remaining.values().next().value], ids = []; remaining.delete(queue[0]);
    while (queue.length) {
      const i = queue.pop(); ids.push(i);
      for (const j of remaining) if (adjacent(cells[i].polygonXZ, cells[j].polygonXZ)) { remaining.delete(j); queue.push(j); }
    }
    components.push({ cellIndices: ids, areaM2: ids.reduce((s, i) => s + cells[i].areaM2, 0) });
  }
  const surfaceArea = core.reduce((sum, t) => sum + t.area, 0);
  return { surfaceAreaM2: surfaceArea, footprintAreaM2: footprintArea, downwardAreaM2: downwardArea,
    downwardProjectionFraction: surfaceArea > EPS ? downwardArea / surfaceArea : 0, overlapAreaM2: area, bandAreaM2: bandArea,
    overlapFraction: footprintArea > EPS ? area / footprintArea : 0, bandFraction: area > EPS ? bandArea / area : 0,
    projectedFoldAreaM2: projectedFoldArea, meanGapM: area > EPS ? gapIntegral / area : null,
    centroidXZ: center, bandCentroidXZ: contactCenter,
    centroidInsideCoreAndSaddle: !!contactCenter && insideUnion(contactCenter, core) && insideUnion(contactCenter, saddle),
    minimum: min, maximum: max, components, cells };
}

function strictCross(a, b) {
  const na = a.normal, nb = b.normal, line = new Vector3().crossVectors(na, nb);
  if (line.length() < 1e-8 && Math.abs(a.points[0].clone().sub(b.points[0]).dot(nb)) < 1e-9) {
    const axis = na.toArray().map(Math.abs).indexOf(Math.max(...na.toArray().map(Math.abs)));
    const aa = a.points.map(p => p.toArray().filter((_, k) => k !== axis));
    const bb = b.points.map(p => p.toArray().filter((_, k) => k !== axis));
    for (const t of [aa, bb]) for (let i = 0; i < 3; i++) {
      const p = t[i], q = t[(i + 1) % 3], n = [p[1] - q[1], q[0] - p[0]];
      const x = aa.map(p => p[0] * n[0] + p[1] * n[1]), y = bb.map(p => p[0] * n[0] + p[1] * n[1]);
      if (Math.min(Math.max(...x), Math.max(...y)) - Math.max(Math.min(...x), Math.min(...y)) <= 1e-14) return false;
    }
    return true;
  }
  if (line.length() < 1e-12) return false;
  line.normalize();
  const section = (first, second) => {
    const distances = first.points.map(p => p.clone().sub(second.points[0]).dot(second.normal));
    // A cut must enter the triangle interior. A shared edge or vertex alone
    // leaves all remaining vertices on one side and does not qualify.
    if (Math.min(...distances) >= -1e-9 || Math.max(...distances) <= 1e-9) return null;
    const values = [];
    for (let i = 0; i < 3; i++) {
      const j = (i + 1) % 3, d = distances[i], next = distances[j];
      if (Math.abs(d) <= 1e-9) values.push(first.points[i].dot(line));
      if (d * next < 0) values.push(first.points[i].clone().lerp(first.points[j], d / (d - next)).dot(line));
    }
    return [Math.min(...values), Math.max(...values)];
  };
  const first = section(a, b), second = section(b, a);
  // Compare whole sections: their endpoints may lie on both boundaries while
  // the segment between them still crosses both triangle interiors.
  return !!first && !!second && Math.min(first[1], second[1]) - Math.max(first[0], second[0]) > 1e-9;
}
function tree(triangles) {
  const box = new Box3(); for (const t of triangles) box.union(t.box);
  if (triangles.length <= 12) return { box, triangles };
  const size = box.getSize(new Vector3()).toArray(), axis = ['x', 'y', 'z'][size.indexOf(Math.max(...size))];
  const sorted = [...triangles].sort((a, b) => a.box.min[axis] + a.box.max[axis] - b.box.min[axis] - b.box.max[axis] || a.row - b.row);
  const half = Math.floor(sorted.length / 2);
  return { box, children: [tree(sorted.slice(0, half)), tree(sorted.slice(half))] };
}
export function crossings(first, second, self = false) {
  const index = tree(second), witnesses = []; let count = 0, tested = 0;
  const pairs = [];
  for (const a of first) {
    const visit = node => {
      if (!a.box.intersectsBox(node.box)) return;
      if (node.children) return node.children.forEach(visit);
      for (const b of node.triangles) {
        // Shared vertices/edges do not make a pair safe: adjacent faces can fold
        // through each other. strictCross rejects boundary-only contact itself.
        if (self && a.row >= b.row) continue;
        if (!a.box.intersectsBox(b.box)) continue;
        tested++; if (!strictCross(a, b)) continue;
        count++; pairs.push([a.row, b.row]);
        if (witnesses.length < 32) witnesses.push({ first: { row: a.row, nativeIDs: a.nativeIDs, xyz: a.points.map(p => p.toArray()) },
          second: { row: b.row, nativeIDs: b.nativeIDs, xyz: b.points.map(p => p.toArray()) } });
      }
    };
    visit(index);
  }
  return { count, testedPairs: tested, pairs, witnesses, witnessesTruncated: count > witnesses.length };
}
