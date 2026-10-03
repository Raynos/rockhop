"""Silent moving review of the immutable finite-cell shape, no cleanup or PBR."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mesh', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert sha(args.mesh) == '318c7536e5234c6a6e285f4d2111dad9fcdf3941e0329951a1f9a7ebf460612a'
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    with np.load(args.mesh, allow_pickle=False) as archive:
        vertices, faces = archive['vertices'].copy(), archive['faces'].copy()
    assert np.isfinite(vertices).all()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new('Unaccepted finite-cell extraction')
    display_faces = faces[:, ::-1].copy()
    mesh.from_pydata(vertices.tolist(), [], display_faces.tolist())
    mesh.update()
    loaded_v = np.empty(vertices.size, dtype=np.float32)
    loaded_f = np.empty(faces.size, dtype=np.int32)
    mesh.vertices.foreach_get('co', loaded_v)
    mesh.loops.foreach_get('vertex_index', loaded_f)
    assert np.array_equal(loaded_v.reshape(vertices.shape), vertices)
    assert np.array_equal(loaded_f.reshape(faces.shape), display_faces)
    obj = bpy.data.objects.new('No repair, reduction, component deletion or garment fit', mesh)
    bpy.context.collection.objects.link(obj)
    matrix = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    obj.matrix_world = matrix
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mat = bpy.data.materials.new('Neutral grey only, no learned material')
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.55, .55, .55, 1)
    shader.inputs['Roughness'].default_value = .65
    obj.data.materials.append(mat)
    centre = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    target = matrix @ Vector(centre.tolist())
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    scene.render.use_persistent_data = True
    scene.world.color = (.16, .16, .16)
    scene.view_settings.view_transform = 'Standard'
    for name, location, watts in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.size = watts, 4
        lamp = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(lamp)
        lamp.location = location
        lamp.rotation_euler = (target - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Measured full-shape orbit')
    data.type = 'ORTHO'
    data.ortho_scale = 2.35
    camera = bpy.data.objects.new('Measured full-shape orbit', data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    frames = out / 'frames'
    frames.mkdir()
    rows = []
    for frame in range(48):
        yaw = frame * 2 * math.pi / 48
        camera.location = target + Vector((4 * math.sin(yaw), -4 * math.cos(yaw), .25))
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        path = frames / f'{frame:03d}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rows.append({'frame': frame, 'yawDegrees': frame * 7.5, 'path': str(path.resolve()), 'SHA256': sha(path)})
    report = {'accepted': False, 'recipeSHA256': sha(__file__), 'inputSHA256': sha(args.mesh),
              'blender': bpy.app.version_string, 'vertices': len(mesh.vertices), 'triangles': len(mesh.polygons),
              'loadedVertexAndIndexArraysIdentical': True, 'displayWinding': 'Original official global reversal',
              'rawToBlenderMatrix': [list(row) for row in matrix], 'material': 'Constant neutral grey, roughness.65',
              'shading': 'Averaged vertex normals only; no vertex smoothing, geometry or topology change',
              'renderer': 'Cycles CPU,4threads,8samples', 'fps': 8, 'frames': 48, 'resolution': [512, 512],
              'camera': {'orthoScale': 2.35, 'target': list(target), 'radius': 4, 'elevation': .25}, 'rows': rows,
              'limits': ['Unaccepted diagnostic extraction, not original invalid raw or a player asset.',
                         'Six zero-area triangles and small detached component retained.',
                         'No learned texture/PBR, rig, fit, motion or CUDA acceptance.']}
    (out / 'orbit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('inputSHA256', 'vertices', 'triangles', 'frames')}), flush=True)


if __name__ == '__main__':
    main()
