"""CPU gray control/donor camera orbits; display registration is not fitting."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Roughness'].default_value = 0.65
    return mat


def mesh_object(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def reference_obj(path, gray, dark):
    vertices, groups = [], {}
    name = 'body'
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'o':
            name = ' '.join(parts[1:])
        elif parts[0] == 'v':
            vertices.append(tuple(map(float, parts[1:4])))
        elif parts[0] == 'f':
            face = [int(p.split('/')[0]) for p in parts[1:]]
            groups.setdefault(name, []).append([i - 1 if i > 0 else len(vertices) + i for i in face])
    objects = []
    for name, faces in groups.items():
        used = sorted({i for f in faces for i in f})
        remap = {index: i for i, index in enumerate(used)}
        objects.append(mesh_object(name, [vertices[i] for i in used],
                                   [[remap[i] for i in f] for f in faces],
                                   dark if 'boxer' in name.lower() else gray))
    return objects


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', required=True)
    parser.add_argument('--native-sha256', required=True)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if sha(args.native) != args.native_sha256 or sha(args.contract) != args.contract_sha256:
        raise ValueError('Frozen donor/contract bytes changed')
    contract = json.loads(Path(args.contract).read_text())
    source = next(x for x in contract['poses'][0]['files'] if x['axes'] == 'zup')
    if sha(source['path']) != source['sha256']:
        raise ValueError('Frozen canonical OBJ changed')
    output = Path(args.out)
    if output.exists():
        raise FileExistsError('Fresh orbit directory required')
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    gray = material('Gray construction control', (0.55, 0.55, 0.55))
    dark = material('Opaque boxers control', (0.12, 0.14, 0.18))
    # Source OBJ already uses Blender XYZ; parse coordinates directly so an
    # importer's forward-axis conversion cannot rotate the canonical control.
    reference = reference_obj(source['path'], gray, dark)
    with np.load(args.native, allow_pickle=False) as raw:
        vertices, faces = raw['vertices'].copy(), raw['faces'].copy()
    donor = mesh_object('UNACCEPTED native donor display copy', vertices.tolist(),
                        faces[:, ::-1].tolist(), gray)
    # Explicit preview-only raw X->Blender Z, raw Y->Y, raw Z->-X.
    # This is not a recovered camera, anatomical registration or wearable fit.
    rotation = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)
    transformed = vertices @ rotation.T
    low, high = transformed.min(axis=0), transformed.max(axis=0)
    scale = contract['scale']['restHeightM'] / (high[2] - low[2])
    translate = -(low + high) / 2 * scale
    translate[2] += contract['scale']['restHeightM'] / 2
    matrix = np.eye(4)
    matrix[:3, :3] = rotation * scale
    matrix[:3, 3] = translate
    donor.matrix_world = Matrix(matrix.tolist())
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.world.color = (0.2, 0.2, 0.2)
    scene.view_settings.view_transform = 'Standard'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    for name, position, watts in [('Key', (3, -3, 4), 450),
                                   ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = watts, 4
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, 0.9)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Matched orbit')
    data.type, data.ortho_scale = 'ORTHO', 2.2
    camera = bpy.data.objects.new('Matched orbit', data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    rows = []
    for family, objects in [('canonical', reference), ('donor', [donor])]:
        directory = output / family
        directory.mkdir()
        for obj in reference + [donor]:
            obj.hide_render = obj not in objects
        for frame in range(72):
            yaw = frame * 2 * math.pi / 72
            camera.location = (5 * math.cos(yaw), 5 * math.sin(yaw), 1.15)
            camera.rotation_euler = (Vector((0, 0, 0.92)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            path = directory / f'{frame:03d}.png'
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rows.append({'family': family, 'frame': frame, 'yawDegrees': frame * 5,
                         'path': str(path), 'sha256': sha(path)})
    report = {'accepted': False, 'kind': 'static donor/control camera orbit, not rig motion or wearable fit',
              'nativeSHA256': sha(args.native), 'contractSHA256': sha(args.contract),
              'referenceOBJ': source, 'recipeSHA256': sha(__file__),
              'previewRawToBlenderMatrixRows': matrix.tolist(),
              'previewAlignment': 'explicit longest raw X axis upward; uniform rest-height match only',
              'framesPerFamily': 72, 'fps': 12, 'shader': 'matched gray studio, no generated PBR',
              'rows': rows, 'limits': ['No actual fitted garment, anatomy, skeleton, engine or device pass',
                                       'Raw decoder arrays untouched; separate display reverses winding only']}
    (output / 'orbit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
