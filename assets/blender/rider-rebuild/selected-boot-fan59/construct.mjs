/** Parent-only single index-only candidate retaining all measured donor fans. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, POLICY, sha, pinned, readCensus, fieldsAndAttributes, topology, compactCandidate, writeArrays }
  from '../selected-production-constructor37/construct.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FROZEN = path.join(ROOT, 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs');
const FROZEN_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741';
const CANDIDATE46_SHA = '624affb3b59053d6bdee32fb3283c6b2ce23ff3d849c3fe0dd9669ec9319f3c8';
const FAN_CENSUS_SHA = '46b48498db71d774e9eb1e98793e0eec0f8d58b2b8e8b8a070edddafb12ec6ce';
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength);
const relative = p => path.relative(ROOT, p);
const same = (a, b) => a.length === b.length && a.every((value, i) => value === b[i]);
const sortedUnique = a => [...new Set(a)].sort((a, b) => a - b);
function triangleKey(a, b, c) {
  if (a < b && a < c) return `${a},${b},${c}`;
  if (b < a && b < c) return `${b},${c},${a}`;
  return `${c},${a},${b}`;
}

export function readProtection(file, censusPin, sourcePin) {
  const resolved = path.resolve(file), raw = fs.readFileSync(resolved), report = JSON.parse(raw);
  assert.equal(sha(raw), FAN_CENSUS_SHA, 'Reviewed complete fan census changed');
  assert.equal(report.status, 'COMPLETE_CPU_FAN_PROTECTION_CENSUS_UNACCEPTED');
  assert.equal(report.recipeSHA256, sha(fs.readFileSync(path.join(HERE, 'census.py'))));
  assert.equal(report.boundedFindingRecipeSHA256, sha(fs.readFileSync(path.join(HERE, 'diagnose.py'))));
  assert.equal(report.constructor46.sha256, CANDIDATE46_SHA); pinned(report.constructor46);
  assert.deepEqual(report.census35, censusPin); assert.deepEqual(report.sourceArrayPackage, sourcePin);
  assert.equal(report.minimumNormalDot, POLICY.minimumNormalDot);
  assert.equal(report.summary.sourceNormalReproductionBelowPoint25, 0);
  assert.equal(report.candidateAttempts, 0); assert.equal(report.sourceInputBytesUnchanged, true);
  const { data } = pinned(report.protection), arrays = {}; let offset = 0;
  assert.deepEqual(Object.keys(report.protection.layout), ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds', 'requiredEdgesOriginal']);
  for (const [name, row] of Object.entries(report.protection.layout)) {
    assert.equal(row.dtype, '<u4'); assert.equal(row.byteOffset, offset);
    assert(Number.isSafeInteger(row.count) && row.count > 0); assert.equal(row.byteLength, row.count * 4);
    assert(offset + row.byteLength <= data.length);
    arrays[name] = new Uint32Array(data.buffer, data.byteOffset + offset, row.count);
    offset += row.byteLength;
  }
  assert.equal(offset, data.length);
  return { ...arrays, report, pin: { path: relative(resolved), sha256: sha(raw) } };
}

export function protectFans(a, t, protection) {
  const n = a.positions.length / 3, centers = new Set(protection.centerOriginalVertexIds);
  assert.equal(centers.size, protection.centerOriginalVertexIds.length);
  assert(centers.size > 0 && [...centers].every(v => v < n));
  const requiredFaces = [], vertices = [], edgeKeys = [];
  for (let i = 0; i < a.triangles.length; i += 3) {
    const tri = a.triangles.subarray(i, i + 3);
    if (!tri.some(v => centers.has(v))) continue;
    requiredFaces.push(i / 3); vertices.push(...tri);
    for (let j = 0; j < 3; j++) edgeKeys.push(Math.min(tri[j], tri[(j + 1) % 3]) * n + Math.max(tri[j], tri[(j + 1) % 3]));
  }
  const locked = sortedUnique(vertices), required = sortedUnique(edgeKeys);
  assert(same(requiredFaces, protection.requiredSourceFaceIds), 'Protection omits/changes a complete donor fan');
  assert(same(locked, protection.lockedOriginalVertexIds), 'Fan vertex closure changed');
  const encoded = [];
  for (let i = 0; i < protection.requiredEdgesOriginal.length; i += 2) {
    const v = protection.requiredEdgesOriginal[i], w = protection.requiredEdgesOriginal[i + 1];
    assert(v < w && w < n); encoded.push(v * n + w);
  }
  assert(same(required, encoded), 'Fan edge closure changed');
  const merged = new Set(required); let addedLocks = 0;
  for (const v of locked) { assert(t.locks[v] === 0 || t.locks[v] === 1); if (!t.locks[v]) addedLocks++; t.locks[v] = 1; }
  for (let i = 0; i < t.requiredEdges.length; i += 2) merged.add(t.requiredEdges[i] * n + t.requiredEdges[i + 1]);
  t.requiredEdges = Uint32Array.from([...merged].sort((a, b) => a - b).flatMap(key => [Math.floor(key / n), key % n]));
  return { protectedCenters: centers.size, originalFanVertices: locked.length, addedLocks,
    exactRequiredSourceFaces: requiredFaces.length, originalFanEdges: required.length,
    totalLockedVertices: t.locks.reduce((sum, value) => sum + value, 0),
    totalRequiredEdges: t.requiredEdges.length / 2,
    policy: 'Union binary vertex_lock=1 with all existing locks; exact center-face and edge checks after compaction. No new simplify flag or error/normal threshold.' };
}

export function fanRetention(a, indices, protection) {
  const centers = new Set(protection.centerOriginalVertexIds), expected = new Set(), actual = new Set();
  for (const face of protection.requiredSourceFaceIds) expected.add(triangleKey(...a.triangles.subarray(3 * face, 3 * face + 3)));
  assert.equal(expected.size, protection.requiredSourceFaceIds.length, 'Duplicate protected source face');
  let duplicateFaces = 0;
  for (let i = 0; i < indices.length; i += 3) {
    const tri = indices.subarray(i, i + 3);
    if (!tri.some(v => centers.has(v))) continue;
    const key = triangleKey(...tri); if (actual.has(key)) duplicateFaces++; actual.add(key);
  }
  const missing = [...expected].filter(key => !actual.has(key));
  const unexpected = [...actual].filter(key => !expected.has(key));
  return { requiredSourceFaces: expected.size, actualProtectedIncidentFaces: actual.size,
    missingCount: missing.length, unexpectedCount: unexpected.length, duplicateFaces,
    firstMissingOrientedTriangles: missing.slice(0, 16), firstUnexpectedOrientedTriangles: unexpected.slice(0, 16),
    passed: missing.length === 0 && unexpected.length === 0 && duplicateFaces === 0 };
}

async function main() {
  assert.equal(process.argv.length, 5, 'Usage: node construct.mjs CENSUS35_JSON FAN_CENSUS59_JSON NEW_OUT');
  assert.equal(sha(fs.readFileSync(FROZEN)), FROZEN_SHA);
  const { a, census, censusPin } = readCensus(process.argv[2]);
  const protection = readProtection(process.argv[3], censusPin,
    { path: census.sourceArrayPackage.path, sha256: census.sourceArrayPackage.sha256 });
  assert.equal(protection.report.summary.sourceVerticesExamined, a.positions.length / 3);
  assert.equal(protection.report.summary.sourceTrianglesExamined, a.triangles.length / 3);
  const out = path.resolve(process.argv[4]), base = path.join(ROOT, 'harness/out/rider-rebuild/selected-boot-fan59');
  const rel = path.relative(base, out); assert(rel && !rel.startsWith('..') && !path.isAbsolute(rel));
  assert(!fs.existsSync(out), 'Never overwrite a candidate'); fs.mkdirSync(out, { recursive: true });
  const report = { status: 'INTAKE_IN_PROGRESS_UNACCEPTED', acceptedArt: false, candidateAttempts: 0,
    census: censusPin, censusSourcePins: census.sourcePins, sourceArrayPackage: census.sourceArrayPackage,
    constructorAncestry: { path: relative(FROZEN), sha256: FROZEN_SHA }, fanProtectionCensus: protection.pin,
    sceneBudgetPassed: false, allocationPassed: false, simplificationTargetIsSoft: true,
    policy: POLICY, recipeSHA256: sha(fs.readFileSync(fileURLToPath(import.meta.url))), groupNames: a.names,
    sourceVertices: a.positions.length / 3, sourceTriangles: a.triangles.length / 3,
    geometricQualification: 'NOT_RUN', bakeCompleted: false, movingReviewPassed: false, devicePassed: false };
  const write = () => fs.writeFileSync(path.join(out, 'constructor.json'), `${JSON.stringify(report, null, 2)}\n`);
  write();
  try {
    const attributes = fieldsAndAttributes(a); report.attributes = attributes.report; report.attributeWeights = attributes.weights; write();
    assert.equal(attributes.report.rowsNotFloat32Normalized, 0);
    const t = topology(a); report.originalTopology = t.report;
    report.fanProtection = protectFans(a, t, protection);
    report.topology = { ...t.report, lockedVertices: report.fanProtection.totalLockedVertices,
      requiredEdges: report.fanProtection.totalRequiredEdges, fanProtection: report.fanProtection };
    report.minimumTrianglesFromLockedVertexCount = Math.ceil(report.fanProtection.totalLockedVertices / 3); write();
    const moduleFile = path.join(ROOT, 'node_modules/meshoptimizer/meshopt_simplifier.js');
    assert.equal(sha(fs.readFileSync(moduleFile)), POLICY.simplifierSHA256);
    const { MeshoptSimplifier } = await import(pathToFileURL(moduleFile).href); await MeshoptSimplifier.ready;
    assert(MeshoptSimplifier.supported);
    const originals = [a.triangles, a.positions, attributes.attributes, t.locks];
    const before = originals.map(value => sha(bytes(value)));
    report.status = 'ONE_PROTECTED_FAN_CANDIDATE_RUNNING_UNACCEPTED'; report.candidateAttempts = 1; write();
    const [indices, approximateError] = MeshoptSimplifier.simplifyWithAttributes(a.triangles, a.positions, 3,
      attributes.attributes, attributes.stride, attributes.weights, t.locks,
      POLICY.targetTriangles * 3, POLICY.targetErrorM, POLICY.flags);
    assert.deepEqual(originals.map(value => sha(bytes(value))), before, 'Index-only API mutated source inputs');
    assert(Number.isFinite(approximateError) && approximateError >= 0);
    report.returnedOriginalIndices = writeArrays(path.join(out, 'returned-original-indices.bin'), { triangles: indices });
    report.targetTriangles = indices.length / 3; report.approximateCombinedErrorM = approximateError;
    report.simplificationTargetTriangles = POLICY.targetTriangles;
    report.simplificationTargetReached = report.targetTriangles <= POLICY.targetTriangles; write();
    const candidate = compactCandidate(a, t, indices);
    report.fanRetention = fanRetention(a, indices, protection); write();
    assert(report.fanRetention.passed, 'Exact protected donor incident fan changed');
    report.candidate = writeArrays(path.join(out, 'candidate.bin'), candidate); report.targetVertices = candidate.originalVertexIds.length;
    report.sourceInputBytesUnchanged = true; report.exactOriginalPositionsAndNamedFields = true;
    report.status = 'UNACCEPTED_SCENE_BUDGET_PENDING';
    report.limits = 'One exact-fan protected index-only candidate. No source topology/PBR edits, new flags, threshold changes, or target-count allocation award. Native surface/orientation/skin/contact, atlas bake, motion and scene budget remain open.';
    write(); console.log(JSON.stringify({ status: report.status, triangles: report.targetTriangles, fanRetention: report.fanRetention }));
  } catch (error) {
    report.status = 'REJECTED_CONSTRUCTOR59_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
