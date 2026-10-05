"""Read lower-head layer ancestry and canonical anatomical sections."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[6]
E=ROOT/'docs/evidence/hero-remaster/finish-2026-10-05/construction'
n=np.load(E/'foundation-source.npz')
r=np.load(ROOT/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface96/ordered-boundaries.npz')
p=n['headXYZ'];t=n['headTriangles'];c=n['canonicalXYZ'];ct=n['canonicalTriangles']
report={'headLayerRegistry':{k:np.asarray(r[k]).shape for k in r.files},'sections':[]}
for z in [1.525,1.535,1.545,1.555,1.565,1.575,1.585,1.595,1.605]:
 cross=[]
 for a,b in [(0,1),(1,2),(2,0)]:
  pa,pb=c[ct[:,a]],c[ct[:,b]]
  m=(pa[:,2]<z)!=(pb[:,2]<z)
  x=pa[m]+((z-pa[m,2])/(pb[m,2]-pa[m,2]))[:,None]*(pb[m]-pa[m])
  cross.extend(x.tolist())
 q=np.array(cross);report['sections'].append({'z':z,'points':len(q),'bounds':[q.min(0).tolist(),q.max(0).tolist()]})
for k in ['outerHeadOrderedNativeRepresentatives','innerHeadOrderedNativeRepresentatives']:
 ids=r[k];q=p[ids];report[k]={'vertices':len(ids),'bounds':[q.min(0).tolist(),q.max(0).tolist()],'mean':q.mean(0).tolist(),'protected':np.intersect1d(ids,n['headProtectedIDs']).tolist()}
(E/'neck-feasibility-source.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
