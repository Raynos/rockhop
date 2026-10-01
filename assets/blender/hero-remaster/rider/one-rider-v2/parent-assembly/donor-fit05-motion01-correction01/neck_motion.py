"""Actual private complete rider GLB views, CPU only with fixed cameras."""
import bpy,json,math,hashlib,time
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit05');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit05-motion01-correction01');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=R/'rider.glb';before=sha(source)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Actual complete rider');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO';scene.render.image_settings.file_format='PNG';rows=[]
def view(name,target,scale,yaw,elevation=0,size=(768,960)):
 target=Vector(target);a=math.radians(yaw);camera.location=target+Vector((4*math.sin(a),-4*math.cos(a),elevation));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=scale;scene.render.resolution_x=size[0];scene.render.resolution_y=size[1];scene.render.resolution_percentage=100;path=O/(name+'.png');scene.render.filepath=str(path);t=time.monotonic();bpy.ops.render.render(write_still=True);rows.append({'path':str(path),'SHA256':sha(path),'cameraMatrix':[list(r) for r in camera.matrix_world],'target':list(target),'scale':scale,'yawDegrees':yaw,'size':list(size),'wallSeconds':time.monotonic()-t});(O/'neck-motion-progress.json').write_text(json.dumps(rows,indent=2)+'\n')
# Private three-bone anatomical motion fixture, NOT final nineteen-bone rig.
from mathutils import Matrix
head=next(o for o in scene.objects if o.type=='MESH' and 'protected' not in o.name.lower());world=head.matrix_world.copy();rest=[world@v.co for v in head.data.vertices]
for v,p in zip(head.data.vertices,rest):v.co=p
head.matrix_world=Matrix.Identity(4);head.data.update()
fixtureData=bpy.data.armatures.new('Private neck motion fixture');rig=bpy.data.objects.new(fixtureData.name,fixtureData);scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');chest=fixtureData.edit_bones.new('fixture.chest');chest.head=(0,0,1.3);chest.tail=(0,0,1.525);neck=fixtureData.edit_bones.new('fixture.neck');neck.head=(0,0,1.525);neck.tail=(0,0,1.61);neck.parent=chest;hb=fixtureData.edit_bones.new('fixture.head');hb.head=(0,0,1.61);hb.tail=(0,0,1.8);hb.parent=neck;bpy.ops.object.mode_set(mode='OBJECT')
groups=[head.vertex_groups.new(name=n) for n in ['fixture.chest','fixture.neck','fixture.head']]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for v in head.data.vertices:
 n=smooth((v.co.z-1.525)/.065);h=smooth((v.co.z-1.59)/.04);w=[1-n,n*(1-h),n*h];assert abs(sum(w)-1)<1e-9
 for g,a in zip(groups,w):
  if a>0:g.add([v.index],a,'REPLACE')
mod=head.modifiers.new('Actual private three-bone neck motion','ARMATURE');mod.object=rig
for p in rig.pose.bones:p.rotation_mode='XYZ'
controls=[(0,0,0),(3,30,0),(6,0,15),(9,-30,-15),(11,0,0)]
poses=[]
for frame in range(1,37):
 t=(frame-1)%12
 for (a,y0,b0),(b,y1,b1) in zip(controls,controls[1:]):
  if a<=t<=b:
   u=(t-a)/(b-a);yaw=y0*(1-u)+y1*u;bend=b0*(1-u)+b1*u;break
 rig.pose.bones['fixture.head'].rotation_euler=(0,math.radians(yaw),0);rig.pose.bones['fixture.neck'].rotation_euler=(math.radians(bend),0,0)
 for p in rig.pose.bones:p.keyframe_insert('rotation_euler',frame=frame)
 poses.append({'frame':frame,'cameraYaw':[0,90,180][(frame-1)//12],'headYawDegrees':yaw,'neckBendDegrees':bend})
scene.frame_start=1;scene.frame_end=36;scene.render.fps=12
for row in poses:
 frame=row['frame'];scene.frame_set(frame);bpy.context.view_layer.update();view('neck-motion-'+str(frame).zfill(4),(0,0,1.565),.52,row['cameraYaw'],size=(512,512))
 deps=bpy.context.evaluated_depsgraph_get();evaluated=head.evaluated_get(deps);mesh=evaluated.to_mesh();row['evaluatedVertexCount']=len(mesh.vertices);row['allEvaluatedCoordinatesFinite']=all(all(math.isfinite(c) for c in v.co) for v in mesh.vertices);evaluated.to_mesh_clear()
 assert row['allEvaluatedCoordinatesFinite']
scene.frame_set(1);M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit05-motion01-correction01');bpy.ops.wm.save_as_mainfile(filepath=str(M/'neck-fixture.blend'));bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);head.select_set(True)
for o in scene.objects:
 if o.type=='MESH' and 'protected' in o.name.lower():o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(M/'neck-fixture.glb'),export_format='GLB',use_selection=True,export_animations=True,export_skins=True)
assert sha(source)==before;(O/'neck-motion-report.json').write_text(json.dumps({'actualSourceGLBSHA256':before,'sourceUnchanged':True,'temporaryFixtureBones':3,'final19BoneRig':False,'weights':'Smooth anatomical worldZ heightbands1.525-1.63, hidden lowerbust chestanchored','poses':poses,'renderFrames':rows,'fixtureGLBSHA256':sha(M/'neck-fixture.glb'),'limits':'Diagnostic neck deformation only; no sitting/lean/IK/contact or runtimecontract qualification'},indent=2)+'\n')
