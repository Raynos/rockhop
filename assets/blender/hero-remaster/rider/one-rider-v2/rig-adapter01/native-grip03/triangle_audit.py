"""Conservative whole-triangle penetration bound, not vertex-only clearance."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.optimize import linprog
np.seterr(all="raise")
ROOT=Path('/Users/raynos/projects/games/rockhop');R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/native-grip03');O=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip03';d=np.load(R/'native-held-shape.npz');v=d['rodPoints'];t=d['rodTriangleIndices'];p=d['wrappedPositionsDQS'];handtris=d['triangleIndices'];a=v[t];n=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);area=np.linalg.norm(n,axis=1);assert np.all(area>1e-12);n/=area[:,None];offset=np.sum(n*a[:,0],axis=1);assert np.isfinite(n).all() and np.isfinite(offset).all()
# Quantized caps may not be exactly coplanar/convex. Inflate each actual face
# plane only enough to contain ALL actual rod vertices; the resulting convex
# envelope contains all actual triangles and yields a conservative bound.
inflation=np.maximum((np.einsum("vi,fi->vf",v,n)-offset).max(0),0);outer=offset+inflation+1e-9;assert np.max(np.einsum("vi,fi->vf",v,n)-outer)<1e-8
rows=[];skipped=0;maxdepth=0
for i,tri in enumerate(handtris):
 q=p[tri];signed=np.einsum("vi,fi->vf",q,n)-outer
 if np.any(np.min(signed,axis=0)>1e-9):skipped+=1;continue
 origin=q[0];e1=q[1]-q[0];e2=q[2]-q[0];constraints=np.column_stack([np.einsum("fi,i->f",n,e1),np.einsum("fi,i->f",n,e2),np.ones(len(n))]);rhs=outer-np.einsum("fi,i->f",n,origin);constraints=np.vstack([constraints,[1,1,0]]);rhs=np.r_[rhs,1]
 result=linprog([0,0,-1],A_ub=constraints,b_ub=rhs,bounds=[(0,None),(0,None),(None,None)],method='highs');assert result.success
 depth=max(0,float(result.x[2]));maxdepth=max(maxdepth,depth);rows.append({'handTriangle':i,'completeVertexIds':d['sourceCompleteVertexIds'][tri].tolist(),'conservativeEnvelopeDepthNativeM':depth,'barycentric':[float(1-result.x[0]-result.x[1]),float(result.x[0]),float(result.x[1])],'deepestPointNative':(origin+e1*result.x[0]+e2*result.x[1]).tolist()})
rows.sort(key=lambda r:r['conservativeEnvelopeDepthNativeM'],reverse=True)
report={'actualRodTriangles':len(t),'handTriangles':len(handtris),'planeInflationMaximumNativeM':float(inflation.max()),'outsideSeparatedTriangles':skipped,'linearPrograms':len(rows),'maxWholeTriangleEnvelopeDepthNativeM':maxdepth,'maxWholeTriangleEnvelopeDepthRuntimeM':maxdepth*1.015,'thresholdRuntimeM':.001,'below1mmConservativeDepth':maxdepth*1.015<.001,'rows':rows,'bufferSHA256':hashlib.sha256((R/'native-held-shape.npz').read_bytes()).hexdigest(),'limits':'Conservative convex-envelope penetration bound; not zero-intersection/contact-gap or anatomy acceptance. Geometry/inputs unchanged.'}
(O/'triangle-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','bufferSHA256','limits']}))
