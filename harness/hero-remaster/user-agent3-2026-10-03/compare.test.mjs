import test from 'node:test';
import assert from 'node:assert/strict';
import { compareMappedPositions, compareThreeWays } from './compare.mjs';

await test('reordered and split exported rows retain the actual native witness', () => {
  const native = new Float64Array([0, 0, 0, 1, 0, 0, 2, 0, 0, 3, 0, 0]);
  const exported = new Float64Array([2, .002, 0, 0, 0, 0, 2, 0, 0]);
  const result = compareMappedPositions(native, exported, [2, 0, 2]);
  assert.equal(result.worst.nativeVertexID, 2);
  assert.equal(result.worst.exportVertexID, 0);
  assert.equal(result.maxM, .002);
  assert.equal(result.rowsAboveDiagnostic, 1);
  assert.equal(result.unexportedNativeVertices, 2);
  assert.equal(result.duplicatedExportRows, 1);
  assert(compareMappedPositions(native, exported, [0, 1, 2]).maxM > 1);
});

await test('export agreement does not hide deformation introduced by conditioning', () => {
  const result = compareThreeWays([0, 0, 0], [.01, 0, 0], [.01, 0, 0], [0]);
  assert.equal(result.conditionedToExport.maxM, 0);
  assert.equal(result.fullToConditioned.maxM, .01);
  assert.equal(result.fullToExport.maxM, .01);
});

await test('invalid source identity and nonfinite samples fail closed', () => {
  for (const id of [undefined, -1, .5, 1])
    assert.throws(() => compareMappedPositions([0, 0, 0], [0, 0, 0], [id]));
  assert.throws(() => compareMappedPositions([NaN, 0, 0], [0, 0, 0], [0]));
  assert.throws(() => compareMappedPositions([0, 0, 0], [Infinity, 0, 0], [0]));
  assert.throws(() => compareThreeWays([0, 0, 0], [], [0, 0, 0], [0]));
});
