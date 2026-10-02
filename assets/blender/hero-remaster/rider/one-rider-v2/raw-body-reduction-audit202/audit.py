"""Read-only exact triangle sections and source-anchored sublevel paths."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,hashlib,heapq,time,resource,subprocess
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1');D=B/'one-rider-v2/raw-body-reduction-audit202';O=R/'docs/evidence/hero-remaster/one-rider-v2/raw-body-reduction-audit202'
z=np.load(D/'lineage.npz');start=time.monotonic();report={'status':'READ_ONLY_RAW_REDUCED_CURRENT_CONSTRUCTION_COMPARISON_UNACCEPTED','meshes':{},'limits':['Sublevel graph and contour labels are geometric construction proxies, not certified anatomical or weight ownership masks.','No geometry edits, weights, rig, exports, solver, render, GPU or production asset changes.','No motion, appearance, mobile, topology suitability or skin pass.','Cleanup and reducer intermediate files absent: causality cannot be apportioned between FloaterRemover, DegenerateFaceRemover and FaceReducer for small local changes.']}
def section(U,F,y):
 tri=U[F];ids=np.flatnonzero((tri[:,:,1].min(1)<y)&(tri[:,:,1].max(1)>y));nodes={};segments=[];graph=defaultdict(list)
 for fi in ids:
  f=F[fi];p=U[f];hits=[]
  for a,b in [(0,1),(1,2),(2,0)]:
   if (p[a,1]<y<p[b,1])or(p[b,1]<y<p[a,1]):
    edge=tuple(sorted((int(f[a]),int(f[b]))));t=(y-p[a,1])/(p[b,1]-p[a,1]);q=p[a]+t*(p[b]-p[a]);nodes[edge]=q;hits.append(edge)
  if len(hits)!=2:continue
  a,b=hits;si=len(segments);segments.append({'face':int(fi),'keys':[list(a),list(b)],'positions':[nodes[a].tolist(),nodes[b].tolist()]});graph[a].append((b,si));graph[b].append((a,si))
 remaining=set(graph);loops=[]
 while remaining:
  seed=min(remaining);ns=set();es=set();stack=[seed]
  while stack:
   k=stack.pop()
   if k in ns:continue
   ns.add(k);remaining.discard(k)
   for j,e in graph[k]:stack.append(j);es.add(e)
  P=np.array([nodes[k] for k in sorted(ns)]);closed=all(len(graph[k])==2 for k in ns);central=P[:,2].min()<0<P[:,2].max();label='central'if central else'positiveZ'if P[:,2].mean()>0 else'negativeZ';order=[]
  if closed:
   cur=min(ns);prev=None
   while cur not in order:
    order.append(cur);nxt=next(n for n,i in graph[cur] if n!=prev);prev,cur=cur,nxt
   Q=np.array([nodes[k] for k in order]);area=abs(float(np.sum(Q[:,0]*np.roll(Q[:,2],-1)-Q[:,2]*np.roll(Q[:,0],-1))))/2
  else:area=None
  loops.append({'label':label,'closed':closed,'segments':[segments[i]for i in sorted(es)],'bounds':[P.min(0).tolist(),P.max(0).tolist()],'centroid':P.mean(0).tolist(),'areaXZ_M2':area,'degreeCounts':dict(Counter(len(graph[k])for k in ns))})
 return {'heightY_M':float(y),'contours':loops}
def compact(s):
 return {'heightY_M':s['heightY_M'],'contourCount':len(s['contours']),'contours':[{k:v for k,v in x.items()if k!='segments'}|{'segments':len(x['segments'])}for x in s['contours']]}
for name in ['native','reduced','paint','current']:
 P=z[name+'Positions'];F0=z[name+'Faces'];U,inv=np.unique(P,axis=0,return_inverse=True);F=inv[F0];E=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0);edgecount=Counter(map(tuple,np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1)));adj=[[]for _ in U]
 for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
 rows=np.r_[E[:,0],E[:,1]];cols=np.r_[E[:,1],E[:,0]];nc,labels=connected_components(coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(U),len(U))).tocsr());sizes=np.bincount(labels)
 low=section(U,F,.94);assert len(low['contours'])==3 and all(x['closed']for x in low['contours']), (name,compact(low));seeds={x['label']:sorted({i for seg in x['segments']for edge in seg['keys']for i in edge if U[i,1]<.94})for x in low['contours']};assert set(seeds)=={'central','positiveZ','negativeZ'}
 cost=np.full(len(U),np.inf);prev=np.full(len(U),-1,int);heap=[]
 for i in seeds['central']:cost[i]=U[i,1];heapq.heappush(heap,(cost[i],i))
 while heap:
  c,i=heapq.heappop(heap)
  if c!=cost[i]:continue
  for j in adj[i]:
   v=max(c,float(U[j,1]))
   if v<cost[j]:cost[j]=v;prev[j]=i;heapq.heappush(heap,(v,j))
 connections=[];ys=np.unique(U[:,1]);sections=[section(U,F,y)for y in [.94,1.15,1.18,1.19,1.20,1.24,1.30,1.35]]
 for label in ['positiveZ','negativeZ']:
  end=min(seeds[label],key=lambda i:(cost[i],i));h=float(cost[end]);path=[end]
  while prev[path[-1]]>=0:path.append(int(prev[path[-1]]))
  path=path[::-1];critical=[i for i in path if U[i,1]==h];below=float((ys[ys<h][-1]+h)/2);above=float((ys[ys>h][0]+h)/2);sections.extend([section(U,F,below),section(U,F,above)]);connections.append({'label':label,'firstConnectionY_M':h,'criticalPhysicalIDs':critical,'criticalPositionsM':U[critical].tolist(),'before':compact(sections[-2]),'after':compact(sections[-1]),'pathPhysicalIDs':path})
 mesh={'positions':len(P),'physicalVertices':len(U),'triangles':len(F),'graphComponents':int(nc),'componentSizesDescending':sorted(map(int,sizes),reverse=True),'boundaryEdges':sum(v==1 for v in edgecount.values()),'nonmanifoldEdges':sum(v>2 for v in edgecount.values()),'connections':connections,'sections':[compact(s)for s in sections]}
 report['meshes'][name]=mesh
 (D/f'{name}-sections.json').write_text(json.dumps(sections,separators=(',',':'))+'\n');np.savez(D/f'{name}-graph.npz',positions=U,faces=F,edges=E,originalRowPhysicalIDs=inv,componentLabels=labels)
 print(name,[(x['label'],x['firstConnectionY_M'])for x in connections],[(s['heightY_M'],len(s['contours']))for s in sections],flush=True)
 assert time.monotonic()-start<1200
report['seconds']=time.monotonic()-start;report['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;report['CPUThreads']=2
report['constructionConclusion']='Raw pre-cleanup/pre-decimation shape already has both low arm–central surface connections. Higher resolution retains essentially the same fused low underarm construction; switching to this raw body alone does not supply a separated high armhole. Cleanup/reduction shifts first connection by measured millimetres, not the roughly110mm required target gap. Native→reduced face maps and intermediate cleanup outputs are absent, so finer per-operator causality is unresolved.'
report['noClaim']='This is a static construction finding, not anatomical semantic segmentation, skin/rig suitability, or visual acceptance.'
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n')
