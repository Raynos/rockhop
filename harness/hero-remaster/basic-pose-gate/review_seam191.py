"""Parent raw-source seam/fan proof; no artwork acceptance."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-seam191';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');sys.path.insert(0,str(R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not(E/'parent-review.json').exists()
freeze=json.loads((E/'freeze.json').read_text());items=freeze['files'];items=[{'path':p,**r}for p,r in items.items()]if isinstance(items,dict)else items
for r in items:assert sha(r['path'])==r['sha256']and Path(r['path']).stat().st_size==r['bytes']
g=GLB(B/'source-preserving-garment185/operator/rider.glb');p=g.j['meshes'][0]['primitives'][0];P=g.array(p['attributes']['POSITION']);F=g.array(p['indices']).reshape(-1,3);U,q=np.unique(P,axis=0,return_inverse=True);T=q[F];U=U.astype(float)
raw=json.loads((B/'source-seam191/literal-inventory.json').read_text());proof=json.loads((B/'source-seam191/endpoint-fan-contract.json').read_text());contract=json.loads((B/'source-seam191/next-construction-contract.json').read_text())
for path,r in raw['inputs'].items():assert sha(path)==r['sha256']
edges=defaultdict(set)
for i,t in enumerate(T):
 for a,b in zip(t,np.roll(t,-1)):edges[tuple(sorted((int(a),int(b))))].add(i)
for rec in proof['rootedBelowTargetPaths']:
 ids=rec['physicalIDs'];assert ids[0]==1571 and max(U[ids,1])==rec['maximumY_M'] and max(U[ids,1])<1.30
 for a,b,r in zip(ids,ids[1:],rec['edges']):assert r['physicalIDs']==[a,b]and set(r['sourceFaces']).issubset(edges[tuple(sorted((a,b)))])
fan=np.flatnonzero((T==1571).any(1)).tolist();assert fan==proof['sourceIncidentFanFaceIDs'];assert np.flatnonzero(q==1571).tolist()==proof['sourceRowAliases']
seam=contract['orderedProspectiveSeamPhysicalIDs'];assert len(seam)==45 and len(set(seam))==45
for a,b in zip(seam,seam[1:]):assert tuple(sorted((a,b)))in edges
assert [seam[0],seam[-1]]==[1571,12928] or [seam[-1],seam[0]]==[1571,12928]
old=set(raw['scopeSourceFaces']);new=old|{4689,4691};assert len(new)==1233 and set(fan).issubset(new)
counts=Counter();direct=defaultdict(list)
for i in new:
 for a,b in zip(T[i],np.roll(T[i],-1)):counts[tuple(sorted((int(a),int(b))))]+=1;direct[tuple(sorted((int(a),int(b))))].append((int(a),int(b)))
assert max(counts.values())==2 and all(v[0]==v[1][::-1]for v in direct.values()if len(v)==2)
out={};ind=Counter()
for key,n in counts.items():
 if n==1:
  a,b=direct[key][0];assert a not in out;out[a]=b;ind[b]+=1
assert set(out)==set(ind)and all(n==1 for n in ind.values())
remain=set(out);lengths=[]
while remain:
 a=min(remain);cur=a;n=0
 while cur in remain:remain.remove(cur);n+=1;cur=out[cur]
 assert cur==a;lengths.append(n)
assert sorted(lengths)==[62,89] and 1571 not in out and 1380 in out
assert len(set(T[list(new)].ravel()))-len(counts)+len(new)==0
oldBoundary=set(v for c in raw['boundaryCycles']for v in c['orderedPhysicalP0IDs']);assert oldBoundary-set(out)=={1571}and set(out)-oldBoundary=={1380}
delta=float(np.linalg.norm(np.array(proof['proposedReleasedFaceContract']['targetEndpointPositionM'])-U[1571]));assert abs(delta-.022861537933349663)<1e-14
x={'status':'SOURCE_SEAM_ENDPOINT_OBSTRUCTION_AND_DISTINCT_RELEASED_FAN_CONTRACT_VERIFIED','frozenFilesVerified':len(items),'rawInputPinsVerified':len(raw['inputs']),'orderedSourceSeamEdges':44,'seamEndpointPhysicalIDs':[1571,12928],'rootedPathMaximumY_M':[r['maximumY_M']for r in proof['rootedBelowTargetPaths']],'newContract':{'addedOriginalFaces':[4689,4691],'totalFaces':1233,'oldReleasedBoundaryVertex':1571,'newFixedBoundaryVertex':1380,'cycleLengths':[89,62],'Euler':0,'proposedEndpointDisplacementM':delta},'source185Unchanged':True,'geometryOutputs':0,'limits':'Contour-rooted dual-graph panel continuation is a registered geometric heuristic, not proven anatomy. Low endpoint obstruction applies if these rooted paths/fans survive; not every annulus topology. New contract has topology feasibility only. No rest-crossing/UV/normal/volume/motion/PBR acceptance.','next':'ONE explicitly unaccepted LEFT-only construction prototype with frozen literal new contract; preserve right/head/hood/cuffs/lowerbody/rig/outside arrays. Actual exported gray/PBR films required; below-scope weight witness remains failed.'}
(E/'parent-review.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
