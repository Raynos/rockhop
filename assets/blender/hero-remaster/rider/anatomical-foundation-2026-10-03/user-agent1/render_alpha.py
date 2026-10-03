"""One true geometric-alpha derivative of the immutable experimental fitting view."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--contract', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, contract_path, out = map(lambda x: Path(x).resolve(), [a.source, a.contract, a.out])
out.mkdir(parents=True, exist_ok=True)
if (out / 'true_A-yaw-000-alpha.png').exists():
    raise RuntimeError('Alpha input exists; preserve frozen bytes')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_hash, contract_hash = sha(source), sha(contract_path)
contract = json.loads(contract_path.read_text())
assert source_hash == contract['sourceMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
pose = next(p for p in contract['poses'] if p['label'] == 'true_A')
for name, trs in pose['poseBasisBlender'].items():
    pb = rig.pose.bones[name]
    pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
root = bpy.data.objects['Foundation file frame, game x0.65']
root.location.x = 0  # Remove file +.65 once; no runtime wrapper.
for obj in list(bpy.data.objects):
    if obj.type == 'MESH':
        obj.hide_render = obj.name not in ['Canonical anatomical body, baked adult hm08', 'Opaque boxer fitting garment']
world = bpy.data.worlds.new('Same fitting light, geometric transparent film')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.8, .8, .8, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .8
scene = bpy.context.scene
scene.world = world
for item in contract['lights']:
    light = bpy.data.lights.new(item['name'], 'AREA')
    light.energy, light.size = item['watts'], item['sizeM']
    obj = bpy.data.objects.new(item['name'], light)
    bpy.context.collection.objects.link(obj)
    obj.location = item['BlenderM']
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Same exact front fitting camera')
camera = bpy.data.objects.new(data.name, data)
bpy.context.collection.objects.link(camera)
camera.matrix_world = Matrix(contract['primaryInput']['cameraMatrixBlenderRows'])
data.type, data.ortho_scale = 'ORTHO', contract['primaryInput']['orthoHorizontalM']
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device, scene.cycles.samples = 'CPU', 4
scene.cycles.use_denoising = True
scene.render.threads_mode, scene.render.threads = 'FIXED', 2
scene.render.resolution_x, scene.render.resolution_y = contract['primaryInput']['resolution']
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'AgX'
file = out / 'true_A-yaw-000-alpha.png'
scene.render.filepath = str(file)
bpy.ops.render.render(write_still=True)
assert sha(source) == source_hash and sha(contract_path) == contract_hash
receipt = {'status': 'EXPERIMENTAL UNACCEPTED alpha-input amendment; bounded donor probe only',
    'parentContract': str(contract_path), 'parentContractSHA256': contract_hash,
    'parentOpaqueInput': contract['primaryInput'], 'sourceMasterSHA256': source_hash,
    'alphaInput': {'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size},
    'camera': contract['primaryInput'], 'poseLabel': 'true_A',
    'change': 'Blender film_transparent=True; RGBA PNG; same geometry, pose, camera, scale and lights',
    'centering': 'File root+.65 removed exactly once; centered input; no second runtime wrapper',
    'limits': contract['limits'], 'recipeSHA256': sha(__file__)}
(out / 'input-amendment.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('TRUE_ALPHA_INPUT', receipt['alphaInput']['sha256'], flush=True)
