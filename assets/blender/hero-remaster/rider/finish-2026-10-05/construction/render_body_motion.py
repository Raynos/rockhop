"""Headless silent played native body movie from the frozen semantic battery.

Render only the supplied derivative; all source/pose mutations are in memory,
never saved. Numerical FK is reused from the independently owned sampler.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import bpy
import numpy as np
from mathutils import Matrix,Quaternion,Vector

ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','battery','out','evidence']:ap.add_argument('--'+k,required=True)
ap.add_argument('--yaw',type=float,default=-45)
ap.add_argument('--stride',type=int,default=2)
ap.add_argument('--mode',choices=['pbr','gray'],default='pbr')
ap.add_argument('--limit',type=int)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source,battery_path,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','battery','out','evidence']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p)for p in [source,battery_path]}
assert pins[str(source)]=='01574c250a3a4b693d17ff373501574ec0e7db5615bcdc0e6b68adcf169e1bc3'
out.mkdir(parents=True,exist_ok=False);evidence.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
rig=bpy.data.objects['Finish rig'];scene=bpy.context.scene
assert scene.name=='Finish natural wearer diagnostic'
rig.animation_data_clear()
for pb in rig.pose.bones:
 for constraint in pb.constraints:constraint.mute=True
visible=['Finish body FOUR','Finish head FOUR','Finish boxer FOUR','Finish coherent cheek']
for ob in scene.objects:
 ob.hide_set(False)
 if ob.type=='MESH':ob.hide_render=ob.name not in visible
 if ob.name in visible:assert not ob.data.shape_keys
ROOT=Path(__file__).resolve().parents[6]
sampler=ROOT/'harness/rider-finish/native-sample.py'
text=sampler.read_text();start=text.index('def apply(command):');end=text.index('\ndef evaluated(o):',start)
exec(compile(text[start:end],str(sampler),'exec'))
world=bpy.data.worlds.new('Finish neutral review world');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.31,.35,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65;scene.world=world
target=Vector((.65,0,.98));yaw=math.radians(a.yaw)
camdata=bpy.data.cameras.new('Frozen full-body camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam)
camdata.type='ORTHO';camdata.ortho_scale=2.45
cam.location=target+Vector((5*math.cos(yaw),5*math.sin(yaw),.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
for name,pos,power,size in [('Key',(3.7,-3.4,4.3),650,4),('Fill',(2.7,3.3,2.7),420,3.5),('Rim',(-2.5,0,3.2),550,3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=pos;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
for engine in ['BLENDER_EEVEE','BLENDER_EEVEE_NEXT']:
 try:scene.render.engine=engine;break
 except TypeError:pass
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
if a.mode=='gray':
 material=bpy.data.materials.new('Finish shape-only neutral gray');material.use_nodes=True
 shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.38,.4,.42,1);shader.inputs['Roughness'].default_value=.7
 scene.view_layers[0].material_override=material
battery=json.loads(battery_path.read_text());rows=battery['frames'][::a.stride]
if a.limit:rows=rows[:a.limit]
metadata={'status':'UNACCEPTED played native exposed-body diagnostic; parent alone judges','inputs':pins,'recipeSHA256':sha(__file__),'samplerSHA256':sha(sampler),'mode':a.mode,'yawNativeDegrees':a.yaw,'resolution':[640,640],'fps':battery['sampling']['hz']/a.stride,'frames':len(rows),'cameraWorldRows':np.array(cam.matrix_world).tolist(),'visibleMeshes':visible,'sourceIndices':[r['index']for r in rows],'limits':['Finite FK stress/idle evidence, no actual bike or physical-support claim.','Stride is declared; exact source command time is retained. No interpolation or pose holds added.','In-memory gray override does not alter the frozen source PBR. No native file save or ordinary assets.']}
(evidence/'render-input.json').write_text(json.dumps(metadata,indent=2)+'\n')
for i,row in enumerate(rows):
 apply(row['command'])
 scene.render.filepath=str(out/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
 if i%12==0:
  progress={'framesDone':i+1,'total':len(rows),'sourceIndex':row['index'],'case':row['case'],'phase':row['phase']}
  (evidence/'progress.json').write_text(json.dumps(progress)+'\n');print('MOVIE_PROGRESS',progress,flush=True)
assert pins=={p:sha(p)for p in pins}
(evidence/'render-receipt.json').write_text(json.dumps({'status':'RENDERED all declared played frames; movie encoding pending','inputPinsExact':True,'frames':len(rows),'recipeSHA256':sha(__file__)},indent=2)+'\n')
print('PLAYED_FRAMES_COMPLETE',len(rows),flush=True)
