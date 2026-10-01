"""Direct visible PAINTED source first: four labelled display rotations only.

No raw geometry/index/coordinate matching prerequisite. Not matched evidence or
an anatomy/rig/contact pass. The parent chooses the observed actual orientation.
"""
import bpy,json,hashlib,math,time
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit');source=R/'generation/h21-buzz-native01/model.glb'
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/painted-orientation-witness01');O.mkdir(exist_ok=True)
if (O/'manifest.json').exists():raise RuntimeError('Frozen orientation witness exists')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sourcehash=sha(source);views=[]
for label,angle in [('identity',0),('X90',90),('X180',180),('X270',270)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));scene=bpy.context.scene
 meshes=[o for o in scene.objects if o.type=='MESH'];roots=[o for o in scene.objects if o.parent is None]
 align=bpy.data.objects.new('Labelled display rotation only',None);scene.collection.objects.link(align)
 for obj in roots:matrix=obj.matrix_world.copy();obj.parent=align;obj.matrix_world=matrix
 align.rotation_euler.x=math.radians(angle);bpy.context.view_layer.update()
 points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)]);centre=(lo+hi)*.5;scale=.55/max(hi-lo)
 norm=bpy.data.objects.new('Whole-bust uniform display framing only',None);scene.collection.objects.link(norm);align.parent=norm;norm.scale=(scale,)*3;norm.location=-centre*scale+Vector((0,0,1.5));bpy.context.view_layer.update()
 materials=[{'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.polygons),'names':[m.name if m else None for m in o.data.materials]} for o in meshes]
 world=bpy.data.worlds.new('Common neutral gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world;target=Vector((0,0,1.5))
 for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Actual painted orientation diagnostic');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=.7;cam.location=target+Vector((0,-4,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 path=O/f'actual-painted-{label}.png';scene.render.filepath=str(path);start=time.perf_counter();bpy.ops.render.render(write_still=True)
 row={'label':label,'displayXRotationDegrees':angle,'path':str(path),'SHA256':sha(path),'wholeBoundsBeforeDisplay':[list(lo),list(hi)],'displayScale':scale,'translation':list(norm.location),'cameraMatrix':[list(r) for r in cam.matrix_world],'materialsUnchanged':materials,'wallSeconds':time.perf_counter()-start};views.append(row)
 (O/'progress.json').write_text(json.dumps({'status':'Actual painted orientation witnesses, no raw match or acceptance claimed','lastCompleted':row},indent=2)+'\n')
assert sha(source)==sourcehash
(O/'manifest.json').write_text(json.dumps({'status':'UNACCEPTED direct painted whole-bust orientation diagnostic','source':str(source),'sourceSHA256':sourcehash,'sourceSHA256After':sha(source),'recipeSHA256':sha(Path(__file__)),'CPUThreads':2,'samples':24,'resolution':[640,640],'orthoScale':.7,'views':views,'rawOrCoordinateGuardBeforeDisplay':False,'limits':['Different uniform display framing for rotated whole bounds, not matched raw geometry.','Native PBR/geometry/UV source unchanged; no saved mesh derivatives.','Parent alone chooses actual orientation and scores appearance.','No rig/contacts/motion/gameplay gate measured.']},indent=2)+'\n');print('PAINTED_WITNESSES_FROZEN',len(views),flush=True)
