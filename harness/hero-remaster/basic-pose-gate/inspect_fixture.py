"""Validate authored control coverage and quantify motion; never accept appearance."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert not a.out.exists()
f=json.loads(a.fixture.read_text());P=np.asarray(f['referenceCentresWorld']);names=f['jointNames'];rows=[]
assert len(names)==19 and len(set(names))==19
for family in f['families']:
 samples=[s for s in f['frames']if s['family']==family];assert len(samples)==f['fps']*f['secondsPerFamily']+1
 D=np.asarray([s['deformationWorldColumnMajor']for s in samples]).reshape(-1,19,4,4).transpose(0,1,3,2)
 assert np.isfinite(D).all() and np.allclose(D[:, :, 3, :],[0,0,0,1])
 assert np.allclose(D[0],np.eye(4))and np.allclose(D[-1],np.eye(4))
 rot=D[:,:,:3,:3];assert np.allclose(np.swapaxes(rot,-1,-2)@rot,np.eye(3),atol=1e-8)
 Q=np.einsum('tnij,nj->tni',D,np.c_[P,np.ones(19)])[:,:,:3]
 limb_errors=[]
 for side in ['L','R']:
  for proximal,distal in [('upperArm','forearm'),('forearm','hand'),('thigh','shin'),('shin','foot')]:
   i,j=[names.index(n+'.'+side)for n in [proximal,distal]]
   error=np.max(abs(np.linalg.norm(Q[:,j]-Q[:,i],axis=-1)-np.linalg.norm(P[j]-P[i])))
   limb_errors.append(float(error));assert error<1e-8,'Control stretches a limb'
 relative=np.swapaxes(rot[:-1],-1,-2)@rot[1:]
 degrees=np.degrees(Rotation.from_matrix(relative.reshape(-1,3,3)).magnitude()).reshape(-1,19)
 rows.append({'family':family,'frames':len(samples),'maximumAdjacentBoneRotationDegrees':float(degrees.max()),'maximumAdjacentJointMotionM':float(np.linalg.norm(np.diff(Q,axis=0),axis=-1).max()),'maximumLimbLengthErrorM':max(limb_errors),'firstStepMaximumRotationDegrees':float(degrees[0].max()),'lastStepMaximumRotationDegrees':float(degrees[-1].max())})
result={'fixtureSHA256':hashlib.sha256(a.fixture.read_bytes()).hexdigest(),'families':rows,'checks':['19 unique declared bones','proper rigid matrices','exact neutral endpoints','fixed physical limb lengths'],'limits':['Adjacent frame numbers do not establish visually convincing transitions.','Bilateral fixtures only; unilateral and unseen halfsteps remain unmeasured.','No contact, collision, textures, rendering, anatomical or gameplay acceptance.']}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows))
