"""Read-only source review photos; no new model, export or appearance substitute."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
args = sys.argv[sys.argv.index('--') + 1:]
out, poses_path = map(lambda p: Path(p).resolve(), args)
out.mkdir(parents=True, exist_ok=False)
wardrobe = ROOT / 'harness/out/rider-rebuild/construction02/selected-wardrobe01/rider-assembled.blend'
face = ROOT / 'harness/out/rider-rebuild/construction02/selected-face03/selected-face-native.blend'
boots = ROOT / 'harness/out/rider-rebuild/selected-boot02/selected-boot-checkpoint.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(wardrobe) == 'f8fd61f677b5ac378fee1494973b4dca832f5f74c07ccff18a9da0d57112de25'
assert sha(face) == '14d7aa71baced13fbd5e53667bf80561698712673ca013e050dbe71ad6f3390c'
assert sha(boots) == '2e836f508a9799325225affe2cbf1e6347c818ef3eaac2884c8cf48f56d435df'
sources = [{'path': str(p), 'sha256': sha(p)} for p in (wardrobe, face, boots, poses_path)]
bpy.ops.wm.open_mainfile(filepath=str(wardrobe))
rig = bpy.data.objects['RiderSkeleton']
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH' and obj.name not in ('RiderHoodie', 'RiderJeans'):
        bpy.data.objects.remove(obj, do_unlink=True)

def append(source, names):
    with bpy.data.libraries.load(str(source), link=False) as (available, selected):
        assert set(names) <= set(available.objects)
        selected.objects = names
    for obj in selected.objects:
        bpy.context.scene.collection.objects.link(obj)
        arms = [m for m in obj.modifiers if m.type == 'ARMATURE']
        assert len(arms) == 1
        arms[0].object = rig
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = Matrix.Identity(4)
        obj.hide_render = False
        obj.hide_viewport = False
        obj.hide_set(False)

append(face, ['RiderBody'])
append(boots, ['ActualSelectedBoot.L', 'ActualSelectedBoot.R'])
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
assert {o.name for o in meshes} == {'RiderBody','RiderHoodie','RiderJeans','ActualSelectedBoot.L','ActualSelectedBoot.R'}
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('SelectedSourceReviewWorld')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.22,.24,.28,1)
world.node_tree.nodes['Background'].inputs[1].default_value = .55
scene.world = world

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

for name, position, power, size in [('Key',(2,-3,4),650,3),('Fill',(-3,-2,2),450,3),('Rim',(0,3,3),700,2)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    aim(obj, (0,0,1))
camera = bpy.data.objects.new('SelectedSourceReviewCamera', bpy.data.cameras.new('SelectedSourceReviewCamera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.12
poses = json.loads(poses_path.read_text())
assert poses['sourceAndRestPreserved']
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
ordered = sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))
frames = [('standing-front',(2.4,-3.5,1.7),None),
          ('standing-profile',(3,0,1.45),None),
          ('forward-lean',(2.4,-3.5,1.7),'forward1')]
for name, position, state in frames:
    deltas = None if state is None else next(r['boneDeltaNativeColumnMajor'] for r in poses['rows'] if r['name']==state)
    for bone in ordered:
        bone.rotation_mode = 'QUATERNION'
        if deltas is None:
            bone.matrix_basis = Matrix.Identity(4)
        else:
            values = deltas[bone.name]
            delta = Matrix([values[i::4] for i in range(4)])
            bone.matrix = delta @ rest[bone.name]
        bpy.context.view_layer.update()
    camera.location = position
    aim(camera,(0,-.05,.90))
    scene.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
assert all(sha(record['path']) == record['sha256'] for record in sources)
(out/'receipt.json').write_text(json.dumps({'accepted':False,'sources':sources,
    'actualSourceMeshes':[o.name for o in meshes], 'photos':[name+'.png' for name,_,_ in frames],
    'missing':'Selected gloves are unfinished; visible hands remain bare.',
    'limits':['Progress photos only, not played acceptance.','Studio source review, not Garage or game delivery.',
              'No source native file modified and no new model asset exported.']},indent=2)+'\n')
