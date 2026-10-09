/** CPU actual59 regression and fixed-point mutations; no simplifier call. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ROOT, pinned, POLICY, sha } from '../selected-production-constructor37/construct.mjs';
import { readProtection, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { normalCensus, fanClosure, augment } from './closure.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const actual = { path: 'harness/out/rider-rebuild/selected-boot-fan59/candidate01/constructor.json',
  sha256: 'e969f9f5f84fffe9d1a13320c374a7a93f929f1f11b1b4b2c975635a6a5fe69f' };
const { data: receiptBytes } = pinned(actual), receipt = JSON.parse(receiptBytes);
const { data: source } = pinned(receipt.sourceArrayPackage), l = receipt.sourceArrayPackage.layout;
const a = { positions: new Float32Array(source.buffer, source.byteOffset + l.positions.byteOffset, l.positions.byteLength / 4),
  normals: new Float32Array(source.buffer, source.byteOffset + l.vertexNormals.byteOffset, l.vertexNormals.byteLength / 4),
  triangles: new Uint32Array(source.buffer, source.byteOffset + l.triangles.byteOffset, l.triangles.byteLength / 4) };
const { data: returned } = pinned(receipt.returnedOriginalIndices), row = receipt.returnedOriginalIndices.layout.triangles;
const indices = new Uint32Array(returned.buffer, returned.byteOffset + row.byteOffset, row.count);
const report = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-fan59/fan-census.json')));
const seed = readProtection(path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-fan59/fan-census.json'), report.census35, report.sourceArrayPackage);
const census = normalCensus(a, indices);
assert.equal(census.verticesExamined, 13246); assert.equal(census.trianglesExamined, 26520);
assert.equal(census.failures.length, 1); assert.equal(census.failures[0].targetVertexId, 6886);
assert.equal(census.failures[0].originalVertexId, 120878);
assert(Math.abs(census.failures[0].normalDot - 0.0199895531) < 1e-8);
assert(fanRetention(a, indices, seed).passed, 'Actual59 still retains every previously required fan');
const addition = augment(a, seed, census);
assert.deepEqual(addition.addedCenters, [120878]);
assert.equal(addition.next.centerOriginalVertexIds.length, seed.centerOriginalVertexIds.length + 1);
assert(!fanRetention(a, indices, addition.next).passed, 'Actual59 is not silently accepted after adding the missing fan');
assert(fanRetention(a, a.triangles, addition.next).passed, 'Full donor source retains every augmented fan');
assert.throws(() => augment(a, addition.next, census), /no new original fan/);

// Multiple new failures are admitted together; order/duplicates cannot change closure.
const seedCenters = new Set(seed.centerOriginalVertexIds), extra = [];
for (let v = 0; extra.length < 2; v++) if (!seedCenters.has(v)) extra.push(v);
const many = { passed: false, failures: extra.map(originalVertexId => ({ originalVertexId, normalDot: -.5 })) };
const all = augment(a, seed, many);
assert.deepEqual(all.addedCenters, extra);
const reversedFailures = { passed: false, failures: [...many.failures].reverse().concat(many.failures[0]) };
assert.deepEqual(augment(a, seed, reversedFailures).next, all.next);
for (const key of ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds']) {
  const next = new Set(all.next[key]); assert([...seed[key]].every(v => next.has(v)), key);
}
const plane = { positions: Float32Array.from([0, 0, 0, 1, 0, 0, 0, 1, 0]),
  normals: Float32Array.from([0, 0, 1, 0, 0, 1, 0, 0, 1]), triangles: Uint32Array.from([0, 1, 2]) };
assert(normalCensus(plane, plane.triangles).passed);
assert.equal(normalCensus(plane, Uint32Array.from([0, 2, 1])).failingVertices, 3);
assert.throws(() => normalCensus(plane, Uint32Array.from([0, 0, 1])), /Degenerate candidate face/);
assert.deepEqual(fanClosure(plane, [2, 1, 2]), fanClosure(plane, [1, 2]));

const recipe = fs.readFileSync(path.join(HERE, 'construct.mjs'), 'utf8');
assert(recipe.includes('simplifyWithAttributes(a.triangles, a.positions, 3,'));
assert(recipe.includes('POLICY.targetTriangles * 3, POLICY.targetErrorM, POLICY.flags'));
assert.equal(recipe.match(/MeshoptSimplifier\.simplifyWithAttributes\(/g).length, 1);
assert(recipe.indexOf('if (row.vertexNormalCensus.passed)') < recipe.indexOf('report.fixedPoint.complete = true'));
assert(recipe.includes('assert(row.fanRetention.passed'));
assert.deepEqual(POLICY.flags, ['ErrorAbsolute']); assert.equal(POLICY.targetErrorM, .001);
assert.equal(POLICY.minimumNormalDot, .25); assert.equal(POLICY.targetTriangles, 8000);
const checks = [
  'Actual59 full census reproduces exactly one failure: target6886/original120878, dot0.0199895531',
  'Existing2227 protected faces still pass; monotone augmentation adds the failing donor fan and rejects the unchanged old candidate',
  'Every failing fan grows together; closure is deterministic, duplicate-safe and preserves previous centers/vertices/faces',
  'No-progress repeated failure rejects; positive/reversed/degenerate geometry fixtures distinguish pass/failure',
  'Loop always re-reduces original source with frozen attributes/error/flags and retains exact fans before CPU completion',
];
const out = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-closure62'); fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'fixtures.json'), `${JSON.stringify({ status: 'CPU_FIXED_POINT_SOURCE_FIXTURES_PASSED_UNACCEPTED',
  actual59: actual, actual59Census: census,
  augmentedProtection: { centers: addition.next.centerOriginalVertexIds.length, vertices: addition.next.lockedOriginalVertexIds.length,
    faces: addition.next.requiredSourceFaceIds.length, edges: addition.next.requiredEdgesOriginal.length / 2 },
  constructorRecipeSHA256: sha(Buffer.from(recipe)), checks,
  limits: 'No reduction or native job ran. Passing closure/source fixtures do not show that the future constructor reaches a fixed point or qualifies art.' }, null, 2)}\n`);
for (const check of checks) console.log(`PASS: ${check}`);
