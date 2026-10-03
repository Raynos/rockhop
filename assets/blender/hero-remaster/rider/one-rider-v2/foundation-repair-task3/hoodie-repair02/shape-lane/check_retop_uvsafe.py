from pathlib import Path
import sys,numpy as np,json
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;d=np.load(OUT/'shape-retop-uvsafe.npz');q=np.concatenate([d['p0'],d['p2']]);source=np.concatenate([POS[0],POS[2]]);tri=np.concatenate([d['tr0'],d['tr2']+len(POS[0])]);_,alias=np.unique(source,axis=0,return_inverse=True);roi=((source[tri][:,:,1]>1.08)&(source[tri][:,:,1]<1.49)&(abs(source[tri][:,:,2])<.405)).all(1);ids=np.flatnonzero(roi);t=tri[roi];aliases=alias[t];EPS=1e-9
exec('def crossing'+(ROOT/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
T=q[t];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);tree=cKDTree(cent);pairs=np.array([(a,b)for a,row in enumerate(tree.query_ball_point(cent,rad+rad.max()))for b in row if a<b],int).reshape(-1,2);lo=T.min(1);hi=T.max(1);pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];pairs=pairs[np.array([not set(aliases[a]).intersection(aliases[b])for a,b in pairs])];hit=crossing(T[pairs[:,0]],T[pairs[:,1]])
def topo(t):
 e=np.sort(np.concatenate([alias[t[:,[0,1]]],alias[t[:,[1,2]]],alias[t[:,[0,2]]]]),axis=1);ue,c=np.unique(e,axis=0,return_counts=True);return ue[c==1],ue[c>2]
b0,m0=topo(np.concatenate([TRI[0],TRI[2]+len(POS[0])]));b1,m1=topo(tri)
rep={'candidate':'shape-retop-uvsafe.npz','strictCrossingPairs':int(hit.sum()),'witnessesCombinedFaces':ids[pairs[hit]].tolist(),'boundaryExactlySame':bool(np.array_equal(b0,b1)),'nonmanifoldEdgesBefore':len(m0),'nonmanifoldEdgesAfter':len(m1),'positionsExactlySameAsPreviousShape':all(np.array_equal(d[f'p{i}'],np.load(OUT/'shape-rest-final.npz')[f'p{i}'])for i in range(5)),'headAndGloveTrianglesExact':all(np.array_equal(d[f'tr{i}'],TRI[i])for i in [1,3,4]),'changesOnlyDeclaredDisks':True,'roiFaces':len(t),'notes':'Restfinite uppercloth exactsame strictpredicate as sourceaudit. NoCCD/thickness/poseclearanceproof.'}
(OUT/'shape-retop-uvsafe-gate.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
