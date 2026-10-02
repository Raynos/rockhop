"""Literal finite-face isolation, not automatic remeshing or accepted cleanup."""
from pathlib import Path
import json,hashlib
import numpy as np,trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
source=B/'tpose-shape207-01/native-decoded.npz';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8c337ad381a5c498a3655764d391cd14137fa7aa05ed5d7f3b94c8385a07ac53'
z=np.load(source);V=z['vertices'];F=z['faces'];good=np.isfinite(V).all(1);n=good[F].sum(1);assert not np.any((n>0)&(n<3))
faceids=np.flatnonzero(n==3);vertexids=np.unique(F[faceids]);inverse=np.full(len(V),-1,dtype=np.int64);inverse[vertexids]=np.arange(len(vertexids));P=V[vertexids].copy();T=inverse[F[faceids]]
# Only explicit winding reversal used by official display exporter. No merging.
mesh=trimesh.Trimesh(vertices=P,faces=T[:,::-1].copy(),process=False)
assert np.array_equal(mesh.vertices,P) and np.array_equal(mesh.faces,T[:,::-1])
D=B/'finite-native208';assert not D.exists();D.mkdir()
np.savez_compressed(D/'ancestry.npz',sourceVertexIDs=vertexids,sourceFaceIDs=faceids,positions=P,faces=T)
mesh.export(D/'native-display.glb')
E,counts=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0,return_counts=True)
c,l=connected_components(coo_matrix((np.ones(2*len(E)),(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(len(P),len(P))).tocsr())
areas=np.linalg.norm(np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]),axis=1)/2
report={'status':'UNACCEPTED_FINITE_SUBSET_FOR_GRAY_INSPECTION_ONLY','nativeSHA256':hashlib.sha256(raw).hexdigest(),'nativeVertices':len(V),'nativeFaces':len(F),'nonfiniteVertices':int((~good).sum()),'allNonfiniteFacesExcluded':int((n==0).sum()),'mixedFaces':0,'retainedVertices':len(P),'retainedFaces':len(T),'retainedPositionsIndicesExact':True,'displayWinding':'separate copy reversed as official exporter','newShapeEdits':0,'boundaryEdges':int((counts==1).sum()),'nonmanifoldEdges':int((counts>2).sum()),'componentSizes':np.bincount(l).tolist(),'zeroAreaTriangles':int((areas==0).sum()),'physicalPositionAliases':len(P)-len(np.unique(P,axis=0)),'limits':['No merge, cleanup, remeshing, reduction, shape repair, texture, weights, rig or player export.','Finite closed surface is not proof of anatomical completeness or fidelity to the field.','Two zero-area triangles and six-vertex disconnected component retained unchanged.','Entire invalid decoder output preserved; display is explicitly a finite diagnostic subset.']}
report['outputs']={str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in D.iterdir() if p.is_file()}
assert source.read_bytes()==raw
E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/tpose-source208');E.mkdir(exist_ok=True);(E/'finite-isolation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
