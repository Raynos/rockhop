"""Read-only raw display correction, after immutable rejected-display checkpoint50."""
import bpy,numpy as np,json,hashlib,math,time,datetime,sys,os
from pathlib import Path
from mathutils import Vector,Matrix
BASE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern')
OUT=BASE/'raw-hood01-display-correction';OUT.mkdir(exist_ok=True)
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/01')
phase=sys.argv[-1];assert phase in ['front','remaining']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
deadline=datetime.datetime(2026,10,1,3,2,2,tzinfo=datetime.timezone.utc).timestamp()
paths=[R/p for p in ['raw-shape.glb','raw-shape.npz','working-display2.glb']]
original=json.loads((BASE/'whole-hood-donor-comparison/manifest.json').read_text())['candidates']['01']
if phase=='front':
 assert not (OUT/'report.json').exists()
 raw=np.load(R/'raw-shape.npz')
 report={'status':'UNACCEPTED read-only raw hood display correction; parent judges','actualStartUTC':'2026-10-01 02:52:02 UTC','deadlineUTC':'2026-10-01 03:02:02 UTC','sourceSHA256':{str(p):sha(p) for p in paths},'rawNPZCounts':{k:list(raw[k].shape) for k in ['vertices','faces']},'retainedHigherResolutionRaw':True,'sourceGeometryUVMaterialUnchanged':True,'previousDisplayFailureRetained':'whole-hood-donor-comparison/raw-display-failure.json','displayCorrection':'Remove worldX180. GLTF importer raw is already+Zup/front-Y. Use exact previous textured-source canonical uniform1.8m display normalizer. No mesh edits or source writes.','views':[],'canonicalMatrix':original['normalization']['canonicalMatrix'],'recipeSHA256':sha(__file__),'CPUThreads':2,'GPU':False,'executable':bpy.app.binary_path,'Blender':bpy.app.version_string,'Python':sys.version,'numpy':np.__version__,'isolatedEnvironment':{k:os.environ.get(k) for k in ['BLENDER_USER_CONFIG','BLENDER_USER_SCRIPTS','BLENDER_USER_EXTENSIONS','TMPDIR']}}
else:report=json.loads((OUT/'report.json').read_text());assert len(report['views'])==1
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'raw-shape.glb'));bpy.context.view_layer.update();scene=bpy.context.scene;objects=[o for o in scene.objects if o.type=='MESH'];canon=Matrix(report['canonicalMatrix']);data=[]
for o in objects:
 old=o.matrix_world.copy();o.parent=None;o.matrix_world=canon@old
 data.append({'object':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'meshCoordinateSHA':hashlib.sha256(np.array([v.co[:] for v in o.data.vertices],dtype=np.float32).tobytes()).hexdigest(),'matrix':[list(r) for r in o.matrix_world]})
report['rawImportedObjects']=data
world=bpy.data.worlds.new('Matched source studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.46))-o.location).to_track_quat('-Z','Y').to_euler()
gray=bpy.data.materials.new('Source geometry neutralgray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65;scene.view_layers[0].material_override=gray
cd=bpy.data.cameras.new('Matched raw hood');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.70
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
try:
 for name,yaw in ([('front',0)] if phase=='front' else [('profile',90),('rear',180)]):
  if time.time()>deadline-20:raise TimeoutError('Original10min CPU display cap')
  target=Vector((0,.010,1.46));a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.025));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=OUT/f'raw-gray-hood-{name}.png';assert not p.exists();scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);report['views'].append({'name':name,'yawDegrees':yaw,'cameraLocation':list(cam.location),'target':list(target),'orthoScale':cd.ortho_scale,'path':str(p),'sha256':sha(p)})
finally:
 report['finishedPhaseUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['sourceSHAAfter']={str(p):sha(p) for p in paths};report['sourceHashesUnchanged']=report['sourceSHA256']==report['sourceSHAAfter'];assert report['sourceHashesUnchanged'];(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('RAW_DISPLAY_PHASE_FROZEN',phase,flush=True)
