/** One anatomical-fan constrained actual41 side; no reduction loop or retry. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ROOT, sha, pinned, topology, compactCandidate, writeArrays } from '../selected-production-constructor37/construct.mjs';
import { protectFans, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { fanClosure, normalCensus } from '../selected-boot-closure62/closure.mjs';
import { SourceTree, faceCensus } from '../selected-boot-surface67/surface.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const IMPORTS = [
  ['selected-production-constructor37/construct.mjs', '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'],
  ['selected-boot-fan59/construct.mjs', 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'],
  ['selected-boot-closure62/closure.mjs', '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'],
  ['selected-boot-surface67/surface.mjs', '4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'],
];
const bytes = value => Buffer.from(value.buffer, value.byteOffset, value.byteLength);
const pin = file => ({ path: path.relative(ROOT, file), sha256: sha(fs.readFileSync(file)) });

function attributes(a, used, policy) {
  // Same37 normal/full varying-field metric, accepting actual75 socket names.
  // Orphaned removed-cap vertices never enter a face or output candidate.
  const n = used.length, k = a.names.length, low = Array(k).fill(Infinity), high = Array(k).fill(-Infinity);
  let sumLow = Infinity, sumHigh = -Infinity, unbound = 0, notNormalized = 0;
  for (let v = 0; v < n; v++) if (used[v]) {
    assert(Math.hypot(...a.normals.subarray(3 * v, 3 * v + 3)) > 0, `Zero referenced source normal ${v}`);
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
  assert.equal(unbound, 0, 'Unbound source row'); assert.equal(notNormalized, 0, 'Source row sum differs from1; never normalize');
  const stride = 3 + varying.length, values = new Float32Array(n * stride);
  for (let v = 0; v < n; v++) if (used[v]) {
    const length = Math.hypot(...a.normals.subarray(3 * v, 3 * v + 3));
    for (let j = 0; j < 3; j++) values[stride * v + j] = a.normals[3 * v + j] / length;
    for (let j = 0; j < varying.length; j++) values[stride * v + 3 + j] = a.fields[k * v + varying[j]];
  }
  const nw = 1 / Math.sqrt(2 * (1 - policy.minimumNormalDot)), fw = Math.sqrt(varying.length) / policy.maximumSkinWeightL1;
  return { values, stride, weights: [nw, nw, nw, ...varying.map(() => fw)],
    report: { names: ['normal.x', 'normal.y', 'normal.z', ...varying.map(j => a.names[j])],
      allOutputFieldNames: a.names, sourceRowSumRange: [sumLow, sumHigh], referencedUnboundRows: unbound,
      sourceRowsNotFloat32Normalized: notNormalized, priorityOnly: true,
      policy: 'Only normal metric channels unitized. Constant fields omitted from metric, retained exactly in full output and original CSR.' } };
}

async function main() {
  assert(process.env.ROCKHOP_GENERATION_CONTROLLER_PID, 'Original parent guard required');
  assert.equal(process.argv.length, 3);
  for (const [file, expected] of IMPORTS) assert.equal(pin(path.join(HERE, '..', file)).sha256, expected);
  const file = path.resolve(process.argv[2]), out = path.dirname(file), m = JSON.parse(fs.readFileSync(file));
  assert(out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-glove-family81') + path.sep));
  assert.equal(m.status, 'ACTUAL41_ANATOMICAL_FANS_PREPARED_UNACCEPTED'); assert.equal(m.acceptedArt, false);
  assert.equal(m.recipe.sha256, pin(path.join(HERE, 'construct.py')).sha256);
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
    denseGeometryPassed: false, selectedBakePassed: false, movingReviewPassed: false, devicePassed: false };
  const reportFile = path.join(out, 'constructor.json'); assert(!fs.existsSync(reportFile), 'Never retry or overwrite');
  const write = () => fs.writeFileSync(reportFile, JSON.stringify(report, null, 2)+'\n'); write();
  try {
    const used = new Uint8Array(a.positions.length / 3); for (const v of a.triangles) used[v] = 1;
    const metric = attributes(a, used, m.policy); report.attributeMetric = metric.report;
    const t = topology(a); report.originalTopology = t.report;
    const protection = fanClosure(a, arrays.centerOriginalVertexIds);
    report.fanProtection = protectFans(a, t, protection);
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
    const census = faceCensus(a, indices, new SourceTree(a.positions, a.triangles));
    report.faceCensus67 = census.report;
    report.faceSamples = writeArrays(path.join(out, 'face-samples.bin'), census.arrays);
    report.stricterGloveFaceSurfacePassed = census.report.maximumDistanceM <= m.policy.maximumSurfaceErrorM;
    report.cpuOrientationAndFaceSurfacePassed = report.vertexNormalCensus.passed && census.report.passed && report.stricterGloveFaceSurfacePassed;
    report.status = report.allocationPassed && report.cpuOrientationAndFaceSurfacePassed
      ? 'UNACCEPTED_ACTUAL41_CANDIDATE_NATIVE_BIDIRECTIONAL_CHECK_REQUIRED' : 'REJECTED_SINGLE_ACTUAL41_CANDIDATE';
    report.limits = 'One source-only attempt. Target-face/vertex CPU checks do not qualify full reverse surface, skin deformation, self-contact, wearer clearance or art. Native70-style full bidirectional0.5mm/normal/skin proof must precede25 bilateral unwrap and32 original selected-PBR bake. No four-weight palette pruning or copied target UVs.';
    write(); console.log(JSON.stringify({ status: report.status, triangles: report.targetTriangles, allocationPassed: report.allocationPassed }));
    if (report.status.startsWith('REJECTED')) process.exitCode = 2;
  } catch (error) { report.status = 'REJECTED_SINGLE_ACTUAL41_CONSTRUCTION'; report.failure = String(error.stack || error); write(); throw error; }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
