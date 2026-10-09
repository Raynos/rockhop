/** One read-only classification of the saved03 failures; no tree build or solve. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ROOT, pinned, sha } from '../selected-production-constructor37/construct.mjs';
import { faceKey, geometricNormal, closestTriangle } from '../selected-boot-surface67/surface.mjs';
import { normalCensus } from '../selected-boot-closure62/closure.mjs';

const start = performance.now();
const pin = p => ({ path: path.relative(ROOT, p), sha256: sha(fs.readFileSync(p)) });
const receipt = { path: 'harness/out/rider-rebuild/selected-glove-family81/right-full03/constructor.json',
  sha256: 'f3af0e5965215f1d12672a960aed7616da2170964724357946adb8f87611cf65' };
const helpers = [
  ['selected-production-constructor37/construct.mjs', '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'],
  ['selected-boot-surface67/surface.mjs', '4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'],
  ['selected-boot-closure62/closure.mjs', '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'],
].map(([p, h]) => ({ path: 'assets/blender/rider-rebuild/'+p, sha256: h }));
for (const helper of helpers) pinned(helper);
const r = JSON.parse(pinned(receipt).data), m = JSON.parse(pinned(r.prepared).data);
assert.equal(r.candidateAttempts, 1); assert.equal(r.status, 'REJECTED_SINGLE_ACTUAL41_CANDIDATE');
function arrays(pkg) {
  const { data } = pinned(pkg), result = {};
  for (const [name, row] of Object.entries(pkg.layout)) {
    const C = row.dtype === '<f4' ? Float32Array : row.dtype === '<i4' ? Int32Array : Uint32Array;
    const count = row.count ?? row.shape.reduce((x, y) => x*y, 1);
    result[name] = new C(data.buffer, data.byteOffset+row.byteOffset, count);
  }
  return result;
}
const s = arrays(m.arrays), c = arrays(r.candidate), names = m.groupNames;
const a = { positions: s.positions, triangles: s.triangles, normals: s.vertexNormals };
const sourceTri = id => Array.from(s.triangles.subarray(3*id, 3*id+3));
const targetTri = id => Array.from(c.triangles.subarray(3*id, 3*id+3), v => c.originalVertexIds[v]);
const point = v => Array.from(s.positions.subarray(3*v, 3*v+3));
const dot = (u, v) => u.reduce((sum, value, j) => sum+value*v[j], 0);
const normal = ids => geometricNormal(...ids.map(point));
const neededVertices = new Set(r.faceCensus67.failures.flatMap(f => f.originalVertexIds));
const failedVertices = new Set(r.vertexNormalCensus.failures.map(f => f.originalVertexId));
for (const v of failedVertices) neededVertices.add(v);
const sourceIncident = new Map([...neededVertices].map(v => [v, []]));
const targetIncident = new Map([...failedVertices].map(v => [v, []]));
const targetKeys = new Map(), exact = new Map(), reversed = new Map();
const targetFaces = Array.from({ length: r.targetTriangles }, (_, i) => targetTri(i));
let zeroAreaFaces = 0;
targetFaces.forEach((ids, i) => {
  const key = faceKey(...ids); if (!targetKeys.has(key)) targetKeys.set(key, []); targetKeys.get(key).push(i);
  for (const v of ids) if (targetIncident.has(v)) targetIncident.get(v).push(i);
  try { normal(ids); } catch { zeroAreaFaces++; }
});
for (let f = 0; f < s.triangles.length/3; f++) {
  const ids = sourceTri(f), key = faceKey(...ids), rev = faceKey(ids[0], ids[2], ids[1]);
  if (targetKeys.has(key)) { assert(!exact.has(key)); exact.set(key, f); }
  if (targetKeys.has(rev)) { assert(!reversed.has(rev)); reversed.set(rev, f); }
  for (const v of ids) if (sourceIncident.has(v)) sourceIncident.get(v).push(f);
}
const sourceFans = [...new Set([...failedVertices].flatMap(v => sourceIncident.get(v)))].sort((x,y) => x-y);
const sourceCensus = normalCensus(a, Uint32Array.from(sourceFans.flatMap(sourceTri)));
const sourceFailed = new Map(sourceCensus.failures.filter(f => failedVertices.has(f.originalVertexId)).map(f => [f.originalVertexId, f]));
const faceRows = r.faceCensus67.failures.map(f => {
  const ids = targetFaces[f.targetFaceId], key = faceKey(...ids), n = normal(ids);
  assert.deepEqual(ids, f.originalVertexIds);
  const own = exact.get(key), reverse = reversed.get(key);
  const query = [0,1,2].map(j => Math.fround(ids.reduce((sum,v) => sum+s.positions[3*v+j], 0)/3));
  const incident = [...new Set(ids.flatMap(v => sourceIncident.get(v)))];
  let best = Infinity, localFaces = [];
  for (const id of incident) {
    const distance = closestTriangle(query, ...sourceTri(id).map(point)).distanceSq;
    if (distance < best) { best = distance; localFaces = [id]; } else if (distance === best) localFaces.push(id);
  }
  // Local geometric bearings are selected by distance only; never choose the best normal.
  const localDot = Math.min(...localFaces.map(id => dot(n, normal(sourceTri(id)))));
  const globalShared = f.bearingSourceFaceIds.some(id => sourceTri(id).some(v => ids.includes(v)));
  const reverseTarget = targetKeys.get(faceKey(ids[0], ids[2], ids[1])) || [];
  const weights = names.map((_, j) => ids.reduce((sum,v) => sum+s.namedWeights[v*names.length+j], 0)/3);
  return { ...f, exactOrientedOwnSourceFaceId: own ?? null, exactReversedSourceFaceId: reverse ?? null,
    ownSourceNormalDot: own === undefined ? null : dot(n, normal(sourceTri(own))),
    reversedSourceNormalDot: reverse === undefined ? null : dot(n, normal(sourceTri(reverse))),
    oppositeDuplicateTargetFaceIds: reverseTarget,
    nearestBearingSharesOriginalVertex: globalShared,
    closestIncidentSourceFaceIds: localFaces, closestIncidentDistanceM: Math.sqrt(best), closestIncidentNormalDot: localDot,
    strongestMeanNamedField: names[weights.indexOf(Math.max(...weights))],
    classification: own !== undefined ? 'EXACT_ORIENTED_SOURCE_FACE' : reverse !== undefined ? 'EXACT_SOURCE_TRIANGLE_REVERSED'
      : !globalShared && localDot >= .25 ? 'DISJOINT_NEAREST_BEARING_WITH_ALIGNED_INCIDENT_REFERENCE_UNPROVEN_WALL_MISMATCH'
      : localDot < 0 ? 'NEW_FACE_OPPOSES_CLOSEST_INCIDENT_SOURCE_REFERENCE' : 'NEW_FACE_NORMAL_FAILURE_UNRESOLVED' };
});
const vertexRows = r.vertexNormalCensus.failures.map(f => {
  const id = f.originalVertexId, sourceIds = sourceIncident.get(id), targetIds = targetIncident.get(id);
  const original = new Set(sourceIds.map(i => faceKey(...sourceTri(i))));
  const selected = new Set(targetIds.map(i => faceKey(...targetFaces[i])));
  const fanExact = sourceIds.length === targetIds.length && original.size === selected.size && [...original].every(k => selected.has(k));
  return { ...f, completeOrientedSourceFanExact: fanExact,
    sourceFanFaces: sourceIds, targetFanFaces: targetIds,
    sourceOwnFanNormalCheck: sourceFailed.get(id) || { passed: true, normalDotAtLeast: .25 },
    inheritedOrientedTargetFaces: targetIds.filter(i => exact.has(faceKey(...targetFaces[i]))),
    exactReversedSourceTargetFaces: targetIds.filter(i => reversed.has(faceKey(...targetFaces[i]))),
    oppositeDuplicateTargetFaces: targetIds.filter(i => { const t=targetFaces[i]; return targetKeys.has(faceKey(t[0],t[2],t[1])); }),
    classification: fanExact ? 'UNCHANGED_FULL_SOURCE_FAN_RAW_NORMAL_FAILURE'
      : f.normalDot === null ? 'CHANGED_FAN_UNDEFINED_GEOMETRIC_NORMAL'
      : sourceFailed.has(id) ? 'CHANGED_FAN_WITH_PREEXISTING_SOURCE_NORMAL_FAILURE' : 'NEW_CHANGED_FAN_NORMAL_FAILURE' };
});
const histogram = (rows, key) => Object.fromEntries([...new Set(rows.map(r => r[key]))].sort().map(k => [k, rows.filter(r => r[key] === k).length]));
const report = { status: 'SAVED_RFULL03_FAILURE_CLASSIFICATION_UNACCEPTED', acceptedArt: false,
  recipe: pin(fileURLToPath(import.meta.url)), helpers, constructor: receipt, prepared: r.prepared, candidate: r.candidate,
  faceClassifications: histogram(faceRows, 'classification'), vertexClassifications: histogram(vertexRows, 'classification'),
  strongestFaceFieldHistogram: histogram(faceRows, 'strongestMeanNamedField'),
  targetZeroAreaFaces: zeroAreaFaces, exactInheritedOrientedFacesAll: exact.size,
  sourceNormalFailureAmong133Centers: sourceFailed.size,
  verifiedOwnAncestryThinSheetWaivers: 0, gateChanged: false, candidateAccepted: false,
  faces: faceRows, vertices: vertexRows, candidateAttemptsAdded: 0, nativeMutation: false,
  elapsedSeconds: (performance.now()-start)/1000,
  limits: 'Source67 oriented ancestry and geometric closest-point functions, with source62 complete vertex fans. A disjoint nearest wall and aligned incident reference are diagnostic evidence only: no own patch identity, thin-sheet waiver, full reverse surface or native qualification is claimed. Existing result stays rejected.' };
const output = path.join(ROOT, 'docs/evidence/rider-rebuild/selected-glove-family81/right-full-guard03/failure-classification.json');
fs.writeFileSync(output, JSON.stringify(report, null, 2)+'\n', { flag: 'wx' });
console.log(JSON.stringify({ ...Object.fromEntries(Object.entries(report).filter(([k]) =>
  ['status','faceClassifications','vertexClassifications','strongestFaceFieldHistogram','targetZeroAreaFaces',
   'exactInheritedOrientedFacesAll','sourceNormalFailureAmong133Centers','elapsedSeconds'].includes(k))), output: pin(output) }, null, 2));
