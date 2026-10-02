"""Read-only exact source chart, contour-rooted panel and seam inventory."""
from pathlib import Path
from collections import defaultdict
import struct,json,hashlib,heapq,time,subprocess,re,os
START=time.monotonic();R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-seam191';O=B/'source-seam191';pins={}
def read(p):
 b=p.read_bytes();pins[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def check():
 assert time.monotonic()-START<590
 s=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',s).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',s).group(1))*page/1e9;assert gb<70;return gb
mem=[check()];source=B/'source-preserving-garment185/operator/rider.glb';raw=read(source);assert pins[str(source)]['sha256']=='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];w={'VEC2':2,'VEC3':3,'SCALAR':1}[a['type']];fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']];size=struct.calcsize(fmt)*w;off=v.get('byteOffset',0)+a.get('byteOffset',0);return [struct.unpack_from('<'+fmt*w,binary,off+k*v.get('byteStride',size)) for k in range(a['count'])]
p=doc['meshes'][0]['primitives'][0];P=acc(p['attributes']['POSITION']);flat=[x[0] for x in acc(p['indices'])];F=[tuple(flat[i:i+3]) for i in range(0,len(flat),3)];U=sorted(set(P));index={x:i for i,x in enumerate(U)};q=[index[x] for x in P];PF=[tuple(q[i] for i in f) for f in F];
scopePath=B/'source-axilla189/positiveZ_lateral-proposed-strip.json';scope=json.loads(read(scopePath));prereg=json.loads(read(E/'preregister.json'));section=json.loads(read(B/'source-axilla189/section-fixed-03.json'));assert section['heightY_M']==1.13
UV=acc(p['attributes']['TEXCOORD_0']);chosen=set(scope['sourceFaceIDs']);boundary=set(scope['boundaryPhysicalVertexIDs']);edgefaces=defaultdict(list);faceUV=[];normals=[];outside=defaultdict(set)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(v):return sum(x*x for x in v)**.5
for fi,t in enumerate(PF):
 faceUV.append({q[row]:UV[row] for row in F[fi]});a,b,c=[U[v] for v in t];n=cross(tuple(y-x for x,y in zip(a,b)),tuple(y-x for x,y in zip(a,c)));l=length(n);normals.append(tuple(x/l for x in n) if l else (0,0,0))
 for k in range(3):
  a,b=t[k],t[(k+1)%3];edgefaces[tuple(sorted((a,b)))].append(fi)
  if fi not in chosen and U[a][1]<1.30 and U[b][1]<1.30:outside[a].add(b);outside[b].add(a)
roots={}
for loop in section['loops']:
 if loop['geometricClass'] not in ['central_Z0_straddling','positiveZ_lateral']:continue
 roots[loop['geometricClass']]=sorted({v for seg in loop['segments'] for ep in seg['endpoints'] for v in ep.get('sourcePhysicalEdge',[]) if U[v][1]<1.13})
labels=defaultdict(set);components=[];seen=set()
for root in sorted(outside):
 if root in seen:continue
 stack=[root];nodes=set()
 while stack:
  i=stack.pop()
  if i in nodes:continue
  nodes.add(i);seen.add(i);stack.extend(outside[i]-nodes)
 ancestry=[label for label,seeds in roots.items() if nodes.intersection(seeds)]
 for i in nodes:labels[i].update(ancestry)
 if nodes.intersection(boundary) or ancestry:components.append({'nodes':sorted(nodes),'ancestry':ancestry,'boundaryNodes':sorted(nodes.intersection(boundary))})
chartgraph=defaultdict(set);dual=defaultdict(list);uvseams=[]
for edge,fis in edgefaces.items():
 if len(fis)!=2:continue
 a,b=fis;continuous=all(faceUV[a][v]==faceUV[b][v] for v in edge)
 if continuous:chartgraph[a].add(b);chartgraph[b].add(a)
 elif a in chosen or b in chosen:uvseams.append({'physicalEdge':edge,'sourceFaces':fis,'cornerUVs':[[faceUV[fi][v] for v in edge] for fi in fis]})
 if a in chosen and b in chosen:
  cost=length(tuple(x-y for x,y in zip(U[edge[0]],U[edge[1]])))*(2-sum(x*y for x,y in zip(normals[a],normals[b])))*(1 if continuous else 2)
  dual[a].append((b,cost));dual[b].append((a,cost))
charts=[];chartid={};seen=set()
for root in range(len(F)):
 if root in seen:continue
 stack=[root];fs=set()
 while stack:
  i=stack.pop()
  if i in fs:continue
  fs.add(i);seen.add(i);stack.extend(chartgraph[i]-fs)
 cid=len(charts)
 for i in fs:chartid[i]=cid
 if fs.intersection(chosen):charts.append({'id':cid,'sourceFaceIDs':sorted(fs),'scopeFaces':sorted(fs.intersection(chosen))})
 else:charts.append({'id':cid,'scopeFaces':[],'sourceFaceCount':len(fs)})
seeds=defaultdict(set)
for edge,fis in edgefaces.items():
 if not set(edge).issubset(boundary):continue
 inside=[fi for fi in fis if fi in chosen];retained=[fi for fi in fis if fi not in chosen]
 if len(inside)==1 and retained:
  ancestry=labels[edge[0]].intersection(labels[edge[1]])
  if len(ancestry)==1:seeds[next(iter(ancestry))].add(inside[0])
distance={};owner={};heap=[]
for label in sorted(seeds):
 for fi in sorted(seeds[label]):
  key=(0.0,label,fi)
  if key<distance.get(fi,(float('inf'),'~',10**9)):distance[fi]=key;owner[fi]=label;heapq.heappush(heap,(*key,fi))
while heap:
 cost,label,seed,fi=heapq.heappop(heap)
 if distance[fi]!=(cost,label,seed):continue
 for nxt,w in dual[fi]:
  key=(cost+w,label,seed)
  if key<distance.get(nxt,(float('inf'),'~',10**9)):distance[nxt]=key;owner[nxt]=label;heapq.heappush(heap,(*key,nxt))
seamedges=[];sg=defaultdict(set)
for edge,fis in edgefaces.items():
 if len(fis)==2 and all(fi in chosen for fi in fis) and owner[fis[0]]!=owner[fis[1]]:
  seamedges.append({'physicalEdge':edge,'sourceFaces':fis,'owners':[owner[fi] for fi in fis],'UVContinuous':all(faceUV[fis[0]][v]==faceUV[fis[1]][v] for v in edge)});a,b=edge;sg[a].add(b);sg[b].add(a)
seamcomponents=[];seen=set()
for root in sorted(sg):
 if root in seen:continue
 stack=[root];ns=set()
 while stack:
  i=stack.pop()
  if i in ns:continue
  ns.add(i);seen.add(i);stack.extend(sg[i]-ns)
 seamcomponents.append({'physicalNodes':sorted(ns),'edges':[x for x in seamedges if x['physicalEdge'][0] in ns],'degrees':{str(i):len(sg[i]) for i in sorted(ns)},'boundaryEndpoints':sorted(ns.intersection(boundary)),'YrangeM':[min(U[i][1] for i in ns),max(U[i][1] for i in ns)],'upperBandNodes':[i for i in sorted(ns) if 1.30<=U[i][1]<=1.32]})
data={'status':'READONLY_SOURCE_CHART_AND_LITERAL_HALFEDGE_INVENTORY','inputs':pins,'scopeSourceFaces':sorted(chosen),'boundaryCycles':scope['orderedSourceBoundaryCycles'],'outsideRootComponents':components,'boundaryAncestry':{str(i):sorted(labels[i]) for i in sorted(boundary)},'UVChartsTouchingScope':[c for c in charts if c['scopeFaces']],'UVSeamsTouchingScope':uvseams,'panelSeedSourceFaces':{k:sorted(v) for k,v in seeds.items()},'geometricPanelContinuation':{str(i):{'owner':owner.get(i),'chartID':chartid[i],'sourceNormal':normals[i],'rootDistance':distance.get(i)} for i in sorted(chosen)},'prospectiveSeamComponents':seamcomponents,'anonymousGBSamples':mem+[check()],'seconds':time.monotonic()-START,'geometryGenerated':False};(O/'literal-inventory.json').write_text(json.dumps(data,indent=2)+'\n');summary={'status':data['status'],'inputs':pins,'scopeFaces':len(chosen),'boundaryCycleLengths':[len(c['orderedPhysicalP0IDs']) for c in scope['orderedSourceBoundaryCycles']],'outsideBoundaryComponents':[{'ancestry':c['ancestry'],'boundaryNodes':len(c['boundaryNodes'])} for c in components if c['boundaryNodes']],'boundaryAncestryCounts':{str(k):sum(tuple(sorted(labels[i]))==k for i in boundary) for k in sorted({tuple(sorted(labels[i])) for i in boundary})},'chartsTouchingScope':len(data['UVChartsTouchingScope']),'UVSeamsTouchingScope':len(uvseams),'panelSeeds':{k:len(v) for k,v in seeds.items()},'panelFaces':{k:sum(v==k for v in owner.values()) for k in sorted(set(owner.values()))},'seamComponents':[{'nodes':len(c['physicalNodes']),'edges':len(c['edges']),'degreeHistogram':{str(k):sum(v==k for v in c['degrees'].values()) for k in sorted(set(c['degrees'].values()))},'boundaryEndpoints':c['boundaryEndpoints'],'YrangeM':c['YrangeM'],'upperBandNodes':c['upperBandNodes']} for c in seamcomponents],'seconds':data['seconds'],'anonymousGBSamples':data['anonymousGBSamples'],'geometryGenerated':False};(E/'report.json').write_text(json.dumps(summary,indent=2)+'\n');assert source.read_bytes()==raw;print(json.dumps(summary))
# One explicit endpoint-fan obstruction for the frozen geometric continuation.
from collections import deque,Counter
lowEnd=min(seamcomponents[0]['boundaryEndpoints'],key=lambda i:U[i][1]);fan=[fi for fi,t in enumerate(PF) if lowEnd in t];added=sorted(set(fan)-chosen);nodealiases=[i for i,v in enumerate(q) if v==lowEnd];paths=[];prospectiveRibbon=set(fi for e in seamedges if min(U[i][1] for i in e['physicalEdge'])<1.30 for fi in e['sourceFaces'])
for label in sorted(roots):
 g=defaultdict(set);provenance=defaultdict(list)
 for fi,t in enumerate(PF):
  if fi in prospectiveRibbon:continue
  if fi in chosen and owner[fi]!=label:continue
  for k in range(3):
   a,b=t[k],t[(k+1)%3]
   if U[a][1]<1.30 and U[b][1]<1.30:g[a].add(b);g[b].add(a);provenance[tuple(sorted((a,b)))].append(fi)
 queue=deque([lowEnd]);prev={lowEnd:None};hit=None;targetset=set(roots[label])
 while queue:
  i=queue.popleft()
  if i in targetset:hit=i;break
  for j in sorted(g[i]):
   if j not in prev:prev[j]=i;queue.append(j)
 if hit is None:paths.append({'rootClass':label,'found':False});continue
 path=[hit]
 while prev[path[-1]] is not None:path.append(prev[path[-1]])
 path=path[::-1];paths.append({'rootClass':label,'found':True,'physicalIDs':path,'maximumY_M':max(U[i][1] for i in path),'edges':[{'physicalIDs':[a,b],'sourceFaces':provenance[tuple(sorted((a,b)))],'positionsM':[U[a],U[b]]} for a,b in zip(path,path[1:])]})
newscope=chosen.union(added);pe=defaultdict(list)
for fi in sorted(newscope):
 t=PF[fi]
 for k in range(3):a,b=t[k],t[(k+1)%3];pe[tuple(sorted((a,b)))].append((fi,a,b))
directed=[v[0] for v in pe.values() if len(v)==1];bg=defaultdict(list);ind=Counter()
for fi,a,b in directed:bg[a].append((b,fi));ind[b]+=1
valid=all(len(v)==1 and ind[a]==1 for a,v in bg.items());cycles=[];remaining=set(bg)
if valid:
 while remaining:
  start=min(remaining);i=start;ns=[];fs=[]
  while i in remaining:remaining.remove(i);ns.append(i);j,fi=bg[i][0];fs.append(fi);i=j
  assert i==start;cycles.append({'orderedPhysicalIDs':ns,'orderedPositionsM':[U[i] for i in ns],'incidentSourceFaces':fs})
oldcycle=next(c for c in scope['orderedSourceBoundaryCycles'] if lowEnd in c['orderedPhysicalP0IDs']);cy=oldcycle['orderedPhysicalP0IDs'];k=cy.index(lowEnd);arc=[cy[k-1],lowEnd,cy[(k+1)%len(cy)]]
contract={'status':'EXACT_BOUNDARY_ENDPOINT_FAN_OBSTRUCTION_TO_REGISTERED_PANEL_CUT','lowEndpointPhysicalID':lowEnd,'sourceRowAliases':nodealiases,'positionM':U[lowEnd],'originalBoundaryArcPhysicalIDs':arc,'sourceIncidentFanFaceIDs':fan,'sourceFanTriangles':[{'faceID':fi,'sourceRows':F[fi],'physicalIDs':PF[fi],'positionsM':[U[i] for i in PF[fi]],'UVs':[UV[i] for i in F[fi]],'scopeOwner':owner.get(fi)} for fi in fan],'rootedBelowTargetPaths':paths,'proofCondition':'For the registered panel continuation, retaining both rooted source panel paths and one exact physical endpoint1571 forces a central/lateral connection below1.30. Splitting only patch-side alias rows cannot remove a retained common physical point/outside fan. This is not a proof that every arbitrary annulus topology fails.','proposedReleasedFaceContract':{'baseScopeSHA256':pins[str(scopePath)]['sha256'],'addExactOriginalFaceIDs':added,'releaseOldBoundaryArcPhysicalIDs':arc,'releaseOnlyPhysicalVertex':lowEnd,'targetEndpointPositionM':[U[lowEnd][0],1.31,U[lowEnd][2]],'endpointDisplacementM':1.31-U[lowEnd][1],'unionFaces':len(newscope),'boundaryDegree2OrientedValid':valid,'boundaryCycles':cycles,'EulerCharacteristic':len({v for fi in newscope for v in PF[fi]})-len(pe)+len(newscope),'overincidentEdges':sum(len(v)>2 for v in pe.values()),'protectedRule':'All source outside union faces and all new union boundary nodes exact; expanded fan is explicitly listed, no coordinate ROI retune. No rig/weights optimized. Newly introduced corners require one-chart triangle barycentric provenance.'},'seconds':time.monotonic()-START,'anonymousGBSamples':[check()],'geometryGenerated':False}
(O/'endpoint-fan-contract.json').write_text(json.dumps(contract,indent=2)+'\n');short={k:v for k,v in contract.items() if k not in ['sourceFanTriangles','rootedBelowTargetPaths']};short['rootedBelowTargetPaths']=[{k:v for k,v in p.items() if k not in ['physicalIDs','edges']} for p in paths];short['proposedReleasedFaceContract']=dict(contract['proposedReleasedFaceContract']);short['proposedReleasedFaceContract']['boundaryCycles']=[{'nodes':len(c['orderedPhysicalIDs'])} for c in cycles];(E/'endpoint-fan-contract-summary.json').write_text(json.dumps(short,indent=2)+'\n');print(json.dumps(short))
# Exact next-construction contract, not a geometry candidate or a scope acceptance.
oldB=set(scope['boundaryPhysicalVertexIDs']);newB=set(bg);addedB=sorted(newB-oldB);removedB=sorted(oldB-newB)
unknown=sorted(i for i in boundary if not labels[i]);unknownBelow=[i for i in unknown if U[i][1]<1.30];unknownAbove=[i for i in unknown if U[i][1]>=1.30]
ordered=[];i=lowEnd;prev=None
while True:
 ordered.append(i);nexts=sorted(sg[i]-({prev} if prev is not None else set()))
 if not nexts:break
 prev,i=i,nexts[0]
assert len(ordered)==45
ribbon=sorted({fi for e in seamedges if min(U[i][1] for i in e['physicalEdge'])<1.30 for fi in e['sourceFaces']});retained={label:sorted(fi for fi in chosen if owner[fi]==label and fi not in ribbon) for label in sorted(roots)}
apex=next(i for i in reversed(ordered) if 1.30<=U[i][1]<=1.32)
newcycle=next(c for c in cycles if addedB and addedB[0] in c['orderedPhysicalIDs']);ci=newcycle['orderedPhysicalIDs'];a,b=arc[0],arc[-1];idx=ci.index(a);replacement=[a]
for step in range(len(ci)):
 nxt=ci[(idx+step+1)%len(ci)];replacement.append(nxt)
 if nxt==b:break
if len(replacement)>len(ci)//2:
 replacement=[a];idx=ci.index(a)
 for step in range(len(ci)):
  nxt=ci[(idx-step-1)%len(ci)];replacement.append(nxt)
  if nxt==b:break
extra={'orderedProspectiveSeamPhysicalIDs':ordered,'orderedPositionsM':[U[i] for i in ordered],'endpointCycleMembership':{str(i):next(k for k,c in enumerate(scope['orderedSourceBoundaryCycles']) if i in c['orderedPhysicalP0IDs']) for i in seamcomponents[0]['boundaryEndpoints']},'candidateUpperApexPhysicalID':apex,'candidateUpperApexPositionM':U[apex],'prospectiveBridgeRibbonOriginalFaceIDs':ribbon,'retainedGeometricPanelFanFaceIDs':retained,'unknownBoundaryBelowTarget':[{'physicalID':i,'positionM':U[i]} for i in unknownBelow],'unknownBoundaryAtOrAboveTarget':[{'physicalID':i,'positionM':U[i]} for i in unknownAbove],'boundaryContract':{'removedOldBoundaryPhysicalIDs':removedB,'addedNewBoundaryPhysicalIDs':addedB,'oldReleasedArcPhysicalIDs':arc,'newFixedArcPhysicalIDs':replacement,'newFixedArcPositionsM':[U[i] for i in replacement],'addedOriginalFaceIDs':added,'unionSourceFaceIDs':sorted(newscope)},'qualification':'Ribbon proposal is exactly the union of both incident original faces along below1.30 cross-owner seam edges; not yet deleted, resealed, geometrically embedded or visually accepted. Retained fan lists are geometric continuation, not garment semantic ground truth. Two rooted witnesses certify only the named fixed-endpoint obstruction.'}
(O/'next-construction-contract.json').write_text(json.dumps(extra,indent=2)+'\n');(E/'next-construction-summary.json').write_text(json.dumps({'orderedSeamNodes':len(ordered),'prospectiveRibbonFaces':len(ribbon),'retainedFanFaceCounts':{k:len(v) for k,v in retained.items()},'candidateUpperApexPhysicalID':apex,'candidateUpperApexPositionM':U[apex],'unknownBoundaryBelowTarget':extra['unknownBoundaryBelowTarget'],'unknownBoundaryAtOrAboveTargetCount':len(unknownAbove),'boundaryContract':{k:v for k,v in extra['boundaryContract'].items() if k!='unionSourceFaceIDs'}},indent=2)+'\n');print(json.dumps({'ribbonFaces':len(ribbon),'retainedFans':{k:len(v) for k,v in retained.items()},'apex':(apex,U[apex]),'unknownBelow':unknownBelow,'unknownAboveCount':len(unknownAbove),'oldArc':arc,'newArc':replacement,'addedBoundary':addedB,'removedBoundary':removedB}))
rims={}
for label,faces in retained.items():
 fs=set(faces);es=[];g=defaultdict(set)
 for edge,fis in edgefaces.items():
  if set(fis).intersection(ribbon) and set(fis).intersection(fs):
   es.append({'physicalEdge':edge,'ribbonSourceFaces':sorted(set(fis).intersection(ribbon)),'retainedSourceFaces':sorted(set(fis).intersection(fs)),'endpointPositionsM':[U[i] for i in edge]});a,b=edge;g[a].add(b);g[b].add(a)
 rims[label]={'halfedges':es,'nodeDegrees':{str(i):len(v) for i,v in sorted(g.items())},'boundaryEndpointPhysicalIDs':sorted(set(g).intersection(boundary)),'branchNodes':[i for i,v in g.items() if len(v)>2]}
extra['prospectiveLongitudinalRims']=rims;(O/'next-construction-contract.json').write_text(json.dumps(extra,indent=2)+'\n');print(json.dumps({'rims':{k:{'edges':len(v['halfedges']),'branchNodes':v['branchNodes'],'boundaryEndpoints':v['boundaryEndpointPhysicalIDs']} for k,v in rims.items()}}))
