"""Actual source/brow GLB reimport comparison, eight views each, CPU2."""
import hashlib
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

R = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-head-brows/trial02')
E.mkdir(parents=True, exist_ok=True)
assert not (E / 'renders.json').exists()
rows = []
sources = [('source', R / 'head-cleanup/mpfb-v8-palette/african/head.glb'),
           ('brows', R / 'autonomous-head-brows/trial02/head.glb')]
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
for label, source in sources:
    before = sha(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Recorded gray diagnostic studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .12, .12, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .45
    scene.world = world
    target = Vector((0, -.02, .08))
    lights = [('Key', (1.6, -2.5, 2.2), 180, 2),
              ('Fill', (-1.6, -1.6, 1), 90, 2),
              ('Rim', (.6, 2, 1.5), 100, 2)]
    for name, location, power, size in lights:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy = power
        data.size = size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Recorded native face framing')
    data.type = 'ORTHO'
    data.ortho_scale = .76
    camera = bpy.data.objects.new('Recorded native face framing', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    gray = bpy.data.materials.new('Diagnostic override, master untouched')
    gray.use_nodes = True
    shader = gray.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.42, .42, .42, 1)
    shader.inputs['Roughness'].default_value = .65
    for mode in ['pbr', 'gray']:
        bpy.context.view_layer.material_override = gray if mode == 'gray' else None
        for yaw, name in [(0, 'front'), (45, 'three-quarter'), (90, 'profile'), (180, 'rear')]:
            angle = math.radians(yaw)
            camera.location = target + Vector((3 * math.sin(angle), -3 * math.cos(angle), 0))
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = E / f'{label}-{mode}-{name}.png'
            assert not path.exists()
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rows.append({'label': label, 'mode': mode, 'yaw': yaw, 'file': path.name,
                         'SHA256': sha(path), 'cameraMatrix': [list(r) for r in camera.matrix_world]})
    assert sha(source) == before
(E / 'renders.json').write_text(json.dumps({'status': 'Diagnostic only; parent independent face judgment required',
    'Blender': bpy.app.version_string, 'backend': 'Cycles CPU', 'threads': 2,
    'samples': 16, 'resolution': [640, 640], 'orthoScale': .76, 'target': list(target),
    'lights': lights, 'sources': {str(p): sha(p) for _, p in sources}, 'views': rows,
    'limits': ['No calibrated imagegen camera/light match', 'No rig or neck motion',
               'No master retouching or geometry/material edits during render']}, indent=2) + '\n')
