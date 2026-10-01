"""Render the unchanged current GLB's actual standing-to-sitting clip on CPU."""
from pathlib import Path
import hashlib
import json
import math
import time
import bpy
from mathutils import Vector

repo=Path('/Users/raynos/projects/games/rockhop')
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')
out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01'
out.mkdir(parents=True,exist_ok=True)
assert not (out/'render-manifest.json').exists(), 'Frozen render cannot be overwritten'
before=hashlib.sha256(source.read_bytes()).hexdigest()
assert before=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
start=time.monotonic()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.fps=12
bpy.ops.import_scene.gltf(filepath=str(source))
rig=next(o for o in scene.objects if o.type=='ARMATURE')
action=next(a for a in bpy.data.actions if 'stand_to_sit_probe' in a.name)
rig.animation_data_create()
for track in rig.animation_data.nla_tracks:track.mute=True
rig.animation_data.action=action
if action.slots:rig.animation_data.action_slot=action.slots[0]
lo,hi=map(float,action.frame_range)
assert hi>lo and abs((hi-lo)/12-23/12)<.001,(lo,hi)
meshes=[o for o in scene.objects if o.type=='MESH']
rigid_sources={o.name:len(o.data.vertices) for o in meshes}
scene.frame_set(round(lo));bpy.context.view_layer.update()
first={b.name:list(rig.matrix_world@b.head) for b in rig.pose.bones}
scene.frame_set(round(hi));bpy.context.view_layer.update()
last={b.name:list(rig.matrix_world@b.head) for b in rig.pose.bones}
assert max((Vector(first[k])-Vector(last[k])).length for k in first)>.3, 'Must show actual moving clip'

def material(name,color,roughness=.7):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    node=mat.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=roughness
    return mat
# Fixed diagnostic seat follows the earlier authored bench fixture; neither it
# nor the studio is exported into the rider or player environment.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-.565*1.015,0,.2175*1.015))
bench=bpy.context.object;bench.name='Stationary diagnostic bench'
bench.scale=(.40*1.015,.60*1.015,.435*1.015)
bench.data.materials.append(material('Bench',(.13,.15,.17)))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002))
bpy.context.object.data.materials.append(material('Studio floor',(.12,.12,.12)))
world=bpy.data.worlds.new('Neutral studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
target=Vector((-.12,0,.89))
lights=[]
for name,position,power,size in [('Key',(3,-4,4),600,4),('Fill',(3,3,2.5),350,4),('Rim',(-3,1,3),450,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    lights.append({'name':name,'position':position,'watts':power,'size':size})
data=bpy.data.cameras.new('Fixed sitting review camera');camera=bpy.data.objects.new(data.name,data)
scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.ortho_scale=2.1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX'
scene.render.resolution_x=512;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
frames=[]
for yaw,name in [(0,'front'),(90,'side'),(135,'rear-three-quarter')]:
    angle=math.radians(yaw);camera.location=target+Vector((4*math.cos(angle),4*math.sin(angle),0))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    folder=out/name/'frames';folder.mkdir(parents=True,exist_ok=True)
    for index in range(24):
        assert time.monotonic()-start<1700,'CPU batch time limit'
        frame=lo+(hi-lo)*index/23;scene.frame_set(int(frame),subframe=frame-int(frame))
        bpy.context.view_layer.update();scene.render.filepath=str(folder/f'{index:04d}.png')
        bpy.ops.render.render(write_still=True)
        frames.append({'angle':yaw,'name':name,'sample':index,'sourceFrame':frame,
            'boneHeads':{b.name:list(rig.matrix_world@b.head) for b in rig.pose.bones}})
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(out/'render-manifest.json').write_text(json.dumps({'source':str(source),'sourceSHA256':before,
    'sourceUnchanged':True,'action':action.name,'actionFrameRange':[lo,hi],'fps':12,'samplesPerAngle':24,
    'angles':[0,90,135],'cameraTarget':list(target),'orthographicScale':2.1,'resolution':[512,640],
    'lightSettings':lights,'sourceVertexCounts':rigid_sources,'firstBoneHeads':first,'lastBoneHeads':last,
    'frames':frames,'seconds':time.monotonic()-start,
    'limits':'Existing authored clip on current GLB, unmodified. Blender LBS import differs from runtime skin-conditioning and IK. Fixed bench is a diagnostic fixture; seat/lap contacts and sitting quality remain unaccepted.'},indent=2)+'\n')
