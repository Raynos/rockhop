"""Bounded pose-aware least squares. No height ownership discontinuity.

The residual is posed edge minus the average blended rotation of that rest
edge. Ownership is scalar, so all poses contribute a quadratic sparse energy.
Translation variation, rather than required rigid rotation, is penalized.
"""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.optimize import minimize
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'scripts'))
from base import *
shape='source'if'--corrected'not in sys.argv else'corrected'
src=HERE.parent/'shape-lane/shape-rest-final.npz'
pp=POS if shape=='source'else[np.load(src)[f'p{i}']for i in range(5)]
uq=np.zeros_like(U);cnt=np.bincount(INV);np.add.at(uq,INV,np.concatenate(pp));uq/=cnt[:,None]
cloth=np.zeros(len(U),bool);cloth[np.unique(CT)]=True;y=U[:,1];z=abs(U[:,2]);e=edges
length=np.linalg.norm(U[e[:,0]]-U[e[:,1]],axis=1)
graph=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr()
uw=np.zeros((len(U),N));np.add.at(uw,INV,np.concatenate(W));uw/=cnt[:,None]
tor=uw.copy();tor[:,[5,6,7,8,9,10,11,12]]=0;total=tor.sum(1);tor/=np.maximum(total[:,None],1e-15);tor[total<1e-9]=0;tor[total<1e-9,2]=1
low=cloth&(y<1.185);le=e[low[e].all(1)]
lg=coo_matrix((np.ones(2*len(le)),(np.r_[le[:,0],le[:,1]],np.r_[le[:,1],le[:,0]])),shape=(len(U),len(U))).tocsr();_,lab=connected_components(lg,directed=False)
torlabel=lab[np.argmin(np.linalg.norm(U-[.64,1.1,0],axis=1))];tormarker=low&(lab==torlabel)&(y>.94)
train=[raise_pose(t)for t in [.25,.5,.75,1,1.2]]+[sit_pose(t,natural=True)for t in [0,.33,.67,1]]+[sit_pose(.5,natural=True,leanoffset=.15)]
def elbow(angle):
 D=np.repeat(np.eye(4)[None],N,axis=0)
 for sg,b in [(1,7),(-1,11)]:
  rr=R.from_rotvec(np.array([0,0,sg])*angle).as_matrix()
  for j in [b,b+1]:D[j,:3,:3]=rr;D[j,:3,3]=P[b]-rr@P[b]
 return D
train +=[elbow(np.deg2rad(a))for a in [35,70,110]]
new=tor.copy();owners={};arms={};records=[]
initial=np.load(HERE/'weights-softened.npz')
for side,sg in [('L',1),('R',-1)]:
 start=time.monotonic();a,b,c=[IND[s+'.'+side]for s in ['upperArm','forearm','hand']]
 axis=P[b]-P[a];t=np.einsum('ij,j->i',U-P[a],axis)/np.dot(axis,axis);fore=smooth((t-.76)/.39)
 cuffids=np.intersect1d(INV[OFF[0]:OFF[1]],INV[OFF[1]:OFF[2]]);cuffids=cuffids[U[cuffids,2]*sg>0]
 dc=dijkstra(graph,indices=cuffids,min_only=True,directed=False);wrist=1-smooth((dc-.018)/.072);wrist[~np.isfinite(dc)]=0
 arm=np.zeros_like(uw);arm[:,a]=1-fore;arm[:,b]=fore*(1-wrist);arm[:,c]=fore*wrist;arm[cuffids]=0;arm[cuffids,c]=1;arms[side]=arm
 label=lab[np.argmin(np.linalg.norm(U-[.61,1.1,sg*.285],axis=1))];marker1=(low&(lab==label)&(y>.87))|(cloth&(U[:,2]*sg>.255)&(y<1.43)&(y>.94))
 active=cloth&(U[:,2]*sg>0)&(y>.87)&(y<1.49)
 # Keep head/hood core and centre torso stationary; true cuff ring stays exactly hand-owned.
 fixed0=(~active)|(z<.100)
 fixed1=cloth&(U[:,2]*sg>0)&(dc<.015)
 fixed0&=~fixed1
 free=np.flatnonzero(~(fixed0|fixed1));fixed=np.flatnonzero(fixed0|fixed1)
 selected=e[active[e].any(1)];i,j=selected.T
 ell=np.linalg.norm(uq[i]-uq[j],axis=1);scale=1/np.maximum(ell,.002)**2
 aa=np.zeros(len(i));bb=aa.copy();ab=aa.copy();ri=aa.copy();rj=aa.copy()
 restedge=uq[i]-uq[j]
 for D in train:
  tm=np.einsum('vj,jab->vab',tor,D[:,:3,:],optimize=False);am=np.einsum('vj,jab->vab',arm,D[:,:3,:],optimize=False)
  tp=np.einsum('vab,vb->va',tm,np.c_[uq,np.ones(len(uq))],optimize=False)
  ap=np.einsum('vab,vb->va',am,np.c_[uq,np.ones(len(uq))],optimize=False);disp=ap-tp
  rotavg=(tm[i,:,:3]+tm[j,:,:3])*.5
  rotdiff=(am[i,:,:3]+am[j,:,:3])*.5-rotavg
  edgechange=.5*np.einsum('eab,eb->ea',rotdiff,restedge,optimize=False)
  ca=disp[i]-edgechange;cb=-disp[j]-edgechange
  cc=tp[i]-tp[j]-np.einsum('eab,eb->ea',rotavg,restedge,optimize=False)
  aa+=scale*np.einsum('ij,ij->i',ca,ca);bb+=scale*np.einsum('ij,ij->i',cb,cb);ab+=scale*np.einsum('ij,ij->i',ca,cb)
  ri-=scale*np.einsum('ij,ij->i',ca,cc);rj-=scale*np.einsum('ij,ij->i',cb,cc)
 Q=coo_matrix((np.r_[aa,bb,ab,ab],(np.r_[i,j,i,j],np.r_[i,j,j,i])),shape=(len(U),len(U))).tocsr()
 rhs=np.zeros(len(U));np.add.at(rhs,i,ri);np.add.at(rhs,j,rj)
 prior=initial['ownership'+side].copy();prior[fixed0]=0;prior[fixed1]=1
 diag=Q.diagonal();anchors=tormarker|marker1
 penalty=.10*np.maximum(diag,1)*anchors+.0005*np.maximum(diag,1)
 desired=prior.copy();desired[tormarker]=0;desired[marker1]=1;desired[fixed0]=0;desired[fixed1]=1
 Q+=diags(penalty);rhs+=penalty*desired
 value=np.zeros(len(U));value[fixed1]=1
 qf=Q[free][:,free];rf=rhs[free]-Q[free][:,fixed]@value[fixed]
 norm=max(float(np.median(qf.diagonal())),1);qf/=norm;rf/=norm
 def objective(x):
  qx=qf@x;g=qx-rf;return .5*float(np.einsum('i,i->',x,qx))-float(np.einsum('i,i->',rf,x)),g
 result=minimize(objective,prior[free],jac=True,bounds=[(0,1)]*len(free),method='L-BFGS-B',options={'maxiter':500,'ftol':1e-11,'gtol':1e-7,'maxls':40})
 value[free]=result.x;owners[side]=value
 records.append({'side':side,'unknowns':len(free),'iterations':result.nit,'converged':bool(result.success),'status':result.message,'seconds':time.monotonic()-start,'initialObjective':float(objective(prior[free])[0]),'finalObjective':float(result.fun)})
 print(records[-1],flush=True)
 # Per-side ownership shares one torso baseline; combine both after solving independently.
alpha=owners['L']+owners['R'];new=tor*(1-alpha[:,None])+arms['L']*owners['L'][:,None]+arms['R']*owners['R'][:,None]
use=cloth&(y>.87)&(y<1.49);new[~use]=uw[~use]
for k in [1,3,4]:new[INV[OFF[k]:OFF[k+1]]]=W[k]
si=np.argsort(new,axis=1)[:,-4:];val=np.take_along_axis(new,si,axis=1);val/=val.sum(1,keepdims=True);new[:]=0;np.put_along_axis(new,si,val,axis=1)
out=[new[INV[OFF[k]:OFF[k+1]]]for k in range(5)]
path=HERE/f'weights-ls-{shape}.npz';np.savez(path,**{f'W{k}':w for k,w in enumerate(out)},ownershipL=owners['L'],ownershipR=owners['R'],uniquePositions=U,sourceCentres=P)
rec={'method':__doc__,'sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'geometry':shape,'geometryFile':str(src)if shape=='corrected'else str(ROOT/'deliverables/C19.glb'),'trainingPoses':len(train),'records':records,'hardAnatomicalAnchors':'centrecloth |z|<.1, exact glove/cuffring plus15mm garment graph extent, rigidhead/hands; semanticlower sleeve/torso components softlypenalized with weight.1diagonalenergy; no ownershipjumpatcomponentcut','contract':'Top4 normalized sharedweldedweights, same19bones/restcentres. Head/glove geometryweights preserved.','limits':'Finite13pose deformation-gradientleast-squares, not cloth mechanics or universal poseclearance. Holdout/visual/collision gate mandatory.'}
(HERE/f'weights-ls-{shape}-provenance.json').write_text(json.dumps(rec,indent=2));print(path,flush=True)
