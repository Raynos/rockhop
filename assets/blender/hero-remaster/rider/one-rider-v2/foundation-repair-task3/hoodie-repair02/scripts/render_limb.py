from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec((ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0])
OUT=ROOT/'hoodie-repair02'
for o in bikeobjects:o.hide_render=True
original={o:list(o.data.materials)for o in meshes};gray=mat('neutral cuff diagnostic',(.42,.42,.42));sc.cycles.samples=8;sc.render.resolution_x=sc.render.resolution_y=480
for case in ['source','anatomical']:
 for t in ['-1','1']:
  dat=np.load(OUT/'rig-lane/limb-poses'/f'{case}-wrist-{t}.npz');posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
  for o,ix in zip(meshes,maps):o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update();o.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(o.data.vertices))
  for app in ['pbr','gray']:
   for o in meshes:
    for k in range(len(o.data.materials)):o.data.materials[k]=gray if app=='gray'else original[o][k]
   for angle,view in [(0,'front'),(90,'side')]:
    tar=Vector((.64,-.36,.86));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.05));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=.38
    sc.render.filepath=str(OUT/'renders'/f'cuff-{case}-{t}-{app}-{view}.png');bpy.ops.render.render(write_still=True)
print('CUFF REPAIR CPU FRAMES COMPLETE')
