"""Analytic cube through actual installed extraction branch; no neural weights."""
import argparse
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path

import numpy as np
from audit_native import audit

SOURCE = Path('/Users/raynos/ml/img2mesh/trellis-mac/stubs/o_voxel_override_convert.py')
SOURCE_SHA = '6de4b7149e7300ac056f2d83eec8d149560cac521cdded4fd812dadffd7bfa5c'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') != str(os.getppid()):
        raise RuntimeError('Use bounded owned-child controller')
    if sha(SOURCE) != SOURCE_SHA: raise ValueError('Installed extraction source changed')
    output = Path(args.out)
    if output.exists(): raise FileExistsError('Fresh fixture directory required')
    import torch
    import trimesh
    spec = importlib.util.spec_from_file_location('pinned_cube_extractor', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    coords = np.array(list(itertools.product((0, 1), repeat=3)), dtype=np.int32)
    flags = np.zeros((8, 3), dtype=bool)
    for axis in range(3):
        flags[np.flatnonzero(np.all(coords == [0, 0, 0], axis=1))[0], axis] = True
        anchor = np.zeros(3, dtype=int); anchor[axis] = 1
        flags[np.flatnonzero(np.all(coords == anchor, axis=1))[0], axis] = True
    vertices, faces = module.flexible_dual_grid_to_mesh(
        torch.from_numpy(coords), torch.full((8, 3), .5, dtype=torch.float32),
        torch.from_numpy(flags), torch.ones((8, 1), dtype=torch.float32),
        aabb=[[0, 0, 0], [2, 2, 2]], grid_size=2, train=False)
    v, f = vertices.numpy(), faces.numpy()
    assert len(v) == 8 and len(f) == 12
    assert np.array_equal(v.min(axis=0), [.5, .5, .5]) and np.array_equal(v.max(axis=0), [1.5, 1.5, 1.5])
    raw = audit(v, f)
    assert raw['boundaryEdges'] == 0 and raw['overusedEdges'] == 0 and raw['zeroAreaTriangles'] == 0
    centres = v[f].mean(axis=1)
    normals = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    sign = np.einsum('ij,ij->i', normals, centres - [1, 1, 1])
    # Independent orientation control is applied ONLY to the analytic fixture.
    control = trimesh.Trimesh(vertices=v.copy(), faces=f.copy(), process=False)
    trimesh.repair.fix_normals(control, multibody=True)
    corrected = audit(control.vertices, control.faces)
    assert corrected['equalDirectionTwoFaceEdges'] == 0 and abs(control.volume - 1) < 1e-8
    output.mkdir(parents=True)
    np.savez_compressed(output / 'cube.npz', vertices=v, faces=f, coords=coords, flags=flags)
    report = {'accepted': False, 'purpose': 'Analytic known closed unit cube through actual installed learned-split branch',
              'sourcePath': str(SOURCE), 'sourceSHA256': sha(SOURCE), 'recipeSHA256': sha(__file__),
              'inputs': {'device': 'CPU', 'dualVertexOffset': [.5, .5, .5], 'splitWeight': 'ones, NON-None like decoder inference', 'closedCubeExtent': 1},
              'rawCube': raw, 'rawOutwardTriangles': int(np.count_nonzero(sign > 0)), 'rawInwardTriangles': int(np.count_nonzero(sign < 0)),
              'fixtureOrientationControl': {'equalDirectionTwoFaceEdges': corrected['equalDirectionTwoFaceEdges'], 'volume': float(control.volume)},
              'localArchiveSHA256': sha(output / 'cube.npz'), 'modelRuns': 0, 'garmentArraysReadOrChanged': False,
              'inference': 'Known valid cube positions/closed connectivity still emerge with inconsistent orientation; denoising steps are absent from this assembly test.',
              'limits': ['Does not compare CUDA implementation or claim a Mac-only regression',
                         'No actual garment normal repair or extra visual comparison',
                         'Does not prove all dense garment contours are normals-only or qualify a new model run']}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
