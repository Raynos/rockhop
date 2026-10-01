"""Actual private complete rider GLB views, CPU only with fixed cameras."""
import bpy,json,math,hashlib,time
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit04-correction01');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit04-correction01');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=R/'rider.glb';before=sha(source)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Actual complete rider');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';scene.render.image_settings.file_format='PNG';rows=[]
def view(name,target,scale,yaw,elevation=0,size=(768,960)):
 target=Vector(target);a=math.radians(yaw);camera.location=target+Vector((4*math.sin(a),-4*math.cos(a),elevation));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=scale;scene.render.resolution_x=size[0];scene.render.resolution_y=size[1];scene.render.resolution_percentage=100;path=O/(name+'.png');scene.render.filepath=str(path);t=time.monotonic();bpy.ops.render.render(write_still=True);rows.append({'path':str(path),'SHA256':sha(path),'cameraMatrix':[list(r) for r in camera.matrix_world],'target':list(target),'scale':scale,'yawDegrees':yaw,'size':list(size),'wallSeconds':time.monotonic()-t});(O/'render-progress.json').write_text(json.dumps(rows,indent=2)+'\n')
for name,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:view('neck-PBR-'+name,(0,0,1.505),.48,yaw,size=(640,640))
for name,yaw in [('front',0),('profile',90),('three-quarter',45),('rear',180)]:view('face-PBR-'+name,(0,0,1.666),.38,yaw,size=(640,640))
for n,yaw in enumerate([0,45,90,135,180,225,270,315,0]):view('full-PBR-'+str(n+1),(0,0,.91),2.03,yaw,.9 if n==8 else 0)
assert sha(source)==before;(O/'render-report.json').write_text(json.dumps({'actualGLBSHA256':before,'sourceUnchanged':True,'CPUThreads':2,'GPUJob':False,'views':rows,'limits':'Static private model only; no motion/rig or gameplay acceptance'},indent=2)+'\n')
