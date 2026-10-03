/** Sampled deformation comparisons with explicit export-to-native IDs. */
import assert from 'node:assert/strict';

export function compareMappedPositions(native, exported, ids, diagnosticM = 0.0001) {
  assert(native.length > 0 && native.length % 3 === 0, 'Invalid native XYZ length');
  assert(exported.length > 0 && exported.length === ids.length * 3, 'Invalid export XYZ length');
  assert(Number.isFinite(diagnosticM) && diagnosticM > 0, 'Invalid diagnostic threshold');
  assert(Array.from(native).every(Number.isFinite), 'Nonfinite native vertex');
  assert(Array.from(exported).every(Number.isFinite), 'Nonfinite exported vertex');
  const nativeCount = native.length / 3, errors = [], covered = new Set();
  let squares = 0, aboveDiagnostic = 0, worst;
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i];
    assert(Number.isInteger(id) && id >= 0 && id < nativeCount, 'Invalid source vertex ID');
    covered.add(id);
    const expected = Array.from(native.slice(id * 3, id * 3 + 3));
    const actual = Array.from(exported.slice(i * 3, i * 3 + 3));
    const distanceM = Math.hypot(...actual.map((v, k) => v - expected[k]));
    errors.push(distanceM); squares += distanceM * distanceM;
    if (distanceM > diagnosticM) aboveDiagnostic++;
    if (!worst || distanceM > worst.distanceM)
      worst = { nativeVertexID: id, exportVertexID: i, distanceM, nativeXYZ: expected, exportedXYZ: actual };
  }
  errors.sort((a, b) => a - b);
  return { exportedRows: ids.length, nativeVertices: nativeCount,
    coveredNativeVertices: covered.size, unexportedNativeVertices: nativeCount - covered.size,
    duplicatedExportRows: ids.length - covered.size, maxM: errors.at(-1),
    p99M: errors[Math.ceil(errors.length * .99) - 1], rmsM: Math.sqrt(squares / errors.length),
    diagnosticM, rowsAboveDiagnostic: aboveDiagnostic, worst,
    status: 'SAMPLED_DISPLACEMENT_ONLY_UNACCEPTED' };
}

export function compareThreeWays(full, conditioned, exported, ids, diagnosticM = 0.0001) {
  assert.equal(full.length, conditioned.length, 'Full and conditioned source vertex counts differ');
  const identity = Array.from({ length: full.length / 3 }, (_, i) => i);
  return {
    fullToConditioned: compareMappedPositions(full, conditioned, identity, diagnosticM),
    fullToExport: compareMappedPositions(full, exported, ids, diagnosticM),
    conditionedToExport: compareMappedPositions(conditioned, exported, ids, diagnosticM),
    limits: ['Finite samples do not prove continuous parity.',
      'Displacement and diagnostic counts do not measure clearance, support or visual quality.'],
  };
}
