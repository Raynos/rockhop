import test from 'node:test';
import assert from 'node:assert/strict';
import { Vector3 } from 'three';
import { invertAnthropometricCOM } from './anthropometric-inverse.mjs';

void test('measured COM inversion solves distinct hips without changing the supplied physical COM', () => {
  const expectedHips = [0.23, 0.81];
  const measure = ([x, y]) => new Vector3(0.8 * x + 0.2 * y + 0.15, -0.1 * x + 0.75 * y + 0.19, 0);
  const target = measure(expectedHips), before = target.toArray(), initial = [-0.1, 0.6];
  const solution = invertAnthropometricCOM(measure, target, initial);
  assert.ok(solution.converged); assert.ok(solution.residualM < 1e-6);
  assert.ok(Math.hypot(...solution.hips.map((value, i) => value - expectedHips[i])) < 1e-6);
  assert.deepEqual(target.toArray(), before); assert.deepEqual(initial, [-0.1, 0.6]);
  assert.notDeepEqual(solution.hips, target.toArray().slice(0, 2));
});

void test('singular anatomy reports the remaining residual without accepting an unreachable target', () => {
  const target = new Vector3(2, 3, 0), initial = [0, 0];
  const result = invertAnthropometricCOM(() => new Vector3(0.2, 0.5, 0), target, initial);
  assert.equal(result.converged, false); assert.deepEqual(result.hips, initial);
  assert.ok(result.residualM > 3); assert.ok(result.iterations <= 16);
});
