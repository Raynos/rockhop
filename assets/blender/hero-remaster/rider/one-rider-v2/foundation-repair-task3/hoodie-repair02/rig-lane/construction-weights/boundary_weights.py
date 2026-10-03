"""Localized sewn-fabric weights from explicit construction boundary topology.
No chart-ownership scalar is loaded. Geometry/topology remain shape-owned.
The first operation rejects a supplied nonclear rest gate: neutral crossings
cannot be repaired by skinning weights. All19 world bind bases stay fixed.
"""
from pathlib import Path
import numpy as np,json,hashlib
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components

def require_rest_gate(path):
 gate=json.loads(Path(path).read_text())
 # QA schemas retain explicit corner folds separately from nonadjacent pairs.
 keys=['restStrictNonadjacentCrossings','restStrictOneCornerCrossings']
 if not all(k in gate for k in keys):raise ValueError('Rest gate missing explicit nonadjacent/corner counts')
 if any(gate[k]>0 for k in keys):raise ValueError('Geometry fails neutral triangle gate; weights cannot qualify it')
 return gate

def harmonic_insert(pos,faces,body_loop,sleeve_loop,boundary_weights):
 """Solve fresh intrinsic ownership/bone weights only inside added fabric.

 Exact loops are provided by the actual topology author. The new patch's
 positive inverse-rest-edge Laplacian supplies a convex harmonic extension of
 boundary rows. It does not mix close spatial sheets or guess anatomy fromY.
 """
 p=np.asarray(pos);t=np.asarray(faces,dtype=int);body=np.asarray(body_loop,dtype=int);sleeve=np.asarray(sleeve_loop,dtype=int)
 if np.intersect1d(body,sleeve).size:raise ValueError('Construction loops overlap')
 domain=np.unique(t);boundary=np.r_[body,sleeve];free=np.setdiff1d(domain,boundary)
 if len(np.unique(boundary))!=len(boundary):raise ValueError('Construction loops repeat vertices')
 bw=np.asarray(boundary_weights)
 if bw.shape!=(len(p),19):raise ValueError('Expected one source19 weight row per construction vertex')
 if not np.isfinite(bw[boundary]).all() or (bw[boundary]<0).any():raise ValueError('Invalid boundary skin rows')
 if np.max(np.abs(bw[boundary].sum(1)-1))>1e-12:raise ValueError('Boundary rows must already be normalized')
 support=np.flatnonzero((bw[boundary]>0).any(0))
 if len(support)>4:raise ValueError('Boundary bone union exceeds four influences; explicit regional construction required')
 if not np.isin(boundary,domain).all():raise ValueError('Declared boundary absent from fabric topology')
 e=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0);length=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)
 if (length<1e-9).any():raise ValueError('Degenerate material edge requires shape correction')
 conductance=1/np.maximum(length,1e-6);g=coo_matrix((np.r_[conductance,conductance],(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(p),len(p))).tocsr();L=diags(np.asarray(g.sum(1)).ravel())-g
 _,component=connected_components(g[domain][:,domain],directed=False)
 if not np.isin(np.unique(component),component[np.searchsorted(domain,boundary)]).all():raise ValueError('Fabric component has no fixed sewn boundary')
 values=np.zeros((len(p),19));values[boundary]=bw[boundary]
 if len(free):values[free]=spsolve(L[free][:,free],-L[free][:,boundary]@values[boundary])
 if not np.isfinite(values[domain]).all()or values[domain].min()<-1e-9:raise ValueError('Unconstrained/disconnected or nonconvex fabric field')
 values[free]=np.maximum(values[free],0);values[free]/=values[free].sum(1,keepdims=True)
 # Restore exact sewn boundary rows: normalization must not perturb aliases.
 values[boundary]=bw[boundary]
 ownership=np.zeros(len(p));ownership[sleeve]=1
 if len(free):ownership[free]=spsolve(L[free][:,free],-L[free][:,boundary]@ownership[boundary])
 assert np.array_equal(values[boundary],bw[boundary])
 return values,{'domain':domain,'free':free,'edges':e,'ownership':ownership,'restLengths':length,'activeBoneUnion':support}

def world_skin(p,w,D):
 return np.einsum('vj,jab,vb->va',w,D[:,:3,:],np.c_[p,np.ones(len(p))],optimize=False)

def paired_material_bounds(pos,grid,weights,matrices):
 """Endpoint gap / available sewn rest path is a necessary average strain.

 Grid[k,angle] must traverse the real new seam from torso to sleeve. Gap is
 computed with actual fixed boundary skin rows, preserving exact source34 D.
 This lower bound alone cannot qualify area, crossings, thickness or support.
 """
 grid=np.asarray(grid,dtype=int);p=np.asarray(pos);rest=np.linalg.norm(np.diff(p[grid],axis=0),axis=2).sum(0)
 if (rest<1e-9).any():raise ValueError('Degenerate fabric paths')
 rows=[]
 for key,D in matrices.items():
  ends=np.r_[grid[0],grid[-1]];q=world_skin(p[ends],weights[ends],D).reshape(2,len(grid[0]),3);gap=np.linalg.norm(q[1]-q[0],axis=1);r=gap/rest
  rows.append({'pose':str(key),'maxNecessaryPathAverageStretch':float(r.max()),'p99NecessaryPathAverageStretch':float(np.quantile(r,.99)),'worstAngularColumn':int(r.argmax()),'worstRestMaterialPathM':float(rest[r.argmax()]),'worstPosedBoundaryGapM':float(gap[r.argmax()])})
 return rows
