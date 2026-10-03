from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'scripts'));from base import *
path=Path(sys.argv[1]);tag=path.stem;data=np.load(path);ws=[data[f'W{i}']for i in range(5)];corrected='corrected'in tag
pp=POS if not corrected else[np.load(HERE.parent/'shape-lane/shape-rest-final.npz')[f'p{i}']for i in range(5)]
folder=HERE/(tag+'-poses');folder.mkdir(exist_ok=True)
cnt=np.bincount(INV);rest=np.zeros_like(U);np.add.at(rest,INV,np.concatenate(pp));rest/=cnt[:,None]
roi=((U[CT][:,:,1]>1.08)&(U[CT][:,:,1]<1.49)&(abs(U[CT][:,:,2])<.405)).all(1);t=CT[roi];e=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0)
l0=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1);a0=np.linalg.norm(np.cross(rest[t[:,1]]-rest[t[:,0]],rest[t[:,2]]-rest[t[:,0]]),axis=1)
def limb(kind,angle):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 for side,sg in [('L',1),('R',-1)]:
  a,b,c=[IND[s+'.'+side]for s in ['upperArm','forearm','hand']]
  pivot=P[c]if kind=='wrist'else P[b];axis=np.array([0,0,sg],float)
  if kind=='twist':axis=P[c]-P[b];axis/=np.linalg.norm(axis)
  rot=R.from_rotvec(axis*angle).as_matrix()
  for j in ([c]if kind=='wrist'else[b,c]):D[j,:3,:3]=rot;D[j,:3,3]=pivot-rot@pivot
 return D
probes=[('rest',0,np.repeat(np.eye(4)[None],N,axis=0))]+[('raise',t,raise_pose(t))for t in [.125,.25,.375,.5,.625,.75,.875,1,1.2]]+[('sit',t,sit_pose(t,natural=True))for t in [0,.25,.5,.75,1]]
probes +=[(kind,angle,limb(kind,np.deg2rad(angle)))for kind,angles in [('elbow',[35,70,110]),('twist',[-90,-45,45,90]),('wrist',[-65,-45,-30,30,45,65])]for angle in angles]
rows=[]
for kind,v,D in probes:
 pts=deform(pp,ws,D,kind=='sit');q=np.zeros_like(U);np.add.at(q,INV,np.concatenate(pts));q/=cnt[:,None]
 ratio=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1)/l0;area=np.linalg.norm(np.cross(q[t[:,1]]-q[t[:,0]],q[t[:,2]]-q[t[:,0]]),axis=1)/a0
 r={'kind':kind,'value':v,'maxAllEdges':float(ratio.max()),'maxEdges2mm':float(ratio[l0>=.002].max()),'p99Edges2mm':float(np.quantile(ratio[l0>=.002],.99)),'collapsedBelowQuarter':int((area<.25).sum())};rows.append(r)
 np.savez(folder/f'{kind}-{v}.npz',**{f'p{i}':p for i,p in enumerate(pts)},matrices=D)
(HERE/(tag+'-gate.json')).write_text(json.dumps({'rows':rows,'reference':str(path),'correctedRest':corrected,'trainingHoldouts':'Raise .125/.375/.625/.875 and sit.25/.5/.75 not trainingstates; wrist/twist all untrained. Finite probes only, triangle QA pending.'},indent=2));print(json.dumps(rows))
