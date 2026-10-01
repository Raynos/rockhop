"""Bounded read-only source-surface arm branch experiment; no new skin or asset."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra,connected_components
repo=Path('/Users/raynos/projects/games/rockhop');private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind32';out.mkdir(exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'body-bind26'))
from common import load,accessor,sha
raw,j,b,p,_=load();rest=accessor(j,b,p['attributes']['POSITION'])[0];tri=accessor(j,b,p['indices'])[0].reshape(-1,3)
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);ut=inv[tri]
edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
length=np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1)
graph=coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr()
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];ix={n:i for i,n in enumerate(names)}
ib=accessor(j,b,j['skins'][0]['inverseBindMatrices'])[0].reshape(-1,4,4).transpose(0,2,1);origins=np.linalg.inv(ib)[:,:3,3]
# Seed selection uses source geometry only, not historical weights.
torso=(np.abs(u[:,2])<.13)&(u[:,1]>.95)&(u[:,1]<1.46)
landmarkTriangles=[6340,6403,27413,27805]
landmarkPhysical=np.unique(ut[landmarkTriangles]);torso[landmarkPhysical]=True
assert torso.any();dt=dijkstra(graph,directed=False,indices=np.flatnonzero(torso),min_only=True)
old=np.load(private/'body-bind26/weight-field.npz');assert np.array_equal(old['unique'],u)
projection=json.loads((repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind30/junction-audit.json').read_text())
branches=[];fields={}
for side,sign in [('L',1),('R',-1)]:
 shoulder,elbow,wrist=[origins[ix[n+'.'+side]] for n in ['upperArm','forearm','hand']]
 def dist(a,b):
  delta=b-a;t=np.clip((u-a)@delta/(delta@delta),0,1);return np.linalg.norm(u-a-t[:,None]*delta,axis=1)
 shaft=np.minimum(dist(shoulder,elbow),dist(elbow,wrist))
 seeds=(sign*u[:,2]>.285)&(u[:,1]>.98)&(u[:,1]<1.4)&(shaft<.09)
 assert seeds.any();da=dijkstra(graph,directed=False,indices=np.flatnonzero(seeds),min_only=True)
 # Read-only Voronoi branch candidate: do not assume this alone proves semantics.
 region=(da<dt)&(sign*u[:,2]>.13)&(u[:,1]>.95)&(u[:,1]<1.51)
 ids=np.flatnonzero(region);components,_=connected_components(graph[ids][:,ids],directed=False)
 flags=[]
 for t in sorted(set(w['triangle'] for w in projection['witnesses'])):
  q=ut[t]
  if np.sign(u[q,2].mean())!=sign:continue
  flags.append({'triangle':t,'branchSelected':region[q].tolist(),'sourcePosition':u[q].tolist(),'armGeodesicDistanceM':da[q].tolist(),'torsoGeodesicDistanceM':dt[q].tolist()})
 branches.append({'side':side,'seedVertices':int(seeds.sum()),'branchVertices':len(ids),'connectedComponents':components,'old26SelectedVerticesInBranch':int((old['selected']&region).sum()),'old26SelectedVerticesExcluded':int((old['selected']&(sign*u[:,2]>0)&~region).sum()),'elbow3789BranchMembership':region[ut[3789]].tolist() if sign*np.mean(rest[tri[3789],2])>0 else None,'projected26Witnesses':flags})
 assert not np.any(region[landmarkPhysical]),'Known torso panel vertices must be excluded'
 fields[side]={'distanceArm':da,'distanceTorso':dt,'region':region,'seeds':seeds}
run=private/'body-bind32';run.mkdir(exist_ok=True)
np.savez_compressed(run/'branch-fields.npz',source=u,triangles=ut,torsoSeeds=torso,inverse=inv,**{side+'_'+k:v for side,f in fields.items() for k,v in f.items()})
report={'status':'Read-only constrained segmentation hypothesis; witnessed torso exclusion verified, not complete semantics or new weights','sourceSHA256':sha(raw),'fieldSHA256':sha((run/'branch-fields.npz').read_bytes()),'explicitReviewedTorsoLandmarks':landmarkTriangles,'settings':{'graph':'Complete original physical garment, Euclidean edge lengths, shortest paths constrained to actual source surface','torsoSeeds':'absZ<.13,Y(.95,1.46), plus explicit parent-reviewed source torso triangles6340/6403/27413/27805','armSeeds':'signedZ>.285,Y(.98,1.4),boneShaftDistance<.09','branch':'arm-surface distance<torso-surface distance,Y(.95,1.51),signedZ>.13','historicalWeightEligibility':False,'noParameterSweep':True},'branches':branches,'limits':['Geodesic Voronoi fields do not alone guarantee torso/sleeve semantic correctness, a smooth joint transition or adequate shoulder coverage.','No new weights, geometry, skin, GLB, renderer or physics mutation.','Compare projected original source memberships at rejected26witnesses; no moving appearance pass.']}
(out/'branch-audit.json').write_text(json.dumps(report,indent=2)+'\n');assert load()[0]==raw
print(json.dumps(branches,indent=2))
