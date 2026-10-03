"""Frozen mesh data only; does not load or run old experiment/base modules."""
from motion import *
import hashlib
sys.path.insert(0,str(HERE.parents[2]/'scripts'))
from glb import GLB
G=GLB(HERE.parents[2]/'deliverables/C19.glb')
if hashlib.sha256(G.raw).hexdigest()!='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e':raise ValueError('C19 seam/ROI source changed')
expected=json.loads((HERE/'frozen-provenance.json').read_text())['frozenInputs']
for name,sha in expected.items():
 if hashlib.sha256((HERE/'input'/name).read_bytes()).hexdigest()!=sha:raise ValueError('Frozen input changed: '+name)
PR=[p for m in G.j['meshes']for p in m['primitives']]
# Exact C19 seam aliases and material ROI selector remain fixed across repairs.
POS=[G.array(pr['attributes']['POSITION']).astype(float)for pr in PR]
OFF=np.r_[0,np.cumsum([len(p)for p in POS])];U,INV=np.unique(np.concatenate(POS),axis=0,return_inverse=True)
def deform(pos,weights,D,closed=False):
 if closed:raise ValueError('Mechanical suite intentionally keeps all corrective morphs zero')
 return [np.einsum('vj,jab,vb->va',w,D[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False)for p,w in zip(pos,weights)]
