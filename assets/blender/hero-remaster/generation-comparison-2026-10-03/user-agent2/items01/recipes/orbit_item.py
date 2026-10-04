# Same existing Agent2 workflow, new item input pins only. No installed edits.
# Parent recipes remain byte-preserved; see recipe-lineage.json for provenance.
"""Silent moving review of the immutable finite-cell shape, no cleanup or PBR."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Matrix, Vector
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pbr_glb(path, output):
    payload = Path(path).read_bytes()
    magic, version, total = struct.unpack_from('<III', payload)
    assert magic == 0x46546C67 and version == 2 and total == len(payload)
    length, kind = struct.unpack_from('<II', payload, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(payload[20:20 + length])
    offset = 20 + length
    binary_length, kind = struct.unpack_from('<II', payload, offset)
    assert kind == 0x004E4942
    binary = payload[offset + 8:offset + 8 + binary_length]
    assert len(doc['meshes']) == 1 and len(doc['meshes'][0]['primitives']) == 1
    for node in doc['nodes']:
        assert 'rotation' not in node and 'translation' not in node and 'scale' not in node
        assert np.array_equal(np.asarray(node.get('matrix', np.eye(4).flatten())), np.eye(4).flatten())
    primitive = doc['meshes'][0]['primitives'][0]
    assert primitive.get('mode', 4) == 4
    def accessor(index):
        spec = doc['accessors'][index]
        view = doc['bufferViews'][spec['bufferView']]
        assert not spec.get('normalized', False) and 'sparse' not in spec and view.get('buffer', 0) == 0
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[spec['componentType']]
        columns = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[spec['type']]
        item = np.dtype(dtype).itemsize
        values = np.ndarray((spec['count'], columns), dtype=dtype, buffer=binary,
                            offset=view.get('byteOffset', 0) + spec.get('byteOffset', 0),
                            strides=(view.get('byteStride', item * columns), item)).copy()
        return values
    vertices = accessor(primitive['attributes']['POSITION'])
    faces = accessor(primitive['indices']).reshape(-1, 3)
    uv = accessor(primitive['attributes']['TEXCOORD_0'])
    normal = accessor(primitive['attributes']['NORMAL']) if 'NORMAL' in primitive['attributes'] else None
    pbr = doc['materials'][primitive['material']]['pbrMetallicRoughness']
    assert pbr.get('baseColorFactor', [1, 1, 1, 1]) == [1, 1, 1, 1]
    paths = {}
    for name in ('baseColorTexture', 'metallicRoughnessTexture'):
        texture = pbr[name]
        assert texture.get('texCoord', 0) == 0 and 'extensions' not in texture
        image = doc['images'][doc['textures'][texture['index']]['source']]
        view = doc['bufferViews'][image['bufferView']]
        begin = view.get('byteOffset', 0)
        suffix = {'image/png': '.png', 'image/jpeg': '.jpg'}[image['mimeType']]
        target = output / (name + suffix)
        target.write_bytes(binary[begin:begin + view['byteLength']])
        paths[name] = str(target.resolve())
    return vertices, faces, uv, normal, pbr, paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mesh', required=True)
    parser.add_argument('--mesh-sha256', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--painted-glb')
    parser.add_argument('--paint-receipt')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert sha(args.mesh) == args.mesh_sha256
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    with np.load(args.mesh, allow_pickle=False) as archive:
        vertices, faces = archive['vertices'].copy(), archive['faces'].copy()
    display_faces = faces[:, ::-1].copy()
    paint, material_paths, uv, normal = None, {}, None, None
    if args.painted_glb:
        assert args.paint_receipt
        paint = json.loads(Path(args.paint_receipt).read_text())
        assert paint['stage'] == 'PBR saved; root moving review pending' and not paint['accepted']
        assert paint['paintedGLBSHA256'] == sha(args.painted_glb) and not paint['remesh'] and not paint['simplification']
        loaded_v, loaded_f, uv, normal, pbr, material_paths = pbr_glb(args.painted_glb, out)
        assert loaded_f.shape == display_faces.shape and np.isfinite(loaded_v).all() and np.isfinite(uv).all()
        geometry_error = float(np.abs(loaded_v[loaded_f] - vertices[display_faces]).max())
        assert geometry_error < 9e-7
        vertices, display_faces = loaded_v, loaded_f
    assert np.isfinite(vertices).all()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mesh = bpy.data.meshes.new('Unaccepted finite-cell extraction')
    mesh.from_pydata(vertices.tolist(), [], display_faces.tolist())
    mesh.update()
    loaded_v = np.empty(vertices.size, dtype=np.float32)
    loaded_f = np.empty(faces.size, dtype=np.int32)
    mesh.vertices.foreach_get('co', loaded_v)
    mesh.loops.foreach_get('vertex_index', loaded_f)
    assert np.array_equal(loaded_v.reshape(vertices.shape), vertices)
    assert np.array_equal(loaded_f.reshape(display_faces.shape), display_faces)
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
    if paint:
        layer = mesh.uv_layers.new(name='Actual GLB TEXCOORD_0')
        loops_uv = uv[display_faces].reshape(-1, 2).copy()
        loops_uv[:, 1] = 1 - loops_uv[:, 1]  # glTF top-left UV to Blender bottom-left.
        layer.data.foreach_set('uv', loops_uv.ravel())
        if normal is not None:
            mesh.normals_split_custom_set_from_vertices(normal.tolist())
        base = mat.node_tree.nodes.new('ShaderNodeTexImage')
        base.image = bpy.data.images.load(material_paths['baseColorTexture'])
        base.image.colorspace_settings.name = 'sRGB'
        mat.node_tree.links.new(base.outputs['Color'], shader.inputs['Base Color'])
        packed = mat.node_tree.nodes.new('ShaderNodeTexImage')
        packed.image = bpy.data.images.load(material_paths['metallicRoughnessTexture'])
        packed.image.colorspace_settings.name = 'Non-Color'
        channels = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
        mat.node_tree.links.new(packed.outputs['Color'], channels.inputs['Color'])
        mat.node_tree.links.new(channels.outputs['Green'], shader.inputs['Roughness'])
        mat.node_tree.links.new(channels.outputs['Blue'], shader.inputs['Metallic'])
        assert pbr.get('roughnessFactor', 1) == 1 and pbr.get('metallicFactor', 1) == 1
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
                         'All original item geometry retained, including any degenerate or disconnected parts.',
                         'No learned texture/PBR, rig, fit, motion or CUDA acceptance.']}
    if paint:
        report.update(material='Actual GLB baseColor and packed roughness/metallic pixels',
                      paintedGLBSHA256=sha(args.painted_glb), paintReceiptSHA256=sha(args.paint_receipt),
                      sourceTriangleCoordinateError=geometry_error,
                      materialImagePins={name: {'path': path, 'SHA256': sha(path)} for name, path in material_paths.items()},
                      shading='Actual GLB normals when present; no vertex or topology smoothing',
                      limits=['Unaccepted generated mesh/PBR; root judges moving evidence.',
                              'No remesh, reduction, component deletion, rig, body fit or through-opening proof.',
                              'Native GLB triangles within9e-7 of frozen shape; actual texture pixels, no image editing.'])
    (out / 'orbit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('inputSHA256', 'vertices', 'triangles', 'frames')}), flush=True)


if __name__ == '__main__':
    main()
