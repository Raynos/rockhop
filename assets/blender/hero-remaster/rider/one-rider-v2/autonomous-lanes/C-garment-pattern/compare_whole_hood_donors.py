"""Read-only NEW H21-01/02/03/05 whole-hood comparison; no cuts or geometry edits.

PBR working-display2 sources keep native materials. Higher-resolution raw sources
are separately rendered gray with documented orientation and matched PBR transform.
"""
import bpy,numpy as np,json,hashlib,math,time,datetime,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/whole-hood-donor-comparison')
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern/whole-hood-donor-comparison')
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
assert not (OUT/'manifest.json').exists(),'Frozen comparison cannot be overwritten'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();deadline=datetime.datetime(2026,10,1,2,56,10,tzinfo=datetime.timezone.utc).timestamp()
report={'status':'UNACCEPTED read-only NEW wholehood donor comparison; no extraction/direction selected','actualStartUTC':'2026-10-01 02:36:10 UTC','deadlineUTC':'2026-10-01 02:56:10 UTC','recipeSHA256':sha(__file__),'CPUThreads':2,'device':'CPU','retiredOldH21_04LineageNotUsed':True,'candidates':{},'views':[],'limitations':['Source heads/hands/bodies are comparison-only; only wholehood alternatives are evaluated.','Matched gray/PBR renders establish visible source shape, not isolated hood topology or rig compatibility.','Lighting/camera are matched across actual sources; mockup lighting differs, so no calibrated7/10 acceptance claim.']}
for i in ['01','02','03','05']:
 paths=[R/i/n for n in ['working-display2.glb','model.glb','raw-shape.glb','raw-shape.npz','generation.json']]
 raw=np.load(R/i/'raw-shape.npz')
 report['candidates'][i]={'name':'H21-'+i,'sources':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths},'preservedHighResolutionRawShapes':{k:list(raw[k].shape) for k in ['vertices','faces']},'rawSeparateFromTexturedReduction':True,'normalization':None}
def setup(i,raw=False):
 bpy.ops.wm.read_factory_settings(use_empty=True);p=R/i/('raw-shape.glb' if raw else 'working-display2.glb');bpy.ops.import_scene.gltf(filepath=str(p));bpy.context.view_layer.update();scene=bpy.context.scene;objects=[o for o in scene.objects if o.type=='MESH']
 # Working-display2 has a corrected -90deg fileX root against glTF's +90deg import.
 # Raw native file has generator -Y-up; after import, rotate worldX180 for upright.
 orientation=Matrix.Rotation(math.pi,4,'X') if raw else Matrix.Identity(4)
 points=np.array([list(orientation@o.matrix_world@v.co) for o in objects for v in o.data.vertices]);lo,hi=points.min(0),points.max(0)
 if not raw:
  scale=1.8/float(hi[2]-lo[2]);origin=[float((lo[0]+hi[0])/2),float((lo[1]+hi[1])/2),float(lo[2])];canon=Matrix.Scale(scale,4)@Matrix.Translation(Vector(origin)*-1)
  report['candidates'][i]['normalization']={'sourceBoundsBlender':[lo.tolist(),hi.tolist()],'heightOldHairInclusiveM':1.8,'scale':scale,'origin':origin,'canonicalMatrix':[list(row) for row in canon],'workingSourceOrientation':'Corrected source root -90deg fileX; actual Blender world+Zup, frontal camera-Y','rawSourceOrientation':'Native generator-Yup; imported raw rotates worldX180deg; SAME PBR canonical transform used'}
 else:canon=Matrix(report['candidates'][i]['normalization']['canonicalMatrix'])
 object_records=[]
 for o in objects:
  old=o.matrix_world.copy();o.parent=None;o.matrix_world=canon@orientation@old
  object_records.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'actualSourceToDisplayMatrix':[list(row) for row in o.matrix_world],'materialSlots':[m.name for m in o.data.materials]})
 key='rawObjects' if raw else 'texturedObjects';report['candidates'][i][key]=object_records
 world=bpy.data.worlds.new('Common matched donor studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
 for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.46))-o.location).to_track_quat('-Z','Y').to_euler()
 gray=bpy.data.materials.new('Native geometry matched gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
 cd=bpy.data.cameras.new('Wholehood matched camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 return scene,cam,gray
def render(i,scene,cam,gray,label,yaw,mode,raw=False,torso=False):
 if time.time()>deadline-35:raise TimeoutError('Original20minute comparison cap reached')
 folder=OUT/i;folder.mkdir(exist_ok=True);target=Vector((0,.010,1.34 if torso else 1.46));a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.025));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.02 if torso else .70
 scene.view_layers[0].material_override=gray if mode=='gray' else None;path=folder/f'{"raw-" if raw else ""}{mode}-{label}.png';scene.render.filepath=str(path);start=time.monotonic();bpy.ops.render.render(write_still=True)
 report['views'].append({'candidate':'H21-'+i,'source':'higher-resolution pre-reduction RAW' if raw else 'textured working-display2 reduction','label':label,'yawDegrees':yaw,'mode':mode,'target':list(target),'scale':cam.data.ortho_scale,'path':str(path),'sha256':sha(path),'wallSeconds':time.monotonic()-start});(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
try:
 # First actual frontal/profile PBR witnesses for ALL four sources.
 for i in ['01','02','03','05']:
  scene,cam,gray=setup(i);render(i,scene,cam,gray,'hood-front',0,'pbr');render(i,scene,cam,gray,'hood-profile',90,'pbr')
 for i in ['01','02','03','05']:
  scene,cam,gray=setup(i)
  for label,yaw in [('hood-front',0),('hood-profile',90),('hood-rear',180)]:
   if yaw==180:render(i,scene,cam,gray,label,yaw,'pbr')
   render(i,scene,cam,gray,label,yaw,'gray')
  for mode in ['pbr','gray']:render(i,scene,cam,gray,'torso-front',0,mode,torso=True)
  scene,cam,gray=setup(i,True)
  for label,yaw in [('hood-front',0),('hood-profile',90),('hood-rear',180)]:render(i,scene,cam,gray,label,yaw,'gray',True)
finally:
 report['finishedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['sourceHashesAfter']={p:sha(p) for c in report['candidates'].values() for p in c['sources']};assert all(report['sourceHashesAfter'][p]==m['sha256'] for c in report['candidates'].values() for p,m in c['sources'].items());report['allSourcesUnchanged']=True;(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('DONOR_COMPARISON_FROZEN',len(report['views']),report['finishedUTC'],flush=True)
