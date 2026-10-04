"""Recompute frozen source references and scope aliases; no construction."""
import hashlib,json
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck67/preparation.json').read_text());ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
n=dict(np.load(qa/'body52/native-fields.npz'));f=dict(np.load(asset/'neck-interface27/triangulated-neck-fields.npz'));reg=dict(np.load(ev/'neck-interface96/ordered-boundaries.npz'));d=json.loads((ev/'neck-interface101/diagnosis.json').read_text());w=json.loads((ev/'neck-interface101/source-section-witnesses.json').read_text());scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];H=n['protectedHeadXYZ'].astype(float);HT=n['protectedHeadTriangles'];B=n['renderedBodyXYZ'].astype(float);P=n['originalFullXYZ'].astype(float);T=n['originalFullTriangles'];Q=P[T];bone_names=n['boneNames'].tolist();neck=n['rigRest'][bone_names.index('neck'),:3,3].astype(float);head=n['rigRest'][bone_names.index('head'),:3,3].astype(float)
head_allowed=np.array(scope['headInitialBoundaryLedNativeVertexIDs']);body_allowed=np.array(scope['bodyExistingRenderedNativeVertices']);_,alias=np.unique(H,axis=0,return_inverse=True);assert np.array_equal(alias,reg['headPositionAlias']);head_fixed=np.setdiff1d(np.unique(HT[scope['headInitialBoundaryLedNativeTriangleIDs']]),head_allowed);body_fixed=np.setdiff1d(np.unique(n['renderedBodyTriangles'][scope['bodyExistingRenderedTriangleIDs']]),body_allowed)
allowed_set=set(map(int,head_allowed));partial=[];partial_members=[]
for a in np.unique(alias[head_allowed]):
 ids=np.flatnonzero(alias==a);inside=np.intersect1d(ids,head_allowed);outside=np.setdiff1d(ids,head_allowed)
 if len(outside):partial.append(int(a));partial_members.append({'aliasClass':int(a),'admittedIDsPinned':inside.tolist(),'outsideIDsProtected':outside.tolist(),'positionNativeM':H[ids[0]].tolist()})
inside_pinned=head_allowed[np.isin(alias[head_allowed],partial)];outside_alias=np.flatnonzero(np.isin(alias,partial)&~np.isin(np.arange(len(H)),head_allowed));free=np.setdiff1d(head_allowed,inside_pinned)
for k,v in [('bodyEditableVertices',body_allowed),('headEditableVertices',head_allowed),('bodyFixedOneCornerVertices',body_fixed),('headFixedOneCornerVertices',head_fixed),('partialHeadUVPositionAliasClassesPinned',partial),('admittedHeadAliasMembersThatMustStayPinned',inside_pinned),('protectedOutsideAliasMembers',outside_alias)]:assert np.array_equal(v,d['exactProtectionConstraints'][k]),k
high=np.any(H[HT,2]>1.60,axis=1);assert not np.any(np.isin(HT[high],head_allowed));assert 29738 in head_fixed and 29738 not in allowed_set
protected_head=np.setdiff1d(np.arange(len(H)),free);protected_body=np.setdiff1d(np.arange(len(B)),body_allowed)
assert np.array_equal(f['headFourWeights'][protected_head],n['protectedHeadWeights'][protected_head].astype(np.float32))
assert np.array_equal(f['bodyFourWeights'][protected_body],n['renderedBodyWeights'][protected_body].astype(np.float32))
assert f['boneNames'].tolist()==bone_names
# Independent vectorized plane intersections carry triangle IDs and barycentric coordinates.
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def sections(z):
 ids=np.flatnonzero((Q[:,:,2].min(1)<z)&(Q[:,:,2].max(1)>=z));faces=Q[ids];positions=[];bary=[]
 for face in faces:
  hits=[];bs=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if (face[i,2]<z)!=(face[j,2]<z):
    u=(z-face[i,2])/(face[j,2]-face[i,2]);v=np.zeros(3);v[i]=1-u;v[j]=u;hits.append(v@face);bs.append(v)
  assert len(hits)==2;positions.append(hits);bary.append(bs)
 return ids,np.array(positions),np.array(bary)
rows=[];maximum=0.;hit_counts=[]
for family,expected in w.items():
 expected_ids=reg['outerHeadOrderedNativeRepresentatives'] if family=='outer' else head_fixed;assert [x['nativeVertex'] for x in expected]==list(expected_ids)
 for item in expected:
  v=item['nativeVertex'];p=H[v];z=p[2];axis=(neck+(head-neck)*((z-neck[2])/(head[2]-neck[2])))[:2];direction=p[:2]-axis;radius=np.linalg.norm(direction);direction/=radius;ids,segments,barys=sections(z);a=segments[:,0,:2];edge=segments[:,1,:2]-a;den=cross2(direction,edge);valid=np.abs(den)>1e-14;distance=np.zeros(len(ids));fraction=np.zeros(len(ids));distance[valid]=cross2(a[valid]-axis,edge[valid])/den[valid];fraction[valid]=cross2(a[valid]-axis,direction)/den[valid];mask=valid&(distance>0)&(fraction>=-1e-9)&(fraction<=1+1e-9);hits=np.flatnonzero(mask);unique=np.unique(np.round(distance[hits],10));assert len(unique)==1,(v,unique);pick=int(hits[np.argmin(distance[hits])]);u=fraction[pick];b=(1-u)*barys[pick,0]+u*barys[pick,1];reference=b@P[T[ids[pick]]];delta=p-reference;radial=radius-distance[pick];residual=float(np.linalg.norm(reference-np.array(item['canonicalSectionRayPositionM'])));maximum=max(maximum,residual);hit_counts.append(len(hits));assert residual<=1e-9 and abs(radial-item['sourceMinusCanonicalRadiusM'])<=1e-9
  rows.append({'family':family,'nativeHeadVertex':v,'canonicalSourceTriangle':int(ids[pick]),'canonicalTriangleVertexIDs':T[ids[pick]].tolist(),'barycentric':b.tolist(),'canonicalReferenceNativeM':reference.tolist(),'sourceNativeM':p.tolist(),'axisNativeXYM':axis.tolist(),'signedRadialDifferenceM':float(radial),'sourceMinusCanonicalXYZM':delta.tolist(),'positiveSegmentHitsBeforeCoincidentDedup':len(hits),'residualToOwnerRoundedReferenceM':residual})
section_rows=[]
for item in d['canonicalHorizontalSections']:
 ids,segments,bs=sections(item['nativeZ']);xyz=segments.reshape(-1,3);width=float(np.ptp(xyz[:,1]));depth=float(np.ptp(xyz[:,0]));assert abs(width-item['widthYM'])<1e-12 and abs(depth-item['depthXM'])<1e-12;section_rows.append({'nativeZ':item['nativeZ'],'widthYM':width,'depthXM':depth,'sourceIntersectedTriangles':ids.tolist()})
changed=np.flatnonzero(np.any(f['bodyRestXYZ'][:len(B)]!=B,axis=1));assert set(changed)==set(reg['bodyCutOrderedNativeIDs']);assert np.array_equal(f['headRestXYZ'][:len(H)],H);delta=np.linalg.norm(f['bodyRestXYZ'][changed].astype(float)-B[changed],axis=1);assert abs(delta.max()-d['frozen27BodyConformation']['maxExistingBodyPositionDeltaM'])<1e-12
fixed_witness=next(x for x in rows if x['family']=='fixedHeadOneCorner' and x['nativeHeadVertex']==29738)
report={'status':'UNACCEPTED_INDEPENDENT_SOURCE_REFERENCE_AND_SCOPE_CHECK','recipeSHA256':sha(__file__),'all21InputPinsUnchanged':True,'verified':{'body56ChangesExactlyOriginalCut':True,'maximumChangedBodyPositionM':float(delta.max()),'headOriginal43707PositionsExact':True,'sourceCanonicalAndDonorAncestryDistinct':True,'planeRayWitnesses':len(rows),'maximumReferenceResidualToOwnerM':maximum,'maximumPositiveSegmentHitCount':max(hit_counts),'fixedHeadOneCornerVertices':len(head_fixed),'fixedBodyOneCornerVertices':len(body_fixed),'partialAliasClasses':len(partial),'admittedAliasMembersPinned':len(inside_pinned),'protectedOutsideAliasMembers':len(outside_alias),'fullyAdmittedFreeRawHeadVertices':len(free),'fullyAdmittedHeadPositionClasses':len(np.unique(alias[free])),'noAbove1_60TouchingTrianglesEdited':True,'protectedHeadIncludingPartialAliasWeightsExactOriginal':True,'protectedBodyFourWeightsExactOriginal':True,'fixed29738WeightsByBone':{bone_names[j]:float(f['headFourWeights'][29738,j]) for j in np.flatnonzero(f['headFourWeights'][29738])}},'fixed29738Witness':fixed_witness,'partialAliasClasses':partial_members,'fixedHeadIDs':head_fixed.tolist(),'fixedBodyIDs':body_fixed.tolist(),'pinnedAdmittedHeadIDs':inside_pinned.tolist(),'actualEditableHeadIDsAfterAliasProtection':free.tolist(),'canonicalSections':section_rows,'planeRayWitnesses':rows,'limits':['Source anatomy guidance only, not accepted/universal anatomical truth. Fixed source mismatch does not prove moving pixel cause or complete local-transition infeasibility.','Reference points are exact intersections on original source triangles with declared barycentric ancestry; not authored geometry or nearest-point sewing. Owner rounds ray radii to1e-10m; residual reflects that rounding.','Only exact frozen geometry/proposal lists used; no solve, new pose, capture, native/export/source edit, scope expansion or competing proposal. Parent alone admits/judges.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'source-assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'verified':report['verified'],'fixed29738':fixed_witness},indent=2))
