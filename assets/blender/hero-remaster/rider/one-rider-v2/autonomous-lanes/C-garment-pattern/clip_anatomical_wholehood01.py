"""One NEW donor01 anatomical exclusion, true edge clipping, no color selection.

Source-only geometry feasibility. No receiver, neck binding or runtime edits.
"""
from pathlib import Path
import numpy as np,json,hashlib,datetime
BASE=Path('/Users/raynos/projects/games/rockhop');A=BASE/'assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/C-garment-pattern';O=BASE/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/wholehood01-anatomical-trial02';O.mkdir(exist_ok=True);R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern/wholehood01-anatomical-trial02');R.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=R.parent/'wholehood01-trial01/donor-source.npz';d=np.load(S);v=d['vertices'];f=d['faces'];uv=d['uv'];fullv,inv=np.unique(v,axis=0,return_inverse=True);f=inv[f]
# Measured source witnesses. Geometric restrictions identify the witness region,
# not an assertion that every sample has a definitive anatomical label.
rear=(fullv[:,1]>.12)&(abs(fullv[:,0])<.19)&(fullv[:,2]>1.33);q=fullv[rear];hoodmax=float(q[:,2].max());cap=hoodmax+.008
neck=(abs(fullv[:,0])<.045)&(fullv[:,1]>-.075)&(fullv[:,1]<.095)&(fullv[:,2]>1.49)&(fullv[:,2]<1.525);nq=fullv[neck]
levels=np.array([1.445,1.49,1.515,1.55,cap]);rx=np.array([.077,.082,.098,.125,.137]);ry=np.array([.095,.108,.127,.147,.154]);cy=np.array([.022,.020,.012,.010,.008])
def ellipse(p):
 z=p[2];ax=np.interp(z,levels,rx);ay=np.interp(z,levels,ry);c=np.interp(z,levels,cy);return (p[0]/ax)**2+((p[1]-c)/ay)**2-1
def floor(p):return p[2]-(1.445+(1.335-1.445)*np.clip((p[1]-.03)/(.12-.03),0,1))
constraints=[('left yoke side',lambda p:p[0]+.19),('right yoke side',lambda p:.19-p[0]),('receiver matching whole yoke floor',floor),('measured top above rear cloth',lambda p:cap-p[2]),('outside measured anatomical neck/jaw volume',ellipse)]
vertices=fullv.tolist();triangles=[];triangleuv=[];origins=[];original=[];intersections={};counts={};splitparents=[]
def intersect(a,b,fun,tag):
 ia,pa,ua=a;ib,pb,ub=b;sa,sb=fun(pa),fun(pb);lo=0.;hi=1.
 # Real edge root for nonplanar ellipse, not centroid-face rejection.
 for _ in range(36):
  t=(lo+hi)/2;s=fun(pa+t*(pb-pa))
  if (s>=0)==(sa>=0):lo=t
  else:hi=t
 t=(lo+hi)/2;co=pa+t*(pb-pa);key=(tag,min(ia,ib),max(ia,ib));idx=intersections.get(key)
 if idx is None:idx=len(vertices);vertices.append(co.tolist());intersections[key]=idx
 return (idx,co,ua+t*(ub-ua))
for fi,face in enumerate(f):
 nodes=[(int(k),fullv[k],uv[fi,j]) for j,k in enumerate(face)];changed=False
 for tag,fun in constraints:
  if not nodes:break
  out=[]
  for a,b in zip(nodes,nodes[1:]+nodes[:1]):
   sa,sb=fun(a[1]),fun(b[1])
   if sa>=0:out.append(a)
   if (sa>=0)!=(sb>=0):out.append(intersect(a,b,fun,tag));changed=True;counts[tag]=counts.get(tag,0)+1
  nodes=out
 if len(nodes)<3:continue
 for k in range(1,len(nodes)-1):
  tri=[nodes[0],nodes[k],nodes[k+1]];ids=[a[0] for a in tri]
  if len(set(ids))<3:continue
  if np.linalg.norm(np.cross(tri[1][1]-tri[0][1],tri[2][1]-tri[0][1]))<1e-12:continue
  triangles.append(ids);triangleuv.append([a[2] for a in tri]);origins.append(fi);original.append(not changed and len(nodes)==3)
vv=np.array(vertices);ff=np.array(triangles,np.int32);uu=np.array(triangleuv);orig=np.array(origins);pres=np.array(original)
# Select proven largest position-connected garment component. Tiny loose source
# face remnants are reported/removed; source cloth islands are not invented.
parent=np.arange(len(vv))
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
def union(a,b):
 a,b=root(int(a)),root(int(b))
 if a!=b:parent[b]=a
for a,b,c in ff:union(a,b);union(a,c)
roots=np.array([root(int(t[0])) for t in ff]);u,ct=np.unique(roots,return_counts=True);major=u[np.argmax(ct)];keep=roots==major;excluded=orig[~keep];ff=ff[keep];uu=uu[keep];orig=orig[keep];pres=pres[keep]
ed=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);ue,ec=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);np.savez_compressed(R/'true-clipped-hood.npz',vertices=vv,faces=ff,uv=uu,sourceFaceOrigins=orig,uncutSourceFace=pres,removedLooseSourceFaceIDs=excluded,boundaryEdges=ue[ec==1])
srcd=np.load(S);sourcef=srcd['faces'];sourcev=srcd['vertices'];protected=int(pres.sum());delta=0.
for i in np.where(pres)[0]:delta=max(delta,float(np.abs(vv[ff[i]]-sourcev[sourcef[orig[i]]]).max()));assert np.array_equal(uu[i],srcd['uv'][orig[i]])
assert delta==0
rep={'status':'UNACCEPTED source-only anatomical clipped hood; inspect before any new binding','actualStartUTC':'2026-10-01 03:38:33 UTC','deadlineUTC':'2026-10-01 04:08:33 UTC','finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'CPUThreads':2,'GPU':False,'oldH21_4LineageRetiredFailures':15,'newDonorFailuresRetained':{'imageLookupSetup':1,'colorMaskSeparation':1},'colorThresholdStopped':True,'sourceArrays':str(S),'sourceArraysSHA256':sha(S),'receiverBodyUnchanged':True,'receiverProtectedTriangles':40386,'measuredRearClothWitness':{'region':'Y>.120,absX<.190,Z>1.330, original source geometric witness','count':len(q),'minXYZ':q.min(0).tolist(),'maxXYZ':q.max(0).tolist(),'topZ':hoodmax},'measuredLowerCentralNeckWitness':{'region':'absX<.045,-.075<Y<.095,1.490<Z<1.525; explicit candidate skin witness requiring visual confirmation','count':len(nq),'minXYZ':nq.min(0).tolist(),'maxXYZ':nq.max(0).tolist()},'declaredRemovalVolume':{'type':'Z-varying anatomical ellipse; retain outside ellipse and below source rearclothtop+8mm','levelsZ':levels.tolist(),'radiusX':rx.tolist(),'radiusY':ry.tolist(),'centerY':cy.tolist(),'topZ':cap,'wholeYokeFloor':'front1.445m→rear1.335m alongY.03→.12;absX<=.19m','colorIgnored':True,'edgeRoots':'36 bisections on real source edges; UV barylinear on same original triangle, never different chart corners'},'actualClippingCounts':counts,'retainedTriangles':len(ff),'exactUncutSourceTriangles':protected,'exactUncutPositionMaxDelta':delta,'exactUncutUV':True,'looseComponentsBeforeRemoval':sorted(ct.tolist(),reverse=True),'removedLooseTriangleCount':int((~keep).sum()),'boundaryEdges':int((ec==1).sum()),'nonmanifoldEdges':int((ec>2).sum()),'geometrySHA256':sha(R/'true-clipped-hood.npz'),'recipeSHA256':sha(__file__),'limitations':['Anatomical ellipse is explicitly authored against source witnesses; visual exclusion must pass, not inferred from scalar counts.','Largest component filtering removes disconnected source remnants; no global remesh or reducer.','No neck binding, body assembly, rig, sourceUV remapping or raw detail transfer yet. Retained raw316248triangle source untouched.','Native sizing head is not final WHITE identity; no head yet assembled.']}
(O/'anatomical-clip-report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
