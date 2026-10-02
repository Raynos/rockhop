"""Read-only necessary bounds on literal A189 left scope; no geometry trial."""
from pathlib import Path
from collections import defaultdict
import struct,json,hashlib,heapq,time,subprocess,re,os
START=time.monotonic();R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/armhole-design190';O=B/'armhole-design190';pins={}
def read(p):
 b=p.read_bytes();pins[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def check():
 assert time.monotonic()-START<590
 s=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',s).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',s).group(1))*page/1e9;assert gb<70;return gb
mem=[check()];source=B/'source-preserving-garment185/operator/rider.glb';raw=read(source);assert pins[str(source)]['sha256']=='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];w={'VEC3':3,'SCALAR':1}[a['type']];fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']];size=struct.calcsize(fmt)*w;off=v.get('byteOffset',0)+a.get('byteOffset',0);return [struct.unpack_from('<'+fmt*w,binary,off+k*v.get('byteStride',size)) for k in range(a['count'])]
p=doc['meshes'][0]['primitives'][0];P=acc(p['attributes']['POSITION']);flat=[x[0] for x in acc(p['indices'])];F=[tuple(flat[i:i+3]) for i in range(0,len(flat),3)];U=sorted(set(P));index={x:i for i,x in enumerate(U)};q=[index[x] for x in P];PF=[tuple(q[i] for i in f) for f in F];scopePath=B/'source-axilla189/positiveZ_lateral-proposed-strip.json';scope=json.loads(read(scopePath));reportPath=R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189/report.json';report=json.loads(read(reportPath));connection=next(x for x in report['firstConnections'] if x['geometricSide']=='positiveZ_lateral');removed=set(scope['sourceFaceIDs']);edgefaces=defaultdict(list);outside=defaultdict(set);inside=defaultdict(set)
for fi,t in enumerate(PF):
 for k in range(3):
  a,b=t[k],t[(k+1)%3];e=tuple(sorted((a,b)));edgefaces[e].append(fi);g=inside if fi in removed else outside;g[a].add(b);g[b].add(a)
def minimax(g,start,target):
 d={start:U[start][1]};prev={};heap=[(d[start],start)]
 while heap:
  c,i=heapq.heappop(heap)
  if c!=d[i]:continue
  if i==target:break
  for j in sorted(g[i]):
   nc=max(c,U[j][1])
   if nc<d.get(j,float('inf')):d[j]=nc;prev[j]=i;heapq.heappush(heap,(nc,j))
 if target not in d:return None
 path=[target]
 while path[-1]!=start:path.append(prev[path[-1]])
 return d[target],path[::-1]
start,target=connection['pathPhysicalIDs'][0],connection['pathPhysicalIDs'][-1];outsidePath=minimax(outside,start,target)
def witness(path):return [{'physicalIDs':[a,b],'positionsM':[U[a],U[b]],'retainedIncidentSourceFaces':[i for i in edgefaces[tuple(sorted((a,b)))] if i not in removed]} for a,b in zip(path,path[1:])]
critical=connection['criticalPhysicalVertexIDs'][0];dist={critical:0.0};prev={};heap=[(0,critical)]
while heap:
 d,i=heapq.heappop(heap)
 if d!=dist[i]:continue
 for j in sorted(inside[i]):
  nd=d+sum((x-y)**2 for x,y in zip(U[i],U[j]))**.5
  if nd<dist.get(j,float('inf')):dist[j]=nd;prev[j]=i;heapq.heappush(heap,(nd,j))
bounds=[]
for height in [1.30,1.32]:
 dy=height-U[critical][1];radius=(.14**2-dy**2)**.5;best=None
 for b in scope['boundaryPhysicalVertexIDs']:
  horiz=((U[b][0]-U[critical][0])**2+(U[b][2]-U[critical][2])**2)**.5
  mind=(max(0,horiz-radius)**2+(height-U[b][1])**2)**.5
  ratio=mind/dist[b]
  if best is None or ratio>best['necessaryMaximumEdgeRatio']:
   path=[b]
   while path[-1]!=critical:path.append(prev[path[-1]])
   best={'targetY_M':height,'criticalPhysicalID':critical,'criticalPositionM':U[critical],'verticalDisplacementM':dy,'remainingHorizontalDisplacementRadiusM':radius,'fixedBoundaryPhysicalID':b,'fixedBoundaryPositionM':U[b],'shortestOriginalInScopePathLengthM':dist[b],'minimumPossibleMovedEndpointDistanceM':mind,'necessaryMaximumEdgeRatio':ratio,'pathPhysicalIDs':path[::-1],'pathEdges':[{'physicalIDs':[a,b],'lengthM':sum((x-y)**2 for x,y in zip(U[a],U[b]))**.5,'sourceIncidentFaces':edgefaces[tuple(sorted((a,b)))]} for a,b in zip(path[::-1],path[::-1][1:])],'maximumTargetYAt1_5RatioM':U[b][1]+1.5*dist[b],'requiredPathLengthAt1_5RatioM':mind/1.5}
 bounds.append(best)
cycles=[{'nodes':len(c['orderedPhysicalP0IDs']),'rangesM':[[min(x[i] for x in c['orderedPositionsM']),max(x[i] for x in c['orderedPositionsM'])] for i in range(3)]} for c in scope['orderedSourceBoundaryCycles']];result={'status':'READONLY_NECESSARY_BOUND_TEST_NO_GEOMETRY','sourceSHA256':pins[str(source)]['sha256'],'scopeSHA256':pins[str(scopePath)]['sha256'],'cycles':cycles,'outsideWitness':None if outsidePath is None else {'maximumSourceY_M':outsidePath[0],'pathNodeCount':len(outsidePath[1]),'pathPhysicalIDs':outsidePath[1],'edges':witness(outsidePath[1]),'consequence':'All path edges have a retained incident face. Exact retained faces force a torso/lateral sublevel connection at or below this Y under every allowed interior edit.'},'fixedBoundaryPathBounds':bounds,'boundAssumptions':'Only the critical source vertex moves to the stated Y, displacement <=140mm, fixed boundary and original patch edges. Endpoint distance is minimized over the full allowed horizontal disk. Triangle inequality forces at least this ratio somewhere on the shortest literal source path. Not an area/folding proof, and not applicable after explicit path-edge removal.','inputs':pins,'runtimeSeconds':time.monotonic()-START,'anonymousGBSamples':mem+[check()],'geometryGenerated':False,'solverRun':False,'cpuThreadLimits':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS']}}
(O/'literal-bound-witness.json').write_text(json.dumps(result,indent=2)+'\n');compact=dict(result);compact['outsideWitness']={k:v for k,v in result['outsideWitness'].items() if k not in ['edges','pathPhysicalIDs']} if outsidePath else None
(E/'report.json').write_text(json.dumps(compact,indent=2)+'\n');assert source.read_bytes()==raw;print(json.dumps(compact))
