/** CPU exact source data/mutation fixtures; never calls the simplifier. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ROOT, pinned, POLICY, sha } from '../selected-production-constructor37/construct.mjs';
import { readProtection, protectFans, fanRetention } from './construct.mjs';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const evidence = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-fan59');
const censusFile = path.join(evidence, 'fan-census.json');
const report = JSON.parse(fs.readFileSync(censusFile));
const protection = readProtection(censusFile, report.census35, report.sourceArrayPackage);
const { data: candidateJSON } = pinned(report.constructor46), receipt = JSON.parse(candidateJSON);
const { data: source } = pinned(receipt.sourceArrayPackage), layout = receipt.sourceArrayPackage.layout;
const a = { positions: new Float32Array(source.buffer, source.byteOffset + layout.positions.byteOffset, layout.positions.byteLength / 4),
  triangles: new Uint32Array(source.buffer, source.byteOffset + layout.triangles.byteOffset, layout.triangles.byteLength / 4) };
const n = a.positions.length / 3;
const firstEdge = [a.triangles[0], a.triangles[1]].sort((a, b) => a - b);
function oldProtection() {
  const locks = new Uint8Array(n); firstEdge.forEach(v => { locks[v] = 1; });
  return { locks, requiredEdges: Uint32Array.from(firstEdge) };
}
const t = oldProtection(), merged = protectFans(a, t, protection);
assert.equal(merged.protectedCenters, 450); assert.equal(merged.originalFanVertices, 2049);
assert.equal(merged.exactRequiredSourceFaces, 2227); assert.equal(merged.originalFanEdges, 4143);
assert(firstEdge.every(v => t.locks[v] === 1));
assert([...protection.lockedOriginalVertexIds].every(v => t.locks[v] === 1));
assert(fanRetention(a, a.triangles, protection).passed, 'Source fans must pass unchanged');
const { data: candidate } = pinned(receipt.candidate), cl = receipt.candidate.layout;
const original = new Uint32Array(candidate.buffer, candidate.byteOffset + cl.originalVertexIds.byteOffset, cl.originalVertexIds.count);
const indices = new Uint32Array(candidate.buffer, candidate.byteOffset + cl.triangles.byteOffset, cl.triangles.count);
const currentResult = fanRetention(a, Uint32Array.from(indices, v => original[v]), protection);
assert(!currentResult.passed && currentResult.missingCount > 0);
const firstFace = protection.requiredSourceFaceIds[0], offset = 3 * firstFace;
const reversed = a.triangles.slice(); [reversed[offset], reversed[offset + 1]] = [reversed[offset + 1], reversed[offset]];
assert(!fanRetention(a, reversed, protection).passed, 'Reversed fan face must reject');
const missing = new Uint32Array(a.triangles.length - 3);
missing.set(a.triangles.subarray(0, offset)); missing.set(a.triangles.subarray(offset + 3), offset);
assert(!fanRetention(a, missing, protection).passed, 'Missing fan face must reject');
const duplicate = new Uint32Array(a.triangles.length + 3);
duplicate.set(a.triangles); duplicate.set(a.triangles.subarray(offset, offset + 3), a.triangles.length);
assert.equal(fanRetention(a, duplicate, protection).duplicateFaces, 1);
assert.throws(() => protectFans(a, oldProtection(), { ...protection,
  requiredSourceFaceIds: protection.requiredSourceFaceIds.subarray(1) }), /complete donor fan/);
assert.throws(() => protectFans(a, oldProtection(), { ...protection,
  lockedOriginalVertexIds: protection.lockedOriginalVertexIds.subarray(1) }), /vertex closure/);
assert.throws(() => protectFans(a, oldProtection(), { ...protection,
  requiredEdgesOriginal: protection.requiredEdgesOriginal.subarray(2) }), /edge closure/);
assert.deepEqual(POLICY.flags, ['ErrorAbsolute']); assert.equal(POLICY.targetErrorM, .001);
assert.equal(POLICY.minimumNormalDot, .25); assert.equal(POLICY.targetTriangles, 8000);
const recipe = fs.readFileSync(path.join(HERE, 'construct.mjs'), 'utf8');
assert.equal(recipe.match(/MeshoptSimplifier\.simplifyWithAttributes\(/g).length, 1);
assert(recipe.includes('sceneBudgetPassed: false, allocationPassed: false, simplificationTargetIsSoft: true'));
const checks = [
  'Complete actual census pins and full source fan closure verified: 450 centers, 2049 vertices, 2227 faces, 4143 edges',
  'Original locks retained; full source fans pass; current candidate fails complete protected-fan retention',
  'Reversed/deleted/duplicate faces and omitted center-fan faces/vertices/edges reject',
  'One index-only call; original 1mm/0.25/8000-soft target and ErrorAbsolute flag unchanged; no allocation pass',
];
fs.writeFileSync(path.join(evidence, 'construction-fixtures.json'), `${JSON.stringify({ status: 'CPU_CONSTRUCTOR_FIXTURES_PASSED_UNACCEPTED',
  recipeSHA256: sha(Buffer.from(recipe)), checks, currentCandidateRetention: currentResult,
  limits: 'No simplifier invocation or new candidate; parent original guard owns the actual single construction.' }, null, 2)}\n`);
for (const check of checks) console.log(`PASS: ${check}`);
