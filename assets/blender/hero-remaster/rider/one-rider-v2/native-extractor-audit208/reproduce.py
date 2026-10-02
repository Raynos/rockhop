#!/usr/bin/env python3
"""CPU-only synthetic extractor audit; does not import Torch or Hunyuan."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import skimage
import trimesh
from skimage import measure

ROOT = Path('/Users/raynos/projects/games/rockhop')
OUT = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/native-extractor-audit208'
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/native-extractor-audit208')
SOURCE = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/hy3dshape/hy3dshape')


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    xyz = np.indices((12, 12, 12)).astype(np.float32)
    sphere = np.sqrt(((xyz - np.float32(5.5)) ** 2).sum(axis=0)) - np.float32(3)
    one_nan = sphere.copy()
    one_nan[3, 3, 3] = np.nan
    grids = {'finite': sphere, 'nan_exterior': np.where(sphere > 1, np.nan, sphere),
             'nan_one': one_nan, 'inf_exterior': np.where(sphere > 1, np.inf, sphere)}
    cases = []
    for name, grid in grids.items():
        # Match MCSurfaceExtractor's direct Lewiner call, before bounds scaling.
        vertices, faces, normals, values = measure.marching_cubes(grid, 0, method='lewiner')
        finite_vertices = np.isfinite(vertices).all(axis=1)
        valid_faces = finite_vertices[faces].all(axis=1)
        path = PRIVATE / (name + '.npz')
        np.savez_compressed(path, inputGrid=grid, vertices=vertices, faces=faces,
                            normals=normals, values=values)
        # Diagnostic only. Preserve pre-Trimesh arrays above; do not export it.
        mesh = trimesh.Trimesh(vertices.copy(), faces.copy())
        cases.append({'name': name, 'gridShape': list(grid.shape),
                      'nonfiniteGrid': int((~np.isfinite(grid)).sum()),
                      'vertices': len(vertices), 'faces': len(faces),
                      'nonfiniteVertices': int((~finite_vertices).sum()),
                      'facesUsingNonfiniteVertices': int((~valid_faces).sum()),
                      'nonfiniteNormals': int((~np.isfinite(normals).all(axis=1)).sum()),
                      'nonfiniteValues': int((~np.isfinite(values)).sum()),
                      'defaultTrimeshVertices': len(mesh.vertices),
                      'defaultTrimeshFaces': len(mesh.faces),
                      'defaultTrimeshNonfiniteVertices': int((~np.isfinite(mesh.vertices).all(axis=1)).sum()),
                      'arrays': pin(path)})
    assert 'torch' not in sys.modules
    report = {'status': 'SYNTHETIC_MECHANISM_CONFIRMED_ACTUAL_207_CAUSE_UNASSESSED',
              'scope': 'CPU source audit and synthetic scalar fields; no model execution',
              'python': sys.version, 'numpy': np.__version__, 'skimage': skimage.__version__,
              'trimesh': trimesh.__version__, 'torchImported': False,
              'cases': cases,
              'sources': [pin(SOURCE / p) for p in [
                  'models/autoencoders/volume_decoders.py',
                  'models/autoencoders/surface_extractors.py',
                  'models/autoencoders/model.py', 'pipelines.py',
                  'models/autoencoders/attention_blocks.py',
                  'models/autoencoders/attention_processors.py']],
              'limitations': [
                  'No native207 grid, arrays or diagnostic report were inspected.',
                  'Synthetic array units are grid cells, not rider metres.',
                  'An exterior NaN sentinel is demonstrated; infinity did not make nonfinite vertex positions in this fixture.',
                  'Default Trimesh cleanup counts do not establish retained anatomy or surface completeness.',
                  'Dense same-latent decoding is a proposed alternative, not an executed repair.']}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'cases': cases, 'torchImported': False}, indent=2))


if __name__ == '__main__':
    main()
