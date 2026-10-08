"""Read-only saved failed hoodie frame/skin readback. Parent runs CPU2 only.

blender -b -t 2 --python-exit-code 1 --python probe-source-pose.py -- OUT.json
No save, fitting, reweighting, bind or render.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
NATIVE = ROOT/'harness/out/rider-rebuild/shoulder-cage05/authored01/selected-cage-outfit.blend'
NATIVE_SHA = 'a0e7f1e54a533a306630fb7fd9ec21e659b3a2f92b6ad03fa430de1659194c97'
CONTROLS = ROOT/'assets/blender/rider-rebuild/shoulder-cage05/controls.json'


def frame(head, tail):
    head = Vector(head)
    result = (Vector(tail)-head).to_track_quat('Y', 'Z').to_matrix().to_4x4()
    result.translation = head
    return result


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    out = Path(args[0]).resolve(); assert not out.exists()
    assert hashlib.sha256(NATIVE.read_bytes()).hexdigest() == NATIVE_SHA
    controls = json.loads(CONTROLS.read_text())
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    source = bpy.data.objects['Hoodie__OriginalSelectedPBR_EditableSourcePoseAid05']
    result = bpy.data.objects['Hoodie__ActualSelectedPBR_Cage05']
    rig = bpy.data.objects['Hoodie_SourcePoseAuthoringAid7_NOT_FINAL_RIG']
    report = {'accepted': False, 'nativeSHA256': NATIVE_SHA,
              'sourceObjectWorld': [list(row) for row in source.matrix_world],
              'derivativeObjectWorld': [list(row) for row in result.matrix_world],
              'rigWorld': [list(row) for row in rig.matrix_world], 'bones': [], 'samples': []}
    for row in controls['authoringBones']:
        bone, pose = rig.data.bones[row['name']], rig.pose.bones[row['name']]
        wanted = frame(row['sourceHead'], row['sourceTail'])
        report['bones'].append({'name': bone.name, 'sourceHead': row['sourceHead'],
            'sourceTail': row['sourceTail'], 'actualRestHead': list(bone.head_local),
            'actualRestTail': list(bone.tail_local), 'actualRest': [list(r) for r in bone.matrix_local],
            'sourceFrameMaximumResidual': max(abs(wanted[i][j]-bone.matrix_local[i][j]) for i in range(4) for j in range(4)),
            'actualPose': [list(r) for r in pose.matrix],
            'sourceTargetHeadDeltaM': (pose.matrix.translation-Vector(row['sourceHead'])).length})
    raw = (ROOT/controls['originalDensePBR']['path']).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]; gltf = json.loads(raw[20:20+size])
    accessor = gltf['accessors'][gltf['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    view = gltf['bufferViews'][accessor['bufferView']]
    positions = np.ndarray((accessor['count'], 3), dtype='<f4', buffer=raw,
        offset=28+size+view.get('byteOffset', 0)+accessor.get('byteOffset', 0),
        strides=(view.get('byteStride', 12), 4))
    axis = Matrix(controls['gltfToBlenderRows'])
    names = {g.index: g.name for g in source.vertex_groups}
    chosen = {}
    for vertex in source.data.vertices:
        rows = [(names[g.group], g.weight) for g in vertex.groups if g.weight > 0]
        name, maximum = max(rows, key=lambda r: r[1])
        if maximum > .99 and len(chosen.setdefault(name, [])) < 4:
            chosen[name].append(vertex.index)
    for index in [i for rows in chosen.values() for i in rows]:
        vertex = source.data.vertices[index]
        start = source.matrix_world@vertex.co
        stored = result.matrix_world@result.data.vertices[index].co
        linear = Vector((0,0,0))
        weights = []
        for group in vertex.groups:
            if group.weight <= 0: continue
            name = names[group.group]; weights.append([name, group.weight])
            deform = rig.matrix_world@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@rig.matrix_world.inverted()
            linear += (deform@start)*group.weight
        report['samples'].append({'vertex': index, 'weights': weights,
            'importedVsActualGLBPositionResidualM': (vertex.co-axis@Vector(positions[index])).length,
            'originalWorld': list(start), 'storedDerivativeWorld': list(stored),
            'expectedLinearWorld': list(linear), 'storedVsLinearResidualM': (stored-linear).length,
            'storedWorldDelta': list(stored-start), 'linearWorldDelta': list(linear-start)})
    report['armaturePreserveVolume'] = [m.use_deform_preserve_volume for m in source.modifiers if m.type == 'ARMATURE']
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'report': str(out), 'samples': len(report['samples']),
        'restFrameResidualMaximum': max(r['sourceFrameMaximumResidual'] for r in report['bones']),
        'storedVsLinearResidualMaximumM': max(r['storedVsLinearResidualM'] for r in report['samples'])}), flush=True)


if __name__ == '__main__': main()
