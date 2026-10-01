"""CPU-only localized DQ authoring hypothesis, never an engine skinning change."""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.spatial.transform import Rotation
np.seterr(all='raise')
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind16')
out=base/'baseline-cpu-affine02'; target=base/'localized-dq-cpu'; target.mkdir(parents=True,exist_ok=True)
m=json.loads((out/'pose-manifest.json').read_text())
def read(rec,n):
    path=out/rec['file']
    if not path.exists(): path=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind16')/out.name/rec['file']
    raw=path.read_bytes(); assert hashlib.sha256(raw).hexdigest()==rec['sha256']
    return np.frombuffer(raw,dtype='<f8').reshape(-1,n).copy()
def save(name,a):
    raw=np.asarray(a,dtype='<f8').tobytes();(target/(name+'.f64')).write_bytes(raw)
    return {'file':name+'.f64','values':len(raw)//8,'sha256':hashlib.sha256(raw).hexdigest()}
def multiply(a,b):
    av,aw=a[...,:3],a[...,3:]; bv,bw=b[...,:3],b[...,3:]
    return np.concatenate((aw*bv+bw*av+np.cross(av,bv),aw*bw-np.sum(av*bv,axis=-1,keepdims=True)),axis=-1)
def rotate(q,p):
    t=2*np.cross(q[...,:3],p)
    return p+q[...,3:]*t+np.cross(q[...,:3],t)
def smooth(lo,hi,v):
    t=np.clip((v-lo)/(hi-lo),0,1);return t*t*(3-2*t)
p=m['primitives'][0];a=p['attributes'];rest=read(a['position'],3);normal=read(a['normal'],3)
si=read(a['skinIndex'],4).astype(int);sw=read(a['skinWeight'],4);bones=p['bones'];legids=[bones.index(b) for b in ['pelvis','thighL','thighR']]
leg=np.sum(sw*np.isin(si,legids),axis=1);nativeY=rest[:,1]/1.015
alpha=smooth(.70,.78,nativeY)*(1-smooth(.94,1.00,nativeY))*smooth(.5,.75,leg)
assert alpha.max()==1 and np.count_nonzero(alpha)>0
# Exact exporter aliases get identical spatial/support masks, never seam splits.
_,inverse=np.unique(rest,axis=0,return_inverse=True)
for group in np.unique(inverse[alpha>0]):
    ids=np.flatnonzero(inverse==group); assert np.ptp(alpha[ids])<1e-12
rows=[]
for row in m['rows']:
    d=row['dump'][0]; mats=read(d['jointTransforms'],16).reshape(-1,4,4).transpose(0,2,1)
    U,s,Vh=np.linalg.svd(mats[:,:3,:3]);R=U@Vh
    assert np.linalg.det(R).min()>.999999 and np.max(np.abs(s-1))<1e-5
    qr=Rotation.from_matrix(R).as_quat();translation=mats[:,:3,3]
    qd=.5*multiply(np.concatenate((translation,np.zeros((19,1))),axis=1),qr)
    # Independent single-bone sanity: DQ translation/rotation must equal the rigid affine map.
    qc=qr.copy();qc[:,:3]*=-1
    decodedTranslation=2*multiply(qd,qc)[:,:3]
    assert np.max(np.abs(decodedTranslation-translation))<1e-12
    assert np.max(np.abs(rotate(qr,rest[:19])-np.einsum('jkl,jl->jk',R,rest[:19])))<1e-12
    # Polar rigidization is diagnostic-only, measure its loss against exact transforms.
    exactJoint=np.einsum('jkl,vl->jvk',mats[:,:3,:3],rest)+translation[:,None,:]
    rigidJoint=np.einsum('jkl,vl->jvk',R,rest)+translation[:,None,:]
    rigidError=float(np.max(np.linalg.norm(exactJoint-rigidJoint,axis=-1)))
    ref=qr[si[np.arange(len(si)),np.argmax(sw,axis=1)]]
    signs=np.where(np.sum(qr[si]*ref[:,None,:],axis=2)<0,-1.,1.)
    blendR=np.sum(qr[si]*(sw*signs)[...,None],axis=1)
    blendD=np.sum(qd[si]*(sw*signs)[...,None],axis=1)
    length=np.linalg.norm(blendR,axis=1,keepdims=True);assert length.min()>.5
    blendR/=length;blendD/=length
    blendD-=blendR*np.sum(blendR*blendD,axis=1,keepdims=True)
    conj=blendR.copy();conj[:,:3]*=-1
    shift=2*multiply(blendD,conj)[:,:3]
    dq=rotate(blendR,rest)+shift
    lbs=read(d['positions'],3);nLBS=read(d['gpuRuleSkinnedNormals'],3)
    # Verify exact recorded matrices reconstruct old skin before a new method.
    F=read(d['skinMatrices'],16).reshape(-1,4,4).transpose(0,2,1)
    reconstructed=np.einsum('vkl,vl->vk',F[:,:3,:3],rest)+F[:,:3,3]
    reconstructionError=float(np.max(np.linalg.norm(reconstructed-lbs,axis=1)))
    assert np.max(np.linalg.norm(reconstructed-lbs,axis=1))<1e-12
    candidate=lbs+alpha[:,None]*(dq-lbs)
    normals=nLBS+alpha[:,None]*(rotate(blendR,normal)-nLBS)
    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-30)
    assert np.array_equal(candidate[alpha==0],lbs[alpha==0])
    dump=dict(d);dump['positions']=save(f"sample{row['i']}-mesh0-positions",candidate);dump['gpuRuleSkinnedNormals']=save(f"sample{row['i']}-mesh0-normals",normals)
    nextRow=dict(row);nextRow['dump']=[dump,*row['dump'][1:]];rows.append(nextRow)
    save(f"sample{row['i']}-mesh0-dq-reference",dq)
    metadata={'sample':row['i'],'baselineAffineReconstructionErrorM':reconstructionError,'jointSingularValueRange':[float(s.min()),float(s.max())],'maximumRigidizationPositionErrorM':rigidError,'quaternionBlendMinimumNorm':float(length.min()),'maximumLocalizedDisplacementM':float(np.linalg.norm(candidate-lbs,axis=1).max()),'untouchedOutsideMaskExact':True,'actualBoneMatricesUnchanged':True}
    (target/f"sample{row['i']}-trial.json").write_text(json.dumps(metadata,indent=2)+'\n')
# Analysis inputs shared exactly, copied and hash checked. No new GLB is authored.
archive=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind16')/out.name
for record in (out if any(out.glob('*.f64')) else archive).glob('*.f64'):
    dest=target/record.name
    if not dest.exists():dest.write_bytes(record.read_bytes())
nm=dict(m);nm['rows']=rows;nm['limits']='CPU hypothetical localized DQ target under actual recorded bones; no export, shader replacement or appearance claim. Small polar rigidization measured explicitly.'
(target/'pose-manifest.json').write_text(json.dumps(nm,indent=2)+'\n')
(target/'mask.json').write_text(json.dumps({'nativeHeightBounds':[.70,1.00],'fullHeightBand':[.78,.94],'support':['pelvis','thighL','thighR'],'supportBlend':[.5,.75],'changedVertices':int((alpha>0).sum()),'fullyChangedVertices':int((alpha==1).sum()),'exporterAliasesIdenticalMask':True,'scope':'Localized CPU authoring hypothesis only; source11 rig/skin/material file untouched'},indent=2)+'\n')
print(json.dumps({'localVertices':int((alpha>0).sum()),'samples':len(rows),'exported':False}))
