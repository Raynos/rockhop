"""Silent headless moving evidence: raw turntable or fitted clip/orbit.

blender -b --python render_orbit.py -- --input MODEL.glb --out frames --frames 48 --clip sit_cruise
Uses Blender lighting; actual Garage evidence is separately captured by parent.
"""
import bpy,sys,argparse,math
from pathlib import Path
from mathutils import Vector,Matrix
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--frames',type=int,default=48);ap.add_argument('--clip');ap.add_argument('--sample',type=int,default=12);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=24
bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
for o in bpy.data.objects:
 if o.type=='ARMATURE':
  if o.animation_data:
   o.animation_data.action=None
   for tr in o.animation_data.nla_tracks:tr.mute=True
  for pb in o.pose.bones:pb.matrix_basis=Matrix.Identity(4)
  if a.clip:
   action=bpy.data.actions.get(a.clip)
   assert action is not None,a.clip
   o.animation_data.action=action
   if action.slots:o.animation_data.action_slot=action.slots[0]
meshes=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and len(o.data.vertices)>100]
for o in meshes:
 for mat in o.data.materials:
  if mat and mat.use_nodes:
   for node in mat.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':node.inputs['Metallic'].default_value=0
pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
centre=(lo+hi)/2;size=max(hi[i]-lo[i] for i in range(3))
world=bpy.data.worlds.new('Neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.145,.17,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
for name,off,power,ls in [('Key',(3,-4,4),600,3),('Fill',(-3,3,2),450,3),('Rim',(-2,-3,4),600,2)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=ls*size
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=centre+Vector(off)*size;obj.rotation_euler=(centre-obj.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Moving orbit');cam=bpy.data.objects.new('Moving orbit',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=size*1.2
scene.render.engine='CYCLES';scene.cycles.samples=a.sample;scene.cycles.use_denoising=True;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
for frame in range(a.frames):
 angle=-math.pi/2+frame/a.frames*math.tau
 cam.location=centre+Vector((math.cos(angle)*size*3,math.sin(angle)*size*3,size*.35));cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.frame_set(round(frame/a.frames*48) if a.clip else 0)
 scene.render.filepath=str(out/f'{frame:04}.png');bpy.ops.render.render(write_still=True)
