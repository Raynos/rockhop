"""Read-only true dual-quaternion runtime-law probe over measured fresh34matrices."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');out=base/'body-bind35';out.mkdir(exist_ok=True)
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');m=json.loads((base/'body-bind34/candidate-cpu/pose-manifest.json').read_text());prim=m['primitives'][0]
def read(rec,lanes):
 raw=(private/'body-bind34/candidate-cpu'/rec['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,lanes).copy()
def multiply(a,b):return np.concatenate((a[...,3,None]*b[...,:3]+b[...,3,None]*a[...,:3]+np.cross(a[...,:3],b[...,:3]),(a[...,3]*b[...,3]-np.sum(a[...,:3]*b[...,:3],axis=-1))[...,None]),axis=-1)
def conjugate(q):return q*np.array([-1,-1,-1,1])
def rotate(q,p):return p+2*np.cross(q[...,:3],np.cross(q[...,:3],p)+q[...,3,None]*p)
def deform(matrices,indices,weights,points,normals):
 R=matrices[:,:3,:3];err=np.max(abs(np.einsum('bji,bjk->bik',R,R)-np.eye(3)));det=np.linalg.det(R)
 assert err<1e-5 and np.max(abs(det-1))<1e-5,'Rigid-bone precondition failed; no silent scale removal'
 real=Rotation.from_matrix(R).as_quat();t=np.c_[matrices[:,:3,3],np.zeros(len(matrices))];dual=.5*multiply(t,real)
 q=real[indices];d=dual[indices];reference=q[np.arange(len(indices)),np.argmax(weights,axis=1)]
 sign=np.where(np.einsum('vli,vi->vl',q,reference)<0,-1.,1.);weighted=weights*sign
 qr=np.sum(q*weighted[:,:,None],axis=1);qd=np.sum(d*weighted[:,:,None],axis=1);length=np.linalg.norm(qr,axis=1);assert np.min(length)>.1
 qr/=length[:,None];qd/=length[:,None];qd-=qr*np.sum(qr*qd,axis=1)[:,None]
 translation=2*multiply(qd,conjugate(qr))[:,:3]
 return rotate(qr,points)+translation,rotate(qr,normals),float(err),float(np.min(length))
rest=read(prim['attributes']['position'],3);normal=read(prim['attributes']['normal'],3);indices=read(prim['attributes']['skinIndex'],4).astype(int);weights=read(prim['attributes']['skinWeight'],4);tri=read(prim['index'],3).astype(int)
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
sourceQ=rest[tri];sourceCross=np.cross(sourceQ[:,1]-sourceQ[:,0],sourceQ[:,2]-sourceQ[:,0]);sourceDot=np.einsum('ti,ti->t',unit(sourceCross),unit(normal[tri].mean(1)));sourceEdge=np.linalg.norm(sourceQ-np.roll(sourceQ,-1,axis=1),axis=2)
arm=(sourceQ[:,:,1].mean(1)>.95)&(np.abs(sourceQ[:,:,2]).mean(1)>.13);hip=(sourceQ[:,:,1].mean(1)>.70)&(sourceQ[:,:,1].mean(1)<1.06)&(np.abs(sourceQ[:,:,2]).mean(1)<.24)
rows=[];samples={}
for row in m['rows']:
 matrices=read(row['dump'][0]['jointTransforms'],16).reshape(-1,4,4).transpose(0,2,1)
 P,N,rigidError,minReal=deform(matrices,indices,weights,rest,normal)
 oldP=read(row['dump'][0]['positions'],3);oldN=read(row['dump'][0]['gpuRuleSkinnedNormals'],3)
 single=(np.count_nonzero(weights>0,axis=1)==1);slot=np.argmax(weights[single],axis=1);bone=indices[single,slot];expected=np.einsum('vij,vj->vi',matrices[bone,:3,:3],rest[single])+matrices[bone,:3,3]
 singleError=float(np.max(np.linalg.norm(P[single]-expected,axis=1)));assert singleError<1e-5
 testP,testN,_,_=deform(matrices,indices,weights,rest,normal) # Deterministic repeated arithmetic, not sign-invariance proof.
 assert np.array_equal(testP,P) and np.array_equal(testN,N)
 r={'sample':row['i'],'rigidMatrixError':rigidError,'minimumBlendRealNorm':minReal,'singleBoneCount':int(single.sum()),'singleBoneParityErrorM':singleError,'maximumPositionDifferenceM':float(np.linalg.norm(P-oldP,axis=1).max()),'scopes':{}}
 for name,roi in [('armGeometry',arm),('hipGeometry',hip)]:
  values={}
  for label,points,normals in [('fresh34LBS',oldP,oldN),('DQProbe',P,N)]:
   Q=points[tri];cross=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);dots=np.einsum('ti,ti->t',unit(cross),unit(normals[tri].mean(1)));stretch=(np.linalg.norm(Q-np.roll(Q,-1,axis=1),axis=2)/np.maximum(sourceEdge,1e-30)).max(1)
   values[label]={'normalOppositionFlags':int((roi&(sourceDot>.2)&(dots<-.2)).sum()),'maximumEdgeStretch':float(stretch[roi].max()),'edgeStretchP90P99':np.quantile(stretch[roi],[.9,.99]).tolist(),'elbow3789':{'normalDot':float(dots[3789]),'maximumEdgeStretch':float(stretch[3789])}}
  r['scopes'][name]=values
 rows.append(r);samples[str(row['i'])+'Positions']=P;samples[str(row['i'])+'Normals']=N
run=private/'body-bind35';run.mkdir(exist_ok=True);np.savez_compressed(run/'dq-probe.npz',**samples)
report={'status':'Read-only CPU actual skin-law feasibility, no shader/asset export','sourceSHA256':m['sourceSHA256'],'fieldSHA256':hashlib.sha256((run/'dq-probe.npz').read_bytes()).hexdigest(),'law':'Rigid joint matrices to dual quaternions; highest-weight reference hemisphere, normalized dual blend with orthogonality projection; rotation plus translation for position, quaternion rotation for normal. No bone/pose/geometry/weight changes.','sources':['https://users.cs.utah.edu/~ladislav/dq/index.html','https://users.cs.utah.edu/~ladislav/kavan07skinning/kavan07skinning.pdf'],'rows':rows,'limits':['Whole shader/CPU contact/normal/morph/shadow/depth parity and all480frame continuity unproven.','Input jointTransforms already include original bind/mesh/bike-frame affines; actual shader must preserve those spaces correctly.','No Blender DQexport claim; this probe changes the evaluated skin law itself.','Normal opposition is diagnostic, not intersection or visual acceptance; DQcan bulge and cannot repair poor garment topology.']}
(out/'dq-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
