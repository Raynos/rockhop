"""Parent independently verifies the rejected indexed construction dump."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/panel-surgery192';B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');sys.path.insert(0,str(R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not(E/'parent-review.json').exists()
freeze=json.loads((E/'freeze.json').read_text())
for path,r in freeze['files'].items():assert sha(path)==r['sha256']and Path(path).stat().st_size==r['bytes']
for path,r in freeze['inputs'].items():assert sha(path)==r['sha256']and Path(path).stat().st_size==r['bytes']
g=GLB(B/'source-preserving-garment185/operator/rider.glb');pr=g.j['meshes'][0]['primitives'][0];attrs={k:g.array(i)for k,i in pr['attributes'].items()};P=attrs['POSITION'];F=g.array(pr['indices']).reshape(-1,3).astype('i8');U,q=np.unique(P,axis=0,return_inverse=True);U=U.astype(float);T=q[F]
z=np.load(B/'panel-surgery192/construction.npz');C=z['positions'].astype(float);kept=z['sourceKeptFaceIDs'];removed=z['removedSourceFaceIDs'];assert len(removed)==69 and np.array_equal(z['indices'],F[kept]) and np.array_equal(kept,np.setdiff1d(np.arange(len(F)),removed))
contract=json.loads((B/'source-seam191/next-construction-contract.json').read_text());assert removed.tolist()==contract['prospectiveBridgeRibbonOriginalFaceIDs'];assert len(z['newPhysicalTriangles'])==0
changed=np.flatnonzero((P!=z['positions']).any(1));assert changed.tolist()==[2409]and q[2409]==1571;assert C[2409,0]==P[2409,0]and C[2409,2]==P[2409,2];assert C[2409,1]==float(np.float32(1.31))
for k,a in attrs.items():assert np.array_equal(z['attribute_'+k],z['positions']if k=='POSITION'else a)
for j,t in enumerate(pr.get('targets',[])):
 for k,i in t.items():assert np.array_equal(z[f'morph_{j}_{k}'],g.array(i))
provenance=json.loads((B/'panel-surgery192/construction-provenance.json').read_text());scope=set(provenance['sourceScopeFaceIDs']);outside=sorted({int(r)for i in range(len(F))if i not in scope for r in F[i]});assert np.array_equal(P[outside],z['positions'][outside]);assert set(removed)<=scope
# Literal new directed boundary compared with the source body boundary.
def boundaries(ts):
 es=defaultdict(list)
 for i,t in enumerate(ts):
  for a,b in zip(t,np.roll(t,-1)):es[tuple(sorted((int(a),int(b))))].append((int(a),int(b),i))
 return es
old=boundaries(T);new=boundaries(T[kept]);cut=[v[0][:2]for key,v in new.items()if len(v)==1 and len(old[key])==2];assert len(cut)==93
out=Counter(a for a,b in cut);inc=Counter(b for a,b in cut);bad=[i for i in sorted(set(out)|set(inc))if out[i]!=1 or inc[i]!=1];assert len(bad)==12 and all(out[i]==inc[i]==2 for i in bad)
# Vertex links at these boundary pinches consist of two retained face fans.
linkFans=[]
for v in bad:
 link=defaultdict(set)
 for t in T[kept][(T[kept]==v).any(1)]:
  a,b=[int(x)for x in t if x!=v];link[a].add(b);link[b].add(a)
 remaining=set(link);components=0
 while remaining:
  components+=1;stack=[min(remaining)];seen=set()
  while stack:
   a=stack.pop()
   if a in seen:continue
   seen.add(a);remaining.discard(a);stack.extend(link[a]-seen)
 assert components==2;linkFans.append({'sourcePhysicalID':v,'retainedLinkComponents':components})
# Independent open-interior Moller segment/triangle witness predicate.
def crosses(a,b):
 for aa,bb in [(a,b),(b,a)]:
  e1,e2=bb[1]-bb[0],bb[2]-bb[0]
  for s,e in zip(aa,np.roll(aa,-1,axis=0)):
   d=e-s;h=np.cross(d,e2);det=float(e1@h)
   if abs(det)<1e-13:continue
   v0=s-bb[0];u=float(v0@h)/det;qv=np.cross(v0,e1);v=float(d@qv)/det;t=float(e2@qv)/det
   if min(u,v,1-u-v,t,1-t)>1e-10:return True
 return False
witnesses=[]
for a,b in [(3552,3556),(3552,3561),(3552,3821),(3552,4110)]:
 assert a in kept and b in kept;assert crosses(C[F[a]],C[F[b]])and not crosses(P[F[a]].astype(float),P[F[b]].astype(float));witnesses.append({'sourceFaces':[a,b],'candidateStrictCrossing':True,'originalClear':True})
# Independently process source-Y sublevel connectivity in the remaining mesh.
CU=z['physicalPositions'].astype(float);graph=[set()for _ in U]
for a,b in new:graph[a].add(b);graph[b].add(a)
section=json.loads((B/'source-axilla189/section-fixed-03.json').read_text());roots={l['geometricClass']:{v for s in l['segments']for ep in s['endpoints']for v in ep.get('sourcePhysicalEdge',[])if U[v,1]<1.13}for l in section['loops']}
parent=np.arange(len(U));active=np.zeros(len(U),bool);tags=[set()for _ in U]
for label in ['central_Z0_straddling','positiveZ_lateral']:
 for v in roots[label]:tags[v].add(label)
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=int(parent[a])
 return a
attachment=None
for y in np.unique(CU[:,1]):
 ids=np.flatnonzero(CU[:,1]==y);active[ids]=True
 for a in ids:
  for b in graph[a]:
   if active[b]:
    x,w=find(int(a)),find(b)
    if x!=w:parent[w]=x;tags[x]|=tags[w]
 if any({'central_Z0_straddling','positiveZ_lateral'}<=tags[find(int(a))]for a in ids):attachment=float(y);break
reported=json.loads((E/'report.json').read_text());assert attachment==reported['leftFirstAttachmentY_M']and attachment<1.3
# Float64 diagnostic plane1.31: do not round it down into Float32 vertex equality.
y=1.31;touches=0
for t in T[kept]:
 ys=CU[t,1]
 if ys.min()<=y<=ys.max() and np.any(ys==y):touches+=1
assert touches==0
ship=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/ship192/ship-gate.json').read_text());assert not ship['errors']
for run in ship['runs']:assert run['finishTimeFloat64LE']=='abaaaaaaaa0a4440'and run['result']['hash']=='368f1ca5bd9e830a'and run['crashRestart']['crashed']
x={'status':'REJECTED_ACTUAL_CONSTRUCTION_BOUNDARY_PINCHES_CROSSINGS_LOW_ATTACHMENT','frozenFilesVerified':len(freeze['files']),'inputPinsVerified':len(freeze['inputs']),'constructionSHA256':sha(B/'panel-surgery192/construction.npz'),'geometryAttempts':1,'newOpenEdges':93,'vertexBoundaryPinches':linkFans,'strictWitnessesIndependentlyVerified':witnesses,'leftAttachmentY_M':attachment,'removedFaces':69,'generatedResealFaces':0,'changedSourceRows':changed.tolist(),'protectedOutsideArraysAndAllOtherOriginalAttributesMorphsExact':True,'planePrecisionCorrection':'Stored movedY is1.309999942779541, not literal1.31. Parent Float64 plane check has0 equality touches; sibling Float32 promotion produced5 point touches. Other rejection gates are unchanged.','scopeLabelCorrection':'Sibling whole topology includes all five primitives, including the head; its2components are not a cloth-only component count.','ordinaryShip192':'PASS_BOTH_TIERS_EXACT_FINISH_CRASH_RESTART_1_2MS_NO_CANDIDATE','limits':'No GLB/export/motion/UV/sealing/volume/PBR/anatomy pass. Complete broadphase certification remains sibling pinned evidence; parent independently verifies all four crossing witnesses and actual boundary failure.','next':'Change actual cut construction; do not retry69-face union with another triangulator or repeat the1571Y pull.'}
(E/'parent-review.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k not in ['vertexBoundaryPinches','strictWitnessesIndependentlyVerified']}))
