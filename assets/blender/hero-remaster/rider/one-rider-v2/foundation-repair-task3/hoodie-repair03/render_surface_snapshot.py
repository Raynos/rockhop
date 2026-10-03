"""Render a literal static snapshot without re-skinning or vertex mapping."""
from pathlib import Path
import bpy,sys,json,math,hashlib,numpy as np
from mathutils import Vector,Matrix,Quaternion
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
a=sys.argv[sys.argv.index('--')+1:];snapshot=Path(a[0]);state=a[1];label=a[2];assert state in ['rest','304'];assert label.replace('-','').replace('_','').isalnum()
setup=(ROOT/'scripts/render_stills.py').read_text().split('cases=sys.argv')[0];setup=setup.replace('root=Path.cwd()','root=ROOT').replace("root/'baseline/rider.glb'",'Path('+repr(str(snapshot))+')');setup=setup.replace(";rig=next(o for o in sc.objects if o.type=='ARMATURE')",'');start=setup.index('lookup={}');end=setup.index('rig.hide_render=True')+len('rig.hide_render=True');setup=setup[:start]+setup[end:];exec(compile(setup,'snapshot-studio','exec'))
for ob in bikeobjects:ob.hide_render=True
saved={ob:list(ob.data.materials)for ob in meshes};gray=mat('Exact surface gray',(.42,.42,.42));sc.cycles.samples=6;dest=ROOT/'hoodie-repair03/renders/sleeve-tube03'/label;dest.mkdir(parents=True,exist_ok=True)
if state=='rest':
 views=[('front',0)]if '--front-only'in a else[('front',0),('side',90),('back',180)];sc.render.resolution_x=sc.render.resolution_y=640;d.ortho_scale=1.95;d.shift_x=d.shift_y=0
else:
 record=json.loads((ROOT/'hoodie-repair03/inputs/recorded-side304.json').read_text());sample=record['sample'];D=np.load(ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz')['D'][304];centres=np.load(ROOT/'experiments/C19-bind.npz')['centres'];Q=np.einsum('nij,nj->ni',D[:,:3,:],np.c_[centres,np.ones(19)]);X=Q[[0,2,4,6,10]];Y=np.array([sample['bones'][n]['position']for n in['pelvis','chest','head','upperArmL','upperArmR']]);xc,yc=X.mean(0),Y.mean(0);u,_,vt=np.linalg.svd((X-xc).T@(Y-yc));rot=u@vt;translation=yc-xc@rot;error=float(np.linalg.norm(X@rot+translation-Y,axis=1).max());assert error<1e-6
 CC=np.array([[1,0,0],[0,0,-1],[0,1,0]]);position=(np.array(sample['camera']['position'])-translation)@rot.T;q=sample['camera']['quaternion'];rotation=rot@np.array(Quaternion([q[3],*q[:3]]).to_matrix());cam.location=Vector(CC@position);cam.rotation_euler=Matrix((CC@rotation).tolist()).to_euler();d.type='PERSP';d.sensor_fit='HORIZONTAL';fovy=2*math.atan(math.tan(math.radians(sample['camera']['fov'])/2)/sample['camera']['zoom']);d.lens=d.sensor_width/(2*math.tan(fovy/2)*(1280/720));view=sample['camera']['view'];d.shift_x=view['offsetX']/view['fullWidth'];d.shift_y=-view['offsetY']/view['fullWidth'];sc.render.resolution_x,sc.render.resolution_y=1280,720;views=[('exact-side',None)]
for name,angle in views:
 if angle is not None:
  target=Vector((.63,0,.91));cam.location=target+Vector((4*math.cos(math.radians(angle)),4*math.sin(math.radians(angle)),.15));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 for appearance in ['pbr','gray']:
  for ob in meshes:
   for i in range(len(ob.data.materials)):ob.data.materials[i]=gray if appearance=='gray'else saved[ob][i]
  sc.render.filepath=str(dest/f'{state}-{name}-{appearance}.png');bpy.ops.render.render(write_still=True)
(dest/f'{state}-render-provenance.json').write_text(json.dumps({'snapshotSHA256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'snapshot':str(snapshot),'state':state,'render':'CPU Cycles2threads6samples','positionProof':'Literal unskinned snapshot import; no vertex mapping or skinning in Blender','status':'Unaccepted diagnostic surface, not runtime skin/driver proof'},indent=2)+'\n')
print('EXACT SNAPSHOT IMAGES COMPLETE')
