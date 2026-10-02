"""Conservative float64 AABB strict interior crossings: new shell against all cloth."""
import numpy as np,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-guided-cage182');a=np.load(R/'bodydata01.npz');parts=[(a['newShellP'],a['newShellF'])]+[(a['p'+str(i)],a['f'+str(i)]) for i in [0,1,2]];pp=[];ff=[];off=0
for p,f in parts:pp.append(p);ff.append(f+off);off+=len(p)
p=np.concatenate(pp);f=np.concatenate(ff);u,inv=np.unique(p,axis=0,return_inverse=True);pf=inv[f];tri=p[f].astype(float);lo=tri.min(1);hi=tri.max(1);pair=[];classes=[]
for i in range(len(a['newShellF'])):
 js=np.where(np.all(hi[i]>=lo[i+1:]-1e-12,axis=1)&np.all(lo[i]<=hi[i+1:]+1e-12,axis=1))[0]+i+1
 for j in js:
  shared=len(set(pf[i])&set(pf[j]))
  if shared<2:pair.append((i,int(j)));classes.append(shared)
ids=np.array(pair,dtype=int);hit=np.zeros(len(ids),dtype=bool)
if len(ids):
 for reverse in [False,True]:
  A=tri[ids[:,int(reverse)]];B=tri[ids[:,int(not reverse)]];e1=B[:,1]-B[:,0];e2=B[:,2]-B[:,0]
  for k in range(3):
   d=A[:,(k+1)%3]-A[:,k];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);valid=abs(det)>1e-12;den=np.where(valid,det,1);s=A[:,k]-B[:,0];U=np.einsum('ij,ij->i',s,h)/den;q=np.cross(s,e1);V=np.einsum('ij,ij->i',d,q)/den;t=np.einsum('ij,ij->i',e2,q)/den
   hit |= valid&(U>1e-7)&(V>1e-7)&(U+V<1-1e-7)&(t>1e-7)&(t<1-1e-7)
classes=np.array(classes);witnesses=ids[hit].tolist();(R/'strict-crossing-witnesses-private.json').write_text(json.dumps(witnesses));report={'status':'PARTIAL_LITERAL_NEW_SHELL_VS_ALL_BODY_CLOTH_NO_ACCEPTANCE','bodydataSHA256':hashlib.sha256((R/'bodydata01.npz').read_bytes()).hexdigest(),'conservativeBroadphase':'All float64 triangle AABBs with1e-12margin; no selfBVH or toleranceweld','newShellTriangles':len(a['newShellF']),'allComparedTriangles':len(f),'zeroOneSharedCandidates':len(pair),'strictZeroShared':int((hit&(classes==0)).sum()),'strictOneShared':int((hit&(classes==1)).sum()),'limits':'New shell self + new shell vs retained lower/gloves/hood only. Source-source inheritedcrossings/head contacts notrerun; coplanar overlap/endpointtouches excluded. Wrongwinding/170degenerates already reject independentofstrictcounts.'};(E/'cross-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
