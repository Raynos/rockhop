/** One soft-target candidate; imports every frozen37 geometry/field algorithm. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, POLICY, sha, readCensus, fieldsAndAttributes, topology, compactCandidate, writeArrays }
  from '../selected-production-constructor37/construct.mjs';
const FROZEN_CONSTRUCTOR = path.join(ROOT, 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs');
const FROZEN_CONSTRUCTOR_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741';
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength);
const relative = p => path.relative(ROOT, p);
function inside(p, base) {
  const rel = path.relative(base, p);
  assert(rel && !rel.startsWith('..') && !path.isAbsolute(rel), `Path outside ${base}: ${p}`);
}
export function targetOutcome(actualTriangles) {
  assert(Number.isSafeInteger(actualTriangles) && actualTriangles > 0);
  return { simplificationTargetTriangles: POLICY.targetTriangles,
    simplificationTargetReached: actualTriangles <= POLICY.targetTriangles,
    targetTriangles: actualTriangles, allocationPassed: false, sceneBudgetPassed: false,
    status: 'UNACCEPTED_SCENE_BUDGET_PENDING' };
}
async function main() {
  assert.equal(process.argv.length, 4, 'Usage: node construct.mjs COMPLETE_CENSUS_JSON NEW_OUT');
  assert.equal(sha(fs.readFileSync(FROZEN_CONSTRUCTOR)), FROZEN_CONSTRUCTOR_SHA);
  const { a, census, censusPin } = readCensus(process.argv[2]);
  const out = path.resolve(process.argv[3]); inside(out, path.join(ROOT, 'harness/out/rider-rebuild/selected-production-allocation46'));
  assert(!fs.existsSync(out), 'Never overwrite a candidate or retry in the same directory');
  fs.mkdirSync(out, { recursive: true });
  const report = { status: 'INTAKE_IN_PROGRESS_UNACCEPTED', acceptedArt: false, candidateAttempts: 0,
    census: censusPin, censusSourcePins: census.sourcePins, sourceArrayPackage: census.sourceArrayPackage,
    constructorAncestry: { path: relative(FROZEN_CONSTRUCTOR), sha256: FROZEN_CONSTRUCTOR_SHA },
    sceneBudgetPassed: false, allocationPassed: false, simplificationTargetIsSoft: true,
    policy: POLICY, recipeSHA256: sha(fs.readFileSync(fileURLToPath(import.meta.url))), groupNames: a.names,
    sourceVertices: a.positions.length / 3, sourceTriangles: a.triangles.length / 3,
    geometricQualification: 'NOT_RUN', bakeCompleted: false, movingReviewPassed: false, devicePassed: false };
  const write = () => fs.writeFileSync(path.join(out, 'constructor.json'), `${JSON.stringify(report, null, 2)}\n`);
  write();
  try {
    const attributes = fieldsAndAttributes(a); report.attributes = attributes.report; report.attributeWeights = attributes.weights; write();
    assert.equal(attributes.report.rowsNotFloat32Normalized, 0, 'Actual source skin row sum is not1 at float32 precision; inspect report, never normalize it silently');
    const t = topology(a); report.topology = t.report;
    report.minimumTrianglesFromLockedVertexCount = Math.ceil(t.report.lockedVertices / 3); write();
    // The measured protected count is retained; it cannot reject a soft target.
    // All original locks and protected-edge/component checks remain mandatory.
    const moduleFile = path.join(ROOT, 'node_modules/meshoptimizer/meshopt_simplifier.js');
    assert.equal(sha(fs.readFileSync(moduleFile)), POLICY.simplifierSHA256);
    const { MeshoptSimplifier } = await import(pathToFileURL(moduleFile).href); await MeshoptSimplifier.ready;
    assert(MeshoptSimplifier.supported, 'Pinned meshoptimizer unavailable');
    const originals = [a.triangles, a.positions, attributes.attributes, t.locks];
    const before = originals.map(value => sha(bytes(value)));
    report.status = 'ONE_ATTRIBUTE_CANDIDATE_RUNNING_UNACCEPTED'; report.candidateAttempts = 1; write();
    const [indices, approximateError] = MeshoptSimplifier.simplifyWithAttributes(a.triangles, a.positions, 3,
      attributes.attributes, attributes.stride, attributes.weights, t.locks,
      POLICY.targetTriangles * 3, POLICY.targetErrorM, POLICY.flags);
    assert.deepEqual(originals.map(value => sha(bytes(value))), before, 'Index-only API mutated source inputs');
    assert(Number.isFinite(approximateError) && approximateError >= 0);
    report.returnedOriginalIndices = writeArrays(path.join(out, 'returned-original-indices.bin'), { triangles: indices });
    report.targetTriangles = indices.length / 3; report.approximateCombinedErrorM = approximateError;
    Object.assign(report, targetOutcome(report.targetTriangles)); write();
    const candidate = compactCandidate(a, t, indices);
    report.candidate = writeArrays(path.join(out, 'candidate.bin'), candidate); report.targetVertices = candidate.originalVertexIds.length;
    report.sourceInputBytesUnchanged = true; report.exactOriginalPositionsAndNamedFields = true;
    report.status = 'UNACCEPTED_SCENE_BUDGET_PENDING';
    report.limits = 'One area-weighted priority attempt; approximate error is not surface/orientation/skin/contact proof. Native gates, selected atlas bake, complete motion and device remain open. No normal-player output.';
    write(); console.log(JSON.stringify({ status: report.status, triangles: report.targetTriangles, approximateError, candidate: report.candidate.path }));
    // Above-target output remains inspectable; allocation has never passed here.
  } catch (error) {
    report.status = 'REJECTED_CONSTRUCTOR46_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
