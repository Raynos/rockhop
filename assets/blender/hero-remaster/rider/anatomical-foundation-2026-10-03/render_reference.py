"""Render actual modest anatomical input geometry; no shape/appearance judgment."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--obj', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(a.obj).resolve(), Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(source), forward_axis='Y', up_axis='Z')
for obj in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    mat = bpy.data.materials.new(obj.name + ' reference')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    boxer = 'boxer' in obj.name.lower()
    bsdf.inputs['Base Color'].default_value = (.025, .035, .05, 1) if boxer else (.5, .5, .5, 1)
    bsdf.inputs['Roughness'].default_value = .7
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
world = bpy.data.worlds.new('Canonical fitting reference')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .12, .12, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .8
bpy.context.scene.world = world
for name, pos, energy in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size = energy, 4
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Exact geometric source')
camera = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(camera)
data.type, data.ortho_scale = 'ORTHO', 2.05
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 8
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 4
scene.render.resolution_x, scene.render.resolution_y = 480, 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
views = []
for index, yaw in enumerate(range(0, 360, 45)):
    r = math.radians(yaw)
    target = Vector((0, 0, .92))
    camera.location = target + Vector((5 * math.cos(r), 5 * math.sin(r), .02))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(out / f'A-yaw-{yaw:03d}.png')
    bpy.ops.render.render(write_still=True)
    views.append({'yawDegrees': yaw, 'cameraBlenderM': list(camera.location),
        'orthoScaleM': data.ortho_scale, 'path': scene.render.filepath,
        'sha256': hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest()})
assert sha == hashlib.sha256(source.read_bytes()).hexdigest()
(out / 'render-contract.json').write_text(json.dumps({'sourceOBJ': str(source), 'sourceSHA256': sha,
    'status': 'Generation/fitting input only; not visual acceptance', 'views': views,
    'limits': 'Gray native face is not approved identity. Modest opaque boxers; body has no garment fusion.'}, indent=2) + '\n')
