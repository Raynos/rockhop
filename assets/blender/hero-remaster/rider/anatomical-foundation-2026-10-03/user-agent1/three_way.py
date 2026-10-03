"""Freeze a weight-only diagnostic and exact shared source/Three.js pose driver.

The source stays immutable. True action-off fixtures and sampled forward/reverse
SLERP stress are separate from actual bike-supported or physics-driven motion.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--evidence', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out, evidence = map(lambda p: Path(p).resolve(), [a.source, a.out, a.evidence])
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
if (out / 'conditioned.blend').exists():
    raise RuntimeError('Frozen diagnostic exists; choose another output leaf')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


source_hash = sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
rig.animation_data_clear()
scene = bpy.context.scene
roles = list(rig.data.bones.keys())
runtime_roles = ['pelvis', 'spine', 'chest', 'neck', 'head'] + [
    role + '.' + side for side in ['L', 'R']
    for role in ['shoulder', 'upperArm', 'forearm', 'hand', 'thigh', 'shin', 'foot']]
assert len(runtime_roles) == 19 and set(runtime_roles).issubset(roles)
objects = {
    'body': bpy.data.objects['Canonical anatomical body, baked adult hm08'],
    'cloth': bpy.data.objects['Separate fitted sweatshirt control, hood not constructed'],
    'jeans': bpy.data.objects['Separate fitted native trousers control'],
    'boxers': bpy.data.objects['Opaque boxer fitting garment'],
}
converted = {}
weight_rows = []
for region, obj in objects.items():
    original_name = obj.name
    obj.name = 'Full native diagnostic ' + region
    derived = obj.copy()
    derived.data = obj.data.copy()
    derived.name = original_name
    bpy.context.collection.objects.link(derived)
    original_vertices = np.array([tuple(v.co) for v in obj.data.vertices])
    original_faces = [list(f.vertices) for f in obj.data.polygons]
    deform_groups = {g.index: g.name for g in obj.vertex_groups if g.name in roles}
    sparse, retained, discarded, maximum, changed = [], [], [], 0, 0
    for v in obj.data.vertices:
        weights = sorted([(deform_groups[g.group], float(g.weight)) for g in v.groups
                          if g.group in deform_groups and g.weight > 0],
                         key=lambda pair: (-pair[1], roles.index(pair[0])))
        total = sum(w for _, w in weights)
        assert total > 0, (region, v.index)
        keep = weights[:4]
        keep_total = sum(w for _, w in keep)
        normalized = [(n, w / keep_total) for n, w in keep]
        sparse.append(weights)
        retained.append(normalized)
        discarded.append((total - keep_total) / total)
        maximum = max(maximum, len(weights))
        changed += len(weights) > 4
        for g in derived.vertex_groups:
            if g.name in roles:
                g.remove([v.index])
        for name, weight in normalized:
            derived.vertex_groups[name].add([v.index], weight, 'REPLACE')
    attr = derived.data.attributes.new('_SOURCE_ID', 'FLOAT', 'POINT')
    for item, v in zip(attr.data, derived.data.vertices):
        item.value = v.index
    assert np.array_equal(original_vertices, np.array([tuple(v.co) for v in derived.data.vertices]))
    assert original_faces == [list(f.vertices) for f in derived.data.polygons]
    for mod in derived.modifiers:
        if mod.type == 'ARMATURE':
            assert mod.object == rig and not mod.use_deform_preserve_volume
    obj.hide_render = True
    converted[region] = derived
    weight_rows.append({'region': region, 'nativeName': obj.name, 'exportName': derived.name,
        'vertices': len(sparse), 'maximumNativeInfluences': maximum,
        'verticesWithDiscardedInfluences': changed,
        'discardedNormalizedMassMax': max(discarded),
        'discardedNormalizedMassMean': float(np.mean(discarded)),
        'geometryPositionsSHA256': hashlib.sha256(original_vertices.astype('<f8').tobytes()).hexdigest(),
        'facesSHA256': hashlib.sha256(json.dumps(original_faces).encode()).hexdigest(),
        'nativeSparseWeights': sparse, 'conditionedSparseWeights': retained,
        'discardedNormalizedMassPerVertex': discarded})

# Native matrices are Blender +X forward/+Z up/-Y left, metres.
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def reset():
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def aim(name, direction):
    pb = rig.pose.bones[name]
    current = pb.matrix.to_quaternion()
    turn = (current @ Vector((0, 1, 0))).rotation_difference(Vector(direction).normalized())
    target = (turn @ current).to_matrix().to_4x4()
    target.translation = pb.matrix.translation
    pb.matrix = target
    bpy.context.view_layer.update()


def world_rotation(name, axis, degrees):
    local_axis = rig.data.bones[name].matrix_local.to_3x3().inverted() @ Vector(axis)
    rig.pose.bones[name].rotation_quaternion = Quaternion(local_axis.normalized(), math.radians(degrees))
    bpy.context.view_layer.update()


poses = {}


def record(label):
    poses[label] = {pb.name: {'location': list(pb.location),
        'quaternionWXYZ': list(pb.rotation_quaternion), 'scale': list(pb.scale)} for pb in rig.pose.bones}


reset()
record('native_rest')
for label, down in [('true_A', -.7071067811865476), ('true_T', 0),
                    ('true_neutral', -.984807753012208), ('raised', .9659258262890683)]:
    reset()
    for side in ['L', 'R']:
        lateral = math.sqrt(1 - down * down) * (-1 if side == 'L' else 1)
        for role in ['upperArm', 'forearm', 'hand']:
            aim(role + '.' + side, (0, lateral, down))
    record(label)
reset()
for side in ['L', 'R']:
    for role in ['upperArm', 'forearm', 'hand']:
        aim(role + '.' + side, (1, 0, 0))
record('forward_reach')
for side in ['L', 'R']:
    for role in ['forearm', 'hand']:
        aim(role + '.' + side, (0, 0, 1))
record('bent_elbows')
reset()
aim('upperArm.L', (.3, -.3, .9))
aim('forearm.L', (1, 0, 0))
world_rotation('forearm.R', (0, 1, 0), 70)
record('asymmetric')
for label, hip, knee, drop, chest in [('squat', -55, 90, -.35, 18),
                                    ('forward_standing_FK', -20, 30, -.10, 35),
                                    ('back_seated_FK', -75, 100, -.40, 12)]:
    reset()
    rig.pose.bones['pelvis'].location.z = drop
    for side in ['L', 'R']:
        world_rotation('thigh.' + side, (0, 1, 0), hip)
        world_rotation('shin.' + side, (0, 1, 0), knee)
        aim('upperArm.' + side, (1, 0, -.1))
        aim('forearm.' + side, (1, 0, .1))
    world_rotation('chest', (0, 1, 0), chest)
    record(label)


def set_pose(row):
    for name, trs in row.items():
        pb = rig.pose.bones[name]
        pb.location = trs['location']
        pb.rotation_quaternion = trs['quaternionWXYZ']
        pb.scale = trs['scale']
    bpy.context.view_layer.update()


def mesh_world(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vv = np.array([tuple(C @ evaluated.matrix_world @ v.co) for v in mesh.vertices], dtype='<f8')
    evaluated.to_mesh_clear()
    return vv


# Each 0.5-second segment is sampled at 48 Hz, including the reverse path.
sequence = ['native_rest', 'true_A', 'true_T', 'true_neutral', 'forward_reach',
            'bent_elbows', 'raised', 'asymmetric', 'squat',
            'forward_standing_FK', 'back_seated_FK', 'native_rest']
sequence += sequence[-2::-1]
streams = {(kind, region): (evidence / f'{region}-{kind}.f64').open('wb')
           for kind in ['native-full', 'native-four'] for region in objects}
frames = []
for index in range((len(sequence) - 1) * 24 + 1):
    segment = min(index // 24, len(sequence) - 2)
    t = (index - segment * 24) / 24
    label0, label1 = sequence[segment:segment + 2]
    row = {}
    for name in roles:
        p0, p1 = poses[label0][name], poses[label1][name]
        row[name] = {'location': list(Vector(p0['location']).lerp(Vector(p1['location']), t)),
            'quaternionWXYZ': list(Quaternion(p0['quaternionWXYZ']).slerp(Quaternion(p1['quaternionWXYZ']), t)),
            'scale': list(Vector(p0['scale']).lerp(Vector(p1['scale']), t))}
    set_pose(row)
    # glTF rotates the armature root into Y-up but retains each bone's native
    # local basis (local +Y still runs along the bone). Do not conjugate it.
    world = {pb.name: C @ rig.matrix_world @ pb.matrix for pb in rig.pose.bones}
    frame = {'index': index, 'timeS': index / 48, 'segment': [label0, label1],
             'fraction': t, 'endpoint': (label0 if t == 0 else label1 if t == 1 else None),
             'jointWorldColumnMajor': {n: [m[r][c] for c in range(4) for r in range(4)] for n, m in world.items()},
             'poseBasisBlender': row}
    frames.append(frame)
    for region, obj in objects.items():
        streams['native-full', region].write(mesh_world(obj).tobytes())
        streams['native-four', region].write(mesh_world(converted[region]).tobytes())
    if index % 96 == 0:
        print('SHARED_DRIVER_SAMPLE', index, flush=True)
for stream in streams.values():
    stream.close()

reset()
for obj in objects.values():
    obj.hide_render = True
for region, obj in converted.items():
    obj.hide_render = region == 'boxers'
bpy.ops.object.select_all(action='DESELECT')
for obj in [root, rig, *converted.values()]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'conditioned.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'conditioned.glb'), export_format='GLB',
    use_selection=True, export_yup=True, export_animations=False, export_attributes=True,
    export_extras=True, export_all_influences=False)
assert sha(source) == source_hash
(evidence / 'weights.json').write_text(json.dumps({'rows': weight_rows}, separators=(',', ':')) + '\n')
driver = {'status': 'UNACCEPTED weight-only diagnostic; FK riding is not bike support',
    'sourceSHA256': source_hash, 'conditionedMasterSHA256': sha(out / 'conditioned.blend'),
    'conditionedGLBSHA256': sha(out / 'conditioned.glb'), 'recipeSHA256': sha(__file__),
    'meshRows': [{k: v for k, v in r.items() if not k.endswith('Weights') and not k.endswith('PerVertex')} for r in weight_rows],
    'jointOrderNative': roles, 'runtimeRoles19': runtime_roles,
    'hierarchy': {b.name: b.parent.name if b.parent else None for b in rig.data.bones},
    'restBonesBlender': {b.name: {'head': list(b.head_local), 'tail': list(b.tail_local),
        'matrixRows': [list(row) for row in b.matrix_local]} for b in rig.data.bones},
    'nonboneRootBlender': [list(row) for row in root.matrix_world],
    'axes': 'Blender +Xforward/+Zup/-Yleft; glTF +Xforward/+Yup/+Zleft; metres',
    'runtimeWrapper': 'NONE for comparison: file root +0.65 retained in BOTH samples; normal game wrapper -0.65',
    'runtimeConditioning': 'unmodified exported weights; normal-game sleeve conditioning measured separately',
    'sampling': {'fps': 48, 'segmentS': .5, 'sequence': sequence, 'frames': len(frames),
        'driver': 'Quaternion shortest-path SLERP plus linear location/scale; exact joint world matrices in file frame; action off'},
    'binaryLayout': 'IEEE754 Float64 little endian, [frame,nativeVertexID,xyz], glTF world metres, no header',
    'fixtures': poses, 'frames': frames,
    'pins': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(evidence.glob('*.f64'))},
    'limits': ['Finite sampled trajectory does not certify all unsampled times.',
        'Forward/back FK extremes test deformation, not real grip/peg/saddle support.',
        'Plain top-four agreement cannot accept shoulder/elbow construction or likeness.',
        'Native gray head remains fitting control; no approved donor integration.']}
(evidence / 'driver.json').write_text(json.dumps(driver, separators=(',', ':')) + '\n')
print('THREE_WAY_READY', driver['conditionedGLBSHA256'], len(frames), flush=True)
