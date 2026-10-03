exec(open('scripts/render_stills.py').read().split('cases=sys.argv')[0])
sc.cycles.samples=4;sc.render.resolution_x=480;sc.render.resolution_y=480
for name in ['A','C19']:
 for sample in range(25):
  dat=np.load(root/'experiments'/f'{name}-rigid_length_stand_to_sit-{sample:03d}.npz');posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
  for o,ix in zip(meshes,maps):
   o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update();o.data.normals_split_custom_set_from_vertices([(0.,0.,0.)]*len(o.data.vertices))
  for angle,an,close in [(0,'front',False),(90,'side',False),(180,'back',False),(120,'hip',True)]:
   tar=Vector((-.18,0,.82))if not close else Vector((-.30,0,.69));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.20 if not close else .35));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=1.85 if not close else .70
   sc.render.filepath=str(out/'movie-frames'/an/name/f'{sample:03d}.png');bpy.ops.render.render(write_still=True)
print('MOVIE FRAMES COMPLETE')
