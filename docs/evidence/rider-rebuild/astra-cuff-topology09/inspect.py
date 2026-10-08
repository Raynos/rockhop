"""Read-only exact cuff06 LEFT witness; writes only the sibling receipt.json.

CPU2 environment: OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
VECLIB_MAXIMUM_THREADS=2 NUMEXPR_NUM_THREADS=2. No Blender or mesh writes.
"""
import hashlib
import json
import runpy
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'assets/blender/rider-rebuild/glove-cuff-fit06/freeze.py'
namespace = runpy.run_path(str(SOURCE))
captured = {}


def trace(frame, event, value):
    if frame.f_code is namespace['main'].__code__:
        if event == 'exception' and isinstance(value[1], AssertionError):
            captured.update(frame.f_locals)
            captured['assertion'] = repr(value[1])
        return trace
    return None


def refuse_write(*args, **kwargs):
    raise RuntimeError('Diagnostic refuses recipe outputs')


original_save = np.savez_compressed
np.savez_compressed = refuse_write
sys.settrace(trace)
try:
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter('always')
        try:
            namespace['main']()
        except AssertionError as error:
            assert 'orientation reversal' in str(error), repr(error)
        else:
            raise RuntimeError('Expected unchanged LEFT failure did not occur')
finally:
    sys.settrace(None)
    np.savez_compressed = original_save
assert captured['side'] == 'L'
assert not (SOURCE.parent / 'controls.json').exists()
assert not list(SOURCE.parent.glob('cuff-sector-offsets-*.npz'))

# Explicit three-term sums avoid this host's spurious matmul warning flags.
linear = captured['linear']
before = np.sum(captured['points'][:, None, :] * linear[None, :, :], axis=2) + captured['translation']
after = np.sum(captured['corrected'].astype(float)[:, None, :] * linear[None, :, :], axis=2) + captured['translation']
assert np.isfinite(before).all() and np.isfinite(after).all()
faces = captured['faces']
first, second = 4985, 5324
assert not set(faces[first]) & set(faces[second])


def normal(triangle):
    value = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
    return value / np.linalg.norm(value)


def inspect(points):
    a, b = points[faces[first]], points[faces[second]]
    plane_distances = np.sum((a - b[0]) * normal(b), axis=1)
    crossings = []
    for edge in (1, 2):
        direction = a[(edge + 1) % 3] - a[edge]
        matrix = np.column_stack((direction, -(b[1] - b[0]), -(b[2] - b[0])))
        rhs = b[0] - a[edge]
        tuv = np.linalg.solve(matrix, rhs)
        t, u, v = map(float, tuv)
        residual = np.sum(matrix * tuv[None, :], axis=1) - rhs
        strict = 1e-7 < t < 1 - 1e-7 and u > 1e-7 and v > 1e-7 and u + v < 1 - 1e-7
        crossings.append({'firstTriangleEdge': edge, 'tuv': [t, u, v],
                          'strictInteriorCrossing': bool(strict),
                          'residualM': float(np.linalg.norm(residual)),
                          'intersectionXYZ': (a[edge] + t * direction).tolist()})
    n1, n2 = normal(points[faces[8353]]), normal(points[faces[8588]])
    dot = float(np.sum(n1 * n2))
    return {'firstTriangleXYZ': a.tolist(), 'secondTriangleXYZ': b.tolist(),
            'firstTriangleSignedDistancesToSecondPlaneM': plane_distances.tolist(),
            'firstTriangleStrictlyOnOneSide': bool(np.all(plane_distances < 0) or np.all(plane_distances > 0)),
            'edgePlaneSolves': crossings,
            'neighborCrease': {'triangles': [8353, 8588],
                               'sharedVertices': sorted(set(map(int, faces[8353])) & set(map(int, faces[8588]))),
                               'normalDot': dot,
                               'normalAngleDegrees': float(np.degrees(np.arccos(np.clip(dot, -1, 1))))}}


result_before, result_after = inspect(before), inspect(after)
assert result_before['firstTriangleStrictlyOnOneSide']
assert not any(row['strictInteriorCrossing'] for row in result_before['edgePlaneSolves'])
assert all(row['strictInteriorCrossing'] for row in result_after['edgePlaneSolves'])
assert max(row['residualM'] for row in result_after['edgePlaneSolves']) < 1e-14


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


receipt = {
    'acceptedArt': False, 'operation': 'READ_ONLY_EXACT_LEFT_CUFF06_NEW_SELF_INTERSECTION_WITNESS',
    'sources': [pin(Path(__file__).resolve()), pin(SOURCE), pin(SOURCE.parent / 'input.json'),
                pin(ROOT / captured['control']['hands']['L']['priorCuffOffsets']['path']),
                pin(ROOT / captured['control']['placement']['path'])],
    'exactOriginalAssertion': captured['assertion'],
    'triangles': [first, second], 'guideVertices': [faces[first].tolist(), faces[second].tolist()],
    'before': result_before, 'after': result_after,
    'originalRecipeWarnings': [{'category': row.category.__name__, 'message': str(row.message), 'line': row.lineno} for row in recorded],
    'recipeOutputWritten': False, 'nativeOrRecipeChanged': False,
    'limits': ['Only LEFT guide faces 4985/5324 and neighboring crease 8353/8588 checked here.',
               'Before strict plane separation and after two interior edge crossings prove a new self-intersection.',
               'No complete intersection scan, area-path analysis, RIGHT, dense transfer or animation validation.',
               'The fixed-frame old/new normal-dot gate is not by itself an inversion proof.']}
(HERE / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'receipt': str((HERE / 'receipt.json').relative_to(ROOT)),
                  'beforeStrictlySeparated': result_before['firstTriangleStrictlyOnOneSide'],
                  'afterStrictInteriorCrossings': sum(row['strictInteriorCrossing'] for row in result_after['edgePlaneSolves']),
                  'afterNeighborNormalAngleDegrees': result_after['neighborCrease']['normalAngleDegrees']}))
