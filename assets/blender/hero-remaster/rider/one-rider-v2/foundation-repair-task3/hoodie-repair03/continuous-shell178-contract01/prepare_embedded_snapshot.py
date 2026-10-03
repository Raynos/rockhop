"""Shade a supplied source-embedded pose without altering literal triangles.
Apply the incremental physical-edge polar rotation relative to the matched
source LBS control to its authored shader normals. Not collision repair.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sys.dont_write_bytecode=True
source,raw,output=map(Path,sys.argv[1:4]);assert not output.exists()
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
z=dict(np.load(source));pose=dict(np.load(raw));D=np.load(R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz')['D'][304]
P=[z[f'p{i}'] for i in range(5)]
B=[np.einsum('vj,jab,vb->va',z[f'W{i}'],D[:,:3,:],np.c_[P[i],np.ones(len(P[i]))],optimize=False) for i in range(5)]
Q=[pose[f'p{i}'].copy() for i in range(5)]
N=[np.einsum('vj,jab,vb->va',z[f'W{i}'],D[:,:3,:3],z[f'n{i}'],optimize=False) for i in range(5)]
for i in range(5):N[i]/=np.maximum(np.linalg.norm(N[i],axis=1,keepdims=True),1e-20)
offset=len(P[0]);aliases=np.r_[z['physicalWeld0'],z['physicalWeld2']];_,rep,group=np.unique(aliases,return_index=True,return_inverse=True)
tr=np.r_[z['tr0'],z['tr2']+offset]
edges=np.unique(np.sort(np.r_[group[tr[:,[0,1]]],group[tr[:,[1,2]]],group[tr[:,[2,0]]]],axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
rest=np.r_[P[0],P[2]][rep];e=rest[edges[:,1]]-rest[edges[:,0]];weight=1/np.maximum(np.linalg.norm(e,axis=1),.002)**2
def rotation(positions):
 p=positions[rep];f=p[edges[:,1]]-p[edges[:,0]];dyad=np.einsum('ni,nj->nij',f,e)*weight[:,None,None];cov=np.zeros((len(rep),3,3));np.add.at(cov,edges[:,0],dyad);np.add.at(cov,edges[:,1],dyad)
 u,sv,vh=np.linalg.svd(cov);fix=np.broadcast_to(np.eye(3),cov.shape).copy();fix[:,2,2]=np.linalg.det(u@vh);return u@fix@vh,sv
base=np.r_[B[0],B[2]];posed=np.r_[Q[0],Q[2]];rb,_=rotation(base);rq,sv=rotation(posed);delta=rq@rb.transpose(0,2,1)
changed=np.linalg.norm(posed-base,axis=1)>1e-12;normals=np.r_[N[0],N[2]];normals[changed]=np.einsum('nij,nj->ni',delta[group[changed]],normals[changed]);N[0],N[2]=normals[:offset],normals[offset:]
Q[1]=np.load(R/'hoodie-repair03/poses/game304-v7-plain.npz')['p1']
assert all(np.isfinite(x).all() for x in Q+N)
np.savez_compressed(output,**{f'p{i}':Q[i] for i in range(5)},**{f'n{i}':N[i] for i in range(5)})
proof={'status':'UNACCEPTED literal source embedding snapshot','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'rawPoseSHA256':hashlib.sha256(raw.read_bytes()).hexdigest(),'snapshotSHA256':hashlib.sha256(output.read_bytes()).hexdigest(),'changedClothVertices':int(changed.sum()),'normalRule':'Incremental proper physical-edge polar rotation relative to exact matched source LBS applied to source weighted shader N; original hard-normal differences retained. Shader-only diagnostic; cannot fix triangle crossings.','heldGloves':'Original recorded closed p1','limits':'Single304 offline static snapshot, no stock skinning/postbone runtime/performance/continuous/contact certificate.'}
output.with_suffix('.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
