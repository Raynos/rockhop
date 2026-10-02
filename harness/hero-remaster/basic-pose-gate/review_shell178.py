"""Independent donor-prefix and topology review of the failed neutral prototype."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,struct
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan';M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((E/'manifest.json').read_text());verified=[]
for name,record in manifest['files'].items():
 p=Path(name);assert p.stat().st_size==record['bytes']and sha(p)==record['sha256'],name;verified.append(name)
def glb(p):
 b=p.read_bytes();assert struct.unpack_from('<II',b)==(0x46546c67,2)
 n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
source=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb');s,sbin=glb(source);a,abin=glb(M/'neutral-assembly01.glb')
assert sha(source)=='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'
assert abin[:len(sbin)]==sbin
assert a['meshes'][1:len(s['meshes'])]==s['meshes'][1:]
assert a['meshes'][0]['primitives'][1:]==s['meshes'][0]['primitives'][1:]
assert a['meshes'][0]['primitives'][0]['attributes']==s['meshes'][0]['primitives'][0]['attributes']
for key in['materials','images','textures','samplers','accessors','bufferViews']:
 assert a.get(key,[])[:len(s.get(key,[]))]==s.get(key,[]),key
for i,node in enumerate(s['nodes']):
 expected={k:v for k,v in node.items()if k!='skin'};assert a['nodes'][i]==expected
assert not a.get('skins')and not a.get('animations')and all('skin'not in n for n in a['nodes'])
d=np.load(M/'drafted-shell01.npz');p=d['p'];f=d['f'];edges=Counter(tuple(sorted((int(x),int(y))))for t in f for x,y in zip(t,np.roll(t,-1)))
nonmanifold=sum(n>2 for n in edges.values());boundary=[e for e,n in edges.items()if n==1];adj=defaultdict(set)
for x,y in boundary:adj[x].add(y);adj[y].add(x)
seen=set();components=0
for start in adj:
 if start in seen:continue
 components+=1;todo=[start];seen.add(start)
 while todo:
  for v in adj[todo.pop()]:
   if v not in seen:seen.add(v);todo.append(v)
audit=json.loads((E/'literal-audit.json').read_text());assert nonmanifold==13 and len(boundary)==248 and components==26
assert nonmanifold==audit['nonmanifoldEdgeCount']
out={'status':'REJECTED_UNRIGGED_CONSTRUCTION_INDEPENDENT_DONOR_TOPOLOGY_CHECK','verifiedBuilderFiles':verified,'sourceSHA256':sha(source),'assemblySHA256':sha(M/'neutral-assembly01.glb'),'originalBINPrefixExact':True,'protectedOtherMeshesAndGloveHoodPrimitivesExact':True,'originalAccessorViewMaterialImageTextureSamplerPrefixesExact':True,'oldNodeTransformsExactExceptRemovedSkinBinding':True,'source19RestLandmarksRetainedButNotBound':True,'authoredVertices':len(p),'authoredTriangles':len(f),'nonmanifoldEdges':nonmanifold,'boundaryEdges':len(boundary),'boundaryComponents':components,'additionalRecordedDefects':'Auditor25degenerate triangles and8strict transverse crossings; not independently collision-rerun here.','cuffMaskWarning':'maxY<=.955 cuff clause is a subset of maxY<=.965 lower clause and adds no triangles. Attribute preservation does not certify retained cuff surfaces or any glove/cuff join.','visibleJoinStatus':'Hood/cuff/hem references are separate and unsewn; no join/contact gate.','limits':'Parent byte/JSON/topology checks only. Unrigged/unbaked; no fullbody/face score, motion, new weights/rig, actual Garage/contact/mobile or production pass.'}
(E/'parent-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'verifiedFiles':len(verified),'nonmanifold':nonmanifold,'boundaryComponents':components,'protectedDonorPrefixesExact':True}))
