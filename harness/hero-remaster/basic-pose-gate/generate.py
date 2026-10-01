"""Continuous exported19bone stress fixtures; reuse independently inspected arms."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
import numpy as np
from scipy.spatial.transform import Rotation as R
REPO=Path(__file__).resolve().parents[3]
OWNER=REPO/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3'
MOTION=OWNER/'hoodie-repair02/rig-lane/mechanical-suite/motion.py'
BASE=OWNER/'hoodie-repair02/scripts/base.py'
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--fps',type=int,default=24);parser.add_argument('--asymmetric',action='store_true');args=parser.parse_args()
assert args.fps in [24,48], 'Only baseline24fps and analytic48fps halfstep fixtures are defined'
assert not args.out.exists(), 'Freeze fixtures; never overwrite a reviewed sequence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[MOTION,MOTION.parent/'frozen-provenance.json',BASE,OWNER/'experiments/C19-bind.npz',OWNER/'deliverables/C19.glb']
provenance={str(p):sha(p) for p in inputs}
sys.path.insert(0,str(MOTION.parent));import motion
P,IND=motion.P,motion.IND
assert len(P)==19
names=list(IND);FPS=args.fps;DURATION=4
primary={'horizontal','overhead','forward'}
secondary={'elbow','forearm_twist','wrist_flex','wrist_deviation','grip'}
def smooth(t):return t*t*(3-2*t)
def pulse(t):return smooth(np.sin(np.pi*np.clip(t,0,1)))
def lower(kind,a):
 """Authored planted-foot fixture, not physical COM or saddle-contact control."""
 pelvis=P[0].copy();rot=R.from_euler('z',-.20*a if kind=='squat' else -.08*a).as_matrix()
 if kind=='lean':
  pelvis[2]+=.06*a;rot=R.from_euler('x',.35*a).as_matrix()
 else:
  pelvis[:2]+=np.array([-.06,-.25] if kind=='squat' else [-.15,-.28])*a
 Q=pelvis+(P-P[0])@rot.T;rotations=np.repeat(rot[None],19,axis=0);errors=[]
 for side,sg in [('L',1),('R',-1)]:
  h,k,f=[IND[x+'.'+side] for x in ['thigh','shin','foot']]
  root,target=Q[h],P[f];l1=np.linalg.norm(P[k]-P[h]);l2=np.linalg.norm(P[f]-P[k])
  ray=target-root;distance=np.linalg.norm(ray);unit=ray/distance
  reach=np.clip(distance,abs(l1-l2)+1e-6,l1+l2-1e-6);hit=root+unit*reach
  # Preserve the source knee plane at neutral instead of introducing a pole
  # jump when the neutral endpoint gives way to the first bending frame.
  restaxis=(P[f]-P[h])/np.linalg.norm(P[f]-P[h])
  pole=P[k]-P[h]-restaxis*np.dot(P[k]-P[h],restaxis)
  assert np.linalg.norm(pole)>1e-6, 'Source knee plane is degenerate'
  mid=motion.ik(root,hit,l1,l2,pole/np.linalg.norm(pole))
  Q[k],Q[f]=mid,hit;rotations[h]=motion.align(P[k]-P[h],mid-root);rotations[k]=motion.align(P[f]-P[k],hit-mid);rotations[f]=np.eye(3)
  errors.append({'side':side,'footTargetErrorM':float(np.linalg.norm(hit-target)),'upperLengthErrorM':float(abs(np.linalg.norm(mid-root)-l1)),'lowerLengthErrorM':float(abs(np.linalg.norm(hit-mid)-l2))})
 D=np.repeat(np.eye(4)[None],19,axis=0);D[:,:3,:3]=rotations;D[:,:3,3]=Q-np.einsum('nij,nj->ni',rotations,P)
 return D,errors
families=['neutral','horizontal','overhead','forward','elbow','forearm_twist','wrist_flex','wrist_deviation','grip','squat','sit','lean']
if args.asymmetric:
 families += [kind+'.'+side for kind in families if kind in primary|secondary for side in ['L','R']]
rows=[]
for family in families:
 kind,side=family.rsplit('.',1) if '.'in family else (family,None)
 for k in range(FPS*DURATION+1):
  t=k/(FPS*DURATION);grip=0.;diagnostic={}
  if kind=='neutral':D=np.repeat(np.eye(4)[None],19,axis=0)
  elif kind in primary:D,diagnostic=motion.arm_pose(kind,pulse(t),'girdle','legacy')
  elif kind in secondary:
   if t<.25:D,diagnostic=motion.arm_pose('forward',.7*smooth(t/.25),'girdle','legacy')
   elif t>.75:D,diagnostic=motion.arm_pose('forward',.7*(1-smooth((t-.75)/.25)),'girdle','legacy')
   else:
    a=pulse((t-.25)/.5)
    D,diagnostic=motion.arm_pose('forward' if kind=='grip' else kind,.7 if kind=='grip' else a,'girdle','legacy')
    grip=a if kind=='grip' else 0.
  else:D,diagnostic=lower(kind,pulse(t) if kind!='lean' else np.sin(2*np.pi*t)**3)
  if side:
   active=[IND[name+'.'+side] for name in ['shoulder','upperArm','forearm','hand']]
   for j in range(19):
    if j not in active:D[j]=np.eye(4)
   diagnostic={**diagnostic,'activeSide':side,'sides':[r for r in diagnostic.get('sides',[]) if r['side']==side]}
  if k in [0,FPS*DURATION]:
   # Exact neutral at the sequence endpoints; no accumulated drift.
   D=np.repeat(np.eye(4)[None],19,axis=0);grip=0.
  assert np.isfinite(D).all() and np.allclose(np.linalg.det(D[:,:3,:3]),1,atol=1e-8)
  rows.append({'family':family,'frame':k,'timeSeconds':k/FPS,'closedGrip':grip,'gripSide':side,'deformationWorldColumnMajor':D.transpose(0,2,1).reshape(19,16).tolist(),'controlDiagnostic':diagnostic})
assert all(sha(p)==v for p,v in [(Path(p),v) for p,v in provenance.items()]),'Owner inputs changed during snapshot; do not freeze mixed controls'
args.out.parent.mkdir(parents=True,exist_ok=True)
manifest={'schemaVersion':1,'kind':'Continuous authored basic-pose stress fixture; not gameplay or accepted anatomy',
 'fps':FPS,'secondsPerFamily':DURATION,'jointNames':names,'referenceCentresWorld':P.tolist(),'families':families,'frames':rows,
 'sourceProvenance':provenance,'fixtureSourceSHA256':sha(Path(__file__)),
 'limits':['Arm controls reuse independent endpoint-matched girdle proxy, not measured scapular mechanics.','Some fixed legacy hand targets are unreachable; residuals stay visible in controlDiagnostic.','Squat/sit/lean are new authored planted-foot stress controls, not animation quality or COM/support proof.','Closed grip uses original two source morph targets; no49clip-specific compression.','No collision, moving gray/PBR, surface contacts, gameplay or appearance gate is accepted by this manifest.']}
args.out.write_text(json.dumps(manifest,separators=(',',':'))+'\n')
print(json.dumps({'families':len(families),'frames':len(rows),'sha256':sha(args.out)}))
