import numpy as np,json,heapq
from pathlib import Path
from collections import deque
ROOT=Path('/Users/raynos/projects/games/rockhop'); BASE=ROOT/'harness/out/rider-rebuild/selected-boot-wearer80'
src=json.loads((ROOT/'harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json').read_text());raw=(ROOT/src['arrays']['path']).read_bytes();frames=json.loads((BASE/'inspect02/inspection.json').read_text());selection=json.loads((BASE/'selection01/selection.json').read_text())
def arr(s,k):
 d=src['arrays']['layout'][s+k];return np.frombuffer(raw,dtype=d['dtype'],offset=d['byteOffset'],count=np.prod(d['shape'])).reshape(d['shape'])
for side in 'LR':
 origin=np.array(frames['sides'][side]['origin']);basis=np.array(frames['sides'][side]['basisColumns']).T
 p=(arr(side,'Positions').astype(float)-origin)@basis;f=arr(side,'Triangles'); tri=p[f];profiles=[]
 highids=np.flatnonzero(tri[:,:,2].max(1)>.09);high=tri[highids]
 for angle in np.arange(64)*2*np.pi/64:
  direction=np.array([np.cos(angle),np.sin(angle)]);delta=high[:,:,0]*direction[1]-high[:,:,1]*direction[0]
  subset=highids[(delta.min(1)<0)&(delta.max(1)>0)];edges={};nodes={};faceparents={}
  for fid in subset:
   face=f[fid];pts=p[face];q=pts[:,0]*direction[1]-pts[:,1]*direction[0];cuts=[]
   for a,b in ((0,1),(1,2),(2,0)):
    if q[a]*q[b]<0:
     t=q[a]/(q[a]-q[b]);v=pts[a]+t*(pts[b]-pts[a]);key=tuple(sorted((int(face[a]),int(face[b]))));cuts.append((key,v))
   assert len(cuts)==2
   (ka,a),(kb,b)=cuts
   if max(a[2],b[2])<=.09 or max(a[:2]@direction,b[:2]@direction)<=0:continue
   if min(a[2],b[2])<.09:
    v=a+(.09-a[2])/(b[2]-a[2])*(b-a);k=('cut',int(fid))
    if a[2]<.09:ka,a=k,v
    else:kb,b=k,v
   if min(a[:2]@direction,b[:2]@direction)<=0:continue
   for key,v in ((ka,a),(kb,b)):nodes[key]=v
   edges.setdefault(ka,[]).append(kb);edges.setdefault(kb,[]).append(ka);faceparents[frozenset((ka,kb))]=int(fid)
  ends=[k for k in edges if len(edges[k])==1 and abs(nodes[k][2]-.09)<1e-10];start=min(ends,key=lambda k:nodes[k][:2]@direction)
  chain=[start];prev=None;cursor=start
  while True:
   opts=[k for k in edges[cursor] if k!=prev]
   if not opts:break
   assert len(opts)==1
   nxt=opts[0];assert nxt not in chain;chain.append(nxt);prev,cursor=cursor,nxt
  assert cursor in ends and len(chain)>2
  q=np.array([nodes[k] for k in chain]);imax=int(np.argmax(q[:,2]));crest=q[imax];cutz=crest[2]-.004
  crossing=next(i for i in range(imax) if q[i,2]<=cutz<q[i+1,2]);a,b=q[crossing:crossing+2];t=(cutz-a[2])/(b[2]-a[2]);seam=a+t*(b-a)
  profiles.append({'angle':float(angle),'crestLocalM':crest.tolist(),'innerDepthPointLocalM':seam.tolist(),'sourceTriangleId':faceparents[frozenset(chain[crossing:crossing+2])],'crestSourceEdgeIds':list(chain[imax])})

 # Trace the explicit authored depth points through their actual source surface.
 vertex_neighbors={}
 for a,b in np.unique(np.sort(f[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0):
  vertex_neighbors.setdefault(int(a),[]).append(int(b));vertex_neighbors.setdefault(int(b),[]).append(int(a))
 anchors=[]
 for r in profiles:
  ids=f[r['sourceTriangleId']];anchors.append(int(ids[np.argmin(np.linalg.norm(p[ids]-r['innerDepthPointLocalM'],axis=1))]))
 loop=[]
 for start,end in zip(anchors,anchors[1:]+anchors[:1]):
  aa,bb=p[start],p[end];direction=bb-aa;length2=direction@direction
  if start==end:continue
  t=np.clip((p-aa)@direction/length2,0,1);distance=np.linalg.norm(p-(aa+t[:,None]*direction),axis=1)
  cost={start:0.};prev={};queue=[(0.,start)]
  while queue:
   value,v=heapq.heappop(queue)
   if value!=cost[v]:continue
   if v==end:break
   for w in vertex_neighbors[v]:
    if distance[w]>.008:continue
    candidate=value+np.linalg.norm(p[w]-p[v])*(1+(max(distance[v],distance[w])/.002)**2)
    if candidate<cost.get(w,float('inf')):cost[w]=candidate;prev[w]=v;heapq.heappush(queue,(candidate,w))
  assert end in prev,(side,start,end)
  path=[end]
  while path[-1]!=start:path.append(prev[path[-1]])
  loop.extend(path[::-1][:-1])
 # Adjacent shortest paths may share a one-edge approach to a guide.
 # Remove that literal retraced spur; reject nonlocal overlaps.
 while len(set(loop))!=len(loop):
  repeated=next(v for v in loop if loop.count(v)>1);loc=[i for i,v in enumerate(loop) if v==repeated]
  assert len(loc)==2 and loc[1]-loc[0]<=3,(side,'nonlocal self-overlap',loc)
  del loop[loc[0]:loc[1]]
 assert len(set(loop))==len(loop)
 barrier={tuple(sorted((a,b))) for a,b in zip(loop,loop[1:]+loop[:1])}
 edge=f[:,((0,1),(1,2),(2,0))].reshape(-1,2);edge.sort(axis=1);key=edge[:,0].astype(np.int64)*len(p)+edge[:,1];order=np.argsort(key);pair=order.reshape(-1,2);assert np.all(key[pair[:,0]]==key[pair[:,1]])
 adj=np.empty(len(edge),np.int32);adj[pair[:,0]]=pair[:,1]//3;adj[pair[:,1]]=pair[:,0]//3
 blocked=np.isin(key,np.array([a*len(p)+b for a,b in barrier]));adj[blocked]=-1;adj=adj.reshape(-1,3)
 inside=np.zeros(len(f),bool);seed=selection['sides'][side]['seedTriangleId'];inside[seed]=1;pending=deque([seed])
 while pending:
  fid=pending.popleft()
  for j in adj[fid]:
   if j>=0 and not inside[j]:inside[j]=1;pending.append(int(j))
 assert 0<inside.sum()<len(f)
 loop=np.array(loop);print(side,'retire',inside.sum(),'boundary',len(loop),'lip221988retired',inside[np.any(f==221988,axis=1)].tolist(),flush=True)
 print(side,'loop localbounds',p[loop].min(0),p[loop].max(0),'crestRange',min(r['crestLocalM'][2] for r in profiles),max(r['crestLocalM'][2] for r in profiles),'sourceupperremoved',int((inside & (tri[:,:,2].max(1)>.09)).sum()),flush=True)
 np.savez_compressed('/tmp/boot83-mouth-'+side+'.npz',loopOriginalVertexIds=loop,retiredOriginalFaceIds=np.flatnonzero(inside),localLoopPoints=p[loop]);Path('/tmp/boot83-mouth-'+side+'.json').write_text(json.dumps(profiles,indent=2))
