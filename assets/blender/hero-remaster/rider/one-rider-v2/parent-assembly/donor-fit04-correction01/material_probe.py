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
 target=Vector(target);a=math.radians(yaw);camera.location=target+Vector((4*math.sin(a),-4*math.cos(a),elevation));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=scale;scene.render.resolution_x=size[0];scene.render.resolution_y=size[1];scene.render.resolution_percentage=100;path=O/(name+'.png');scene.render.filepath=str(path);t=time.monotonic();bpy.ops.render.render(write_still=True);rows.append({'path':str(path),'SHA256':sha(path),'cameraMatrix':[list(r) for r in camera.matrix_world],'target':list(target),'scale':scale,'yawDegrees':yaw,'size':list(size),'wallSeconds':time.monotonic()-t});(O/'material-probe-progress.json').write_text(json.dumps(rows,indent=2)+'\n')
materials=[m for m in bpy.data.materials if m.use_nodes];state=[];nodeReport=[]
for mat in materials:
 p=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:continue
 if 'garment' not in mat.name.lower() and 'Material' not in mat.name:continue
 # Source object has the garment plus whitebust material names; inspect every sourcegraph, but modify only garment slots.
 garment=next(o for o in scene.objects if o.type=='MESH' and 'protected' in o.name)
 if mat not in list(garment.data.materials):continue
 if list(garment.data.materials).index(mat)==1:continue
 nodeReport.append({'material':mat.name,'inputs':{i.name:[{'node':l.from_node.type,'image':l.from_node.image.name if l.from_node.type=='TEX_IMAGE' and l.from_node.image else None} for l in i.links] for i in p.inputs if i.is_linked}})
 state.append((mat,p,[(l.from_socket,l.to_socket) for l in p.inputs['Normal'].links],[(l.from_socket,l.to_socket) for l in p.inputs['Base Color'].links],p.inputs['Base Color'].default_value[:]))
for mat,p,norm,base,value in state:
 for l in list(p.inputs['Normal'].links):mat.node_tree.links.remove(l)
for name,yaw in [('front',0),('rear',180)]:view('probe-no-normal-'+name,(0,0,1.505),.48,yaw,size=(640,640))
for mat,p,norm,base,value in state:
 for a,b in norm:mat.node_tree.links.new(a,b)
 for l in list(p.inputs['Base Color'].links):mat.node_tree.links.remove(l)
 p.inputs['Base Color'].default_value=(.48,.29,.12,1)
for name,yaw in [('front',0),('rear',180)]:view('probe-flat-base-'+name,(0,0,1.505),.48,yaw,size=(640,640))
(O/'material-node-witness.json').write_text(json.dumps(nodeReport,indent=2)+'\n')
assert sha(source)==before;(O/'material-probe-report.json').write_text(json.dumps({'actualGLBSHA256':before,'sourceUnchanged':True,'CPUThreads':2,'GPUJob':False,'views':rows,'limits':'Static private model only; no motion/rig or gameplay acceptance'},indent=2)+'\n')
