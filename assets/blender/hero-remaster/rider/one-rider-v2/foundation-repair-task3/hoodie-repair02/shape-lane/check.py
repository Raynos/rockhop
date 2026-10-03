from pathlib import Path
import sys,json,numpy as np
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).parent;d=np.load(OUT/'source-geometry.npz');base=d['source'];tri=d['tri'];alias=d['alias'];roi=((base[tri][:,:,1]>1.08)&(base[tri][:,:,1]<1.49)&(abs(base[tri][:,:,2])<.405)).all(1);ids=np.flatnonzero(roi);tri=tri[roi];aliases=alias[tri];EPS=1e-9
exec((OUT.parents[1]/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0].join(['def crossing','']))
rows=[]
for path in [OUT/'source-geometry.npz',OUT/'shoulder-only.npz',OUT/'envelope-arap.npz']:
 dat=np.load(path);p=dat['source']if 'source'in dat else np.concatenate([dat['p0'],dat['p2']]);bvh=BVHTree.FromPolygons(p.tolist(),tri.tolist(),all_triangles=True,epsilon=0.0);pairs=np.array(sorted(set(tuple(sorted(x))for x in bvh.overlap(bvh)if x[0]!=x[1])),int).reshape(-1,2);pairs=pairs[np.array([not set(aliases[a]).intersection(aliases[b])for a,b in pairs])];hit=crossing(p[tri[pairs[:,0]]],p[tri[pairs[:,1]]]);rows.append({'name':path.name,'strictCrossingPairs':int(hit.sum()),'witnesses':ids[pairs[hit]].tolist()});print(rows[-1],flush=True)
(OUT/'rest-crossing-gate.json').write_text(json.dumps({'rows':rows,'predicate':'BVH broadphase strict transverse6edge tests shared sourcepositionaliases excluded. Full upperclothfinite restcheck, noCCD/thickness.'},indent=2))
