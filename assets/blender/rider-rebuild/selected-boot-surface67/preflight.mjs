/** Exhaustive comparison to every actual63 native query; no simplifier/Blender. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SourceTree, geometricNormal, faceKey, faceCensus } from './surface.mjs';
import { ROOT, ACTUAL62, FINDING66, REFERENCE, readJSON, arrays, filePin, pinned, actualInput } from './io.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export function preflight(out) {
  const started = performance.now(), { receipt, a, returned } = actualInput();
  const reference = readJSON(REFERENCE); pinned(reference.production); pinned(reference.sourceNPZ); pinned(reference.recipe);
  const z = arrays(reference.arrays); assert.equal(z.sourceFaceId.length, 26528);
  const finding = readJSON(FINDING66), nativeFailed = new Set(finding.failures.map(r => r.targetFaceId));
  assert.equal(nativeFailed.size, 95);
  const report = { status: 'PARTIAL_CPU_PREFLIGHT_BEFORE_TREE_UNACCEPTED', acceptedArt: false,
    constructor: ACTUAL62, nativeReference: REFERENCE, diagnosis66: FINDING66,
    recipes: ['surface.mjs', 'io.mjs', 'preflight.mjs'].map(name => filePin(path.join(HERE, name))),
    sourceArrays: { path: receipt.sourceArrayPackage.path, sha256: receipt.sourceArrayPackage.sha256 },
    sourceTriangles: a.triangles.length / 3, samples: z.sourceFaceId.length, completedSamples: 0,
    disagreements: [], inheritedNativeFailures: [], nativeNewFailuresMissedByCPU: [], cpuAdditionalNewFailures: [],
    exactCPUTies: [], sameFloat32DistanceDifferentFaces: 0, maximumDistanceDeltaM: 0,
    minimumNormalDot: .25, maximumSurfaceErrorM: .001,
    limits: 'CPU comparison only. All actual native failures stay in initial66 constraints; independent native qualification remains required. Float32 BVH arithmetic is not silently treated as equivalent.' };
  fs.mkdirSync(out, { recursive: true });
  const write = () => fs.writeFileSync(path.join(out, 'preflight.json'), `${JSON.stringify(report, null, 2)}\n`);
  write();
  try {
    const tree = new SourceTree(a.positions, a.triangles);
    report.treeBuildSeconds = (performance.now() - started) / 1000; report.treeNodes = tree.nodes.length;
    report.status = 'PARTIAL_CPU_PREFLIGHT_QUERYING_ALL_ACTUAL63_UNACCEPTED'; write();
    let maximumDotDelta = 0, sameFaces = 0, nativeOwnDistanceSmallerCount = 0;
    for (let i = 0; i < z.sourceFaceId.length; i++) {
      const ids = returned.subarray(i * 3, i * 3 + 3), p = Array.from(ids, v => Array.from(a.positions.subarray(3 * v, 3 * v + 3)));
      const query = [0, 1, 2].map(j => Math.fround((p[0][j] + p[1][j] + p[2][j]) / 3)), normal = geometricNormal(...p);
      const near = tree.nearest(query), nativeId = z.sourceFaceId[i], exact = tree.ancestry.get(faceKey(...ids));
      const product = face => normal.reduce((sum, v, j) => sum + v * tree.normals[3 * face + j], 0);
      const normalDot = product(near.sourceFaceId), allBearingDot = Math.min(...near.bearingSourceFaceIds.map(product)), recordedBearingDot = product(nativeId);
      maximumDotDelta = Math.max(maximumDotDelta, Math.abs(Math.fround(recordedBearingDot) - z.normalDot[i]));
      const delta = near.distanceM - z.distanceM[i]; report.maximumDistanceDeltaM = Math.max(report.maximumDistanceDeltaM, Math.abs(delta));
      if (near.exactTieFaces.length > 1) report.exactCPUTies.push({ targetFaceId: i, faces: near.exactTieFaces });
      if (near.sourceFaceId !== nativeId) {
        const nativeAtQuery = tree.closestFace(query, nativeId), nativeDistance64 = Math.sqrt(nativeAtQuery.distanceSq);
        if (nativeDistance64 < near.distanceM) nativeOwnDistanceSmallerCount++;
        const sameFloat32Distance = Math.fround(near.distanceM) === z.distanceM[i];
        if (sameFloat32Distance) report.sameFloat32DistanceDifferentFaces++;
        report.disagreements.push({ targetFaceId: i, exactInheritedSourceFaceId: exact ?? null,
          nativeSourceFaceId: nativeId, cpuSourceFaceId: near.sourceFaceId,
          nativeDistanceM: z.distanceM[i], cpuDistanceM: near.distanceM, nativeBearingDistanceCPU: nativeDistance64,
          nativeDot: z.normalDot[i], cpuDot: normalDot, minimumDotAllGeometricBearings: allBearingDot,
          cpuBearingSourceFaceIds: near.bearingSourceFaceIds, sameFloat32Distance,
          cause: near.exactTieFaces.length > 1 ? 'EXACT_CPU_DISTANCE_TIE' : 'FLOAT32_NATIVE_AND_FLOAT64_CPU_NEAREST_DIFFER',
          nativeFailed: nativeFailed.has(i), cpuFailed: allBearingDot < .25 || near.distanceM > .001 });
      } else sameFaces++;
      const cpuFailure = allBearingDot < .25 || near.distanceM > .001;
      if (exact === undefined) {
        if (nativeFailed.has(i) && !cpuFailure) report.nativeNewFailuresMissedByCPU.push(i);
        if (!nativeFailed.has(i) && cpuFailure) report.cpuAdditionalNewFailures.push(i);
      } else if (nativeFailed.has(i)) report.inheritedNativeFailures.push({ targetFaceId: i, exactSourceFaceId: exact, nativeSourceFaceId: nativeId });
      report.completedSamples = i + 1;
      if ((i + 1) % 2048 === 0) write();
    }
    assert.equal(nativeOwnDistanceSmallerCount, 0, 'BVH pruning skipped a closer recorded bearing');
    assert.equal(maximumDotDelta, 0, 'Source/target arithmetic does not reproduce native recorded dots');
    assert.deepEqual(report.inheritedNativeFailures, [{ targetFaceId: 15560, exactSourceFaceId: 278671, nativeSourceFaceId: 278672 }]);
    report.sameSourceFaces = sameFaces; report.maximumRecordedBearingDotDelta = maximumDotDelta;
    report.nativeBearingCloserThanCPUCount = nativeOwnDistanceSmallerCount;
    const full = faceCensus(a, returned, tree); report.actual62ProperFaceCensus = full.report;
    report.status = 'COMPLETE_CPU_NATIVE_COMPARISON_UNACCEPTED'; report.elapsedSeconds = (performance.now() - started) / 1000;
    report.validationPassed = report.completedSamples === report.samples;
    report.constructingCandidateOrChangingNativePolicy = false; write();
    return report;
  } catch (error) { report.status = 'REJECTED_CPU_NATIVE_COMPARISON_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error; }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  assert.equal(process.argv.length, 3, 'Usage: node preflight.mjs OWNED_EVIDENCE_OUTPUT');
  const out = path.resolve(process.argv[2]), base = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-boot-surface67');
  assert(out === base, 'Preflight writes only owned67 evidence');
  const r = preflight(out);
  console.log(JSON.stringify({ status: r.status, samples: r.completedSamples, sameFaces: r.sameSourceFaces,
    differentFaces: r.disagreements.length, missedNativeNewFailures: r.nativeNewFailuresMissedByCPU,
    additionalCPUFailures: r.cpuAdditionalNewFailures, elapsedSeconds: r.elapsedSeconds }));
}
