from pathlib import Path
import sys,json,numpy as np
from scipy.spatial import cKDTree
OUT=Path(__file__).parent;d=np.load(OUT/'source-geometry.npz');base=d['source'];tri=d['tri'];alias=d['alias'];roi=((base[tri][:,:,1]>1.08)&(base[tri][:,:,1]<1.49)&(abs(base[tri][:,:,2])<.405)).all(1);ids=np.flatnonzero(roi);tri=tri[roi];aliases=alias[tri];EPS=1e-9
exec('def crossing'+(OUT.parents[1]/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
rows=[]
for path in [OUT/'source-geometry.npz',OUT/'envelope-rest.npz']+sorted(OUT.glob('raise-target-*.npz')):
 dat=np.load(path);p=dat['source']if 'source'in dat else np.concatenate([dat['p0'],dat['p2']]);T=p[tri];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);tree=cKDTree(cent);neighbours=tree.query_ball_point(cent,rad+rad.max());pairs=np.array([(a,b)for a,row in enumerate(neighbours)for b in row if a<b],dtype=int).reshape(-1,2);c0=len(pairs);keep=np.linalg.norm(cent[pairs[:,0]]-cent[pairs[:,1]],axis=1)<=rad[pairs[:,0]]+rad[pairs[:,1]]+1e-12;pairs=pairs[keep];lo=T.min(1);hi=T.max(1);keep=((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1);pairs=pairs[keep];pairs=pairs[np.array([not set(aliases[a]).intersection(aliases[b])for a,b in pairs])];hit=crossing(T[pairs[:,0]],T[pairs[:,1]]);rows.append({'name':path.name,'strictCrossingPairs':int(hit.sum()),'witnesses':ids[pairs[hit]].tolist()[:20],'radialCandidates':c0,'aabbCandidatesNonadjacent':len(pairs)});print(rows[-1],flush=True)
(OUT/'pose-target-gate.json').write_text(json.dumps({'rows':rows,'predicate':'Exhaustive containing-sphere KD tree broadphase followed by AABB and strict transverse6edge tests, shared sourcepositionaliases excluded. Full upperclothfinite restcheck, noCCD/thickness.'},indent=2))
