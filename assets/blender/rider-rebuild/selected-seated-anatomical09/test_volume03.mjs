/** Tiny topology/lineage fixtures only; no production source or native opens. */
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { morphFields, validateManifest } from './transport-volume03.mjs';

const positions = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]];
const normals = positions.map(() => [0, 0, 1]), ids = [8, 2, 19, 8], faces = [0, 1, 2, 3, 1, 2];
const row = (nativeID, deltaGLTF) => ({ nativeID, deltaGLTF, deltaBlender: [deltaGLTF[0], -deltaGLTF[2], deltaGLTF[1]] });
test('Native IDs carry the same new field across split primitive rows', () => {
  const result = morphFields(ids, positions, normals, faces, [row(8, [0, 0, .25])]);
  assert.deepEqual(result.POSITION.slice(0, 3), [0, 0, .25]);
  assert.deepEqual(result.POSITION.slice(9, 12), [0, 0, .25]);
  assert.deepEqual(result.POSITION.slice(3, 9), [0, 0, 0, 0, 0, 0]);
  assert(result.NORMAL.every(Number.isFinite)); assert(result.maximumNormalRotationRadians > 0);
  assert.equal(result.TANGENT, undefined);
});
test('Rigid translation leaves authored split normal and tangent fields exact', () => {
  const authored = positions.map(() => [.6, 0, .8]), tangents = positions.map(() => [.8, 0, -.6, -1]);
  const result = morphFields(ids, positions, authored, faces, [8, 2, 19].map(id => row(id, [.25, .5, .75])), tangents);
  assert(result.NORMAL.every(v => v === 0)); assert(result.TANGENT.every(v => v === 0));
  assert.equal(result.maximumNormalRotationRadians, 0);
});
test('Duplicate IDs or inconsistent coordinate conventions fail closed', () => {
  assert.throws(() => morphFields(ids, positions, normals, faces, [row(8, [0, 0, .25]), row(8, [0, 0, .5])]));
  assert.throws(() => morphFields(ids, positions, normals, faces, [{...row(8, [0, 0, .25]), deltaBlender: [0, .25, 0]}]));
});
test('Incomplete and unpinned manifests cannot run', () => {
  assert.throws(() => validateManifest({accepted: false, pins: {}}));
  assert.throws(() => validateManifest({accepted: true, pins: {}}));
});
