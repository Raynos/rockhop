"""Actual CPU UV inpainting/export coordinate preservation, without weights."""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

import numpy as np


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
    source = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/hy3dpaint')
    sys.path.insert(0, str(source))
    import torch
    import trimesh
    import custom_rasterizer
    from DifferentiableRenderer.MeshRender import MeshRender
    from utils.uvwrap_utils import mesh_uv_wrap
    from paint_geometry_getter import preserve_getter_state
    torch.set_num_threads(4)
    vertices = np.array([[-.37, -.21, -.11], [.53, -.18, -.04], [.02, .64, .09], [.07, .03, .78]], dtype=np.float32)
    faces = np.array([[0, 2, 1], [0, 1, 3], [1, 2, 3], [2, 0, 3]], dtype=np.int32)
    wrapped = mesh_uv_wrap(trimesh.Trimesh(vertices=vertices.copy(), faces=faces.copy(), process=False))
    assert np.array_equal(wrapped.vertices[wrapped.faces], vertices[faces])
    report = {'accepted': False, 'modelRuns': 0, 'recipeSHA256': sha(__file__),
              'adapterSHA256': sha(Path(__file__).with_name('paint_geometry_getter.py')),
              'sourceFiles': {str(p.relative_to(source)): sha(p) for p in [Path(inspect.getfile(MeshRender)),
                              source / 'utils/uvwrap_utils.py', source / 'DifferentiableRenderer/mesh_utils.py']},
              'rasterizerSource': inspect.getfile(custom_rasterizer), 'device': 'cpu',
              'UVWrapTriangleCoordinatesIdentical': True, 'cases': [],
              'limits': ['Known asymmetric tetrahedron, not full garment UV/bake or CUDA parity.',
                         'Owned instance adapter only, no shared source edits or model weights.',
                         'No remesh, simplification, smoothing or triangle deletion.']}
    for name, adapt in [('actualInstalledGetter', False), ('ownedCopiedGetter', True)]:
        # Source load_mesh/set_mesh writes numpy arrays; use a fresh mesh per case.
        mesh = trimesh.Trimesh(vertices=np.asarray(wrapped.vertices).copy(), faces=np.asarray(wrapped.faces).copy(), process=False)
        mesh.visual = trimesh.visual.texture.TextureVisuals(uv=np.asarray(wrapped.visual.uv).copy())
        renderer = MeshRender(default_resolution=32, texture_size=32, device='cpu')
        renderer.load_mesh(mesh)
        if adapt:
            preserve_getter_state(renderer)
        positions_before = renderer.vtx_pos.detach().cpu().numpy().copy()
        uv_before = renderer.vtx_uv.detach().cpu().numpy().copy()
        outputs, states = [], []
        for _ in range(2):
            texture = torch.full((32, 32, 3), .5, dtype=torch.float32)
            mask = np.full((32, 32), 255, dtype=np.uint8)
            output = renderer.uv_inpaint(texture, mask)
            assert np.isfinite(output).all()
            outputs.append(output)
            states.append({'positionsIdentical': bool(np.array_equal(positions_before, renderer.vtx_pos.detach().cpu().numpy())),
                           'UVIdentical': bool(np.array_equal(uv_before, renderer.vtx_uv.detach().cpu().numpy()))})
        positions_after = renderer.vtx_pos.detach().cpu().numpy().copy()
        uv_after = renderer.vtx_uv.detach().cpu().numpy().copy()
        returned = renderer.get_mesh(normalize=False)
        returned_v, returned_f, returned_uv, returned_uvf = returned
        difference = np.max(np.abs(returned_v[returned_f] - vertices[faces]))
        case = {'name': name, 'inpaintCalls': 2,
                'stateAfterEachInpaint': states,
                'positionsUnchangedDuringInpaint': bool(np.array_equal(positions_before, positions_after)),
                'UVUnchangedDuringInpaint': bool(np.array_equal(uv_before, uv_after)),
                'indicesIdentical': bool(np.array_equal(returned_f, wrapped.faces)),
                'maxExportTriangleCoordinateError': float(difference),
                'triangleCount': len(returned_f), 'finiteInpaintImages': True}
        if adapt:
            assert all(state['positionsIdentical'] and state['UVIdentical'] for state in states)
            assert case['positionsUnchangedDuringInpaint'] and case['UVUnchangedDuringInpaint']
            assert case['indicesIdentical'] and difference < 2e-7
        else:
            assert not case['positionsUnchangedDuringInpaint'] and difference > .1
        np.savez_compressed(out / (name + '.npz'), positionsBefore=positions_before, positionsAfter=positions_after,
                            uvBefore=uv_before, uvAfter=uv_after, exportVertices=returned_v, exportFaces=returned_f,
                            exportUV=returned_uv, exportUVFaces=returned_uvf)
        report['cases'].append(case)
    report['ownedPreservationControlPass'] = True
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
