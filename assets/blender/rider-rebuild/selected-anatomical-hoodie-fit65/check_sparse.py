"""Sparse fields equal dense cubic fields, including exact derivative bounds."""
import io
import json
import runpy
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
M = runpy.run_path(str(HERE/'multiscale.py'))
rng = np.random.default_rng(65); checks = []
bounds = np.array([[-.04, -.04, -.04], [.04, .04, .04]])
points = rng.uniform(-.04, .04, (513, 3))
levels, dense_levels = [], []
for spacing in (.04, .02):
    dense = M['Cage'](bounds, spacing); sparse = M['SparseLevel'](bounds, spacing)
    coordinates = np.indices(dense.shape).reshape(3, -1).T
    possible = np.flatnonzero(np.all((coordinates >= 3) & (coordinates < dense.shape-3), axis=1))
    active = np.sort(rng.choice(possible, min(70, len(possible)), replace=False))
    values = rng.normal(size=(len(active), 3))*.0001
    dense.values[active] = values; sparse.active = active; sparse.values = values.copy()
    query = np.r_[-1, np.arange(dense.count), dense.count+1]
    lookup = sparse.lookup(query)
    assert np.array_equal(lookup[1:-1], dense.values) and not lookup[[0, -1]].any()
    a, da = dense.evaluate(points, True); b, db = sparse.evaluate(points, True)
    assert np.array_equal(a, b) and np.array_equal(da, db)
    assert sparse.certificate() == dense.certificate()['derivativeColumnUpperBounds']
    levels.append(sparse); dense_levels.append(dense)
checks.extend(['Sparse hash lookup matches every dense coefficient including missing/outside indices',
    'Sparse cubic positions/Jacobians equal dense positions/Jacobians exactly',
    'Sparse implicit-zero adjacent-difference bounds equal full dense certificate exactly'])

field = M['Multiscale'].__new__(M['Multiscale']); field.levels = levels
moved, jac = field.evaluate(points, True)
expected = points.copy(); expected_jac = np.broadcast_to(np.eye(3), jac.shape).copy()
for dense in dense_levels:
    value, derivative = dense.evaluate(points, True)
    expected += value-points; expected_jac += derivative-np.eye(3)
assert np.array_equal(moved, expected) and np.array_equal(jac, expected_jac)
cert = field.certificate(); column_sum = np.sum([p.certificate()['derivativeColumnUpperBounds'] for p in dense_levels], axis=0)
assert cert['globalDisplacementLipschitzUpperBound'] == float(np.linalg.norm(column_sum))
assert np.linalg.svd(jac-np.eye(3), compute_uv=False).max() <= cert['globalDisplacementLipschitzUpperBound']
checks.append('Shared sum field and global multilevel derivative certificate cover the actual summed Jacobian')

stream = io.BytesIO(); np.savez_compressed(stream, **M['map_arrays']([field])); stream.seek(0)
restored = M['restore_maps'](np.load(stream))[0]; restored_points, restored_jac = restored.evaluate(points, True)
assert np.array_equal(restored_points, moved) and np.array_equal(restored_jac, jac)
assert restored.certificate() == cert
checks.append('Compressed sparse multilevel map serialization/reload has byte-exact position/Jacobian replay and certificates')
print(json.dumps({'passed': True, 'checks': checks}, indent=2))
