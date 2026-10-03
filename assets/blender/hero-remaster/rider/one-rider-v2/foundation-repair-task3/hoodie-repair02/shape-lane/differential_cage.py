"""Offline pose editing via local rotation-preserving differential cage.
Same welded garment, frozen rest metric, soft attachment to exact LBS, anatomical
arm-plane underarm target and60mm bounded correction. Not cloth simulation.
No gravity, mass, contacts, dynamic warmstart or garment01 spring shell.
"""
from pathlib import Path
import sys,json,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent
class Cage:
 def __init__(self):
  sd=np.load(OUT/'shape-retop-uvsafe.npz');self.pos=[sd[f'p{i}']for i in range(5)];self.tri=[sd[f'tr{i}']for i in range(5)];self.weightsFile=ROOT/'hoodie-repair02/rig-lane/weights-ls-corrected.npz';wd=np.load(self.weightsFile);self.w=[wd[f'W{i}']for i in range(5)]
  self.rest=np.zeros_like(U);np.add.at(self.rest,INV,np.concatenate(self.pos));self.rest/=np.bincount(INV)[:,None];ct=np.concatenate([INV[self.tri[i]+OFF[i]]for i in [0,2]]);self.cloth=np.zeros(len(U),bool);self.cloth[np.unique(ct)]=True
  x,y,z=U.T;roi=self.cloth&(y>1.075)&(y<1.49)&(abs(z)>.12)&(abs(z)<.34);self.free=np.flatnonzero(roi);self.active=np.unique(ct[roi[ct].any(1)]);self.fixed=np.setdiff1d(self.active,self.free)
  e=np.unique(np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1),axis=0);e=e[np.isin(e,self.active).all(1)];self.e=e;self.r=self.rest[e[:,0]]-self.rest[e[:,1]];length=np.linalg.norm(self.r,axis=1);self.ew=(.008/np.maximum(length,.002))**2
  g=coo_matrix((np.r_[self.ew,self.ew],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();self.L=diags(np.asarray(g.sum(1)).ravel())-g
  # Fixed outer geometry plus smoothly increased anchor stiffness around each domain
  # edge. No discontinuous skin ownership is authored by this cage.
  anchor=np.full(len(U),.4);anchor+=10*smooth((abs(z)-.27)/.055)+10*smooth((.16-abs(z))/.04)+10*smooth((1.135-y)/.06)+10*smooth((y-1.43)/.06);self.anchor=anchor
  A=self.L[self.free][:,self.free]+diags(anchor[self.free]);self.solve=factorized(A.tocsc())
 def target(self,D,maxCorrection=.060,iterations=24):
  skin=deform(self.pos,self.w,D);world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(skin));world/=np.bincount(INV)[:,None]
  if np.max(abs(D-np.eye(4)))<1e-10:return skin,{'identityRestExact':True,'maxCorrectionM':0.,'method':'Differential cage skipped identity'}
  desired=world.copy();activation=[]
  for sg,a in [(1,6),(-1,10)]:
   rest=(P[a+1]-P[a]);rest/=np.linalg.norm(rest);axis=D[a,:3,:3]@rest;axis/=np.linalg.norm(axis);up=D[2,:3,:3]@np.array([0.,1.,0.]);normal=up-axis*np.dot(up,axis);norm=np.linalg.norm(normal)
   if norm<.2:continue
   normal/=norm;shoulder=D[a,:3,:3]@P[a]+D[a,:3,3];angle=np.arccos(np.clip(np.dot(axis,D[2,:3,:3]@rest),-1,1));full=np.arccos(np.clip(np.dot(rest,np.array([0.,0.,sg])),-1,1));act=float(smooth(angle/full));activation.append(act)
   delta=world-shoulder;along=np.einsum('ij,j->i',delta,axis);depth=np.maximum(-.075-np.einsum('ij,j->i',delta,normal),0)
   region=smooth((along+.003)/.075)*smooth((.612-along)/.13)*(U[:,2]*sg>0)*smooth((U[:,1]-1.105)/.055)*smooth((1.49-U[:,1])/.045)*smooth((abs(U[:,2])-.13)/.03)*self.cloth
   lift=np.minimum(.035,.55*depth)*region*act;desired+=lift[:,None]*normal
  q=world.copy();rot=np.repeat(np.eye(3)[None],len(U),axis=0);e=self.e
  for it in range(iterations):
   pe=q[e[:,0]]-q[e[:,1]];cov=np.zeros((len(U),3,3));outer=pe[:,:,None]*self.r[:,None,:]*self.ew[:,None,None];np.add.at(cov,e[:,0],outer);np.add.at(cov,e[:,1],outer);aa,_,bb=np.linalg.svd(cov[self.active]);rr=aa@bb;bad=np.linalg.det(rr)<0;aa[bad,:,-1]*=-1;rot[self.active]=aa@bb
   re=np.einsum('nij,nj->ni',(rot[e[:,0]]+rot[e[:,1]])*.5,self.r)*self.ew[:,None];rhs=np.zeros_like(U);np.add.at(rhs,e[:,0],re);np.add.at(rhs,e[:,1],-re);b=rhs[self.free]+self.anchor[self.free,None]*desired[self.free]-self.L[self.free][:,self.fixed]@q[self.fixed];nq=np.column_stack([self.solve(b[:,c])for c in range(3)]);delta=nq-world[self.free];length=np.linalg.norm(delta,axis=1);nq=world[self.free]+delta*np.minimum(1,maxCorrection/np.maximum(length,1e-15))[:,None];q[self.free]=nq
  correction=q-world;out=[skin[i]+correction[INV[OFF[i]:OFF[i+1]]]for i in range(5)];return out,{'identityRestExact':False,'maxCorrectionM':float(np.linalg.norm(correction,axis=1).max()),'changedUniqueVertices':int((np.linalg.norm(correction,axis=1)>1e-8).sum()),'armTargetActivation':activation,'method':'Rest-metric localrotation-preserving differential edit, exact LBS softattachment andfixed torso/sleeve outer/cuff boundaries,35mmanatomicalnormal target with60mm totalcap. Candidate only. No runtimephysics.'}
if __name__=='__main__':
 cage=Cage();rows=[]
 for kind,t in [('raise',0),('raise',.25),('raise',.5),('raise',.75),('raise',1),('sit',0),('sit',.5),('sit',1)]:
  D=raise_pose(t)if kind=='raise'else sit_pose(t,natural=True);p,m=cage.target(D);np.savez(OUT/f'differential-{kind}-{t}.npz',**{f'p{i}':v for i,v in enumerate(p)},matrices=D);m.update(pose=kind,t=t);rows.append(m);print(m,flush=True)
 (OUT/'differential-cage-provenance.json').write_text(json.dumps({'sourceSHA256':'186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e','shape':'shape-retop-uvsafe.npz','weights':str(cage.weightsFile),'rows':rows,'limits':'Offline poseedit mustbakeinverseLBSmorphandqualifystockruntime. No mass/clothsims/CCD/collisionconstraints. Head/hands/fixedboundaries held.'},indent=2))
