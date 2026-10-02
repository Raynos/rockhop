"""One registered read-only physical mincut with in-scope source fan completion."""
from pathlib import Path
from collections import defaultdict,Counter,deque
import ast,hashlib,json,struct,time,subprocess,re,sys
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193';O=B/'physical-cut193';EXT=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/panel-surgery192');start=time.monotonic();pins={};memory=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();v=sha(b);assert h is None or v==h;pins[str(p)]={'sha256':v,'bytes':len(b)};return b
def save(p,x):p.write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
def check():
 assert time.monotonic()-start<590
 txt=subprocess.check_output(['vm_stat'],text=True);pg=int(re.search(r'page size of (\d+)',txt).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',txt).group(1))*pg/1e9;assert gb<70;memory.append(gb)
check();reg=json.loads(pin(E/'preregister.json'));ext=json.loads(pin(EXT/'next-operator-receipt.json','d696726dd830fe419f6db4ad556180fc50e3f61b316804809f4055aed0625b5e'))
for item in ext['evidence']:pin(EXT/item['file'],item['sha256'])
source=B/'source-preserving-garment185/operator/rider.glb';raw=pin(source,reg['source185SHA256']);reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';tree=ast.parse(pin(reader));cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),globals());C=GLB(source,reg['source185SHA256']);a,F=C.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);PF=q[F];contract=json.loads(pin(B/'source-seam191/next-construction-contract.json'));scope=set(contract['boundaryContract']['unionSourceFaceIDs']);assert len(scope)==1233;section=json.loads(pin(B/'source-axilla189/section-fixed-03.json'));assert section['heightY_M']==1.13;roots={}
for loop in section['loops']:
 if loop['geometricClass'] in ['central_Z0_straddling','positiveZ_lateral']:roots[loop['geometricClass']]={i for seg in loop['segments'] for ep in seg['endpoints'] for i in ep.get('sourcePhysicalEdge',[]) if U[i,1]<1.13}
edgefaces=defaultdict(list);vertexfaces=defaultdict(set);links=defaultdict(lambda:defaultdict(set))
for fi,t in enumerate(PF):
 for v in t:vertexfaces[int(v)].add(fi)
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);edgefaces[tuple(sorted((i,j)))].append(fi)
for(i,j),fs in edgefaces.items():
 if len(fs)==2:
  x,y=fs
  for v in(i,j):links[v][x].add(y);links[v][y].add(x)
def components(nodes,adj):
 remaining=set(nodes);out=[]
 while remaining:
  root=min(remaining);seen=set();stack=[root]
  while stack:
   i=stack.pop()
   if i in seen or i not in remaining:continue
   seen.add(i);stack.extend(adj.get(i,set())-seen)
  remaining-=seen;out.append(sorted(seen))
 return out
subedges={e:fs for e,fs in edgefaces.items() if U[e[0],1]<1.30 and U[e[1],1]<1.30};eligible={e for e,fs in subedges.items() if len(fs)==2 and all(fi in scope for fi in fs)};parent=list(range(len(U)))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def union(i,j):
 i,j=find(i),find(j)
 if i!=j:parent[max(i,j)]=min(i,j)
for e in sorted(subedges):
 if e not in eligible:union(*e)
componentsOfProtected=defaultdict(list)
for i in sorted({v for e in subedges for v in e}):componentsOfProtected[find(i)].append(i)
centralComp={find(i) for i in roots['central_Z0_straddling']};lateralComp={find(i) for i in roots['positiveZ_lateral']};sharedProtected=sorted(centralComp&lateralComp);cut=[];flow=None;networkRecords=[]
if not sharedProtected:
 keys=sorted(componentsOfProtected);node={key:i for i,key in enumerate(keys)};src=len(node);sink=src+1;g=[[] for _ in range(sink+1)];INF=len(eligible)+1
 def add(i,j,capacity,back=0):
  g[i].append([j,len(g[j]),capacity]);g[j].append([i,len(g[i])-1,back])
 for e in sorted(eligible):
  x,y=find(e[0]),find(e[1])
  if x!=y:add(node[x],node[y],1,1);networkRecords.append({'sourcePhysicalEdge':e,'protectedComponentIDs':[x,y]})
 for key in sorted(centralComp):add(src,node[key],INF)
 for key in sorted(lateralComp):add(node[key],sink,INF)
 sys.setrecursionlimit(10000);flow=0
 while True:
  level=[-1]*len(g);level[src]=0;queue=deque([src])
  while queue:
   i=queue.popleft()
   for j,rev,cap in g[i]:
    if cap and level[j]<0:level[j]=level[i]+1;queue.append(j)
  if level[sink]<0:break
  pos=[0]*len(g)
  def send(i,lim):
   if i==sink:return lim
   while pos[i]<len(g[i]):
    arc=g[i][pos[i]];j,rev,cap=arc
    if cap and level[j]==level[i]+1:
     sent=send(j,min(lim,cap))
     if sent:arc[2]-=sent;g[j][rev][2]+=sent;return sent
    pos[i]+=1
   return 0
  while True:
   sent=send(src,INF)
   if not sent:break
   flow+=sent
  check()
 reach={src};stack=[src]
 while stack:
  i=stack.pop()
  for j,rev,cap in g[i]:
   if cap and j not in reach:reach.add(j);stack.append(j)
 cut=[e for e in sorted(eligible) if(find(e[0])!=find(e[1])) and((node[find(e[0])] in reach)!=(node[find(e[1])] in reach))];assert len(cut)==flow
seedRemoval=set(fi for e in cut for fi in edgefaces[e]);removal=set(seedRemoval);completion=[];obstruction=None
while not sharedProtected:
 bad=[]
 for v in sorted({int(i) for fi in removal for i in PF[fi]}):
  kept=vertexfaces[v]-removal;cc=components(kept,links[v])
  if len(cc)>1:bad.append((v,cc))
 if not bad:break
 v,cc=bad[0];protected=[c for c in cc if any(fi not in scope for fi in c)]
 if len(protected)>1:
  obstruction={'physicalID':v,'sourcePositionM':U[v].tolist(),'sourceIncidentFaceIDs':sorted(vertexfaces[v]),'retainedFaceLinkSectors':cc,'protectedRetainedSectors':protected,'reason':'At least two protected/outside retained sectors; no in-scope removal can connect retained link while keeping both sectors'};break
 keep=protected[0] if protected else min(cc,key=lambda c:(-len(c),tuple(c)));added=set(fi for c in cc if c!=keep for fi in c);assert added and added<=scope;completion.append({'physicalID':v,'retainedSectorsBefore':cc,'keptSector':keep,'addedRemovedFaces':sorted(added)});removal|=added;check()
# Verify literal physical topology/link structure for the actual read-only face mask.
def auditMask(mask):
 kept=set(range(len(F)))-mask;newEdges=defaultdict(list);fa=defaultdict(set)
 for fi in sorted(mask):
  t=PF[fi]
  for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);newEdges[tuple(sorted((i,j)))].append((fi,i,j))
 boundary=[r[0] for e,r in newEdges.items() if len(r)==1];out=defaultdict(list);ind=Counter()
 for fi,i,j in boundary:out[i].append((j,fi));ind[j]+=1
 badBoundary=[{'physicalID':i,'out':len(out[i]),'in':ind[i]} for i in sorted(set(out)|set(ind)) if len(out[i])!=1 or ind[i]!=1];cycles=[];remaining=set(out)
 if not badBoundary:
  while remaining:
   root=min(remaining);i=root;cycle=[];faces=[]
   while i in remaining:remaining.remove(i);cycle.append(i);j,fi=out[i][0];faces.append(fi);i=j
   assert i==root;cycles.append({'orderedPhysicalIDs':cycle,'positionsM':U[cycle].tolist(),'removedIncidentSourceFaces':faces})
 pinches=[];sourceLinkFailures=[]
 for v in sorted(vertexfaces):
  sourceCC=components(vertexfaces[v],links[v]);retained=vertexfaces[v]-mask;cc=components(retained,links[v])
  if len(sourceCC)!=1:sourceLinkFailures.append({'physicalID':v,'sourceFaceLinkComponents':sourceCC})
  if len(cc)>1:pinches.append({'physicalID':v,'retainedFaceLinkComponents':cc})
 for e,fs in edgefaces.items():
  rr=[fi for fi in fs if fi in mask]
  if len(rr)==2:fa[rr[0]].add(rr[1]);fa[rr[1]].add(rr[0])
 dual=components(mask,fa);verts={int(v) for fi in mask for v in PF[fi]};gg=defaultdict(set)
 for e,fs in edgefaces.items():
  if any(fi in kept for fi in fs) and U[e[0],1]<1.30 and U[e[1],1]<1.30:i,j=e;gg[i].add(j);gg[j].add(i)
 reachable=set(roots['central_Z0_straddling']);stack=list(sorted(reachable))
 while stack:
  i=stack.pop()
  for j in gg[i]-reachable:reachable.add(j);stack.append(j)
 separated=not reachable.intersection(roots['positiveZ_lateral'])
 # Minimax path on whole remaining original p0 graph retains high attachment.
 import heapq
 allg=defaultdict(set)
 for e,fs in edgefaces.items():
  if any(fi in kept for fi in fs):i,j=e;allg[i].add(j);allg[j].add(i)
 d={i:float(U[i,1]) for i in roots['central_Z0_straddling']};prev={};heap=[(h,i) for i,h in d.items()];heapq.heapify(heap)
 while heap:
  h,i=heapq.heappop(heap)
  if h!=d[i]:continue
  for j in sorted(allg[i]):
   nh=max(h,float(U[j,1]))
   if nh<d.get(j,float('inf')):d[j]=nh;prev[j]=i;heapq.heappush(heap,(nh,j))
 target=min(roots['positiveZ_lateral'],key=lambda i:(d.get(i,float('inf')),i));h=d.get(target,float('inf'));path=[target]
 while path[-1] in prev:path.append(prev[path[-1]])
 return {'removedFaces':sorted(mask),'outsideScopeFaces':sorted(mask-scope),'removedEulerCharacteristic':len(verts)-len(newEdges)+len(mask),'removedEdgeDualComponents':dual,'boundaryEdgeCount':len(boundary),'badBoundaryNodes':badBoundary,'orderedBoundaryCycles':cycles,'sourceVertexLinkFailures':sourceLinkFailures,'retainedVertexLinkPinches':pinches,'centralAndLateralRootsSeparatedBelow1_30':separated,'unsealedFirstLeftAttachmentY_M':h if np.isfinite(h) else None,'unsealedMinimaxPathPhysicalIDs':path[::-1],'sourcePositionsChanged':0,'outsideRetainedFacesExact':True}
mincutAudit=auditMask(removal) if not sharedProtected else None
# Independent verification of supplied star domain by literal source ancestry.
star=set(int(fi) for fi in np.flatnonzero(np.isin(PF,contract['orderedProspectiveSeamPhysicalIDs']).any(1)));assert len(star)==168 and sorted(star-scope)==[3823,3824];assert sorted(star)==ext['nextOperator']['removedSourceFaceIDs'];starAudit=auditMask(star);assert starAudit['removedEulerCharacteristic']==1 and len(starAudit['removedEdgeDualComponents'])==1 and starAudit['boundaryEdgeCount']==78 and not starAudit['badBoundaryNodes'] and not starAudit['retainedVertexLinkPinches'];assert starAudit['unsealedFirstLeftAttachmentY_M']==1.3028745651245117
save(O/'literal-separator.json',{'sourceSHA256':sha(raw),'roots':{k:sorted(v) for k,v in roots.items()},'eligibleUnitEdges':[{'physicalEdge':e,'sourceIncidentFaces':edgefaces[e]} for e in sorted(eligible)],'protectedSublevelComponents':{str(i):v for i,v in componentsOfProtected.items()},'rootProtectedComponents':{'central':sorted(centralComp),'lateral':sorted(lateralComp)},'sharedProtectedComponents':sharedProtected,'flow':flow,'cutEdges':[{'physicalEdge':e,'sourceIncidentFaces':edgefaces[e],'positionsM':U[list(e)].tolist()} for e in cut],'seedRemovedSourceFaceIDs':sorted(seedRemoval),'fanCompletionSteps':completion,'fanCompletionObstruction':obstruction,'finalMaskAudit':mincutAudit,'externalStar168IndependentAudit':starAudit})
summary={'status':'READONLY_SEPARATOR_AND_FAN_FEASIBILITY_NO_GEOMETRY','sourceSHA256':sha(raw),'inputs':pins,'unitEligibleEdgeCount':len(eligible),'protectedSublevelComponents':len(componentsOfProtected),'finiteSeparatorExists':not bool(sharedProtected),'mincutCost':flow,'seedRemovalFaces':len(seedRemoval),'fanCompletionSteps':len(completion),'completedRemovalFaces':len(removal),'fanCompletionObstruction':obstruction,'mincutMask':None if mincutAudit is None else {k:v for k,v in mincutAudit.items() if k not in ['removedFaces','orderedBoundaryCycles','removedEdgeDualComponents','unsealedMinimaxPathPhysicalIDs']},'mincutMaskBoundaryCycleLengths':[] if mincutAudit is None else[len(c['orderedPhysicalIDs']) for c in mincutAudit['orderedBoundaryCycles']],'mincutMaskRemovedDualComponentSizes':[] if mincutAudit is None else[len(c) for c in mincutAudit['removedEdgeDualComponents']],'externalStar168Verified':{'faces':168,'outsideScopeFaces':[3823,3824],'Euler':1,'boundaryCycleLengths':[len(c['orderedPhysicalIDs']) for c in starAudit['orderedBoundaryCycles']],'retainedVertexLinkPinches':len(starAudit['retainedVertexLinkPinches']),'sourceRootSeparationBelow1_30':starAudit['centralAndLateralRootsSeparatedBelow1_30'],'unsealedAttachmentY_M':starAudit['unsealedFirstLeftAttachmentY_M'],'sourcePositionsChanged':0},'seconds':time.monotonic()-start,'anonymousGBSamples':memory,'geometryGenerated':False};assert source.read_bytes()==raw;save(E/'report.json',summary);print(json.dumps(summary),flush=True)
# Compact source-aware contract comparison; no new geometry or chart fitting.
inv=json.loads(pin(B/'source-seam191/literal-inventory.json'));chartOf={fi:c['id'] for c in inv['UVChartsTouchingScope'] for fi in c.get('sourceFaceIDs',[])};owners={int(fi):v['owner'] for fi,v in inv['geometricPanelContinuation'].items()};UV=a['TEXCOORD_0'];comparisons={}
for name,mask,au in [('physicalMincut47',removal,mincutAudit),('sourceSeamStar168',star,starAudit)]:
 if au is None or len(au['orderedBoundaryCycles'])!=1:continue
 cycle=au['orderedBoundaryCycles'][0]['orderedPhysicalIDs'];rootReach={}
 for label in sorted(roots):
  gg=defaultdict(set)
  for e,fs in edgefaces.items():
   if any(fi not in mask for fi in fs) and U[e[0],1]<1.30 and U[e[1],1]<1.30:i,j=e;gg[i].add(j);gg[j].add(i)
  reach=set(roots[label]);stack=list(sorted(reach))
  while stack:
   i=stack.pop()
   for j in gg[i]-reach:reach.add(j);stack.append(j)
  rootReach[label]=reach
 boundaryRecords=[]
 for i,j in zip(cycle,cycle[1:]+cycle[:1]):
  fs=edgefaces[tuple(sorted((i,j)))];removed=next(fi for fi in fs if fi in mask);retained=next(fi for fi in fs if fi not in mask);low=[v for v in(i,j) if U[v,1]<1.30];rootLabels=[label for label,reach in rootReach.items() if any(v in reach for v in low)];normal=np.cross(a['POSITION'][F[retained]][1].astype(float)-a['POSITION'][F[retained]][0],a['POSITION'][F[retained]][2].astype(float)-a['POSITION'][F[retained]][0]);normal/=np.linalg.norm(normal);rows=[int(F[retained][np.flatnonzero(PF[retained]==v)[0]]) for v in(i,j)];boundaryRecords.append({'removedDirectedPhysicalEdge':[i,j],'retainedDirectedPhysicalEdge':[j,i],'removedSourceFace':removed,'retainedSourceFace':retained,'belowTargetRootLabels':rootLabels,'retained191ContinuationOwner':owners.get(retained),'retainedSourceChart':chartOf.get(retained),'removedSourceChart':chartOf.get(removed),'retainedSourceNormal':normal.tolist(),'retainedSourceCornerRows':rows,'retainedCornerUVs':UV[rows].tolist(),'positionsM':U[[i,j]].tolist()})
 highs=[i for i in cycle if 1.30<=U[i,1]<=1.32];pairs=[]
 for ii,i in enumerate(highs):
  for j in highs[ii+1:]:
   k,l=cycle.index(i),cycle.index(j)
   if k>l:k,l=l,k;i,j=j,i
   arcA=boundaryRecords[k:l];arcB=boundaryRecords[l:]+boundaryRecords[:k];labelsA=set(v for e in arcA for v in e['belowTargetRootLabels']);labelsB=set(v for e in arcB for v in e['belowTargetRootLabels']);feasible=len(labelsA)==len(labelsB)==1 and labelsA!=labelsB
   if feasible:pairs.append({'physicalIDs':[i,j],'positionsM':U[[i,j]].tolist(),'sourceChordLengthM':float(np.linalg.norm(U[i].astype(float)-U[j])),'arcEdgeCounts':[len(arcA),len(arcB)],'arcRootClasses':[sorted(labelsA),sorted(labelsB)],'arcRootUnsupportedCounts':[sum(not e['belowTargetRootLabels'] for e in arcA),sum(not e['belowTargetRootLabels'] for e in arcB)],'arcRetained191UnsupportedCounts':[sum(e['retained191ContinuationOwner'] is None for e in arcA),sum(e['retained191ContinuationOwner'] is None for e in arcB)]})
 choice=min(pairs,key=lambda p:(-p['sourceChordLengthM'],tuple(p['physicalIDs']))) if pairs else None;pts=U[sorted({int(v) for fi in mask for v in PF[fi]})].astype(float);bp=U[cycle].astype(float);comparison={'domainFaces':len(mask),'exactRemovedSourceFaceIDs':sorted(mask),'outside1233SourceFaceIDs':sorted(mask-scope),'perimeterEdges':len(cycle),'perimeterSourceYspanM':[float(bp[:,1].min()),float(bp[:,1].max())],'domainAxisRangesM':[[float(pts[:,k].min()),float(pts[:,k].max())] for k in range(3)],'domainMaximumEuclideanWidthM':float(np.linalg.norm(pts[:,None]-pts[None],axis=2).max()),'chartsTouchingRemovedDomain':sorted({chartOf.get(fi) for fi in mask if chartOf.get(fi) is not None}),'retainedBoundaryCharts':sorted({e['retainedSourceChart'] for e in boundaryRecords if e['retainedSourceChart'] is not None}),'removedBoundaryCharts':sorted({e['removedSourceChart'] for e in boundaryRecords if e['removedSourceChart'] is not None}),'boundary191UnsupportedOwnerCount':sum(e['retained191ContinuationOwner'] is None for e in boundaryRecords),'belowTargetUnsupportedRootEdgeCount':sum(not e['belowTargetRootLabels'] and any(p[1]<1.30 for p in e['positionsM']) for e in boundaryRecords),'highOnlyRootUnsupportedEdges':sum(not e['belowTargetRootLabels'] and all(p[1]>=1.30 for p in e['positionsM']) for e in boundaryRecords),'allHighPerimeterNodesInTargetBand':[{'physicalID':i,'positionM':U[i].tolist()} for i in highs],'rootPureArcHighEndpointPairs':pairs,'recommendedSourceHighEndpointPair':choice,'boundarySourceAncestry':boundaryRecords,'wholeSourceAttachmentY_M':au['unsealedFirstLeftAttachmentY_M'],'noGeometryGenerated':True};comparisons[name]=comparison
save(O/'domain-source-comparison.json',comparisons);save(E/'domain-source-comparison-summary.json',{name:{k:v for k,v in c.items() if k not in ['exactRemovedSourceFaceIDs','boundarySourceAncestry','rootPureArcHighEndpointPairs','allHighPerimeterNodesInTargetBand']} for name,c in comparisons.items()});summary['inputs']=pins;save(E/'report.json',summary);print(json.dumps({name:{k:v for k,v in c.items() if k not in ['exactRemovedSourceFaceIDs','boundarySourceAncestry','rootPureArcHighEndpointPairs','allHighPerimeterNodesInTargetBand']} for name,c in comparisons.items()}),flush=True)
# Source parameter reference for the selected47face disk: no spatial mesh generated.
import math
selected=comparisons['physicalMincut47'];cycle=mincutAudit['orderedBoundaryCycles'][0]['orderedPhysicalIDs'];first,last=1420,13550;k,l=cycle.index(first),cycle.index(last);assert k<l;centralArc=cycle[k:l+1];lateralArc=(cycle[l:]+cycle[:k+1])[::-1];reference={};arcRecords={};maxBoundaryToChord=0.0
for label,arc,sign in [('central',centralArc,-1),('lateral',lateralArc,1)]:
 pts=U[arc].astype(float);lengths=np.linalg.norm(np.diff(pts,axis=0),axis=1);cum=np.concatenate([[0],np.cumsum(lengths)]);stations=cum/cum[-1];arcRecords[label]={'physicalIDs':arc,'normalizedSourceArcLengthStations':stations.tolist(),'sourceArcLengthM':float(cum[-1])}
 for physicalID,u in zip(arc,stations):
  uv=[float(u),float(sign*math.sin(math.pi*u))];uv[1]=0.0 if physicalID in[first,last] else uv[1]
  if physicalID in reference:assert np.allclose(reference[physicalID],uv,atol=1e-14)
  reference[physicalID]=uv;chord=(1-u)*U[first].astype(float)+u*U[last];maxBoundaryToChord=max(maxBoundaryToChord,float(np.linalg.norm(chord-U[physicalID])))
assert len(reference)==49 and len({int(v) for fi in removal for v in PF[fi]})==49
paramTriangles=[];parameterArea=[];sourceArea=[]
for fi in sorted(removal):
 pt=np.array([reference[int(v)] for v in PF[fi]]);aa=float(np.cross(pt[1]-pt[0],pt[2]-pt[0]))/2;parameterArea.append(aa);world=U[PF[fi]].astype(float);area=float(np.linalg.norm(np.cross(world[1]-world[0],world[2]-world[0])))/2;sourceArea.append(area);paramTriangles.append({'sourceFaceID':fi,'sourceCornerRows':F[fi].tolist(),'physicalCornerIDs':PF[fi].tolist(),'sourceChartID':chartOf[fi],'sourceReferenceCornersUV':pt.tolist(),'signedReferenceArea':aa,'sourceSpatialAreaM2':area})
lensCycle=np.array([reference[i] for i in cycle]);lensArea=float(sum(np.cross(lensCycle[i],lensCycle[(i+1)%len(lensCycle)]) for i in range(len(lensCycle))))/2;referenceClear=min(parameterArea)>1e-12 and abs(sum(parameterArea)-lensArea)<1e-12;assert referenceClear
proposal={'status':'FROZEN_PROPOSAL_ONLY_ACTUAL_TRIAL194_REQUIRES_PARENT_COMMIT','domain':'physicalMincut47','exactRemovedSourceFaceIDs':sorted(removal),'fixedOrientedBoundaryPhysicalIDs':cycle,'highSeamEndpointPhysicalIDs':[first,last],'highSeamEndpointPositionsM':U[[first,last]].tolist(),'highSeam':'Straight shared chord between1420and13550, allY1.301290512--1.305065036. Shared stations=sorted exact union of both normalizedarc stations, common endpoints collapse byphysicalID only. No bulge/tuning/parameterloop.','radialLevels':[0,1/3,2/3,1],'arcCorrespondence':arcRecords,'geometryRule':'Each panel ring point at sourcearc stationu andr is(1-r)*literal piecewise-linear sourceboundaryarc(u)+r*highchord(u). Ringr1/3,2/3 retains eacharc station list; sharedr1 uses union stations. Deterministic parameter zipper triangles, then clip each against original47reference triangles. Collapse exact common endpoints only; never discard small area/failed intersections.','sourceReference':'Existing47source triangulation embedded in a convexlens: centralarc(u,-sin(pi*u)), lateralarc(u,+sin(pi*u)); endpoints(0,0)/(1,0). Parameter-only source reference; no new3Dmesh. Existingtriangle IDs define barycentric cell locator.','referenceChecks':{'all49VerticesOnPerimeter':True,'noOriginalInteriorVertices':True,'minimumSignedTriangleArea':min(parameterArea),'triangleAreaSum':sum(parameterArea),'convexLensSignedArea':lensArea,'areaResidual':sum(parameterArea)-lensArea,'noncollapsedConsistentSourceTriangulation':referenceClear},'sourceProvenance':'Clip new parameter triangles at original47source-reference triangle edges, including chart boundaries. Every resulting corner records one exactsourceface/chart and barycentric coordinates for TEXCOORD_0/1/2,COLOR_0/1/2,sourcejointfield and both morph POSITION/NORMAL fields. No nearestrow/SVD/globalharmonicfit.','sharedPhysicalFieldRule':'At a shared parameter location select lowestID containing originalsourceface for canonical19joint/morph ancestry; all UVchart aliases use this same physical skin/morph field, while UV/color ancestry remains its own originalsinglechart face. Runtime Float32 field and aliases independently checked. Source-weight optimization is forbidden. If exactbarycentric joint support cannot be encoded in stockThree fourlanes without loss, rejectGLB preflight and retain geometrydump; no silent top4/pruning/newjoint.','normalRule':'All existingoriginal NORMAL rows unchanged. Append explicitnewNORMAL alias rows derived from candidate area-weighted incidentnewtriangles, and record exactlywhich appendedrows. Boundary newfacecorners use copiedsourceUV/skin/morph provenance and appendedlocalnormals; originaloutside aliases remain sourceexact. No static shading pass assumed.','protection':'Delete exactly47originalindices, keepall otheroriginalsource face rows/order and arrays exact; originalBIN prefix/rig19binds/head/hood/right/cuffs/lowerbody/PBR/morphmetadata exact. Appendnewaccessors only afterstaticgates. No originalposition moved, including1571.','maximumBoundaryToProposedChordCorrespondenceDistanceM':maxBoundaryToChord,'sourceRemovedTriangleAreaSumM2':sum(sourceArea),'trialLimit':'ONE194generatedconstruction only, CPU2, finite/area/winding/manifold/rootseparation/fullcrossing/singlechartprovenance/exportlegality first; rejectbeforemotion onfailure. No cropping/newcost/operatorvariant. Source2030/2172andhips remain failed.','geometricAndArtAcceptance':False,'geometryGenerated':False}
save(O/'selected-source-reference.json',{'referencePhysicalVertexUV':reference,'originalSourceTriangles':paramTriangles,'proposal':proposal});save(E/'operator-proposal.json',proposal);print(json.dumps({'sourceReferenceClear':referenceClear,'minimumReferenceArea':min(parameterArea),'sourceRemovedAreaM2':sum(sourceArea),'maximumBoundaryToChordCorrespondenceDistanceM':maxBoundaryToChord,'actualGeometryGenerated':False}),flush=True)

# Final parent-selected explicit transfer/normal policies, reproducible without a mesh trial.
proposal['sharedPhysicalFieldRule']='NEW corners only: exact dense19 barycentric source-joint interpolation at canonical lowestID containing originalsourceface; select largest4positive lanes, ties ascending originaljointordinal; Float32 renormalize by absolute lane sum as stockThree. Record discarded positive weightmass for EVERYnewcorner and keep dense19 reference. This is explicit transfer reduction, not weightfitting/artacceptance; no originalweight changed. Allphysical UVchart aliases share identicalFloat32 JOINTS_0/WEIGHTS_0 and same canonical interpolated morphs. No claim of moving accuracy from interpolation/reduction.'
proposal['normalRule']='Every original NORMAL row remains exact. Appended NORMAL rows on original fixedboundaryphysical vertices copy canonical matched retainedsourcechart corner normal; preserve and record any genuine source hard-normal alias explicitly. Interior/sharedseam physical normals are normalized area-weighted sum of incident candidate faces across both panels, cached identically across all UVchart aliases. Reject undefined/zero normal; originaloutside aliases untouched. Changedgeometry shading/PBR remains a played-film gate.'
proposal['geometryPreflight']='ONE194only. Preserve exactboundarycoordinates and originaloutsideindices. Test all actualFloat32newtriangles for nonzero/noncollapsed area, duplicatephysical corners/faces, winding/manifold/rootseparation/fullcrossing. Reject collapsed/sliver/fold/crossing construction rather than delete triangles, perturb boundary or retry parameters. Record actual newcorner displacement against its canonical source barycentric position; use140mm proposed rejection bar and retain honest boundary-to-chord envelope140.288433mm (not a proof actualnewcorner displacement exceeds140mm).'
proposal['unsupported191OwnersResolvedByLiteralRoots']=[r for r in comparisons['physicalMincut47']['boundarySourceAncestry'] if r['retained191ContinuationOwner'] is None]
save(E/'operator-proposal.json',proposal)
ref=json.loads((O/'selected-source-reference.json').read_text());ref['proposal']=proposal;save(O/'selected-source-reference.json',ref)
