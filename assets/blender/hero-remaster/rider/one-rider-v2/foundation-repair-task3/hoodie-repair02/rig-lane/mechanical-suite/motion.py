"""Motion-only V7 mechanical ablation, world-space skin matrices.

Three variants: legacy fixed-glenoid stress; identical endpoint/orientation IK
with fixed girdle; endpoint-matched existing-girdle participation. No weights,
rest centres, topology or limb lengths change. The single clavicle-like proxy
does not represent a separate scapula or measured glenoid orientation.
"""
from pathlib import Path
import sys,json,numpy as np
from scipy.spatial.transform import Rotation as R,Slerp
HERE=Path(__file__).resolve().parent
P=np.asarray(json.loads((HERE/'frozen-provenance.json').read_text())['centres'],dtype=float)
N=len(P)
NAMES=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
IND={name:i for i,name in enumerate(NAMES)}
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def align(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b)
 if c < -1+1e-10:
  trial=np.eye(3)[np.argmin(abs(a))];axis=np.cross(a,trial);axis/=np.linalg.norm(axis)
  return R.from_rotvec(axis*np.pi).as_matrix()
 K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
 return np.eye(3)+K+np.einsum('ij,jk->ik',K,K,optimize=False)/max(1+c,1e-12)
def ik(a,b,l1,l2,pole):
 d=b-a;r=np.linalg.norm(d);u=d/r;s=(l1*l1-l2*l2+r*r)/(2*r);h=np.sqrt(max(0,l1*l1-s*s))
 v=np.asarray(pole)-u*np.dot(pole,u);v/=np.linalg.norm(v);return a+u*s+v*h

def unit(x):return x/max(np.linalg.norm(x),1e-15)
def frame(axis,normal):
 u=unit(axis);v=unit(normal-u*np.dot(u,normal));return np.stack([u,v,np.cross(u,v)],axis=1)
def mul(a,b):return np.einsum('ij,jk->ik',a,b,optimize=False)
def apply(r,x):return np.einsum('ij,j->i',r,x,optimize=False)
def rotate_subtree(D,ids,pivot,rot):
 for j in ids:
  D[j,:3,:3]=mul(rot,D[j,:3,:3]);D[j,:3,3]=apply(rot,D[j,:3,3]-pivot)+pivot
 return D
def centres(D):return np.einsum('nij,nj->ni',D[:,:3,:],np.c_[P,np.ones(N)],optimize=False)

def legacy(kind,t):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 if kind=='neutral':return D
 primary=['horizontal','overhead','functional_overhead','forward']
 armkind=kind if kind in primary else'forward'
 amount=t if kind in primary else .7
 for sg,a in [(1,6),(-1,10)]:
  theta=np.deg2rad(140);plane=np.deg2rad(45)
  direction={'horizontal':np.array([0,0,sg]),'overhead':np.array([0,1,sg*.1]),'functional_overhead':np.array([np.sin(theta)*np.sin(plane),-np.cos(theta),sg*np.sin(theta)*np.cos(plane)]),'forward':np.array([1,0,sg*.1])}[armkind]
  full=align(P[a+1]-P[a],direction);rot=Slerp([0,1],R.from_matrix([np.eye(3),full]))([amount]).as_matrix()[0]
  rotate_subtree(D,[a,a+1,a+2],P[a],rot)
 if kind in ['elbow','legacy_elbow']:
  Q=centres(D)
  for a in [6,10]:
   # The true bend hinge is transverse to the current upperarm; both sides
   # flex toward world up, not opposite signs of an arbitrary worldZ axis.
   u=unit(Q[a+1]-Q[a]);bend=unit(np.array([0.,1,0])-u*u[1]);axis=unit(np.cross(u,bend))
   if kind=='legacy_elbow':axis=unit(np.cross(Q[a+2]-Q[a+1],np.array([0.,1,0])))
   angle=90 if kind=='legacy_elbow'else 100
   rotate_subtree(D,[a+1,a+2],Q[a+1],R.from_rotvec(axis*np.deg2rad(angle)*t).as_matrix())
 if kind in ['forearm_twist','legacy_distal_axial','wrist_flex','wrist_deviation']:
  Q=centres(D)
  for a in [6,10]:
   u=unit(Q[a+2]-Q[a+1]);bend=unit(np.array([0.,1,0])-u*u[1]);hinge=unit(np.cross(u,bend))
   axis=u if kind in ['forearm_twist','legacy_distal_axial']else hinge if kind=='wrist_flex'else bend
   angle={'forearm_twist':75,'legacy_distal_axial':90,'wrist_flex':45,'wrist_deviation':20}[kind]*t
   ids=[a+1,a+2]if kind=='forearm_twist'else[a+2];j=a+1 if kind=='forearm_twist'else a+2
   rotate_subtree(D,ids,Q[j],R.from_rotvec(axis*np.deg2rad(angle)).as_matrix())
 return D

def arm_pose(kind,t,variant='girdle',target_mode='legacy'):
 """Return19 deformation matrices+audit. kind names are in legacy().

 target_mode=legacy retains exact old hand positions/orientations. `inset`
 moves BOTH controls' targets20mm toward their fixed shoulder to leave modest
 reach reserve. The legacy comparator cannot share that new target definition.
 """
 src=legacy(kind,t);old=centres(src)
 if variant=='legacy'or kind=='neutral':return src,{'variant':variant,'kind':kind,'fraction':t,'targetMode':target_mode,'sides':[]}
 D=np.repeat(np.eye(4)[None],N,axis=0);rec=[]
 for side,sg in [('L',1),('R',-1)]:
  s,a,b,c=[IND[x+'.'+side]for x in ['shoulder','upperArm','forearm','hand']]
  target=old[c].copy()
  if target_mode=='inset':target+=unit(P[a]-target)*.020*smooth(t if kind in ['horizontal','overhead','functional_overhead','forward']else .7)
  targetrot=src[c,:3,:3].copy()
  ulegacy=unit(old[b]-old[a]);elev=float(np.degrees(np.arccos(np.clip(-ulegacy[1],-1,1))))
  # Small clavicle elevation/retraction proxy. These8/6deg amplitudes are
  # authored assumptions, not a subject-specific clinical model. Full scapular
  # upward rotation cannot be encoded by this single clavicle-like link.
  g=smooth((elev-25)/140)
  beta=np.deg2rad(8)*g if variant=='girdle'else 0
  phi=np.deg2rad(6)*g if variant=='girdle'else 0
  if kind not in ['horizontal','overhead','functional_overhead']:phi=-phi*.7 # outreach protraction authored, no universal anatomy claim
  l1=np.linalg.norm(P[b]-P[a]);l2=np.linalg.norm(P[c]-P[b])
  def root_at(factor):
   rx=R.from_rotvec(np.array([-sg*beta*factor,0,0])).as_matrix();ry=R.from_rotvec(np.array([0,-sg*phi*factor,0])).as_matrix()
   rg=mul(ry,rx);return rg,P[s]+apply(rg,P[a]-P[s])
  girdleFactor=1.;rg,root=root_at(girdleFactor)
  def feasible(q):return abs(l1-l2)+1e-9 <= np.linalg.norm(target-q) <= l1+l2-1e-9
  # Reduce only the authored girdle contribution when it makes the common
  # target unreachable. End targets never move and links never stretch.
  if not feasible(root) and feasible(root_at(0)[1]):
   lo,hi=0.,1.
   for _ in range(48):
    mid=(lo+hi)*.5
    if feasible(root_at(mid)[1]):lo=mid
    else:hi=mid
   girdleFactor=lo;rg,root=root_at(girdleFactor)
  beta*=girdleFactor;phi*=girdleFactor;distance=np.linalg.norm(target-root)
  # Never stretch; if a legacy target is infeasible, preserve lengths and
  # report its error. Impossible external targets remain visibly unqualified.
  reach=np.clip(distance,abs(l1-l2)+1e-10,l1+l2-1e-10);hit=root+unit(target-root)*reach
  ray=unit(hit-root);pole=old[b]-P[a]-ray*np.dot(old[b]-P[a],ray)
  if np.linalg.norm(pole)<1e-7:pole=np.array([-1.,0,0])-ray*(-ray[0])
  # Existing girdle participation only; keep common worldpole so elbow-plane
  # differences come from changed root, not an added hand orientation change.
  mid=ik(root,hit,l1,l2,pole)
  normal=unit(np.cross(mid-root,hit-mid));restnormal=unit(np.cross(P[b]-P[a],P[c]-P[b]))
  rua=mul(frame(mid-root,normal),frame(P[b]-P[a],restnormal).T)
  rfa=mul(frame(hit-mid,normal),frame(P[c]-P[b],restnormal).T)
  oldnormal=unit(np.cross(old[b]-old[a],old[c]-old[b]))
  oldforeframe=mul(frame(old[c]-old[b],oldnormal),frame(P[c]-P[b],restnormal).T)
  # Preserve the specified axial forearm rotation; endpoint positions alone do
  # not carry pronation/supination. This must not silently disappear in IK.
  forearmResidual=mul(oldforeframe.T,src[b,:3,:3])
  rfa=mul(rfa,forearmResidual)
  for j,q,rot in [(s,P[s],rg),(a,root,rua),(b,mid,rfa),(c,hit,targetrot)]:
   D[j,:3,:3]=rot;D[j,:3,3]=q-apply(rot,P[j])
  flex=np.degrees(np.arccos(np.clip(np.dot(unit(mid-root),unit(hit-mid)),-1,1)))
  rec.append({'side':side,'target':target.tolist(),'achievedHand':hit.tolist(),'handTargetErrorM':float(np.linalg.norm(hit-target)),'handRotationErrorRad':float(R.from_matrix(mul(targetrot.T,D[c,:3,:3])).magnitude()),'girdleContributionFactor':girdleFactor,'girdleElevationDegrees':float(np.degrees(beta)),'girdleRetractionDegrees':float(np.degrees(phi)),'upperarmTargetDirection':unit(old[b]-old[a]).tolist(),'actualUpperarmDirection':unit(mid-root).tolist(),'upperarmDirectionDeviationDegrees':float(np.degrees(np.arccos(np.clip(np.dot(unit(mid-root),ulegacy),-1,1)))),'glenoidShiftM':float(np.linalg.norm(root-P[a])),'elbowFlexionDegrees':float(flex),'girdleLinkLengthErrorM':float(abs(np.linalg.norm(root-P[s])-np.linalg.norm(P[a]-P[s]))),'upperarmLengthErrorM':float(abs(np.linalg.norm(mid-root)-l1)),'forearmLengthErrorM':float(abs(np.linalg.norm(hit-mid)-l2)),'elbowPoleWorld':unit(pole).tolist(),'elbowHingeWorld':normal.tolist(),'forearmAxisWorld':unit(hit-mid).tolist()})
 return D,{'variant':variant,'kind':kind,'fraction':t,'targetMode':target_mode,'sides':rec}

def neutral_elbow(degrees,side='both'):
 """Clean isolation: armrest held; forearm/hand rotate forward at real elbow.

 These are mechanical fixtures, not scanned anatomical axes or game poses.
 """
 D=np.repeat(np.eye(4)[None],N,axis=0)
 if side not in ['both','L','R']:raise ValueError('side must be both, L or R')
 for label,a in [('L',6),('R',10)]:
  if side not in ['both',label]:continue
  u=unit(P[a+1]-P[a]);front=unit(np.array([1.,0,0])-u*u[0]);axis=unit(np.cross(u,front))
  rotate_subtree(D,[a+1,a+2],P[a+1],R.from_rotvec(axis*np.deg2rad(degrees)).as_matrix())
 return D

if __name__=='__main__':
 print(json.dumps(arm_pose('overhead',1)[1],indent=2))
