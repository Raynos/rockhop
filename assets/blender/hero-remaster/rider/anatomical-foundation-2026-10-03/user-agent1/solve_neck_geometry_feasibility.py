"""One fixed geometry-only screened-biharmonic solve; no skin or capture."""
import hashlib, heapq, json, time
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[6]; owned=Path(__file__).resolve().parent
qa=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out=ev/'neck-interface102';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
proposal=ev/'neck-interface101/proposal.json'; scope_path=qa/'body59/proposal.json'
field_path=owned/'neck-interface27/triangulated-neck-fields.npz'
inputs=[proposal,scope_path,field_path,owned/'neck-interface28/auxiliary-restored.blend',qa/'body52/native-fields.npz',ev/'neck-interface96/ordered-boundaries.npz',qa/'neck68/FINDING.md',qa/'neck65/FINDING.md']
pins={str(p.relative_to(root)):sha(p) for p in inputs}
assert sha(proposal)=='7366452caf44e9f09b2b2d817a9a4e7c221fb29761ce1842efda4e7a99f5eeb1'
assert sha(scope_path)=='5f563c032791a9426c0447a2b8c818b140fd62e56a621fd4b81efd461cfdefa6'
assert sha(inputs[3])=='60036a17b60db73b66abc140c943c2589d2eb2c91340e5c50bc59bd6a7e6a5e4'
assert not (out/'geometry-solve.json').exists()
start=time.monotonic(); f=dict(np.load(field_path));n=np.load(inputs[4]);r=np.load(inputs[5]);scope=json.loads(scope_path.read_text())['preciseInitialAuthoringMargin']
NB,NH=len(f['bodyRestXYZ']),len(f['headRestXYZ']); hp=n['protectedHeadXYZ']; alias=r['headPositionAlias']; he=set(scope['headInitialBoundaryLedNativeVertexIDs'])
virtual=np.unique(alias[list(he)]);partial={int(v) for v in virtual if not set(np.flatnonzero(alias==v))<=he}
head_free=np.array(sorted(v for v in he if int(alias[v]) not in partial)+list(range(len(hp),NH)))
body_free=np.r_[scope['bodyExistingRenderedNativeVertices'],np.arange(9037,NB)].astype(int)
# Reuse only declared physical seam and original head exact-position quotient.
bids=np.arange(NB)+238;hids=np.arange(NH)+238+NB+int(alias.max())+1
hids[:len(alias)]=alias+238+NB
for key,ids in [('body',bids),('head',hids)]:
 sid=f[key+'SeamPhysicalIDs'];ids[sid>=0]=sid[sid>=0]
raw_ids=np.r_[bids,hids];_,representative,mapping=np.unique(raw_ids,return_index=True,return_inverse=True)
rawP=np.vstack([f['bodyRestXYZ'],f['headRestXYZ']]).astype(float);P=rawP[representative];N=len(P)
assert np.array_equal(P[mapping],rawP)
mutable=np.zeros(NB+NH,dtype=bool);mutable[body_free]=True;mutable[NB+head_free]=True
fixed=np.zeros(N,dtype=bool);np.logical_or.at(fixed,mapping,~mutable);free=np.flatnonzero(~fixed);NF=len(free)
T=np.vstack([mapping[:NB][f['bodyTriangles']],mapping[NB:][f['headTriangles']]])
assert (np.diff(np.sort(T,axis=1),axis=1)>0).all()
# Exact anatomy reference. No canonical reference is assigned to a fixed vertex.
canonical=n['originalFullXYZ'].astype(float);cp=canonical[n['originalFullTriangles']]
names=n['boneNames'].tolist();neck=n['rigRest'][names.index('neck'),:3,3];head=n['rigRest'][names.index('head'),:3,3]
def section_ray(p):
 z=p[2];origin=(neck+(head-neck)*((z-neck[2])/(head[2]-neck[2])))[:2]
 direction=p[:2]-origin;direction/=np.linalg.norm(direction)
 faces=cp[(cp[:,:,2].min(axis=1)<z)&(cp[:,:,2].max(axis=1)>=z)];hits=[]
 for face in faces:
  points=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if (face[i,2]<z)!=(face[j,2]<z):points.append(face[i]+(face[j]-face[i])*((z-face[i,2])/(face[j,2]-face[i,2])))
  a,b=np.array(points)[:,:2];matrix=np.column_stack([direction,a-b])
  if abs(np.linalg.det(matrix))<1e-14:continue
  distance,fraction=np.linalg.solve(matrix,a-origin)
  if distance>0 and -1e-9<=fraction<=1+1e-9:hits.append(distance)
 hits=np.unique(np.round(hits,10));assert len(hits)==1
 return np.r_[origin+direction*hits[0],z]
def interp(u,knots,points):
 j=max(int(np.searchsorted(knots,u,side='right')-1),0);end=knots[j+1] if j+1<len(knots) else 1.
 t=(u-knots[j])/(end-knots[j]);return (1-t)*points[j]+t*points[(j+1)%len(points)]
Qraw=rawP.copy();bp=n['renderedBodyXYZ'];refs=f['bodyAttributeEdgeSources']
for v in body_free:
 a,b,t=refs[v];Qraw[v]=(1-t)*bp[int(a)]+t*bp[int(b)]
# Classify outer/inner by source topology distance, not spatial nearest-point transfer.
vt=alias[n['protectedHeadTriangles']];adj=[set() for _ in range(int(alias.max())+1)]
for a,b,c in vt:adj[a].update([int(b),int(c)]);adj[b].update([int(a),int(c)]);adj[c].update([int(a),int(b)])
def boundary_distance(seeds):
 d=np.full(len(adj),np.inf);owner=np.full(len(adj),-1);queue=[]
 for i,v in enumerate(seeds):d[v]=0;owner[v]=i;heapq.heappush(queue,(0.,int(v),i))
 while queue:
  distance,v,origin=heapq.heappop(queue)
  if distance!=d[v] or origin!=owner[v]:continue
  for w in adj[v]:
   cost=distance+np.linalg.norm(hp[r['headAliasRepresentative'][v]]-hp[r['headAliasRepresentative'][w]])
   if cost<d[w]:d[w]=cost;owner[w]=origin;heapq.heappush(queue,(cost,w,origin))
 return d,owner
outer=f['headOriginalFrontOrderedIDs'];inner=r['innerHeadOrderedNativeRepresentatives'][::-1];inner=np.roll(inner,-int(np.argmax(hp[inner,0])))
outer_d,_=boundary_distance(alias[outer]);inner_d,inner_owner=boundary_distance(alias[inner])
ilength=np.linalg.norm((np.roll(hp[inner],-1,axis=0)-hp[inner])[:,:2],axis=1);iu=np.r_[0.,np.cumsum(ilength[:-1])]/ilength.sum()
for v in head_free:
 if v>=len(hp):continue
 target=section_ray(hp[v].astype(float))
 if inner_d[alias[v]]<outer_d[alias[v]]:
  u=iu[inner_owner[alias[v]]];offset=interp(u,iu,hp[inner])-interp(u,f['headOriginalKnots'],hp[outer]);target+=offset
 Qraw[NB+v]=target
shared=np.array([interp(u,f['bodyOriginalKnots'],bp[f['bodyOriginalFrontOrderedIDs']]) for u in f['commonU']])
for key,offset in [('body',0),('head',NB)]:
 sid=f[key+'SeamPhysicalIDs'];ids=np.flatnonzero(sid>=0);Qraw[offset+ids]=shared[sid[ids]]
cap=np.flatnonzero(f['headAttributeEdgeSources'][:,0]<0);assert len(cap)==1
Qraw[NB+cap[0]]=Qraw[NB+inner].mean(axis=0)
Q=Qraw[representative];Q[fixed]=P[fixed]
# Reference masses and cotangent stiffness. Topology/coefficients are frozen once.
points=P[T];cross=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]);twice=np.linalg.norm(cross,axis=1)
assert (twice>0).all();mass=np.zeros(N)
for j in range(3):np.add.at(mass,T[:,j],twice/6)
edges=[];cot=[]
for i,j,k in [(0,1,2),(1,2,0),(2,0,1)]:
 edges.append(np.sort(T[:,[i,j]],axis=1));cot.append(.5*np.einsum('ij,ij->i',points[:,i]-points[:,k],points[:,j]-points[:,k])/twice)
edges=np.concatenate(edges);weights=np.concatenate(cot);E,inverse=np.unique(edges,axis=0,return_inverse=True);W=np.zeros(len(E));np.add.at(W,inverse,weights)
local=np.isin(T,free).any(axis=1);local_edges=np.unique(np.sort(np.concatenate([T[local][:,[0,1]],T[local][:,[1,2]],T[local][:,[2,0]]]),axis=1),axis=0)
h=float(np.median(np.linalg.norm(P[local_edges[:,0]]-P[local_edges[:,1]],axis=1)))
# L = M^-1 K. h^4 L^T M L equals h^4 K^T M^-1 K.
diag=np.zeros(N);KP=np.zeros_like(P)
for a,b in [(0,1),(1,0)]:
 np.add.at(diag,E[:,a],W);np.add.at(KP,E[:,a],W[:,None]*(P[E[:,a]]-P[E[:,b]]))
row_ids=np.unique(np.r_[free,E[np.isin(E,free).any(axis=1)].ravel()]);row_index=np.full(N,-1);row_index[row_ids]=np.arange(len(row_ids));col_index=np.full(N,-1);col_index[free]=np.arange(NF)
K=np.zeros((len(row_ids),NF));K[row_index[free],np.arange(NF)]=diag[free]
for a,b in [(0,1),(1,0)]:
 valid=col_index[E[:,b]]>=0;np.add.at(K,(row_index[E[valid,a]],col_index[E[valid,b]]),-W[valid])
G=np.diag(mass[free])+h**4*(K.T@(K/mass[row_ids,None]));rhs=mass[free,None]*(Q[free]-P[free])-h**4*(K.T@(KP[row_ids]/mass[row_ids,None]))
# Exact border first-difference constraints from fully exterior reference faces.
exterior=fixed[T].all(axis=1);normals=np.zeros((N,3))
for j in range(3):np.add.at(normals,T[exterior,j],cross[exterior])
constraints=[[] for _ in free]
for a,b in [(0,1),(1,0)]:
 valid=(col_index[E[:,a]]>=0)&fixed[E[:,b]]
 for v,w in E[valid][:,[a,b]]:
  norm=normals[w];length=np.linalg.norm(norm)
  if length>0:constraints[col_index[v]].append(norm/length)
owners=[];directions=[];rank_counts={0:0,1:0,2:0,3:0}
for i,ns in enumerate(constraints):
 if ns:
  _,s,vh=np.linalg.svd(np.array(ns),full_matrices=True);rank=int((s>1e-10).sum());basis=vh[rank:].T
 else:rank=0;basis=np.eye(3)
 rank_counts[rank]+=1
 for direction in basis.T:owners.append(i);directions.append(direction)
owners=np.array(owners);directions=np.array(directions);print('GEOMETRY_SYSTEM',N,NF,len(owners),rank_counts,flush=True)
H=G[owners[:,None],owners[None,:]]*(directions@directions.T);b=np.einsum('ij,ij->i',directions,rhs[owners]);x=np.linalg.solve(H,b)
residual=float(np.linalg.norm(H@x-b)/max(np.linalg.norm(b),1e-30));assert residual<1e-8
D=np.zeros((NF,3));np.add.at(D,owners,x[:,None]*directions);solved=P.copy();solved[free]+=D
constraint_residual=max([abs(float(np.dot(D[i],normal))) for i,ns in enumerate(constraints) for normal in ns]+[0.])
assert constraint_residual<1e-10 and np.array_equal(solved[fixed],P[fixed])
solved=solved.astype(np.float32);result=solved[mapping];assert np.array_equal(result[~mutable],rawP[~mutable].astype(np.float32))
fields=dict(f);fields['bodyRestXYZ']=result[:NB];fields['headRestXYZ']=result[NB:];fields['sharedRestFloat32XYZ']=solved[mapping[:NB][np.flatnonzero(f['bodySeamPhysicalIDs']>=0)][np.argsort(f['bodySeamPhysicalIDs'][f['bodySeamPhysicalIDs']>=0])]]
assert len(fields['sharedRestFloat32XYZ'])==238
np.savez_compressed(out/'geometry-fields.npz',**fields)
np.savez_compressed(out/'solve-witnesses.npz',physicalRawToNode=mapping,referenceXYZ=P,anatomicalReferenceXYZ=Q,solvedXYZ=solved,freePhysicalNodes=free,fixedPhysicalNodes=np.flatnonzero(fixed),cotangentEdges=E,cotangentWeights=W,lumpedAreas=mass,variableOwner=owners,variableDirection=directions,displacementXYZ=D)
new_points=solved[T].astype(float);new_cross=np.cross(new_points[:,1]-new_points[:,0],new_points[:,2]-new_points[:,0]);new_area=np.linalg.norm(new_cross,axis=1)/2
orientation=np.einsum('ij,ij->i',cross,new_cross);bad=np.flatnonzero(orientation<=0)
report={'status':'UNACCEPTED_ONE_GEOMETRY_SOLVE_COMPLETE_REST_QUALIFICATION_PENDING','recipeSHA256':sha(__file__),'pins':pins,'elapsedS':time.monotonic()-start,'operator':'One frozen screened-biharmonic geometric solve, M+h^4 K^T M^-1 K; exact exterior and first-difference tangent subspace clamps. No weights touched.','physicalNodes':N,'freePhysicalNodes':NF,'degreesOfFreedom':len(owners),'tangentConstraintRanks':rank_counts,'sourceMedianLocalEdgeM':h,'normalizedLinearResidual':residual,'maximumTangentDisplacementResidualM':constraint_residual,'fieldsSHA256':sha(out/'geometry-fields.npz'),'solveWitnessSHA256':sha(out/'solve-witnesses.npz'),'outsideFloat32PositionsExact':True,'sourceWeightsAllExact':all(np.array_equal(fields[k],f[k]) for k in f if 'Weights' in k),'referenceTriangleMinimumAreaM2':float(new_area.min()),'referenceTrianglesAtOrBelow1e_14':int((new_area<=1e-14).sum()),'referenceNormalSignChanges':len(bad),'normalSignChangeGlobalTriangleIDs':bad.tolist(),'bodyChangedExistingIDs':np.flatnonzero((result[:9037]!=f['bodyRestXYZ'][:9037]).any(axis=1)).tolist(),'headChangedExistingIDs':np.flatnonzero((result[NB:NB+len(hp)]!=f['headRestXYZ'][:len(hp)]).any(axis=1)).tolist(),'maxPositionDeltaM':float(np.linalg.norm(solved.astype(float)-P,axis=1).max()),'limits':['Canonical Q is a fit objective for free nodes only; fixed surfaces are not claimed anatomical matches.','Single fixed operator, no skin solve, coefficient sweep, pose/capture/export/install/model/GPU/worker or promotion. Native save/reopen and rest contacts follow.','Reference normal sign change is relative to old normal, not proof of a topological winding reversal. All M0-M5 and original99failures open.']}
(out/'geometry-solve.json').write_text(json.dumps(report,indent=2)+'\n');assert pins=={p:sha(root/p) for p in pins}
print(json.dumps({k:report[k] for k in ['status','elapsedS','freePhysicalNodes','degreesOfFreedom','referenceTriangleMinimumAreaM2','referenceNormalSignChanges','maxPositionDeltaM']},indent=2))
