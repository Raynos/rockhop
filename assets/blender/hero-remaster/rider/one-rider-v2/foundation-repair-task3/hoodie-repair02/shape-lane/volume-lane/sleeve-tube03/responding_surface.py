"""Continuous boundary-driven material construction; neutral only verified.
No fitted pose atlas or weight search. Pose/render qualification awaits rest appearance.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import SourceCharts,unit,smooth,MORPH

def rotation(a,b):
 a=unit(np.asarray(a)[None])[0];b=unit(np.asarray(b)[None])[0];v=np.cross(a,b);d=float(np.clip(a@b,-1,1));s=np.linalg.norm(v)
 if s<1e-10:
  if d>0:return np.eye(3)
  seed=np.eye(3)[np.argmin(abs(a))];axis=unit(np.cross(a,seed)[None])[0];return 2*np.outer(axis,axis)-np.eye(3)
 K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K*((1-d)/(s*s))

def curve_frames(C,N=13,seed=None):
 s=np.linspace(0,1,N);cc=(1-s[:,None])**3*C[0]+3*(1-s[:,None])**2*s[:,None]*C[1]+3*(1-s[:,None])*s[:,None]**2*C[2]+s[:,None]**3*C[3];tt=unit(3*(1-s[:,None])**2*(C[1]-C[0])+6*(1-s[:,None])*s[:,None]*(C[2]-C[1])+3*s[:,None]**2*(C[3]-C[2]));e=np.array([1.,0,0])if seed is None else np.asarray(seed);e=unit((e-tt[0]*np.dot(e,tt[0]))[None])[0];frames=[]
 for i,t in enumerate(tt):
  if i:e=rotation(tt[i-1],t)@e;e=unit((e-t*np.dot(e,t))[None])[0]
  frames.append(np.c_[e,np.cross(t,e),t])
 return cc,np.array(frames)

def polar_fit(rest,posed):
 A=rest-rest.mean(0);B=posed-posed.mean(0);u,_,vh=np.linalg.svd(np.einsum('ni,nj->ij',B,A));fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vh);return u@fix@vh

class RespondingSleeve:
 def __init__(self,path=None):
  self.path=Path(path or HERE/'source-sleeve-tube-rest07-uvchart.npz');self.f=dict(np.load(self.path));self.c=SourceCharts();self.cap={};self.rest={}
  for sg,side in [(1,'L'),(-1,'R')]:
   f=self.f;faces=f['tr0'][f['bodyCapFaceIDs'+side]];ids=np.unique(faces);lookup={int(v):j for j,v in enumerate(ids)};tri=np.array([[lookup[int(v)]for v in t]for t in faces]);p=f['p0'][ids];e=np.unique(np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1),axis=0);w=1/np.maximum(np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1),.002)**2;g=coo_matrix((np.r_[w,w],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(ids),len(ids))).tocsr();L=diags(np.asarray(g.sum(1)).ravel())-g;fixed=np.flatnonzero(f['sourceUniqueVertex0'][ids]>=0);free=np.setdiff1d(np.arange(len(ids)),fixed);solve=factorized(L[free][:,free].tocsc());self.cap[side]=(ids,fixed,free,solve,L[free][:,fixed]);C=f['curveControlRest'+side];rows=f['tubeRows'+side];cc,M=curve_frames(C,len(rows));local=np.einsum('rij,rnj->rni',np.transpose(M,(0,2,1)),f['p0'][rows]-cc[:,None]);self.rest[side]=(C,cc,M,local)
 def deform(self,D,closed=False):
  f=self.f;c=self.c;q=[]
  for pi in range(5):
   p=f[f'p{pi}'].copy()
   if closed:p[:len(c.pos[pi])]+=MORPH[pi]
   v=np.c_[p,np.ones(len(p))];q.append(np.einsum('vb,bjk,vk->vj',f[f'W{pi}'],D,v)[:,:3])
  # Actual new edge nodes are barycentric on the posed SOURCE triangle,
  # rather than multiplying independently averaged P and W (non-equivalent).
  for pi in [0,2]:
   par=f[f'sourceVertexParents{pi}'];b=f[f'sourceVertexBarycentric{pi}'];idx=np.flatnonzero((np.arange(len(par))>=len(c.pos[pi]))&(par[:,0]>=0)&(par[:,1]>=0));q[pi][idx]=(q[pi][par[idx]]*b[idx,:,None]).sum(1)
  refs={}
  for pi in [0,2]:
   active=np.unique(f[f'tr{pi}']);par=f[f'sourceVertexParents{pi}'];source=active[(active<len(c.pos[pi]))|((par[active,0]>=0)&(par[active,1]>=0))]
   for i in source:refs[int(f[f'physicalWeld{pi}'][i])]=q[pi][i].copy()
  for pi in [0,2]:
   for i in np.unique(f[f'tr{pi}']):
    key=int(f[f'physicalWeld{pi}'][i])
    if i>=len(c.pos[pi])and key in refs:q[pi][i]=refs[key]
  for sg,side,a in [(1,'L',6),(-1,'R',10)]:
   ids,fixed,free,solve,Lfx=self.cap[side];rigid=np.einsum('jk,vk->vj',D[2],np.c_[f['p0'][ids],np.ones(len(ids))])[:,:3];delta=q[0][ids[fixed]]-rigid[fixed];correction=np.zeros_like(rigid);correction[fixed]=delta;correction[free]=np.column_stack([solve(-Lfx@delta[:,j])for j in range(3)]);q[0][ids]=rigid+correction
   rows=f['tubeRows'+side];C,restC,restM,local=self.rest[side];root=q[0][f['bodyOpeningVertices'+side]].copy();end=q[0][rows[-1]].copy();R=polar_fit(f['p0'][rows[0]],root);E=polar_fit(f['p0'][rows[-1]],end);Cnew=np.array([root.mean(0),root.mean(0)+R@(C[1]-C[0]),end.mean(0)+E@(C[2]-C[3]),end.mean(0)]);cc,M=curve_frames(Cnew,len(rows),R@restM[0,:,0]);expected0=cc[0]+np.einsum('ij,nj->ni',M[0],local[0]);expected1=cc[-1]+np.einsum('ij,nj->ni',M[-1],local[-1]);res0=np.einsum('ij,nj->ni',M[0].T,root-expected0);res1=np.einsum('ij,nj->ni',M[-1].T,end-expected1);s=smooth(np.linspace(0,1,len(rows)));ll=local+(1-s[:,None,None])*res0+s[:,None,None]*res1;qq=cc[:,None]+np.einsum('rij,rnj->rni',M,ll);qq[0]=root;qq[-1]=end;q[0][rows]=qq
  # UV-only duplicated longitudinal/root rows receive the exact material
  # point of their physical weld; no source control is changed.
  materialRefs=dict(refs)
  for side in ['L','R']:
   ids=np.unique(np.r_[self.cap[side][0],f['tubeRows'+side].ravel()])
   for i in ids:
    k=int(f['physicalWeld0'][i])
    if k not in refs:materialRefs[k]=q[0][i].copy()
  for pi in [0,2]:
   for i in np.unique(f[f'tr{pi}']):
    k=int(f[f'physicalWeld{pi}'][i])
    if i>=len(c.pos[pi])and k in materialRefs:q[pi][i]=materialRefs[k]
  return q

if __name__=='__main__':
 driver=RespondingSleeve();D=np.broadcast_to(np.eye(4),(19,4,4)).copy();q=driver.deform(D);f=driver.f;neutral=max(float(np.abs(q[i]-f[f'p{i}']).max())for i in range(5));assert neutral<1e-10,neutral
 report={'status':'NEUTRAL_IDENTITY_VERIFIED_ONLY; standing review gates posed runs','candidateSHA256':hashlib.sha256(driver.path.read_bytes()).hexdigest(),'maximumNeutralDeltaM':neutral,'method':'Exact original19bone LBS source controls; clipped triangles use actual posed source-edge barycentric points. Free torso cap/opening uses positive rest-graph harmonic displacement from sewn source boundary. Tube follows a cubic responding centreline and rotation-minimizing frames, with frozen per-row source-shaped local material coordinates and exact root/end residuals. No pose atlas/staticweight fitting, no DQ.','runtime':'Explicit post-bone material geometry adapter if qualified. Does not assert stock4skin equivalence. Root separate4influence bind ablation remains independent.','remaining':'Standing shape/normals, actual304 fulltriangles and visual, between-key and game-envelope gates untested; no contact/support/volume acceptance.'};(HERE/'responding-surface-neutral.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
