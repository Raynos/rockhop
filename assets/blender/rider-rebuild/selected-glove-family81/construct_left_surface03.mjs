/** LEFT singular-fan gates with the independently measured surface02 intake. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, sha, pinned, topology, compactCandidate, writeArrays } from '../selected-production-constructor37/construct.mjs';
import { protectFans, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { fanClosure, normalCensus } from '../selected-boot-closure62/closure.mjs';
import { SourceTree, faceCensus, faceKey, geometricNormal } from '../selected-boot-surface67/surface.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const IMPORTS = [
  ['selected-production-constructor37/construct.mjs', '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'],
  ['selected-boot-fan59/construct.mjs', 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'],
  ['selected-boot-closure62/closure.mjs', '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'],
  ['selected-boot-surface67/surface.mjs', '4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'],
];
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength);
const pin = file => ({ path: path.relative(ROOT, file), sha256: sha(fs.readFileSync(file)) });
const UNDEFINED_VERTEX = 320543, UNDEFINED_FACES = [518306, 518310, 561015, 561016, 561020];

function undefinedFan(a) {
  assert([...a.normals.subarray(3 * UNDEFINED_VERTEX, 3 * UNDEFINED_VERTEX + 3)].every(v => v === 0));
  const protection = fanClosure(a, [UNDEFINED_VERTEX]);
  assert.deepEqual([...protection.requiredSourceFaceIds], UNDEFINED_FACES, 'Known source fan changed');
  for (const face of UNDEFINED_FACES) {
    const ids = a.triangles.subarray(3 * face, 3 * face + 3), corner = ids.indexOf(UNDEFINED_VERTEX);
    const loop = a.loopIds[3 * face + corner];
    assert([...a.cornerNormals.subarray(3 * loop, 3 * loop + 3)].every(v => v === 0));
    geometricNormal(...Array.from(ids, id => Array.from(a.positions.subarray(3 * id, 3 * id + 3))));
  }
  return protection;
}

function classifyUndefined(a, indices, raw, protection) {
  const retained = fanRetention(a, indices, protection); assert(retained.passed);
  const source = new Map(UNDEFINED_FACES.map(face => [faceKey(...a.triangles.subarray(3 * face, 3 * face + 3)), face]));
  const normals = ids => geometricNormal(...Array.from(ids, id => Array.from(a.positions.subarray(3 * id, 3 * id + 3))));
  const faces = [];
  for (let i = 0; i < indices.length; i += 3) {
    const ids = indices.subarray(i, i + 3); if (!ids.includes(UNDEFINED_VERTEX)) continue;
    const sourceId = source.get(faceKey(...ids)); assert(sourceId !== undefined);
    const targetNormal = normals(ids), sourceNormal = normals(a.triangles.subarray(3 * sourceId, 3 * sourceId + 3));
    const dot = targetNormal.reduce((sum, value, j) => sum + value * sourceNormal[j], 0);
    assert(dot >= 1-1e-12, 'Exact source fan geometric orientation changed');
    faces.push({ targetFaceId: i / 3, sourceFaceId: sourceId, positiveAreaGeometricOrientationDot: dot });
  }
  assert.equal(faces.length, 5);
  const classified = raw.failures.filter(row => row.originalVertexId === UNDEFINED_VERTEX);
  const remaining = raw.failures.filter(row => row.originalVertexId !== UNDEFINED_VERTEX);
  assert.equal(classified.length, 1, 'Raw62 source-singular failure must remain present');
  return { originalVertexId: UNDEFINED_VERTEX, rawClassifiedFailure: classified[0], raw62ResultPreserved: true,
    exactSourceFanRetention: retained, geometricFaceOrientation: faces, remainingFailures: remaining,
    passed: remaining.length === 0,
    meaning: 'Only undefined source-average comparison classified by exact oriented ancestry. Raw62 remains failed; final target requires explicit nonzero hard-normal seam. No glove fit or source-fold acceptance.' };
}

function attributes(a, used, policy) {
  // Same37 normal/full varying-field metric, accepting actual75 socket names.
  // Orphaned removed-cap vertices never enter a face or output candidate.
  const n = used.length, k = a.names.length, low = Array(k).fill(Infinity), high = Array(k).fill(-Infinity);
  let sumLow = Infinity, sumHigh = -Infinity, unbound = 0, notNormalized = 0;
  for (let v = 0; v < n; v++) if (used[v]) {
    const normalLength = Math.hypot(...a.normals.subarray(3 * v, 3 * v + 3));
    assert(normalLength > 0 || v === UNDEFINED_VERTEX, `Unexpected zero referenced source normal ${v}`);
    let sum = 0;
    for (let j = 0; j < k; j++) {
      const w = a.fields[k * v + j]; assert(Number.isFinite(w) && w >= 0 && w <= 1);
      low[j] = Math.min(low[j], w); high[j] = Math.max(high[j], w); sum += w;
    }
    sumLow = Math.min(sumLow, sum); sumHigh = Math.max(sumHigh, sum);
    if (sum === 0) unbound++; if (Math.fround(sum) !== 1) notNormalized++;
  }
  const varying = a.names.map((_, j) => j).filter(j => low[j] !== high[j]);
  assert(varying.length + 3 <= 32, 'Actual complete fields exceed attribute channel limit; never prune');
  assert.equal(unbound, 0, 'Unbound source row');
  // Stored float32 component sums are reported; raw fields and raw priorities remain exact.
  const stride = 3 + varying.length, values = new Float32Array(n * stride);
  for (let v = 0; v < n; v++) if (used[v]) {
    const length = Math.hypot(...a.normals.subarray(3 * v, 3 * v + 3));
    if (length > 0) for (let j = 0; j < 3; j++) values[stride * v + j] = a.normals[3 * v + j] / length;
    else assert.equal(v, UNDEFINED_VERTEX, 'Only the exact locked source-singular normal metric may be undefined');
    for (let j = 0; j < varying.length; j++) values[stride * v + 3 + j] = a.fields[k * v + varying[j]];
  }
  const nw = 1 / Math.sqrt(2 * (1 - policy.minimumNormalDot)), fw = Math.sqrt(varying.length) / policy.maximumSkinWeightL1;
  return { values, stride, weights: [nw, nw, nw, ...varying.map(() => fw)],
    report: { names: ['normal.x', 'normal.y', 'normal.z', ...varying.map(j => a.names[j])],
      allOutputFieldNames: a.names, sourceRawSumRange: [sumLow, sumHigh], referencedUnboundRows: unbound,
      sourceFloat32NotExactlyOne: notNormalized, priorityOnly: true,
      undefinedSourceNormalMetric: { originalVertexId: UNDEFINED_VERTEX, values: [0, 0, 0],
        reason: 'Explicitly undefined priority at the immutable complete source fan; not a generated or normalized shading normal.' },
      policy: 'Defined normal metric channels unitized. The one exact retained singular fan has no normal priority; all fields retained exactly. Raw62 failure and required native seam stay explicit.' } };
}

async function main() {
  assert(process.env.ROCKHOP_GENERATION_CONTROLLER_PID, 'Original parent guard required');
  assert.equal(process.argv.length, 3);
  for (const [file, expected] of IMPORTS) assert.equal(pin(path.join(HERE, '..', file)).sha256, expected);
  const file = path.resolve(process.argv[2]), out = path.dirname(file), m = JSON.parse(fs.readFileSync(file));
  assert(out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-glove-family81') + path.sep));
  assert.equal(m.status, 'ACTUAL41_LEFT_SURFACE_SINGULAR_FAN_PREPARED_UNACCEPTED'); assert.equal(m.acceptedArt, false);
  assert.equal(m.sourceObject, 'ActualSelectedGlove.L'); assert.equal(m.side, 'L');
  assert.equal(m.recipe.sha256, pin(path.join(HERE, 'construct_left_surface03.py')).sha256);
  pinned(m.sourceSurfaceLandmarks); pinned(m.sourceSelectorRecipe);
  assert.equal(m.semanticRecipe.sha256, '1a821b543685ade57d1d9deb8862afa3f40e86d03ca6ede6644b3f341278bc1c'); pinned(m.semanticRecipe);
  assert.equal(m.nativeSeamRecipe.sha256, pin(path.join(HERE, 'left_normals.py')).sha256);
  const { data } = pinned(m.arrays), arrays = {}; let end = 0;
  for (const [name, row] of Object.entries(m.arrays.layout)) {
    assert.equal(row.byteOffset, end); assert(['<i4', '<u4', '<f4'].includes(row.dtype));
    const count = row.shape.reduce((x, y) => x * y, 1); assert.equal(row.byteLength, count * 4);
    const C = row.dtype === '<f4' ? Float32Array : row.dtype === '<i4' ? Int32Array : Uint32Array;
    arrays[name] = new C(data.buffer, data.byteOffset + end, count); assert.equal(sha(bytes(arrays[name])), row.sha256);
    end += row.byteLength;
  }
  assert.equal(end, data.length);
  const a = { positions: arrays.positions, triangles: Uint32Array.from(arrays.triangles), loopIds: arrays.triangleLoopIds,
    normals: arrays.vertexNormals, cornerNormals: arrays.cornerNormals, fields: arrays.namedWeights,
    materials: arrays.faceMaterialIds, names: m.groupNames, uv: m.uvLayerNames.map((name, i) => ({ name, values: arrays['uvLayer'+i] })) };
  const report = { status: 'ACTUAL41_SINGLE_CANDIDATE_INTAKE_UNACCEPTED', acceptedArt: false, recipe: pin(fileURLToPath(import.meta.url)),
    prepared: pin(file), sourceReceipt: m.sourceReceipt, sourceNative: m.native, sourceObject: m.sourceObject,
    sourceGeometry: m.sourceGeometry, originalSourceArrays: m.sourceArrays, cpuAdmission: m.cpuAdmission,
    policy: m.policy, groupNames: a.names, candidateAttempts: 0, semanticSourceFans: m.semanticSourceFans,
    sourceSurfaceLandmarks: m.sourceSurfaceLandmarks, sourceSelectorRecipe: m.sourceSelectorRecipe,
    undefinedSourceNormalFan: m.undefinedSourceNormalFan,
    requiredNativeSeam: { recipe: m.nativeSeamRecipe, applied: false, instruction: m.requiredNativeShading },
    denseGeometryPassed: false, selectedBakePassed: false, movingReviewPassed: false, devicePassed: false };
  const reportFile = path.join(out, 'constructor.json'); assert(!fs.existsSync(reportFile), 'Never retry or overwrite');
  const write = () => fs.writeFileSync(reportFile, JSON.stringify(report, null, 2)+'\n'); write();
  try {
    const used = new Uint8Array(a.positions.length / 3); for (const v of a.triangles) used[v] = 1;
    const singularProtection = undefinedFan(a);
    assert(arrays.centerOriginalVertexIds.includes(UNDEFINED_VERTEX));
    const t = topology(a); report.originalTopology = t.report;
    const protection = fanClosure(a, arrays.centerOriginalVertexIds);
    report.fanProtection = protectFans(a, t, protection);
    assert.equal(t.locks[UNDEFINED_VERTEX], 1);
    const metric = attributes(a, used, m.policy); report.attributeMetric = metric.report;
    report.protection = writeArrays(path.join(out, 'protected-fans.bin'), protection); write();
    assert(protection.requiredSourceFaceIds.length <= m.policy.targetTriangles, 'Exact anatomical fans alone exceed allocation');
    assert(Math.ceil(report.fanProtection.totalLockedVertices / 3) <= m.policy.targetTriangles, 'Locked source vertices exceed allocation');
    const moduleFile = path.join(ROOT, 'node_modules/meshoptimizer/meshopt_simplifier.js');
    assert.equal(pin(moduleFile).sha256, 'd2e80c60a84c700947f97ab4678cc222a5b9ab409a0745eef2dcaa79bb1ef922');
    const { MeshoptSimplifier } = await import(pathToFileURL(moduleFile).href); await MeshoptSimplifier.ready;
    assert(MeshoptSimplifier.supported);
    const originals = [a.positions, a.triangles, a.normals, a.fields, metric.values, t.locks];
    const hashes = originals.map(value => sha(bytes(value)));
    report.status = 'ONE_ACTUAL41_SIDE_REDUCTION_RUNNING_UNACCEPTED'; report.candidateAttempts = 1; write();
    const [indices, approximateError] = MeshoptSimplifier.simplifyWithAttributes(a.triangles, a.positions, 3,
      metric.values, metric.stride, metric.weights, t.locks, m.policy.targetTriangles * 3, m.policy.maximumSurfaceErrorM, ['ErrorAbsolute']);
    assert.deepEqual(originals.map(value => sha(bytes(value))), hashes, 'Immutable source or constraints changed');
    assert(Number.isFinite(approximateError) && approximateError >= 0);
    report.returnedOriginalIndices = writeArrays(path.join(out, 'returned-original-indices.bin'), { triangles: indices });
    const candidate = compactCandidate(a, t, indices), offsets = [0], groups = [], weights = [];
    for (const id of candidate.originalVertexIds) {
      const begin = arrays.fieldOffsets[id], end = arrays.fieldOffsets[id + 1];
      for (let i = begin; i < end; i++) { groups.push(arrays.fieldIndices[i]); weights.push(arrays.fieldWeights[i]); }
      offsets.push(groups.length);
    }
    Object.assign(candidate, { fieldOffsets: Uint32Array.from(offsets), fieldIndices: Int32Array.from(groups), fieldWeights: Float32Array.from(weights) });
    report.candidate = writeArrays(path.join(out, 'candidate.bin'), candidate);
    report.targetVertices = candidate.originalVertexIds.length; report.targetTriangles = indices.length / 3;
    report.allocationPassed = report.targetTriangles <= m.policy.targetTriangles; report.approximateCombinedErrorM = approximateError;
    report.fanRetention = fanRetention(a, indices, protection); assert(report.fanRetention.passed, 'Protected source fan changed');
    report.sourceBytesUnchanged = true; report.exactOriginalPositionsAndCompleteNamedFields = true; write();
    report.vertexNormalCensus = normalCensus(a, indices); write();
    report.undefinedSourceNormalClassification = classifyUndefined(a, indices, report.vertexNormalCensus, singularProtection); write();
    const census = faceCensus(a, indices, new SourceTree(a.positions, a.triangles));
    report.faceCensus67 = census.report;
    report.faceSamples = writeArrays(path.join(out, 'face-samples.bin'), census.arrays);
    report.stricterGloveFaceSurfacePassed = census.report.maximumDistanceM <= m.policy.maximumSurfaceErrorM;
    report.cpuOrientationAndFaceSurfacePassed = report.undefinedSourceNormalClassification.passed && census.report.passed && report.stricterGloveFaceSurfacePassed;
    report.status = report.allocationPassed && report.cpuOrientationAndFaceSurfacePassed
      ? 'UNACCEPTED_ACTUAL41_CANDIDATE_NATIVE_BIDIRECTIONAL_CHECK_REQUIRED' : 'REJECTED_SINGLE_ACTUAL41_CANDIDATE';
    report.limits = 'One LEFT source-only attempt. Raw62 undefined-normal failure remains recorded. Exactly L320543 uses retained five-face geometric ancestry; every other normal/0.5mm condition stays unchanged. Native target must apply the explicit five-corner hard-normal seam before shading/export admission. Full native reverse surface, skin/body/self-contact, source-fold wearability, selected bake, motion and art remain open. No palette pruning or copied target UVs.';
    write(); console.log(JSON.stringify({ status: report.status, triangles: report.targetTriangles, allocationPassed: report.allocationPassed }));
    if (report.status.startsWith('REJECTED')) process.exitCode = 2;
  } catch (error) { report.status = 'REJECTED_SINGLE_ACTUAL41_CONSTRUCTION'; report.failure = String(error.stack || error); write(); throw error; }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
