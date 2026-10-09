/** Parent-guarded fixed-point fan constraints; immutable original-source reduction. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, POLICY, sha, readCensus, fieldsAndAttributes, topology, compactCandidate, writeArrays }
  from '../selected-production-constructor37/construct.mjs';
import { readProtection, protectFans, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { normalCensus, fanClosure, augment, MINIMUM_NORMAL_DOT } from './closure.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FROZEN37 = path.join(ROOT, 'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs');
const FROZEN37_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741';
const FROZEN59 = path.join(ROOT, 'assets/blender/rider-rebuild/selected-boot-fan59/construct.mjs');
const FROZEN59_SHA = 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f';
const relative = file => path.relative(ROOT, file);
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength);
const writeJSON = (file, value) => fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);

async function main() {
  assert.equal(process.argv.length, 5, 'Usage: node construct.mjs CENSUS35_JSON FAN_CENSUS59_JSON NEW_OUT');
  assert.equal(sha(fs.readFileSync(FROZEN37)), FROZEN37_SHA);
  assert.equal(sha(fs.readFileSync(FROZEN59)), FROZEN59_SHA);
  assert.equal(MINIMUM_NORMAL_DOT, POLICY.minimumNormalDot);
  assert.deepEqual(POLICY.flags, ['ErrorAbsolute']); assert.equal(POLICY.targetErrorM, .001);
  const { a, census, censusPin } = readCensus(process.argv[2]);
  const seed = readProtection(process.argv[3], censusPin,
    { path: census.sourceArrayPackage.path, sha256: census.sourceArrayPackage.sha256 });
  let protection = fanClosure(a, seed.centerOriginalVertexIds);
  for (const key of Object.keys(protection)) assert.deepEqual(protection[key], seed[key], 'Seed source-fan closure changed');
  const out = path.resolve(process.argv[4]), base = path.join(ROOT, 'harness/out/rider-rebuild/selected-boot-closure62');
  const rel = path.relative(base, out); assert(rel && !rel.startsWith('..') && !path.isAbsolute(rel));
  assert(!fs.existsSync(out), 'Never overwrite a closure experiment'); fs.mkdirSync(out, { recursive: true });
  const report = { status: 'FIXED_POINT_INTAKE_UNACCEPTED', acceptedArt: false, candidateAttempts: 0,
    census: censusPin, censusSourcePins: census.sourcePins, sourceArrayPackage: census.sourceArrayPackage,
    constructorAncestry: { path: relative(FROZEN37), sha256: FROZEN37_SHA },
    fanConstructorAncestry: { path: relative(FROZEN59), sha256: FROZEN59_SHA }, initialFanCensus: seed.pin,
    recipeSHA256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
    closureRecipeSHA256: sha(fs.readFileSync(path.join(HERE, 'closure.mjs'))), policy: POLICY,
    groupNames: a.names, sourceVertices: a.positions.length / 3, sourceTriangles: a.triangles.length / 3,
    sceneBudgetPassed: false, allocationPassed: false, simplificationTargetIsSoft: true,
    geometricQualification: 'NOT_RUN', bakeCompleted: false, movingReviewPassed: false, devicePassed: false,
    fixedPoint: { complete: false, minimumNormalDot: MINIMUM_NORMAL_DOT,
      rule: 'Each iteration reduces the same immutable original source with identical attributes/error/flags. Add every failing candidate original fan together; source locks/required fans grow monotonically. Stop at complete CPU normal pass; reject if no new fan can be protected.',
      runtimeBound: 'The parent original external guard bounds the whole invocation; no local retry/time-limit substitute.',
      iterations: [] } };
  const write = () => writeJSON(path.join(out, 'constructor.json'), report); write();
  try {
    const attributes = fieldsAndAttributes(a); report.attributes = attributes.report; report.attributeWeights = attributes.weights;
    assert.equal(attributes.report.rowsNotFloat32Normalized, 0);
    const t = topology(a); report.originalTopology = t.report; write();
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
      row.status = row.vertexNormalCensus.passed ? 'CPU_NORMAL_FIXED_POINT_UNACCEPTED' : 'REQUIRES_MORE_SOURCE_FAN_CONSTRAINTS';
      write();
      if (row.vertexNormalCensus.passed) {
        report.fixedPoint.complete = true;
        Object.assign(report, { candidate: row.candidate, returnedOriginalIndices: row.returnedOriginalIndices,
          fanProtection: row.fanProtection, fanRetention: row.fanRetention, finalFanProtection: row.protection,
          targetTriangles: row.targetTriangles, targetVertices: row.targetVertices,
          approximateCombinedErrorM: row.approximateCombinedErrorM, vertexNormalCensus: row.vertexNormalCensus,
          simplificationTargetTriangles: POLICY.targetTriangles, simplificationTargetReached: row.targetTriangles <= POLICY.targetTriangles,
          sourceInputBytesUnchanged: true, exactOriginalPositionsAndNamedFields: true,
          geometricQualification: 'CPU_VERTEX_NORMAL_PASSED_NATIVE_GEOMETRY_PENDING',
          status: 'UNACCEPTED_SCENE_BUDGET_PENDING',
          limits: 'CPU constraint fixed point only. Output may exceed soft target, up to original mesh. Native geometric face/surface/skin/contact, selected atlas/PBR bake, motion and scene allocation remain required.' });
        write(); console.log(JSON.stringify({ status: report.status, iterations: iteration, triangles: row.targetTriangles,
          normalCensusPassed: true, sceneBudgetPassed: false })); return;
      }
      const addition = augment(a, protection, row.vertexNormalCensus);
      row.addedOriginalFanCenters = addition.addedCenters;
      row.nextProtectedCenters = addition.next.centerOriginalVertexIds.length; write();
      protection = addition.next;
    }
  } catch (error) {
    report.status = 'REJECTED_FIXED_POINT_CONSTRUCTOR62_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
