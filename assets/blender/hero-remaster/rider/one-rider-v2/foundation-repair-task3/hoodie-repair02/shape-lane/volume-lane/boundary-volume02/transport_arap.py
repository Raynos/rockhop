"""Sewn-boundary ARAP material ablation on BOTH reconstructed charts.
No collision acceptance is built into ARAP: literal full gates remain mandatory.
Reference: Sorkine & Alexa, SGP2007, https://doi.org/10.2312/SGP/SGP07/109-116
Frozen source/weights/D, exactly pinned boundaries, no pose atlas or W search.
"""
from pathlib import Path
import numpy as np,json,hashlib,sys
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
HERE=Path(__file__).resolve().parent;H=HERE.parents[2];ROOT=H.parent
f=np.load(HERE.parent/'armhole-construction/armhole-chart-outward.npz');assert hashlib.sha256((HERE.parent/'armhole-construction/armhole-chart-outward.npz').read_bytes()).hexdigest()=='10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7'
class Chart:
 def __init__(self,ids,tri,fixed):
  self.ids=ids;self.p=f['p0'][ids];self.tri=tri;self.fixed=fixed;self.free=np.setdiff1d(np.arange(len(ids)),fixed);self.edges=np.unique(np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1),axis=0);self.a,self.b=self.edges.T;self.dp=self.p[self.a]-self.p[self.b];self.w=1/np.maximum(np.linalg.norm(self.dp,axis=1),.002)**2;g=coo_matrix((np.r_[self.w,self.w],(np.r_[self.a,self.b],np.r_[self.b,self.a])),shape=(len(ids),len(ids))).tocsr();self.L=diags(np.asarray(g.sum(1)).ravel())-g;self.solve=factorized(self.L[self.free][:,self.free].tocsc());self.Lfb=self.L[self.free][:,fixed]
 def run(self,posed,iterations=12):
  q=posed[self.ids].copy();boundary=q[self.fixed].copy();history=[]
  for iteration in range(iterations):
   dq=q[self.a]-q[self.b];C=np.zeros((len(q),3,3));term=self.w[:,None,None]*np.einsum('ei,ej->eij',dq,self.dp,optimize=False);np.add.at(C,self.a,term);np.add.at(C,self.b,term);u,s,v=np.linalg.svd(C);R=np.einsum('nij,njk->nik',u,v,optimize=False);negative=np.linalg.det(R)<0;u[negative,:,-1]*=-1;R=np.einsum('nij,njk->nik',u,v,optimize=False);edge=self.w[:,None]*np.einsum('eij,ej->ei',(R[self.a]+R[self.b])*.5,self.dp,optimize=False);rhs=np.zeros_like(q);np.add.at(rhs,self.a,edge);np.add.at(rhs,self.b,-edge);old=q.copy();q[self.free]=self.solve(rhs[self.free]-self.Lfb@boundary);q[self.fixed]=boundary;history.append(float(np.linalg.norm(q-old,axis=1).max()))
  return q,history
charts=[]
for side in ['L','R']:
 n=len(f[f'oldCutSourceAlias{side}']);tess=f[f'insertChartTriangles{side}'];insertIds=f[f'insertChartVertices{side}'];bodyT=f['tr0'][f[f'bodyClosureFaceIDs{side}']];bodyIds=np.full(len(insertIds),-1,int);bodyIds[tess[:,[0,2,1]].ravel()]=bodyT.ravel();assert(bodyIds>=0).all();fixed=np.arange(2*n)
 charts.append(('body-'+side,Chart(bodyIds,tess[:,[0,2,1]],fixed)));charts.append(('insert-'+side,Chart(insertIds,tess,fixed)))
def skin(D):
 out=[]
 for i in range(5):
  p=f[f'p{i}'];w=f[f'W{i}'];A=np.einsum('vj,jab->vab',w,D,optimize=False);out.append(np.einsum('vab,vb->va',A[:,:3,:3],p,optimize=False)+A[:,:3,3])
 return out
if __name__=='__main__':
 authPath=ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz';auth=np.load(authPath);D=auth['D'][304];pts=skin(D);control=[p.copy()for p in pts];neutral=f['p0'].copy();nhistory=[]
 for name,c in charts:
  q,h=c.run(pts[0]);pts[0][c.ids]=q;qn,hn=c.run(f['p0']);neutral[c.ids]=qn;nhistory.append({'chart':name,'iterations':len(h),'maxFinalStepM':h[-1],'maxOffsetM':float(np.linalg.norm(q-control[0][c.ids],axis=1).max()),'boundaryDeltaM':float(np.linalg.norm(q[c.fixed]-control[0][c.ids[c.fixed]],axis=1).max())})
 out=HERE/'arap-material-actual304.npz';np.savez_compressed(out,matrices=D,**{f'p{i}':p for i,p in enumerate(pts)});r={'status':'UNACCEPTED metric-only transport ablation; no collision or area barriers yet','sourceShapeSHA256':'10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7','authoritativeDPath':str(authPath),'authoritativeDSHA256':hashlib.sha256(authPath.read_bytes()).hexdigest(),'sample':304,'DHash':hashlib.sha256(D.tobytes()).hexdigest(),'candidatePath':str(out),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'neutralIdentityMaxErrorM':float(np.linalg.norm(neutral-f['p0'],axis=1).max()),'heldPrimitivesExact':all(np.array_equal(pts[i],control[i])for i in [1,2,3,4]),'charts':nhistory,'method':'Positive inverse-rest-edge weighted vertex ARAP,12local/global iterations, Dirichlet original sewn boundaries and high opening. Only added chart interiors change. All matrices/weights/source geometry stay frozen.','primarySource':'https://doi.org/10.2312/SGP/SGP07/109-116','limits':'ARAP objective alone neither enforces volume nor guarantees nonintersection; full literal gate decides whether to continue. Retained upper self-crossings cannot be repaired by this interior-only response.'};(HERE/'arap-material-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
