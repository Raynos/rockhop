import assert from 'node:assert/strict';
import test from 'node:test';
import { Matrix3, Quaternion, Vector3 } from 'three';
import { reconstruct, activation, rotation } from './deform.mjs';

test('boundary-constrained reconstruction removes a stretched interior', () => {
  const source = [[-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0], [0, 0, 0]].map(p => new Vector3(...p));
  const vertices = source.map((rest, i) => ({ rest, posed: i === 4 ? new Vector3(3, 4, 0) : rest.clone() }));
  const fixed = new Map(source.slice(0, 4).map((p, i) => [i, p]));
  const result = reconstruct(vertices, [0, 1, 2, 3].map(i => [i, 4, 1]), fixed, source.map(() => new Matrix3()), Date.now() + 1000);
  assert(result.positions[4].length() < 1e-12); assert(result.relativeResidual < 1e-10);
  for (let i = 0; i < 4; i++) assert(result.positions[i].equals(source[i]));
});
test('pose-only activation is exact at rest and key with smooth finite values', () => {
  const identity = new Quaternion(), axis = new Vector3(0, 0, 1), key = [1, 1.1].map(a => new Quaternion().setFromAxisAngle(axis, a));
  const radius = Math.hypot(...key.map(q => q.angleTo(identity)));
  assert(activation([identity, identity], key, radius) < 1e-12); assert.equal(activation(key, key, radius), 1);
  const weights = [0, .25, .5, .75, 1].map(t => activation(key.map(q => identity.clone().slerp(q, t)), key, radius));
  assert(weights.every((w, i) => Number.isFinite(w) && w >= 0 && w <= 1 && (!i || w >= weights[i - 1])));
});
test('polar transport removes scale and rejects a reflected frame', () => {
  const r = rotation(new Matrix3().set(2, 0, 0, 0, 3, 0, 0, 0, 4));
  assert(r.elements.every((v, i) => Math.abs(v - new Matrix3().elements[i]) < 1e-9));
  assert.throws(() => rotation(new Matrix3().set(-1, 0, 0, 0, 1, 0, 0, 0, 1)));
});
