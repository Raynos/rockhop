"""Parent-only bounded original47 read: actual glove41 guides and named skin.

No save or mutation. Blender --background --threads 2 --python-exit-code 1
--python extract.py -- OUT. The parent owns the native resource guard.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
COMPONENT = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/component.py',
             'sha256': '6fcc124b1fe5cf69a3cd0cd4114ff3fc16b6bd3e7741fb4b2b7488648c6bbd87'}
RECEIPT = {'path': 'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json',
           'sha256': '55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): digest.update(block)
    return digest.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], row
    return path


def main(output):
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    receipt = json.loads(checked(RECEIPT).read_text())
    component = runpy.run_path(str(checked(COMPONENT)))
    component_receipt = component['intake_gate'](receipt)
    helpers, geometry = component['helpers'](json.loads(checked(receipt['priorInput']).read_text()))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])), use_scripts=False) == {'FINISHED'}
    rig = component['scoped'](bpy)
    assert component['canonical'](helpers['rest'](rig)) == receipt['expectedRest']
    assert geometry(bpy.data.objects['RiderHoodie']) == receipt['expectedHoodieGeometry']
    data, witnesses = {}, {}
    for name in ('ActualSelectedGlove.L', 'ActualSelectedGlove.R'):
        obj = bpy.data.objects[name]
        assert obj.matrix_world.is_identity
        obj.data.calc_loop_triangles()
        positions = np.empty((len(obj.data.vertices), 3), np.float32)
        faces = np.empty((len(obj.data.loop_triangles), 3), np.int32)
        obj.data.vertices.foreach_get('co', positions.ravel())
        obj.data.loop_triangles.foreach_get('vertices', faces.ravel())
        data[name+'_positions'], data[name+'_triangles'] = positions, faces
        witnesses[name] = geometry(obj)
        assert witnesses[name] == component_receipt['expectedConstructedGeometry'][name]
    source = bpy.data.objects['RiderHoodie']
    names = [group.name for group in source.vertex_groups]
    # CSR preserves every original named field, including more than four weights.
    offsets, indices, weights = [0], [], []
    for vertex in source.data.vertices:
        for group in vertex.groups:
            indices.append(group.group); weights.append(group.weight)
        offsets.append(len(indices))
    data.update(groupNames=np.asarray(names), fieldOffsets=np.asarray(offsets, np.int64),
                fieldIndices=np.asarray(indices, np.int32), fieldWeights=np.asarray(weights, np.float32))
    output.mkdir(parents=True)
    np.savez(output/'actual-guides.npz', **data)
    report = {'status': 'ACTUAL47_GLOVE41_AND_HOODIE_FIELD_CACHE', 'acceptedArt': False,
              'recipe': pin(__file__), 'sourceReceipt': RECEIPT, 'component': COMPONENT,
              'native': receipt['native'], 'arrays': pin(output/'actual-guides.npz'),
              'gloveGeometry': witnesses, 'hoodieGeometry': receipt['expectedHoodieGeometry'],
              'rest': receipt['expectedRest'], 'nativeMutation': False,
              'arrayHashes': {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in data.items()}}
    (output/'actual-guides.json').write_text(json.dumps(report, indent=2)+'\n')
    print(report['status'], flush=True)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--')+1])
