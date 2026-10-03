"""Finite actual V7 triangle gates including separate one-sewn-corner folds."""
from surface_slide import *
from scipy.spatial import cKDTree
EPS=1e-9
exec('def crossing'+(ROOT/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
c=TorsoSurfaceSlide();base=np.concatenate([c.pos[0],c.pos[2]]);original=np.concatenate([POS[0],POS[2]]);tri=np.concatenate([c.tri[0],c.tri[2]+len(POS[0])]);_,alias=np.unique(original,axis=0,return_inverse=True)
regions={'upper':((original[tri][:,:,1]>1.08)&(original[tri][:,:,1]<1.49)&(abs(original[tri][:,:,2])<.405)).all(1),'lateral-hem':((original[tri][:,:,1]>.99)&(original[tri][:,:,1]<1.49)&(abs(original[tri][:,:,2])<.405)).all(1)}
def gate(path,region):
 roi=regions[region];ids=np.flatnonzero(roi);t=tri[roi];aliases=alias[t];edges=np.unique(np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[0,2]]]),axis=1),axis=0);l0=np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1);area0=np.linalg.norm(np.cross(base[t[:,1]]-base[t[:,0]],base[t[:,2]]-base[t[:,0]]),axis=1)
 d=np.load(path);q=np.concatenate([d['p0'],d['p2']]);assert np.isfinite(q).all();T=q[t];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1)
 pairs=np.array([(a,b)for a,rr in enumerate(cKDTree(cent).query_ball_point(cent,rad+rad.max()))for b in rr if a<b],int).reshape(-1,2);lo=T.min(1);hi=T.max(1);pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)]
 shared=(aliases[pairs[:,0],:,None]==aliases[pairs[:,1],None,:]).any(2).sum(1);keep=shared<2;pairs=pairs[keep];shared=shared[keep];hit=crossing(T[pairs[:,0]],T[pairs[:,1]]);rat=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(l0,1e-15);area=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)/np.maximum(area0,1e-15)
 return {'file':path.name,'region':region,'strictNonadjacentCrossings':int((hit&(shared==0)).sum()),'strictOneCornerCrossings':int((hit&(shared==1)).sum()),'maxEdgeMinRest2mm':float(rat[l0>=.002].max()),'p99EdgeMinRest2mm':float(np.quantile(rat[l0>=.002],.99)),'collapsedFaces25Pct':int((area<.25).sum()),'minAreaRatio':float(area.min()),'witnessCombinedFacePairs':ids[pairs[hit]].tolist()[:20]}
if __name__=='__main__':
 originalLane=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/hoodie-repair02/shape-lane/volume-lane');files=[originalLane/f'skin-{s}.npz'for s in ['forward-1','elbow-1','single-elbow-90']]+sorted(OUT.glob('slide-*.npz'));rows=[]
 for f in files:
  for r in regions:
   m=gate(f,r);rows.append(m);print({k:v for k,v in m.items()if k!='witnessCombinedFacePairs'},flush=True)
 (OUT/'slide-finite-gates.json').write_text(json.dumps({'method':'Exact V7 triangles; sphere/AABB broadphase; six-edge strict transverse crossings; only complete sewn edges excluded, one-corner crossings counted separately','limits':'Finite9poses, noCCD/material/body/contact guarantee','rows':rows},indent=2))
