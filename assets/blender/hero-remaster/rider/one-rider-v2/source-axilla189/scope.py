"""Read-only proposed actual source face/boundary cycles; no triangle changes."""
from pathlib import Path
from collections import defaultdict,Counter
import ast,json,struct,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189';S=B/'source-axilla189';sha=lambda b:hashlib.sha256(b).hexdigest();reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(reader.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);C=env['GLB'](B/'source-preserving-garment185/operator/rider.glb','ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5');a,f=C.primitive(0,0);P=a['POSITION'];U,q=np.unique(P,axis=0,return_inverse=True);pf=q[f];report=json.loads((E/'report.json').read_text());prereg=json.loads((E/'strip-scope-preregister.json').read_text());T=P[f];mask=((T[:,:,1]>=1.16)&(T[:,:,1]<=1.35)&(T[:,:,0]>=.53)&(T[:,:,0]<=.73)&(abs(T[:,:,2])>=.145)&(abs(T[:,:,2])<=.31)).all(1);rows=[]
for conn in report['firstConnections']:
 positive=conn['geometricSide']=='positiveZ_lateral';ids=np.flatnonzero(mask&(T[:,:,2].mean(1)>0 if positive else T[:,:,2].mean(1)<0));edge=defaultdict(list)
 for i in ids:
  t=pf[i]
  for k in range(3):edge[tuple(sorted(map(int,[t[k],t[(k+1)%3]])))].append(int(i))
 adj=defaultdict(set)
 for v in edge.values():
  for i in v:adj[i].update(j for j in v if j!=i)
 seeds=set(conn['criticalSourceFaces'])&set(map(int,ids));assert seeds;chosen=set();stack=[min(seeds)]
 while stack:
  i=stack.pop()
  if i in chosen:continue
  chosen.add(i);stack.extend(adj[i]-chosen)
 pe=defaultdict(list)
 for i in chosen:
  t=pf[i]
  for k in range(3):x,z=map(int,[t[k],t[(k+1)%3]]);pe[tuple(sorted((x,z)))].append((i,x,z))
 directed=[v[0]for e,v in pe.items()if len(v)==1];graph=defaultdict(list);ind=Counter()
 for fi,x,z in directed:graph[x].append((z,fi));ind[z]+=1
 valid=all(len(v)==1 and ind[x]==1 for x,v in graph.items());cycles=[];remaining=set(graph)
 if valid:
  while remaining:
   start=min(remaining);x=start;cy=[];faces=[]
   while x in remaining:remaining.remove(x);cy.append(x);n,fi=graph[x][0];faces.append(fi);x=n
   assert x==start;cycles.append({'orderedPhysicalP0IDs':cy,'orderedPositionsM':U[cy].tolist(),'sourceRowAliases':[np.flatnonzero(q==i).tolist()for i in cy],'incidentSourceFaces':faces})
 data={'geometricSide':conn['geometricSide'],'sourceFaceIDs':sorted(chosen),'sourcePhysicalVertexIDs':sorted(set(pf[list(chosen)].ravel().tolist())),'boundaryPhysicalVertexIDs':sorted(graph),'boundaryDegree2OrientedValid':valid,'scopeOverincidentEdges':sum(len(v)>2 for v in pe.values()),'orderedSourceBoundaryCycles':cycles,'unselectedROIFragmentsFaces':len(ids)-len(chosen),'originalCriticalFacesInScope':sorted(chosen&set(conn['criticalSourceFaces']))};(S/(conn['geometricSide']+'-proposed-strip.json')).write_text(json.dumps(data,indent=2)+'\n');rows.append({'side':conn['geometricSide'],'faces':len(chosen),'vertices':len(data['sourcePhysicalVertexIDs']),'fixedBoundaryVertices':len(graph),'boundaryCycleLengths':[len(x['orderedPhysicalP0IDs'])for x in cycles],'boundaryGraphValid':valid,'scopeOverincidentEdges':data['scopeOverincidentEdges'],'droppedROIFaces':len(ids)-len(chosen),'rawScopePath':str(S/(conn['geometricSide']+'-proposed-strip.json'))})
x={'status':'READONLY_PROPOSED_SOURCE_TRANSITION_STRIP_SCOPE_NO_GEOMETRY','preregisterSHA256':sha((E/'strip-scope-preregister.json').read_bytes()),'sourceSHA256':C.h,'recipeSHA256':sha(Path(__file__).read_bytes()),'scopes':rows,'qualification':'Geometric ROI component, not certified semantic garment mask. Boundary validity is not a repair or anatomical feasibility pass.'};(E/'strip-scope-summary.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
