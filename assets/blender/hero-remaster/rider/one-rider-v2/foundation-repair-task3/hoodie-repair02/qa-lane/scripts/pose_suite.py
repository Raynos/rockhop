"""Small fixed CPU qualification suite. Source matrices, not copied local quaternions."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from scipy.spatial.transform import Rotation as R,Slerp
ROOT=Path(__file__).resolve().parents[3]; Q=ROOT/'hoodie-repair02/qa-lane';sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'))
from base import *
assert hashlib.sha256((Q/'C19-source.glb').read_bytes()).hexdigest()=='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'

def joint_rotate(D,ids,pivot,rotation):
 T=np.eye(4);T[:3,:3]=rotation;T[:3,3]=pivot-rotation@pivot
 for j in ids:D[j]=T@D[j]
 return D

def arms(kind,t=1):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 for sg,a in [(1,6),(-1,10)]:
  target={'horizontal':np.array([0,0,sg]),'overhead':np.array([0,1,sg*.10]),'forward':np.array([1,0,sg*.10])}[kind]
  rot=align(P[a+1]-P[a],target);rot=Slerp([0,1],R.from_matrix([np.eye(3),rot]))([t]).as_matrix()[0]
  joint_rotate(D,[a,a+1,a+2],P[a],rot)
 return D

def elbow(t):
 D=arms('forward',.7)
 for a in [6,10]:
  pivot=D[a+1,:3,:3]@P[a+1]+D[a+1,:3,3]
  direction=D[a+1,:3,:3]@(P[a+2]-P[a+1]);direction/=np.linalg.norm(direction)
  axis=np.cross(direction,np.array([0.,1.,0.]));axis/=np.linalg.norm(axis)
  joint_rotate(D,[a+1,a+2],pivot,R.from_rotvec(axis*t*np.pi*.5).as_matrix())
 return D

def twist(t,wrist=False):
 D=arms('forward',.7)
 for a in [6,10]:
  axis=D[a+1,:3,:3]@(P[a+2]-P[a+1]);axis/=np.linalg.norm(axis)
  j=a+2 if wrist else a+1;pivot=D[j,:3,:3]@P[j]+D[j,:3,3]
  joint_rotate(D,[a+2]if wrist else[a+1,a+2],pivot,R.from_rotvec(axis*t*np.pi*.5).as_matrix())
 return D

def squat(t):
 D=np.repeat(np.eye(4)[None],N,axis=0);hip=P[0]+np.array([-.07*t,-.28*t,0]);tor=R.from_euler('z',-.20*t).as_matrix()
 for j in range(13):D[j,:3,:3]=tor;D[j,:3,3]=hip-tor@P[0]
 for h,k,f,sg in [(13,14,15,1),(16,17,18,-1)]:
  Qh=hip+tor@(P[h]-P[0]);Qf=P[f];Qk=ik(Qh,Qf,np.linalg.norm(P[k]-P[h]),np.linalg.norm(P[f]-P[k]),[1,0,sg*.2])
  for j,q,rot in [(h,Qh,align(P[k]-P[h],Qk-Qh)),(k,Qk,align(P[f]-P[k],Qf-Qk)),(f,Qf,np.eye(3))]:D[j,:3,:3]=rot;D[j,:3,3]=q-rot@P[j]
 return D

def main():
 probes=[('neutral',0,np.repeat(np.eye(4)[None],N,axis=0),False)]
 for kind in ['horizontal','overhead','forward']:
  for t in [.25,.5,.75,1]:probes.append((kind,t,arms(kind,t),False))
 for kind,fn in [('elbow',elbow),('twist',twist),('wrist',lambda t:twist(t,True)),('squat',squat)]:
  for t in [.5,1]:probes.append((kind,t,fn(t),False))
 for t in [0,.125,.25,.375,.5,.625,.75,.875,1]:probes.append(('sit',t,sit_pose(t,True),True))
 for t in [.5,1]:probes.append(('lean',t,sit_pose(1,True,.25*t),True))
 # Control keeps C19 authored unnatural neck orientation; same support paths.
 variants={'source':(POS,W),'source-natural':(POS,W)}
 if (OUT/'round1-bind.npz').exists():
  b=np.load(OUT/'round1-bind.npz');new=[b[f'p{i}']for i in range(5)];ww=[b[f'W{i}']for i in range(5)];variants.update({'r1-shape':(new,W),'r1-shape-weights':(new,ww)})
 if len(sys.argv)>1:
  label=sys.argv[2]if len(sys.argv)>2 else'candidate'
  if sys.argv[1]=='SOURCE':variants={label:(POS,W)}
  else:
   b=np.load(sys.argv[1]);variants={label:([b[f'p{i}']for i in range(5)],[b[f'W{i}']for i in range(5)])}
 rows=[]
 for variant,(pos,w)in variants.items():
  for kind,t,D,closed in probes:
   dd=sit_pose(t,False)if (variant=='source'or variant.startswith('source-matched'))and kind=='sit'else sit_pose(1,False,.25*t)if (variant=='source'or variant.startswith('source-matched'))and kind=='lean'else D
   fn=f'{variant}-{kind}-{t:g}.npz'; points=deform(pos,w,dd,closed)
   np.savez(Q/'poses'/fn,**{f'p{i}':p for i,p in enumerate(points)},matrices=dd)
   rows.append({'variant':variant,'probe':kind,'fraction':t,'path':str(Q/'poses'/fn),'closed_glove_morph':closed,'source_relative_rest':variant,'head_neck_posture':'authored_source'if variant=='source'or variant.startswith('source-matched')else'root_natural'})
 rest={v:{f'p{i}':p for i,p in enumerate(pos)}for v,(pos,w)in variants.items()}
 for v,x in rest.items():np.savez(Q/f'{v}-bind.npz',**x)
 (Q/(label+'-canonical-manifest.json'if len(sys.argv)>1 else'pose-manifest.json')).write_text(json.dumps({'source_sha256':hashlib.sha256((Q/'C19-source.glb').read_bytes()).hexdigest(),'rows':rows,'poses_per_variant':len(probes),'axes_ranges':{'arm_targets':'world target vectors horizontal[0,0,±1], overhead[0,1,±.1], forward[1,0,±.1], about actual upperarm centres','elbow':'45/90 degree bilateral flex about cross(current forearm axis, worldUp); each forearm bends upward toward shoulder plane, no mirrored worldZ signs','forearm_twist':'45/90 degree about current anatomical forearm axis, forearm+hand subtree','wrist':'45/90 degree turn about current anatomical forearm axis, hand only;90 degree deliberately severe stress','squat':'hip drop140/280mm, torso lean5.7/11.5deg, original foot targets','lean':'seated torso additional7.16/14.32degree forward lean with fixed original grip/ankle targets'},'limitations':['Finite CPU poses, no continuous collision certificate.','Probe angles are stress tests, not authored motions or human range claims.','Natural posture is root supplied hypothesis, not clinical anatomy.'],'render_protocol':{'views':['front','side','rear'],'materials':['gray','original_PBR'],'matched_cameras':True,'required_contact_closeups':['left and right cuff/glove','underarm','hip/saddle'],'priority':['neutral','horizontal-1','overhead-1','forward-1','elbow-1','twist-1','wrist-1','sit-1','lean-1']}},indent=2))
 print(json.dumps({'variants':list(variants),'pose_count':len(rows),'manifest':str(Q/(label+'-canonical-manifest.json'if len(sys.argv)>1 else'pose-manifest.json'))}))

if __name__=='__main__':main()
