"""Bounded P3 neutral-body repair preview, no skin/pose or source overwrite.

Blender -b --factory-startup --python-exit-code 1 --python repair_pixal03.py --
  --input ORIGINAL.glb --out FRESH_DIR
Voxel union at 1/900 body height, separate decimation and color/PBR rebakes.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Matrix, Vector

args = argparse.ArgumentParser()
args.add_argument('--input', required=True)
args.add_argument('--out', required=True)
a = args.parse_args(sys.argv[sys.argv.index('--') + 1:])
source = Path(a.input).resolve()
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
assert set(p.name for p in out.iterdir()) <= {'attempt.json'}, 'fresh derivative only'
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_sha == 'fa149ce5584cc2039d92cda7403c852bbe93004c28f1790894492e7ec7d6e005', 'frozen P3 working body'
recipe_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
attempt = {'defect': 'P3-TOPOLOGY-01', 'candidate': 'P3', 'attempt': 1,
           'status': 'unaccepted preview; parent must judge before any next stage',
           'source': str(source), 'sourceSHA256': source_sha, 'recipeSHA256': recipe_sha,
           'hypothesis': 'A fine voxel union can close small export breaks without replacing body anatomy; separate UV/PBR rebake preserves existing appearance',
           'scope': 'Same whole body, geometry derivative only; no rig, anatomy target, pose or physics edits',
           'voxelResolutionOverHeight': 900, 'requestedFaces': 55000, 'textureSize': 2048,
           'limits': ['Voxel/decimation may soften fingers or folds; comparison required',
                      'Texture defects already in the source may persist', 'This is not deformation or rig acceptance']}
(out / 'attempt.json').write_text(json.dumps(attempt, indent=2) + '\n')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
assert len(meshes) == 1, 'single whole unrigged source'
src = meshes[0]
assert all(m.type != 'ARMATURE' for m in src.modifiers)
# Bake the imported object's world transform into a local analysis copy.
world = src.matrix_world.copy()
src.data.transform(world)
src.parent = None
src.matrix_world = Matrix.Identity(4)
src.name = 'P3_FrozenTextureDonor'
bounds = [src.matrix_world @ Vector(v) for v in src.bound_box]
height = max(v.z for v in bounds) - min(v.z for v in bounds)
assert .8 < height < 1.2, 'native normalization, not a fitted rider scale'
dst = src.copy()
dst.data = src.data.copy()
bpy.context.collection.objects.link(dst)
dst.name = 'P3_RepairPreview1'


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    result = {'vertices': len(bm.verts), 'triangles': triangles(obj),
              'boundaryEdges': sum(e.is_boundary for e in bm.edges),
              'edgesNotManifold': sum(not e.is_manifold for e in bm.edges)}
    bm.free()
    return result


before = topology(src)
active(dst)
voxel = dst.modifiers.new('FineBodyUnion', 'REMESH')
voxel.mode = 'VOXEL'
voxel.voxel_size = height / 900
voxel.adaptivity = 0
voxel.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier=voxel.name)
after_voxel = topology(dst)
assert after_voxel['triangles'] > 55000, 'do not upsample a failed voxel result'
dec = dst.modifiers.new('SeparateWorkingReduction', 'DECIMATE')
dec.ratio = 55000 / after_voxel['triangles']
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dec.name)
for face in dst.data.polygons:
    face.use_smooth = True
after = topology(dst)
assert after['triangles'] <= 56000 and after['triangles'] > 50000
active(dst)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(75), island_margin=.003,
                         area_weight=1, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
dst.data.materials.clear()
material = bpy.data.materials.new('P3_RebakedSourcePBR')
material.use_nodes = True
dst.data.materials.append(material)
principled = material.node_tree.nodes.get('Principled BSDF')
target_node = material.node_tree.nodes.new('ShaderNodeTexImage')
donors = []
for mat in src.data.materials:
    assert mat and mat.use_nodes
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    assert not bsdf.inputs['Normal'].is_linked, 'normal-map transfer must not be silently lost'
    output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
    emission = mat.node_tree.nodes.new('ShaderNodeEmission')
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    donors.append((mat, bsdf, emission))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = height * .004
scene.render.bake.max_ray_distance = height * .012
scene.render.bake.margin = 8
images = {}
for channel, color in [('Base Color', True), ('Roughness', False), ('Metallic', False)]:
    image = bpy.data.images.new('P3_' + channel.replace(' ', ''), width=2048, height=2048, alpha=False)
    image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    for mat, bsdf, emission in donors:
        socket = bsdf.inputs[channel]
        for link in list(emission.inputs['Color'].links):
            mat.node_tree.links.remove(link)
        if socket.is_linked:
            mat.node_tree.links.new(socket.links[0].from_socket, emission.inputs['Color'])
        else:
            value = socket.default_value
            emission.inputs['Color'].default_value = tuple(value) if color else (value, value, value, 1)
    target_node.image = image
    material.node_tree.nodes.active = target_node
    active(dst)
    src.select_set(True)
    bpy.ops.object.bake(type='EMIT')
    image.filepath_raw = str(out / (channel.replace(' ', '-') + '.png'))
    image.file_format = 'PNG'
    image.save()
    image.pack()
    images[channel] = image
for channel, image in images.items():
    tex = target_node if channel == 'Base Color' else material.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    material.node_tree.links.new(tex.outputs['Color'], principled.inputs[channel])
active(dst)
bpy.ops.export_scene.gltf(filepath=str(out / 'working.glb'), export_format='GLB', use_selection=True,
                          export_animations=False, export_skins=False)
src.hide_render = True
src.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'master.blend'))
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
report = {'status': 'generated unaccepted geometry preview; visual judgment pending', 'attempt': attempt,
          'blender': bpy.app.version_string, 'sourceUnchanged': True, 'nativeHeight': height,
          'voxelSize': height / 900, 'before': before, 'afterVoxel': after_voxel, 'after': after,
          'topologyMethod': 'BMesh edge incidence on actual imported/repaired mesh; raw source UV splits can differ from positional-weld audit',
          'UV': 'Smart Project75deg / margin.003 / area weight1',
          'bake': {'channels': list(images), 'type': 'EMIT', 'samples': 1, 'CPUThreads': 6,
                   'cageExtrusion': height * .004, 'maxRayDistance': height * .012, 'paddingPixels': 8},
          'outputSHA256': hashlib.sha256((out / 'working.glb').read_bytes()).hexdigest(),
          'textureFiles': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')}}
(out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
