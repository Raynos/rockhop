/** Conservative AABB broadphase; final contact uses the qualified finite SAT predicate. */
import { triangleContact } from './triangle-contacts.mjs';
const EPSILON = 1e-9;
const overlap = (a, b) => [0, 1, 2].every(k => a.min[k] <= b.max[k] + EPSILON && b.min[k] <= a.max[k] + EPSILON);
export function triangleRows(vertices, faces, sourceIDs = null) {
  return faces.map((ids, id) => {
    const points = ids.map(i => vertices[i]);
    return { id, ids: sourceIDs ? ids.map(i => sourceIDs[i]) : ids, points, min: [0, 1, 2].map(k => Math.min(...points.map(p => p[k]))), max: [0, 1, 2].map(k => Math.max(...points.map(p => p[k]))) };
  });
}
function build(rows) {
  const min = [0, 1, 2].map(k => Math.min(...rows.map(r => r.min[k]))), max = [0, 1, 2].map(k => Math.max(...rows.map(r => r.max[k])));
  if (rows.length <= 12) return { min, max, rows };
  const axis = [0, 1, 2].reduce((a, b) => max[a] - min[a] >= max[b] - min[b] ? a : b);
  const sorted = rows.slice().sort((a, b) => a.min[axis] + a.max[axis] - b.min[axis] - b.max[axis]), half = Math.floor(sorted.length / 2);
  return { min, max, left: build(sorted.slice(0, half)), right: build(sorted.slice(half)) };
}
export function bvhContacts(a, b, excludeSharedNative = false, sameSet = false) {
  if (!a.length || !b.length) return { pairs: 0, witnesses: [], candidates: 0 };
  const tree = build(b), witnesses = []; let pairs = 0, candidates = 0;
  function query(row, node) {
    if (!overlap(row, node)) return;
    if (!node.rows) { query(row, node.left); query(row, node.right); return; }
    for (const other of node.rows) {
      if (sameSet && other.id <= row.id || excludeSharedNative && row.ids.some(id => other.ids.includes(id)) || !overlap(row, other)) continue;
      candidates++;
      if (triangleContact(row.points, other.points, EPSILON)) { pairs++; if (witnesses.length < 12) witnesses.push({ triangleA: row.id, triangleB: other.id }); }
    }
  }
  for (const row of a) query(row, tree);
  return { pairs, witnesses, candidates, epsilonM: EPSILON, limits: 'Finite contact only; no swept/volume penetration. Shared native IDs are excluded only when explicitly requested.' };
}
