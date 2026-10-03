"""Export immutable experimental fitting inputs from the measured own-bind body.

This qualifies exact input identity/axes/modesty, never final likeness,
wearability, surface clearance, native-weight loss or motion acceptance.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--driver', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--evidence', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, driver_path, out, evidence = map(lambda s: Path(s).resolve(), [a.source, a.driver, a.out, a.evidence])
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
if (out / 'contract.json').exists():
    raise RuntimeError('Frozen fitting inputs exist; choose another leaf')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_hash = sha(source)
driver = json.loads(driver_path.read_text())
assert source_hash == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
boxers = bpy.data.objects['Opaque boxer fitting garment']
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
for obj in list(bpy.data.objects):
    if obj.type == 'MESH':
        obj.hide_render = True
pose_rows = []
render_objects = []
for label in ['true_A', 'true_T', 'true_neutral']:
    for name, trs in driver['fixtures'][label].items():
        pb = rig.pose.bones[name]
        pb.location = trs['location']
        pb.rotation_quaternion = trs['quaternionWXYZ']
        pb.scale = trs['scale']
    bpy.context.view_layer.update()
    meshes = []
    for obj in [body, boxers]:
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = bpy.data.meshes.new_from_object(evaluated)
        world = evaluated.matrix_world.copy()
        vertices = [world @ v.co - Vector((root.location.x, 0, 0)) for v in mesh.vertices]
        faces = [list(f.vertices) for f in mesh.polygons]
        meshes.append({'region': 'body' if obj == body else 'opaque_boxers',
            'verticesBlenderCenteredM': [list(v) for v in vertices], 'faces': faces})
        if label == 'true_A':
            static = bpy.data.objects.new('Experimental fitting ' + meshes[-1]['region'], mesh)
            bpy.context.collection.objects.link(static)
            static.hide_render = False
            for v, p in zip(static.data.vertices, vertices):
                v.co = p
            for f in static.data.polygons:
                f.use_smooth = True
            render_objects.append(static)
        else:
            bpy.data.meshes.remove(mesh)
    files = []
    for axes in ['zup', 'yup']:
        text = ['# EXPERIMENTAL UNACCEPTED fitting body and opaque boxers; metres; centered X=0']
        offset = 1
        for region in meshes:
            text.append('o ' + region['region'])
            for p in region['verticesBlenderCenteredM']:
                v = C @ Vector(p) if axes == 'yup' else Vector(p)
                text.append('v ' + ' '.join(format(n, '.9g') for n in v))
            for face in region['faces']:
                text.append('f ' + ' '.join(str(i + offset) for i in face))
            offset += len(region['verticesBlenderCenteredM'])
        file = out / f'{label}-body-boxers-{axes}.obj'
        file.write_text('\n'.join(text) + '\n')
        files.append({'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size, 'axes': axes})
    pose_rows.append({'label': label, 'action': None, 'morphs': 0, 'correctives': 0,
        'poseBasisBlender': driver['fixtures'][label], 'meshes': [{'region': m['region'],
            'vertices': len(m['verticesBlenderCenteredM']), 'faces': len(m['faces']),
            'facesSHA256': hashlib.sha256(json.dumps(m['faces']).encode()).hexdigest()} for m in meshes],
        'files': files})

world = bpy.data.worlds.new('Experimental canonical fitting studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.8, .8, .8, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .8
scene = bpy.context.scene
scene.world = world
lights = []
for name, pos, power in [('Key', (3, -3, 4), 450), ('Fill', (2, 4, 3), 350), ('Rim', (-3, 0, 4), 400)]:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size = power, 4
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    lights.append({'name': name, 'BlenderM': list(pos), 'watts': power, 'sizeM': 4})
data = bpy.data.cameras.new('Exact experimental fitting camera')
camera = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(camera)
data.type, data.ortho_scale = 'ORTHO', 2.2
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 4
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x, scene.render.resolution_y = 512, 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
views = []
for yaw, elevated in [(y, False) for y in range(0, 360, 45)] + [(45, True)]:
    r = math.radians(yaw)
    target = Vector((0, 0, .92))
    camera.location = target + Vector((5 * math.cos(r), 5 * math.sin(r), 1.4 if elevated else 0))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    file = out / f'true_A-yaw-{yaw:03d}{"-elevated" if elevated else ""}.png'
    scene.render.filepath = str(file)
    bpy.ops.render.render(write_still=True)
    views.append({'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
        'yawDegrees': yaw, 'elevated': elevated, 'cameraBlenderM': list(camera.location),
        'cameraMatrixBlenderRows': [list(row) for row in camera.matrix_world],
        'cameraMatrixGLTFColumnMajor': [(C @ camera.matrix_world)[r][c] for c in range(4) for r in range(4)],
        'orthoHorizontalM': 2.2, 'orthoVerticalM': 2.2, 'resolution': [512, 512],
        'bodyRestHeightOccupancy': 1.822571873664856 / 2.2})
assert sha(source) == source_hash
contract = {'status': 'EXPERIMENTAL UNACCEPTED stable geometry/pose/axes fitting inputs; bounded donor comparison only',
    'sourceMasterSHA256': source_hash, 'nativeFullMasterSHA256': driver['sourceSHA256'],
    'driverSHA256': sha(driver_path), 'diagnosticGLBSHA256': driver['conditionedGLBSHA256'],
    'recipeSHA256': sha(__file__), 'bodyGeometrySHA256': driver['meshRows'][0]['geometryPositionsSHA256'],
    'bodyFacesSHA256': driver['meshRows'][0]['facesSHA256'],
    'conditioning': 'Explicit descending-weight top4 then normalization; sampled raw export parity <0.001mm; native loss remains visible/quantified',
    'scale': {'metres': True, 'restHeightM': 1.822571873664856, 'upperArmM': .264937,
        'forearmM': .273355, 'shoulderJointSpanM': .392147},
    'axes': {'blender': '+Xforward,+Zup,-Yleft', 'gltf': '+Xforward,+Yup,+Zleft',
        'OBJ': 'Centered X=0; file root+0.65 removed exactly ONCE; do not apply runtime wrapper again'},
    'preservedGLBRootX': .65, 'ordinaryRuntimeWrapperX': -.65,
    'completeJointOrder': driver['jointOrderNative'], 'runtimeRoles19': driver['runtimeRoles19'],
    'hierarchy': driver['hierarchy'], 'restBonesBlender': driver['restBonesBlender'],
    'poses': pose_rows, 'primaryInput': views[0], 'views': views, 'lights': lights,
    'approvedIdentityDonorSHA256': 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754',
    'head': 'Native gray head is a fitting control ONLY; retain approved donor identity/PBR',
    'generationUse': 'One bounded cheap local donor probe allowed from exact primary image+contract pins; no fit/appearance/production acceptance',
    'limits': ['Stable exact fitting inputs are not wearable fit or final body proportion approval.',
        'Garment control has known contact/self-intersection witnesses under motion.',
        'Legacy runtime conditioner changes authored body/cloth up to28.100/25.604mm.',
        'No global loader edit or optout; root alone judges M0–M5.']}
(out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
(evidence / 'contract-receipt.json').write_text(json.dumps({'contract': str(out / 'contract.json'),
    'contractSHA256': sha(out / 'contract.json'), 'status': contract['status'],
    'sourcePreserved': sha(source) == source_hash, 'primaryInput': views[0], 'views': len(views)}, indent=2) + '\n')
print('EXPERIMENTAL_FITTING_CONTRACT', sha(out / 'contract.json'), views[0]['sha256'], flush=True)
