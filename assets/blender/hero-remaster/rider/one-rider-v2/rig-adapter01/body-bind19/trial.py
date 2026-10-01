"""One constrained local ARAP target from actual poses; no asset export/GPU."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import splu
np.seterr(all='raise')
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind19');out=base/'arap-cpu';out.mkdir(parents=True,exist_ok=True)
source=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind16/baseline-cpu-affine02');private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind16/baseline-cpu-affine02')
m=json.loads((source/'pose-manifest.json').read_text())
def read(rec,n):
 p=source/rec['file'];p=p if p.exists() else private/rec['file'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,n).copy()
def save(name,a):
 raw=np.asarray(a,dtype='<f8').tobytes();(out/(name+'.f64')).write_bytes(raw);return {'file':name+'.f64','values':len(raw)//8,'sha256':hashlib.sha256(raw).hexdigest()}
p=m['primitives'][0];a=p['attributes'];rest=read(a['position'],3);normal=read(a['normal'],3);tri=read(p['index'],3).astype(int);si=read(a['skinIndex'],4).astype(int);sw=read(a['skinWeight'],4);bones=p['bones']
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);ut=inv[tri]
leg=(sw*np.isin(si,[bones.index(b) for b in ['pelvis','thighL','thighR']])).sum(1)
assert np.max(np.abs(leg-leg[first][inv]))<1e-7
# Only original pants/pelvis with nearly pure leg support, not hoodie or sleeves.
active=(u[:,1]>.72)&(u[:,1]<.959175)&(np.abs(u[:,2])<.235)&(leg[first]>.99999)
edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
length=np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1);ew=1/np.maximum(length,1e-6)
adj=coo_matrix((np.r_[ew,ew],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr();degree=np.asarray(adj.sum(1)).ravel();L=diags(degree)-adj
boundary=np.asarray(adj@(~active).astype(float)).ravel()>0;free=active&(~boundary);f=np.flatnonzero(free);k=np.flatnonzero(~free)
assert len(f)>0
# Soft proximity keeps observed pose, hard graph boundary stays exact. Stronger
# source top/bottom proximity avoids a sudden change at bind/support transitions.
t=np.clip((u[:,1]-.72)/(.959175-.72),0,1);blend=np.sin(np.pi*t)**2
penalty=degree*(.005+.08*(1-blend)**2)
A=(L[f][:,f]+diags(penalty[f])).tocsc();solve=splu(A).solve
localEdges=edges[np.any(free[edges],axis=1)];weights=ew[np.any(free[edges],axis=1)];i,j=localEdges.T;re=u[i]-u[j]
# Exact actual authored seat top triangles copied from the preceding audit.
prior=json.loads((source/'report.json').read_text());bt=read(m['bodyworkSource']['triangles'],3).astype(int);seatIds=np.asarray(prior['contours'][0]['seatTriangleIds'],dtype=int)
rows=[]
for row in m['rows']:
 d=row['dump'][0];lbs=read(d['positions'],3);P=lbs[first].copy();assert np.max(np.linalg.norm(lbs-P[inv],axis=1))<1e-7
 target=P.copy();seat=read(row['bodyworkBikeFrame'],3)[bt[seatIds]]
 # Precompute horizontal barycentric coefficients for actual exported seat.
 e1=seat[:,1,[0,2]]-seat[:,0,[0,2]];e2=seat[:,2,[0,2]]-seat[:,0,[0,2]]
 det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];valid=np.abs(det)>1e-12
 S=seat[valid];e1=e1[valid];e2=e2[valid];det=det[valid]
 changes=[]
 for iteration in range(15):
  pe=P[i]-P[j]
  cov=np.zeros((len(u),3,3));outer=weights[:,None,None]*pe[:,:,None]*re[:,None,:]
  np.add.at(cov,i,outer);np.add.at(cov,j,outer)
  U,_,Vh=np.linalg.svd(cov);sign=np.linalg.det(U@Vh);U[:,:,2]*=np.where(sign<0,-1.,1.)[:,None];R=U@Vh
  b=np.zeros_like(P);term=.5*weights[:,None]*np.einsum('ekl,el->ek',R[i]+R[j],re);np.add.at(b,i,term);np.add.at(b,j,-term)
  # Boundary right-hand terms only require edges touching free region.
  rhs=b[f]-L[f][:,k]@target[k]+penalty[f,None]*target[f]
  q=P.copy();q[f]=solve(rhs)
  # Seat-contact projection constrains just penetrating local vertices. It is
  # an authoring constraint, not a collision proof or skeleton correction.
  dx=q[f,None,0]-S[None,:,0,0];dz=q[f,None,2]-S[None,:,0,2]
  v=(dx*e2[None,:,1]-dz*e2[None,:,0])/det;w=(e1[None,:,0]*dz-e1[None,:,1]*dx)/det
  inside=(v>=-1e-6)&(w>=-1e-6)&(v+w<=1.000001)
  sy=S[None,:,0,1]+v*(S[None,:,1,1]-S[None,:,0,1])+w*(S[None,:,2,1]-S[None,:,0,1])
  bound=np.max(np.where(inside,sy+.001,-np.inf),axis=1)
  q[f,1]=np.maximum(q[f,1],bound)
  changes.append(float(np.linalg.norm(q-P,axis=1).max()));P=q
 assert np.array_equal(P[k],target[k]);candidate=lbs.copy();candidate[free[inv]]=P[inv[free[inv]]]
 assert np.array_equal(candidate[~free[inv]],lbs[~free[inv]])
 # Transport source normals with local ARAP rotations for diagnostic fold test.
 nLBS=read(d['gpuRuleSkinnedNormals'],3);normals=nLBS.copy();normals[free[inv]]=np.einsum('vkl,vl->vk',R[inv[free[inv]]],normal[free[inv]])
 normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-30)
 F=read(d['skinMatrices'],16).reshape(-1,4,4).transpose(0,2,1);smallest=np.linalg.svd(F[free[inv],:3,:3],compute_uv=False)[:,-1]
 assert smallest.min()>.1
 delta=np.zeros_like(rest);delta[free[inv]]=np.linalg.solve(F[free[inv],:3,:3],(candidate[free[inv]]-lbs[free[inv]])[:,:,None])[:,:,0]
 roundtrip=lbs+np.einsum('vkl,vl->vk',F[:,:3,:3],delta)
 assert np.max(np.linalg.norm(roundtrip-candidate,axis=1))<1e-12
 dump=dict(d);dump['positions']=save(f"sample{row['i']}-mesh0-positions",candidate);dump['gpuRuleSkinnedNormals']=save(f"sample{row['i']}-mesh0-normals",normals)
 nextrow=dict(row);nextrow['dump']=[dump,*row['dump'][1:]];rows.append(nextrow)
 save(f"sample{row['i']}-mesh0-corrective-delta",delta)
 (out/f"sample{row['i']}-trial.json").write_text(json.dumps({'sample':row['i'],'iterations':15,'iterationMaximumDisplacementM':changes,'minimumInverseSkinSingularValue':float(smallest.min()),'maximumPosedDisplacementM':float(np.linalg.norm(candidate-lbs,axis=1).max()),'maximumSourceCorrectiveDisplacementM':float(np.linalg.norm(delta,axis=1).max()),'outsideRegionExact':True,'boneTargetsUnchanged':True,'aliasesSameCorrective':True,'sourceRoundtripErrorM':float(np.linalg.norm(roundtrip-candidate,axis=1).max())},indent=2)+'\n')
for record in private.glob('*.f64'):
 dest=out/record.name
 if not dest.exists():dest.write_bytes(record.read_bytes())
nm=dict(m);nm['rows']=rows;nm['limits']='CPU local ARAP pose-corrective authoring only, hard graph boundaries and actual seat vertex projection. No exported GLB or engine driver.'
(out/'pose-manifest.json').write_text(json.dumps(nm,indent=2)+'\n')
(out/'settings.json').write_text(json.dumps({'method':'Local/global ARAP with exact position aliases','freePhysicalVertices':len(f),'iterations':15,'activeY':[.72,.959175],'absZBelow':.235,'legWeightAbove':.99999,'seatUpwardVertexClearanceM':.001,'hardBoundary':True,'softProximity':'.005+.08*(1-sin(pi*t)^2)^2 times graph degree','noParameterSweep':True,'exported':False},indent=2)+'\n')
print(json.dumps({'samples':len(rows),'freePhysicalVertices':len(f),'exported':False}))
