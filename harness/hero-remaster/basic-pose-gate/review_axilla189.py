"""Parent raw-source sublevel connectivity and frozen scope verification."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib,json,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop'); E=R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189'
sys.path.insert(0,str(R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (E/'parent-review.json').exists()
freeze=json.loads((E/'freeze.json').read_text()); report=json.loads((E/'report.json').read_text())
for r in freeze['files']:
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
for p,r in report['inputs'].items():assert sha(p)==r['sha256']
base=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
g=GLB(base/'source-preserving-garment185/operator/rider.glb'); p=g.j['meshes'][0]['primitives'][0]
P=g.array(p['attributes']['POSITION']); F=g.array(p['indices']).reshape(-1,3); U,q=np.unique(P,axis=0,return_inverse=True); T=q[F]
edges=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),1),axis=0)
adj=[[]for _ in U]
for a,b in edges:adj[a].append(b);adj[b].append(a)
# Independently reconstruct literal plane segments from physical source edge IDs.
def section(y):
 graph=defaultdict(set); seg=[]
 for f,t in enumerate(T):
  ys=U[t,1]
  if not ys.min()<y<ys.max():continue
  assert not np.any(ys==y),'Use declared noncritical planes'
  keys=[]
  for a,b in zip(t,np.roll(t,-1)):
   if (U[a,1]<y<U[b,1]) or (U[b,1]<y<U[a,1]):keys.append(tuple(sorted((int(a),int(b)))))
  assert len(keys)==2
  graph[keys[0]].add(keys[1]);graph[keys[1]].add(keys[0]);seg.append((f,keys))
 remaining=set(graph);loops=[]
 while remaining:
  stack=[min(remaining)];nodes=set()
  while stack:
   n=stack.pop()
   if n in nodes:continue
   nodes.add(n);remaining.discard(n);stack.extend(graph[n]-nodes)
  xyz=np.array([U[a]+(y-U[a,1])/(U[b,1]-U[a,1])*(U[b]-U[a])for a,b in nodes]);label='central_Z0_straddling'if xyz[:,2].min()<0<xyz[:,2].max() else 'positiveZ_lateral'if xyz[:,2].mean()>0 else 'negativeZ_lateral'
  loops.append({'label':label,'closed':all(len(graph[n])==2 for n in nodes),'nodes':nodes})
 return loops
low=section(.94);assert len(low)==3 and all(x['closed']for x in low)
seeds={x['label']:{v for e in x['nodes']for v in e if U[v,1]<.94}for x in low}
# Union-find by increasing source-Y independently of builder Dijkstra paths.
parent=np.arange(len(U));active=np.zeros(len(U),bool);labels=[set()for _ in U]
for name,ids in seeds.items():
 for i in ids:labels[i].add(name)
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
heights={}
for y in np.unique(U[:,1]):
 ids=np.flatnonzero(U[:,1]==y);active[ids]=True
 for i in ids:
  for j in adj[i]:
   if active[j]:
    a,b=find(int(i)),find(int(j))
    if a!=b:parent[b]=a;labels[a]|=labels[b]
 for i in ids:
  names=labels[find(int(i))]
  if 'central_Z0_straddling'in names:
   for name in ['positiveZ_lateral','negativeZ_lateral']:
    if name in names and name not in heights:heights[name]=float(y)
 if len(heights)==2:break
for c in report['firstConnections']:
 assert heights[c['geometricSide']]==c['firstSublevelSurfaceConnectionY_M']
 for a,b in zip(c['pathPhysicalIDs'],c['pathPhysicalIDs'][1:]):assert b in adj[a]
 assert max(float(U[i,1])for i in c['pathPhysicalIDs'])==heights[c['geometricSide']]
 assert len(section(c['beforeY']))==c['contoursBefore'] and len(section(c['afterY']))==c['contoursAfter']
for r in report['sections']:
 loops=section(r['heightY_M']);assert len(loops)==r['contourCount'] and sum(x['closed']for x in loops)==r['closedContourCount']
scope=[]
for rec in json.loads((E/'strip-scope-summary.json').read_text())['scopes']:
 raw=json.loads(Path(rec['rawScopePath']).read_text()); chosen=raw['sourceFaceIDs'];counts=Counter();out=Counter();inc=Counter()
 for t in T[chosen]:
  for a,b in zip(t,np.roll(t,-1)):counts[tuple(sorted((int(a),int(b))))]+=1
 for t in T[chosen]:
  for a,b in zip(t,np.roll(t,-1)):
   if counts[tuple(sorted((int(a),int(b))))]==1:out[int(a)]+=1;inc[int(b)]+=1
 bad=[{'physicalID':i,'out':out[i],'in':inc[i],'sourceRows':np.flatnonzero(q==i).tolist(),'positionM':U[i].tolist()}for i in sorted(set(out)|set(inc))if out[i]!=1 or inc[i]!=1]
 assert (not bad)==rec['boundaryGraphValid'];assert len(chosen)==rec['faces']
 scope.append({'side':rec['side'],'faces':len(chosen),'boundaryNodes':len(out),'invalidBoundaryNodes':bad,'valid':not bad})
ship=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/ship189/ship-gate.json').read_text());assert ship['errors']==[]
for run in ship['runs']:assert run['finishTimeFloat64LE']=='abaaaaaaaa0a4440' and run['result']['hash']=='368f1ca5bd9e830a' and run['crashRestart']['crashed']
result={'status':'READONLY_SOURCE_ATTACHMENT_CONFIRMED_NO_BILATERAL_GEOMETRY_AUTHORIZATION','frozenFilesVerified':len(freeze['files']),'inputPinsVerified':len(report['inputs']),'parentMethod':'Raw GLB plane graph plus independent source-Y union-find; exact original edge paths and directed scope boundary counts','firstSourceConnectionY_M':heights,'scope':scope,'sourceUnchanged':True,'wholeAnatomyOrConstructionAccepted':False,'ship189':'PASS_REPLAY_CLEAR_CRASH_RESTART_NO_CANDIDATE','next':'Explicit minimal halfedge fan closure audit of invalid right boundary before any geometry; no ROI retuning or source edits','cosmetics':'PAUSED'}
(E/'parent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
