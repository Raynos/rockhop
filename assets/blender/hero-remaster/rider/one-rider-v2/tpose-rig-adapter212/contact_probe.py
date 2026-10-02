"""Literal NEW surface witnesses; declared palm approach remains unaccepted."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation
from trimesh.triangles import closest_point
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212'
z=np.load(B/'finite-cleanup210/ancestry.npz');M=np.array(json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/head-join211/join-contract.json').read_text())['explicitBodyTransform']['matrixNativeToCanonical']);P=z['positions'].astype(float)@M[:3,:3].T+M[:3,3];F=z['faces'][:,::-1];tri=P[F];C=tri.mean(1);N=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);N/=np.linalg.norm(N,axis=1)[:,None]
summary=json.loads((E/'section-summary.json').read_text())
def arm(h):
    s=next(s for s in summary if s['axis']==2 and s['planeCanonicalM']==h)
    return np.array(max((l for l in s['loops'] if l['areaCentroidCanonical'][1]>1.2),key=lambda l:l['areaM2'])['areaCentroidCanonical'])
def basis(long,normal):
    y=long/np.linalg.norm(long);zz=normal-y*np.dot(y,normal);zz/=np.linalg.norm(zz);return np.column_stack((np.cross(y,zz),y,zz))
results=[]
for sign in (1,-1):
    wrist=arm(sign*.50);long=arm(sign*.64)-arm(sign*.54)
    patch=np.flatnonzero((sign*C[:,2]>.54)&(sign*C[:,2]<.59)&(C[:,1]>1.33)&(C[:,1]<1.45)&(N[:,0]>.5))
    assert len(patch)>0
    desired=arm(sign*.56)+np.array([.045,0,0]);hits=closest_point(tri[patch],np.repeat(desired[None],len(patch),axis=0));i=np.argmin(np.linalg.norm(hits-desired,axis=1));fi=int(patch[i]);point=hits[i];normal=N[fi]
    A=basis(long,normal);T=basis(np.array([0.,-1.,0.]),np.array([1.,0.,0.]));delta=T@A.T
    # Surface witness hypothesised on rear cylinder wall; axis socket lies17mm ahead.
    radius=.017;targetSurfaceOffset=delta@(point-wrist);targetAxisOffset=targetSurfaceOffset+np.array([radius,0,0])
    results.append({'side':'L' if sign==1 else 'R','wristEstimate':wrist.tolist(),'sourcePalmTriangleRow':fi,'sourceNativeFaceID':int(z['sourceNativeFaceIDs'][fi]),'sourceFaceRows':F[fi].tolist(),'sourcePalmSurfacePoint':point.tolist(),'sourcePalmSurfaceNormal':normal.tolist(),'sourceFingerAxisMeasuredSectionDifference':long.tolist(),'sourceProperAnatomicalFrame':A.tolist(),'targetProperAnatomicalFrame':T.tolist(),'deltaWorldQuaternion':Rotation.from_matrix(delta).as_quat().tolist(),'targetWristToPalmSurfaceOffset':targetSurfaceOffset.tolist(),'targetWristToGripAxisOffset':targetAxisOffset.tolist(),'declaredGripRadiusM':radius,'maximumDeclaredFrameDeterminantError':float(max(abs(np.linalg.det(A)-1),abs(np.linalg.det(T)-1))),'limits':['Actual triangle point, not point floating in a hole. Wrist station is an authoring estimate.','Local front-facing palm triangle is a declared candidate contact, not anatomically segmented or validated grip.','Downward fingers/forward palm is a riding hypothesis; no finger wrap or cylinder collision pass.','The17mm support offset uses procedural bike grip maximum radius; authored bike GLB contact surface still requires matching.']})
(E/'contact-witnesses.json').write_text(json.dumps({'status':'READ_ONLY_NEW_SURFACE_WITNESSES_DECLARED_TARGET_ORIENTATION','hands':results},indent=2)+'\n');print(json.dumps(results,indent=2))
