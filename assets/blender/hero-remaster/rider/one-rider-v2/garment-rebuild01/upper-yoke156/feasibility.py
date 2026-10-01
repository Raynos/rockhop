"""One whole-face upper-yoke selection, no source cutting/sculpting or exports."""
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np,json,struct,hashlib
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/upper-yoke156';RUN=ROOT/'garment-rebuild01/upper-yoke156'
source=ROOT/'rig-adapter01/body-bind34/rider.glb';raw=source.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 assert 'byteStride' not in v and 'sparse' not in a
 return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
p=doc['meshes'][0]['primitives'][0];P=acc(p['attributes']['POSITION']);T=acc(p['indices']).reshape(-1,3);SP,inv=np.unique(P,axis=0,return_inverse=True);ST=inv[T];f=np.load(ROOT/'garment-rebuild01/cage04/fit04.npz');NP=f['positions'];Q=f['quads']
height=1.20;sourceFaces=np.where(P[T,1].min(1)>height)[0];nativeKeep=np.where(NP[Q,1].max(1)<=height)[0]
def uses(faces):
 out=defaultdict(list)
 for i,face in enumerate(faces):
  for k in range(len(face)):a,b=int(face[k]),int(face[(k+1)%len(face)]);out[tuple(sorted([a,b]))].append((i,a,b))
 return out
def boundaryAudit(points,faces):
 e=uses(faces);edges=[pair for pair,u in e.items() if len(u)==1];adj=defaultdict(set)
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 pending=set(adj);loops=[]
 while pending:
  a=min(pending);seen=set();stack=[a]
  while stack:
   v=stack.pop()
   if v in seen:continue
   seen.add(v);stack.extend(adj[v]-seen)
  pending-=seen;ordered=[]
  if all(len(adj[v])==2 for v in seen):
   prev=None;cur=min(seen)
   for _ in range(len(seen)):ordered.append(cur);nxt=min(adj[cur]-({prev} if prev is not None else set()));prev,cur=cur,nxt
   assert cur==ordered[0]
   if tuple(ordered[:2])!=e[tuple(sorted(ordered[:2]))][0][1:]:ordered=list(reversed(ordered))
  loops.append({'vertices':len(seen),'degreeHistogram':dict(Counter(len(adj[v]) for v in seen)), 'vertexIDs':sorted(seen),'orderedBoundaryFaceWinding':ordered,'centroid':points[list(seen)].mean(0).tolist(),'bounds':[points[list(seen)].min(0).tolist(),points[list(seen)].max(0).tolist()]})
 return {'faces':len(faces),'nonmanifoldEdges':sum(len(u)>2 for u in e.values()),'loops':sorted(loops,key=lambda r:-r['vertices'])}
s=boundaryAudit(SP,ST[sourceFaces]);c=boundaryAudit(NP,Q[nativeKeep]);removedIDs=np.where(~np.isin(np.arange(len(Q)),nativeKeep))[0];nativeYoke=boundaryAudit(NP,Q[removedIDs]);neck=[r for r in s['loops'] if r['vertices']==307 and r['bounds'][0][1]>1.35]
report={'status':'Single explicit upper-yoke boundary feasibility; no exported character','sourceSHA256':hashlib.sha256(raw).hexdigest(),'cageSHA256':hashlib.sha256((ROOT/'garment-rebuild01/cage04/fit04.npz').read_bytes()).hexdigest(),'settings':{'heightM':height,'sourceKeep':'Whole original body0 triangles, all corners strictly above1.20m. No vertex clipping or planar cut. Hood lower boundary min1.355m stays exact.','nativeKeep':'Whole original cage04 quads, all corners at/below1.20m. Geometry, weights and UV retained exact outside explicit removed panel.'},'sourceRetainedTriangleIDs':sourceFaces.tolist(),'nativeRetainedQuadIDs':nativeKeep.tolist(),'nativeRemovedQuadIDs':np.where(~np.isin(np.arange(len(Q)),nativeKeep))[0].tolist(),'sourceYoke':s,'nativeRemaining':c,'nativeUpperYoke':nativeYoke,'source307ProtectedLoopIdentified':len(neck)==1,'sourceFourBoundaryYokeFeasible':len(s['loops'])==4 and all(r['orderedBoundaryFaceWinding'] for r in s['loops']),'nativeFourBoundaryYokeFeasible':len(nativeYoke['loops'])==4 and all(r['orderedBoundaryFaceWinding'] for r in nativeYoke['loops']),'expectedInterfaces':'Source4 loops (hood/chest/Larm/Rarm), native3 matching chest/Larm/Rarm plus existing unrelated hem/cuffs/jeans openings.','sourceBytesUnchanged':source.read_bytes()==raw}
(OUT/'boundary-feasibility.json').write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(RUN/'boundary-instrument.npz',sourcePositions=SP,sourceTriangles=ST,sourceInverse=inv,sourceRetainedTriangleIDs=sourceFaces,nativeRetainedQuadIDs=nativeKeep)
print(json.dumps({'sourceLoops':[{k:v for k,v in r.items() if k not in ['vertexIDs','orderedBoundaryFaceWinding']} for r in s['loops']], 'nativeLoops':[{k:v for k,v in r.items() if k not in ['vertexIDs','orderedBoundaryFaceWinding']} for r in c['loops']],'sourceProtected307':len(neck)==1},indent=2))
