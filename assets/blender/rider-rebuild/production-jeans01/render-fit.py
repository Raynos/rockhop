"""Read-only rest-fit diagnosis of the actual saved authored jeans.

blender -b -t 2 --python-exit-code 1 --python render-fit.py -- NATIVE SHA OUT
The complete visible wearer is retained. These stills cannot pass moving art.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
native, expected, output = sys.argv[sys.argv.index('--') + 1:]
native, output = Path(native).resolve(), Path(output).resolve()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(native) == expected
assert output.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans01')
output.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(native))
body, jeans, rig = [bpy.data.objects[n] for n in ('RiderBody', 'RiderJeans', 'RiderSkeleton')]
assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
assert jeans.get('productionJeansRecipe') == 'rockhop-authored-selected-jeans-v1'
assert not body.hide_render and not body.hide_viewport and not body.hide_get()
inventory = []
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj.hide_render = obj not in (body, jeans)
        inventory.append({'name': obj.name, 'vertices': len(obj.data.vertices),
                          'polygons': len(obj.data.polygons),
                          'rendered': not obj.hide_render})
jeans.hide_render = False
jeans.hide_set(False)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('JeansActualFitReviewWorld')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .55
scene.world = world


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


for label, position, energy in [('Key', (2, -3, 4), 650),
                                ('Fill', (-3, -2, 2), 450),
                                ('Rim', (0, 3, 3), 700)]:
    data = bpy.data.lights.new(label, 'AREA')
    data.energy, data.size = energy, 3
    light = bpy.data.objects.new(label, data)
    scene.collection.objects.link(light)
    light.location = position
    aim(light, (0, 0, .65))
camera = bpy.data.objects.new('JeansActualFitCamera', bpy.data.cameras.new('JeansActualFitCamera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type, camera.data.ortho_scale = 'ORTHO', 1.2
photos = []
for label, position in [('front', (1.1, -3, .9)), ('back', (-1.1, 3, .9)),
                        ('profile', (3, 0, .9))]:
    camera.location = position
    aim(camera, (0, 0, .55))
    path = output / (label + '.png')
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    photos.append({'path': str(path), 'sha256': sha(path)})
assert sha(native) == expected
(output / 'receipt.json').write_text(json.dumps({
    'accepted': False, 'native': {'path': str(native), 'sha256': expected},
    'rendererSHA256': sha(Path(__file__)), 'savedMeshInventory': inventory,
    'completeBodyVisible': True, 'photos': photos,
    'limits': ['Rest-fit diagnosis only; no positive moving-art judgment.',
               'Actual selected dense maps are not baked yet.',
               'No source native modified, no player asset exported.']}, indent=2) + '\n')
