"""Complete literal cloth crossing attribution; bounded-memory broadphase."""
from pathlib import Path
import numpy as np,json,ast,hashlib,sys
from scipy.spatial import cKDTree
from collections import Counter
HERE=Path(__file__).resolve().parent;H=HERE.parents[2];ROOT=H.parent
SHAPE=HERE.parent/'armhole-construction/armhole-chart-outward.npz';f=np.load(SHAPE)
assert hashlib.sha256(SHAPE.read_bytes()).hexdigest()=='10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7'
code=(ROOT/'audit/self_intersections.py').read_text();node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef)and n.name=='crossing');exec(compile(ast.Module(body=[node],type_ignores=[]),'<strict triangle predicate>','exec'));EPS=1e-9
p=[f[f'p{i}']for i in range(5)];rest=np.r_[p[0],p[2]];tr=np.r_[f['tr0'],f['tr2']+len(p[0])];alias=np.r_[f['physicalWeld0'],f['physicalWeld2']][tr];kinds=np.r_[np.repeat('retained0',33968),f['newFaceKind'],np.repeat('retained2',len(f['tr2']))];centreY=rest[tr][:,:,1].mean(1)
def full_gate(pts):
 q=np.r_[pts[0],pts[2]];T=q[tr];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);tree=cKDTree(cent);lo=T.min(1);hi=T.max(1);hits=[];sh=[]
 for start in range(0,len(T),64):
  nearby=tree.query_ball_point(cent[start:start+64],rad[start:start+64]+rad.max());pairs=np.array([(start+a,b)for a,rr in enumerate(nearby)for b in rr if start+a<b],int).reshape(-1,2)
  if not len(pairs):continue
  pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=(alias[pairs[:,0],:,None]==alias[pairs[:,1],None,:]).any(2).sum(1);keep=shared<2;pairs=pairs[keep];shared=shared[keep]
  hit=crossing(T[pairs[:,0]],T[pairs[:,1]]);hits.extend(pairs[hit].tolist());sh.extend(shared[hit].tolist())
 hits=np.array(hits,int).reshape(-1,2);sh=np.array(sh,int);classes=Counter('|'.join(sorted((str(kinds[a]),str(kinds[b]))))for a,b in hits);source=np.array([k.startswith('retained')for k in kinds]);fixed=source[hits].all(1);upper=(centreY[hits]>1.08).any(1);new=~source[hits].all(1)
 return {'allClothTriangles':len(T),'strictNonadjacentCrossings':int((sh==0).sum()),'strictOneCornerCrossings':int((sh==1).sum()),'allPairClasses':dict(classes),'retainedRetainedCrossingPairs':int(fixed.sum()),'upperRetainedRetainedCrossingPairs':int((fixed&upper).sum()),'newFabricInvolvedPairs':int(new.sum()),'upperNewFabricInvolvedPairs':int((new&upper).sum()),'crossingPairs':hits.tolist(),'sharedPhysicalWeldCorners':sh.tolist()}
if __name__=='__main__':
 path=Path(sys.argv[1])if len(sys.argv)>1 else H/'rig-lane/construction-weights/poses/shape_control-actual_source34-304.npz';d=np.load(path);pts=[d[f'p{i}']for i in range(5)];r=full_gate(pts);r.update(posePath=str(path),poseSHA256=hashlib.sha256(path.read_bytes()).hexdigest(),shapeSHA256=hashlib.sha256(SHAPE.read_bytes()).hexdigest(),method='All cloth0+2 triangles; authoritative explicit physicalWeld adjacency, strict transverse six-edge predicate;64-triangle memory-bounded AABB broadphase; no pose atlas, no crop, no pair witness truncation',limits='Does not classify tangent/coplanar contact; head/glove surfaces require separate QA gate. Retained geometry is a fixed obstacle in the planned interior-only transport.');out=HERE/(path.stem+'-all-pairs.json');out.write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ['crossingPairs','sharedPhysicalWeldCorners']},indent=2),flush=True)
