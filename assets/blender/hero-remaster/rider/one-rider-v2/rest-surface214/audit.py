"""Read-only full-surface CPU BVH audit, retaining adjacent and unresolved pairs."""
from pathlib import Path
import sys,time,json,hashlib,ast,struct
import numpy as np
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/rest-surface214';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');D=B/'rest-surface214';D.mkdir(exist_ok=True)
src=B/'finite-cleanup210/clean-native.glb';expected='2ff3cfb0dd9ddff6b6cbb6695f2426961296409ececd730e123ef39babbd6b74';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)==expected
tree=ast.parse((R/'assets/blender/hero-remaster/rider/one-rider-v2/finite-cleanup210/clean.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='glb_read'],type_ignores=[]),'<readonly_glb>','exec'),globals());j,v,f=glb_read(src);v=v.astype(float);start=time.monotonic()
def strict(A,B):
 hit=np.zeros(len(A),bool)
 for aa,bb in ((A,B),(B,A)):
  e1=bb[:,1]-bb[:,0];e2=bb[:,2]-bb[:,0]
  for k in range(3):
   d=aa[:,(k+1)%3]-aa[:,k];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);scale=np.linalg.norm(e1,axis=1)*np.linalg.norm(e2,axis=1)*np.linalg.norm(d,axis=1);valid=abs(det)>scale*1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);s=aa[:,k]-bb[:,0];u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);z=np.einsum('ij,ij->i',d,q)*inv;t=np.einsum('ij,ij->i',e2,q)*inv
   hit|=valid&(u>1e-9)&(z>1e-9)&(u+z<1-1e-9)&(t>1e-9)&(t<1-1e-9)
 return hit
A=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]]);C=np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0.]]]);assert strict(A,C)[0] and not strict(A,C+np.array([2,0,0]))[0]
for scale in [1e-8,1.,1e8]:assert strict(A*scale,C*scale)[0]
bvh=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True,epsilon=0);pairs=np.array(sorted({tuple(sorted(x)) for x in bvh.overlap(bvh) if x[0]!=x[1]}),dtype=np.int64).reshape(-1,2);del bvh
hits=[];cop=[];counts={0:0,1:0,2:0,3:0}
for begin in range(0,len(pairs),8192):
 q=pairs[begin:begin+8192];a=v[f[q[:,0]]];b=v[f[q[:,1]]];hit=strict(a,b);hits.extend(q[hit].tolist())
 n=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);n2=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]);un=n/np.linalg.norm(n,axis=1)[:,None];un2=n2/np.linalg.norm(n2,axis=1)[:,None];near=(np.linalg.norm(np.cross(un,un2),axis=1)<1e-10)&(abs(np.einsum('ij,ij->i',b[:,0]-a[:,0],un))<1e-12);cop.extend(q[near].tolist())
 for i,j in q[hit]:counts[len(set(f[i])&set(f[j]))]+=1
hits=np.array(hits,dtype=np.int64).reshape(-1,2);cop=np.array(cop,dtype=np.int64).reshape(-1,2);assert not (D/'pairs.npz').exists();np.savez_compressed(D/'pairs.npz',strictPairs=hits,coplanarUnclassifiedPairs=cop)
report={'status':'FULL_FINITE_REST_TRANSVERSE_AUDIT_NO_ANATOMY_ACCEPTANCE','source':str(src),'sourceSHA256':expected,'vertices':len(v),'faces':len(f),'bvhCandidatePairs':len(pairs),'strictTransversePairs':len(hits),'strictPairsBySharedPhysicalVertices':counts,'strictFirst20':hits[:20].tolist(),'coplanarUnclassifiedPairs':len(cop),'coplanarFirst20':cop[:20].tolist(),'pairOutput':str(D/'pairs.npz'),'pairOutputSHA256':sha(D/'pairs.npz'),'seconds':time.monotonic()-start,'method':'CPU Blender BVHTree broadphase, float64 six-edge strict interior Moller-Trumbore, determinant threshold relative to edge magnitudes; no adjacent-pair exclusions','controls':'Crossing/separated fixtures plus scale invariance 1e-8/1/1e8','limits':['Coplanar positive-area overlap remains UNCLASSIFIED, not cleared','Endpoint/tangent-only contact excluded; no thickness/depth/art/rig/motion pass','Finite diagnostic subset of invalid native generation; no native completion proof','Raw rest coordinates retained; no repair, sampling or GPU']};assert sha(src)==expected;(E/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
