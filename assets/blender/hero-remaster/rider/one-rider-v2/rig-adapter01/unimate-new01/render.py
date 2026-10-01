"""Actual exported neural and GT animation in matched fixed-camera CPU renders."""
from pathlib import Path
import bpy,math,sys,json,hashlib
from mathutils import Vector
P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/unimate-new01');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01');args=sys.argv[sys.argv.index('--')+1:];kind=args[args.index('--kind')+1];assert kind in ['gt','raw'];preview='--preview' in args
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/(kind+'-animated.glb')));meshes=[o for o in scene.objects if o.type=='MESH'];rig=next(o for o in scene.objects if o.type=='ARMATURE');scene.frame_set(0);bpy.context.view_layer.update()
# Fixed canonical-frame camera/floor/bench for both clips; never reframe a bad pose.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX';scene.render.resolution_x=320;scene.render.resolution_y=400;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Neutral');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
mat=bpy.data.materials.new('Neutral bench');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.22,.22,.22,1)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-.50,.10));bench=bpy.context.object;bench.name='Same diagnostic bench';bench.scale=(.55,.36,.39);bench.data.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-.099));bpy.context.object.data.materials.append(mat)
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.size=size;lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,1))-lo.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Actual canonical motion');camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);scene.camera=camera;cd.type='ORTHO';cd.ortho_scale=1.9
receipts=[];frames=[0] if preview else list(range(0,57,2))
for yaw in ([0] if preview else [0,90]):
 a=math.radians(yaw);target=Vector((0,0,.68));camera.location=target+Vector((4*math.sin(a),4*math.cos(a),0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for i,f in enumerate(frames):
  scene.frame_set(f);bpy.context.view_layer.update();path=O/(f'preview-{kind}.png' if preview else f'actual-{kind}-{yaw:03d}-{i+1:04d}.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);receipts.append({'sampleFrame':f,'timeSeconds':f/30,'yaw':yaw,'file':str(path),'SHA256':hashlib.sha256(path.read_bytes()).hexdigest()})
(O/(kind+('-preview' if preview else '-render')+'-receipt.json')).write_text(json.dumps({'kind':kind,'sourceGLB':str(P/(kind+'-animated.glb')),'frames':receipts,'CPUthreads':2,'GPUjob':False,'scope':'Actual exported canonical motion; no restored player rig/contact claim'},indent=2)+'\n')
