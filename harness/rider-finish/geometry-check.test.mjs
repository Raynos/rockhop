import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkPair, inspectSnapshot } from './geometry-check.mjs';
const surface = xyzWorld => ({ xyzWorld, faces: [[0, 1, 2]] });
await test('finite crossing, coplanar contact and separation are distinct', () => {
  const a = surface([[0, 0, 0], [2, 0, 0], [0, 2, 0]]);
  const crossing = surface([[.2, .2, -1], [.2, .2, 1], [.6, .2, 1]]);
  assert.equal(checkPair(a, crossing).properCrossings, 1);
  const coplanar = surface([[.1, .1, 0], [.8, .1, 0], [.1, .8, 0]]);
  assert.equal(checkPair(a, coplanar).finiteContacts, 1); assert.equal(checkPair(a, coplanar).properCrossings, 0);
  assert.equal(checkPair(a, surface([[0, 0, 3], [2, 0, 3], [0, 2, 3]])).finiteContacts, 0);
});
await test('degenerate and omitted head cannot receive clean qualification', () => {
  const degenerate = surface([[0, 0, 0], [1, 0, 0], [2, 0, 0]]);
  assert.equal(checkPair(degenerate, degenerate).status, 'DEGENERATE_SURFACE_UNQUALIFIED');
  assert.throws(() => inspectSnapshot({ parts: { body: { full: degenerate, four: degenerate } } }), /head mandatory/);
});
