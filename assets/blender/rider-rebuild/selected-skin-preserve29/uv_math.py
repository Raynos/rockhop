"""Exact selected material/UV chart boundary and coverage accounting."""
import hashlib
import numpy as np


def chart(uv, materials):
    uv = np.asarray(uv, dtype=np.float32); materials = np.asarray(materials, dtype=np.int32)
    assert uv.shape == (len(materials), 3, 2) and np.isfinite(uv).all()
    edges = np.concatenate((uv[:, [0, 1]], uv[:, [1, 2]], uv[:, [2, 0]]))
    mat = np.tile(materials, 3)
    first, second = edges[:, 0], edges[:, 1]
    nonzero = np.any(first != second, axis=1)
    first, second, mat = first[nonzero], second[nonzero], mat[nonzero]
    reverse = (first[:, 0] > second[:, 0]) | ((first[:, 0] == second[:, 0]) & (first[:, 1] > second[:, 1]))
    coordinates = np.concatenate((np.where(reverse[:, None], second, first), np.where(reverse[:, None], first, second)), axis=1)
    coordinates[coordinates == 0] = 0  # Canonicalize signed zero only.
    rows = np.empty(len(mat), dtype=[('material', '<i4'), ('edge', '<f4', (4,))])
    rows['material'] = mat; rows['edge'] = coordinates
    unique, group = np.unique(rows, return_inverse=True)
    incidence = np.bincount(group, weights=np.where(reverse, -1, 1)).astype('<i4')
    boundary = incidence != 0
    digest = hashlib.sha256(unique[boundary].tobytes()+incidence[boundary].tobytes()).hexdigest()
    a, b = uv[:, 1].astype(float)-uv[:, 0], uv[:, 2].astype(float)-uv[:, 0]
    area = abs(a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0])*.5
    return {'directedMaterialBoundarySHA256': digest, 'boundarySegments': int(boundary.sum()),
            'absoluteUVAreaByMaterial': {str(int(m)): float(area[materials == m].sum()) for m in np.unique(materials)},
            'arithmeticErrorBound': float(np.finfo(float).eps*max(1, len(uv))*max(1., float(abs(uv).max()))**2*64)}


def compare(source, target):
    assert source['directedMaterialBoundarySHA256'] == target['directedMaterialBoundarySHA256'], 'Selected UV/material chart boundary changed'
    assert source['absoluteUVAreaByMaterial'].keys() == target['absoluteUVAreaByMaterial'].keys()
    tolerance = source['arithmeticErrorBound']+target['arithmeticErrorBound']
    errors = {m: abs(source['absoluteUVAreaByMaterial'][m]-target['absoluteUVAreaByMaterial'][m])
              for m in source['absoluteUVAreaByMaterial']}
    assert all(error <= tolerance for error in errors.values()), ('Selected UV coverage/folding changed', errors, tolerance)
    return {'exactSelectedChartBoundaries': True, 'unchangedMaterialUVAreaWithinArithmetic': True,
            'absoluteUVAreaErrors': errors, 'arithmeticErrorBound': tolerance}


def rgba8_mip_bytes(width, height):
    result = 0
    while True:
        result += width*height*4
        if width == height == 1: return result
        width, height = max(1, width//2), max(1, height//2)
