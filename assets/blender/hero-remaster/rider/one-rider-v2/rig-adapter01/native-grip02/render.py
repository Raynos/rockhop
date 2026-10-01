"""Literal open-wrap-open native skin geometry played from exported frame buffers."""
import bpy,json,hashlib,math,datetime
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip02';RUN=BASE/'rig-adapter01/native-grip02';MASTER=BASE/'parent-assembly/donor-fit05/rider.blend';BUFFER=RUN/'native-hand-animation.npz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(MASTER);frames=np.load(BUFFER);source=np.array(frames['sourcePositions']);positions=frames['framePositionsDQS'];ids=frames['sourceCompleteVertexIds'];centre=frames['cylinderCentre'];axis=frames['cylinderAxis'];radius=float(frames['cylinderRadius']);bpy.ops.wm.open_mainfile(filepath=str(MASTER));scene=bpy.context.scene;body=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));mesh=body.data;allpoints=np.array([v.co for v in mesh.vertices]);assert np.array_equal(allpoints[ids],source)
for o in list(scene.objects):
 if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
gray=bpy.data.materials.new('Actual moving neutral native skin');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.35,.35,.35,1);bs.inputs['Roughness'].default_value=.7
for o in scene.objects:
 if o.type=='MESH':
  for i in range(len(o.data.materials)):o.data.materials[i]=gray
mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops))
green=bpy.data.materials.new('Literal radius18mmhandle');green.use_nodes=True;bs=green.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.025,.24,.07,1);bs.inputs['Roughness'].default_value=.45
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=.160,location=centre);handle=bpy.context.object;handle.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();handle.data.materials.append(green)
world=bpy.data.worlds.new('Actual grip diagnosticstudio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(centre)-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Played native grip');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.29;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.render.fps=16;target=Vector(source.mean(0));target.z=.81
views=[];deadline=datetime.datetime.fromisoformat(json.loads((OUT/'setup.json').read_text())['hardDeadlineUTC'])
for mode in ['DQS','LBS']:
 positions=frames['framePositions'+mode]
 for label,yaw in [('front',0),('palm',180),('profile',90)]:
  folder=RUN/(mode+'-'+label);folder.mkdir(exist_ok=True);a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.05));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();files=[]
  for index,p in enumerate(positions):
   if datetime.datetime.now(datetime.timezone.utc)>=deadline:raise RuntimeError('Actualframebatchdeadline')
   handle.location=frames['frameCylinderCentres'][index];current=allpoints.copy();current[ids]=p;assert np.array_equal(current[np.setdiff1d(np.arange(len(current)),ids)],allpoints[np.setdiff1d(np.arange(len(current)),ids)]);mesh.vertices.foreach_set('co',current.ravel());mesh.update();scene.frame_set(index);path=folder/f'{index:03}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);files.append({'frame':index,'file':str(path),'sha256':sha(path)})
   if index in [0,8,16,24,32]:
    saved=OUT/f'actual-{mode}-{label}-{index:03}.png';saved.write_bytes(path.read_bytes())
  views.append({'skinMode':mode,'view':label,'frames':files,'sourcePlayedBufferSHA256':sha(BUFFER),'cameraTarget':list(target),'cameraPosition':list(cam.location),'orthoScale':cd.ortho_scale})
assert before==sha(MASTER);(OUT/'render-report.json').write_text(json.dumps({'status':'Actual same-pose DQS/LBS native skin comparison; handle entry has measuredintermediatepenetration; parentjudgmentpending','views':views,'CPUThreads':2,'sourceSHA256Before':before,'sourceSHA256After':sha(MASTER),'recipeSHA256':sha(Path(__file__)),'diagnosticNormals':'Recomputed deformed gray geometry normals; no PBR texture/normal preservation claim','fps':16,'framesPerView':len(positions),'movingHandleDisclosure':'Handle starts70mmoutsideactualpalm then enters anchor; do nothide12mmtransitionpenetration measuredinbuildreport'},indent=2)+'\n');print('ACTUAL_THREEVIEW_NATIVE_GRIP_PLAYED',flush=True)
