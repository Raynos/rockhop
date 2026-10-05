"""Silent read-only body05 film of the exact saved grounded02 pose stream.

Every forward30Hz endpoint is retained. Clip boundaries are cuts; each clip
plays continuously. The source is never saved and this diagnostic accepts no
art, geometry, contact, normal, engine, bike or device gate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'source-sha256', 'poses', 'poses-sha256', 'out']:
    parser.add_argument('--' + name, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, poses_path, out = [Path(getattr(args, name)).resolve()
                           for name in ['source', 'poses', 'out']]
assert not out.exists(), 'Fresh output only; no overwrite'
assert sha(source) == args.source_sha256
assert sha(poses_path) == args.poses_sha256
stream = json.loads(poses_path.read_text())
assert stream['hz'] == 30 and len(stream['records']) == 688
assert stream['driverSHA256'] == 'ca43ca11eaca6025d528c3ab5c70c6887429308db3bcdc112d75e40cf0c48297'
rows = [(index, row) for index, row in enumerate(stream['records'])
        if row['direction'] == 'forward']
assert len(rows) == 344
expected = {'idle': 61, 'crouch': 76, 'jump-land': 70, 'walk': 76, 'jog': 61}
assert list(stream['clips']) == list(expected)
for clip, count in expected.items():
    samples = [row for _, row in rows if row['clip'] == clip]
    assert len(samples) == count
    assert [row['sampleIdentity'] for row in samples] == list(range(count))
    assert all(abs(row['timeS'] - i / 30) < 1e-12 for i, row in enumerate(samples))

bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.context.window.scene = scene
rig = bpy.data.objects['Finish rig']
bpy.context.view_layer.update()
names = [bone.name for bone in rig.data.bones]
assert len(names) == 51
assert all(list(row['poseBasis']) == names for _, row in rows)
rest = {bone.name: [list(v) for v in bone.matrix_local] for bone in rig.data.bones}
rig_world = [list(v) for v in rig.matrix_world]
rest_digest = hashlib.sha256(json.dumps({'names': names, 'rest': rest,
    'rigWorld': rig_world}, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
rig.animation_data_clear()
rig.hide_set(False)
rig.hide_viewport = False
for bone in rig.pose.bones:
    for constraint in bone.constraints:
        constraint.mute = True
    bone.rotation_mode = 'QUATERNION'
    bone.scale = (1, 1, 1)

visible = ['Finish body FOUR', 'Finish head FOUR', 'Finish boxer FOUR', 'Finish coherent cheek']
for obj in scene.objects:
    obj.hide_set(False)
    if obj.type == 'MESH':
        obj.hide_render = obj.name not in visible
    if obj.name in visible:
        obj.hide_viewport = False
        assert not obj.data.shape_keys
        obj.animation_data_clear()
scene.view_layers[0].material_override = None

world = bpy.data.worlds.new('Grounded diagnostic world')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.28, .31, .35, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
scene.world = world

# One world-Z=0 plane. Its shader grid marks fixed half-metre cells.
bpy.ops.mesh.primitive_plane_add(size=16, location=(2.65, 0, 0))
floor = bpy.context.object
floor.name = 'Fixed world zero floor with half-metre grid'
material = bpy.data.materials.new('Fixed half-metre floor grid')
material.use_nodes = True
nodes, links = material.node_tree.nodes, material.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Roughness'].default_value = .85
position = nodes.new('ShaderNodeNewGeometry')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(position.outputs['Position'], separate.inputs['Vector'])
stripes = []
for axis in ['X', 'Y']:
    modulo = nodes.new('ShaderNodeMath'); modulo.operation = 'FLOORED_MODULO'
    modulo.inputs[1].default_value = .5
    links.new(separate.outputs[axis], modulo.inputs[0])
    narrow = nodes.new('ShaderNodeMath'); narrow.operation = 'LESS_THAN'
    narrow.inputs[1].default_value = .008
    links.new(modulo.outputs[0], narrow.inputs[0]); stripes.append(narrow)
combine = nodes.new('ShaderNodeMath'); combine.operation = 'MAXIMUM'
for i, stripe in enumerate(stripes):
    links.new(stripe.outputs[0], combine.inputs[i])
mix = nodes.new('ShaderNodeMixRGB')
mix.inputs[1].default_value = (.17, .19, .21, 1)
mix.inputs[2].default_value = (.32, .35, .38, 1)
links.new(combine.outputs[0], mix.inputs[0])
links.new(mix.outputs[0], shader.inputs['Base Color'])
floor.data.materials.append(material)

base_target = Vector((.65, 0, .98))
camera_data = bpy.data.cameras.new('Front root-X-follow diagnostic camera')
camera = bpy.data.objects.new(camera_data.name, camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'; camera_data.ortho_scale = 2.65
base_camera = base_target + Vector((5, 0, .6))
camera.rotation_euler = (base_target - base_camera).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
for name, pos, power, size in [('Key', (4, -3.4, 4.3), 650, 5),
                              ('Fill', (3, 3.3, 2.7), 420, 5),
                              ('Rim', (-2.5, 0, 3.2), 550, 5)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power; data.shape = 'DISK'; data.size = size
    light = bpy.data.objects.new(name, data); scene.collection.objects.link(light)
    light.location = pos
    light.rotation_euler = (base_target-light.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640; scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.render.fps = 30
out.mkdir(parents=True)
frames = out / 'frames'; frames.mkdir()


def pose_bytes(pose):
    values = [value for name in names for field in ['location', 'quaternionWXYZ']
              for value in pose[name][field]]
    assert all(math.isfinite(value) for value in values)
    # This is the original sampler's signed-zero-only serialization rule.
    return struct.pack('<' + 'd' * len(values), *(0.0 if value == 0 else value for value in values))


metadata = {'status': 'UNACCEPTED_GROUNDED_FRONT_PBR_DIAGNOSTIC',
    'source': str(source), 'sourceSHA256': sha(source),
    'poseStream': str(poses_path), 'poseStreamSHA256': sha(poses_path),
    'poseStreamSourceSHA256': stream['sourceSHA256'],
    'driverSHA256': stream['driverSHA256'], 'readerSHA256': stream['readerSHA256'],
    'recipeSHA256': sha(__file__), 'blender': bpy.app.version_string,
    'boneOrder': names, 'immutableRestWorld': {'restRows': rest, 'rigWorldRows': rig_world,
        'sha256': rest_digest}, 'visibleMeshes': visible,
    'resolution': [640, 640], 'fps': 30, 'frameCount': len(rows),
    'clipForwardSamples': expected, 'cameraNativeYawDegrees': 0,
    'cameraFollow': 'Evaluated pelvis world-X delta only; fixed Y/Z/rotation/scale.',
    'cameraBaseLocationNativeM': list(base_camera), 'cameraTargetNativeM': list(base_target),
    'cameraOrthoScaleM': camera_data.ortho_scale, 'floorWorldZ': 0,
    'gridSpacingM': .5, 'sourceSaved': False, 'perFrame': [],
    'limits': ['Inherited body/boxer contacts and moving-normal failures remain visible and unresolved.',
        'Grounded02 was measured on body04d; exact unchanged51 pose replay does not transfer its sole/contact metrics to body05.',
        'Five separate clips have declared cuts; uninterrupted original30Hz samples within each clip, including endpoints.',
        '344 discrete frames play for344/30 seconds; authored clip durations sum11.3s and include five endpoint frames.',
        'Walk travels2.5m and jog4m; camera follows worldX only. No source normalization or floor/foot correction.',
        'Actual pose properties are checked byte-for-byte after assignment; no synthetic FK or neural poses.',
        'No art, geometry, support, export/engine/GPU, bike, phone or promotion pass. Parent alone judges played evidence.']}
(out / 'render-input.json').write_text(json.dumps(metadata, indent=2) + '\n')
rest_root = (rig.matrix_world @ rig.data.bones['pelvis'].matrix_local).translation
for frame, (record_index, row) in enumerate(rows):
    for name in names:
        bone = rig.pose.bones[name]; pose = row['poseBasis'][name]
        bone.location = pose['location']; bone.rotation_quaternion = pose['quaternionWXYZ']
    bpy.context.view_layer.update()
    actual = {bone.name: {'location': list(bone.location),
                         'quaternionWXYZ': list(bone.rotation_quaternion)} for bone in rig.pose.bones}
    expected_bytes = pose_bytes(row['poseBasis'])
    assert pose_bytes(actual) == expected_bytes, 'Assigned actual pose properties must match saved sample bytes'
    root_x = (rig.matrix_world @ rig.pose.bones['pelvis'].matrix).translation.x-rest_root.x
    assert abs(root_x-row['rootOffsetNativeM'][0]) < 2e-6
    camera.location = base_camera + Vector((root_x, 0, 0))
    bpy.context.view_layer.update()
    path = frames / f'{frame:04d}.png'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    assert path.is_file() and path.stat().st_size > 0
    metadata['perFrame'].append({'frame': frame, 'recordIndex': record_index,
        'clip': row['clip'], 'sampleIdentity': row['sampleIdentity'], 'timeS': row['timeS'],
        'supportPhase': row['supportPhase'], 'poseBasisSHA256': hashlib.sha256(expected_bytes).hexdigest(),
        'actualAssignmentBytesExact': True, 'cameraRootXFollowM': root_x,
        'cameraWorldRows': [list(v) for v in camera.matrix_world], 'pngSHA256': sha(path)})
    (out / 'progress.json').write_text(json.dumps({'framesDone': frame+1, 'framesTotal': len(rows),
        'clip': row['clip'], 'sampleIdentity': row['sampleIdentity']}) + '\n')
    if frame % 12 == 0:
        print('GROUNDED_FRAME', frame+1, len(rows), row['clip'], row['timeS'], flush=True)
assert rest == {bone.name: [list(v) for v in bone.matrix_local] for bone in rig.data.bones}
assert rig_world == [list(v) for v in rig.matrix_world]
assert sha(source) == args.source_sha256 and sha(poses_path) == args.poses_sha256
metadata.update(status='UNACCEPTED_RENDERED344_FORWARD_FRAMES_ENCODING_PENDING',
                sourcePinsStillExact=True, actualPoseBasisBytesExactAll344=True,
                original51RestWorldExact=True)
(out / 'render-receipt.json').write_text(json.dumps(metadata, indent=2) + '\n')
print('GROUNDED_RENDER_READY', len(rows), flush=True)
