/** Parent-guarded joint vertex/face fixed point from the immutable full donor. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, POLICY, sha, readCensus, fieldsAndAttributes, topology, compactCandidate, writeArrays }
  from '../selected-production-constructor37/construct.mjs';
import { protectFans, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { normalCensus, fanClosure, MINIMUM_NORMAL_DOT } from '../selected-boot-closure62/closure.mjs';
import { SourceTree, faceCensus } from './surface.mjs';
import { addFailures } from './closure.mjs';
import { FINDING66, REFERENCE, ACTUAL62, arrays, filePin, readJSON, verifyImports } from './io.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FROZEN37 = path.join(ROOT, 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs');
const FROZEN37_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741';
const FROZEN59 = path.join(ROOT, 'assets/blender/rider-rebuild/selected-boot-fan59/construct.mjs');
const FROZEN59_SHA = 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f';
const FROZEN62 = path.join(ROOT, 'assets/blender/rider-rebuild/selected-boot-closure62/construct.mjs');
const FROZEN62_SHA = '56ac49d3d2001f65ea39bb6d151768e8b9626c8c192bf1ed90fa03ffaefa42cc';
const relative = file => path.relative(ROOT, file);
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength);
const writeJSON = (file, value) => fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);

async function main() {
  assert.equal(process.argv.length, 7, 'Usage: node construct.mjs CENSUS35_JSON FINDING66_JSON PREFLIGHT_JSON REVIEWED_PREFLIGHT_SHA NEW_OUT');
  verifyImports();
  assert.equal(sha(fs.readFileSync(FROZEN37)), FROZEN37_SHA);
  assert.equal(sha(fs.readFileSync(FROZEN59)), FROZEN59_SHA);
  assert.equal(sha(fs.readFileSync(FROZEN62)), FROZEN62_SHA);
  assert.equal(MINIMUM_NORMAL_DOT, POLICY.minimumNormalDot);
  assert.deepEqual(POLICY.flags, ['ErrorAbsolute']); assert.equal(POLICY.targetErrorM, .001);
  const { a, census, censusPin } = readCensus(process.argv[2]);
  assert.equal(path.resolve(process.argv[3]), path.join(ROOT, FINDING66.path));
  const finding = readJSON(FINDING66);
  assert.deepEqual(finding.sourceArrays, { path: census.sourceArrayPackage.path, sha256: census.sourceArrayPackage.sha256 });
  const seed = arrays(finding.proposedConstructionConstraint.arrays);
  let protection = fanClosure(a, seed.centerOriginalVertexIds);
  for (const key of Object.keys(protection)) assert.deepEqual(protection[key], seed[key], 'Complete66 source-fan closure changed');
  const preflightPath = path.resolve(process.argv[4]), expectedPreflight = process.argv[5];
  assert.equal(preflightPath, path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-surface67/preflight.json'));
  assert(/^[a-f0-9]{64}$/.test(expectedPreflight));
  const preflightPin = filePin(preflightPath); assert.equal(preflightPin.sha256, expectedPreflight);
  const preflight = readJSON(preflightPin);
  assert.equal(preflight.status, 'COMPLETE_CPU_NATIVE_COMPARISON_UNACCEPTED');
  assert.equal(preflight.validationPassed, true); assert.equal(preflight.completedSamples, 26528);
  assert.equal(preflight.samples, preflight.completedSamples);
  assert.deepEqual(preflight.constructor, ACTUAL62); assert.deepEqual(preflight.nativeReference, REFERENCE);
  assert.deepEqual(preflight.diagnosis66, FINDING66);
  assert.deepEqual(preflight.sourceArrays, finding.sourceArrays);
  assert.deepEqual(preflight.nativeNewFailuresMissedByCPU, []);
  assert.equal(preflight.maximumRecordedBearingDotDelta, 0); assert.equal(preflight.nativeBearingCloserThanCPUCount, 0);
  assert.equal(preflight.minimumNormalDot, .25); assert.equal(preflight.maximumSurfaceErrorM, .001);
  for (const recipe of preflight.recipes) assert.deepEqual(recipe, filePin(path.join(ROOT, recipe.path)));
  // Include all measured native failures and all proper CPU tie failures together.
  const initial = addFailures(a, protection, { passed: true, failures: [] }, preflight.actual62ProperFaceCensus, false);
  protection = initial.next;
  const out = path.resolve(process.argv[6]), base = path.join(ROOT, 'harness/out/rider-rebuild/selected-boot-surface67');
  const rel = path.relative(base, out); assert(rel && !rel.startsWith('..') && !path.isAbsolute(rel));
  assert(!fs.existsSync(out), 'Never overwrite a closure experiment'); fs.mkdirSync(out, { recursive: true });
  const report = { status: 'FIXED_POINT_INTAKE_UNACCEPTED', acceptedArt: false, candidateAttempts: 0,
    census: censusPin, censusSourcePins: census.sourcePins, sourceArrayPackage: census.sourceArrayPackage,
    constructorAncestry: { path: relative(FROZEN37), sha256: FROZEN37_SHA },
    fanConstructorAncestry: { path: relative(FROZEN59), sha256: FROZEN59_SHA }, initialFaceDiagnosis: FINDING66, initialConstraintArrays: finding.proposedConstructionConstraint.arrays,
    fixedPointConstructorAncestry62: { path: relative(FROZEN62), sha256: FROZEN62_SHA },
    exhaustiveNative63Preflight: preflightPin, initialCPUAddedFanCenters: initial.addedCenters,
    recipeSHA256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
    closureRecipeSHA256: sha(fs.readFileSync(path.join(HERE, 'closure.mjs'))),
    surfaceRecipeSHA256: sha(fs.readFileSync(path.join(HERE, 'surface.mjs'))), policy: POLICY,
    groupNames: a.names, sourceVertices: a.positions.length / 3, sourceTriangles: a.triangles.length / 3,
    sceneBudgetPassed: false, allocationPassed: false, simplificationTargetIsSoft: true,
    geometricQualification: 'NOT_RUN', bakeCompleted: false, movingReviewPassed: false, devicePassed: false,
    fixedPoint: { complete: false, minimumNormalDot: MINIMUM_NORMAL_DOT,
      rule: 'Each iteration reduces the same immutable original source with identical attributes/error/flags. Census every vertex and face. New faces use globally nearest geometry including all common closest-edge/vertex bearings; exact oriented source faces use their own ancestry. Add every failing target/source-bearing fan together, monotonically. Stop only when both complete censuses pass; reject if no new fan can be protected.',
      runtimeBound: 'The parent original external guard bounds the whole invocation; no local retry/time-limit substitute.',
      iterations: [] } };
  const write = () => writeJSON(path.join(out, 'constructor.json'), report); write();
  try {
    const attributes = fieldsAndAttributes(a); report.attributes = attributes.report; report.attributeWeights = attributes.weights;
    assert.equal(attributes.report.rowsNotFloat32Normalized, 0);
    const t = topology(a); report.originalTopology = t.report; write();
    const tree = new SourceTree(a.positions, a.triangles);
    const moduleFile = path.join(ROOT, 'node_modules/meshoptimizer/meshopt_simplifier.js');
    assert.equal(sha(fs.readFileSync(moduleFile)), POLICY.simplifierSHA256);
    const { MeshoptSimplifier } = await import(pathToFileURL(moduleFile).href); await MeshoptSimplifier.ready;
    assert(MeshoptSimplifier.supported);
    const immutable = [a.triangles, a.positions, a.normals, a.fields, attributes.attributes];
    const originalHashes = immutable.map(value => sha(bytes(value)));
    for (;;) {
      const iteration = report.candidateAttempts + 1, stem = `iteration-${String(iteration).padStart(3, '0')}`;
      const row = { iteration, status: 'RUNNING_UNACCEPTED', fanProtection: protectFans(a, t, protection) };
      row.protection = writeArrays(path.join(out, `${stem}-protection.bin`), protection);
      report.fixedPoint.iterations.push(row); report.candidateAttempts = iteration;
      report.status = 'FIXED_POINT_ORIGINAL_SOURCE_REDUCTION_RUNNING_UNACCEPTED'; write();
      const locksHash = sha(bytes(t.locks));
      const [indices, approximateError] = MeshoptSimplifier.simplifyWithAttributes(a.triangles, a.positions, 3,
        attributes.attributes, attributes.stride, attributes.weights, t.locks,
        POLICY.targetTriangles * 3, POLICY.targetErrorM, POLICY.flags);
      assert.deepEqual(immutable.map(value => sha(bytes(value))), originalHashes, 'Original source/attributes changed');
      assert.equal(sha(bytes(t.locks)), locksHash, 'Simplifier mutated source locks');
      assert(Number.isFinite(approximateError) && approximateError >= 0);
      row.returnedOriginalIndices = writeArrays(path.join(out, `${stem}-returned-original-indices.bin`), { triangles: indices });
      row.targetTriangles = indices.length / 3; row.approximateCombinedErrorM = approximateError; write();
      const candidate = compactCandidate(a, t, indices);
      row.candidate = writeArrays(path.join(out, `${stem}-candidate.bin`), candidate);
      row.targetVertices = candidate.originalVertexIds.length;
      row.fanRetention = fanRetention(a, indices, protection); write();
      assert(row.fanRetention.passed, 'Previously protected exact source fan changed');
      row.vertexNormalCensus = normalCensus(a, indices);
      assert.equal(row.vertexNormalCensus.verticesExamined, row.targetVertices);
      const face = faceCensus(a, indices, tree); row.faceCentroidCensus = face.report;
      row.faceCentroidArrays = writeArrays(path.join(out, `${stem}-face-centroids.bin`), face.arrays);
      const complete = row.vertexNormalCensus.passed && row.faceCentroidCensus.passed;
      row.status = complete ? 'CPU_VERTEX_AND_FACE_FIXED_POINT_UNACCEPTED' : 'REQUIRES_MORE_SOURCE_FAN_CONSTRAINTS';
      write();
      if (complete) {
        report.fixedPoint.complete = true;
        Object.assign(report, { candidate: row.candidate, returnedOriginalIndices: row.returnedOriginalIndices,
          fanProtection: row.fanProtection, fanRetention: row.fanRetention, finalFanProtection: row.protection,
          targetTriangles: row.targetTriangles, targetVertices: row.targetVertices,
          approximateCombinedErrorM: row.approximateCombinedErrorM, vertexNormalCensus: row.vertexNormalCensus,
          faceCentroidCensus: row.faceCentroidCensus, faceCentroidArrays: row.faceCentroidArrays,
          simplificationTargetTriangles: POLICY.targetTriangles, simplificationTargetReached: row.targetTriangles <= POLICY.targetTriangles,
          sourceInputBytesUnchanged: true, exactOriginalPositionsAndNamedFields: true,
          geometricQualification: 'CPU_VERTEX_AND_FACE_PASSED_NATIVE_GEOMETRY_PENDING',
          nativeFaceAncestryProofRequired: true, nativeFaceAncestryPolicyChanged: false,
          status: 'UNACCEPTED_SCENE_BUDGET_PENDING',
          limits: 'CPU constraint fixed point only. Output may exceed soft target, up to original mesh. Native67 inherited-face proof and independent geometric face/surface/skin/contact, selected atlas/PBR bake, motion and scene allocation remain required.' });
        write(); console.log(JSON.stringify({ status: report.status, iterations: iteration, triangles: row.targetTriangles,
          normalCensusPassed: true, sceneBudgetPassed: false })); return;
      }
      const addition = addFailures(a, protection, row.vertexNormalCensus, row.faceCentroidCensus);
      row.addedOriginalFanCenters = addition.addedCenters;
      row.nextProtectedCenters = addition.next.centerOriginalVertexIds.length; write();
      protection = addition.next;
    }
  } catch (error) {
    report.status = 'REJECTED_FIXED_POINT_CONSTRUCTOR67_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
