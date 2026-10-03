"""Read-only body-bind34 actual runtime deformation bridge for fresh 19 joints.

Source34 denotes adapter version34, not 34 joints. Matrices are already in
bike-frame world space with source mesh bind prefixes included. No local
quaternion transfer or source11 matrix substitution occurs.
"""
from motion import *
import hashlib
DEFAULT_MANIFEST=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json')
DEFAULT_RAW=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu')
def canonical(name):
 name=name.removeprefix('fresh.')
 if name.endswith(('L','R'))and not name.endswith(('.L','.R')):name=name[:-1]+'.'+name[-1]
 return name

def read_f64(spec,rawdir):
 raw=(Path(rawdir)/spec['file']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('Recorded payload hash differs: '+spec['file'])
 x=np.frombuffer(raw,dtype='<f8')
 if len(x)!=spec['values']:raise ValueError('Recorded payload length differs')
 return x

def source34_world_matrices(sample,manifest=DEFAULT_MANIFEST,rawdir=DEFAULT_RAW,primitive=0):
 doc=json.loads(Path(manifest).read_text());pr=doc['primitives'][primitive]
 names=[canonical(n)for n in pr['bones']]
 if names!=NAMES:raise ValueError('Explicit source34 joint contract differs')
 origins=np.asarray([x['sourceWorld']for x in pr['inverseBindOriginPositions']])
 if np.max(np.linalg.norm(origins-P,axis=1))>1e-6:raise ValueError('Source34 bind centres differ; requires explicit retarget, not direct matrix copy')
 row=next(r for r in doc['rows']if r['i']==sample)
 D=read_f64(row['dump'][primitive]['jointTransforms'],rawdir).reshape(N,4,4).transpose(0,2,1).copy()
 if not np.isfinite(D).all()or not np.allclose(D[:,3,:],[0,0,0,1],atol=1e-9):raise ValueError('Nonfinite/nonaffine source matrix')
 return D,{'sourceManifestSHA256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),'sourceGLBSHA256':doc['sourceSHA256'],'sample':sample,'tick':row['tick'],'primitive':primitive,'jointOrder':NAMES,'space':'source34 bike-frame world deformation','sourceDebug':row['debug'],'sourceContacts':row['contacts']}

def rigid_arm_control(source):
 """Same actual roots and hand endpoints/orientations; rigid 2-link arm IK.

 Forearm transverse plane follows actual source elbow pole. Hand source linear
 transform stays exact. Torso/head/legs/shoulders stay source-exact. No new
 weights or inferred scapula. Unreachable targets are reported, never stretched.
 """
 D=np.asarray(source,dtype=float).copy();Q=centres(D);records=[]
 for side,a in [('L',6),('R',10)]:
  b,c=a+1,a+2;root,target=Q[a],Q[c];l1=np.linalg.norm(P[b]-P[a]);l2=np.linalg.norm(P[c]-P[b])
  dist=np.linalg.norm(target-root);reach=np.clip(dist,abs(l1-l2)+1e-10,l1+l2-1e-10);hit=root+unit(target-root)*reach
  ray=unit(hit-root);pole=Q[b]-root-ray*np.dot(Q[b]-root,ray)
  if np.linalg.norm(pole)<1e-7:pole=np.array([-1.,0,0])-ray*(-ray[0])
  mid=ik(root,hit,l1,l2,pole);normal=unit(np.cross(mid-root,hit-mid));rn=unit(np.cross(P[b]-P[a],P[c]-P[b]))
  ua=mul(frame(mid-root,normal),frame(P[b]-P[a],rn).T);fa=mul(frame(hit-mid,normal),frame(P[c]-P[b],rn).T)
  oldnormal=unit(np.cross(Q[b]-Q[a],Q[c]-Q[b]));oldframe=mul(frame(Q[c]-Q[b],oldnormal),frame(P[c]-P[b],rn).T)
  u,_,vt=np.linalg.svd(source[b,:3,:3]);oldrot=mul(u,vt)
  fa=mul(fa,mul(oldframe.T,oldrot))
  for j,q,r in [(a,root,ua),(b,mid,fa)]:D[j,:3,:3]=r;D[j,:3,3]=q-apply(r,P[j])
  D[c,:3,3]=hit-apply(D[c,:3,:3],P[c])
  records.append({'side':side,'handTargetErrorM':float(np.linalg.norm(hit-target)),'handLinearTransformExact':bool(np.array_equal(source[c,:3,:3],D[c,:3,:3])),'elbowSourceToRigidDisplacementM':float(np.linalg.norm(mid-Q[b])),'sourceUpperLengthM':float(np.linalg.norm(Q[b]-Q[a])),'sourceForearmLengthM':float(np.linalg.norm(Q[c]-Q[b])),'rigidUpperLengthM':float(np.linalg.norm(mid-root)),'rigidForearmLengthM':float(np.linalg.norm(hit-mid)),'sourceUpperScaleSingularValues':np.linalg.svd(source[a,:3,:3],compute_uv=False).tolist(),'sourceForearmScaleSingularValues':np.linalg.svd(source[b,:3,:3],compute_uv=False).tolist(),'elbowPoleWorld':unit(pole).tolist(),'forearmAxisWorld':unit(hit-mid).tolist(),'elbowHingeWorld':normal.tolist()})
 return D,records


def load_frozen_source34(sample):
 """Load portable exact source controls without the private runtime dump."""
 f=np.load(HERE/'source34-controls.npz');D=f[f'D{int(sample)}'].copy()
 rows=json.loads((HERE/'source34-manifest.json').read_text())['rows'];row=next(r for r in rows if r['sample']==sample and r['variant']=='source')
 if hashlib.sha256(D.tobytes()).hexdigest()!=row['worldMatricesSHA256']:raise ValueError('Frozen source34 D changed')
 return D,row

def skin_future_geometry(positions,weights,D,bind_centres):
 """Matrix LBS in documented bike-frame space for the SAME fresh19 bind.

 Each primitive's positions may differ; its vertex weights/order must match.
 This neither conditions weights nor calibrates a different rig's bind.
 """
 if np.asarray(bind_centres).shape!=P.shape or np.max(np.linalg.norm(np.asarray(bind_centres)-P,axis=1))>1e-6:raise ValueError('Future rig centres differ; explicit retarget required')
 result=[]
 for p,w in zip(positions,weights,strict=True):
  p=np.asarray(p);w=np.asarray(w)
  if w.shape!=(len(p),N)or not np.isfinite(p).all()or not np.isfinite(w).all():raise ValueError('Geometry/weights contract differs')
  result.append(np.einsum('vj,jab,vb->va',w,D[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False))
 return result
