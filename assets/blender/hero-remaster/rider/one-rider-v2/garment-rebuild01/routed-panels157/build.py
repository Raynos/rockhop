"""ONE new routed four-hole surface. No native crewneck deformation or source faces."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,struct,time
import numpy as np
from scipy.spatial import ConvexHull,cKDTree
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=ROOT/'garment-rebuild01/routed-panels157';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/routed-panels157';assert not (RUN/'routed-instrument.npz').exists(),'One attempt; retain archive'
raw=(ROOT/'rig-adapter01/body-bind34/rider.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];assert 'byteStride' not in v and 'sparse' not in a
 return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
def uses(faces):
 result=defaultdict(list)
 for i,face in enumerate(faces):
  for k in range(len(face)):a,b=int(face[k]),int(face[(k+1)%len(face)]);result[tuple(sorted([a,b]))].append((i,a,b))
 return result
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-20)
def prim(i):
 p=doc['meshes'][0]['primitives'][i];a=p['attributes'];P=acc(a['POSITION']);J=acc(a['JOINTS_0']);V=acc(a['WEIGHTS_0']);W=np.zeros((len(P),19))
 for k in range(4):W[np.arange(len(P)),J[:,k]]+=V[:,k]
 return P,acc(p['indices']).reshape(-1,3),acc(a['NORMAL']),acc(a['TEXCOORD_0']),W
BP,BT,BN,BU,BW=prim(0);HP,HT,HN,HU,HW=prim(2);sourceAll,iv=np.unique(np.concatenate([BP,HP]),axis=0,return_inverse=True);bi=iv[:len(BP)];hi=iv[len(BP):]
literal=json.loads((OUT.parent/'neck-boundary-audit154/literal-rings.json').read_text());sr=literal['sourceMaterialInterfaces'][0]['orderedRing'];hu=uses(hi[HT]);sr=list(sr)
if tuple(sr[:2])==hu[tuple(sorted(sr[:2]))][0][1:]:sr=list(reversed(sr))
c=np.load(ROOT/'garment-rebuild01/cage04/fit04.npz');NP=c['positions'];NW=c['weights'];Q=c['quads'];oldtri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]]);cross=np.cross(NP[oldtri[:,1]]-NP[oldtri[:,0]],NP[oldtri[:,2]]-NP[oldtri[:,0]]);NN=np.zeros_like(NP)
for k in range(3):np.add.at(NN,oldtri[:,k],cross)
NN=unit(NN);contract=json.loads((OUT.parent/'upper-yoke156/boundary-feasibility.json').read_text());upperQuadIDs=np.array(contract['nativeRemovedQuadIDs']);keep=np.ones(len(Q),bool);keep[upperQuadIDs]=False;keptQ=Q[keep]
# Native lower topology stays exact. Only its three open upper interfaces are used.
nativeLoops=[r for r in contract['nativeUpperYoke']['loops'] if r['vertices']!=20];chest=next(r for r in nativeLoops if r['vertices']==36);left=next(r for r in nativeLoops if r['centroid'][2]>.2);right=next(r for r in nativeLoops if r['centroid'][2]<-.2)
def anchor(points,ring):
 ring=np.array(ring);p=points[ring].astype(np.float64);z=(p[:,2].min()+p[:,2].max())/2;hits=[]
 for i in range(len(ring)):
  j=(i+1)%len(ring);d0=p[i,2]-z;d1=p[j,2]-z
  if d0*d1<=0 and abs(d0-d1)>1e-12:
   a=d0/(d0-d1);pt=p[i]+a*(p[j]-p[i]);hits.append((float(pt[0]),i,a,pt.tolist()))
 assert hits;_,i,a,pt=max(hits,key=lambda r:r[0]);first=i if a<.5 else (i+1)%len(ring);ring=np.roll(ring,-first);p=points[ring].astype(np.float64);length=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);t=np.r_[0,np.cumsum(length[:-1])]/length.sum();return ring,t,pt
sr,st,sanchor=anchor(sourceAll,sr);aliases=np.array([np.where(hi==i)[0][0] for i in sr]);sourceBoundary=HP[aliases]
# Source cloth tangent: only regional original body adjacency guides first row,
# no original source triangle topology/skin is inherited as upper garment.
badj=defaultdict(set)
for tri in bi[BT]:
 for k in range(3):a,b=int(tri[k]),int(tri[(k+1)%3]);badj[a].add(b);badj[b].add(a)
shared=set(sr.tolist());directions=[]
for i,v in enumerate(sr):
 neighbors=sorted(badj[v]-shared);assert neighbors,'No adjacent source cloth tangent'
 d=sourceAll[neighbors].mean(0)-sourceAll[v];normal=HN[aliases[i]].astype(float);d-=normal*(d@normal);assert np.linalg.norm(d)>1e-9;directions.append(d/np.linalg.norm(d))
sourceFirst=sourceBoundary+.012*np.array(directions)
nadj=defaultdict(set)
for q in Q[upperQuadIDs]:
 for k in range(4):a,b=int(q[k]),int(q[(k+1)%4]);nadj[a].add(b);nadj[b].add(a)
loops=[{'name':'hood','center':np.array([0.,1.,0.]),'angle':25.,'native':False,'ring':sr,'t':st,'world':sourceBoundary,'first':sourceFirst,'weights':HW[aliases],'normals':HN[aliases],'anchor':sanchor}]
for name,r,axis in [('chest',chest,[0,-1,0]),('leftArm',left,[0,0,1]),('rightArm',right,[0,0,-1])]:
 ids,t,a=anchor(NP,r['orderedBoundaryFaceWinding']);border=set(ids.tolist());dirs=[]
 for v in ids:
  incident=Q[upperQuadIDs][np.isin(Q[upperQuadIDs],v).any(1)];assert len(incident);d=NP[incident].mean(axis=(0,1))-NP[v];d-=NN[v]*(d@NN[v]);assert np.linalg.norm(d)>1e-9;dirs.append(d/np.linalg.norm(d))
 loops.append({'name':name,'center':np.array(axis,dtype=float),'angle':30.,'native':True,'ring':ids,'t':t,'world':NP[ids],'first':NP[ids]+.012*np.array(dirs),'weights':NW[ids],'normals':NN[ids],'anchor':a})
param=[];world=[];locked=[];weight=[];vertexGroups=[];boundaryParamIDs=[];firstParamIDs=[]
for group,r in enumerate(loops):
 center=r['center'];u=np.array([1.,0,0]);v=np.cross(center,u);theta=-2*np.pi*r['t'];circle=np.cos(theta)[:,None]*u+np.sin(theta)[:,None]*v
 r['boundaryParamIDs']=np.arange(len(param),len(param)+len(r['ring']));boundaryParamIDs.extend(r['boundaryParamIDs']);
 for p,w,k in zip(np.cos(np.deg2rad(r['angle']))*center+np.sin(np.deg2rad(r['angle']))*circle,r['world'],r['weights']):param.append(p);world.append(w);weight.append(k);locked.append(True);vertexGroups.append(group)
 r['firstParamIDs']=np.arange(len(param),len(param)+len(r['ring']));firstParamIDs.extend(r['firstParamIDs'])
 for p,w,k in zip(np.cos(np.deg2rad(r['angle']+4))*center+np.sin(np.deg2rad(r['angle']+4))*circle,r['first'],r['weights']):param.append(p);world.append(w);weight.append(k);locked.append(True);vertexGroups.append(-1)
# New uniform routed parameter mesh, omitting caps and locked tangent rows.
count=1800;golden=np.pi*(3-np.sqrt(5));centers=np.array([r['center'] for r in loops]);cut=np.cos(np.deg2rad([r['angle']+5.5 for r in loops]));nativeTree=cKDTree(NP[np.unique(Q[upperQuadIDs])]);nativeUpperIDs=np.unique(Q[upperQuadIDs])
def scaffold(d):
 x,y,z=d;core=np.array([.63+.15*x,1.30+.145*y,.235*z]);az=abs(z);side=1 if z>=0 else -1
 if az<=.50:return core
 u=np.clip((az-.50)/(np.cos(np.deg2rad(30))-.50),0,1);smooth=u*u*(3-2*u);radius=np.sqrt(max(1-z*z,1e-8));tube=np.array([.63+.074*x/radius,1.445-.285*u+.020*y/radius,side*(.205+.073*u+.072*y/radius)])
 return core*(1-smooth)+tube*smooth
for i in range(count):
 y=1-2*(i+.5)/count;r=np.sqrt(1-y*y);d=np.array([r*np.cos(i*golden),y,r*np.sin(i*golden)])
 if np.any(centers@d>cut):continue
 p=scaffold(d);param.append(d);world.append(p);weight.append(NW[nativeUpperIDs[nativeTree.query(p)[1]]]);locked.append(False);vertexGroups.append(-1)
param=np.array(param);target=np.array(world);world=np.array(world);weight=np.array(weight);locked=np.array(locked);vertexGroups=np.array(vertexGroups);hull=ConvexHull(param)
missing=sorted(set(range(len(param)))-set(hull.vertices.tolist()))
if missing:(OUT/'parameter-hull-setup-failure.json').write_text(json.dumps({'kind':'Parameter hull omits near-duplicate floating-point circle samples before any geometry export','missingParameterIDs':missing,'groups':[int(vertexGroups[i]) for i in missing],'parameterVertexCount':len(param),'hullVertexCount':len(hull.vertices)},indent=2)+'\n')
assert not missing,'Every parameter point must participate'
tri=hull.simplices.copy();normals=hull.equations[:,:3];cross=np.cross(param[tri[:,1]]-param[tri[:,0]],param[tri[:,2]]-param[tri[:,0]]);flip=np.einsum('ij,ij->i',cross,normals)<0;tri[flip]=tri[flip][:,[0,2,1]]
cap=(vertexGroups[tri[:,0]]>=0)&(vertexGroups[tri[:,0]]==vertexGroups[tri[:,1]])&(vertexGroups[tri[:,1]]==vertexGroups[tri[:,2]]);tri=tri[~cap];adj=defaultdict(set)
for f in tri:
 for k in range(3):a,b=int(f[k]),int(f[(k+1)%3]);adj[a].add(b);adj[b].add(a)
# New interior absolute embedding: source/cage-guided routed anatomical target
# plus local fairness, with all true boundaries/tangent rows fixed from outset.
free=np.where(~locked)[0];index={v:k for k,v in enumerate(free)};A=lil_matrix((len(free),len(free)));B=np.zeros((len(free),3));skinB=np.zeros((len(free),19));screen=.12
for i,k in index.items():
 degree=len(adj[i]);A[k,k]=degree*(1+screen);B[k]+=degree*screen*target[i];skinB[k]+=degree*screen*weight[i]
 for j in adj[i]:
  if j in index:A[k,index[j]]-=1
  else:B[k]+=world[j];skinB[k]+=weight[j]
world[free]=spsolve(A.tocsr(),B);weight[free]=spsolve(A.tocsr(),skinB);weight=np.maximum(weight,0);weight/=np.maximum(weight.sum(1,keepdims=True),1e-20)
for r in loops:world[r['boundaryParamIDs']]=r['world'];weight[r['boundaryParamIDs']]=r['weights']
# Map native boundary aliases directly to unchanged original native vertex IDs.
P=list(NP);W=list(NW);mapIDs=np.full(len(param),-1,dtype=int)
for r in loops:
 if r['native']:mapIDs[r['boundaryParamIDs']]=r['ring']
for i in range(len(param)):
 if mapIDs[i]<0:mapIDs[i]=len(P);P.append(world[i]);W.append(weight[i])
P=np.array(P);W=np.array(W);newT=mapIDs[tri];nativeT=np.array([q[k] for q in keptQ for k in [[0,1,2],[0,2,3]]]);T=np.concatenate([nativeT,newT]);cross=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);N=np.zeros_like(P)
for k in range(3):np.add.at(N,T[:,k],cross)
N=unit(N);hoodIDs=mapIDs[loops[0]['boundaryParamIDs']];N[hoodIDs]=HN[aliases];UV=c['uvLoops'].reshape(-1,4,2);triangleUV=np.zeros((len(T),3,2));triangleUV[:len(nativeT)]=np.array([uv[k] for uv in UV[keep] for k in [[0,1,2],[0,2,3]]])
np.savez_compressed(RUN/'routed-instrument.npz',positions=P,triangles=T,weights=W,normals=N,triangleUV=triangleUV,newTriangleIDs=np.arange(len(nativeT),len(T)),parameterPositions=param,parameterTriangles=tri,parameterToOutputVertexIDs=mapIDs,
 protectedRingIDs=hoodIDs,protectedHoodAliases=aliases,protectedHoodPositions=HP,protectedHoodTriangles=HT,protectedHoodNormals=HN,protectedHoodUV=HU,protectedHoodWeights=HW,nativeRetainedQuadIDs=np.where(keep)[0],nativeRemovedYokeQuadIDs=upperQuadIDs,nativeOriginalVertexIDs=np.arange(len(NP)))
edge=uses(T);nonman=sum(len(u)>2 for u in edge.values());same=sum(len(u)==2 and u[0][1:]==u[1][1:] for u in edge.values());hoodSeam=[]
for i in range(307):
 j=(i+1)%307;u=hu[tuple(sorted([int(sr[i]),int(sr[j])]))][0];newu=edge[tuple(sorted([int(hoodIDs[i]),int(hoodIDs[j])]))];hoodSeam.append(len(newu)==1 and newu[0][1:]==(int(hoodIDs[i]),int(hoodIDs[j])) and u[1:]==(int(sr[j]),int(sr[i])))
area=np.linalg.norm(cross,axis=1)/2
report={'status':'ONE newly routed anatomical panel instrument; rest crossing gate pending, not accepted', 'sourceSHA256':hashlib.sha256(raw).hexdigest(),'sourceUnchanged':(ROOT/'rig-adapter01/body-bind34/rider.glb').read_bytes()==raw,'instrumentSHA256':hashlib.sha256((RUN/'routed-instrument.npz').read_bytes()).hexdigest(),'settings':{'construction':'New four-hole spherical-cap constrained tessellation + C19/cage04 anatomical torso and separate routed shoulders; native20collar absent and no source fused cloth faces inherited','capAnglesDegrees':[25,30,30,30],'tangentRowParameterAdvanceDegrees':4,'worldTangentRowDistanceM':.012,'candidateInteriorSamples':1800,'screenedTargetStiffness':screen,'shapeGuide':'Cage04 H21-silhouette widths + freshC19 shoulder-to-arm routing; original source body adjacency used only to continue hood cloth tangent','nativeRemovedQuadIDs':upperQuadIDs.tolist(),'fixedLoops':[{ 'name':r['name'],'count':len(r['ring']),'sourceOrNativeIDs':r['ring'].tolist(),'parameterIDs':r['boundaryParamIDs'].tolist(),'tangentParameterIDs':r['firstParamIDs'].tolist(),'frontSagittalAnchor':r['anchor']} for r in loops]},'parameterVertices':len(param),'newYokeTriangles':len(newT),'allTriangles':len(T),'nonmanifoldEdges':nonman,'sameDirectionSharedEdges':same,'all307OppositeHoodWinding':all(hoodSeam),'minimumAreaM2':float(area.min()),'zeroAreaTriangles':int((area<1e-12).sum()),'protectedSeamPositionMaxDeltaM':float(abs(P[hoodIDs]-HP[aliases]).max()),'protectedSeamNormalMaxDelta':float(abs(N[hoodIDs]-HN[aliases]).max()),'protectedSeamWeightMaxDelta':float(abs(W[hoodIDs]-HW[aliases]).max()),'nativeAllOriginalPositionsExact':bool(np.array_equal(P[:len(NP)],NP)),'nativeAllOriginalWeightsExact':bool(np.array_equal(W[:len(NP)],NW)),'newYokeParameterIndicesNotAssetAcceptance':True,'limits':['Diagnostic instrument only until rest crossings are clear; no GLB/PBR bake/face/body quality pass.','Original head immutable source reference, unchanged original hood attrs stored exact.','New yoke UV zeros placeholder; retained native per-corner UV exact.','Three-boundary tangent directions/new topology are deliberate routing, not inherited source armpit topology.']}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n');print(json.dumps({k:v for k,v in report.items() if k!='settings'},indent=2))
