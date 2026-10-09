/** Numerical BVH/closure fixtures; never invokes the simplifier or Blender. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { closestTriangle, SourceTree, faceCensus } from './surface.mjs';
import { addFailures } from './closure.mjs';
import { normalCensus } from '../selected-boot-closure62/closure.mjs';
import { ROOT, ACTUAL62, FINDING66, readJSON, arrays, actualInput, filePin } from './io.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url)), checks = [];
for (const scale of [1, 1e-3, 1e-6]) {
  const p = [[0, 0, 0], [scale, 0, 0], [0, scale, 0]];
  const inside = closestTriangle([.25 * scale, .25 * scale, scale], ...p);
  const outside = closestTriangle([2 * scale, 0, 0], ...p);
  assert(Math.abs(inside.distanceSq / (scale * scale) - 1) < 1e-14);
  assert(Math.abs(outside.distanceSq / (scale * scale) - 1) < 1e-14);
  assert.deepEqual(inside.feature, [0, 1, 2]); assert.deepEqual(outside.feature, [1]);
}
assert.throws(() => closestTriangle([0, 0, 0], [0, 0, 0], [1, 0, 0], [2, 0, 0]), /Degenerate/);
checks.push('Meter/millimeter/micron point-triangle distance and feature fixtures pass; genuine collinear source rejects');

let seed = 6781; const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
const positions = Float32Array.from({ length: 160 * 9 }, () => 20 * random() - 10);
const triangles = Uint32Array.from({ length: 160 * 3 }, (_, i) => i);
const tree = new SourceTree(positions, triangles);
for (let i = 0; i < 240; i++) {
  const query = [0, 1, 2].map(() => 40 * random() - 20), result = tree.nearest(query);
  let minimum = Infinity, id = -1;
  for (let j = 0; j < triangles.length / 3; j++) {
    const d = tree.closestFace(query, j).distanceSq;
    if (d < minimum || (d === minimum && j < id)) { minimum = d; id = j; }
  }
  assert.equal(result.sourceFaceId, id); assert.equal(result.distanceM, Math.sqrt(minimum));
}
checks.push('Exhaustive branch-and-bound equals brute force for every deterministic random query, including points outside source bounds');

const folded = { positions: Float32Array.from([0,0,0, 1,0,0, 0,1,0, 0,0,1]), triangles: Uint32Array.from([0,1,2, 1,0,3]) };
const foldedTree = new SourceTree(folded.positions, folded.triangles), hit = foldedTree.nearest([.5,-.5,-.5]);
assert.deepEqual(hit.bearingSourceFaceIds, [0,1]); assert.deepEqual(hit.closestBoundaryFeatureOriginalVertices.slice().sort(), [0,1]);
assert(faceCensus(folded, Uint32Array.from([1,2,0]), foldedTree).report.passed, 'Cyclic source-face ancestry retained');
const reversed = faceCensus(folded, Uint32Array.from([0,2,1]), foldedTree).report;
assert(!reversed.passed && reversed.failures[0].normalDot === -1);
const newFold = faceCensus(folded, Uint32Array.from([1,3,2]), foldedTree).report; assert(!newFold.passed);
checks.push('Closest shared-edge faces are all geometric bearings; cyclic exact ancestry passes while reversed/new folds reject at unchanged0.25');

const { a, returned } = actualInput(), native = normalCensus(a, returned);
assert(native.passed && native.verticesExamined === 13250);
const formerlyRejected = [];
for (let i = 0; i < a.triangles.length; i += 3) {
  const p = Array.from(a.triangles.subarray(i, i + 3), v => Array.from(a.positions.subarray(v * 3, v * 3 + 3)));
  const u = p[1].map((v, j) => v - p[0][j]), v = p[2].map((v, j) => v - p[0][j]);
  const dot = (a, b) => a.reduce((sum, value, j) => sum + value * b[j], 0);
  if (dot(u, u) * dot(v, v) - dot(u, v) ** 2 > 1e-24) continue;
  formerlyRejected.push(i / 3);
  const q = [0, 1, 2].map(j => (p[0][j] + p[1][j] + p[2][j]) / 3), hit = closestTriangle(q, ...p);
  assert(Number.isFinite(hit.distanceSq) && hit.distanceSq < .001 ** 2);
}
assert.equal(formerlyRejected.length, 78);
checks.push('All 78 actual positive microscopic source faces rejected by the old Gram cutoff have finite scale-independent closest points');
const preflightFile = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-surface67/preflight.json');
const preflight = JSON.parse(fs.readFileSync(preflightFile));
assert.equal(preflight.status, 'COMPLETE_CPU_NATIVE_COMPARISON_UNACCEPTED');
assert.equal(preflight.completedSamples, 26528); assert.equal(preflight.maximumRecordedBearingDotDelta, 0);
assert.deepEqual(preflight.nativeNewFailuresMissedByCPU, []); assert.deepEqual(preflight.cpuAdditionalNewFailures, [10230]);
assert.equal(preflight.disagreements.length, 305);
for (const recipe of preflight.recipes) assert.deepEqual(recipe, filePin(path.join(ROOT, recipe.path)));
const finding = readJSON(FINDING66), prior = arrays(finding.proposedConstructionConstraint.arrays);
const next = addFailures(a, prior, native, preflight.actual62ProperFaceCensus, false);
const complete = new Set(next.next.centerOriginalVertexIds);
for (const row of preflight.actual62ProperFaceCensus.failures) {
  for (const v of [...row.originalVertexIds, ...row.sourceBearingOriginalVertexIds]) assert(complete.has(v));
}
assert.throws(() => addFailures(a, next.next, native, preflight.actual62ProperFaceCensus), /no new original fan/);
const permutation = { ...preflight.actual62ProperFaceCensus, failures: [...preflight.actual62ProperFaceCensus.failures].reverse() };
assert.deepEqual(addFailures(a, prior, native, permutation, false).next, next.next);
checks.push('All 26,528 actual63 queries validated; all 94 native new failures plus one shared-edge failure enter simultaneous monotone closure; no-progress rejects');

const recipe = fs.readFileSync(path.join(HERE, 'construct.mjs'), 'utf8');
assert(recipe.includes('simplifyWithAttributes(a.triangles, a.positions, 3,'));
assert(recipe.includes('POLICY.targetTriangles * 3, POLICY.targetErrorM, POLICY.flags'));
assert.equal(recipe.match(/MeshoptSimplifier\.simplifyWithAttributes\(/g).length, 1);
assert(recipe.includes('row.vertexNormalCensus.passed && row.faceCentroidCensus.passed'));
assert(recipe.includes('assert(row.fanRetention.passed'));
assert(recipe.includes('readJSON(preflightPin)') && recipe.includes('preflight.nativeNewFailuresMissedByCPU, []'));
assert(recipe.indexOf('if (complete)') < recipe.indexOf('report.fixedPoint.complete = true'));
assert(recipe.includes('nativeFaceAncestryProofRequired: true, nativeFaceAncestryPolicyChanged: false'));
checks.push('Constructor admits reviewed exhaustive preflight, re-reduces original source, retains exact fans and requires both full censuses before completion');

const out = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-surface67');
fs.writeFileSync(path.join(out, 'fixtures.json'), `${JSON.stringify({ status: 'CPU_SURFACE_AND_CLOSURE_FIXTURES_PASSED_NATIVE_PROOF_PENDING',
  actual62: ACTUAL62, preflight: filePin(preflightFile), checks,
  initialJointProtection: { centers: next.next.centerOriginalVertexIds.length, addedCenters: next.addedCenters,
    vertices: next.next.lockedOriginalVertexIds.length, faces: next.next.requiredSourceFaceIds.length, edges: next.next.requiredEdgesOriginal.length / 2 },
  limits: 'No simplifier or native job. Actual native67 proof and independent qualification remain required.' }, null, 2)}\n`);
for (const check of checks) console.log(`PASS: ${check}`);
