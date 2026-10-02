"""Literal frozen-prototype audit, no mesh edits or rendering."""
import numpy as np,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan')
E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan')
a=np.load(R/'drafted-shell01.npz');p=a['p'];f=a['f'];panels=a['panel'];tri=p[f];lo=tri.min(1);hi=tri.max(1)
edges={}
for fi,t in enumerate(f):
 for x,y in zip(t,np.roll(t,-1)):edges.setdefault(tuple(sorted((int(x),int(y)))),[]).append(fi)
area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
bad=[{'edge':list(e),'faceIDs':ids,'panels':panels[ids].tolist(),'positions':p[list(e)].tolist()} for e,ids in edges.items() if len(ids)>2]
boundary=[e for e,ids in edges.items() if len(ids)==1];adj={}
for x,y in boundary:adj.setdefault(x,set()).add(y);adj.setdefault(y,set()).add(x)
seen=set();bc=[]
for x in adj:
 if x in seen:continue
 todo=[x];seen.add(x);c=[]
 while todo:
  w=todo.pop();c.append(w)
  for y in adj[w]:
   if y not in seen:seen.add(y);todo.append(y)
 bc.append({'vertices':len(c),'degreeTwoEverywhere':all(len(adj[x])==2 for x in c),'min':p[c].min(0).tolist(),'max':p[c].max(0).tolist()})
def intersects(t,u):
 # Strict interior segment/triangle intersections; coplanar overlap not claimed.
 for A,B,C in [(t,u,None),(u,t,None)]:
  v0,v1,v2=B;e1=v1-v0;e2=v2-v0
  for k in range(3):
   origin=A[k];d=A[(k+1)%3]-origin;h=np.cross(d,e2);det=e1@h
   if abs(det)<1e-12:continue
   s=origin-v0;u0=s@h/det;q=np.cross(s,e1);v=d@q/det;dist=e2@q/det
   if 1e-7<u0<1-1e-7 and 1e-7<v<1-1e-7 and u0+v<1-1e-7 and 1e-7<dist<1-1e-7:return True
 return False
cross=[];candidatePairs=0
for i in range(len(f)):
 js=np.where(np.all(hi[i]>=lo[i+1:]-1e-9,axis=1)&np.all(lo[i]<=hi[i+1:]+1e-9,axis=1))[0]+i+1
 for j in js:
  if set(f[i])&set(f[j]):continue
  candidatePairs+=1
  if intersects(tri[i],tri[j]):cross.append([i,int(j)])
rep={'status':'REJECTED_LITERAL_TOPOLOGY_FREEZE','shellNPZSHA256':hashlib.sha256((R/'drafted-shell01.npz').read_bytes()).hexdigest(),'shellGLBSHA256':hashlib.sha256((R/'shell01.glb').read_bytes()).hexdigest(),'neutralAssemblySHA256':hashlib.sha256((R/'neutral-assembly01.glb').read_bytes()).hexdigest(),'nonmanifoldEdgeCount':len(bad),'nonmanifoldWitnesses':bad,'boundaryEdges':len(boundary),'boundaryConnectedComponents':bc,'degenerateAreaBelow1e12':int((area<1e-12).sum()),'minimumTriangleAreaM2':float(area.min()),'maximumEdgeLengthM':float(max(np.linalg.norm(p[e[0]]-p[e[1]]) for e in edges)),'strictNonadjacentTransverseCrossings':len(cross),'crossingWitnessFacePairs':cross,'crossingBroadphasePairs':candidatePairs,'crossingLimits':'Strict segment-triangle interiors only; coplanar overlaps, endpoint touch, one-corner crossings and donor-shell intersections not certified.','armTorsoSpace':'Parametric drafts use torso side Y=.19 atZ1.26; sleeve underarmY=.245atZ1.28.45mm lateral nominal root separation sewn by gusset. This is not a measured minimum clearance.','protectedSeams':'Source hood/lower/cuffs/gloves remain separate donor components; no physically sewn donor joins and no contact acceptance.','decision':'One meaningful geometry output fails. No geometry re-run or rigging. Parent sole silhouette/integration judge.'}
(E/'literal-audit.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items() if k not in ['nonmanifoldWitnesses','crossingWitnessFacePairs']}))
