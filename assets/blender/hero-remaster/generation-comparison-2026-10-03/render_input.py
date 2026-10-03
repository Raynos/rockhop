"""Render pinned canonical anatomy with real alpha; no image synthesis or edits."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--obj', required=True)
parser.add_argument('--sha256', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, output = Path(args.obj).resolve(), Path(args.out).resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest() == args.sha256
output.mkdir(parents=True, exist_ok=True)
assert not (output / 'input-contract.json').exists()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(source), forward_axis='Y', up_axis='Z')
for obj in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    material = bpy.data.materials.new(obj.name + ' gray fitting reference')
    material.use_nodes = True
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (.025, .035, .05, 1) if 'boxer' in obj.name.lower() else (.5, .5, .5, 1)
    shader.inputs['Roughness'].default_value = .7
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
world = bpy.data.worlds.new('Gray reference lighting')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .12, .12, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .8
scene = bpy.context.scene
scene.world = world
for name, pos, energy in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size = energy, 4
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = pos
    light.rotation_euler = (Vector((0, 0, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Canonical A alpha source')
camera = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(camera)
data.type, data.ortho_scale = 'ORTHO', 2.05
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 8
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 4
scene.render.resolution_x, scene.render.resolution_y = 480, 640
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'AgX'
views = []
for yaw in range(0, 360, 45):
    target = Vector((0, 0, .92))
    radians = math.radians(yaw)
    camera.location = target + Vector((5 * math.cos(radians), 5 * math.sin(radians), .02))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    path = output / f'body-boxers-A-{yaw:03d}.png'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    views.append({'yawDegrees': yaw, 'cameraBlenderM': list(camera.location),
                  'orthoScaleM': data.ortho_scale, 'path': str(path),
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
assert hashlib.sha256(source.read_bytes()).hexdigest() == args.sha256
(output / 'input-contract.json').write_text(json.dumps({
    'accepted': False, 'sourceOBJ': str(source), 'sourceSHA256': args.sha256,
    'axes': 'Blender +X forward, +Z up, -Y game-left; metres; OBJ centered X=0',
    'pose': 'True straight-arm 45 degree A', 'heightM': 1.822571873664856,
    'alpha': 'Rendered geometry alpha, no remover or synthesized pixels',
    'identity': 'Gray stock fitting face is unaccepted; immutable approved head retained separately',
    'views': views, 'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
}, indent=2) + '\n')
