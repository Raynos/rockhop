"""Independent all-endpoint and segment-intersection gap check, source read-only."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189';S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-axilla189');rows=[]
def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
for p in sorted(S.glob('section-fixed-*.json')):
 d=json.loads(p.read_text());central=[l for l in d['loops']if l['geometricClass']=='central_Z0_straddling'and l['closed']]
 if len(central)!=1:continue
 for lateral in d['loops']:
  if lateral in central or not lateral['closed']:continue
  a=np.array([x['positionsM']for x in lateral['segments']])[:,:,[0,2]];b=np.array([x['positionsM']for x in central[0]['segments']])[:,:,[0,2]];av=a[:,1]-a[:,0];bv=b[:,1]-b[:,0];den=cross(av[:,None],bv[None]);delta=b[None,:,0]-a[:,None,0];valid=abs(den)>1e-20;safe=np.where(valid,den,1);t=cross(delta,bv[None])/safe;u=cross(delta,av[:,None])/safe;hits=valid&(t>=0)&(t<=1)&(u>=0)&(u<=1);best=float('inf')
  for pts,ss in [(a.reshape(-1,2),b),(b.reshape(-1,2),a)]:
   v=ss[:,1]-ss[:,0];q=np.clip(((pts[:,None]-ss[None,:,0])*v[None]).sum(2)/(v*v).sum(1)[None],0,1);dist=np.linalg.norm(pts[:,None]-(ss[None,:,0]+q[:,:,None]*v[None]),axis=2);best=min(best,float(dist.min()))
  if hits.any():best=0.
  prior=next(x['gapM']for x in d['armTorsoGapCandidates']if x['lateralClass']==lateral['geometricClass']);rows.append({'heightY_M':d['heightY_M'],'lateralClass':lateral['geometricClass'],'verifiedAllEndpointGapM':best,'segmentIntersectionPairs':int(hits.sum()),'priorFirstEndpointDifferenceM':best-prior})
x={'status':'READONLY_ALL_ENDPOINT_POLYGON_GAPS_VERIFIED','rows':rows,'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Both endpoints of every literal triangle-plane segment against all opposite segments plus all2Dsegment intersections; no first-endpoint-order assumption'};(E/'verified-gaps.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
