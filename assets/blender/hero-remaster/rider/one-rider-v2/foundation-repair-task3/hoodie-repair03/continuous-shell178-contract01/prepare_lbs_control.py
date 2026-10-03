"""Freeze an exact recorded source-only LBS ablation, with held recorded gloves."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sys.dont_write_bytecode=True
source,output=map(Path,sys.argv[1:3]);assert not output.exists()
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');control=R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz';D=np.load(control)['D'][304];z=dict(np.load(source));q={}
for i in range(5):
 p=z[f'p{i}'];w=z[f'W{i}'];q[f'p{i}']=np.einsum('vj,jab,vb->va',w,D[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False);n=np.einsum('vj,jab,vb->va',w,D[:,:3,:3],z[f'n{i}'],optimize=False);q[f'n{i}']=n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-20)
q['p1']=np.load(R/'hoodie-repair03/poses/game304-v7-plain.npz')['p1'];np.savez_compressed(output,**q);output.with_suffix('.json').write_text(json.dumps({'status':'Exact source-only LBS matched control; no acceptance','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'controlsSHA256':hashlib.sha256(control.read_bytes()).hexdigest(),'poseSHA256':hashlib.sha256(output.read_bytes()).hexdigest(),'state':304,'closedHands':'Held original recorded p1'},indent=2)+'\n')
