"""Parent verifies finite source fan scopes independently, no geometry edit."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-fan190';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
sys.path.insert(0,str(R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not(E/'parent-review.json').exists()
freeze=json.loads((E/'freeze.json').read_text())
for rec in freeze['inputs']+freeze['files']:
 p=Path(rec['path']);assert sha(p)==rec['sha256']and p.stat().st_size==rec['bytes']
g=GLB(B/'source-preserving-garment185/operator/rider.glb');p=g.j['meshes'][0]['primitives'][0];P=g.array(p['attributes']['POSITION']);F=g.array(p['indices']).reshape(-1,3);U,q=np.unique(P,axis=0,return_inverse=True);T=q[F]
old=json.loads((B/'source-axilla189/negativeZ_lateral-proposed-strip.json').read_text());chosen=set(old['sourceFaceIDs']);pinch=7392
incident={i for i,t in enumerate(T)if pinch in t};excluded=incident-chosen
# Original excluded face sectors are exactly two edge-connected pairs.
sectors=[];remaining=set(excluded)
while remaining:
 stack=[min(remaining)];comp=set()
 while stack:
  i=stack.pop()
  if i in comp:continue
  comp.add(i);remaining.discard(i)
  stack.extend(j for j in remaining if len(set(T[i])&set(T[j]))==2)
 sectors.append(sorted(comp))
assert sorted(sectors)==[[32104,32105],[32311,32312]]
def topology(ids):
 ef=defaultdict(list);vs=set()
 for i in ids:
  t=T[i];vs.update(map(int,t))
  for a,b in zip(t,np.roll(t,-1)):ef[tuple(sorted((int(a),int(b))))].append((int(a),int(b),i))
 assert all(len(x)<=2 for x in ef.values())
 assert all(v[0][:2]==v[1][:2][::-1]for v in ef.values()if len(v)==2)
 boundary=[v[0][:2]for v in ef.values()if len(v)==1];out=defaultdict(list);inc=Counter()
 for a,b in boundary:out[a].append(b);inc[b]+=1
 assert all(len(v)==1 and inc[i]==1 for i,v in out.items())
 rest=set(out);loops=[]
 while rest:
  a=min(rest);cur=a;cy=[]
  while cur in rest:rest.remove(cur);cy.append(cur);cur=out[cur][0]
  assert cur==a;loops.append(cy)
 fa=defaultdict(set)
 for v in ef.values():
  if len(v)==2:a,b=v[0][2],v[1][2];fa[a].add(b);fa[b].add(a)
 reach=set();stack=[min(ids)]
 while stack:
  a=stack.pop()
  if a in reach:continue
  reach.add(a);stack.extend(fa[a]-reach)
 assert reach==ids
 return len(vs)-len(ef)+len(ids),sorted(map(len,loops)),vs
rows=[]
for sec in sectors:
 ids=chosen|set(sec);chi,loops,vs=topology(ids);new=vs-set(old['sourcePhysicalVertexIDs']);assert len(new)==1
 node=next(iter(new));dist=float(np.linalg.norm(U[node]-U[pinch]));assert dist>.02
 for face in sec: # Every proposed sector face is necessary to remove degree4 pinch.
  test=ids-{face};count=Counter(tuple(sorted(map(int,e)))for t in T[list(test)]for e in zip(t,np.roll(t,-1)));degree=Counter(v for edge,n in count.items()if n==1 for v in edge);assert degree[pinch]==4
 rows.append({'facesAdded':sec,'newPhysicalVertex':node,'sourceRows':np.flatnonzero(q==node).tolist(),'extentM':dist,'Euler':chi,'cycleLengths':loops,'capRejected':True})
assert all(r['Euler']==0 and r['cycleLengths']==[72,90]for r in rows)
x={'status':'FINITE_TWO_FACE_FAN_TOPOLOGY_VERIFIED_20MM_SCOPE_REJECTED','filesVerified':len(freeze['files']),'inputsVerified':len(freeze['inputs']),'source185Unchanged':True,'parentMethod':'Raw original physical face-edge graph/halfedge cycles/components/Euler and single-face deletion witness','sectors':rows,'geometryCandidateOutputs':0,'judgment':'Original189 and frozen190 bounded scope remain rejected; no geometry or skin acceptance. Rejected local displacement requires changed interior construction, not a secretly enlarged weight patch.'}
(E/'parent-review.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
