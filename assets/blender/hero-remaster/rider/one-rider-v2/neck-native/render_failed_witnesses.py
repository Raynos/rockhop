"""Matched CPU gray witnesses of preserved open collar and exact failed prefix."""
import bpy,json,hashlib,math,time
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/neck-native')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
settings={'backend':'Cycles CPU','threads':4,'samples':16,'resolution':[640,640],'target':[0,.015,1.58],'orthoScale':.5,'yaws':[0,90,180,45],'material':'Diagnostic gray; no head or join invented'}
for label,path,out in [('baseline-open-retained-collar',R/'collar-trial1/body-open-collar.glb',O/'baseline'),('trial02-failed-open-prefix',R/'neck-native/trial02/failed-strip.glb',O/'trial02')]:
 out.mkdir(parents=True,exist_ok=True)
 if (out/'gray-witness.json').exists():raise RuntimeError('Frozen witness exists')
 before=sha(path);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));scene=bpy.context.scene
 gray=bpy.data.materials.new('Geometry diagnostic only neutral gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
 for o in scene.objects:
  if o.type=='MESH':o.data.materials.clear();o.data.materials.append(gray)
 world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
 for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.58))-o.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('Native collar geometry closeup');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.50
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';views=[]
 for view,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:
  target=Vector((0,.015,1.58));angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),.08));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=out/f'gray-{view}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);views.append({'label':view,'file':str(p),'sha256':sha(p)})
 assert sha(path)==before
 (out/'gray-witness.json').write_text(json.dumps({'status':label+'; unaccepted diagnostic only','source':str(path),'sourceSHA256':before,'sourceSHA256After':sha(path),'recipeSHA256':sha(Path(__file__)),'settings':settings,'views':views,'newHeadOrJoinAdded':False},indent=2)+'\n')
print('WITNESSES_FROZEN',flush=True)
