"""Actual installed skimage: sparse SDF, missing coverage and mask addressing."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import skimage
from skimage import measure
from audit_native import audit
from finite_cell_mc import extract


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    module = Path(measure.__file__).parent
    report = {'accepted': False, 'modelRuns': 0, 'skimage': skimage.__version__,
              'recipeSHA256': sha(__file__), 'adapterSHA256': sha(Path(__file__).with_name('finite_cell_mc.py')),
              'installedMCFiles': {p.name: sha(p) for p in sorted(module.glob('*marching_cubes*')) if p.is_file()},
              'cases': [], 'limits': ['Analytic controls do not establish actual decoder field coverage.',
                                     'No field filling, NaN removal, remeshing or shared-source changes.',
                                     'Mask addressing qualified only at step_size=1 in this installed runtime.']}
    # One valid cell at an asymmetric location, all other samples missing.
    sentinel = np.full((5, 6, 7), np.nan, dtype=np.float32)
    cube = np.ones((2, 2, 2), dtype=np.float32)
    cube[0, 0, 0] = -1
    sentinel[1:3, 2:4, 3:5] = cube
    expected_v, expected_f, _, _ = measure.marching_cubes(cube, 0, method='lewiner')
    v, f, counts = extract(sentinel)
    assert np.array_equal(v, expected_v + [1, 2, 3]) and np.array_equal(f, expected_f)
    report['cases'].append({'name': 'asymmetricSingleCellUpperCornerMask', 'pass': True, **counts})
    axis = np.linspace(-1.4, 1.4, 65, dtype=np.float32)
    field = np.float32(.917) - np.sqrt(axis[:, None, None] ** 2 + axis[None, :, None] ** 2 + axis[None, None, :] ** 2)
    dense_v, dense_f, _, _ = measure.marching_cubes(field, 0, method='lewiner')
    band = field.copy()
    band[np.abs(field) > .18] = np.nan
    cut = band.copy()
    cut[:33] = np.nan
    constant = np.full(field.shape, np.nan, dtype=np.float32)
    constant[12:52, 13:51, 14:50] = 1
    for name, volume in [('denseSphere', field), ('finiteBandSphere', band),
                         ('cutCoverageSphere', cut), ('constantPositiveNoSurface', constant)]:
        before = hashlib.sha256(volume.tobytes()).hexdigest()
        vertices, faces, counts = extract(volume)
        metrics = audit(vertices, faces)
        assert hashlib.sha256(volume.tobytes()).hexdigest() == before
        arrays_identical = bool(np.array_equal(vertices, dense_v) and np.array_equal(faces, dense_f))
        if name in ('denseSphere', 'finiteBandSphere'):
            assert arrays_identical and metrics['validGeometryArrays']
            assert metrics['boundaryEdges'] == metrics['overusedEdges'] == metrics['zeroAreaTriangles'] == 0
        elif name == 'cutCoverageSphere':
            assert metrics['validGeometryArrays'] and metrics['boundaryEdges'] > 0
        else:
            assert len(vertices) == len(faces) == counts['finiteCrossingCells'] == 0
        native = audit(dense_v, dense_f)
        if name != 'denseSphere':
            try:
                nv, nf, _, _ = measure.marching_cubes(volume, 0, method='lewiner')
                native = audit(nv, nf)
            except (ValueError, RuntimeError) as error:
                native = {'exception': type(error).__name__, 'message': str(error)}
        archive = out / (name + '.npz')
        np.savez_compressed(archive, volume=volume, vertices=vertices, faces=faces)
        report['cases'].append({'name': name, 'pass': True, **counts, 'nativeAudit': native,
                                'derivedAudit': metrics, 'denseSphereArraysIdentical': arrays_identical,
                                'fieldBytesUnchanged': True, 'fixtureSHA256': sha(archive)})
    report['allControlsPass'] = all(c['pass'] for c in report['cases'])
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
