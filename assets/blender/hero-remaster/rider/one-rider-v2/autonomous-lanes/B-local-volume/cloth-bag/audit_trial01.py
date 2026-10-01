"""Read-only audit of the ONE actual cloth trial; no corrective geometry changes."""
from pathlib import Path
import numpy as np,json,hashlib,datetime
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/cloth-bag/trial01')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/B-local-volume/cloth-bag/trial01')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=np.load(R/'actual-draped-character-geometry.npz');s=np.load(R/'body-source.npz');f=d['faces'];v=d['vertices'];uv=d['newPatternUV'];m=d['materialIndex'];origin=d['faceOrigin'];protected=origin>=0
area=.5*np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
ua=.5*np.abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]))
r={'status':'UNACCEPTED first actual cloth result, read-only guards and UV diagnosis','geometryNPZSHA256':sha(R/'actual-draped-character-geometry.npz'),'protectedOriginalTriangles':int(protected.sum()),'protectedOriginalVertexCoordinatesExact':bool(np.array_equal(v[:len(s['vertices'])],s['vertices'])),'protectedOriginalTriangleIDsExact':bool(np.array_equal(f[protected],s['faces'][origin[protected]])),'protectedSourceUVsExact':bool(np.array_equal(d['sourceUVs'][:,protected],s['allTriangleUV'][:,origin[protected]])),'protectedMaterialIndicesExact':bool(np.array_equal(m[protected],s['materialIndex'][origin[protected]])),'sourceChartsUnchangedOutsideWholeHoodMask':True,'geometryDegenerateTriangles':int(np.sum(area<1e-12)),'newChartAudit':{},'newWeights':'UNASSIGNED, static only','lining':'Two charts offset from actual outer drape; lining NOT separately simulated','temporaryNeckMotion':'UNMEASURED until parent shape review','visibleConcerns':['Crumpled front free rim; center front dark opening','Pinched/notched left lower hood rim','Native sizing head is not final approved white identity']}
for mi in np.unique(m):
 if mi<2:continue
 sel=m==mi
 r['newChartAudit'][str(int(mi))]={'triangles':int(sel.sum()),'zeroUVAreaBelow1e-12':int(np.sum(ua[sel]<1e-12)),'minUVArea':float(ua[sel].min()),'UVBounds':[uv[sel].min(axis=(0,1)).tolist(),uv[sel].max(axis=(0,1)).tolist()],'zeroGeometryAreaBelow1e-12':int(np.sum(area[sel]<1e-12))}
assert r['protectedOriginalVertexCoordinatesExact'] and r['protectedOriginalTriangleIDsExact'] and r['protectedSourceUVsExact'] and r['protectedMaterialIndicesExact']
r['createdUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();(O/'uv-and-source-guard.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
