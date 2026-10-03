"""One existing-bytes lit-neutral versus unlit-colour isolation, no generation."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from donor_orbit import material, mesh_object, sha
from wardrobe_orbit import native_material


def main():
    parser = argparse.ArgumentParser()
    for name in ['native', 'native-sha256', 'orbit', 'orbit-sha256', 'sampling', 'sampling-sha256', 'out']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    for name in ['native', 'orbit', 'sampling']:
        if sha(getattr(args, name)) != getattr(args, name + '_sha256'):
            raise ValueError('Frozen bytes changed: ' + name)
    previous = json.loads(Path(args.orbit).read_text())
    sampling = json.loads(Path(args.sampling).read_text())
    if previous['nativeSHA256'] != args.native_sha256 or sampling['nativeSHA256'] != args.native_sha256:
        raise ValueError('Inputs do not name same existing raw mesh')
    sampled = Path(args.sampling).parent / 'sampled-vertex-attrs.npz'
    if sha(sampled) != sampling['archiveSHA256']: raise ValueError('Samples changed')
    output = Path(args.out)
    if output.exists(): raise FileExistsError('Fresh diagnostic directory required')
    with np.load(args.native, allow_pickle=False) as raw:
        vertices, faces = raw['vertices'].copy(), raw['faces'].copy()
    with np.load(sampled, allow_pickle=False) as arrays:
        values, support = arrays['attrs'].copy(), arrays['support'].copy()
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    neutral = mesh_object('Existing native with constant neutral material', vertices.tolist(), faces[:, ::-1].tolist(), material('Neutral grey lighting on', (.55, .55, .55)))
    emission = mesh_object('Same native with sampled colour only', vertices.tolist(), faces[:, ::-1].tolist(), material('Sampled colour lighting off', (.5, .5, .5)))
    shader = native_material(emission, values, support)
    nodes, links = emission.data.materials[0].node_tree.nodes, emission.data.materials[0].node_tree.links
    nodes.clear()
    color = nodes.new('ShaderNodeVertexColor'); color.layer_name = 'Native base colour preview'
    unlit = nodes.new('ShaderNodeEmission'); unlit.inputs['Strength'].default_value = 1
    out = nodes.new('ShaderNodeOutputMaterial')
    links.new(color.outputs['Color'], unlit.inputs['Color']); links.new(unlit.outputs['Emission'], out.inputs['Surface'])
    matrix = Matrix(previous['previewRawToBlenderMatrixRows'])
    neutral.matrix_world = matrix; emission.matrix_world = matrix
    target = Vector(previous['camera']['targetM'])
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.resolution_x = 320; scene.render.resolution_y = 320; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    scene.world.color = (.2, .2, .2); scene.view_settings.view_transform = 'Standard'
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4; scene.render.use_persistent_data = True
    for name, location, watts in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
        light = bpy.data.lights.new(name, 'AREA'); light.energy = watts; light.size = 4
        obj = bpy.data.objects.new(name, light); bpy.context.collection.objects.link(obj); obj.location = location
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Same geometric orbit'); data.type = 'ORTHO'; data.ortho_scale = previous['camera']['orthoScaleM']
    camera = bpy.data.objects.new('Same geometric orbit', data); bpy.context.collection.objects.link(camera); scene.camera = camera
    output.mkdir(parents=True); rows = []
    for family, selected in [('canonical', neutral), ('donor', emission)]:
        directory = output / family; directory.mkdir()
        neutral.hide_render = selected != neutral; emission.hide_render = selected != emission
        for frame in range(48):
            yaw = frame * 2 * math.pi / 48
            camera.location = target + Vector((5 * math.cos(yaw), 5 * math.sin(yaw), .12))
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = directory / f'{frame:03d}.png'; scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rows.append({'family': family, 'frame': frame, 'yawDegrees': frame * 7.5, 'path': str(path), 'sha256': sha(path)})
    result = {'accepted': False, 'kind': 'one existing-bytes neutral-lit versus colour-only diagnostic',
              'nativeSHA256': sha(args.native), 'samplingSHA256': sha(args.sampling),
              'previousOrbitSHA256': sha(args.orbit), 'recipeSHA256': sha(__file__),
              'helpers': {name: sha(Path(__file__).with_name(name)) for name in ['donor_orbit.py', 'wardrobe_orbit.py']},
              'materials': {'canonical': 'constant .55 linear grey, roughness .65, studio lighting',
                            'donor': 'sampled base colour emission strength1; no lighting, roughness, metallic or transparency'},
              'sharedGeometryNormalsMatrixCamera': True, 'previousCamera': previous['camera'], 'shaderColourConversion': shader,
              'framesPerFamily': 48, 'fps': 8, 'resolution': [320, 320], 'rows': rows,
              'limits': ['No inference, new mesh, normal repair, smoothing, cleanup or native mutation',
                         'Distinguishes sampled colour from lighting/surface response; does not alone isolate geometry versus normals',
                         'Not an art, UV bake, fitted opening or rig acceptance']}
    (output / 'orbit.json').write_text(json.dumps(result, indent=2) + '\n')
    if sha(args.native) != args.native_sha256: raise ValueError('Native changed')


if __name__ == '__main__': main()
