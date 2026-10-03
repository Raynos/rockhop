"""Continuous matched skin/cloth-off/cloth-on films from immutable simulated streams."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--comparison', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); folder = Path(a.comparison).resolve(); out = folder / 'review'; out.mkdir(exist_ok=True)
if (out / 'review.json').exists():
    raise RuntimeError('Frozen collision review exists')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs = ['comparison.json', 'collision-off.json', 'comparison-streams.npz', 'collision-off-streams.npz', 'engine-handoff.json']; pins = {name: sha(folder / name) for name in inputs}
on, off = np.load(folder / 'comparison-streams.npz'), np.load(folder / 'collision-off-streams.npz'); descriptor = json.loads((folder / 'engine-handoff.json').read_text())
assert len(on['skin']) == len(off['collisionOff']) == 49
arm = descriptor['nativeConsumedColliders']['body']; used = [row['bodyVertexID'] for row in arm['relevantArmVertices']]; lookup = {old: new for new, old in enumerate(used)}
body_faces = [[lookup[i] for i in t['bodyVertexIDs']] for t in arm['relevantArmTriangles']]
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene
world = bpy.data.worlds.new('Neutral matched fabric review'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.10, .10, .10, 1); world.node_tree.nodes['Background'].inputs[1].default_value = .6; scene.world = world
def material(name, color, roughness):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = roughness; b.inputs['Specular IOR Level'].default_value = .125; return m
fabric = material('Same neutral fabric all variants', (.27, .32, .39), .85); skin = material('Same canonical arm all variants', (.46, .38, .29), .75)
white = bpy.data.materials.new('White diagnostic labels'); white.use_nodes = True; nt = white.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (1, 1, 1, 1); o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs['Surface'])
variants = [('SKIN ONLY', on['skin'], -.60), ('CLOTH COLLISION OFF', off['collisionOff'], 0.), ('CLOTH COLLISION ON', on['collision'], .60)]
objects = []
for label, data, shift in variants:
    for name, verts, faces, mat in [('fabric', data[0], on['patchFaces'], fabric), ('canonical arm', on['body'][0][used], body_faces, skin)]:
        mesh = bpy.data.meshes.new(label + name); mesh.from_pydata(verts.tolist(), [], faces.tolist() if hasattr(faces, 'tolist') else faces); mesh.update()
        obj = bpy.data.objects.new(label + name, mesh); bpy.context.collection.objects.link(obj); obj.location.y = shift; mesh.materials.append(mat)
        for p in mesh.polygons:
            p.use_smooth = True
        objects.append((obj, data if name == 'fabric' else on['body'][:, used], shift))
all_points = np.concatenate([data.reshape(-1, 3) + np.array([0, shift, 0]) for o, data, shift in objects]); lower, upper = all_points.min(0), all_points.max(0)
target = Vector((lower + upper) / 2); vertical = max(upper[2] - lower[2] + .25, (upper[1] - lower[1] + .18) / (1280 / 720))
camera_data = bpy.data.cameras.new('Matched collision camera'); camera_data.type = 'ORTHO'; camera_data.ortho_scale = vertical * 1280/720
camera = bpy.data.objects.new(camera_data.name, camera_data); bpy.context.collection.objects.link(camera); scene.camera = camera
for name, pos, energy in [('Key', (3, -3, 4), 400), ('Fill', (-3, 3, 4), 400)]:
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.size = 4; obj = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(obj); obj.location = pos
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
text = bpy.data.curves.new('Legend', 'FONT'); text.size = .029; legend = bpy.data.objects.new('Legend', text); bpy.context.collection.objects.link(legend); legend.parent = camera
legend.location = (-vertical * 1280/720 * .48, vertical * .44, -2); text.materials.append(white)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 4; scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'; scene.render.threads = 2; scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'; frames = []; number = 0; minimum = 1.
for view, sign in [('front', 1), ('rear', -1)]:
    camera.location = target + Vector((3 * sign, 0, .08)); camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    ordered_labels = [v[0] for v in variants] if sign == 1 else [v[0] for v in variants][::-1]
    for index in range(49):
        for o, data, shift in objects:
            for v, point in zip(o.data.vertices, data[index]):
                v.co = point
            o.data.update()
        text.body = 'LEFT: ' + ordered_labels[0] + '  /  CENTER: ' + ordered_labels[1] + '  /  RIGHT: ' + ordered_labels[2] + '\nSAME REST / PINS / BODY / CLOTH SETTINGS; OFF DISABLES ONLY BODY+SELF COLLISION\n' + view.upper() + '   simulation t=' + format(index/24, '.3f') + 's / display slowed2x / LOCAL TEST UNACCEPTED'
        bpy.context.view_layer.update(); border = 1.
        for o, data, shift in objects:
            for v in o.data.vertices:
                q = world_to_camera_view(scene, camera, o.matrix_world @ v.co); border = min(border, q.x, q.y, 1-q.x, 1-q.y)
        assert border >= 0, (view, index, border); minimum = min(minimum, border)
        p = out / f'{number:04d}.png'; scene.render.filepath = str(p); bpy.ops.render.render(write_still=True)
        frames.append({'displayFrame': number, 'simulationFrame': index+1, 'timeS': index/24, 'view': view, 'PNG_SHA256': sha(p), 'minimumNormalizedBorder': border}); number += 1
        if index % 12 == 0:
            print('SLEEVE_COLLISION_PLAYED', view, index, flush=True)
assert pins == {name: sha(folder / name) for name in inputs}
report = {'status': 'UNACCEPTED continuous matched collision-off/on plus skinned-control fabric review; parent judges',
    'pins': pins, 'recipeSHA256': sha(__file__), 'frames': frames, 'FPS': 12, 'resolution': [1280, 720], 'minimumNormalizedBorder': minimum,
    'render': 'CyclesCPU2threads4samples', 'nativeCameraTargetM': list(target), 'orthoVerticalM': vertical,
    'limits': ['Local sleeve only; body rendering is exact relevant native arm triangles, full body was used by simulation collider.',
        'No cosmetic recoloring between variants and no posed art decision. Playback2x slower than simulated24Hz; raw time is recorded.',
        'Native consumed collision response is not automatically a live game GLB behavior; actual engine/mobile validation remains required.']}
(out / 'review.json').write_text(json.dumps(report, indent=2) + '\n'); print('SLEEVE_COLLISION_REVIEW_READY', sha(out / 'review.json'), flush=True)
