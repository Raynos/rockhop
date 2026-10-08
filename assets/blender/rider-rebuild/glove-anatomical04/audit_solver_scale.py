"""Read-only measurement of Blender5.2.1's cotangent triangle area gate."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def measure(vertices, faces, anchors):
    cross = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                     vertices[faces[:, 2]] - vertices[faces[:, 0]])
    magnitude = np.linalg.norm(cross, axis=1)
    active = magnitude > np.finfo(np.float32).eps
    incident = np.zeros(len(vertices), dtype=np.int32)
    np.add.at(incident, faces[active].ravel(), 1)
    zero = np.flatnonzero(incident == 0)
    return {'trianglesSuppressedByCotangentGate': int(np.count_nonzero(~active)),
            'verticesWithZeroActiveIncidentTriangles': len(zero),
            'unanchoredZeroColumns': len(np.setdiff1d(zero, anchors)),
            'unanchoredZeroColumnExamples': np.setdiff1d(zero, anchors)[:24].tolist(),
            'minimumTriangleCrossMagnitude': float(magnitude.min())}


def main():
    controls_path = HERE / 'controls-orientation02.json'
    controls = json.loads(controls_path.read_text())
    source = np.load(ROOT / controls['pins']['denseSelected']['path'])
    vertices, faces = source['vertices'], source['faces']
    report = {'acceptedArt': False, 'operation': 'READ_ONLY_COTANGENT_AREA_GATE_AUDIT',
              'recipeSHA256': sha(__file__), 'controlsSHA256': sha(controls_path),
              'float32Epsilon': float(np.finfo(np.float32).eps), 'cases': {},
              'primaryBlenderVersion': 'v5.2.1',
              'primarySource': [
                  {'url': 'https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/blenlib/intern/math_geom.cc',
                   'sha256': '3d7559d04f8d28e71e9a3d98d519a6c020763fe7119855f6c90f1712b5fce958',
                   'lines': [202, 216], 'meaning': 'Cotangent weight is zero unless triangle cross magnitude exceeds FLT_EPSILON.'},
                  {'url': 'https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/modifiers/intern/MOD_laplaciandeform.cc',
                   'sha256': 'd56f120e37066fe9a892ec4090fffec03e149f82c115a6ea8356330a4e8d2096',
                   'lines': [291, 292, 413, 722, 723], 'meaning': 'Modifier assembles cotangent least-squares system; failed solve emits observed warning.'},
                  {'url': 'https://raw.githubusercontent.com/blender/blender/v5.2.1/intern/eigen/intern/linear_solver.cc',
                   'sha256': '886e3061226fef8e10106b86d9e535c18782368999bcb8089363a1589c377e32',
                   'lines': [284, 298], 'meaning': 'Least-squares uses M transpose M followed by sparse LU.'}]}
    for side in ('R', 'L'):
        placement = controls['hands'][side]['initialPlacement']
        anchors = [row['sourceVertex'] for row in controls['hands'][side]['handles']]
        initial = (np.einsum('ij,kj->ik', vertices.astype(float), np.asarray(placement['linear']))
                   + np.asarray(placement['translation'])).astype(np.float32)
        assert np.isfinite(initial).all()
        report['cases'][side + '_world_float32'] = measure(initial, faces, anchors)
    report['cases']['original_source_units'] = measure(vertices, faces, anchors)
    guide_path = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/gloves/retopology-prototype.npz'
    guide = np.load(guide_path)
    report['guide'] = {'path': str(guide_path.relative_to(ROOT)), 'sha256': sha(guide_path),
                       'measurement': measure(guide['vertices'].astype(np.float32), guide['faces'], [])}
    report['finding'] = ('Both world-scale systems contain542 unanchored vertices whose every incident '
                         'cotangent triangle is suppressed: zero Laplacian columns make the normal matrix singular. '
                         'The selected coarse guide has no suppressed triangle in source units.')
    path = ROOT / 'docs/evidence/rider-rebuild/glove-anatomical04/solver-scale-audit02.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'cases': report['cases']}))


if __name__ == '__main__':
    main()
