"""Actual GLB turntable, CPU2. No new construction or rig claim."""
import bpy,json,math,time,datetime,hashlib
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01/turntable');O.mkdir(exist_ok=True)
assert not (O/'manifest.json').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=sha(R/'character.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'character.glb'));s=bpy.context.scene
w=bpy.data.worlds.new('Matched gray studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);w.node_tree.nodes['Background'].inputs[1].default_value=.65;s.world=w
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual turntable');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=.56
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
frames=[]
for i in range(36):
 if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,1,2,16,30,tzinfo=datetime.timezone.utc):break
 a=math.radians(i*10);target=Vector((0,.012,1.525));cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.035));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();path=O/f'{i:04d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append({'i':i,'yawDegrees':i*10,'path':str(path),'sha256':sha(path)})
assert sha(R/'character.glb')==source
(O/'manifest.json').write_text(json.dumps({'status':'UNACCEPTED actual GLB turntable; no deformation/rig claim','sourceSHA256':source,'recipeSHA256':sha(__file__),'frames':frames,'CPUThreads':2,'finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
