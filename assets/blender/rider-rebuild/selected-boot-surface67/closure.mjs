/** All vertex and geometric-face failures add original source fans together. */
import assert from 'node:assert/strict';
import { fanClosure } from '../selected-boot-closure62/closure.mjs';

export function failureCenters(vertex, face) {
  const centers = new Set();
  for (const row of vertex.failures) {
    assert(row.normalDot === null || row.normalDot < .25); centers.add(row.originalVertexId);
  }
  for (const row of face.failures) {
    assert(row.normalDot < .25 || row.distanceM > .001);
    assert.equal(row.exactInheritedSourceFace, false, 'Exact inherited face failed geometric identity');
    for (const v of [...row.originalVertexIds, ...row.sourceBearingOriginalVertexIds]) centers.add(v);
  }
  return [...centers].sort((a, b) => a - b);
}
export function addFailures(a, protection, vertex, face, requireProgress = true) {
  assert(!vertex.passed || !face.passed, 'No failed metric to constrain');
  const prior = new Set(protection.centerOriginalVertexIds), requested = failureCenters(vertex, face);
  const added = requested.filter(v => !prior.has(v));
  if (requireProgress) assert(added.length > 0, 'Fixed-point rejected: no new original fan can be protected');
  const next = fanClosure(a, [...prior, ...requested]);
  for (const key of ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds']) {
    const after = new Set(next[key]); assert([...protection[key]].every(v => after.has(v)), `Protection shrank: ${key}`);
  }
  const edges = new Set();
  for (let i = 0; i < next.requiredEdgesOriginal.length; i += 2) edges.add(`${next.requiredEdgesOriginal[i]},${next.requiredEdgesOriginal[i + 1]}`);
  for (let i = 0; i < protection.requiredEdgesOriginal.length; i += 2) assert(edges.has(`${protection.requiredEdgesOriginal[i]},${protection.requiredEdgesOriginal[i + 1]}`));
  return { next, addedCenters: added, requestedCenters: requested };
}
