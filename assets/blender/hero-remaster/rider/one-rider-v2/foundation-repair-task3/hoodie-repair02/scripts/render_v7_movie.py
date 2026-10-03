from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
setup=(ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0]
setup=setup.replace('maps=[]','maps=[]; original_corner_normals={}')
setup=setup.replace(' orig=np.array([list(o.matrix_world@v.co)'," o.data.update();original_corner_normals[o]=np.array([list(v.vector)for v in o.data.corner_normals])@np.array(o.matrix_world.to_3x3().inverted().transposed()).T\n orig=np.array([list(o.matrix_world@v.co)")
def accessor(g,ai):
 ac=g.j['accessors'][ai];a=g.array(ai).astype(float)if'bufferView'in ac else np.zeros((ac['count'],3))
 if'sparse'in ac:
  ss=ac['sparse'];bb=g.j['bufferViews'][ss['indices']['bufferView']];ix=np.frombuffer(g.bin,dtype={5125:'<u4',5123:'<u2',5121:'u1'}[ss['indices']['componentType']],count=ss['count'],offset=bb.get('byteOffset',0)+ss['indices'].get('byteOffset',0));bb=g.j['bufferViews'][ss['values']['bufferView']];a[ix]=np.frombuffer(g.bin,dtype='<f4',count=ss['count']*3,offset=bb.get('byteOffset',0)+ss['values'].get('byteOffset',0)).reshape(-1,3)
 return a
OUT=ROOT/'hoodie-repair02';frames=OUT/'renders/movie-v7';frames.mkdir(exist_ok=True)
for variant in ['candidate']:
 source=ROOT/'deliverables/C19.glb'if variant=='control'else OUT/'deliverables/rider-compression-v7.glb'
 exec(setup.replace("root/'baseline/rider.glb'",'Path('+repr(str(source))+')'))
 base_norm=[accessor(g,p['attributes']['NORMAL'])for p in prims];closed_norm=[n.copy()for n in base_norm];weights=[]
 for i,p in enumerate(prims):
  ids=g.array(p['attributes']['JOINTS_0']);ws=g.array(p['attributes']['WEIGHTS_0']);ww=np.zeros((len(ws),19));np.put_along_axis(ww,ids,ws,axis=1);weights.append(ww)
  for ta in p.get('targets',[])[:2]:
   if'NORMAL'in ta:closed_norm[i]+=accessor(g,ta['NORMAL'])
 sc.render.resolution_x=sc.render.resolution_y=384;sc.cycles.samples=3
 for k in range(49):
  file=OUT/'poses'/f'v5-movie-control-{k:03d}.npz'if variant=='control'else OUT/'poses'/f'v6-movie-candidate-{k:03d}.npz';dat=np.load(file);posed=np.concatenate([dat[f'p{i}']for i in range(5)]);v=posed[:,[0,2,1]];v[:,1]*=-1
  DD=dat['matrices'];nn=[n.copy()for n in closed_norm]
  if variant=='candidate':
   for i in range(3):nn[i]+=accessor(g,prims[i]['targets'][k+2]['NORMAL'])
  nw=np.concatenate([np.einsum('vj,jab,vb->va',ws,DD[:,:3,:3],n,optimize=False)for ws,n in zip(weights,nn)]);nw/=np.maximum(np.linalg.norm(nw,axis=1,keepdims=True),1e-15);nw=nw[:,[0,2,1]];nw[:,1]*=-1
  for o,ix in zip(meshes,maps):
   o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update()
   if np.min(ix)>=sum(len(g.array(p['attributes']['POSITION']))for p in prims[:3]):
    CC=np.array([[1,0,0],[0,0,-1],[0,1,0]]);rot=CC@DD[4,:3,:3]@CC.T;o.data.normals_split_custom_set((original_corner_normals[o]@rot.T).tolist())
   else:o.data.normals_split_custom_set_from_vertices(nw[ix].tolist())
  for angle,view in [(0,'front'),(90,'side'),(180,'rear')]:
   tar=Vector((-.18,0,.84));cam.location=tar+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.15));cam.rotation_euler=(tar-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=1.85;file=frames/f'{variant}-{k:03d}-{view}.png'
   if not file.exists():sc.render.filepath=str(file);bpy.ops.render.render(write_still=True)
print('V7 MATCHED CPU MOVIE COMPLETE')
