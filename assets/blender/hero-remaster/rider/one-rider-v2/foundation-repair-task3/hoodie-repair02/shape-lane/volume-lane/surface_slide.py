"""Distinct static torso-surface slide construction, frozen V7 skin ownership.
Rest-metric differential editing frees lateral torso material to slide axially and
circumferentially on its own rest radial torso envelope. Sleeve/collar/cuff are
controlled; actual triangle gates, not smoothed normals, decide usefulness.
No dynamics, height-band displacement, spring shell or pose atlas.
"""
from rounded_curve import *
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized

class TorsoSurfaceSlide(RoundedSleeve):
 def __init__(self):
  super().__init__();self.torso=self.uw[:,1:4].sum(1);self.arm=self.uw[:,6:9].sum(1)+self.uw[:,10:13].sum(1)
  ct=np.concatenate([INV[self.tri[i]+OFF[i]]for i in [0,2]])
  cuff=np.intersect1d(np.unique(np.concatenate([INV[OFF[i]:OFF[i+1]]for i in [0,2]])),np.unique(INV[OFF[1]:OFF[2]]))
  # Region is semantic skeleton ownership; no world-Y strip is displaced.
  eligible=self.cloth&((self.torso>.25)|(self.arm>.02));central=(abs(U[:,2])<.09)&(self.torso>.8)
  collar=(U[:,1]>P[3,1]-.025)&(self.arm<.08)
  self.free=np.flatnonzero(eligible&~central&~collar&~np.isin(np.arange(len(U)),cuff))
  self.active=np.unique(ct[np.isin(ct,self.free).any(1)]);self.fixed=np.setdiff1d(self.active,self.free)
  e=np.unique(np.sort(np.concatenate([ct[:,[0,1]],ct[:,[1,2]],ct[:,[0,2]]]),axis=1),axis=0);e=e[np.isin(e,self.active).all(1)]
  self.e=e;self.r=self.unique[e[:,0]]-self.unique[e[:,1]];length=np.linalg.norm(self.r,axis=1);self.ew=(.008/np.maximum(length,.002))**2
  g=coo_matrix((np.r_[self.ew,self.ew],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();self.L=diags(np.asarray(g.sum(1)).ravel())-g
  # Original owner proportions are frozen. Lateral torso has tangential freedom;
  # sleeve stays softly attached to the independently frozen rounded volume cage.
  anchor=.025+.65*self.arm**2;self.anchor=anchor
  self.solve=factorized((self.L[self.free][:,self.free]+diags(anchor[self.free])).tocsc())
  self.cx=float((P[6,0]+P[10,0])*.5);self.radial=self.unique[:,[0,2]]-np.array([self.cx,0.]);self.rho=np.linalg.norm(self.radial,axis=1)
  self.slide=smooth((self.torso-.35)/.55)*smooth((abs(U[:,2])-.08)/.09)
  self.slide[~eligible|central|collar|np.isin(np.arange(len(U)),cuff)]=0
 def target(self,D,posed=None,iterations=32,maxCorrection=.180,withVolume=True):
  original=deform(self.pos,self.w,D)if posed is None else posed
  if np.max(abs(D-np.eye(4)))<1e-10:return [p.copy()for p in original],{'neutralIdentityExact':True,'maxCorrectionM':0.}
  desired,volumeMeta=super().target(D,posed=original)if withVolume else (original,{})
  world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(original));world/=np.bincount(INV)[:,None]
  want=np.zeros_like(U);np.add.at(want,INV,np.concatenate(desired));want/=np.bincount(INV)[:,None]
  q=want.copy();e=self.e;rot=np.repeat(np.eye(3)[None],len(U),axis=0);fixedTerm=self.L[self.free][:,self.fixed]@q[self.fixed]
  for iteration in range(iterations):
   pe=q[e[:,0]]-q[e[:,1]];cov=np.zeros((len(U),3,3));outer=pe[:,:,None]*self.r[:,None,:]*self.ew[:,None,None];np.add.at(cov,e[:,0],outer);np.add.at(cov,e[:,1],outer)
   aa,_,bb=np.linalg.svd(cov[self.active]);rr=aa@bb;bad=np.linalg.det(rr)<0;aa[bad,:,-1]*=-1;rot[self.active]=aa@bb
   re=np.einsum('nij,nj->ni',(rot[e[:,0]]+rot[e[:,1]])*.5,self.r)*self.ew[:,None];rhs=np.zeros_like(U);np.add.at(rhs,e[:,0],re);np.add.at(rhs,e[:,1],-re)
   b=rhs[self.free]+self.anchor[self.free,None]*want[self.free]-fixedTerm;nq=np.column_stack([self.solve(b[:,c])for c in range(3)])
   # Rest-exact radial torso coordinate manifold. Only its axial/circumferential
   # coordinates may slide; this projection does not establish body contact.
   local=np.einsum('va,ab->vb',nq-D[2,:3,3],D[2,:3,:3],optimize=False);r=local[:,[0,2]]-np.array([self.cx,0.]);nr=np.linalg.norm(r,axis=1);projected=local.copy();projected[:,[0,2]]=np.array([self.cx,0.])+r*(self.rho[self.free]/np.maximum(nr,1e-12))[:,None]
   manifold=np.einsum('va,ba->vb',projected,D[2,:3,:3],optimize=False)+D[2,:3,3];blend=self.slide[self.free];nq=nq*(1-blend[:,None])+manifold*blend[:,None]
   delta=nq-world[self.free];length=np.linalg.norm(delta,axis=1);nq=world[self.free]+delta*np.minimum(1,maxCorrection/np.maximum(length,1e-15))[:,None];q[self.free]=nq
  delta=q-world;out=[original[i]+delta[INV[OFF[i]:OFF[i+1]]]for i in range(5)]
  local=np.einsum('va,ab->vb',q-D[2,:3,3],D[2,:3,:3],optimize=False);before=np.einsum('va,ab->vb',world-D[2,:3,3],D[2,:3,:3],optimize=False);slideIds=self.free[self.slide[self.free]>.5]
  return out,{'neutralIdentityExact':False,'maxCorrectionM':float(np.linalg.norm(delta,axis=1).max()),'freeVertices':len(self.free),'changedVertices':int((np.linalg.norm(delta,axis=1)>1e-8).sum()),'maxTorsoAxialSlideM':float(abs(local[slideIds,1]-before[slideIds,1]).max(initial=0)),'headHandsExact':all(np.array_equal(out[i],original[i])for i in [1,3,4]),'volumeMeta':volumeMeta,'method':'Frozen ownership + rest-metric differential reconstruction + lateral torso axial/circumferential slide on source radial envelope. Static pose construction, no world-height target.','limits':'No cloth dynamics/body scan/contact/CCD guarantee. Projection does not guarantee monotonic2D surface chart. Actual triangle crossings and compression are decisive.'}
