"""Explicit torso/inner-sleeve construction chart, separate ownership ablation.
Chart geometry transports original radial detail on torso and rounded arm cages;
source topology/normal field joins charts. This can alter effective posed arm
ownership, although source runtime W remains fixed: report that confound.
"""
from chart_labels import *
from scipy.sparse.csgraph import dijkstra
class TwoChartCage(SourceCharts):
 def __init__(self):
  super().__init__();e=self.edges;length=np.linalg.norm(self.unique[e[:,0]]-self.unique[e[:,1]],axis=1);g=coo_matrix((np.r_[length,length],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();collar=np.flatnonzero(self.cloth&(U[:,1]>1.48));held=np.r_[self.cuff,collar];distance=dijkstra(g,directed=False,indices=held,min_only=True)
  total=self.uw[:,1:4].sum(1)+self.uw[:,6:9].sum(1)+self.uw[:,10:13].sum(1);self.edit=self.cloth*smooth((total-.25)/.65)*smooth(distance/.05);self.edit[held]=0;self.held=held;self.mapping={}
  for sg,a in [(1,6),(-1,10)]:
   field=self.fields[sg];ids=np.flatnonzero((field>1e-8)&self.cloth);ref=self.ref[sg];curve=RoundedCurve(P[[a,a+1,a+2]],ref['startNormal']);s=curve.closest(self.unique[ids]);c,t,n,b=curve.at(s);rr=self.unique[ids]-c;local=np.stack([np.einsum('ij,ij->i',rr,t),np.einsum('ij,ij->i',rr,n),np.einsum('ij,ij->i',rr,b)],axis=1);self.mapping[sg]={'a':a,'ids':ids,'s':s,'local':local,'curve':curve,'normal':ref['startNormal']}
 def target(self,D,posed=None):
  skin=deform(self.pos,self.w,D,closed=True)if posed is None else posed
  if np.max(abs(D-np.eye(4)))<1e-10:return [p.copy()for p in skin],{'neutralIdentityExact':True,'maxCorrectionM':0.}
  world=np.zeros_like(U);np.add.at(world,INV,np.concatenate(skin));world/=np.bincount(INV)[:,None]
  body=np.einsum('ab,vb->va',D[2,:3,:],np.c_[self.unique,np.ones(len(U))],optimize=False);target=body.copy();rows=[]
  for sg,r in self.mapping.items():
   a=r['a'];ids=r['ids'];Q=np.einsum('nij,nj->ni',D[[a,a+1,a+2],:3,:],np.c_[P[[a,a+1,a+2]],np.ones(3)],optimize=False);curve=RoundedCurve(Q,np.einsum('ab,b->a',D[a,:3,:3],r['normal'],optimize=False));s=r['s']/r['curve'].length*curve.length;c,t,n,b=curve.at(s);phis=[]
   for fraction,j in [(.75,a+1),(.97,a+2)]:
    sr=np.array([r['curve'].length*fraction]);_,_,nr,_=r['curve'].at(sr);_,tp,np_,bp=curve.at(sr/r['curve'].length*curve.length);want=np.einsum('ab,b->a',D[j,:3,:3],nr[0],optimize=False);want=unit(want-tp[0]*np.dot(want,tp[0]));phis.append(float(np.arctan2(np.dot(want,bp[0]),np.dot(want,np_[0]))))
   f=r['s']/r['curve'].length;fore=phis[0]*smooth((f-.35)/.40);hand=phis[0]+np.arctan2(np.sin(phis[1]-phis[0]),np.cos(phis[1]-phis[0]))*smooth((f-.76)/.21);phi=np.where(f<.76,fore,hand);cs=np.cos(phi);sn=np.sin(phi);nn=n*cs[:,None]+b*sn[:,None];bb=b*cs[:,None]-n*sn[:,None];local=r['local'];warped=c+t*local[:,0,None]+nn*local[:,1,None]+bb*local[:,2,None];field=self.fields[sg][ids]
   target[ids]+=(warped-body[ids])*field[:,None];rows.append({'side':sg,'referenceArcM':r['curve'].length,'posedArcM':curve.length,'mappedVertices':len(ids)})
  correction=(target-world)*self.edit[:,None];out=[skin[i]+correction[INV[OFF[i]:OFF[i+1]]]for i in range(5)]
  return out,{'neutralIdentityExact':False,'maxCorrectionM':float(np.linalg.norm(correction,axis=1).max()),'headHandsExact':all(np.array_equal(out[i],skin[i])for i in [1,3,4]),'heldCuffCollarExact':bool(np.array_equal(correction[self.held],np.zeros_like(correction[self.held]))),'rows':rows,'effectiveOwnershipChanged':True,'limits':'Normal/topology chart assignment is authored anatomy, not groundtruth. Cage target changes effective posed torso-versus-arm response; compare separately to chart-weight-only same-D ablation. No triangle/contact certificate.'}
if __name__=='__main__':
 cage=TwoChartCage();rows=[];reference=ROOT/'hoodie-repair02/qa-lane/screenshot01/body34-reference-sample304.npz';D=np.load(reference)['joint_transforms0'];old=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/hoodie-repair02/shape-lane/volume-lane')
 for name,D in [('game304',D),('forward',np.load(old/'skin-forward-1.npz')['matrices']),('single90',np.load(old/'skin-single-elbow-90.npz')['matrices'])]:
  q,m=cage.target(D);np.savez(OUT/f'twochart-{name}.npz',**{f'p{i}':v for i,v in enumerate(q)},matrices=D);m.update(file=f'twochart-{name}.npz',matrixSHA256=hashlib.sha256(D.tobytes()).hexdigest());rows.append(m);print(m,flush=True)
 (OUT/'twochart-provenance.json').write_text(json.dumps({'sourceV7BindSHA256':hashlib.sha256(cage.input.read_bytes()).hexdigest(),'rows':rows},indent=2))
