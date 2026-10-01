"""Actual GLB reimport evidence. CPU2; hard stop before 02:17 UTC."""
import bpy,bmesh,json,hashlib,time,math,datetime
from collections import Counter
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
deadline=datetime.datetime(2026,10,1,2,17,tzinfo=datetime.timezone.utc).timestamp()
assert not (O/'reimport-and-renders.json').exists(),'Frozen review cannot be overwritten'
report={'status':'UNACCEPTED C garment-pattern actual GLB evidence','recipeSHA256':sha(__file__),'GLBSHA256':sha(R/'character.glb'),'threads':2,'device':'CPU','views':[],'neckDeformation':'Unmeasured until static actual views reviewed','contactsAndRig':'UNMEASURED; static assembly only'}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'character.glb'));scene=bpy.context.scene
report['reimport']=[]
for o in scene.objects:
 if o.type!='MESH':continue
 report['reimport'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.polygons),'UVLayers':[x.name for x in o.data.uv_layers],'materials':[m.name for m in o.data.materials],'materialFaceCounts':dict(Counter(p.material_index for p in o.data.polygons)),'materialImageNodes':{m.name:[{'image':n.image.name,'size':list(n.image.size)} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] for m in o.data.materials if m.use_nodes}})
world=bpy.data.worlds.new('Matched studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.50))-o.location).to_track_quat('-Z','Y').to_euler()
gray=bpy.data.materials.new('Matched neutral gray diagnostic');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
cd=bpy.data.cameras.new('Actual GLB matching evidence');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
views=[('neck-front',0,(0,.015,1.53),.45),('neck-profile',90,(0,.015,1.53),.45),('neck-rear',180,(0,.015,1.53),.45),('neck-three-quarter',45,(0,.015,1.53),.45),('full-front',0,(0,0,.90),1.96),('full-rear',180,(0,0,.90),1.96),('face-front',0,(0,-.018,1.66),.255),('face-profile',90,(0,-.018,1.66),.255)]
try:
 for label,yaw,t,scale in views:
  target=Vector(t);a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.03));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
  for mode in ['pbr','gray']:
   if time.time()>deadline-35:report['unfinished']='Deadline halted remaining views';raise TimeoutError('Original lane deadline reached')
   scene.view_layers[0].material_override=gray if mode=='gray' else None
   path=O/f'{mode}-{label}.png';scene.render.filepath=str(path);start=time.monotonic();bpy.ops.render.render(write_still=True)
   report['views'].append({'label':label,'mode':mode,'yaw':yaw,'target':t,'scale':scale,'path':str(path),'sha256':sha(path),'seconds':time.monotonic()-start})
   (O/'reimport-and-renders.json').write_text(json.dumps(report,indent=2)+'\n')
finally:
 report['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['GLBSHA256After']=sha(R/'character.glb');assert report['GLBSHA256After']==report['GLBSHA256'];(O/'reimport-and-renders.json').write_text(json.dumps(report,indent=2)+'\n');print('REIMPORT_FROZEN',len(report['views']),flush=True)
