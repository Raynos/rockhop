"""Bounded source-construction diagonal alternatives for actual exported witness.
Two candidates only, frozen positions/UVs/materialseams. Test changedfaces against
alluppercloth including one-shared-vertex interior intersections (no adjacencyhide).
"""
from pathlib import Path
import sys,json,numpy as np,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;sd=np.load(OUT/'shape-retop-uvsafe.npz');pp=[sd[f'p{i}']for i in range(5)];tris=[sd[f'tr{i}']for i in range(5)];uv=G.array(PR[2]['attributes']['TEXCOORD_0']).astype(float);EPS=1e-9
exec('def crossing'+(ROOT/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
def normal_area(p,t):
 q=p[t];return np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
def uv_area(t):
 q=uv[t];a=q[:,1]-q[:,0];b=q[:,2]-q[:,0];return a[:,0]*b[:,1]-a[:,1]*b[:,0]
baseU=np.concatenate([POS[0],POS[2]]);_,aliases=np.unique(baseU,axis=0,return_inverse=True);paths=sorted((ROOT/'hoodie-repair02/qa-lane/runtime/v6/geometry-poses').glob('*.npz'));reports=[]
for label,fa,fb,new in [('flip78',78,79,np.array([[121,101,106],[101,121,108]])),('flip80',79,80,np.array([[108,107,121],[107,108,106]]))]:
 old=tris[2][[fa,fb]];oldUV=uv_area(old);newUV=uv_area(new);oldN=normal_area(pp[2],old);newN=normal_area(pp[2],new);normal=oldN.sum(0);signed=newN@normal;pro={'label':label,'changedFacesPrimitive2':[fa,fb],'oldTriangles':old.tolist(),'newTriangles':new.tolist(),'oldUVsignedAreas':oldUV.tolist(),'newUVsignedAreas':newUV.tolist(),'sameUVorientation':bool(np.all(oldUV*newUV>0)),'restNormalsForward':bool(np.all(signed>0)),'restAreaSumRatio':float(np.linalg.norm(newN,axis=1).sum()/np.linalg.norm(oldN,axis=1).sum())}
 nt=[t.copy()for t in tris];nt[2][[fa,fb]]=new;ct=np.concatenate([nt[0],nt[2]+len(POS[0])]);roi=((baseU[ct][:,:,1]>1.08)&(baseU[ct][:,:,1]<1.49)&(abs(baseU[ct][:,:,2])<.405)).all(1);allids=np.flatnonzero(roi);ctroi=ct[roi];change=np.array([len(nt[0])+fa,len(nt[0])+fb]);rows=[]
 for path in paths:
  data=np.load(path);p=np.concatenate([data['p0'],data['p2']]);T=p[ctroi];A=p[ct[change]];alo=A.min(1);ahi=A.max(1);blo=T.min(1);bhi=T.max(1);pairs=np.array([(j,k)for j in range(2)for k in np.flatnonzero(((blo<=ahi[j])&(bhi>=alo[j])).all(1))if allids[k]!=change[j]],int).reshape(-1,2)
  hit=crossing(A[pairs[:,0]],T[pairs[:,1]]);pairs=pairs[hit];actual=[]
  for j,k in pairs:
   # Exclude shared complete edge only: two triangle planes intersect only at that
   # edge unless coplanar, already outside this transverse predicate. Sharedsingle
   # vertex is NOT excluded; a diagonal flip cannot hide collisions this way.
   shared=np.intersect1d(aliases[ct[change[j]]],aliases[ctroi[k]])
   if len(shared)<2:actual.append([int(change[j]),int(allids[k])])
  if actual:rows.append({'file':path.name,'literalLocalCrossings':actual})
 pro['runtimeFramesTested']=len(paths);pro['runtimeFailFrames']=len(rows);pro['runtimeFailRows']=rows;reports.append(pro);np.savez(OUT/f'interpolation-topology-{label}.npz',**{f'p{i}':p for i,p in enumerate(pp)},**{f'tr{i}':t for i,t in enumerate(nt)},**{f'n{i}':sd[f'n{i}']for i in range(5)});print(json.dumps({k:v for k,v in pro.items()if k!='runtimeFailRows'}),flush=True)
(OUT/'interpolation-retop-probes.json').write_text(json.dumps({'sourceShapeSHA256':hashlib.sha256((OUT/'shape-retop-uvsafe.npz').read_bytes()).hexdigest(),'runtimeEvidence':'frozen actualV6positions101frames; positions same under replacement topology, changedface localstrongstrictpredicate','reports':reports,'limits':'All unchanged oldfacepairs relyonindependent original101gate; noalltimeCCD or thickness certificate. Canonicalposes/holdoutsnewindicesneedparentqualification.'},indent=2))
