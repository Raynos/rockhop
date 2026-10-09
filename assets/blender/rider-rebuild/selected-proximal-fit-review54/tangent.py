"""Actual triangle-tangent changes; no ambient-volume strain substitution."""
import numpy as np


def measure(original, current, faces):
    stretches = np.full((len(faces), 2), np.nan); areas = np.full(len(faces), np.nan)
    valid = np.zeros(len(faces), bool)
    for start in range(0, len(faces), 32768):
        a = original[faces[start:start+32768]]; b = current[faces[start:start+32768]]
        e1, e2 = a[:, 1]-a[:, 0], a[:, 2]-a[:, 0]
        f1, f2 = b[:, 1]-b[:, 0], b[:, 2]-b[:, 0]
        length = np.linalg.norm(e1, axis=1); area = np.linalg.norm(np.cross(e1, e2), axis=1)
        ok = (length > 0) & (area > 0); rows = np.flatnonzero(ok)+start
        x = np.sum(e1[ok]*e2[ok], axis=1)/length[ok]
        y = area[ok]/length[ok]
        u = f1[ok]/length[ok, None]
        v = (f2[ok]-u*x[:, None])/y[:, None]
        # Direct3x2 SVD avoids squaring conditioning on tiny donor slivers.
        stretches[rows] = np.linalg.svd(np.stack((u, v), axis=-1), compute_uv=False)[:, ::-1]
        areas[rows] = np.linalg.norm(np.cross(f1[ok], f2[ok]), axis=1)/area[ok]
        valid[rows] = True
    assert valid.any()
    percentiles = [0, .1, 1, 5, 50, 95, 99, 99.9, 100]
    selected = np.flatnonzero(valid)
    low = selected[np.argsort(stretches[valid, 0], kind='stable')[:8]]
    high = selected[np.argsort(-stretches[valid, 1], kind='stable')[:8]]
    report = {'metric': 'Principal stretches of each actual triangle tangent plane, original native to saved native',
        'triangleCount': len(faces), 'sourceDegenerateTriangles': int((~valid).sum()),
        'sourceDegenerateFaceIdsFirst32': np.flatnonzero(~valid)[:32].tolist(),
        'newZeroAreaFromNondegenerateSource': int(np.sum(areas[valid] == 0)),
        'percentiles': percentiles,
        'minorPrincipalStretch': np.percentile(stretches[valid, 0], percentiles).tolist(),
        'majorPrincipalStretch': np.percentile(stretches[valid, 1], percentiles).tolist(),
        'areaRatio': np.percentile(areas[valid], percentiles).tolist(),
        'mostCompressedFaceIds': low.tolist(), 'mostStretchedFaceIds': high.tolist(),
        'acceptanceThresholdInvented': False,
        'limits': ['Source-degenerate faces cannot define a tangent basis; their count is retained, not passed.',
                   'Triangle tangents describe rest-shape changes, not posed cloth behavior or intersection clearance.']}
    return report, stretches, areas


if __name__ == '__main__':
    import json
    p = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    f = np.array([[0, 1, 2]])
    for matrix, expected in [(np.diag([1., 1., .0325]), [1., 1.]),
                             (np.diag([2., .5, 1.]), [.5, 2.])]:
        _, measured, area = measure(p, p@matrix.T, f)
        assert np.allclose(measured[0], expected) and np.allclose(area, 1.)
    angle = .73; rotation = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])
    _, measured, area = measure(p, p@rotation.T+np.array([1, 2, 3]), f)
    assert np.allclose(measured, 1) and np.allclose(area, 1)
    difficult = np.array([[1e6, -1e6, 0], [1e-6, 1e-6, 0], [0, 0, 1]])/np.sqrt(2)
    _, measured, area = measure(p, p@difficult.T, f)
    assert np.allclose(measured[0], [1e-6, 1e6], rtol=1e-6, atol=1e-12) and np.allclose(area, 1)
    print(json.dumps({'passed': True, 'actualRiderRun': False,
        'checks': ['Normal-only compression does not change cloth tangent strain',
                   'Known anisotropic tangent stretches and area', 'Rigid rotation/translation invariance',
                   'Minor tangent stretch survives ill-conditioned direct SVD']}))
