from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec((ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0])
OUT=ROOT/'hoodie-repair02'
for o in bikeobjects:o.hide_render=True
original={o:list(o.data.materials)for o in meshes};gray=mat('neutral repaired garment',(.42,.42,.42));sc.cycles.samples=4;sc.render.resolution_x=sc.render.resolution_y=480
cases=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else ['r1-control-rest-0','r1-shape-rest-0','r1-weights-rest-0','r1-control-raise-1','r1-weights-raise-1','r1-control-sit-1','r1-weights-sit-1']
for name in cases:
 dat=np.load(OUT/'poses'/f'{name}.npz');posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
 for o,ix in zip(meshes,maps):o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update();o.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(o.data.vertices))
 for app in ['pbr','gray']:
  for o in meshes:
   for k in range(len(o.data.materials)):o.data.materials[k]=gray if app=='gray'else original[o][k]
  for angle,view in [(0,'front'),(90,'side'),(180,'rear')]:
   tar=Vector((.64,0,1.18))if 'sit'not in name else Vector((-.10,0,1.0));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.1));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=1.75 if 'raise'in name else 1.20
   file=OUT/'renders'/f'{name}-{app}-{view}.png'
   if not file.exists():sc.render.filepath=str(file);bpy.ops.render.render(write_still=True)
print('REPAIR CPU FRAMES COMPLETE')
