# Same existing Agent2 workflow, new item input pins only. No installed edits.
# Parent recipes remain byte-preserved; see recipe-lineage.json for provenance.
"""Actual installed xatlas and CPU renderer preservation on frozen garment."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mesh', required=True)
    parser.add_argument('--mesh-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.mesh) == args.mesh_sha256
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    sys.path.insert(0, '/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/hy3dpaint')
    import torch
    import trimesh
    from utils.uvwrap_utils import mesh_uv_wrap
    from DifferentiableRenderer.MeshRender import MeshRender
    from paint_geometry_getter import preserve_getter_state
    torch.set_num_threads(4)
    with np.load(args.mesh, allow_pickle=False) as archive:
        vertices, faces = archive['vertices'].copy(), archive['faces'][:, ::-1].copy()
    started = time.monotonic()
    mesh = trimesh.Trimesh(vertices=vertices.copy(), faces=faces.copy(), process=False)
    wrapped = mesh_uv_wrap(mesh)
    same_shape = wrapped.faces.shape == faces.shape
    identical_triangles = same_shape and np.array_equal(wrapped.vertices[wrapped.faces], vertices[faces])
    report = {'accepted': False, 'modelRuns': 0, 'inputSHA256': sha(args.mesh),
              'recipeSHA256': sha(__file__), 'UVWrapSourceSHA256': sha(inspect.getfile(mesh_uv_wrap)),
              'originalVertices': len(vertices), 'originalFaces': len(faces),
              'wrappedVertices': len(wrapped.vertices), 'wrappedFaces': len(wrapped.faces),
              'wrappedUVShape': list(wrapped.visual.uv.shape), 'wrappedUVFinite': bool(np.isfinite(wrapped.visual.uv).all()),
              'UVWrapTriangleCoordinatesIdentical': bool(identical_triangles),
              'UVWrapSeconds': time.monotonic() - started,
              'limits': ['No remesh, simplification, source edits, paint inference or asset acceptance.',
                         'Fail before painting if UV wrapping changes triangle coordinates or count.']}
    def save():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    np.savez_compressed(out / 'wrapped.npz', vertices=np.asarray(wrapped.vertices), faces=np.asarray(wrapped.faces),
                        uv=np.asarray(wrapped.visual.uv))
    report['wrappedSHA256'] = sha(out / 'wrapped.npz')
    save()
    assert identical_triangles and report['wrappedUVFinite'], 'UV topology/geometry changed; retain result, no paint'
    renderer = MeshRender(default_resolution=32, texture_size=32, device='cpu')
    renderer.load_mesh(wrapped)
    preserve_getter_state(renderer)
    before_v, before_uv = renderer.vtx_pos.clone(), renderer.vtx_uv.clone()
    for _ in range(2):
        output = renderer.uv_inpaint(torch.full((32, 32, 3), .5), np.full((32, 32), 255, dtype=np.uint8))
        assert np.isfinite(output).all()
        assert torch.equal(renderer.vtx_pos, before_v) and torch.equal(renderer.vtx_uv, before_uv)
    returned_v, returned_f, returned_uv, returned_uvf = renderer.get_mesh(normalize=False)
    error = float(np.max(np.abs(returned_v[returned_f] - vertices[faces])))
    report.update(rendererSourceSHA256=sha(inspect.getfile(MeshRender)),
                  copiedGetterSHA256=sha(Path(__file__).with_name('paint_geometry_getter.py')),
                  actualTwoInpaintCallsPreserveState=True, exportIndicesIdentical=bool(np.array_equal(returned_f, wrapped.faces)),
                  maxExportTriangleCoordinateError=error, elapsedSeconds=time.monotonic() - started)
    save()
    assert report['exportIndicesIdentical'] and error < 3e-7
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
