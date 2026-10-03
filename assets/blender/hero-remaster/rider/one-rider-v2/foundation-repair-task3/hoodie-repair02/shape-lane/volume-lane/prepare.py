from sleeve_curve import *
from scipy.spatial.transform import Rotation as R
sleeve=SleeveCurve();rows=[]
def elbow(degrees):
 D=np.repeat(np.eye(4)[None],N,axis=0);a=6;direction=unit(P[a+2]-P[a+1]);axis=unit(np.cross(direction,np.array([1.,0.,0.])));rot=R.from_rotvec(axis*np.radians(degrees)).as_matrix()
 for j in [a+1,a+2]:D[j,:3,:3]=rot;D[j,:3,3]=P[a+1]-rot@P[a+1]
 return D
qa=ROOT/'hoodie-repair02/qa-lane/poses'
probes=[('neutral',0,np.repeat(np.eye(4)[None],N,axis=0))]+[('single-elbow',t,elbow(t))for t in [30,60,90,120]]
for kind in ['forward','elbow','overhead']:
 for fraction in [.5,1]:probes.append((kind,fraction,np.load(qa/f'v5-{kind}-{fraction:g}.npz')['matrices']))
for kind,fraction,D in probes:
 skin=deform(sleeve.pos,sleeve.w,D);np.savez(OUT/f'skin-{kind}-{fraction}.npz',**{f'p{i}':p for i,p in enumerate(skin)},matrices=D)
 for mode,clear in [('curve',False),('capsule',True)]:
  p,m=sleeve.target(D,clearance=clear);name=f'{mode}-{kind}-{fraction}.npz';np.savez(OUT/name,**{f'p{i}':q for i,q in enumerate(p)},matrices=D);m.update(mode=mode,pose=kind,fraction=fraction);rows.append(m);print({k:v for k,v in m.items()if k not in ['sides','method','limits']},flush=True)
(OUT/'provenance.json').write_text(json.dumps({'sourceV7BindSHA256':hashlib.sha256(sleeve.input.read_bytes()).hexdigest(),'sourceV7ShapeSHA256':hashlib.sha256((ROOT/'hoodie-repair02/v7-shape-input.npz').read_bytes()).hexdigest(),'rows':rows,'scope':'Bounded 11poses, curve vsproxycapsule ablation. Singleleftarm30/60/90/120forwardbend, oppositearmrest. MatchedsameDposes. No renders/GPU/runtimeclaims.'},indent=2))
