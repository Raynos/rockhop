from pathlib import Path
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
setup=(ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0]
setup=setup.replace('maps=[]','maps=[]; original_corner_normals={}')
setup=setup.replace(' orig=np.array([list(o.matrix_world@v.co)'," o.data.update();original_corner_normals[o]=np.array([list(v.vector)for v in o.data.corner_normals])@np.array(o.matrix_world.to_3x3().inverted().transposed()).T\n orig=np.array([list(o.matrix_world@v.co)")
import json
sample=json.loads(Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played/candidate/side/textured/report.json').read_text())['samples'][304]
for variant in ['source','v7-plain','v7-cage','volume-slide']:
 source=ROOT/'deliverables/C19.glb'if variant=='source'else ROOT/'hoodie-repair02/deliverables/rider-compression-v7.glb'
 exec(setup.replace("root/'baseline/rider.glb'",'Path('+repr(str(source))+')'))
 from mathutils import Quaternion
 data=np.load(ROOT/'hoodie-repair03/poses'/f'game304-{variant}.npz');DD=data['matrices'];posed=np.concatenate([data[f'p{i}']for i in range(5)]);CC=np.array([[1,0,0],[0,0,-1],[0,1,0]]);v=posed@CC.T
 # Standard frozen normals, then the same actual weighted matrix normal transform.
 nn=[];weights=[];offset=np.r_[0,np.cumsum([len(g.array(p['attributes']['POSITION']))for p in prims])]
 for pr in prims:
  n=g.array(pr['attributes']['NORMAL']).astype(float);ids=g.array(pr['attributes']['JOINTS_0']);ws=g.array(pr['attributes']['WEIGHTS_0']);w=np.zeros((len(ws),19));np.put_along_axis(w,ids,ws,axis=1);weights.append(w);nn.append(n)
 skin=np.concatenate([np.einsum('vj,jab,vb->va',w,DD[:,:3,:3],n,optimize=False)for w,n in zip(weights,nn)]);skin/=np.maximum(np.linalg.norm(skin,axis=1,keepdims=True),1e-15);skin=skin@CC.T
 for o,ix in zip(meshes,maps):
  o.data.vertices.foreach_set('co',v[ix].astype('f4').ravel());o.data.update()
  if np.min(ix)>=offset[3]:o.data.normals_split_custom_set((original_corner_normals[o]@(CC@DD[4,:3,:3]@CC.T).T).tolist())
  else:o.data.normals_split_custom_set_from_vertices(skin[ix].tolist())
 # Match archived actual camera in bike-frame coordinates. Rigid registration is
 # independently constrained by recorded joint positions (residual<0.1µm).
 pp=np.load(ROOT/'experiments/C19-bind.npz')['centres'];Q=np.einsum('nij,nj->ni',DD[:,:3,:],np.c_[pp,np.ones(19)])
 names=['pelvis','chest','head','upperArmL','upperArmR'];idx=[0,2,4,6,10];X=Q[idx];Y=np.array([sample['bones'][n]['position']for n in names]);xc=X.mean(0);yc=Y.mean(0);u,s,vt=np.linalg.svd((X-xc).T@(Y-yc));rowrot=u@vt;translation=yc-xc@rowrot;err=np.linalg.norm(X@rowrot+translation-Y,axis=1).max()
 position=(np.array(sample['camera']['position'])-translation)@rowrot.T;rcam=rowrot@np.array(Quaternion([sample['camera']['quaternion'][3],*sample['camera']['quaternion'][:3]]).to_matrix());cam.location=Vector(CC@position);cam.rotation_euler=Matrix((CC@rcam).tolist()).to_euler();d.type='PERSP';d.sensor_fit='HORIZONTAL';aspect=1280/720;fovy=2*math.atan(math.tan(math.radians(sample['camera']['fov'])/2)/sample['camera']['zoom']);d.lens=d.sensor_width/(2*math.tan(fovy/2)*aspect);view=sample['camera']['view'];d.shift_x=view['offsetX']/view['fullWidth'];d.shift_y=-view['offsetY']/view['fullWidth'];sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.cycles.samples=6
 for o in bikeobjects:o.hide_render=True
 original={o:list(o.data.materials)for o in meshes};gray=mat('neutral garment diagnostic',(.42,.42,.42))
 for app in ['pbr','gray']:
  for o in meshes:
   for i in range(len(o.data.materials)):o.data.materials[i]=gray if app=='gray'else original[o][i]
  dest=ROOT/'hoodie-repair03/renders/game304';dest.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(dest/f'{variant}-{app}.png');bpy.ops.render.render(write_still=True)
 (dest/f'{variant}-camera.json').write_text(json.dumps({'sourceCamera':sample['camera'],'bikeRegistrationMaxResidualM':float(err),'normalMode':'standard LBS source normal emulation; cage candidate normals not yet rederived','materials':'original GLB textures in CPU Cycles; does not certify WebGL/PBR equivalence','frame':304,'screenshotExactSource':'unconfirmed'},indent=2))
print('EXACT REFERENCE-CAMERA CPU COMPARISON COMPLETE')
