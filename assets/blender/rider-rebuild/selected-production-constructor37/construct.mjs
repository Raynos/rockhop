/** One parent-guarded index-only selected boot candidate; never a sweep. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '../../../..');
export const POLICY = Object.freeze({
  sourceObject: 'ActualSelectedBoot.L', sourceTriangles: 610934, targetTriangles: 8000,
  targetErrorM: 0.001, minimumNormalDot: 0.25, maximumSkinWeightL1: 0.3,
  flags: ['ErrorAbsolute'], appearance: 'fresh-target-atlas-from-immutable-selected-donor',
  censusRecipeSHA256: 'b570c6bb9a79e734cf0aa9381523d53c2436eef279bfe1c746fd3b3aa85bbb76',
  censusInputSHA256: '8b1e26da8faa9781de787c741a74083bfe778d8552076a094863b5ad5a28f8c8',
  nativeSHA256: 'a155d13f9b4df422bf851f847c7d392fbd3451c5d20c675093e8913bd05138ad',
  simplifierSHA256: 'd2e80c60a84c700947f97ab4678cc222a5b9ab409a0745eef2dcaa79bb1ef922',
});
const STAGES = ['target-vertices', 'target-face-centroids', 'target-edge-midpoints', 'source-vertices', 'source-face-centroids'];
export const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const bytes = a => Buffer.from(a.buffer, a.byteOffset, a.byteLength);
const relative = p => path.relative(ROOT, p);
function inside(p, base) {
  const rel = path.relative(base, p);
  assert(rel && !rel.startsWith('..') && !path.isAbsolute(rel), `Path outside ${base}: ${p}`);
}
export function pinned(row) {
  assert(row && typeof row.path === 'string' && /^[a-f0-9]{64}$/.test(row.sha256), 'Missing real file pin');
  const p = path.resolve(ROOT, row.path); inside(p, ROOT);
  const data = fs.readFileSync(p); assert.equal(sha(data), row.sha256, `Changed pin: ${row.path}`);
  return { p, data };
}
function arrayFrom(binary, row, dtype, shape) {
  assert(row && row.dtype === dtype && JSON.stringify(row.shape) === JSON.stringify(shape), 'Array schema mismatch');
  const length = shape.reduce((a, b) => a * b, 1);
  assert(Number.isSafeInteger(length) && row.byteLength === 4 * length && row.byteOffset % 4 === 0);
  assert(row.byteOffset >= 0 && row.byteOffset + row.byteLength <= binary.length);
  const C = dtype === '<f4' ? Float32Array : dtype === '<i4' ? Int32Array : Uint32Array;
  return new C(binary.buffer, binary.byteOffset + row.byteOffset, length);
}
export function validateCensus(census) {
  assert.equal(census.status, 'COMPLETED_REJECTED_BOOT_CENSUS_UNACCEPTED', 'Actual census incomplete; no simplifier call permitted');
  assert.equal(census.acceptedArt, false);
  assert.equal(census.recipeSHA256, POLICY.censusRecipeSHA256);
  assert.equal(census.inputSHA256, POLICY.censusInputSHA256);
  assert.equal(census.sourcePins.rejectedNative.sha256, POLICY.nativeSHA256);
  assert.equal(census.sourceTriangles, POLICY.sourceTriangles);
  assert.equal(census.targetTriangles, 8000);
  assert(Number.isSafeInteger(census.sourceVertices) && census.sourceVertices > 0);
  assert(Number.isSafeInteger(census.targetVertices) && census.targetVertices > 0);
  assert.equal(census.surfaceBoundM, POLICY.targetErrorM);
  assert.equal(census.minimumNormalDot, POLICY.minimumNormalDot);
  for (const name of STAGES) {
    const row = census.stages[name];
    assert(row?.complete && row.completedCount === row.totalCount && row.totalCount > 0, `Incomplete census stage: ${name}`);
    assert.equal(row.missingNearestCount, 0, `Missing census source bearings: ${name}`);
    const expected = { 'target-vertices': census.targetVertices, 'target-face-centroids': census.targetTriangles,
      'source-vertices': census.sourceVertices, 'source-face-centroids': census.sourceTriangles }[name];
    if (expected) assert.equal(row.totalCount, expected, `Wrong census coverage: ${name}`);
  }
  assert(census.orientationRegions && Number.isInteger(census.orientationRegions.count));
  assert(census.sourceArrayPackage?.layout && census.sourceArrayPackage.groupNames?.length);
  assert.equal(census.sourceArrayPackage.coordinateFrame,
    'Original mesh local coordinates in meters; parent/world bind unchanged in pinned rejected native.');
}
export function readCensus(censusPath) {
  const p = path.resolve(censusPath); inside(p, path.join(ROOT, 'harness/out/rider-rebuild/selected-production-census35'));
  const raw = fs.readFileSync(p); const census = JSON.parse(raw); validateCensus(census);
  for (const row of Object.values(census.sourcePins)) pinned(row);
  for (const name of STAGES) pinned(census.stages[name].arrays);
  pinned(census.orientationRegions.arrays);
  const pkg = census.sourceArrayPackage; const { data } = pinned(pkg); const l = pkg.layout;
  const n = census.sourceVertices, f = census.sourceTriangles, k = pkg.groupNames.length;
  assert(Number.isSafeInteger(n) && n > 0 && n * n < Number.MAX_SAFE_INTEGER);
  assert(l.cornerNormals?.shape?.[1] === 3); const loops = l.cornerNormals.shape[0];
  // Copy only indices for the API's unsigned contract; source bytes stay immutable.
  const a = { positions: arrayFrom(data, l.positions, '<f4', [n, 3]),
    triangles: Uint32Array.from(arrayFrom(data, l.triangles, '<i4', [f, 3])),
    loopIds: arrayFrom(data, l.triangleLoopIds, '<i4', [f, 3]),
    normals: arrayFrom(data, l.vertexNormals, '<f4', [n, 3]),
    cornerNormals: arrayFrom(data, l.cornerNormals, '<f4', [loops, 3]),
    fields: arrayFrom(data, l.namedWeights, '<f4', [n, k]),
    materials: arrayFrom(data, l.faceMaterialIds, '<i4', [f]), names: pkg.groupNames,
    uv: pkg.uvLayerNames.map((name, i) => ({ name, values: arrayFrom(data, l[`uvLayer${i}`], '<f4', [loops, 2]) })) };
  // Reject overlapping records or unreported trailing bytes, including unknown layouts.
  const ranges = Object.values(l).map(r => [r.byteOffset, r.byteOffset + r.byteLength]).sort((x, y) => x[0] - y[0]);
  let end = 0; for (const range of ranges) { assert.equal(range[0], end); end = range[1]; } assert.equal(end, data.length);
  return { a, census, censusPin: { path: relative(p), sha256: sha(raw) } };
}

export function fieldsAndAttributes(a) {
  const n = a.positions.length / 3, k = a.names.length;
  assert(n > 0 && Number.isInteger(n) && k > 0 && new Set(a.names).size === k);
  assert(a.names.every(name => typeof name === 'string' && name.startsWith('DEF-')), 'Need actual named deform-bone fields');
  assert.equal(a.fields.length, n * k); assert.equal(a.normals.length, n * 3);
  const low = Array(k).fill(Infinity), high = Array(k).fill(-Infinity);
  let sumLow = Infinity, sumHigh = -Infinity, sumAbs = 0, notFloat32Normalized = 0;
  let normalLengthLow = Infinity, normalLengthHigh = 0;
  const bounds = [Array(3).fill(Infinity), Array(3).fill(-Infinity)];
  for (let v = 0; v < n; v++) {
    let sum = 0, nsq = 0;
    for (let j = 0; j < 3; j++) {
      const p = a.positions[3 * v + j], q = a.normals[3 * v + j];
      assert(Number.isFinite(p) && Number.isFinite(q), `Invalid position/normal at ${v}`);
      bounds[0][j] = Math.min(bounds[0][j], p); bounds[1][j] = Math.max(bounds[1][j], p); nsq += q * q;
    }
    assert(nsq > 0, `Zero source normal at ${v}`);
    normalLengthLow = Math.min(normalLengthLow, Math.sqrt(nsq)); normalLengthHigh = Math.max(normalLengthHigh, Math.sqrt(nsq));
    for (let j = 0; j < k; j++) {
      const w = a.fields[k * v + j]; assert(Number.isFinite(w) && w >= 0 && w <= 1, `Invalid named field at ${v}/${a.names[j]}`);
      low[j] = Math.min(low[j], w); high[j] = Math.max(high[j], w); sum += w;
    }
    assert(sum > 0, `Unbound source vertex ${v}`);
    sumLow = Math.min(sumLow, sum); sumHigh = Math.max(sumHigh, sum); sumAbs = Math.max(sumAbs, Math.abs(sum - 1));
    if (Math.fround(sum) !== 1) notFloat32Normalized++;
  }
  const varying = a.names.map((_, i) => i).filter(i => low[i] !== high[i]);
  assert(varying.length + 3 <= 32, 'Actual named fields exceed meshoptimizer channel limit');
  const normalWeight = 1 / Math.sqrt(2 * (1 - POLICY.minimumNormalDot));
  const fieldWeight = Math.sqrt(varying.length) / POLICY.maximumSkinWeightL1;
  const stride = 3 + varying.length, attributes = new Float32Array(n * stride);
  for (let v = 0; v < n; v++) {
    const length = Math.hypot(...a.normals.subarray(3 * v, 3 * v + 3));
    for (let j = 0; j < 3; j++) attributes[stride * v + j] = a.normals[3 * v + j] / length;
    for (let j = 0; j < varying.length; j++) attributes[stride * v + 3 + j] = a.fields[k * v + varying[j]];
  }
  return { attributes, stride, weights: [normalWeight, normalWeight, normalWeight, ...varying.map(() => fieldWeight)],
    report: { boundsLocalM: bounds, normalLengthRange: [normalLengthLow, normalLengthHigh],
      sourceRowSumRange: [sumLow, sumHigh], maximumSourceRowSumError: sumAbs, rowsNotFloat32Normalized: notFloat32Normalized,
      normalizationPolicy: 'Require source row sum to round to1 at float32 storage precision before actual call; never change donor fields. Normal attributes alone are unitized for the priority metric; output mesh normals are fresh geometry.',
      fields: a.names.map((name, i) => ({ name, range: [low[i], high[i]], varying: low[i] !== high[i] })),
      attributeNames: ['normal.x', 'normal.y', 'normal.z', ...varying.map(i => a.names[i])],
      priorityOnly: true, commonMultiplier: 1 } };
}

export function topology(a) {
  const n = a.positions.length / 3, f = a.triangles.length / 3, k = a.names.length;
  assert(Number.isInteger(f) && a.materials.length === f && a.loopIds.length === 3 * f);
  const locks = new Uint8Array(n), parent = Uint32Array.from({ length: n }, (_, i) => i);
  const used = new Uint8Array(n), incidentMaterials = Array.from({ length: n }, () => new Set());
  function root(v) { while (parent[v] !== v) { parent[v] = parent[parent[v]]; v = parent[v]; } return v; }
  const keys = new Float64Array(3 * f), order = Uint32Array.from({ length: 3 * f }, (_, i) => i);
  for (let i = 0; i < 3 * f; i++) {
    const v = a.triangles[i], face = Math.floor(i / 3), c = i % 3;
    const w = a.triangles[3 * face + (c + 1) % 3];
    assert(v < n && w < n && v !== w, `Invalid source edge at ${i}`); assert(a.materials[face] >= 0);
    assert(a.loopIds[i] >= 0 && a.loopIds[i] < a.cornerNormals.length / 3);
    used[v] = 1; parent[root(v)] = root(w); incidentMaterials[v].add(a.materials[face]);
    keys[i] = Math.min(v, w) * n + Math.max(v, w);
  }
  for (const layer of a.uv) for (const x of layer.values) assert(Number.isFinite(x), 'Nonfinite donor UV');
  for (const x of a.cornerNormals) assert(Number.isFinite(x), 'Nonfinite donor corner normal');
  order.sort((i, j) => keys[i] - keys[j]);
  const requiredEdges = [], uvSeams = a.uv.map(layer => ({ name: layer.name, edges: 0 }));
  let boundaries = 0, materialEdges = 0, cornerNormalEdges = 0;
  function endpointLoop(edgeOrdinal, v) {
    const face = Math.floor(edgeOrdinal / 3), c = edgeOrdinal % 3;
    return a.loopIds[3 * face + (a.triangles[edgeOrdinal] === v ? c : (c + 1) % 3)];
  }
  for (let start = 0; start < order.length;) {
    let stop = start + 1; while (stop < order.length && keys[order[stop]] === keys[order[start]]) stop++;
    const key = keys[order[start]], v = Math.floor(key / n), w = key - v * n;
    const boundary = stop - start !== 2;
    const material = !boundary && a.materials[Math.floor(order[start] / 3)] !== a.materials[Math.floor(order[start + 1] / 3)];
    if (boundary || material) { locks[v] = 1; locks[w] = 1; requiredEdges.push(v, w); }
    if (boundary) boundaries++; if (material) materialEdges++;
    if (!boundary) {
      const l = [v, w].map(endpoint => [endpointLoop(order[start], endpoint), endpointLoop(order[start + 1], endpoint)]);
      for (let layer = 0; layer < a.uv.length; layer++) {
        const values = a.uv[layer].values;
        if (l.some(([i, j]) => values[2 * i] !== values[2 * j] || values[2 * i + 1] !== values[2 * j + 1])) uvSeams[layer].edges++;
      }
      if (l.some(([i, j]) => [0, 1, 2].some(c => a.cornerNormals[3 * i + c] !== a.cornerNormals[3 * j + c]))) cornerNormalEdges++;
    }
    start = stop;
  }
  // Meshoptimizer internally compares positions. Keep coincident native vertices
  // locked and separate so unrelated shells/field discontinuities cannot merge.
  const sorted = Uint32Array.from({ length: n }, (_, i) => i);
  const compare = (i, j) => a.positions[3 * i] - a.positions[3 * j] || a.positions[3 * i + 1] - a.positions[3 * j + 1] || a.positions[3 * i + 2] - a.positions[3 * j + 2];
  sorted.sort(compare); let coincidentVertices = 0, coincidentGroups = 0;
  let crossComponentGroups = 0, differingNamedFieldGroups = 0, extraCoincidentLocks = 0;
  for (let start = 0; start < n;) {
    let stop = start + 1; while (stop < n && compare(sorted[start], sorted[stop]) === 0) stop++;
    if (stop - start > 1) {
      const group = sorted.subarray(start, stop).filter(v => used[v]);
      if (group.length > 1) {
        coincidentGroups++;
        if (new Set(group.map(v => root(v))).size > 1) crossComponentGroups++;
        if (group.some(v => Array.from({ length: k }, (_, j) => j).some(j => a.fields[k * v + j] !== a.fields[k * group[0] + j]))) differingNamedFieldGroups++;
        for (const v of group) { if (!locks[v]) extraCoincidentLocks++; locks[v] = 1; coincidentVertices++; }
      }
    }
    start = stop;
  }
  const components = new Map();
  for (let v = 0; v < n; v++) { parent[v] = root(v); if (used[v]) components.set(parent[v], (components.get(parent[v]) || 0) + 1); }
  assert.equal(a.fields.length, n * k);
  return { locks, requiredEdges: Uint32Array.from(requiredEdges), components: parent, incidentMaterials,
    report: { sourceComponents: components.size, unreferencedVertices: n - used.reduce((x, y) => x + y, 0),
      boundaryOrNonmanifoldEdges: boundaries, materialEdges, coincidentVerticesLocked: coincidentVertices,
      coincidentPositionGroups: coincidentGroups, coincidentGroupsAcrossComponents: crossComponentGroups,
      coincidentGroupsWithDifferentNamedFields: differingNamedFieldGroups, additionalConservativeCoincidentLocks: extraCoincidentLocks,
      coincidencePolicy: 'Additional conservative protection, not an assertion that coincident points are equivalent. Required frozen25 locks are boundary/material edges. No weld, no empirical unlocking sweep; report counts before the single call.',
      requiredEdges: requiredEdges.length / 2, lockedVertices: locks.reduce((x, y) => x + y, 0), uvSeams,
      cornerNormalDiscontinuityEdges: cornerNormalEdges,
      uvPolicy: 'Donor loop UVs/corner normals remain immutable; fresh target unwrap and selected-to-active PBR bake. No UV coefficient or copied target normal.',
      contactLockPolicy: 'No invented contact-region locks. Exact boundaries/material edges and all coincident source positions are protected; finite contact remains an independent moving gate.' } };
}

export function compactCandidate(a, t, originalIndices) {
  assert(originalIndices instanceof Uint32Array && originalIndices.length > 0 && originalIndices.length % 3 === 0);
  const n = a.positions.length / 3, k = a.names.length, used = new Uint8Array(n), seenComponents = new Set();
  const sourceComponents = new Set(a.triangles.filter((_, i) => i % 3 === 0).map(v => t.components[v]));
  for (const v of originalIndices) { assert(v < n, 'Returned index leaves source'); used[v] = 1; }
  for (let v = 0; v < n; v++) if (t.locks[v]) assert(used[v], `Locked source vertex removed: ${v}`);
  const ancestry = Uint32Array.from(Array.from(used.keys()).filter(v => used[v]));
  const remap = new Int32Array(n).fill(-1); ancestry.forEach((v, i) => { remap[v] = i; });
  const positions = new Float32Array(ancestry.length * 3), fields = new Float32Array(ancestry.length * k);
  ancestry.forEach((v, i) => { positions.set(a.positions.subarray(3 * v, 3 * v + 3), 3 * i); fields.set(a.fields.subarray(k * v, k * v + k), k * i); });
  const indices = Uint32Array.from(originalIndices, v => remap[v]), materials = new Int32Array(indices.length / 3);
  const outputEdges = new Set();
  for (let i = 0; i < originalIndices.length; i += 3) {
    const face = originalIndices.subarray(i, i + 3), component = t.components[face[0]];
    assert(face.every(v => t.components[v] === component), 'Output face bridges disconnected source components'); seenComponents.add(component);
    const shared = [...t.incidentMaterials[face[0]]].filter(m => face.every(v => t.incidentMaterials[v].has(m)));
    assert.equal(shared.length, 1, `Ambiguous target material ancestry at triangle ${i / 3}`); materials[i / 3] = shared[0];
    const [v, w, z] = face; assert(v !== w && w !== z && z !== v, 'Repeated output triangle index');
    const ab = [0, 1, 2].map(j => a.positions[3 * w + j] - a.positions[3 * v + j]);
    const ac = [0, 1, 2].map(j => a.positions[3 * z + j] - a.positions[3 * v + j]);
    const cross = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]];
    assert(cross.some(x => x !== 0), 'Zero-area output face');
    for (let c = 0; c < 3; c++) { const p = face[c], q = face[(c + 1) % 3]; outputEdges.add(Math.min(p, q) * n + Math.max(p, q)); }
  }
  assert.equal(seenComponents.size, sourceComponents.size, 'Selected source component disappeared');
  for (let i = 0; i < t.requiredEdges.length; i += 2) {
    const v = t.requiredEdges[i], w = t.requiredEdges[i + 1]; assert(outputEdges.has(Math.min(v, w) * n + Math.max(v, w)), 'Protected source edge removed');
  }
  return { positions, triangles: indices, originalVertexIds: ancestry, namedWeights: fields, faceMaterialIds: materials,
    requiredEdgesOriginal: t.requiredEdges, lockedOriginalVertexIds: Uint32Array.from(t.locks.keys()).filter(v => t.locks[v]) };
}
export function writeArrays(file, arrays) {
  const layout = {}; let offset = 0; const blocks = [];
  for (const [name, a] of Object.entries(arrays)) {
    layout[name] = { byteOffset: offset, byteLength: a.byteLength,
      dtype: a instanceof Float32Array ? '<f4' : a instanceof Int32Array ? '<i4' : '<u4', count: a.length };
    blocks.push(bytes(a)); offset += a.byteLength;
  }
  const data = Buffer.concat(blocks); fs.writeFileSync(file, data, { flag: 'wx' });
  return { path: relative(file), sha256: sha(data), layout };
}

async function main() {
  assert.equal(process.argv.length, 4, 'Usage: node construct.mjs COMPLETE_CENSUS_JSON NEW_OUT');
  const { a, census, censusPin } = readCensus(process.argv[2]);
  const out = path.resolve(process.argv[3]); inside(out, path.join(ROOT, 'harness/out/rider-rebuild/selected-production-constructor37'));
  assert(!fs.existsSync(out), 'Never overwrite a candidate or retry in the same directory');
  fs.mkdirSync(out, { recursive: true });
  const report = { status: 'INTAKE_IN_PROGRESS_UNACCEPTED', acceptedArt: false, candidateAttempts: 0,
    census: censusPin, censusSourcePins: census.sourcePins, sourceArrayPackage: census.sourceArrayPackage,
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
    assert(report.minimumTrianglesFromLockedVertexCount <= POLICY.targetTriangles, 'Protected source vertices alone require more than8000 triangles; stop without a simplifier call or unlocking sweep');
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
    report.allocationPassed = report.targetTriangles <= POLICY.targetTriangles; write();
    const candidate = compactCandidate(a, t, indices);
    report.candidate = writeArrays(path.join(out, 'candidate.bin'), candidate); report.targetVertices = candidate.originalVertexIds.length;
    report.sourceInputBytesUnchanged = true; report.exactOriginalPositionsAndNamedFields = true;
    report.status = report.allocationPassed ? 'UNACCEPTED_CANDIDATE_AWAITING_NATIVE_QUALIFICATION' : 'REJECTED_ALLOCATION_ABOVE_8000';
    report.limits = 'One area-weighted priority attempt; approximate error is not surface/orientation/skin/contact proof. Native gates, selected atlas bake, complete motion and device remain open. No normal-player output.';
    write(); console.log(JSON.stringify({ status: report.status, triangles: report.targetTriangles, approximateError, candidate: report.candidate.path }));
    if (!report.allocationPassed) process.exitCode = 2;
  } catch (error) {
    report.status = 'REJECTED_CONSTRUCTOR37_UNACCEPTED'; report.failure = String(error.stack || error); write(); throw error;
  }
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
