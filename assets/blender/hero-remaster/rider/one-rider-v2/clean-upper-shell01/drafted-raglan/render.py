import bpy, math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan')
E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan');F=R/'frames';F.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'neutral-assembly01.glb'))
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Neutral world');sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.resolution_x=400;sc.render.resolution_y=450;sc.render.resolution_percentage=100;sc.world.color=(.3,.3,.3);sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='Standard'
for loc,power,size in [((3,-3,4),450,4),((-2,2,3),300,3),((.7,0,4),150,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((.65,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.05
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035))
gray=bpy.data.materials.new('Neutral construction gray');gray.diffuse_color=(.42,.42,.42,1);gray.use_nodes=True;gray.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.42,.42,1);gray.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
origin=Vector((.645,0,.91))
def camera(angle):
 cam.location=origin+Vector((3*math.cos(angle),3*math.sin(angle),.08));cam.rotation_euler=(origin-cam.location).to_track_quat('-Z','Y').to_euler()
for mode in ['pbr','gray']:
 sc.view_layers[0].material_override=gray if mode=='gray' else None
 for label,ang in [('front',0),('side',-math.pi/2),('back',math.pi)]:
  camera(ang);sc.render.filepath=str(E/f'{mode}-{label}.png');bpy.ops.render.render(write_still=True)
 for frame in range(24):
  camera(2*math.pi*frame/24);sc.render.filepath=str(F/f'{mode}-{frame:03d}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'neutral-render01.blend'));print('RENDER_COMPLETE_CPU_4SAMPLES_54FRAMES')
