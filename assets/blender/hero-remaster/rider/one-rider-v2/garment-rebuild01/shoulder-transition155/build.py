"""One bounded shoulder transition, CPU only. Keeps all protected source bytes."""
from pathlib import Path
from collections import defaultdict, deque
import hashlib, json, struct, time
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
REPO=Path('/Users/raynos/projects/games/rockhop')
RUN=ROOT/'garment-rebuild01/shoulder-transition155';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/shoulder-transition155'
SOURCE=ROOT/'rig-adapter01/body-bind34/rider.glb';CAGE=ROOT/'garment-rebuild01/cage04/fit04.npz'
assert not (RUN/'transition.npz').exists(),'One bounded attempt; preserve archive'
start=time.monotonic();raw=SOURCE.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def acc(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 assert 'byteStride' not in v and 'sparse' not in a
 return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],width)
def prim(i):
 p=doc['meshes'][0]['primitives'][i];a=p['attributes'];P=acc(a['POSITION']);W=np.zeros((len(P),19));J=acc(a['JOINTS_0']);V=acc(a['WEIGHTS_0'])
 for k in range(4):W[np.arange(len(P)),J[:,k]]+=V[:,k]
 return P,acc(p['indices']).reshape(-1,3),W,acc(a['NORMAL']),acc(a['TEXCOORD_0'])
P0,T0,W0,N0,U0=prim(0);HP,HT,HW,HN,HU=prim(2)
globalP,inv=np.unique(np.concatenate([P0,HP]),axis=0,return_inverse=True);hoodInv=inv[len(P0):]
rings=json.loads((OUT.parent/'neck-boundary-audit154/literal-rings.json').read_text());sring=rings['sourceMaterialInterfaces'][0]['orderedRing']
shell=json.loads((OUT.parent/'neck-boundary-audit154/native-transition-shells.json').read_text())[-1]
f=np.load(CAGE);P=f['positions'].copy();W=f['weights'].copy();Q=f['quads'];UV=f['uvLoops'].reshape(-1,4,2)
removed=np.array(shell['removedQuadIDs']);keep=np.ones(len(Q),bool);keep[removed]=False;kept=Q[keep];nring=shell['newBoundaryComponents'][0]['orderedRing']
def edgeuses(faces):
 out=defaultdict(list)
 for i,face in enumerate(faces):
  for k in range(len(face)):a,b=int(face[k]),int(face[(k+1)%len(face)]);out[tuple(sorted([a,b]))].append((i,a,b))
 return out
def orient(ring,uses,reverse):
 ring=list(ring);u=uses[tuple(sorted(ring[:2]))][0]
 if (tuple(ring[:2])==u[1:])==reverse:ring=list(reversed(ring))
 return ring
sring=orient(sring,edgeuses(hoodInv[HT]),True);nring=orient(nring,edgeuses(kept),False)
# Rotate each loop to anatomical front (+gameX); choose four cyclic landmarks.
def parameters(points,ring):
 ring=np.array(ring);pts=points[ring];idx=int(np.argmax(pts[:,0]));ring=np.roll(ring,-idx);pts=points[ring]
 anchors=[0,int(np.argmax(pts[:,2])),int(np.argmin(pts[:,0])),int(np.argmin(pts[:,2]))]
 if not all(a<b for a,b in zip(anchors,anchors[1:])):
  anchors=[0,int(np.argmin(pts[:,2])),int(np.argmin(pts[:,0])),int(np.argmax(pts[:,2]))]
 assert all(a<b for a,b in zip(anchors,anchors[1:])),('Noncyclic anatomical landmarks',anchors)
 anchors.append(len(ring));t=np.zeros(len(ring))
 for j in range(4):
  ids=np.arange(anchors[j],anchors[j+1]+1)%len(ring);dist=np.linalg.norm(np.diff(pts[ids],axis=0),axis=1);cs=np.r_[0,np.cumsum(dist)]/dist.sum()
  t[ids[:-1]]=j/4+cs[:-1]/4
 return ring,t,anchors
sr,st,sa=parameters(globalP,sring);nr,nt,na=parameters(P,nring)
# Both loop orders must be compatible; no independent closest-point correspondence.
assert np.sign(np.sum(np.cross(globalP[sr]-globalP[sr].mean(0),np.roll(globalP[sr],-1,axis=0)-globalP[sr].mean(0))[:,1]))==np.sign(np.sum(np.cross(P[nr]-P[nr].mean(0),np.roll(P[nr],-1,axis=0)-P[nr].mean(0))[:,1]))
def interp(t,values,at):
 return np.array([np.interp(at,np.r_[t,1],np.r_[values[:,d],values[0,d]]) for d in range(values.shape[1])]).T
hoodAliases=np.array([np.where(hoodInv==i)[0][0] for i in sr]);SP=HP[hoodAliases];SW=HW[hoodAliases];SN=HN[hoodAliases];SU=HU[hoodAliases]
center=SP[:,[0,2]].mean(0);target=interp(st,SP,nt);target[:,[0,2]]=center+(target[:,[0,2]]-center)*1.10;target[:,1]-=.055
# Coherent local panel deformation: fixed outer loop, zero at graph shell5,
# harmonic displacement across shells1..4. No source surface snapping.
adj=defaultdict(set)
for face in kept:
 for k in range(4):a,b=int(face[k]),int(face[(k+1)%4]);adj[a].add(b);adj[b].add(a)
dist={int(i):0 for i in nr};queue=deque(dist)
while queue:
 i=queue.popleft()
 if dist[i]>=5:continue
 for j in adj[i]:
  if j not in dist:dist[j]=dist[i]+1;queue.append(j)
D=np.zeros_like(P);D[nr]=target-P[nr];interior=[i for i,d in dist.items() if 0<d<5];index={i:k for k,i in enumerate(interior)};A=lil_matrix((len(interior),len(interior)));B=np.zeros((len(interior),3))
for i,k in index.items():
 for j in adj[i]:
  weight=1/max(np.linalg.norm(P[i]-P[j]),1e-5);A[k,k]+=weight
  if j in index:A[k,index[j]]-=weight
  else:B[k]+=weight*D[j]
D[interior]=spsolve(A.tocsr(),B);newNative=P+D
outerAtSource=interp(nt,target,st);outerW=interp(nt,W[nr],st)
positions=[newNative];weights=[W];sourceIDs=[np.full(len(P),-1)];nativeIDs=[np.arange(len(P))]
ringIDs=[];normFixed=[];uvProtected=[]
for fraction in [0.,.25,.5,.75]:
 offset=sum(len(x) for x in positions);ringIDs.append(np.arange(offset,offset+len(SP)))
 positions.append(SP*(1-fraction)+outerAtSource*fraction);weights.append(SW*(1-fraction)+outerW*fraction)
 sourceIDs.append(hoodAliases.copy() if fraction==0 else np.full(len(SP),-1));nativeIDs.append(np.full(len(SP),-1))
Pout=np.concatenate(positions);Wout=np.concatenate(weights);tris=[];scope=[];cornerUV=[]
for quad,uv in zip(kept,UV[keep]):
 for ids in [[0,1,2],[0,2,3]]:tris.append(quad[ids]);scope.append(0);cornerUV.append(uv[ids])
transitionStart=len(tris)
for r in range(3):
 a,b=ringIDs[r],ringIDs[r+1]
 for i in range(len(sr)):
  j=(i+1)%len(sr)
  for tri in [[a[i],a[j],b[j]],[a[i],b[j],b[i]]]:tris.append(tri);scope.append(1);cornerUV.append(np.zeros((3,2)))
# Ordered zipper reduction: merge anatomical normalized arc parameters.
a=ringIDs[-1];i=j=0
while i<len(a) or j<len(nr):
 ni=st[(i+1)%len(a)] if i+1<len(a) else 1.;nj=nt[(j+1)%len(nr)] if j+1<len(nr) else 1.
 if i<len(a) and (j==len(nr) or ni<=nj):tri=[a[i%len(a)],a[(i+1)%len(a)],nr[j%len(nr)]];i+=1
 else:tri=[a[i%len(a)],nr[(j+1)%len(nr)],nr[j%len(nr)]];j+=1
 tris.append(tri);scope.append(1);cornerUV.append(np.zeros((3,2)))
T=np.array(tris);scope=np.array(scope);cross=np.cross(Pout[T[:,1]]-Pout[T[:,0]],Pout[T[:,2]]-Pout[T[:,0]]);area=np.linalg.norm(cross,axis=1)/2
norm=np.zeros_like(Pout)
for k in range(3):np.add.at(norm,T[:,k],cross)
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-20);norm[ringIDs[0]]=SN
# Native original loop UVs are exact. New transition UV is an explicit bake chart;
# protected boundary original UVs are retained separately, not silently reassigned.
triUV=np.array(cornerUV)
allParameter=np.full(len(Pout),np.nan);allParameter[nr]=nt
for ids in ringIDs:allParameter[ids]=st
for k in range(transitionStart,len(T)):
 tri=T[k];u=allParameter[tri].copy()
 if u.max()-u.min()>.5:u[u<.5]+=1
 fraction=[]
 for v in tri:
  fraction.append(1. if v<len(P) else (v-len(P))//len(sr)/4)
 triUV[k]=np.c_[u,fraction]
np.savez_compressed(RUN/'transition.npz',positions=Pout,triangles=T,weights=Wout,normals=norm,triangleUV=triUV,
 nativeVertexIDs=np.concatenate(nativeIDs),protectedHoodVertexIDs=np.concatenate(sourceIDs),triangleScope=scope,
 removedNativeQuadIDs=removed,protectedRingIDs=ringIDs[0],nativeOuterRingIDs=nr,
 protectedHoodPositions=HP,protectedHoodNormals=HN,protectedHoodUV=HU,protectedHoodWeights=HW,protectedHoodTriangles=HT,
 protectedBoundaryOriginalUV=SU,protectedBoundaryOriginalNormals=SN,protectedBoundaryOriginalWeights=SW)
uses=edgeuses(T);nonman=[e for e,u in uses.items() if len(u)>2];direction=[e for e,u in uses.items() if len(u)==2 and u[0][1:]==u[1][1:]]
# Boundary from new garment and protected hood has opposite incidence by construction.
seamChecks=[];huses=edgeuses(hoodInv[HT])
for i in range(len(sr)):
 j=(i+1)%len(sr);hu=huses[tuple(sorted([int(sr[i]),int(sr[j])]))][0]
 seamChecks.append(hu[1:]==(int(sr[j]),int(sr[i])))
report={'status':'One bounded NEW native shoulder transition; unaccepted until actual visual/motion review'}
report.update({'sourceSHA256':hashlib.sha256(raw).hexdigest(),'cageSHA256':hashlib.sha256(CAGE.read_bytes()).hexdigest(),
 'transitionSHA256':hashlib.sha256((RUN/'transition.npz').read_bytes()).hexdigest(),
 'settings':{'nativeRemovedWholeQuads':removed.tolist(),'nativeFaceShells':8,'protectedRingCount':307,'nativeOuterRingCount':60,
 'cyclicSourceLandmarks':sa,'cyclicNativeLandmarks':na,'loopParameter':'Front/lateral/rear/opposite lateral quarter arcs, cumulative edge length within each quarter',
 'outerTargetRadialScale':1.10,'outerTargetDownwardM':.055,'panelDeformation':'Inverse-edge Laplacian displacement, ring fixed, graph-distance5 boundary zero',
 'intermediateRingFractions':[0.,.25,.5,.75],'reduction':'Ordered zipper by normalized cyclic landmark arc'},
 'sourceBytesUnchanged':SOURCE.read_bytes()==raw,'protectedSeamMaxPositionDeltaM':float(abs(Pout[ringIDs[0]]-SP).max()),
 'protectedSeamWeightMaxDelta':float(abs(Wout[ringIDs[0]]-SW).max()),'protectedSeamNormalMaxDelta':float(abs(norm[ringIDs[0]]-SN).max()),
 'all307SeamEdgesOppositeHoodWinding':all(seamChecks),'nonmanifoldEdges':len(nonman),'sameDirectionSharedEdges':len(direction),
 'vertices':len(Pout),'nativeTriangles':int((scope==0).sum()),'transitionTriangles':int((scope==1).sum()),
 'minimumTriangleAreaM2':float(area.min()),'zeroAreaTriangles':int((area<1e-12).sum()),
 'nativeDisplacementQuantilesM':np.quantile(np.linalg.norm(D,axis=1),[0,.5,.95,1]).tolist(),
 'movingUVUnbaked':True,'diagnosticOriginalBodyPatchFacesUsed':0,'seconds':time.monotonic()-start,
 'limits':['New transition only; no source head/hood edits or high-detail PBR bake.','No complete GLB, appearance score, contact/physics/Garage validation; actual34 CPU probes required.']})
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
