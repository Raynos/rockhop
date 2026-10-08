import assert from 'node:assert/strict';
import { Box3, Matrix3, Vector3 } from 'three';
export const V = p => new Vector3(...p);
export function anatomicalCageMember(influences, eligible, excluded) {
  return influences.some(({ joint, weight }) => weight > 0 && eligible.has(joint))
    && !influences.some(({ joint, weight }) => weight > 0 && excluded.has(joint));
}
export function rotation(matrix) {
  let r = matrix.clone();
  assert(r.determinant() > 1e-8, 'No invertible orientation-preserving skin/cage frame');
  for (let i = 0; i < 16; i++) {
    const inverse = r.clone().invert().transpose(), next = r.clone(); let change = 0;
    for (let k = 0; k < 9; k++) { next.elements[k] = (r.elements[k] + inverse.elements[k]) / 2; change += (next.elements[k] - r.elements[k]) ** 2; }
    r = next; if (change < 1e-20) break;
  }
  assert(Math.abs(r.determinant() - 1) < 1e-5, 'Polar rotation did not converge'); return r;
}
export function triangleFrame(points) {
  const x = points[1].clone().sub(points[0]).normalize(), z = new Vector3().crossVectors(x, points[2].clone().sub(points[0])).normalize();
  assert(z.lengthSq() > .99, 'Degenerate cage triangle'); const y = new Vector3().crossVectors(z, x);
  return new Matrix3().set(x.x, y.x, z.x, x.y, y.y, z.y, x.z, y.z, z.z);
}
export function index(triangles) {
  const box = new Box3(); for (const t of triangles) box.union(t.box);
  if (triangles.length <= 12) return { box, triangles };
  const extent = box.getSize(new Vector3()).toArray(), axis = ['x', 'y', 'z'][extent.indexOf(Math.max(...extent))];
  const sorted = [...triangles].sort((a, b) => a.box.min[axis] + a.box.max[axis] - b.box.min[axis] - b.box.max[axis]);
  const half = Math.floor(sorted.length / 2); return { box, children: [index(sorted.slice(0, half)), index(sorted.slice(half))] };
}
export function closest(point, root) {
  let best = null;
  const visit = node => {
    if (best && node.box.distanceToPoint(point) ** 2 > best.distanceSq) return;
    if (node.children) return [...node.children].sort((a, b) => a.box.distanceToPoint(point) - b.box.distanceToPoint(point)).forEach(visit);
    for (const t of node.triangles) {
      const p = t.shape.closestPointToPoint(point, new Vector3()), d = p.distanceToSquared(point);
      if (!best || d < best.distanceSq) best = { point: p, distanceSq: d, triangle: t };
    }
  };
  visit(root); return best;
}
export function inside(point, triangles) {
  let angle = 0;
  for (const t of triangles) {
    const [a, b, c] = t.points.map(p => p.clone().sub(point)), la = a.length(), lb = b.length(), lc = c.length();
    if (Math.min(la, lb, lc) < 1e-12) return false;
    angle += 2 * Math.atan2(a.dot(new Vector3().crossVectors(b, c)), la * lb * lc + a.dot(b) * lc + b.dot(c) * la + c.dot(a) * lb);
  }
  return Math.abs(angle) > 2 * Math.PI;
}
/** Fixed-rotation differential-coordinate reconstruction. Edge goals remove the
 * skin-weight-gradient stretch while retaining source edge detail. Dirichlet
 * rows carry actual contact/obstacle handles; no objective weight can trade them.
 */
export function reconstruct(vertices, edges, fixed, rotations, deadline) {
  const free = vertices.map((_, i) => i).filter(i => !fixed.has(i)), slots = new Map(free.map((id, i) => [id, i]));
  const n = free.length, diagonal = new Float64Array(n), rhs = new Float64Array(n * 3), links = [];
  for (const [a, b, w] of edges) {
    const rest = vertices[a].rest.clone().sub(vertices[b].rest);
    const d = rest.clone().applyMatrix3(rotations[a]).add(rest.clone().applyMatrix3(rotations[b])).multiplyScalar(.5);
    const ia = slots.get(a), ib = slots.get(b);
    for (const [id, other, slot, sign] of [[a, b, ia, 1], [b, a, ib, -1]]) if (slot !== undefined) {
      diagonal[slot] += w; const target = fixed.get(other);
      for (let k = 0; k < 3; k++) rhs[slot * 3 + k] += w * (sign * d.getComponent(k) + (target?.getComponent(k) ?? 0));
    }
    if (ia !== undefined && ib !== undefined) links.push([ia, ib, w]);
  }
  assert(diagonal.every(d => d > 0), 'Unanchored or isolated reconstruction vertex');
  const multiply = x => {
    const y = new Float64Array(x.length);
    for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) y[i * 3 + k] = diagonal[i] * x[i * 3 + k];
    for (const [a, b, w] of links) for (let k = 0; k < 3; k++) { y[a * 3 + k] -= w * x[b * 3 + k]; y[b * 3 + k] -= w * x[a * 3 + k]; }
    return y;
  };
  const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0), x = new Float64Array(free.flatMap(id => vertices[id].posed.toArray()));
  const ax = multiply(x), r = rhs.map((v, i) => v - ax[i]), z = r.map((v, i) => v / diagonal[Math.floor(i / 3)]), p = z.slice();
  let rz = dot(r, z), iteration = 0;
  const relative = () => Math.sqrt(dot(r, r) / Math.max(1e-30, dot(rhs, rhs)));
  for (; iteration < 300 && relative() > 1e-10; iteration++) {
    assert(Date.now() < deadline, 'Bounded corrective deadline reached');
    const ap = multiply(p), denom = dot(p, ap); assert(denom > 0, 'Reconstruction system is not positive definite');
    const alpha = rz / denom;
    for (let i = 0; i < x.length; i++) { x[i] += alpha * p[i]; r[i] -= alpha * ap[i]; z[i] = r[i] / diagonal[Math.floor(i / 3)]; }
    const next = dot(r, z), beta = next / rz;
    for (let i = 0; i < p.length; i++) p[i] = z[i] + beta * p[i]; rz = next;
  }
  assert(relative() < 1e-8, 'Reconstruction failed to converge within 300 CG steps');
  const positions = vertices.map((v, id) => fixed.get(id)?.clone() ?? V(Array.from(x.slice(slots.get(id) * 3, slots.get(id) * 3 + 3))));
  return { positions, cgIterations: iteration, relativeResidual: relative(), freeVertices: n };
}
export function relativeFlex(pelvis, thigh, restRelative) {
  return pelvis.clone().invert().multiply(thigh).multiply(restRelative.clone().invert()).normalize();
}
export function activation(current, key, radius) {
  const distance = Math.hypot(...current.map((q, i) => q.angleTo(key[i]))), x = distance / radius;
  return x >= 1 ? 0 : (1 - x) ** 4 * (4 * x + 1);
}
