"""Read actual selected fitted coordinates only; no evaluation or model write.

Parent serial CPU2 command:
Blender -b -t 2 --python-exit-code 1 --python extract.py -- FRESH_OUTPUT
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
NATIVE = ROOT / 'harness/out/rider-rebuild/production-authoring01/conditioned-neck02/editable-real-source-outfit.blend'
NATIVE_SHA = '860d310b639e36e8093d63c6aaf3075a123d03dcbed0557aa99b5a65db80c5b6'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/glove-anatomical04')
    assert not out.exists() and sha(NATIVE) == NATIVE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75
    assert rig.matrix_world.is_identity
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'operation': 'READ_ONLY_FITTED_MESH_EXTRACTION',
              'native': {'path': str(NATIVE.relative_to(ROOT)), 'sha256': NATIVE_SHA},
              'recipeSHA256': sha(__file__), 'hands': {},
              'evaluatedMesh': False, 'blendWritten': False, 'modelMutation': False}
    for side in ('R', 'L'):
        obj = bpy.data.objects['Gloves__SelectedFittedSource.' + side]
        mesh = obj.data
        assert not obj.modifiers and all(len(p.vertices) == 3 for p in mesh.polygons)
        vertices = np.empty((len(mesh.vertices), 3), dtype=np.float64)
        mesh.vertices.foreach_get('co', vertices.ravel())
        matrix = np.asarray(obj.matrix_world, dtype=np.float64)
        vertices = vertices @ matrix[:3, :3].T + matrix[:3, 3]
        triangles = np.empty((len(mesh.polygons), 3), dtype=np.int32)
        mesh.polygons.foreach_get('vertices', triangles.ravel())
        uv = np.empty((len(mesh.loops), 2), dtype=np.float32)
        mesh.uv_layers.active.data.foreach_get('uv', uv.ravel())
        path = out / ('fitted-' + side + '.npz')
        np.savez_compressed(path, vertices=vertices, faces=triangles,
                            blenderCornerUV=uv.reshape(-1, 3, 2),
                            matrixWorld=matrix)
        report['hands'][side] = {'object': obj.name, 'vertices': len(vertices),
                                 'triangles': len(triangles),
                                 'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                                 'bounds': [vertices.min(0).tolist(), vertices.max(0).tolist()]}
    (out / 'extract.json').write_text(json.dumps(report, indent=2) + '\n')
    assert sha(NATIVE) == NATIVE_SHA
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
