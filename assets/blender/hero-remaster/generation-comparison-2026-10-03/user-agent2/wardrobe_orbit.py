"""Silent CPU isolated garment guide/native appearance orbit, not wearable fit."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from donor_orbit import material, mesh_object, reference_obj, sha


def native_material(obj, values, support):
    mesh = obj.data
    clipped = np.clip(values, 0, 1)
    srgb = clipped[:, :3]
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    linear[support == 0] = [1, 0, 1]
    rgba = np.column_stack([linear, np.ones(len(linear))]).astype(np.float32)
    layer = mesh.color_attributes.new(name='Native base colour preview', type='FLOAT_COLOR', domain='POINT')
    layer.data.foreach_set('color', rgba.reshape(-1))
    for name, channel in [('Native metallic preview', 3), ('Native roughness preview', 4)]:
        attribute = mesh.attributes.new(name=name, type='FLOAT', domain='POINT')
        attribute.data.foreach_set('value', clipped[:, channel].astype(np.float32))
    mat = mesh.materials[0]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = nodes.get('Principled BSDF')
    color = nodes.new('ShaderNodeVertexColor'); color.layer_name = layer.name
    links.new(color.outputs['Color'], principled.inputs['Base Color'])
    for name, socket in [('Native metallic preview', 'Metallic'), ('Native roughness preview', 'Roughness')]:
        node = nodes.new('ShaderNodeAttribute'); node.attribute_name = name
        links.new(node.outputs['Fac'], principled.inputs[socket])
    return {'baseColorInterpretation': 'native sRGB channels converted to linear for Blender preview',
            'materialClampOnlyOutOfRangeChannelElements': int(np.count_nonzero(values != clipped)),
            'unsupportedVerticesMagenta': int(np.count_nonzero(support == 0)),
            'alpha': 'retained in sample archive but inactive in opaque preview',
            'method': 'per-vertex shader channels, not a UV texture bake'}


def main():
    parser = argparse.ArgumentParser()
    for name in ['native', 'native-sha256', 'sampling', 'sampling-sha256', 'geometry-contract', 'geometry-contract-sha256', 'out']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--garment', choices=['hoodie', 'jeans'], required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    for name in ['native', 'sampling', 'geometry_contract']:
        if sha(getattr(args, name)) != getattr(args, name + '_sha256'):
            raise ValueError('Frozen ' + name + ' bytes changed')
    contract = json.loads(Path(args.geometry_contract).read_text())
    garment = next(item for item in contract['garments'] if item['garment'] == args.garment)
    source = next(item for item in garment['files'] if item['axes'] == 'zup')
    if sha(source['path']) != source['sha256']:
        raise ValueError('Canonical isolated metric garment changed')
    report = json.loads(Path(args.sampling).read_text())
    if report['nativeSHA256'] != args.native_sha256:
        raise ValueError('Sampling is not from this native donor')
    sampled_archive = Path(args.sampling).parent / 'sampled-vertex-attrs.npz'
    if sha(sampled_archive) != report['archiveSHA256']:
        raise ValueError('Derived appearance archive changed')
    output = Path(args.out)
    if output.exists(): raise FileExistsError('Fresh orbit directory required')
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    guide_color = (.56, .28, .028) if args.garment == 'hoodie' else (.023, .045, .085)
    guide_material = material('Flat experimental appearance guide', guide_color)
    canonical = reference_obj(source['path'], guide_material, guide_material)
    with np.load(args.native, allow_pickle=False) as raw:
        vertices, faces = raw['vertices'].copy(), raw['faces'].copy()
    with np.load(sampled_archive, allow_pickle=False) as sampled:
        values, support = sampled['attrs'].copy(), sampled['support'].copy()
    if values.shape != (len(vertices), 6) or support.shape != (len(vertices),):
        raise ValueError('Expected six sampled appearance channels per decoded vertex')
    donor = mesh_object('UNACCEPTED isolated garment native display', vertices.tolist(), faces[:, ::-1].tolist(), material('Derived native appearance', (.5, .5, .5)))
    shader = native_material(donor, values, support)
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]], dtype=float)
    transformed = vertices @ rotation.T
    low, high = transformed.min(axis=0), transformed.max(axis=0)
    target_low, target_high = np.array(source['minM']), np.array(source['maxM'])
    # Uniform isolated garment Z-extent match; not a recovered camera or fit.
    scale = (target_high[2] - target_low[2]) / (high[2] - low[2])
    translate = (target_low + target_high) / 2 - (low + high) / 2 * scale
    matrix = np.eye(4); matrix[:3, :3] = rotation * scale; matrix[:3, 3] = translate
    donor.matrix_world = Matrix(matrix.tolist())
    target = Vector(((target_low + target_high) / 2).tolist())
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.resolution_x = 512; scene.render.resolution_y = 512; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.film_transparent = False
    scene.world.color = (.2, .2, .2); scene.view_settings.view_transform = 'Standard'
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4; scene.render.use_persistent_data = True
    for name, location, watts in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
        light = bpy.data.lights.new(name, 'AREA'); light.energy = watts; light.size = 4
        obj = bpy.data.objects.new(name, light); bpy.context.collection.objects.link(obj); obj.location = location
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data = bpy.data.cameras.new('Matched isolated garment orbit')
    camera_data.type = 'ORTHO'; camera_data.ortho_scale = float(np.max(target_high - target_low) * 1.18)
    camera = bpy.data.objects.new('Matched isolated garment orbit', camera_data)
    bpy.context.collection.objects.link(camera); scene.camera = camera
    rows = []
    for family, objects in [('canonical', canonical), ('donor', [donor])]:
        directory = output / family; directory.mkdir()
        for obj in canonical + [donor]: obj.hide_render = obj not in objects
        for frame in range(72):
            yaw = frame * 2 * math.pi / 72
            camera.location = target + Vector((5 * math.cos(yaw), 5 * math.sin(yaw), .12))
            camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = directory / f'{frame:03d}.png'; scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rows.append({'family': family, 'frame': frame, 'yawDegrees': frame * 5, 'path': str(path), 'sha256': sha(path)})
    result = {'accepted': False, 'kind': 'isolated flat guide/native sampled appearance camera orbit, no wearable fit',
              'nativeSHA256': sha(args.native), 'samplingSHA256': sha(args.sampling),
              'geometryContractSHA256': sha(args.geometry_contract), 'canonicalOBJ': source,
              'recipeSHA256': sha(__file__), 'helperSHA256': sha(Path(__file__).with_name('donor_orbit.py')),
              'garment': args.garment, 'previewRawToBlenderMatrixRows': matrix.tolist(),
              'previewAlignment': 'raw Z up, uniform isolated garment Z-extent and centre match only; not body height',
              'camera': {'targetM': list(target), 'orthoScaleM': camera_data.ortho_scale, 'radiusM': 5, 'riseM': .12},
              'shader': shader, 'guideLinearRGB': list(guide_color), 'framesPerFamily': 72, 'fps': 12, 'rows': rows,
              'limits': ['No joined hood, openings, fit, anatomy, rig, physics or device pass',
                         'Flat guide input is not detailed concept PBR reconstruction',
                         'Native archive unchanged; display winding reversed and channels sampled only']}
    (output / 'orbit.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
