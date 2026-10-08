import assert from 'node:assert/strict';
import test from 'node:test';
import { Vector3 } from 'three';
import { crossings, surface } from './geometry.mjs';

const triangle = (row, nativeIDs, points) => surface(points.map(p => new Vector3(...p)), { row, nativeIDs });
const first = triangle(0, [0, 1, 2], [[0, 0, 0], [1, 0, 0], [0, 1, 0]]);
const fixtures = [
  ['shared vertex only', [0, 3, 4], [[0, 0, 0], [-1, 0, 1], [0, -1, 1]], 0],
  ['shared noncoplanar edge only', [0, 1, 3], [[0, 0, 0], [1, 0, 0], [0, 0, 1]], 0],
  ['shared coplanar edge only', [0, 1, 3], [[0, 0, 0], [1, 0, 0], [0, -1, 0]], 0],
  ['shared vertex with interior crossing', [0, 3, 4], [[0, 0, 0], [0.6, 0.2, -1], [0.6, 0.2, 1]], 1],
  ['shared edge with coplanar fold', [0, 1, 3], [[0, 0, 0], [1, 0, 0], [0.2, 0.5, 0]], 1],
];
for (const [name, ids, points, expected] of fixtures) test(name, () => {
  const second = triangle(1, ids, points), report = crossings([first, second], [first, second], true);
  assert.equal(report.count, expected);
  assert.equal(report.testedPairs, 1, 'Adjacent faces must reach the geometric test exactly once');
  assert.deepEqual(report.pairs, expected ? [[0, 1]] : []);
});
test('interior crossing with coincident boundary endpoints', () => {
  const a = triangle(0, [0, 1, 2], [[-1, -1, 0], [1, -1, 0], [0, 1, 0]]);
  const b = triangle(1, [3, 4, 5], [[-1, 0, -1], [1, 0, -1], [0, 0, 1]]);
  assert.equal(crossings([a], [b]).count, 1);
});
