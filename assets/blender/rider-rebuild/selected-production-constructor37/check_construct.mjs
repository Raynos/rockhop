import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MeshoptSimplifier } from '../../../../node_modules/meshoptimizer/meshopt_simplifier.js';
import { POLICY, sha, validateCensus, fieldsAndAttributes, topology, compactCandidate } from './construct.mjs';

function source(positions, faces, options = {}) {
  const n = positions.length / 3;
  const names = options.names || ['DEF-foot.L', 'DEF-shin.L', 'DEF-toe.L'];
  const normals = new Float32Array(n * 3); for (let v = 0; v < n; v++) normals[3 * v + 2] = 1;
  const fields = new Float32Array(n * names.length); for (let v = 0; v < n; v++) fields[v * names.length] = 1;
  const cornerNormals = new Float32Array(faces.length * 3), uv = new Float32Array(faces.length * 2);
  for (let i = 0; i < faces.length; i++) {
    cornerNormals[3 * i + 2] = 1; uv[2 * i] = positions[3 * faces[i]]; uv[2 * i + 1] = positions[3 * faces[i] + 1];
  }
  return { positions: Float32Array.from(positions), triangles: Uint32Array.from(faces),
    loopIds: Int32Array.from({ length: faces.length }, (_, i) => i), normals, fields, names,
    cornerNormals, uv: [{ name: 'DonorUV', values: uv }], materials: new Int32Array(faces.length / 3), ...options };
}
function grid(size) {
  const p = [], f = [];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) p.push(x / 100, y / 100, 0);
  for (let y = 0; y < size - 1; y++) for (let x = 0; x < size - 1; x++) {
    const v = y * size + x; f.push(v, v + 1, v + size, v + 1, v + size + 1, v + size);
  }
  return source(p, f);
}

test('incomplete actual census fails before a library call or candidate allocation', () => {
  assert.throws(() => validateCensus({ status: 'INCOMPLETE_REJECTED_BOOT_CENSUS' }), /Actual census incomplete/);
  const c = { status: 'COMPLETED_REJECTED_BOOT_CENSUS_UNACCEPTED', acceptedArt: false,
    recipeSHA256: POLICY.censusRecipeSHA256, inputSHA256: POLICY.censusInputSHA256,
    sourcePins: { rejectedNative: { sha256: POLICY.nativeSHA256 } }, sourceTriangles: 610934,
    targetTriangles: 8000, targetVertices: 4002, sourceVertices: 305469,
    surfaceBoundM: .001, minimumNormalDot: .25, stages: { 'target-vertices': { complete: false } } };
  assert.throws(() => validateCensus(c), /Incomplete census stage/);
});

test('named fields retain rare values and changing bone identity despite equal ranked slots', () => {
  const a = grid(2); a.fields.set([.8, .2, 0, .2, .8, 0, .8, .19999999, .00000001, .2, .8, 0]);
  const before = Buffer.from(a.fields.buffer).toString('hex'); const row = fieldsAndAttributes(a);
  assert.equal(row.stride, 6); assert.deepEqual(row.report.attributeNames.slice(3), a.names);
  assert.equal(row.attributes[3], a.fields[0]); assert.equal(row.attributes[9], a.fields[3]);
  assert.equal(row.attributes[17], a.fields[8]); assert.notEqual(row.attributes[3], row.attributes[9]);
  assert.equal(Buffer.from(a.fields.buffer).toString('hex'), before);
  assert.deepEqual(row.weights.slice(3), Array(3).fill(Math.sqrt(3) / .3));
});

test('drop only globally exact constant fields; report row sums without normalizing', () => {
  const a = grid(2); const before = Float32Array.from(a.fields); const row = fieldsAndAttributes(a);
  assert.equal(row.stride, 3); assert.deepEqual(a.fields, before); assert.deepEqual(row.report.sourceRowSumRange, [1, 1]);
  a.fields[0] = .9; const bad = fieldsAndAttributes(a);
  assert.equal(bad.report.rowsNotFloat32Normalized, 1); assert.equal(a.fields[0], Math.fround(.9));
  a.fields.fill(0); assert.throws(() => fieldsAndAttributes(a), /Unbound source vertex/);
  a.fields[0] = -1; assert.throws(() => fieldsAndAttributes(a), /Invalid named field/);
});

test('priority scale expresses existing vector and skin budgets without model-size multiplier', () => {
  const a = grid(2); a.fields.set([1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0]);
  const row = fieldsAndAttributes(a), normalDistance = Math.sqrt(2 * (1 - .25));
  assert(Math.abs(row.weights[0] * normalDistance - 1) <= Number.EPSILON);
  const delta = [.16, -.16, 0]; assert(delta.reduce((s, x) => s + Math.abs(x), 0) > .3);
  assert(Math.hypot(...delta.map(x => x * row.weights[3])) > 1);
  const smaller = { ...a, positions: Float32Array.from(a.positions, x => x / 10) };
  assert.deepEqual(fieldsAndAttributes(smaller).weights, row.weights);
});

test('boundary/material edges stay exact; donor UV seam is measured without reusing its chart', () => {
  const a = grid(3); const initial = topology(a);
  assert.equal(initial.report.boundaryOrNonmanifoldEdges, 8); assert.equal(initial.locks[4], 0);
  assert.equal(initial.report.uvSeams[0].edges, 0);
  a.materials[1] = 1; a.uv[0].values[6] += .125;
  const changed = topology(a); assert(changed.report.materialEdges > 0); assert(changed.report.uvSeams[0].edges > 0);
  assert.equal(changed.locks[4], 1);
  const originalUV = Float32Array.from(a.uv[0].values); topology(a); assert.deepEqual(a.uv[0].values, originalUV);
});

test('coincident disconnected shells keep distinct source IDs and cannot disappear', () => {
  const a = source([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0], [0, 1, 2, 3, 4, 5]);
  const t = topology(a); assert.equal(t.report.sourceComponents, 2); assert.equal(t.report.coincidentVerticesLocked, 6);
  const c = compactCandidate(a, t, a.triangles); assert.deepEqual([...c.originalVertexIds], [0, 1, 2, 3, 4, 5]);
  assert.throws(() => compactCandidate(a, t, new Uint32Array([0, 1, 2])), /Locked source vertex removed/);
});

test('compaction preserves exact positions/fields and compact-to-original direction', () => {
  const a = source([9, 9, 9, 0, 0, 0, 8, 8, 8, 1, 0, 0, 7, 7, 7, 0, 1, 0], [5, 1, 3]);
  a.fields.set([.5, .25, .25], 3); const c = compactCandidate(a, topology(a), a.triangles);
  assert.deepEqual([...c.originalVertexIds], [1, 3, 5]); assert.deepEqual([...c.triangles], [2, 0, 1]);
  assert.deepEqual([...c.positions], [0, 0, 0, 1, 0, 0, 0, 1, 0]);
  assert.deepEqual([...c.namedWeights.slice(0, 3)], [.5, .25, .25]);
});

test('pinned real WASM on a tiny grid retains input bytes and refuses forced allocation', async () => {
  assert.equal(sha(fs.readFileSync(new URL('../../../../node_modules/meshoptimizer/meshopt_simplifier.js', import.meta.url))), POLICY.simplifierSHA256);
  const a = grid(5), t = topology(a), attr = fieldsAndAttributes(a);
  const inputs = [a.positions, a.triangles, attr.attributes, t.locks];
  const hash = x => sha(Buffer.from(x.buffer, x.byteOffset, x.byteLength)); const before = inputs.map(hash);
  await MeshoptSimplifier.ready;
  const [indices, error] = MeshoptSimplifier.simplifyWithAttributes(a.triangles, a.positions, 3,
    attr.attributes, attr.stride, attr.weights, t.locks, 3, .001, ['ErrorAbsolute']);
  assert.deepEqual(inputs.map(hash), before); assert(error >= 0 && error <= .001);
  assert(indices.length > 3, 'Protected perimeter must stop above an impossible1-triangle request');
  assert(indices.length < a.triangles.length, 'Flat interior should simplify');
  const c = compactCandidate(a, t, indices);
  c.originalVertexIds.forEach((v, i) => assert.deepEqual(c.positions.slice(3 * i, 3 * i + 3), a.positions.slice(3 * v, 3 * v + 3)));
});
