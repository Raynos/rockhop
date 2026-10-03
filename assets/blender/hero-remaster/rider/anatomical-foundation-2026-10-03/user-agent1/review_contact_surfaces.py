"""Play exact05 loader-evaluated contact patches over native motion for label review."""
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
for n in ['source', 'driver', 'expanded', 'map', 'played', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
paths = {n: Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'expanded', 'map', 'played']}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {n: sha(p) for n, p in paths.items()}
surface_map, played, driver, expanded = [json.loads(paths[n].read_text()) for n in ['map', 'played', 'driver', 'expanded']]
assert played['surfaceMapSHA256'] == pins['map'] and played['candidateGLBSHA256'] == surface_map['candidateGLBSHA256']
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
if (out / 'review.json').exists():
    raise RuntimeError('Frozen contact review exists')
bpy.ops.wm.open_mainfile(filepath=str(paths['source']))
rig = bpy.data.objects['Independent anatomical foundation rig']
cloth = bpy.data.objects['Sewn clean hoodie with dropped hood']
jeans = bpy.data.objects['Separate fitted native trousers control']
gear = [bpy.data.objects[n] for n in ['Registered black leather gloves on own finger bind', 'Registered boots from bounded foot accessory regions']]
visible = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
for o in list(bpy.data.objects):
    if o.type in ['LIGHT', 'CAMERA']:
        bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
world = bpy.data.worlds.new('Contact binding review studio'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.07, .07, .07, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65; scene.world = world
for name, position, watts in [('Key', (4, -4, 5), 500), ('Fill', (3, 4, 4), 350), ('Rim', (-3, 0, 4), 450)]:
    d = bpy.data.lights.new(name, 'AREA'); d.energy, d.size = watts, 4
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = Vector(position) + Vector((.65, 0, 0)); o.rotation_euler = (Vector((.65, 0, 1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
d = bpy.data.cameras.new('Contact binding played camera'); camera = bpy.data.objects.new(d.name, d); bpy.context.collection.objects.link(camera)
d.type, d.ortho_scale = 'ORTHO', 3.15; scene.camera = camera
scene.render.engine = 'CYCLES'; scene.cycles.device, scene.cycles.samples = 'CPU', 4; scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x, scene.render.resolution_y = 512, 768; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'

def emission(name, color):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nodes = mat.node_tree.nodes; nodes.clear()
    e = nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = 1
    o = nodes.new('ShaderNodeOutputMaterial'); mat.node_tree.links.new(e.outputs[0], o.inputs['Surface'])
    return mat

patches = {}
for surface in surface_map['surfaces']:
    # Duplicate triangle corners: offset the diagnostic display only, never the binding receipt.
    count = len(surface['triangles'])
    mesh = bpy.data.meshes.new(surface['label']); mesh.from_pydata([(0, 0, 0)] * (count * 3), [], [(i * 3, i * 3 + 1, i * 3 + 2) for i in range(count)])
    o = bpy.data.objects.new(surface['label'], mesh); bpy.context.collection.objects.link(o); o.data.materials.append(emission(surface['label'], surface['color']))
    patches[surface['label']] = (o, {v['vertexID']: i for i, v in enumerate(surface['vertices'])}, surface)
text = bpy.data.curves.new('Contact label legend', 'FONT'); text.size = .048; text.align_x = 'LEFT'
legend = bpy.data.objects.new('Contact label legend', text); bpy.context.collection.objects.link(legend)
legend.parent = camera; legend.location = (-.99, 1.39, -2); legend.data.materials.append(emission('Legend white', (1, 1, 1)))
frames = []; number = 0; minimum = 1
for mode in ['gear', 'underlying body']:
    for o in gear:
        o.hide_render = mode != 'gear'
    jeans.hide_render = mode != 'gear'
    for fi, sampled in enumerate(played['frames']):
        index = sampled['driverFrame']; frame = driver['frames'][index]
        for name, trs in frame['poseBasisBlender'].items():
            pb = rig.pose.bones[name]; pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
        for config in expanded['configs']:
            o = cloth if config['region'] == 'cloth' else jeans
            for name in config['keys']:
                o.data.shape_keys.key_blocks[name].value = expanded['frames'][index]['coefficients'][config['region']][name]
        for stream in sampled['patches']:
            o, lookup, surface = patches[stream['label']]
            o.hide_render = (stream['label'].startswith('body-') if mode == 'gear' else not stream['label'].startswith('body-'))
            world = [Vector((p[0], -p[2], p[1])) for p in stream['positionsFileWorldM']]
            for ti, triangle in enumerate(surface['triangles']):
                p = [world[lookup[v]] for v in triangle['vertexIDs']]
                normal = (p[1] - p[0]).cross(p[2] - p[0]).normalized()
                for k in range(3):
                    o.data.vertices[ti * 3 + k].co = p[k] + normal * .003
            o.data.update()
        yaw = math.radians(-45 - fi / (len(played['frames']) - 1) * 360)
        target = Vector((.65, 0, 1.15)); camera.location = target + Vector((4 * math.cos(yaw), 4 * math.sin(yaw), .15))
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        text.body = '05 CONTACT PATCH PROPOSALS\n' + mode.upper() + ' / frame ' + str(index) + '\nPALMS red L / blue R\nSOLES gold L / green R\nSEAT magenta (gear view)\nDISPLAY OFFSET 3mm / NO CONTACT PASS'
        bpy.context.view_layer.update(); deps = bpy.context.evaluated_depsgraph_get(); border = 1
        for o in visible:
            if o.hide_render:
                continue
            ev = o.evaluated_get(deps); mesh = ev.to_mesh()
            for v in mesh.vertices:
                q = world_to_camera_view(scene, camera, ev.matrix_world @ v.co); border = min(border, q.x, q.y, 1 - q.x, 1 - q.y)
            ev.to_mesh_clear()
        assert border >= 0, (mode, index, border)
        minimum = min(minimum, border)
        file = out / f'{number:04d}.png'; scene.render.filepath = str(file); bpy.ops.render.render(write_still=True)
        frames.append({'displayFrame': number, 'mode': mode, 'driverFrame': index, 'PNG_SHA256': sha(file), 'minimumNormalizedBorder': border})
        number += 1
        if fi % 12 == 0:
            print('CONTACT_PATCH_PLAYED', mode, fi, index, flush=True)
assert pins == {n: sha(p) for n, p in paths.items()}
report = {'status': 'UNACCEPTED labeled moving05 anatomical binding proposals; parent judges', 'pins': pins, 'candidateGLBSHA256': surface_map['candidateGLBSHA256'],
    'recipeSHA256': sha(__file__), 'frames': frames, 'FPS': 6, 'resolution': [512, 768], 'minimumWholeRiderNormalizedBorder': minimum,
    'displayOnlyOffsetM': .003, 'render': 'CyclesCPU2threads4samples',
    'limits': ['Synthetic bike-free poses and rotating camera, no posed art judgment.', 'Exact surface-map coordinates are unoffset; display offset only improves visibility.', 'Gear/body patches shown separately; no gear fit, supported-bike or closed-volume contact proof.', 'Underlying body mode hides gloves/boots/jeans to expose anatomy; seat shown only in gear mode.']}
(out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
print('CONTACT_REVIEW_READY', sha(out / 'review.json'), flush=True)
