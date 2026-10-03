from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec((ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0])
OUT=ROOT/'hoodie-repair02';frames=OUT/'renders/movie-v4';frames.mkdir(exist_ok=True);sc.render.resolution_x=sc.render.resolution_y=384;sc.cycles.samples=3
for k in range(49):
 for variant in ['control','candidate']:
  dat=np.load(OUT/'poses'/f'v4-movie-{variant}-{k:03d}.npz');posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
  for o,ix in zip(meshes,maps):o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update();o.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(o.data.vertices))
  for angle,view in [(0,'front'),(90,'side')]:
   tar=Vector((-.18,0,.84));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.15));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=1.85;file=frames/f'{variant}-{k:03d}-{view}.png'
   if not file.exists():sc.render.filepath=str(file);bpy.ops.render.render(write_still=True)
print('MOVIE CPU COMPLETE')
