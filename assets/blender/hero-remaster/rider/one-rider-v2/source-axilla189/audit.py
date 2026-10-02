"""Literal p0 rest sections and minimax-height topology, no skin semantics."""
from pathlib import Path
from collections import defaultdict,Counter
from scipy.spatial.transform import Rotation
import ast,json,struct,hashlib,time,heapq,re,subprocess
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189';S=B/'source-axilla189';S.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();start=time.monotonic();pins={};attempt=json.loads((E/'attempt.json').read_text());assert attempt['status']=='REGISTERED_BEFORE_MEASUREMENT'
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();d=sha(b)
 if h:assert d==h
 pins[str(p)]={'sha256':d,'bytes':len(b)};return b
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def memory():
 x=subprocess.check_output(['vm_stat'],text=True);pg=int(re.search(r'page size of (\d+)',x).group(1));v=int(re.search(r'Anonymous pages:\s+(\d+)',x).group(1))*pg/1e9;assert v<70;assert time.monotonic()-start<590;return v
try:
 mem=[memory()];reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(pin(reader).decode());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env)
 source=B/'source-preserving-garment185/operator/rider.glb';base=B/'rig-adapter01/body-bind34/rider.glb';pin(source,'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5');pin(base,'adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7');C=env['GLB'](source,pins[str(source)]['sha256']);D=env['GLB'](base,pins[str(base)]['sha256']);a,f=C.primitive(0,0);b,bf=D.primitive(0,0);assert np.array_equal(f,bf)and all(a[k].tobytes()==b[k].tobytes()for k in a)
 for p in [R/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/shape-lane/volume-lane/source-embedding23/continuous-shell-handoff.json',R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181/report.json',R/'docs/evidence/hero-remaster/one-rider-v2/source-rig188/read-only/report.json']:pin(p)
 P=a['POSITION'];U,q=np.unique(P,axis=0,return_inverse=True);pf=q[f];T=P[f].astype(float);ylo=T[:,:,1].min(1);yhi=T[:,:,1].max(1);aliases=[np.flatnonzero(q==i).tolist()for i in range(len(U))];edgefaces=defaultdict(list);adj=defaultdict(set)
 for i,t in enumerate(pf):
  for k in range(3):
   x,z=map(int,[t[k],t[(k+1)%3]]);edgefaces[tuple(sorted((x,z)))].append(i);adj[x].add(z);adj[z].add(x)
 def gap(A,B):
  aa=np.array([s['positionsM']for s in A['segments']])[:,:,[0,2]];bb=np.array([s['positionsM']for s in B['segments']])[:,:,[0,2]];best=(float('inf'),None)
  for reverse in [False,True]:
   pts,segs=(bb[:,0],aa)if reverse else(aa[:,0],bb);v=segs[:,1]-segs[:,0];den=(v*v).sum(1)
   delta=pts[:,None,:]-segs[None,:,0,:];t=np.clip((delta*v[None]).sum(2)/den[None],0,1);near=segs[None,:,0,:]+t[:,:,None]*v[None];dd=np.linalg.norm(pts[:,None]-near,axis=2);i,j=np.unravel_index(dd.argmin(),dd.shape)
   if dd[i,j]<best[0]:best=(float(dd[i,j]),{'reverse':reverse,'pointSegmentIndex':int(i),'oppositeSegmentIndex':int(j),'pointXZ':pts[i].tolist(),'nearestXZ':near[i,j].tolist(),'segmentParameter':float(t[i,j])})
  return {'gapM':best[0],'witness':best[1]}
 def section(y,label):
  ids=np.flatnonzero((ylo<=y)&(yhi>=y));nodes={};segments=[];cop=[];vertex=[];touch=[]
  for fi in ids:
   ti=f[fi];ph=pf[fi];tr=T[fi];on=np.flatnonzero(tr[:,1]==y)
   if len(on)==3:cop.append(int(fi));continue
   hits={}
   for k in range(3):
    h=(k+1)%3;ya,yb=tr[k,1],tr[h,1];x,z=int(ph[k]),int(ph[h]);edge=tuple(sorted((x,z)))
    if ya==y and yb==y:
     for lane in [k,h]:hits[('v',int(ph[lane]))]=(tr[lane],{'sourcePhysicalVertex':int(ph[lane]),'sourceRows':aliases[int(ph[lane])]})
    elif ya==y:hits[('v',x)]=(tr[k],{'sourcePhysicalVertex':x,'sourceRows':aliases[x]})
    elif yb==y:hits[('v',z)]=(tr[h],{'sourcePhysicalVertex':z,'sourceRows':aliases[z]})
    elif(ya<y<yb)or(yb<y<ya):
     t=(y-ya)/(yb-ya);p=tr[k]+t*(tr[h]-tr[k]);hits[('e',*edge)]=(p,{'sourcePhysicalEdge':list(edge),'sourceEdgeRows':[int(ti[k]),int(ti[h])],'parameterFromFirstRow':float(t),'sourceIncidentFaces':edgefaces[edge]})
   if len(hits)==1:touch.append(int(fi));continue
   if len(hits)!=2:
    if hits:vertex.append({'sourceFace':int(fi),'intersectionNodeCount':len(hits)})
    continue
   ks=list(hits);entry={'sourceFace':int(fi),'sourceTriangleRows':ti.tolist(),'physicalTriangle':ph.tolist(),'nodeKeys':[list(k)for k in ks],'positionsM':[hits[k][0].tolist()for k in ks],'endpoints':[hits[k][1]for k in ks]};segments.append(entry)
   for k in ks:nodes[k]=hits[k][0]
  graph=defaultdict(list)
  for i,s in enumerate(segments):
   k,j=map(tuple,s['nodeKeys']);graph[k].append((j,i));graph[j].append((k,i))
  remaining=set(graph);loops=[]
  while remaining:
   seed=next(iter(remaining));stack=[seed];ns=set();es=set()
   while stack:
    k=stack.pop()
    if k in ns:continue
    ns.add(k);remaining.discard(k)
    for n,i in graph[k]:es.add(i);stack.append(n)
   closed=all(len(graph[n])==2 for n in ns);ordered=[]
   if closed:
    cur=min(ns);prev=None
    while cur not in ordered:
     ordered.append(cur);nxt=next(n for n,i in graph[cur]if n!=prev);prev,cur=cur,nxt
   coords=np.array([nodes[n]for n in(ordered if closed else sorted(ns))]);seg=[segments[i]for i in sorted(es)];central=bool(coords[:,2].min()<0<coords[:,2].max());cxz=coords[:,[0,2]];area=abs(float(np.cross(cxz,np.roll(cxz,-1,axis=0)).sum()))/2 if closed else None
   loops.append({'closed':closed,'geometricClass':'central_Z0_straddling'if central else'positiveZ_lateral'if coords[:,2].mean()>0 else'negativeZ_lateral','nodeCount':len(ns),'segmentCount':len(es),'boundsM':[coords.min(0).tolist(),coords.max(0).tolist()],'centroidM':coords.mean(0).tolist(),'areaXZ_M2':area,'nodeDegrees':dict(Counter(len(graph[n])for n in ns)),'orderedNodeKeys':[list(n)for n in ordered],'orderedPositionsM':coords.tolist(),'segments':seg})
  loops.sort(key=lambda x:x['centroidM'][2]);central=[x for x in loops if x['geometricClass']=='central_Z0_straddling'];gaps=[]
  if len(central)==1:
   for x in loops:
    if x is not central[0]and x['closed']and central[0]['closed']:gaps.append({'lateralClass':x['geometricClass'],**gap(x,central[0])})
  result={'label':label,'heightY_M':float(y),'primitive':0,'intersectedSourceFaceIDs':ids.tolist(),'contourCount':len(loops),'closedContourCount':sum(x['closed']for x in loops),'openContourCount':sum(not x['closed']for x in loops),'coplanarFaces':cop,'pointOnlyTouchFaces':touch,'vertexCases':vertex,'loops':loops,'armTorsoGapCandidates':gaps};save(S/f'section-{label}.json',result);return result
 sections=[section(y,f'fixed-{i:02d}')for i,y in enumerate(attempt['planesYMetres'])];low=sections[0];assert len(low['loops'])==3 and all(x['closed']for x in low['loops']);labels={x['geometricClass']:x for x in low['loops']};assert len(labels)==3
 def low_seeds(loop):
  result=set()
  for s in loop['segments']:
   for ep in s['endpoints']:
    for i in ep.get('sourcePhysicalEdge',[]):
     if U[i,1]<.94:result.add(i)
  return result
 seeds={k:low_seeds(v)for k,v in labels.items()};central=seeds['central_Z0_straddling'];cost=np.full(len(U),np.inf);prev=np.full(len(U),-1,int);heap=[]
 for i in central:cost[i]=float(U[i,1]);heapq.heappush(heap,(cost[i],i))
 while heap:
  c,i=heapq.heappop(heap)
  if c!=cost[i]:continue
  for j in sorted(adj[i]):
   nc=max(c,float(U[j,1]))
   if nc<cost[j]:cost[j]=nc;prev[j]=i;heapq.heappush(heap,(nc,j))
 levels=np.unique(U[:,1]);connections=[]
 for side in ['positiveZ_lateral','negativeZ_lateral']:
  target=min(seeds[side],key=lambda i:(cost[i],i));path=[target]
  while prev[path[-1]]>=0:path.append(int(prev[path[-1]]))
  path=path[::-1];h=float(cost[target]);at=np.flatnonzero(U[:,1]==h).tolist();below=float((levels[levels<h][-1]+h)/2);above=float((levels[levels>h][0]+h)/2);before=section(below,side+'-before');after=section(above,side+'-after');ancestry=[{'physicalEdge':[int(i),int(j)],'sourceRowAliases':[aliases[i],aliases[j]],'sourceFaces':edgefaces[tuple(sorted((i,j)))]}for i,j in zip(path,path[1:])];connections.append({'geometricSide':side,'firstSublevelSurfaceConnectionY_M':h,'criticalPhysicalVertexIDs':[int(i)for i in path if float(U[i,1])==h],'criticalSourceRowAliases':[aliases[i]for i in path if float(U[i,1])==h],'criticalPositionM':[U[i].tolist()for i in path if float(U[i,1])==h],'pathPhysicalIDs':path,'pathSourceEdges':ancestry,'criticalSourceFaces':sorted({fi for i in path if float(U[i,1])==h for j in adj[i]for fi in edgefaces[tuple(sorted((i,j)))]}),'beforeY':below,'afterY':above,'contoursBefore':before['contourCount'],'contoursAfter':after['contourCount']})
 mem.append(memory());attrs=[{'semantic':k,'shape':list(v.shape),'sha256':sha(v.tobytes())}for k,v in a.items()];centres=C.rest()[:,:3,3];names=[C.d['nodes'][i]['name']for i in C.d['skins'][0]['joints']];rig=[{'name':n,'restCentreM':p.tolist()}for n,p in zip(names,centres)]
 def compact(x):return {k:x[k]for k in ['label','heightY_M','contourCount','closedContourCount','openContourCount','coplanarFaces','pointOnlyTouchFaces','vertexCases','armTorsoGapCandidates']}|{'contours':[ {k:v for k,v in l.items()if k not in ['segments','orderedNodeKeys','orderedPositionsM']}for l in x['loops']]}
 report={'status':'FROZEN_READONLY_P0_SOURCE_REST_ATTACHMENT_DIAGNOSTIC','source185SHA256':pins[str(source)]['sha256'],'source34SHA256':pins[str(base)]['sha256'],'p0GeometryAndAttributesExact185Vs34':True,'sourcePrimitive':0,'method':'Literal triangle-plane intersections keyed by exact Float32 physical source edges/vertices. No p1/p2 or weight ownership in classification. First attachment is minimax-height path in original p0edge graph, then adjacent critical-Y interval sections.','sourceP0Arrays':attrs,'sourceP0IndicesSHA256':sha(f.tobytes()),'sections':[compact(x)for x in sections],'firstConnections':connections,'rigCentresContextOnly':rig,'seconds':time.monotonic()-start,'memoryAnonymousGB':mem,'inputs':pins,'recipeSHA256':sha(Path(__file__).read_bytes()),'privateOutputs':[{'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in sorted(S.glob('*.json'))],'limits':['Geometric central/lateral labels are contour geometry, not certified garment/skin semantics.','Section minima are exact polygonal rest-contour separation; no moving support, thickness or anatomical validation.','Minimax source-edge attachment is topology of p0sublevel surface, not a material seam or weight-derived axilla.','No repair, solver, geometry export, render, weights or pose changes.']};save(E/'report.json',report)
 for p,d in pins.items():assert sha(Path(p).read_bytes())==d['sha256']
 attempt['status']=report['status'];save(E/'attempt.json',attempt);print(json.dumps({'seconds':report['seconds'],'sections':[(x['heightY_M'],x['contourCount'])for x in sections],'firstConnections':[(x['geometricSide'],x['firstSublevelSurfaceConnectionY_M'],x['criticalSourceRowAliases'],x['contoursBefore'],x['contoursAfter'])for x in connections]}))
except Exception as e:
 attempt['status']='FROZEN_READONLY_DIAGNOSTIC_FAILURE';attempt['failures'].append({'type':type(e).__name__,'error':str(e)});save(E/'attempt.json',attempt);raise
