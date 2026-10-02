"""Source-only47/59 cut diagnostics, no candidate construction or fitting."""
from pathlib import Path
from collections import defaultdict,Counter
import ast,hashlib,json,struct,heapq,time,subprocess,re
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/authored-panel202';sha=lambda b:hashlib.sha256(b).hexdigest();pins={};start=time.monotonic()
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();s=sha(b);assert h is None or s==h;pins[str(p)]={'sha256':s,'bytes':len(b)};return b
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n')
def check():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',s).group(1));n=int(re.search(r'Anonymous pages:\s+(\d+)',s).group(1))*page;assert n<70_000_000_000 and time.monotonic()-start<1200;return n
mem=[check()];fr=json.loads(pin(E/'freeze.json'))
for p,r in fr['files'].items():pin(p,r['sha256'])
base=R/'docs/evidence/hero-remaster/one-rider-v2';c=json.loads(pin(base/'physical-cut193/parent-construction-contract.json'));r=json.loads(pin(base/'source-ruled194/parent-review.json'));section=json.loads(pin(B/'source-axilla189/section-fixed-03.json'))
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';cl=next(n for n in ast.parse(pin(reader)).body if isinstance(n,ast.ClassDef)and n.name=='GLB');exec(compile(ast.Module(body=[cl],type_ignores=[]),str(reader),'exec'),globals());source=B/'source-preserving-garment185/operator/rider.glb';s='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';pin(source,s);g=GLB(source,s);a,F=g.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);P=q[F]
all_edges=defaultdict(list)
for fi,t in enumerate(P):
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);all_edges[tuple(sorted((i,j)))].append((fi,i,j))
# Source roots remain exact original section-edge ancestry.
roots={loop['geometricClass']:{int(i)for seg in loop['segments']for ep in seg['endpoints']for i in ep.get('sourcePhysicalEdge',[])if U[i,1]<1.13}for loop in section['loops']}
assert roots['central_Z0_straddling'] and roots['positiveZ_lateral']
whole_positions=[];whole_faces=[];whole_face_names=[]
for pi in range(3):
 aa,ff=g.primitive(0,pi);off=len(whole_positions);whole_positions.extend(aa['POSITION']);whole_faces.extend(ff+off);whole_face_names.extend((pi,i)for i in range(len(ff)))
W,ww=np.unique(np.array(whole_positions,np.float32),axis=0,return_inverse=True);WP=ww[np.array(whole_faces,np.int64)];lookup={tuple(v):i for i,v in enumerate(W)};p0_to_whole=np.array([lookup[tuple(v)]for v in U]);whole_to_p0={int(j):i for i,j in enumerate(p0_to_whole)}
wr={n:{int(p0_to_whole[i])for i in ids}for n,ids in roots.items()}
def measure(removed):
 removed=set(removed);edges=defaultdict(list);loc_edges=defaultdict(list);graph=defaultdict(set)
 for fi,t in enumerate(P):
  for k in range(3):
   i,j=map(int,[t[k],t[(k+1)%3]]);edge=tuple(sorted((i,j)))
   (loc_edges if fi in removed else edges)[edge].append((fi,i,j))
 for fidx,(t,(pi,fi))in enumerate(zip(WP,whole_face_names)):
  if pi==0 and fi in removed:continue
  for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);graph[i].add(j);graph[j].add(i)
 dist={i:float(W[i,1])for i in wr['central_Z0_straddling']};prev={i:None for i in dist};heap=[(v,i)for i,v in dist.items()];heapq.heapify(heap);hit=None
 while heap:
  v,i=heapq.heappop(heap)
  if dist[i]!=v:continue
  if i in wr['positiveZ_lateral']:hit=i;break
  for j in sorted(graph[i]):
   y=max(v,float(W[j,1]))
   if y<dist.get(j,float('inf')):dist[j]=y;prev[j]=i;heapq.heappush(heap,(y,j))
 path=[]
 if hit is not None:
  path=[hit]
  while prev[path[-1]]is not None:path.append(prev[path[-1]])
  path.reverse()
 # Literal edge support: all retained p0 faces incident to a chosen path edge.
 protected=set();path_edges=[]
 for i,j in zip(path,path[1:]):
  pi,pj=whole_to_p0.get(i),whole_to_p0.get(j);owners=[]
  if pi is not None and pj is not None:owners=[fi for fi,aa,bb in all_edges[tuple(sorted((pi,pj)))]if fi not in removed];protected.update(owners)
  path_edges.append({'wholePhysicalIDs':[i,j],'sourceP0PhysicalIDs':[pi,pj],'retainedSourceP0IncidentFaceIDs':owners})
 # Per-source-vertex retained link: a connected path (boundary) or cycle.
 incident=defaultdict(list)
 for fi,t in enumerate(P):
  if fi in removed:continue
  for k,v in enumerate(t):incident[int(v)].append(tuple(map(int,[t[(k+1)%3],t[(k+2)%3]])))
 bad=[]
 for v in sorted(set(P[sorted(removed)].ravel().tolist())):
  links=defaultdict(set)
  for i,j in incident[v]:links[i].add(j);links[j].add(i)
  if not links:continue
  left=set(links);components=0
  while left:
   stack=[min(left)];seen=set()
   while stack:
    k=stack.pop()
    if k in seen:continue
    seen.add(k);stack.extend(links[k]-seen)
   left-=seen;components+=1
  deg=Counter(len(x)for x in links.values());valid=components==1 and set(deg)<=set([1,2])and deg[1]in [0,2]
  if not valid:bad.append({'sourcePhysicalID':v,'linkComponents':components,'linkDegreeCounts':dict(deg),'sourcePositionM':U[v].tolist()})
 boundary=[x[0]for edge,x in loc_edges.items()if len(x)==1];outgoing=Counter(i for fi,i,j in boundary);incoming=Counter(j for fi,i,j in boundary);boundaryIDs=set(outgoing)|set(incoming);degreeBad=[{'physicalID':i,'outgoing':outgoing[i],'incoming':incoming[i]}for i in sorted(boundaryIDs)if outgoing[i]!=1 or incoming[i]!=1]
 cycles=[]
 if not degreeBad:
  nxt={i:j for fi,i,j in boundary};left=set(nxt)
  while left:
   st=min(left);i=st;ids=[]
   while i in left:left.remove(i);ids.append(i);i=nxt[i]
   assert i==st;cycles.append(ids)
 # Face edge-dual components of removed set.
 adj=defaultdict(set)
 for edge,rr in loc_edges.items():
  if len(rr)==2:i,j=rr[0][0],rr[1][0];adj[i].add(j);adj[j].add(i)
 left=removed.copy();fc=[]
 while left:
  stack=[min(left)];seen=set()
  while stack:
   i=stack.pop()
   if i in seen:continue
   seen.add(i);stack.extend(adj[i]-seen)
  left-=seen;fc.append(sorted(seen))
 nodes=set(P[sorted(removed)].ravel().tolist());chi=len(nodes)-len(loc_edges)+len(removed)
 return {'removedSourceFaceIDs':sorted(removed),'sourceFaces':len(removed),'sourceNodes':len(nodes),'sourceEdges':len(loc_edges),'removedEuler':chi,'removedEdgeDualComponents':fc,'cutBoundaryEdges':len(boundary),'cutBoundaryDegreeFailures':degreeBad,'orderedCutBoundaryCycles':cycles,'retainedVertexLinkFailures':bad,'firstRootedAttachmentY_M':dist[hit]if hit is not None else None,'wholePhysicalPath':path,'sourceP0PhysicalPath':[whole_to_p0.get(i)for i in path],'pathPositionsM':W[path].tolist(),'pathEdges':path_edges,'protectedRetainedP0FaceIDs':sorted(protected),'allPathSourceSupportOutsideRemoved':not protected&removed,'inside1_30_1_32Band':hit is not None and 1.30<=dist[hit]<=1.32}
old=set(c['exactRemovedSourceFaceIDs']);cross=set(r['crossedRetainedSourceFaceIDs']);assert len(old)==47 and len(cross)==12 and not old&cross
m47=measure(old);m59=measure(old|cross)
# The second59 loop bounds a literal retained two-triangle island. It is
# source-domain regularization, not removal of candidate defects.
assert sorted(map(len,m59['orderedCutBoundaryCycles']))==[4,53]
small=set(next(x for x in m59['orderedCutBoundaryCycles']if len(x)==4))
island={fi for fi,t in enumerate(P)if fi not in old|cross and set(map(int,t))<=small};assert island=={8350,8351}
assert not island&set(m59['protectedRetainedP0FaceIDs'])
m61=measure(old|cross|island);assert m61['removedEuler']==1 and len(m61['orderedCutBoundaryCycles'])==1 and not m61['retainedVertexLinkFailures'] and not m61['cutBoundaryDegreeFailures']
# Exact cut halfedges and original source-chart corner donors for next review.
sew=[]
for edge,rr in all_edges.items():
 removed=[x for x in rr if x[0]in set(m61['removedSourceFaceIDs'])];retained=[x for x in rr if x[0]not in set(m61['removedSourceFaceIDs'])]
 if len(removed)!=1 or len(retained)!=1:continue
 fi,i,j=removed[0];rfi,ri,rj=retained[0];assert (i,j)==(rj,ri)
 ir=int(F[fi,np.flatnonzero(P[fi]==i)[0]]);jr=int(F[fi,np.flatnonzero(P[fi]==j)[0]]);rir=int(F[rfi,np.flatnonzero(P[rfi]==i)[0]]);rjr=int(F[rfi,np.flatnonzero(P[rfi]==j)[0]])
 sew.append({'removedSourceFaceID':fi,'retainedSourceFaceID':rfi,'removedOrientedPhysicalEdge':[i,j],'removedSourceCornerRows':[ir,jr],'retainedSourceCornerRows':[rir,rjr],'exactFixedPositionsM':U[[i,j]].tolist(),'removedSourceUV':a['TEXCOORD_0'][[ir,jr]].tolist(),'retainedSourceUV':a['TEXCOORD_0'][[rir,rjr]].tolist(),'removedSourceNormals':a['NORMAL'][[ir,jr]].tolist(),'retainedSourceNormals':a['NORMAL'][[rir,rjr]].tolist()})
assert len(sew)==53
m61['exact53CutHalfedges']=sorted(sew,key=lambda x:tuple(x['removedOrientedPhysicalEdge']));m61['closedSourceIslandAddedFaceIDs']=sorted(island)
assert m47['firstRootedAttachmentY_M']==1.301290512084961
# Root ancestry on the exact61 retained induced low graph. Chart islands are
# not anatomical labels. Upper endpoints have no low-root label by definition.
rem61=set(m61['removedSourceFaceIDs']);low_graph=defaultdict(set)
for t,(pi,fi)in zip(WP,whole_face_names):
 if pi==0 and fi in rem61:continue
 for k in range(3):
  i,j=map(int,[t[k],t[(k+1)%3]])
  if W[i,1]<1.30 and W[j,1]<1.30:low_graph[i].add(j);low_graph[j].add(i)
low_labels={};left=set(low_graph)
while left:
 stack=[min(left)];seen=set()
 while stack:
  i=stack.pop()
  if i in seen:continue
  seen.add(i);stack.extend(low_graph[i]-seen)
 left-=seen;names=sorted(n for n,ids in wr.items()if ids&seen)
 for i in seen:low_labels[i]=names
boundary=m61['orderedCutBoundaryCycles'][0];labels=[low_labels.get(int(p0_to_whole[i]),[])if U[i,1]<1.30 else ['HIGH_Y_GE1_30']for i in boundary];runs=[]
for idx,(pid,lab)in enumerate(zip(boundary,labels)):
 if not runs or runs[-1]['rootLabels']!=lab:runs.append({'rootLabels':lab,'orderedBoundaryIndices':[],'sourcePhysicalIDs':[]})
 runs[-1]['orderedBoundaryIndices'].append(idx);runs[-1]['sourcePhysicalIDs'].append(pid)
if len(runs)>1 and runs[0]['rootLabels']==runs[-1]['rootLabels']:
 runs[0]['orderedBoundaryIndices']=runs[-1]['orderedBoundaryIndices']+runs[0]['orderedBoundaryIndices'];runs[0]['sourcePhysicalIDs']=runs[-1]['sourcePhysicalIDs']+runs[0]['sourcePhysicalIDs'];runs.pop()
m61['below1_30BoundaryRootOwnershipRuns']=runs;m61['rootLabelsAreAncestryNotTorsoAnatomyMask']=True
nodes61=set(P[sorted(rem61)].ravel().tolist());bset=set(boundary);m61['frontRearSourceLandmarks']=[{'sourcePhysicalID':i,'positionM':U[i].tolist(),'domainClass':'boundary'if i in bset else'interior'if i in nodes61 else'external_protected','incidentRemovedSourceFaces':[fi for fi in sorted(rem61)if i in P[fi]]}for i in [1488,1420,13448,13550,12815,13219,12928,1571,1380,1543,8238]]
# Keep genuine literal arc ancestry, WITHOUT length-pairing correspondence.
front,rear=1420,13550;assert boundary[0]==front;ri=boundary.index(rear);arc61={'central':boundary[:ri+1],'lateral':[front]+list(reversed(boundary[ri:]))}
arcs=[]
for name,ids in arc61.items():
 oldids=c['arcCorrespondence'][name]['physicalIDs'];oldedges={tuple(sorted(e))for e in zip(oldids,oldids[1:])};newedges=list(zip(ids,ids[1:]));arcs.append({'name':name,'orderedSourcePhysicalIDs':ids,'sourceEdgeLengthM':[float(np.linalg.norm(U[i].astype(float)-U[j]))for i,j in newedges],'old194ExactEdgeAncestry':[tuple(sorted(e))in oldedges for e in newedges],'old194NodesStillOnThisArc':[i for i in oldids if i in ids],'addedPhysicalIDs':[i for i in ids if i not in oldids],'removedOldPhysicalIDs':[i for i in oldids if i not in ids],'use':'Literal source halfedge ancestry only. No station, nearest or arc-length mapping between arcs; not a donor parameterization or fit.'})
m61['literalSourceArcAncestry']=arcs

mem.append(check());save('high-path-extension.json',{'status':'READONLY_LITERAL47_HIGH_CONNECTION_AND_CLOSED61_HALO_DIAGNOSTIC_NOT_GEOMETRY_REGISTRATION','sourceSHA256':s,'geometryAttempts':0,'weights':0,'solvers':0,'exports':0,'GPU':False,'source47':m47,'expanded59':m59,'closed61':m61,'expansionReason':'Exactly194s12 retained-source crossing witnesses; no coordinate ROI or arbitrary halo. Removing witnesses is NOT proof a new fill is clear.','crossed12SourceFaces':sorted(cross),'mechanismDifference':'Keep the literal retained high source connection; remove/re-author the low bridge and nearby crossed retained faces. Do not replace high source connection with194 independent ruled arcs or the1235 all-new joining annulus.','limits':['Read-only original source cut graphs only. No boundary reseal, texture transport, rest-clear candidate, new skin or appearance/motion pass.','A path support list preserves this particular graph path only; it does not establish correct cloth panel anatomy or sufficient tangent/fold control.','The closed61 source domain is topology-valid but remains unregistered for actual construction. Its high path and chart/control recipe need parent review.', 'The194 fill also had30 panel/panel strict crossings. Removing12 retained crossing faces addresses context only, not that self-fold failure; never reuse its ruled sheets automatically.'],'inputPins':pins,'timing':{'elapsedSeconds':time.monotonic()-start,'anonymousBytesSamples':mem,'CPUThreads':2}})
print(json.dumps({k:{x:m[x]for x in ['sourceFaces','removedEuler','cutBoundaryEdges','cutBoundaryDegreeFailures','retainedVertexLinkFailures','firstRootedAttachmentY_M','inside1_30_1_32Band','protectedRetainedP0FaceIDs']}for k,m in [('source47',m47),('expanded59',m59),('closed61',m61)]}))
