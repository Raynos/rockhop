"""One parent-selected dorsal window; read-only exact sequential polygon clipping."""
import numpy as np,json,hashlib
from pathlib import Path
ROOT=Path('/Users/raynos/projects/games/rockhop')
p=ROOT/'harness/out/rider-rebuild/glove-cuff-construction07/inspection01/guide-L.npz'
a=np.load(p);source=a['originalSourceXYZ'];faces=a['faces'];verts=[x.copy() for x in source];ancestry=[{i:1.0} for i in range(len(source))];polys=[(list(map(int,f)),i) for i,f in enumerate(faces)]
# First y < -.65, then z > 0. Each edge split shared across incident polygons.
for axis,value,sign in [(1,-.65,-1),(2,0.,1)]:
 cache={};out=[]
 for poly,owner in polys:
  clipped=[]
  for x,z in zip(poly,poly[1:]+poly[:1]):
   dx=sign*(verts[x][axis]-value); dz=sign*(verts[z][axis]-value); xin=dx>0;zin=dz>0
   if xin:clipped.append(x)
   if xin!=zin:
    key=tuple(sorted((x,z)))
    if key not in cache:
     t=dx/(dx-dz);pos=verts[x]+t*(verts[z]-verts[x]);pos[axis]=value
     weights={i:(1-t)*w for i,w in ancestry[x].items()}
     for i,w in ancestry[z].items():weights[i]=weights.get(i,0)+t*w
     cache[key]=len(verts);verts.append(pos);ancestry.append(weights)
    clipped.append(cache[key])
  if len(clipped)>=3:out.append((clipped,owner))
 polys=out
f=[];owners=[]
for poly,owner in polys:
 for j in range(1,len(poly)-1):f.append([poly[0],poly[j],poly[j+1]]);owners.append(owner)
f=np.array(f);owners=np.array(owners);verts=np.array(verts)
edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);unique,count=np.unique(edges,axis=0,return_counts=True)
assert count.max()==2
adj={int(x):[] for x in np.unique(f)}
for x,z in unique:adj[x].append(z);adj[z].append(x)
unseen=set(adj);components=[];loops=[]
while unseen:
 todo=[unseen.pop()];component=set(todo)
 while todo:
  for z in adj[todo.pop()]:
   if z in unseen:unseen.remove(z);component.add(z);todo.append(z)
 ids=np.array(sorted(component));em=np.isin(unique[:,0],ids);fm=np.isin(f[:,0],ids);boundary=unique[(count==1)&em]
 badj={int(x):[] for x in np.unique(boundary)}
 for x,z in boundary:badj[x].append(z);badj[z].append(x)
 assert all(len(x)==2 for x in badj.values()),'non-loop boundary'
 remaining=set(badj);componentloops=[]
 while remaining:
  start=min(remaining);loop=[];previous=None;node=start
  while node not in loop:
   loop.append(node);other=sorted(x for x in badj[node] if x!=previous)[0];previous,node=node,other
  assert node==start;remaining.difference_update(loop);componentloops.append(len(loop));loops.append(loop)
 chi=len(ids)-int(em.sum())+int(fm.sum())
 components.append(dict(vertices=len(ids),edges=int(em.sum()),triangles=int(fm.sum()),euler=chi,boundaryLoops=componentloops,originalFaceOwners=np.unique(owners[fm]).tolist()))
looprecords=[]
for loop in loops:
 records=[]
 for x,z in zip(loop,loop[1:]+loop[:1]):
  incident=np.flatnonzero(np.sum(np.isin(f,[x,z]),axis=1)==2);assert len(incident)==1
  records.append({'start':{'sourceXYZ':verts[x].tolist(),'sourceVertexBarycentric':{str(k):w for k,w in ancestry[x].items()}},'end':{'sourceXYZ':verts[z].tolist(),'sourceVertexBarycentric':{str(k):w for k,w in ancestry[z].items()}},'sourceFace':int(owners[incident[0]]),'plane':'Y=-.65' if abs(verts[x,1]+.65)<1e-10 and abs(verts[z,1]+.65)<1e-10 else 'Z=0'})
 looprecords.append(records)
area=np.linalg.norm(np.cross(verts[f[:,1]]-verts[f[:,0]],verts[f[:,2]]-verts[f[:,0]]),axis=1)/2
result={'acceptedArt':False,'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'window':'sourceY < -0.65 AND sourceZ > 0','components':components,'boundaryLoops':looprecords,'nonmanifoldEdges':int((count>2).sum()),'minimumAreaSourceUnitsSquared':float(area.min()),'lipAnchors':[{'vertex':int(i),'sourceXYZ':source[i].tolist(),'inside':bool(source[i,1]<-.65 and source[i,2]>0)} for i in a['oldLipAnchors']],'witnessFaces':[{ 'face':i,'fullyInside':bool(np.all(source[faces[i],1]<-.65)&np.all(source[faces[i],2]>0)),'included':i in owners} for i in [4985,5324]],'negativeZHandleVerticesAllExcluded':bool(np.all(source[[5403,5422,5478,5544,5548,5549,5584,5585,5655,5659,5660,5661,5704,5717,5718,5719,5773,5791,5798],2]<0)),'limits':['Temporary clipping only; no saved or edited model.','Boundary interpolation retains face and vertex ancestry.','Topology does not certify feature semantics, geometric clearance, or moving appearance.']}
Path('/tmp/astra-cuff-boundary11-dorsal.json').write_text(json.dumps(result,indent=2)+'\n')
np.savez('/tmp/astra-cuff-boundary11-dorsal-plot.npz',source=source,faces=faces,vertices=verts,patchFaces=f,sourceOwners=owners,boundary=np.array(loops[0]))
print(json.dumps({**{k:v for k,v in result.items() if k not in ['boundaryLoops','components']},'components':[{**{k:v for k,v in c.items() if k!='originalFaceOwners'},'originalFaceOwnerCount':len(c['originalFaceOwners'])} for c in components]}))
