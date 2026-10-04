"""Verify frozen fields, energy stationarity and proposed collar; never solve."""
import hashlib,json
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck70/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
f=dict(np.load(asset/'neck-interface27/triangulated-neck-fields.npz'));c=dict(np.load(ev/'neck-interface102/candidate-fields-ancestry-corrected.npz'));initial=dict(np.load(asset/'neck-interface29/geometry-only-fields.npz'));g=dict(np.load(ev/'neck-interface102/geometry-fields.npz'));w=dict(np.load(ev/'neck-interface102/solve-witnesses.npz'));n=dict(np.load(qa/'body52/native-fields.npz'));reg=dict(np.load(ev/'neck-interface96/ordered-boundaries.npz'));scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];s=json.loads((qa/'neck68/source-assessment.json').read_text());owner=json.loads((ev/'neck-interface102/geometry-solve.json').read_text());request=json.loads((ev/'neck-interface102/expansion-request.json').read_text())
NB,NH=len(f['bodyRestXYZ']),len(f['headRestXYZ']);head_orig=len(n['protectedHeadXYZ']);body_orig=len(n['renderedBodyXYZ']);alias=reg['headPositionAlias'];head_free=np.r_[s['actualEditableHeadIDsAfterAliasProtection'],np.arange(head_orig,NH)];body_free=np.r_[scope['bodyExistingRenderedNativeVertices'],np.arange(body_orig,NB)];mutable=np.zeros(NB+NH,dtype=bool);mutable[body_free]=True;mutable[NB+head_free]=True
# Reconstruct a physical quotient by distinct body/head keys, exact head aliases,
# and the declared common seam. No spatial nearest-point merging is allowed.
keys=[]
for part,count in [('body',NB),('head',NH)]:
 for i in range(count):
  sid=int(f[part+'SeamPhysicalIDs'][i]);keys.append(('seam',sid) if sid>=0 else (part,int(alias[i]) if part=='head' and i<head_orig else i))
lookup={};ours=np.array([lookup.setdefault(k,len(lookup)) for k in keys]);mapping=w['physicalRawToNode'];forward={};reverse={}
for a,b in zip(ours,mapping):
 assert forward.setdefault(int(a),int(b))==b and reverse.setdefault(int(b),int(a))==a
assert len(lookup)==len(w['referenceXYZ'])==45178
raw=np.vstack([f['bodyRestXYZ'],f['headRestXYZ']]).astype(float);P=w['referenceXYZ'];Q=w['anatomicalReferenceXYZ'];free=w['freePhysicalNodes'];fixed=w['fixedPhysicalNodes'];assert np.array_equal(P[mapping],raw);is_fixed=np.zeros(len(P),dtype=bool);np.logical_or.at(is_fixed,mapping,~mutable);assert np.array_equal(fixed,np.flatnonzero(is_fixed)) and np.array_equal(free,np.flatnonzero(~is_fixed));assert len(free)==1236
assert np.array_equal(Q[fixed],P[fixed]);D=w['displacementXYZ'];solved=P.copy();solved[free]+=D;assert np.array_equal(solved.astype(np.float32),w['solvedXYZ']);result=w['solvedXYZ'][mapping];assert np.array_equal(result[:NB],c['bodyRestXYZ']) and np.array_equal(result[NB:],c['headRestXYZ']) and np.array_equal(result[~mutable],raw[~mutable].astype(np.float32))
changes={};corrections={}
for part,count,orig,allowed in [('body',NB,body_orig,body_free),('head',NH,head_orig,head_free)]:
 changed=np.flatnonzero(np.any(c[part+'RestXYZ']!=f[part+'RestXYZ'],axis=1));assert set(changed)<=set(allowed);assert np.array_equal(c[part+'RestXYZ'],g[part+'RestXYZ']);assert np.array_equal(c[part+'FixedReferenceTriangles'],f[part+'Triangles']);local=np.flatnonzero(np.isin(c[part+'Triangles'],allowed).any(axis=1));assert np.array_equal(local,c[part+'LocalTriangleIDs'])
 for label in ['Full','Four']:assert np.array_equal(c[part+label+'Weights'],f[part+label+'Weights'])
 for key in [part+'AttributeEdgeSources',part+'CornerAttributeEdgeSources',part+'CandidatePolygonToCheckpointPolygon',part+'CandidateCornerToCheckpointCorner',part+'SeamPhysicalIDs']:assert np.array_equal(c[key],f[key])
 for k in initial:
  if k!=part+'TriangleSourcePolygonIDs' and not k.endswith('TriangleSourcePolygonIDs'):assert np.array_equal(c[k],initial[k]),k
 assert np.array_equal(c[part+'TriangleCheckpointPolygonIDs'],initial[part+'TriangleSourcePolygonIDs'])
 cap=np.flatnonzero(f[part+'AttributeEdgeSources'][:,0]<0);cap_faces=np.flatnonzero(np.isin(c[part+'Triangles'],cap).any(axis=1));corrected=np.flatnonzero(c[part+'TriangleSourcePolygonIDs']!=initial[part+'TriangleSourcePolygonIDs']);assert np.array_equal(cap_faces,corrected) and (c[part+'TriangleSourcePolygonIDs'][cap_faces]==-1).all()
 changes[part]={'changedExistingIDs':changed[changed<orig].tolist(),'changedDerivedIDs':changed[changed>=orig].tolist(),'existingChanged':int((changed<orig).sum()),'derivedChanged':int((changed>=orig).sum()),'localTriangles':len(local),'retessellatedReferenceTriangleRows':int((c[part+'Triangles']!=f[part+'Triangles']).any(axis=1).sum())};corrections[part]={'correctedNewCapTriangleIDs':cap_faces.tolist(),'oldReceiptRetained':True,'geometryWeightsTrianglesIdenticalToInitial':True}
assert np.array_equal(c['boneNames'],f['boneNames']) and np.array_equal(c['rigRest'],f['rigRest']) and np.array_equal(c['rigWorld'],f['rigWorld'])
assert np.array_equal(c['headRestXYZ'][s['fixedHeadIDs']],f['headRestXYZ'][s['fixedHeadIDs']]) and np.array_equal(c['bodyRestXYZ'][s['fixedBodyIDs']],f['bodyRestXYZ'][s['fixedBodyIDs']])
assert np.array_equal(c['headRestXYZ'][s['pinnedAdmittedHeadIDs']],f['headRestXYZ'][s['pinnedAdmittedHeadIDs']])
# Rebuild mass and cotangent stiffness independently from original triangles.
T=np.vstack([mapping[:NB][f['bodyTriangles']],mapping[NB:][f['headTriangles']]]);tp=P[T];norm=np.cross(tp[:,1]-tp[:,0],tp[:,2]-tp[:,0]);twice=np.linalg.norm(norm,axis=1);mass=np.zeros(len(P));np.add.at(mass,T.ravel(),np.repeat(twice/6,3));assert np.allclose(mass,w['lumpedAreas'],rtol=1e-12,atol=1e-18)
edge_rows=[];weight_rows=[]
for a,b,o in [(1,2,0),(2,0,1),(0,1,2)]:
 edge_rows.append(np.sort(T[:,[a,b]],axis=1));weight_rows.append(.5*np.einsum('ij,ij->i',tp[:,a]-tp[:,o],tp[:,b]-tp[:,o])/twice)
E,inv=np.unique(np.vstack(edge_rows),axis=0,return_inverse=True);W=np.zeros(len(E));np.add.at(W,inv,np.concatenate(weight_rows));assert np.array_equal(E,w['cotangentEdges']) and np.allclose(W,w['cotangentWeights'],rtol=1e-12,atol=1e-12)
local=T[np.isin(T,free).any(axis=1)];le=np.unique(np.sort(np.vstack([local[:,[0,1]],local[:,[1,2]],local[:,[2,0]]]),axis=1),axis=0);h=float(np.median(np.linalg.norm(P[le[:,0]]-P[le[:,1]],axis=1)));assert abs(h-owner['sourceMedianLocalEdgeM'])<1e-15
# Kx as edge incidence products. Verify gradient projection without another solve.
def K(x):
 r=np.zeros_like(x);v=W[:,None]*(x[E[:,0]]-x[E[:,1]]);np.add.at(r,E[:,0],v);np.add.at(r,E[:,1],-v);return r
X=P.copy();X[free]+=D;gradient=mass[:,None]*(X-Q)+h**4*K(K(X)/mass[:,None]);directions=w['variableDirection'];owners=w['variableOwner'];projected=np.einsum('ij,ij->i',directions,gradient[free[owners]])
Dgradient=mass[:,None]*(X-P)+h**4*K(K(X-P)/mass[:,None]);rhs=mass[:,None]*(Q-P)-h**4*K(K(P)/mass[:,None]);projected_rhs=np.einsum('ij,ij->i',directions,rhs[free[owners]]);res=float(np.linalg.norm(projected)/np.linalg.norm(projected_rhs));assert res<1e-8
# Independently construct each first-difference normal constraint and null space.
exterior=is_fixed[T].all(axis=1);normals=np.zeros_like(P);np.add.at(normals,T[exterior].ravel(),np.repeat(norm[exterior],3,axis=0));ci={int(v):i for i,v in enumerate(free)};constraints=[[] for _ in free]
for a,b in [(0,1),(1,0)]:
 for v,z in E[(~is_fixed[E[:,a]])&is_fixed[E[:,b]]][:,[a,b]]:
  length=np.linalg.norm(normals[z])
  if length>0:constraints[ci[int(v)]].append(normals[z]/length)
rank_counts={0:0,1:0,2:0,3:0};max_tangent=0.
for i,ns in enumerate(constraints):
 rank=int(np.linalg.matrix_rank(np.array(ns),tol=1e-10)) if ns else 0;rank_counts[rank]+=1;basis=directions[owners==i];assert len(basis)==3-rank
 if len(basis):assert np.allclose(basis@basis.T,np.eye(len(basis)),atol=1e-12)
 if ns:
  vals=np.array(ns)@D[i];max_tangent=max(max_tangent,float(np.abs(vals).max()));assert not len(basis) or np.abs(np.array(ns)@basis.T).max()<1e-10
assert rank_counts=={int(k):v for k,v in owner['tangentConstraintRanks'].items()} and max_tangent<1e-10
# Request is exactly the alias-complete source one-ring; it has not been moved.
hp=n['protectedHeadXYZ'];ht=n['protectedHeadTriangles'];old=np.array(scope['headInitialBoundaryLedNativeVertexIDs']);incident=ht[np.isin(ht,old).any(axis=1)];expanded=np.flatnonzero(np.isin(alias,np.unique(alias[np.unique(incident)])));added=np.setdiff1d(expanded,old);added_tri=np.flatnonzero(np.isin(ht,added).any(axis=1));expanded_tri=np.flatnonzero(np.isin(ht,expanded).any(axis=1));new_tri=np.setdiff1d(expanded_tri,scope['headInitialBoundaryLedNativeTriangleIDs'])
for key,arr in [('addedHeadNativeVertexIDs',added),('addedHeadIncidentTriangleIDs',added_tri),('newlyIncidentHeadTriangleIDs',new_tri),('allExpandedHeadNativeVertexIDs',expanded),('allExpandedHeadIncidentTriangleIDs',expanded_tri)]:assert np.array_equal(arr,request[key]),key
assert np.array_equal(c['headRestXYZ'][added],f['headRestXYZ'][added]);assert not (hp[ht[added_tri],2]>1.60).any();donor=np.load(qa/'body59/neck-witnesses.npz')['headOriginalDonorVertexIDs'];assert np.array_equal(donor[added],request['addedHeadSourceDonorVertexIDs'])
report={'status':'FAILED_CANDIDATE_FIELDS_AND_FROZEN_OPERATOR_REPRODUCED_NO_SOLVE','recipeSHA256':sha(__file__),'all30InputPinsUnchanged':True,'physicalNodes':len(P),'freePhysicalNodes':len(free),'degreesOfFreedom':len(owners),'frozenMassAndCotangentCoefficientsReproduced':True,'medianLocalEdgeM':h,'independentProjectedStationarityResidual':res,'tangentConstraintRanks':rank_counts,'maximumTangentDisplacementResidualM':max_tangent,'maximumPositionDeltaM':float(np.linalg.norm(X-P,axis=1).max()),'fixedOneCornerAndPartialAliasPositionsExact':True,'allFullFourWeightsAndRigFieldsExact':True,'fieldsNativeFloat32ExpectedXYZ':True,'changes':changes,'ancestryCorrection':corrections,'collarRequest':{'addedIDs':len(added),'totalHeadIDs':len(expanded),'addedIncidentTriangles':len(added_tri),'newlyIncidentTriangles':len(new_tri),'totalIncidentTriangles':len(expanded_tri),'exactSourceAliasCompleteOneRing':True,'donorIDsExact':True,'unedited':True,'above1_60Touches':0,'necessaryMinimumCardinalityOrSufficient':False},'limits':['No new solve. Frozen operator coefficients, displacement stationarity and tangent null spaces checked at archived solution; objective Q provenance and source normals reported separately.','Topological collar equality is not necessity, minimum repair cardinality or sufficiency. Existing free/free crossings can falsify a fixed-anchor-only explanation.','Native/raw attribute/topology/intersections checked by separate read-only reader. No moving/art/engine/device/player admission.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'fields-operator.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['changes','ancestryCorrection']},indent=2))
