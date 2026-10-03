"""Matched native before/after corrective films, played continuous shared sweep."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'driver', 'expanded', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, dp, ep, out = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'expanded', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
driver, expanded = json.loads(dp.read_text()), json.loads(ep.read_text())
assert sha(source) == expanded['masterSHA256'] and sha(dp) == expanded['poseDriverSHA256']
out.mkdir(parents=True, exist_ok=True)
if (out / 'native-review.json').exists():
    raise RuntimeError('Frozen native capture exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.hide_render = obj not in [objects[r] for r in ['body', 'cloth', 'jeans']]
scene = bpy.context.scene
world = bpy.data.worlds.new('Identical local corrective review studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.11, .11, .11, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65
scene.world = world
lights = []
for name, pos, power in [('Key', (4, -4, 5), 450), ('Fill', (3, 4, 4), 350), ('Rim', (-3, 0, 4), 400)]:
    data = bpy.data.lights.new(name, 'AREA'); data.energy, data.size = power, 4
    obj = bpy.data.objects.new(name, data); bpy.context.collection.objects.link(obj)
    obj.location = Vector(pos) + Vector((.65, 0, 0)); obj.rotation_euler = (Vector((.65, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    lights.append({'name': name, 'positionM': list(obj.location), 'watts': power, 'sizeM': 4})
data = bpy.data.cameras.new('Identical before/after 3Q camera')
camera = bpy.data.objects.new(data.name, data); bpy.context.collection.objects.link(camera)
data.type, data.ortho_scale = 'ORTHO', 1.9
scene.camera = camera
scene.render.engine = 'CYCLES'; scene.cycles.device, scene.cycles.samples = 'CPU', 4
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 4
scene.render.resolution_x, scene.render.resolution_y = 512, 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
indices = list(range(0, len(driver['frames']), 4)); views = []
for label, yaw in [('front3q', -45), ('rear3q', -135)]:
    angle = math.radians(yaw); target = Vector((.65, 0, 1.20))
    camera.location = target + Vector((4 * math.cos(angle), 4 * math.sin(angle), 0))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    folders = {name: out / (label + '-' + name) for name in ['before', 'after']}
    for path in folders.values():
        path.mkdir(exist_ok=True)
    for number, index in enumerate(indices):
        frame = driver['frames'][index]
        for name, trs in frame['poseBasisBlender'].items():
            pb = rig.pose.bones[name]
            pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
        for state in ['before', 'after']:
            for config in expanded['configs']:
                obj = objects[config['region']]
                for name in config['keys']:
                    obj.data.shape_keys.key_blocks[name].value = expanded['frames'][index]['coefficients'][config['region']][name] if state == 'after' else 0
            bpy.context.view_layer.update()
            scene.render.filepath = str(folders[state] / f'{number:04d}.png')
            bpy.ops.render.render(write_still=True)
        if number % 12 == 0:
            print('LOCAL_CORRECTIVE_PLAYED', label, number, index, flush=True)
    views.append({'name': label, 'yawDegrees': yaw, 'cameraBlenderWorldM': list(camera.location),
        'cameraMatrixBlenderRows': [list(row) for row in camera.matrix_world],
        'orthoHorizontalM': 1.9, 'orthoVerticalM': 2.85, 'targetBlenderM': list(target),
        'folders': {name: str(path) for name, path in folders.items()}})
assert sha(source) == expanded['masterSHA256'] and sha(dp) == expanded['poseDriverSHA256']
report = {'status': 'UNACCEPTED matched native before/after played corrective review; root judges',
    'masterSHA256': sha(source), 'poseDriverSHA256': sha(dp), 'expandedDriverSHA256': sha(ep), 'recipeSHA256': sha(__file__),
    'framesPerFilm': len(indices), 'fps': 12, 'driverFrameIndices': indices, 'views': views, 'lights': lights,
    'panelOrder': 'BeforeLEFT/afterRIGHT; same camera/lights/original full body and native-four garment weights, ONLY morph coefficients differ',
    'render': {'engine': 'CyclesCPU', 'threads': 4, 'samples': 4, 'singlePanelResolution': [512, 768], 'filmResolution': [1024, 768]},
    'limits': ['Synthetic sharedFKmotion not supportedbike/physics play.',
        'Selected source-ID local volume prototype only; remaining local/global contacts/held-out regression still open.',
        'Gray head/native flat structural wardrobe colors are fitting control, not identity/PBR approval.',
        'Normalplayer assets/source inputs unchanged; no audio, no production promotion.']}
(out / 'native-review.json').write_text(json.dumps(report, indent=2) + '\n')
print('LOCAL_CORRECTIVE_FILMS_READY', sha(out / 'native-review.json'), flush=True)
