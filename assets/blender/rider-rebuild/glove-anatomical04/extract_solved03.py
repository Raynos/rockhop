"""Bounded read-only actual saved guide/right-result coordinate extraction.

Parent CPU2 lease only. No source/native mutation, fit, bind, render or bake.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'harness/out/rider-rebuild/glove-anatomical04/guide02/guide-sculpt-L.blend'
EXPECTED = 'ce50929296c718dad592b6e320587b1de852187583003b4f74004f46222cc329'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arrays(mesh):
    vertices = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    faces = np.empty((len(mesh.polygons), 3), dtype=np.int32)
    assert all(len(face.vertices) == 3 for face in mesh.polygons)
    mesh.vertices.foreach_get('co', vertices.ravel())
    mesh.polygons.foreach_get('vertices', faces.ravel())
    assert np.isfinite(vertices).all()
    return vertices, faces


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 1
    out = Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/glove-anatomical04')
    assert sha(SOURCE) == EXPECTED
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'operation': 'READ_ONLY_ACTUAL_SOLVED_GUIDE_AND_RIGHT_RESULT_ARRAYS',
              'native': {'path': str(SOURCE.relative_to(ROOT)), 'sha256': EXPECTED},
              'recipeSHA256': sha(__file__), 'arrays': {},
              'nativeWrites': 0, 'bindCalls': 0, 'fits': 0, 'renders': 0}
    graph = bpy.context.evaluated_depsgraph_get()
    for side in ('R', 'L'):
        obj = bpy.data.objects['Gloves__SelectedGuideSculpt.' + side]
        actual = obj.evaluated_get(graph)
        mesh = actual.to_mesh()
        vertices, faces = arrays(mesh)
        assert len(vertices) == 8000 and len(faces) == 16000
        path = out / ('guide-' + side + '.npz')
        np.savez_compressed(path, vertices=vertices, faces=faces,
                            objectMatrix=np.asarray(obj.matrix_world, dtype=np.float64))
        report['arrays']['guide' + side] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                                          'frame': 'original selected source units', 'vertices': len(vertices)}
        actual.to_mesh_clear()
    obj = bpy.data.objects['Gloves__AnatomicallySculptedSelected.R']
    assert obj.matrix_world.is_identity
    vertices, faces = arrays(obj.data)
    assert len(vertices) == 284571 and len(faces) == 569142
    path = out / 'actual-right.npz'
    np.savez_compressed(path, vertices=vertices, faces=faces)
    report['arrays']['actualRight'] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                                      'frame': 'actual saved world units', 'vertices': len(vertices)}
    (out / 'extract.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
