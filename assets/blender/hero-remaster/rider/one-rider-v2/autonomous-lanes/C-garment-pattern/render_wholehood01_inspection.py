"""Actual masked NEW donor hood PBR/gray before any receiver changes."""
import bpy,math,json,datetime,hashlib
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern/wholehood01-trial01');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/wholehood01-trial01');bpy.ops.wm.open_mainfile(filepath=str(R/'donor-mask-inspection.blend'));scene=bpy.context.scene
world=bpy.data.worlds.new('Matched source studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power in [('Key',(3,-4,4),600),('Fill',(-3,-2,2.5),350),('Rim',(1,3,3),450)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.46))-o.location).to_track_quat('-Z','Y').to_euler()
gray=bpy.data.materials.new('Matched neutralgray');gray.use_nodes=True;p=gray.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.42,.42,1);p.inputs['Roughness'].default_value=.65
cd=bpy.data.cameras.new('Matched maskedhood');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=.50;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';views=[]
for mode in ['pbr','gray']:
 for name,yaw in [('front',0),('profile',90),('rear',180),('three-quarter',45)]:
  target=Vector((0,.010,1.48));a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),.025));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.view_layers[0].material_override=gray if mode=='gray' else None;out=O/f'inspection-{mode}-hood-{name}.png';assert not out.exists();scene.render.filepath=str(out);bpy.ops.render.render(write_still=True);views.append(str(out))
(O/'mask-render-report.json').write_text(json.dumps({'status':'Unaccepted source-only mask inspection, receiver unchanged','finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'views':views,'CPUThreads':2,'recipeSHA':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
