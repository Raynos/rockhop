"""Owned rest-geometry modeling: fixed-boundary harmonic patch + ARAP gusset cage.
No weights, runtime physics or render job. Mesh order and UVs unchanged.
"""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized,spsolve
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent
cloth=np.zeros(len(U),bool);cloth[np.unique(CT)]=True
patches=[]
def patch(q):
 for sg in [1,-1]:
  select=((U[:,0]-.517)**2+((U[:,1]-1.367)*1.3)**2+((U[:,2]-sg*.183)*1.3)**2)<.03**2
  faces=CT[select[CT].all(1)];ee=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[0,2]]]),axis=1);ee,c=np.unique(ee,axis=0,return_counts=True);boundary=np.unique(ee[c==1]);vs=np.unique(faces);inside=np.setdiff1d(vs,boundary)
  graph=coo_matrix((np.ones(len(ee)*2),(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();L=diags(np.asarray(graph.sum(1)).ravel())-graph
  if len(inside):q[inside]=spsolve(L[inside][:,inside],-L[inside][:,boundary]@q[boundary])
  patches.append({'sideSign':sg,'vertices':vs.tolist(),'interior':inside.tolist(),'boundary':boundary.tolist(),'facesGlobalCombined':np.flatnonzero(select[CT].all(1)).tolist(),'eulerCharacteristic':int(len(vs)-len(ee)+len(faces)),'boundaryFixedExactly':True,'boundaryEdges':ee[c==1].tolist()})
 return q
qpatch=patch(U.copy())
# Cage handles are applied to the original connected surface. Symmetric lift acts on
# only the low armhole crease; outer sleeves, neckline and lower torso anchors hold.
x,y,z=U.T;az=abs(z)
roi=cloth&(y>1.065)&(y<1.485)&(az<.355);ids=np.flatnonzero(roi);active=np.unique(CT[roi[CT].any(1)]);free=np.flatnonzero(roi);fixed=np.setdiff1d(active,free)
e=edges[np.isin(edges,active).all(1)];length=np.linalg.norm(U[e[:,0]]-U[e[:,1]],axis=1);ew=np.ones(len(e))
graph=coo_matrix((np.r_[ew,ew],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(U),len(U))).tocsr();L=diags(np.asarray(graph.sum(1)).ravel())-graph
crease=np.exp(-((az-.194)/.025)**4)*np.exp(-((y-1.20)/.040)**4)*cloth
chest=smooth((y-1.09)/.12)*smooth((1.49-y)/.15)*smooth((.215-az)/.08)*smooth((x-.65)/.12)*cloth
target=U.copy();target[:,1]+=.155*crease;target[:,0]-=.030*chest
# Soft constraints allow adjacent triangles to redistribute tangentially; high crease
# handles direct the modeled rest cage. This does not assert a physical textile law.
anchor=np.full(len(U),.08);anchor+=45*crease;anchor+=8*chest;anchor+=18*smooth((az-.29)/.05)*cloth;anchor+=15*smooth((y-1.43)/.045)*cloth
A=L[free][:,free]+diags(anchor[free]);solve=factorized(A.tocsc());q=target.copy();q[~roi]=U[~roi];rotation=np.repeat(np.eye(3)[None],len(U),axis=0)
sourceEdge=U[e[:,0]]-U[e[:,1]]
for iteration in range(24):
 posedEdge=q[e[:,0]]-q[e[:,1]];cov=np.zeros((len(U),3,3));out=posedEdge[:,:,None]*sourceEdge[:,None,:]
 np.add.at(cov,e[:,0],out);np.add.at(cov,e[:,1],out)
 aa,_,bb=np.linalg.svd(cov[active]);rr=aa@bb;bad=np.linalg.det(rr)<0;aa[bad,:,-1]*=-1;rotation[active]=aa@bb
 re=np.einsum('nij,nj->ni',(rotation[e[:,0]]+rotation[e[:,1]])*.5,sourceEdge);rhs=np.zeros_like(U);np.add.at(rhs,e[:,0],re);np.add.at(rhs,e[:,1],-re)
 b=rhs[free]+anchor[free,None]*target[free]-L[free][:,fixed]@q[fixed]
 q[free]=np.column_stack([solve(b[:,c])for c in range(3)])
# Rebuild tiny folded shoulder surfaces after modeling, with boundary fixed in new cage.
patches.clear();q=patch(q)
for name,points in [('shoulder-only',qpatch),('envelope-arap',q)]:
 out={f'p{i}':points[INV[OFF[i]:OFF[i+1]]].copy()for i in range(5)}
 np.savez(OUT/f'{name}.npz',**out,uniquePositions=points,sourceAlias=INV,sourceUnique=U,primitiveOffsets=OFF)
 disp=np.linalg.norm(points-U,axis=1);trisBefore=U[CT];trisAfter=points[CT];a=np.cross(trisBefore[:,1]-trisBefore[:,0],trisBefore[:,2]-trisBefore[:,0]);b=np.cross(trisAfter[:,1]-trisAfter[:,0],trisAfter[:,2]-trisAfter[:,0]);l0=np.linalg.norm(U[edges[:,0]]-U[edges[:,1]],axis=1);l1=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1);ar=np.linalg.norm(b,axis=1)/np.maximum(np.linalg.norm(a,axis=1),1e-15)
 metrics={'sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'method':name,'topologyUVMaterialsUnchanged':True,'primitiveCount':len(POS),'maxRestDisplacementM':float(disp.max()),'changedUniqueVertices':int((disp>1e-9).sum()),'headExact':all(np.array_equal(POS[i],out[f'p{i}'])for i in [3,4]),'handsExact':np.array_equal(POS[1],out['p1']),'aliasesExact':True,'clothEdgeRatioMax':float((l1/l0).max()),'clothEdgeRatioP99':float(np.quantile(l1/l0,.99)),'clothAreaRatioMin':float(ar.min()),'facesBelowQuarterSourceArea':int((ar<.25).sum()),'negativeSourceNormalDotFaces':int((np.einsum('ij,ij->i',a,b)<0).sum()),'patches':patches,'notes':'Normal-dot sign is source-frame orientation diagnostic, not inversion certification under changing curved silhouette. Rest ARAP cage is authoring, not runtime cloth or rejected garment01 solver. All exact aliases use one common coordinate.'}
 (OUT/f'{name}-provenance.json').write_text(json.dumps(metrics,indent=2));print(name,json.dumps({k:v for k,v in metrics.items()if k!='patches'}),flush=True)
