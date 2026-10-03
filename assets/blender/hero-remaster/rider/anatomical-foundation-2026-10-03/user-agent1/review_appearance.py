"""Continuous textured whole-rider native replay; bike-free, never seated proof."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'driver', 'expanded', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, dp, ep, out = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'expanded', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in [source, dp, ep]}
driver, expanded = json.loads(dp.read_text()), json.loads(ep.read_text())
out.mkdir(parents=True, exist_ok=True)
if (out / 'native-review.json').exists():
    raise RuntimeError('Frozen capture exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
visible = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
assert len(visible) == 8, [o.name for o in visible]
for o in list(bpy.data.objects):
    if o.type in ['LIGHT', 'CAMERA']:
        bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
world = bpy.data.worlds.new('Pinned textured appearance review studio'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.11, .11, .11, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65; scene.world = world
lights = []
for name, pos, power in [('Key', (4, -4, 5), 450), ('Fill', (3, 4, 4), 350), ('Rim', (-3, 0, 4), 400)]:
    data = bpy.data.lights.new(name, 'AREA'); data.energy, data.size = power, 4
    o = bpy.data.objects.new(name, data); bpy.context.collection.objects.link(o)
    o.location = Vector(pos) + Vector((.65, 0, 0)); o.rotation_euler = (Vector((.65, 0, 1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    lights.append({'name': name, 'positionM': list(o.location), 'watts': power, 'sizeM': 4})
data = bpy.data.cameras.new('Pinned textured whole-rider 3Q camera'); camera = bpy.data.objects.new(data.name, data); bpy.context.collection.objects.link(camera)
data.type, data.ortho_scale = 'ORTHO', 3.15; scene.camera = camera
scene.render.engine = 'CYCLES'; scene.cycles.device, scene.cycles.samples = 'CPU', 4; scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x, scene.render.resolution_y = 512, 768; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
indices = list(range(0, len(driver['frames']), 4)); views = []
for label, yaw in [('front3q', -45), ('rear3q', -135)]:
    angle = math.radians(yaw); target = Vector((.65, 0, 1.15)); camera.location = target + Vector((4 * math.cos(angle), 4 * math.sin(angle), 0))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    folder = out / label; folder.mkdir(exist_ok=True); minimum_border = 1.; frames = []
    for number, index in enumerate(indices):
        frame = driver['frames'][index]
        for name, trs in frame['poseBasisBlender'].items():
            pb = rig.pose.bones[name]; pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
        for config in expanded['configs']:
            o = objects[config['region']]
            for name in config['keys']:
                o.data.shape_keys.key_blocks[name].value = expanded['frames'][index]['coefficients'][config['region']][name]
        bpy.context.view_layer.update()
        # All evaluated head, garment, hand and foot vertices participate in bounds.
        border = 1.; deps = bpy.context.evaluated_depsgraph_get()
        for o in visible:
            evaluated = o.evaluated_get(deps); mesh = evaluated.to_mesh()
            for v in mesh.vertices:
                q = world_to_camera_view(scene, camera, evaluated.matrix_world @ v.co)
                border = min(border, q.x, q.y, 1 - q.x, 1 - q.y)
            evaluated.to_mesh_clear()
        if border < 0:
            raise RuntimeError(f'Whole-rider framing failed {label} f{index}:{border}')
        minimum_border = min(minimum_border, border)
        file = folder / f'{number:04d}.png'; scene.render.filepath = str(file); bpy.ops.render.render(write_still=True)
        frames.append({'displayFrame': number, 'driverFrame': index, 'driverTimeS': frame['timeS'], 'minimumNormalizedBorder': border, 'file': str(file), 'sha256': sha(file)})
        if number % 12 == 0:
            print('APPEARANCE_PLAYED', label, number, index, 'border', border, flush=True)
    views.append({'name': label, 'yawDegrees': yaw, 'cameraMatrixBlenderRows': [list(row) for row in camera.matrix_world],
        'orthoHorizontalM': 2.1, 'orthoVerticalM': 3.15, 'targetBlenderM': list(target), 'folder': str(folder),
        'minimumNormalizedBorder': minimum_border, 'frames': frames})
assert pins == {str(p): sha(p) for p in [source, dp, ep]}
report = {'status': f'UNACCEPTED {source.parent.name} textured whole-rider continuous bike-free synthetic FK review; root judges',
    'pins': pins, 'recipeSHA256': sha(__file__), 'framesPerFilm': len(indices), 'fps': 12, 'driverFrameIndices': indices,
    'visibleObjects': [o.name for o in visible], 'views': views, 'lights': lights,
    'render': {'engine': 'CyclesCPU', 'threads': 2, 'samples': 4, 'resolution': [512, 768]},
    'limits': ['Bike-free pose sweep includes reach/bends/stress; no actual bicycle or seated/contact qualification.',
        'Candidate preserves clothing patterns and local correctives; neckline/hood/glove/boot and full fit remain unaccepted.',
        'Native played film is not export/actual-engine/mobile or production release acceptance; no audio.']}
(out / 'native-review.json').write_text(json.dumps(report, indent=2) + '\n')
print('APPEARANCE_REVIEW_READY', sha(out / 'native-review.json'), flush=True)
