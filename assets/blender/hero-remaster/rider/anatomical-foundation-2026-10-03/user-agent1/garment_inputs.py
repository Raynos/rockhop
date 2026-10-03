"""Experimental alpha garment layout inputs; appearance donors, never wearable passes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--contract', required=True)
ap.add_argument('--donor', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--reference', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, contract_path, donor_path, out = map(lambda s: Path(s).resolve(), [a.source, a.contract, a.donor, a.out])
out.mkdir(parents=True, exist_ok=True)
if (out / 'input-contract.json').exists():
    raise RuntimeError('Frozen garment inputs exist')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
reference_path = Path(a.reference).resolve()
reference_sha = 'd48e3913d368275488a135da1779b22a6ebb42ae5e719b3ebbcfbce58932ae9a'
assert sha(reference_path) == reference_sha
pins = {str(p): sha(p) for p in [source, contract_path, donor_path, reference_path]}
assert pins[str(donor_path)] == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
contract = json.loads(contract_path.read_text())
assert pins[str(source)] == contract['sourceMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
shirt = bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
jeans = bpy.data.objects['Separate fitted native trousers control']
boxers = bpy.data.objects['Opaque boxer fitting garment']
for name, trs in next(p for p in contract['poses'] if p['label'] == 'true_A')['poseBasisBlender'].items():
    pb = rig.pose.bones[name]
    pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
root.location.x = 0

# Import donor MATERIALS/images, then construct only its raw primitive2 hood.
# No donor bones, deformation field, body anatomy or inverse bind is adopted.
existing_materials = set(bpy.data.materials)
bpy.ops.import_scene.gltf(filepath=str(donor_path))
imported_materials = set(bpy.data.materials) - existing_materials
raw = donor_path.read_bytes()
json_length = int.from_bytes(raw[12:16], 'little')
doc = json.loads(raw[20:20 + json_length])
binary = raw[28 + json_length:]


def accessor(index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: '<u1'}[a['componentType']])
    stride = v.get('byteStride', components * dtype.itemsize)
    return np.ndarray((a['count'], components), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0), strides=(stride, dtype.itemsize)).copy()


primitive = doc['meshes'][0]['primitives'][2]
positions = accessor(primitive['attributes']['POSITION'])
uv = accessor(primitive['attributes']['TEXCOORD_0'])
normals = accessor(primitive['attributes']['NORMAL'])
triangles = accessor(primitive['indices']).reshape(-1, 3)
material_name = doc['materials'][primitive['material']]['name']
matches = [m for m in imported_materials if m.name == material_name or m.name.startswith(material_name + '.')]
assert len(matches) == 1, [(m.name) for m in imported_materials]
material = matches[0]
mesh = bpy.data.meshes.new('Exact donor hood, raw runtime primitive2')
mesh.from_pydata([(float(p[0]) - .65, -float(p[2]), float(p[1])) for p in positions], [], triangles.tolist())
hood = bpy.data.objects.new('Donor hood appearance guide, NOT joined or fitted', mesh)
bpy.context.collection.objects.link(hood)
mesh.materials.append(material)
uv_layer = mesh.uv_layers.new(name='Preserved donor TEXCOORD_0')
for loop in mesh.loops:
    u, v = uv[loop.vertex_index]
    uv_layer.data[loop.index].uv = (float(u), 1 - float(v))
for f in mesh.polygons:
    f.use_smooth = True
mesh.normals_split_custom_set_from_vertices([(float(n[0]), -float(n[2]), float(n[1])) for n in normals])
for obj in list(bpy.data.objects):
    if obj.type == 'MESH':
        obj.hide_render = True

scene = bpy.context.scene
world = bpy.data.worlds.new('Calibrated experimental garment studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.8, .8, .8, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .8
scene.world = world
for item in contract['lights']:
    light = bpy.data.lights.new(item['name'], 'AREA')
    light.energy, light.size = item['watts'], item['sizeM']
    obj = bpy.data.objects.new(item['name'], light)
    bpy.context.collection.objects.link(obj)
    obj.location = item['BlenderM']
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Pinned fitting front camera')
camera = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(camera)
camera.matrix_world = Matrix(contract['primaryInput']['cameraMatrixBlenderRows'])
data.type, data.ortho_scale = 'ORTHO', 2.2
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 8
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x, scene.render.resolution_y = 512, 512
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format, scene.render.image_settings.color_mode = 'PNG', 'RGBA'
scene.view_settings.view_transform = 'AgX'
# Flat conditioning colors follow the pinned concept, without claiming PBR match.
for obj, rgba in [(shirt, (.56, .28, .028, 1)), (jeans, (.023, .045, .085, 1))]:
    guide = bpy.data.materials.new('Experimental flat appearance guide ' + obj.name)
    guide.diffuse_color = rgba
    guide.use_nodes = True
    guide.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rgba
    guide.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .85
    obj.data.materials.clear()
    obj.data.materials.append(guide)
    if obj == shirt:
        hood.data.materials.clear()
        hood.data.materials.append(guide)
scene.view_settings.exposure = -1
rows = []
for name, visible in [('hoodie-context', [body, boxers, shirt, hood]),
                      ('hoodie-only', [shirt, hood]),
                      ('jeans-context', [body, jeans]), ('jeans-only', [jeans]),
                      ('hoodie-context-rear', [body, boxers, shirt, hood]),
                      ('hoodie-only-rear', [shirt, hood]),
                      ('jeans-context-rear', [body, jeans]), ('jeans-only-rear', [jeans])]:
    if name.endswith('-rear'):
        camera.location = (-5, 0, .92)
        camera.rotation_euler = (Vector((0, 0, .92)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    for obj in [body, shirt, jeans, boxers, hood]:
        obj.hide_render = obj not in visible
    file = out / (name + '.png')
    scene.render.filepath = str(file)
    bpy.ops.render.render(write_still=True)
    rows.append({'name': name, 'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
        'visibleObjects': [o.name for o in visible],
        'cameraMatrixBlenderRows': [list(r) for r in camera.matrix_world]})
assert pins == {str(p): sha(p) for p in [source, contract_path, donor_path, reference_path]}
receipt = {'status': 'EXPERIMENTAL UNACCEPTED garment appearance/layout inputs; not wearable fit',
    'pins': pins, 'parentFittingContractSHA256': sha(contract_path), 'primaryPose': 'true_A/action off',
    'camera': contract['primaryInput'], 'axes': contract['axes'], 'scale': contract['scale'],
    'body': 'Frozen original anatomy, explicit four-weight control; no rejected rest-fit used',
    'hood': {'donorMesh': 0, 'donorPrimitive': 2, 'vertices': len(positions), 'triangles': len(triangles),
        'material': material.name, 'originalMaterialName': material_name,
        'appearanceOverride': 'Same flat mustard as shirt; donor dark texture retained in memory only', 'rawPositionSHA256': hashlib.sha256(positions.tobytes()).hexdigest(),
        'positionConversion': '[rawX−0.65,−rawZ,rawY], metres; no extra1.015',
        'fit': 'Static donor shell for appearance guide ONLY, not joined to native neckline'},
    'openings': {'nativeShirt': 'neck/two cuffs/hem; source boundaryIDs fit-witness01',
        'nativeJeans': 'waist/two ankles', 'donorHood': 'original lower body graft and upper open rim; not native shirt collar'},
    'images': rows, 'approvedAppearanceReference': {'path': str(reference_path), 'sha256': reference_sha,
        'libraryZIP': 'libfile_3254a01e3c108191afaf8b4280791275',
        'ZIPsha256': '2b9b6c0b945e7a795ae17bed466e0e80062176040f27e423046cb04a16419fff',
        'use': 'Clothing appearance only; protected b7 head/hair immutable'},
    'flatAppearanceGuides': 'Shirt linearRGBA .56/.28/.028/1; denim .023/.045/.085/1; not target PBR proof',
    'limits': ['Layout/appearance donors only; source generated solids do not certify holes, fit, weights, rig or motion.',
        'Native shirt is hoodless; donor hood is a disjoint static visual guide, not constructed hoodie.',
        'Known underarm/knee/hem fit failures remain; native gray head not identity target.',
        'Root alone judges; no normal player assets modified.']}
(out / 'input-contract.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('GARMENT_INPUTS', [(r['name'], r['sha256']) for r in rows], flush=True)
