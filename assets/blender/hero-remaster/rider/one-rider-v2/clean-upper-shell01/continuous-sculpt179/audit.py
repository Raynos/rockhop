"""Actual frozen sculpt NPZ and exported GLB literal audit; no mutations."""
import numpy as np,json,hashlib,struct,math,time
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/continuous-sculpt179');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179')
def glb(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);b=raw[28+n:]
 def array(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];k={'SCALAR':1,'VEC3':3,'VEC4':4,'VEC2':2}[a['type']];return np.ndarray((a['count'],k),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*k),np.dtype(dt).itemsize)).copy()
 q=j['meshes'][0]['primitives'][0];p=array(q['attributes']['POSITION']);p=np.column_stack((p[:,0],-p[:,2],p[:,1]));f=array(q['indices']).reshape(-1,3);p,inv=np.unique(p,axis=0,return_inverse=True);return p,inv[f],j

def intersect(t,u):
 for A,B in [(t,u),(u,t)]:
  v0,v1,v2=B;e1=v1-v0;e2=v2-v0
  for k in range(3):
   origin=A[k];d=A[(k+1)%3]-origin;h=np.cross(d,e2);det=e1@h
   if abs(det)<1e-12:continue
   s=origin-v0;u0=s@h/det;q=np.cross(s,e1);v=d@q/det;dist=e2@q/det
   if 1e-7<u0<1-1e-7 and 1e-7<v<1-1e-7 and u0+v<1-1e-7 and 1e-7<dist<1-1e-7:return True
 return False

def audit(p,f,name):
 tri=p[f];edges={};orient={};adj=[set() for _ in p]
 for i,t in enumerate(f):
  for x,y in zip(t,np.roll(t,-1)):
   x=int(x);y=int(y);e=tuple(sorted((x,y)));edges.setdefault(e,[]).append(i);orient.setdefault(e,[]).append(x<y);adj[x].add(y);adj[y].add(x)
 seen=set();components=0
 for x in range(len(p)):
  if x in seen:continue
  components+=1;todo=[x];seen.add(x)
  while todo:
   for y in adj[todo.pop()]:
    if y not in seen:seen.add(y);todo.append(y)
 boundary={e:ids for e,ids in edges.items() if len(ids)==1};badj={}
 for x,y in boundary:badj.setdefault(x,set()).add(y);badj.setdefault(y,set()).add(x)
 seen=set();cycles=[];raw=[]
 for x in badj:
  if x in seen:continue
  todo=[x];seen.add(x);c=[]
  while todo:
   w=todo.pop();c.append(w)
   for y in badj[w]:
    if y not in seen:seen.add(y);todo.append(y)
  raw.append(c);cycles.append({'vertices':len(c),'degreeTwoEverywhere':all(len(badj[x])==2 for x in c),'min':p[c].min(0).tolist(),'max':p[c].max(0).tolist()})
 area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 bvh=BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True,epsilon=0.0);other=BVHTree.FromPolygons(p.tolist(),f.tolist(),all_triangles=True,epsilon=0.0);pairs=bvh.overlap(other);cross=[];one=[];tested=0
 for i,j in pairs:
  if i>=j:continue
  shared=set(f[i])&set(f[j])
  if len(shared)>=2:continue
  tested+=1
  if intersect(tri[i],tri[j]):
   (one if shared else cross).append([i,j])
 gaps=[]
 for z in [1.10,1.18,1.26]:
  points=[]
  for a,b in edges:
   A=p[a];B=p[b]
   if (A[2]-z)*(B[2]-z)<0:points.append(A+(B-A)*((z-A[2])/(B[2]-A[2])))
  ys=np.sort(np.unique(np.round(np.abs(np.array(points)[:,1]),7)));diff=np.diff(ys);ids=np.where((ys[:-1]>.10)&(ys[:-1]<.25)&(diff>.008))[0]
  gaps.append({'height':z,'lateralGapCandidates':[[float(ys[i]),float(ys[i+1]),float(diff[i])] for i in ids],'interpretation':'Cross-section separated lateral intervals only; parent must classify torso/sleeve ownership, not global collision margin.'})
 (R/(name+'-private-boundaries.json')).write_text(json.dumps({'boundaryVertexIDs':raw,'strictZeroSharedWitnesses':cross,'strictOneSharedWitnesses':one},indent=2))
 return {'vertices':len(p),'triangles':len(f),'components':components,'boundaryEdges':len(boundary),'boundaryComponents':cycles,'nonmanifoldEdges':sum(len(ids)>2 for ids in edges.values()),'wrongTwoFaceWindingEdges':sum(len(ids)==2 and orient[e][0]==orient[e][1] for e,ids in edges.items()),'degenerateBelow1e12':int((area<1e-12).sum()),'minimumAreaM2':float(area.min()),'strictZeroSharedCrossings':len(cross),'strictOneSharedCrossings':len(one),'bvhPairs':len(pairs),'strictPairsTested':tested,'crossSectionGaps':gaps}
a=np.load(R/'sculpt-shell01.npz');auth=audit(a['p'],a['f'],'authored');p,f,j=glb(R/'shell01.glb');actual=audit(p,f,'exported');rep={'status':'FROZEN_LITERAL_AUDIT_NO_VISUAL_ACCEPTANCE','authored':auth,'actualExportedExactPositionWeld':actual,'sha256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['sculpt-shell01.npz','shell01.glb','neutral-assembly01.glb']},'protectedSeams':'Actual cuff source-row interpolation inprivatecorrespondence; source donor topology not sewn. Hood andhem joins open/unaccepted.','limits':'Strict interior transverse predicates; coplanar overlap and endpoint touches excluded, no donor-shell collision count or motion qualification.'};(E/'literal-audit.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep))
