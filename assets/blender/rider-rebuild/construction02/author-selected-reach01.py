"""Author reach, grip and release on the verified complete selected outfit."""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index('--') + 1:]
source = Path(args[0]).resolve()
out = Path(args[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
contract_path = source.parent / 'rider-contract.json'
contract = json.loads(contract_path.read_text())
(out / 'input-receipt.json').write_text(json.dumps({
    'accepted': False,
    'inputs': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in [Path(__file__).resolve(), source, contract_path]],
    'context': 'Generic authored action; never actual bike/physics evidence.'}, indent=2) + '\n')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['RiderSkeleton']
rig.animation_data_clear()
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 193
action = bpy.data.actions.new('RiderStandReachGripRelease')
rig.animation_data_create()
rig.animation_data.action = action
names = [b.name for b in rig.data.bones]
assert len(names) == 75
assert set(names) == set(contract['specification']['jointNames'])
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
rest_heads = {b.name: b.head_local.copy() for b in rig.data.bones}
meshes = [obj for obj in scene.objects if obj.type == 'MESH' and obj.parent == rig]
expected = {'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}
assert {o.name for o in meshes} == expected, 'Complete selected source required for dressed animation'
assert hashlib.sha256((source.parent / 'rider.glb').read_bytes()).hexdigest() == contract['glbSHA256']
for obj in meshes:
    assert not obj.hide_render and not obj.hide_viewport
    assert obj.data.attributes.get('_NATIVE_ID') is not None
    assert all(material and material.use_nodes for material in obj.data.materials)
    for vertex in obj.data.vertices:
        values = [group.weight for group in vertex.groups if group.weight > 0]
        assert 1 <= len(values) <= 4 and all(value > .0001 for value in values)
        assert sum(values) == 1, 'Final canonical fields required before animation'



def reset():
    for name in names:
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def smooth(x):
    x = max(0, min(1, x))
    return x*x*(3 - 2*x)


def phases(frame):
    reach = smooth((frame - 25) / 48) if frame <= 169 else 1 - smooth((frame - 169) / 24)
    grip = smooth((frame - 97) / 24) if frame <= 145 else 1 - smooth((frame - 145) / 24)
    return reach, grip


def set_world_rotation(name, rotation):
    bone = rig.pose.bones[name]
    matrix = rotation.to_matrix().to_4x4()
    matrix.translation = bone.matrix.translation.copy()
    bone.matrix = matrix
    bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def aim(group, end, direction):
    axis = (rest_heads[end] - rest_heads[group[0]]).normalized()
    swing = axis.rotation_difference(direction.normalized())
    for name in group:
        set_world_rotation(name, swing @ rest[name].to_quaternion())


def basis(forward, normal):
    x = forward.normalized()
    y = (normal - x * normal.dot(x)).normalized()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()


palms = {}
lengths = {}
for side, suffix, sign in [('left', 'L', 1), ('right', 'R', -1)]:
    hand = contract['specification']['hands'][side]
    wrist = hand['wristJointId']
    forward = (rest_heads[hand['forwardJointId']] - rest_heads[wrist]).normalized()
    radial = rest_heads[hand['radialJointId']] - rest_heads[hand['ulnarJointId']]
    normal = forward.cross(radial).normalized() * hand['normalSign']
    alignment = basis(Vector((0, -1, -.15)), Vector((0, 0, -1))) @ basis(forward, normal).inverted()
    palms[side] = alignment.to_quaternion() @ rest[wrist].to_quaternion()
    upper, lower = 'DEF-upper_arm.' + suffix, 'DEF-forearm.' + suffix
    lengths[side] = [(rest_heads[lower] - rest_heads[upper]).length,
                     (rest_heads[wrist] - rest_heads[lower]).length]


def pose(frame):
    reset()
    reach, grip = phases(frame)
    if reach == 0 and grip == 0: return reach, grip
    for side, suffix, sign in [('left', 'L', 1), ('right', 'R', -1)]:
        upper, lower, wrist = ['DEF-' + stem + '.' + suffix for stem in ['upper_arm', 'forearm', 'hand']]
        start = rig.pose.bones[upper].matrix.translation.copy()
        target = rest_heads[wrist].lerp(Vector((sign * .22, -.49, 1.40)), reach)
        pole_point = rest_heads[lower].lerp(Vector((sign * .36, -.20, 1.17)), reach)
        ray = target - start
        distance = ray.length
        ray.normalize()
        pole = pole_point - start
        pole = (pole - ray * pole.dot(ray)).normalized()
        a, b = lengths[side]
        assert abs(a-b) < distance < a+b, (frame, side, distance, a+b)
        along = (a*a + distance*distance - b*b) / (2*distance)
        elbow = start + ray * along + pole * math.sqrt(max(0, a*a - along*along))
        aim([upper, 'DEF-upper_arm.' + suffix + '.001'], lower, elbow-start)
        aim([lower, 'DEF-forearm.' + suffix + '.001'], wrist, target-elbow)
        set_world_rotation(wrist, rest[wrist].to_quaternion().slerp(palms[side], reach))
        for name, flex in contract['driver']['digitFlex'][side].items():
            bone = rig.pose.bones[name]
            bone.rotation_quaternion = Quaternion(Vector(flex['axisLocal']), grip * flex['maxRadians'])
    bpy.context.view_layer.update()
    return reach, grip


measurements = []
for frame in range(1, 194):
    scene.frame_set(frame)
    reach, grip = pose(frame)
    for name in names:
        bone = rig.pose.bones[name]
        for prop in ['location', 'rotation_quaternion', 'scale']:
            bone.keyframe_insert(data_path=prop, frame=frame, group=name)
    if frame in [1, 25, 73, 97, 121, 145, 169, 193]:
        observations = {}
        for side, suffix in [('left', 'L'), ('right', 'R')]:
            points = [rig.pose.bones['DEF-' + stem + '.' + suffix].matrix.translation.copy()
                      for stem in ['upper_arm', 'forearm', 'hand']]
            actual = [(points[1]-points[0]).length, (points[2]-points[1]).length]
            assert max(abs(a-b) for a, b in zip(actual, lengths[side])) < .0001
            observations[side] = {'segmentLengthsMetres': actual, 'wrist': list(points[2])}
        measurements.append({'frame': frame, 'reach': reach, 'grip': grip, 'arms': observations})

samples = {}
for frame in [1, 73, 121, 193]:
    scene.frame_set(frame)
    pose(frame)
    graph = bpy.context.evaluated_depsgraph_get()
    samples[frame] = {o.name: [v.co.copy() for v in o.evaluated_get(graph).data.vertices] for o in meshes}
for name in samples[1]:
    assert len(samples[1][name]) == len(samples[193][name])
return_error = max((a-b).length for name in samples[1]
                   for a, b in zip(samples[1][name], samples[193][name]))
assert return_error < .0001, return_error
scene.frame_set(1)
pose(1)
bpy.ops.object.select_all(action='DESELECT')
rig.hide_set(False)
rig.select_set(True)
for obj in meshes:
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'rider-generic.blend'))
bpy.ops.export_scene.gltf(filepath=str(out / 'rider.glb'), export_format='GLB', use_selection=True,
    export_animations=True, export_animation_mode='ACTIVE_ACTIONS', export_force_sampling=True,
    export_nla_strips_merged_animation_name='RiderStandReachGripRelease',
    export_bake_animation=True, export_optimize_animation_size=False,
    export_optimize_animation_keep_anim_armature=True, export_def_bones=True, export_skins=True,
    export_influence_nb=4, export_all_influences=False, export_apply=True,
    export_yup=True, export_attributes=True)
raw = (out / 'rider.glb').read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
gltf = json.loads(raw[20:20+size])
contract['glbSHA256'] = hashlib.sha256(raw).hexdigest()
contract['exportedObjectMeshes'] = [
    {'nodeIndex': i, 'nodeName': node.get('name'), 'meshIndex': node['mesh'],
     'meshName': gltf['meshes'][node['mesh']].get('name'),
     'primitiveCount': len(gltf['meshes'][node['mesh']]['primitives'])}
    for i, node in enumerate(gltf['nodes']) if 'mesh' in node]
contract['genericAction'] = {'name': action.name, 'seconds': 8, 'context': 'authored generic, not actual physics'}
(out / 'rider-contract.json').write_text(json.dumps(contract, indent=2) + '\n')
report = {'accepted': False, 'action': action.name, 'fps': 24, 'frames': 193,
          'resetJointsEveryAuthoredFrame': 75, 'allLocalTRSKeyedEveryFrame': True,
          'glbSHA256': contract['glbSHA256'], 'glbBytes': len(raw),
          'animationNames': [a.get('name') for a in gltf.get('animations', [])],
          'animationChannelCounts': [len(a['channels']) for a in gltf.get('animations', [])],
          'returnMaxVertexErrorMetres': return_error, 'samples': measurements,
          'meshNames': [o.name for o in meshes], 'sourceArmLengthsMetres': lengths,
          'limits': ['Authored generic movement, never played bike evidence.',
                     'No art, anatomical envelope, grip contact or native/GPU moving parity acceptance.',
                     'Canonical selected source fields/materials retained; independent exact exported readback required.']}
assert report['animationNames'] == ['RiderStandReachGripRelease'], report['animationNames']
assert report['animationChannelCounts'] == [225], report['animationChannelCounts']
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
