"""Extend frozen200 source-boundary proof to retained p0+p1+p2 cloth only."""
from pathlib import Path
from collections import defaultdict, Counter
import ast, hashlib, heapq, json, struct, time
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/local-retopology-design200'
sha=lambda b:hashlib.sha256(b).hexdigest();pins={};start=time.monotonic()
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();s=sha(b);assert h is None or h==s
 pins[str(p)]={'sha256':s,'bytes':len(b)};return b
original_freeze=pin(E/'freeze.json');original=json.loads(original_freeze)
for group in ['inputPins','ownedRecipeEvidencePins']:
 for p,row in original[group].items():pin(p,row['sha256'])
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py'
cl=next(n for n in ast.parse(reader.read_bytes()).body if isinstance(n,ast.ClassDef)and n.name=='GLB')
exec(compile(ast.Module(body=[cl],type_ignores=[]),str(reader),'exec'),globals())
source=B/'source-preserving-garment185/operator/rider.glb';h='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';g=GLB(source,h)
mesh=[g.primitive(0,i)for i in range(3)];p0U,p0q=np.unique(mesh[0][0]['POSITION'],axis=0,return_inverse=True)
domain=json.loads((E/'source-domain-boundaries.json').read_text());mask=set(domain['proposedSourceFaceIDs'])
P=np.concatenate([x[0]['POSITION']for x in mesh]);U,q=np.unique(P,axis=0,return_inverse=True);off=np.cumsum([0]+[len(x[0]['POSITION'])for x in mesh])
lookup={tuple(p):i for i,p in enumerate(U)};oldmap={i:lookup[tuple(p)]for i,p in enumerate(p0U)}
graph=defaultdict(set);ef=defaultdict(list);primitive_nodes=defaultdict(set)
for pi,(a,F)in enumerate(mesh):
 for fi,t in enumerate(q[off[pi]+F]):
  if pi==0 and fi in mask:continue
  primitive_nodes[pi].update(map(int,t))
  for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);graph[i].add(j);graph[j].add(i);ef[tuple(sorted((i,j)))].append([pi,fi])
section=json.loads((B/'source-axilla189/section-fixed-03.json').read_text())
roots={loop['geometricClass']:{oldmap[int(i)]for s in loop['segments']for ep in s['endpoints']for i in ep.get('sourcePhysicalEdge',[])if p0U[i,1]<1.13}for loop in section['loops']}
remaining=set(graph);components=[];cid={}
while remaining:
 stack=[min(remaining)];seen=set()
 while stack:
  i=stack.pop()
  if i in seen:continue
  seen.add(i);stack.extend(graph[i]-seen)
 remaining-=seen;label=len(components)
 for i in seen:cid[i]=label
 components.append({'componentID':label,'physicalNodes':len(seen),'rootLabels':sorted(n for n,ids in roots.items()if seen&ids),'primitiveReferencedNodes':{str(pi):len(seen&ns)for pi,ns in primitive_nodes.items()},'axisBoundsM':[U[sorted(seen)].min(0).tolist(),U[sorted(seen)].max(0).tolist()]})
best={};prev={};heap=[]
for i in sorted(roots['central_Z0_straddling']):best[i]=float(U[i,1]);prev[i]=None;heapq.heappush(heap,(best[i],i))
hit=None
while heap:
 d,i=heapq.heappop(heap)
 if d!=best[i]:continue
 if i in roots['positiveZ_lateral']:hit=i;break
 for j in sorted(graph[i]):
  v=max(d,float(U[j,1]))
  if v<best.get(j,float('inf')):best[j]=v;prev[j]=i;heapq.heappush(heap,(v,j))
path=[]
if hit is not None:
 path=[hit]
 while prev[path[-1]]is not None:path.append(prev[path[-1]])
 path.reverse()
rings=[]
for c in domain['orderedBoundaryRings']:
 ids=c['orderedPhysicalIDs'];labels=[cid[oldmap[i]]for i in ids]
 rings.append({'orderedOriginalP0PhysicalIDs':ids,'orderedWholePhysicalIDs':[oldmap[i]for i in ids],'orderedRetainedWholeComponentIDs':labels,'componentCounts':dict(Counter(labels)),'ownershipMeaning':'Literal full retained graph components; root labels are geometric, not anatomy. The89/62 are patch cuts atY1.16–1.35, neither cuff nor all-high rings.'})
seams={}
for pi in [1,2]:
 shared=set(q[:off[1]])&set(q[off[pi]:off[pi+1]])
 seams[str(pi)]={'sourceExactSharedPhysicalNodes':len(shared),'retainedSharedPhysicalNodes':len(primitive_nodes[0]&primitive_nodes[pi]),'originalP0IDs':[i for i,v in oldmap.items()if v in shared]}
mesh0_nodes=[{'nodeID':i,'name':n.get('name'),'skin':n.get('skin'),'worldColumnMajor':g.world(i).T.ravel().tolist()}for i,n in enumerate(g.d['nodes'])if n.get('mesh')==0]
result={'status':'READONLY_WHOLE_CLOTH_EXTENSION_NO_CAP_GEOMETRY','originalDesignFreezeSHA256':sha(original_freeze),'sourceSHA256':h,'physicalIDConvention':'np.unique concatenated mesh0 p0,p1,p2 Float32 POSITION; original p0 mapping explicit','sameMesh0AttachmentForAllThreePrimitives':mesh0_nodes,'removedP0SourceFaces':sorted(mask),'retainedWholeComponents':components,'boundaryRingsByRetainedWholeOwnership':rings,'sourcePrimitiveSeams':seams,'retainedWholeMinimaxPathFound':hit is not None,'retainedWholeMinimaxAttachmentY_M':best.get(hit),'retainedRootPathPhysicalIDs':path,'retainedRootPathPositionsM':U[path].tolist(),'retainedRootPathEdges':[{'wholePhysicalIDs':[i,j],'sourcePrimitiveAndFaces':ef[tuple(sorted((i,j)))]}for i,j in zip(path,path[1:])],'p0ToWholePhysicalMap':{str(i):v for i,v in oldmap.items()},'separateCapHypothesis':'REJECTED: no retained whole-cloth shoulder path connects the left and central roots. Separate independent disk closures would leave left source garment detached unless a new explicit high join or different source domain is registered. No cap geometry generated.','geometryAttempts':0,'newWeights':0,'solverRuns':0,'exports':0,'GPUWork':False,'seconds':time.monotonic()-start,'inputPins':pins}
(E/'whole-cloth-extension.json').write_text(json.dumps(result,indent=2)+'\n')
for p,row in pins.items():assert sha(Path(p).read_bytes())==row['sha256']
print(json.dumps({k:result[k]for k in ['originalDesignFreezeSHA256','retainedWholeComponents','retainedWholeMinimaxPathFound','retainedWholeMinimaxAttachmentY_M','sourcePrimitiveSeams','separateCapHypothesis','seconds']}))
