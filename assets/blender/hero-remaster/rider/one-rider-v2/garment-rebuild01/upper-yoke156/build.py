"""ONE full four-boundary yoke Dirichlet construction; no annulus shape offsets."""
from pathlib import Path
from contextlib import redirect_stdout
import io,runpy,json,hashlib
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
RECIPE=Path(__file__).parent
with redirect_stdout(io.StringIO()):s=runpy.run_path(str(RECIPE/'feasibility.py'))
ROOT=s['ROOT'];OUT=s['OUT'];RUN=s['RUN'];SOURCE=s['source'];raw=s['raw'];NP=s['NP'];Q=s['Q'];f=s['f'];report=s['report'];acc=s['acc'];doc=s['doc'];uses=s['uses']
assert not (RUN/'yoke-instrument.npz').exists(),'Only one construction attempt; preserve result'
# Native upper panel has exactly four real anatomical boundaries.
assert report['nativeFourBoundaryYokeFeasible']
upperIDs=np.array(report['nativeRemovedQuadIDs']);upperMask=np.zeros(len(Q),bool);upperMask[upperIDs]=True
collar=next(r for r in report['nativeUpperYoke']['loops'] if r['vertices']==20)
collarIDs=np.array(collar['orderedBoundaryFaceWinding']);removeNeck=np.array([i for i in upperIDs if np.isin(Q[i],collarIDs).any()])
keep=np.ones(len(Q),bool);keep[removeNeck]=False;KQ=Q[keep];nativeT=np.array([q[k] for q in KQ for k in [[0,1,2],[0,2,3]]])
# New307 loop has opposite original protected hood winding. Original native collar
# loop is reversed because it describes the removed panel's inner boundary.
hp=doc['meshes'][0]['primitives'][2];a=hp['attributes'];HP=acc(a['POSITION']);HT=acc(hp['indices']).reshape(-1,3);HN=acc(a['NORMAL']);HU=acc(a['TEXCOORD_0']);J=acc(a['JOINTS_0']);V=acc(a['WEIGHTS_0']);HW=np.zeros((len(HP),19))
for k in range(4):HW[np.arange(len(J)),J[:,k]]+=V[:,k]
SP,hoodInv=np.unique(HP,axis=0,return_inverse=True);hu=uses(hoodInv[HT]);boundary=[e for e,u in hu.items() if len(u)==1];adj={}
for x,y in boundary:adj.setdefault(x,set()).add(y);adj.setdefault(y,set()).add(x)
# Identify protected lower307 by exact source material shared positions.
bodyPositions=s['P'];shared=set(map(tuple,bodyPositions))&set(map(tuple,HP));seed=min(i for i,p in enumerate(SP) if tuple(p) in shared);sr=[];prev=None;cur=seed
for _ in range(307):sr.append(cur);nxt=min(adj[cur]-({prev} if prev is not None else set()));prev,cur=cur,nxt
assert cur==sr[0] and len(sr)==307
if tuple(sr[:2])==hu[tuple(sorted(sr[:2]))][0][1:]:sr=list(reversed(sr))
# Sagittal FRONT edge crossing (+X) establishes correspondence. This chooses a
# plane-crossing, not extrema of the entire irregular source perimeter.
def anchor(points,ring):
 ring=np.array(ring);p=points[ring];centerZ=(p[:,2].min()+p[:,2].max())/2;hits=[]
 for i in range(len(ring)):
  j=(i+1)%len(ring);d0=p[i,2]-centerZ;d1=p[j,2]-centerZ
  if d0*d1<=0 and abs(d0-d1)>1e-12:
   alpha=d0/(d0-d1);cross=p[i]+alpha*(p[j]-p[i]);hits.append((cross[0],i,alpha,cross.tolist()))
 assert hits;_,i,alpha,cross=max(hits,key=lambda x:x[0]);first=i if alpha<.5 else (i+1)%len(ring);ring=np.roll(ring,-first);p=points[ring];length=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);t=np.r_[0,np.cumsum(length[:-1])]/length.sum()
 return ring,t,{'sagittalZ':centerZ,'frontCrossingGame':cross,'firstOriginalVertex':int(ring[0])}
sr,st,sa=anchor(SP,sr);cr,ct,ca=anchor(NP,collarIDs)
# Opposite-facing native original collar is the lower edge of removed collar row;
# initial boundary samples lie on its original edge polyline.
def interpolate(t,values,at):return np.array([np.interp(at,np.r_[t,1],np.r_[values[:,d],values[0,d]]) for d in range(values.shape[1])]).T
sourceAliases=np.array([np.where(hoodInv==i)[0][0] for i in sr]);boundaryPositions=HP[sourceAliases]
initialBoundary=interpolate(ct,NP[cr],st)
# Get next native20 boundary, oriented as surviving native faces (new bridge
# traverses that edge in reverse); polar orientation checked against source ring.
audit=s['boundaryAudit'](NP,KQ);inner=next(r for r in audit['loops'] if r['vertices']==20 and r['bounds'][0][1]>1.45)
nr,nt,na=anchor(NP,inner['orderedBoundaryFaceWinding'])
def orientation(points):return np.sign(np.sum(np.cross(points-points.mean(0),np.roll(points,-1,axis=0)-points.mean(0))[:,1]))
assert orientation(SP[sr])==orientation(NP[nr]),'Mismatch would twist yoke topology'
ringIDs=np.arange(len(NP),len(NP)+307);Pinit=np.concatenate([NP,initialBoundary]);T=list(nativeT);i=j=0
while i<307 or j<len(nr):
 ti=st[i+1] if i+1<307 else 1.;tj=nt[j+1] if j+1<len(nr) else 1.
 if i<307 and (j==len(nr) or ti<=tj):tri=[ringIDs[i%307],ringIDs[(i+1)%307],nr[j%len(nr)]];i+=1
 else:tri=[ringIDs[i%307],nr[(j+1)%len(nr)],nr[j%len(nr)]];j+=1
 T.append(tri)
T=np.array(T);adj={i:set() for i in np.unique(T)}
for tri in T:
 for k in range(3):x,y=int(tri[k]),int(tri[(k+1)%3]);adj[x].add(y);adj[y].add(x)
upperVertices=set(Q[upperMask].reshape(-1));lowerVertices=set(Q[~upperMask].reshape(-1));free=sorted(upperVertices-lowerVertices-set(collarIDs));free=[i for i in free if i in adj];index={i:k for k,i in enumerate(free)}
D=np.zeros_like(Pinit);D[ringIDs]=boundaryPositions-initialBoundary;A=lil_matrix((len(free),len(free)));B=np.zeros((len(free),3))
for i,k in index.items():
 for j in adj[i]:
  weight=1/max(np.linalg.norm(Pinit[i]-Pinit[j]),1e-5);A[k,k]+=weight
  if j in index:A[k,index[j]]-=weight
  else:B[k]+=weight*D[j]
D[free]=spsolve(A.tocsr(),B);P=Pinit+D;P[ringIDs]=boundaryPositions
# Preserve native lower weights. Dense field inside new yoke is harmonically
# interpolated from protected hood and native interface Dirichlet constraints.
W=np.concatenate([f['weights'],HW[sourceAliases]]);weightsB=np.zeros((len(free),19))
for i,k in index.items():
 for j in adj[i]:
  if j not in index:weightsB[k]+=W[j]/max(np.linalg.norm(Pinit[i]-Pinit[j]),1e-5)
W[free]=spsolve(A.tocsr(),weightsB);W=np.maximum(W,0);W/=np.maximum(W.sum(1,keepdims=True),1e-20);W[:len(NP)][list(lowerVertices)]=f['weights'][list(lowerVertices)];W[ringIDs]=HW[sourceAliases]
cross=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);area=np.linalg.norm(cross,axis=1)/2;norm=np.zeros_like(P)
for k in range(3):np.add.at(norm,T[:,k],cross)
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-20);norm[ringIDs]=HN[sourceAliases]
sourceReferenceCross=np.cross(Pinit[T[:,1]]-Pinit[T[:,0]],Pinit[T[:,2]]-Pinit[T[:,0]]);dots=np.einsum('ij,ij->i',cross,sourceReferenceCross)/(np.maximum(np.linalg.norm(cross,axis=1)*np.linalg.norm(sourceReferenceCross,axis=1),1e-20))
allUses=uses(T);nonman=sum(len(u)>2 for u in allUses.values());same=sum(len(u)==2 and u[0][1:]==u[1][1:] for u in allUses.values())
UV=f['uvLoops'].reshape(-1,4,2);triUV=np.zeros((len(T),3,2));triUV[:len(nativeT)]=np.array([uv[k] for uv in UV[keep] for k in [[0,1,2],[0,2,3]]])
# Save diagnostic coordinates only until rest intersection check passes. This is
# not an exported assembled rider or unaccepted model advertised as rig-ready.
np.savez_compressed(RUN/'yoke-instrument.npz',positions=P,triangles=T,weights=W,normals=norm,triangleUV=triUV,sourceReferencePositions=Pinit,
 protectedRingIDs=ringIDs,protectedHoodAliases=sourceAliases,protectedHoodPositions=HP,protectedHoodTriangles=HT,protectedHoodNormals=HN,protectedHoodUV=HU,protectedHoodWeights=HW,
 nativeUnchangedVertexIDs=np.array(sorted(lowerVertices)),nativeUpperPanelQuadIDs=upperIDs,nativeRemovedCollarQuadIDs=removeNeck,freeDeformedNativeVertexIDs=np.array(free),
 newTriangleIDs=np.arange(len(nativeT),len(T)),nativeOriginalVertexIDs=np.arange(len(NP)))
report={'status':'One four-boundary upper-yoke construction instrument; rest intersection gate required before motion/asset export', 'sourceSHA256':hashlib.sha256(raw).hexdigest(),'sourceUnchanged':SOURCE.read_bytes()==raw,'cageSHA256':hashlib.sha256((ROOT/'garment-rebuild01/cage04/fit04.npz').read_bytes()).hexdigest(),'instrumentSHA256':hashlib.sha256((RUN/'yoke-instrument.npz').read_bytes()).hexdigest(),
 'settings':{'nativeUpperYokeQuads':720,'heightWholeFaceSelectionM':1.20,'protectedSourceEndpoints':307,'nativeFixedInterfaces':[36,22,22], 'shapeTarget':'Source-fitted cage04 low-frequency clothing scaffold + exact retained H21 hood lower surface. Original H21 upper cloth is shape-only because its source cut has fused arm/chest boundary.', 'correspondence':'Sagittal front edge intersection and oriented cumulative edge length, no perimeter-extrema quarter or radial/downward offsets', 'sourceAnchor':sa,'nativeCollarAnchor':ca,'nativeInnerAnchor':na,'deformation':'Whole upper720-quad four-boundary inverse-edge Dirichlet displacement; all lower/native interface vertices fixed','newSkin':'Dense19 harmonic Dirichlet on same four-boundary local upper panel, protected seam/native lower fields exact'},
 'nativeOutsidePanelMaxPositionDeltaM':float(abs(P[list(lowerVertices)]-NP[list(lowerVertices)]).max()), 'nativeOutsidePanelMaxWeightDelta':float(abs(W[list(lowerVertices)]-f['weights'][list(lowerVertices)]).max()), 'protectedSeamMaxPositionDeltaM':float(abs(P[ringIDs]-HP[sourceAliases]).max()),'protectedSeamWeightMaxDelta':float(abs(W[ringIDs]-HW[sourceAliases]).max()),'protectedSeamNormalMaxDelta':float(abs(norm[ringIDs]-HN[sourceAliases]).max()),
 'nonmanifoldEdges':nonman,'sameDirectionSharedEdges':same,'zeroAreaTriangles':int((area<1e-12).sum()),'minimumAreaM2':float(area.min()),'restOppositionToScaffold':int((dots<0).sum()),'nativeDisplacementQuantilesM':np.quantile(np.linalg.norm(D[:len(NP)],axis=1),[0,.5,.95,1]).tolist(),'vertices':len(P),'triangles':len(T),'sourceGeometryReusedAsUpperCloth':False,'UVLimits':'Lower/native per-corner UV exact; new307-to20 closure chart unbaked and zero placeholder. Original source hoodUV exact separate.', 'limits':['Diagnostic construction instrument only. No complete GLB or appearance/rig approval.','Rest crossings must be inspected before all480 motion probe.','Original head immutable source reference, no source-patch assembly.']}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n');print(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
