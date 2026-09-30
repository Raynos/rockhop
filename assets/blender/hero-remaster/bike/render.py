import bpy,sys,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
src=Path(sys.argv[-2]).resolve();out=Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
for o in bpy.context.scene.objects:
 if 'blur' in o.name:o.hide_render=True
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=720;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('review-world');scene.world.color=(.19,.19,.19)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((0,-3,4),900,4),((2,2,2),1000,3),((-2,1,2),600,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;aim(l,(.6,0,.25))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.345));floor=bpy.context.object;floor.name='review-floor';m=bpy.data.materials.new('review-floor');m.diffuse_color=(.07,.075,.085,1);floor.data.materials.append(m)
bpy.ops.object.camera_add(location=(2.3,-3,1.4));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.6;scene.camera=cam;aim(cam,(.64,0,.24))
out.parent.mkdir(parents=True,exist_ok=True)
if out.suffix=='.png':
 scene.render.filepath=str(out);bpy.ops.render.render(write_still=True)
else:
 scene.eevee.taa_render_samples=12
 frame_dir=out.parent/'frames'/out.stem;frame_dir.mkdir(parents=True,exist_ok=True)
 for i in range(48):
  angle=-math.pi/2+math.tau*i/48
  cam.location=(.64+3*math.cos(angle),3*math.sin(angle),1.15);aim(cam,(.64,0,.24))
  scene.render.filepath=str(frame_dir/f'{i:03d}.png');bpy.ops.render.render(write_still=True)
 import subprocess
 subprocess.run(['ffmpeg','-y','-framerate','12','-i',str(frame_dir/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','19',str(out)],check=True)
