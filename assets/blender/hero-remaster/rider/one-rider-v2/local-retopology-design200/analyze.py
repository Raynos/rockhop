"""Read-only literal local annulus/domain/atlas proof, never create geometry."""
from pathlib import Path
from collections import defaultdict, Counter
import ast, gzip, hashlib, heapq, json, re, struct, subprocess, time
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/local-retopology-design200'
sha=lambda b:hashlib.sha256(b).hexdigest(); pins={}; start=time.monotonic()
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();s=sha(b);assert h is None or h==s
 pins[str(p)]={'sha256':s,'bytes':len(b)};return b
def memory():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',s).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',s).group(1))*page/1e9
 assert gb<70 and time.monotonic()-start<590;return gb
def save(n,d): (E/n).write_text(json.dumps(d,indent=2)+'\n')
mem=[memory()];base=R/'docs/evidence/hero-remaster/one-rider-v2'
for rel in ['foundation-repair-task3/current-construction03-checkpoint.txt','foundation-repair-task3/Sculpt179-bounded-repair-guidance.txt','foundation-repair-task3/Construction21-current-status.txt','local-shell199/README.md','local-shell199/parent-review.json','local-shell199/parent-construction-contract200.json','anatomical-field-design196/parent-review197-final.json','physical-cut193/parent-review.json','physical-cut193/domain-source-comparison-summary.json','source-ruled194/parent-review.json']:
 pin(base/rel)
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py'
cl=next(n for n in ast.parse(pin(reader)).body if isinstance(n,ast.ClassDef) and n.name=='GLB')
exec(compile(ast.Module(body=[cl],type_ignores=[]),str(reader),'exec'),globals())
source=B/'source-preserving-garment185/operator/rider.glb';h='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';pin(source,h);g=GLB(source,h)
a,F=g.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);PF=q[F]
contract=json.loads(pin(B/'source-seam191/next-construction-contract.json'))
pin(B/'source-seam191/literal-inventory.json');pin(B/'source-axilla189/positiveZ_lateral-proposed-strip.json')
section=json.loads(pin(B/'source-axilla189/section-fixed-03.json'))
fields=json.loads(gzip.decompress(pin(base/'source-weight-audit194/source-fields.json.gz')))
old=set(contract['boundaryContract']['unionSourceFaceIDs']);assert len(old)==1233
scope=old|{3823,3824};assert len(scope)==1235
star=set(json.loads((base/'physical-cut193/parent-review.json').read_bytes())['removedSourceFaceIDs']);assert star<=scope
all_edges=defaultdict(list);local_edges=defaultdict(list);rows=defaultdict(list)
for row,i in enumerate(q):rows[int(i)].append(row)
uv=a['TEXCOORD_0'];face_uv=[{int(q[row]):uv[row] for row in t} for t in F]
chart_adj=defaultdict(set)
for fi,t in enumerate(PF):
 for k in range(3):
  i,j=map(int,[t[k],t[(k+1)%3]]);edge=tuple(sorted((i,j)));all_edges[edge].append((i,j,fi))
  if fi in scope:local_edges[edge].append((i,j,fi))
for edge,rr in all_edges.items():
 if len(rr)==2:
  f0,f1=rr[0][2],rr[1][2]
  if all(np.array_equal(face_uv[f0][i],face_uv[f1][i])for i in edge):chart_adj[f0].add(f1);chart_adj[f1].add(f0)
unseen=set(range(len(F)));chart={};chart_id=0
while unseen:
 stack=[min(unseen)];seen=set()
 while stack:
  fi=stack.pop()
  if fi in seen:continue
  seen.add(fi);stack.extend(chart_adj[fi]-seen)
 unseen-=seen
 for fi in seen:chart[fi]=chart_id
 chart_id+=1
directed=[rr[0]for rr in local_edges.values()if len(rr)==1];nxt={};ind=Counter()
for i,j,fi in directed:assert i not in nxt;nxt[i]=(j,fi);ind[j]+=1
assert all(ind[i]==1 for i in nxt)
remaining=set(nxt);cycles=[]
while remaining:
 st=min(remaining);i=st;ids=[];edges=[]
 while i in remaining:
  remaining.remove(i);ids.append(i);j,fi=nxt[i];outside=[r for r in all_edges[tuple(sorted((i,j)))]if r[2]not in scope]
  assert len(outside)==1 and outside[0][:2]==(j,i)
  edges.append({'directedPhysicalIDs':[i,j],'removedIncidentSourceFace':fi,'retainedIncidentSourceFace':outside[0][2],'removedSourceChartID':chart[fi],'retainedSourceChartID':chart[outside[0][2]],'sourceCornerRows':[int(F[fi,np.flatnonzero(PF[fi]==v)[0]])for v in [i,j]]});i=j
 assert i==st
 cycles.append({'orderedPhysicalIDs':ids,'positionsM':U[ids].tolist(),'directedHalfedges':edges})
assert sorted(len(c['orderedPhysicalIDs'])for c in cycles)==[62,89]
def projected_crossings(points,axes):
 p=points[:,axes]; pairs=[]
 cross=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
 for i in range(len(p)):
  a=p[i];u=p[(i+1)%len(p)]-a
  for j in range(i+1,len(p)):
   if j==i+1 or (i==0 and j==len(p)-1):continue
   b=p[j];v=p[(j+1)%len(p)]-b;den=cross(u,v)
   if abs(den)<=1e-14:continue
   t=cross(b-a,v)/den;w=cross(b-a,u)/den
   if 1e-10<t<1-1e-10 and 1e-10<w<1-1e-10:pairs.append({'edgeIndices':[i,j],'fractions':[t,w]})
 return pairs
for c in cycles:
 p=np.array(c['positionsM']);centre=p.mean(0);_,sv,vh=np.linalg.svd(p-centre,full_matrices=False)
 residual=np.einsum('ij,j->i',p-centre,vh[-1],optimize=False)
 c['geometryFacts']={'axisBoundsM':[p.min(0).tolist(),p.max(0).tolist()],
 'closedSourcePolylineLengthM':float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum()),
 'bestFitPlaneCentreM':centre.tolist(),'bestFitPlaneUnitNormal':vh[-1].tolist(),
 'bestFitPlaneMaximumResidualM':float(abs(residual).max()),'singularValuesM':sv.tolist(),
 'projectionProperNonadjacentCrossings':{name:projected_crossings(p,axes)for name,axes in [('XY',[0,1]),('XZ',[0,2]),('YZ',[1,2])]},
 'projectionMeaning':'Strict interior segment crossings only, with1e-14 determinant and1e-10 endpoint guards. Nonzero counts prove multi-valued projections; zero counts do not certify injectivity because collinear overlaps/endpoint touches are not counted.'}
 high={i for i in range(len(p))if p[i,1]>=1.30};runs=[]
 while high:
  st=next((i for i in sorted(high)if (i-1)%len(p)not in high),min(high));run=[];i=st
  while i in high:high.remove(i);run.append(i);i=(i+1)%len(p)
  runs.append({'orderedBoundaryIndices':run,'physicalIDs':[c['orderedPhysicalIDs'][i]for i in run]})
 c['sourceHighBoundaryRunsYGE1_30']=runs
roots={loop['geometricClass']:{int(i)for s in loop['segments']for ep in s['endpoints']for i in ep.get('sourcePhysicalEdge',[])if U[i,1]<1.13}for loop in section['loops']}
outside_graph=defaultdict(set)
for edge,rr in all_edges.items():
 if any(r[2]not in scope for r in rr):i,j=edge;outside_graph[i].add(j);outside_graph[j].add(i)
low=set(i for i in outside_graph if U[i,1]<1.30);left=low.copy();labels={};components=[]
while left:
 stack=[min(left)];seen=set()
 while stack:
  i=stack.pop()
  if i in seen:continue
  seen.add(i);stack.extend((outside_graph[i]&low)-seen)
 left-=seen;names=sorted(n for n,ids in roots.items()if seen&ids)
 for i in seen:labels[i]=names
 boundary_nodes=sorted(seen&set(nxt))
 if boundary_nodes:components.append({'sourcePhysicalIDs':sorted(seen),'rootLabels':names,'boundaryPhysicalIDs':boundary_nodes})
assert all(not({'central_Z0_straddling','positiveZ_lateral'}<=set(c['rootLabels']))for c in components)
target=roots['positiveZ_lateral'];dist={};prev={};heap=[]
for i in sorted(roots['central_Z0_straddling']):dist[i]=float(U[i,1]);prev[i]=None;heapq.heappush(heap,(dist[i],i))
hit=None
while heap:
 d,i=heapq.heappop(heap)
 if d!=dist[i]:continue
 if i in target:hit=i;break
 for j in sorted(outside_graph[i]):
  v=max(d,float(U[j,1]))
  if v<dist.get(j,float('inf')):dist[j]=v;prev[j]=i;heapq.heappush(heap,(v,j))
path=[]
if hit is not None:
 path=[hit]
 while prev[path[-1]]is not None:path.append(prev[path[-1]])
 path.reverse()
cuff={r['physicalSourceID']for r in fields['leftGloveBodyCuffRecords']};nodes=set(map(int,PF[sorted(scope)].ravel()));assert not cuff&nodes
p2,_=g.primitive(0,2);lookup={tuple(v):i for i,v in enumerate(U)};hood={lookup[tuple(v)]for v in p2['POSITION']if tuple(v)in lookup};hood_touch=sorted(hood&nodes)
landmarks=[1488,13448,1420,13550,12815,13219,12928,1571,1380,1543,8238]
record={'sourceSHA256':h,'physicalIDConvention':'np.unique source185 p0 Float32 POSITION lexicographic equality','proposedSourceFaceIDs':sorted(scope),'additionalSourceFaceIDs':[3823,3824],'sourceStar168IsSubset':True,'sourcePhysicalIDs':sorted(nodes),'orderedBoundaryRings':cycles,'outsideBelow1_30ComponentsTouchingBoundary':components,'boundaryRootLabels':{str(i):labels.get(i,[])for i in sorted(nxt)},'originalCuff65ProtectedIDs':sorted(cuff),'hoodSharedPhysicalIDsTouchingDomain':hood_touch,'attachmentLandmarks':[{'physicalID':i,'positionM':U[i].tolist(),'allSourceP0Rows':rows[i],'fixedBoundary':i in nxt,'sourceDomainIncidentFaces':[fi for fi in sorted(scope)if i in PF[fi]]}for i in landmarks],'outsideRetainedMinimaxAttachment':{'found':hit is not None,'heightY_M':dist[hit]if hit is not None else None,'physicalPath':path,'pathPositionsM':U[path].tolist()},'sourceChartAndCornerProvenance':[{'sourceFaceID':fi,'sourceChartID':chart[fi],'originalCornerRows':F[fi].tolist(),'physicalCornerIDs':PF[fi].tolist(),'sourceUV':uv[F[fi]].tolist(),'sourceNormals':a['NORMAL'][F[fi]].tolist()}for fi in sorted(scope)]}
seam_ids=contract['orderedProspectiveSeamPhysicalIDs'];sp=U[seam_ids].astype(float);lengths=np.linalg.norm(np.diff(sp,axis=0),axis=1);cumulative=np.r_[0,np.cumsum(lengths)]
record['original45NodeSeamReference']={'orderedPhysicalIDs':seam_ids,'positionsM':sp.tolist(),'originalEdgeLengthsM':lengths.tolist(),'cumulativeSourceLengthM':cumulative.tolist(),'totalSourceLengthM':float(cumulative[-1]),'everyNodeInside1235':all(i in nodes for i in seam_ids),'endpointsNowInterior':all(i not in nxt for i in [seam_ids[0],seam_ids[-1]]),'use':'Reference fold direction/ancestry only, not lift targets or length-matched ruled interpolation.'}
old_boundary=set(json.loads((base/'physical-cut193/parent-review.json').read_text())['orientedFillBoundaryPhysicalIDs'])
record['explicitChangedBoundaryContract']={'old193Fixed78NowReleasedInteriorIDs':sorted((old_boundary&nodes)-set(nxt)),'old193Fixed78StillFixedNewBoundaryIDs':sorted(old_boundary&set(nxt)),'newFixed151BoundaryIDs':sorted(nxt),'all542SourceInteriorIDsAvailableOnlyAfterParentRegistration':sorted(nodes-set(nxt))}
correspondence={}
for label,fs in contract['retainedGeometricPanelFanFaceIDs'].items():
 graph=defaultdict(list)
 for fi in fs:
  for k in range(3):i,j=map(int,[PF[fi,k],PF[fi,(k+1)%3]]);w=float(np.linalg.norm(U[i].astype(float)-U[j]));graph[i].append((j,w));graph[j].append((i,w))
 target_boundary=set(nxt)&set(graph);best={};parent={};queue=[]
 for i in sorted(target_boundary):best[i]=(0.0,i);parent[i]=None;heapq.heappush(queue,(0.0,i,i))
 while queue:
  d,root,i=heapq.heappop(queue)
  if best[i]!=(d,root):continue
  for j,w in sorted(graph[i]):
   test=(d+w,root)
   if test<best.get(j,(float('inf'),10**9)):best[j]=test;parent[j]=i;heapq.heappush(queue,(*test,j))
 table=[]
 for i in seam_ids:
  route=[i]if i in best else []
  while route and parent[route[-1]]is not None:route.append(parent[route[-1]])
  table.append({'seamPhysicalID':i,'found':i in best,'boundaryPhysicalID':best[i][1]if i in best else None,'sourcePanelPathLengthM':best[i][0]if i in best else None,'sourcePanelPhysicalPath':route})
 correspondence[label]=table
record['sourcePanelGeodesicBoundaryCorrespondence']=correspondence
save('source-domain-boundaries.json',record)
report={'status':'READONLY_NEW_LOCAL_RETOPOLOGY_DOMAIN_NOT_GEOMETRY_APPROVAL','sourceSHA256':h,'geometryAttempts':0,'weightsComputed':0,'solverRuns':0,'exports':0,'GPUWork':False,'domainFaces':len(scope),'physicalNodes':len(nodes),'physicalEdges':len(local_edges),'EulerCharacteristic':len(nodes)-len(local_edges)+len(scope),'overincidentEdges':sum(len(rr)>2 for rr in local_edges.values()),'orderedBoundaryLengths':[len(c['orderedPhysicalIDs'])for c in cycles],'boundaryYRangesM':[[float(U[c['orderedPhysicalIDs'],1].min()),float(U[c['orderedPhysicalIDs'],1].max())]for c in cycles],'sourceChartsTouchingDomain':sorted({chart[fi]for fi in scope}),'cuffDomainIntersection':len(cuff&nodes),'hoodSharedDomainIntersection':len(hood_touch),'oldSeamEndpointsNowInterior':all(i in nodes and i not in nxt for i in [1571,12928]),'retainedOutsideFirstAttachmentY_M':dist[hit]if hit is not None else None,'boundaryAncestryCounts':dict(Counter(tuple(labels.get(i,[]))for i in nxt)),'inputPins':pins,'seconds':time.monotonic()-start,'anonymousGBSamples':mem+[memory()]}
report['boundaryAncestryCounts']={','.join(k):v for k,v in report['boundaryAncestryCounts'].items()}
save('report.json',report)
for p,row in pins.items():assert sha(Path(p).read_bytes())==row['sha256']
print(json.dumps({k:v for k,v in report.items()if k!='inputPins'}))
