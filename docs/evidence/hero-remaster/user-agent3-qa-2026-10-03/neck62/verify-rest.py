"""Independent admitted-scope, stored ancestry and rest-registry audit only."""
import hashlib,json
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck61/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
f=np.load(asset/'neck-interface27/triangulated-neck-fields.npz');old=np.load(asset/'neck-interface27/authored-neck-fields.npz');base=np.load(qa/'body52/native-fields.npz');reg=np.load(ev/'neck-interface96/ordered-boundaries.npz');r=json.loads((out/'native-read.json').read_text());n=np.load(out/'native-read.npz');f={k:f[k] for k in f.files};old={k:old[k] for k in old.files};base={k:base[k] for k in base.files};reg={k:reg[k] for k in reg.files};n={k:n[k] for k in n.files};scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];auth=json.loads((ev/'neck-interface97/authoring.json').read_text());tri=json.loads((ev/'neck-interface98/triangulation.json').read_text())
assert sha(out/'native-read.npz')==r['nativeReadNPZ_SHA256']
b,c,failed=[r['snapshots'][x] for x in ['baseline','candidate','failed']]
assert all(c['objects'][name]==state for name,state in b['objects'].items());assert all(c['objects'][name]==state for name,state in failed['objects'].items());assert b['images']==c['images']==failed['images'];assert b['materials']==c['materials']==failed['materials'];assert b['bones']==c['bones']==f['boneNames'].tolist();assert len(b['bones'])==51
assert np.array_equal(f['rigRest'],base['rigRest']) and np.array_equal(f['rigWorld'],base['rigWorld'])
unchanged_old_arrays=[k for k in old.keys() if 'Triangles' not in k and 'LocalTriangle' not in k and 'TriangleSource' not in k and 'CornerAttribute' not in k]
for k in unchanged_old_arrays:assert np.array_equal(f[k],old[k]),k
rows=[];aux=[];ancestry=[];normal_deltas=[]
def polygon(key,i):
 start=int(n[key+'_polygonStarts'][i]);count=int(n[key+'_polygonCounts'][i]);return n[key+'_loopVertices'][start:start+count]
def attrs(key):
 label,part,field=key.split('_');return r['snapshots'][label]['domains'][part+'_'+field]['attributes']
def array_attr(key,name,field):return n[attrs(key)[name]['fields'][field]]
for part in ['body','head']:
 ap=next(x for x in auth['parts'] if x['part']==part);tr=next(x for x in tri['parts'] if x['part']==part);key='baseline_'+part+'_source';xyz=n[key+'_positions'];count=len(xyz);allowed=np.array(scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs']);allowed_tri=set(scope['bodyExistingRenderedTriangleIDs' if part=='body' else 'headInitialBoundaryLedNativeTriangleIDs']);outside=np.setdiff1d(np.arange(count),allowed);source_t=n[key+'_triangleVertices'];source_poly=n[key+'_trianglePolygons'];split=set(ap['splitOriginalPolygonIDs']);original_faces=len(n[key+'_polygonCounts']);candidate_map=f[part+'CandidatePolygonToCheckpointPolygon'];corner_map=f[part+'CandidateCornerToCheckpointCorner'];point=f[part+'AttributeEdgeSources'];refs=f[part+'CornerAttributeEdgeSources'];candidate_xyz=f[part+'RestXYZ'];polygon_copies=defaultdict(list)
 for ci,si in enumerate(candidate_map):polygon_copies[int(si)].append(ci)
 assert np.array_equal(xyz,base['renderedBodyXYZ' if part=='body' else 'protectedHeadXYZ'].astype(np.float32))
 assert np.array_equal(source_t,base['renderedBodyTriangles' if part=='body' else 'protectedHeadTriangles'])
 changed_xyz=np.flatnonzero(np.any(candidate_xyz[:count]!=xyz,axis=1));assert set(changed_xyz)<=set(allowed)
 for face in split:assert set(np.flatnonzero(source_poly==face))<=allowed_tri
 assert np.array_equal(refs,old[part+'CornerAttributeEdgeSources'][corner_map]);assert np.array_equal(point,old[part+'AttributeEdgeSources'])
 for label in ['full','four']:
  ck='candidate_'+part+'_'+label;fk='failed_'+part+'_'+label
  assert c['domains'][part+'_'+label]['world']==b['domains'][part+'_source']['world']
  srcname='Canonical body with hidden head interface' if part=='body' else 'Protected textured head above hidden neck interface'
  dstname='Bounded neck27 triangulated '+part+' '+label+', unaccepted'
  for field in ['world','basis','local','parentInverse','parent','parentType','parentBone','modifiers','constraints']:assert c['objects'][dstname][field]==b['objects'][srcname][field],(part,label,field)
  assert c['domains'][part+'_'+label]['materialNames']==b['domains'][part+'_source']['materialNames']
  assert np.array_equal(n[ck+'_positions'],candidate_xyz);assert np.array_equal(n[ck+'_weights'],f[part+label.title()+'Weights']);assert np.array_equal(n[ck+'_triangleVertices'],f[part+'Triangles'])
  triangle_sources=candidate_map[n[ck+'_trianglePolygons']];triangle_sources=np.where(triangle_sources<original_faces,triangle_sources,-1);assert np.array_equal(triangle_sources,f[part+'TriangleSourcePolygonIDs'])
  assert np.array_equal(n[ck+'_loopVertices'],n[fk+'_loopVertices'][corner_map]);assert np.array_equal(n[ck+'_smooth'],n[fk+'_smooth'][candidate_map]);assert np.array_equal(n[ck+'_materialIndices'],n[fk+'_materialIndices'][candidate_map])
  baseline_w=(base['originalFullWeights'][base['renderedBodySourceIDs'].astype(int)] if part=='body' and label=='full' else base['renderedBodyWeights'] if part=='body' else base['protectedHeadWeights']).astype(np.float32)
  changed_w=np.flatnonzero(np.any(n[ck+'_weights'][:count]!=baseline_w,axis=1));assert set(changed_w)<=set(allowed)
  assert np.array_equal(candidate_xyz[outside],xyz[outside]);assert np.array_equal(n[ck+'_weights'][outside],baseline_w[outside])
  for i in range(original_faces):
   copies=polygon_copies[i]
   if i not in split:assert len(copies)==1 and np.array_equal(polygon(ck,int(copies[0])),polygon(key,i))
  old_corners=(refs[:,0]>=0)&(refs[:,0]==refs[:,1]);protected=np.zeros(len(refs),dtype=bool);protected[old_corners]=np.isin(n[key+'_loopVertices'][refs[old_corners,0].astype(int)],outside)
  attribute_rows=[]
  for name,a in attrs(key).items():
   if name in ['position','.corner_vert','.corner_edge','.edge_verts']:continue
   ac=attrs(ck)[name];assert (a['kind'],a['domain'])==(ac['kind'],ac['domain']);domain=a['domain'];fields=[]
   for prop in a['fields']:
    original=array_attr(key,name,prop);actual=array_attr(ck,name,prop)
    if domain=='POINT':assert np.array_equal(actual[outside],original[outside])
    elif domain=='CORNER':assert np.array_equal(actual[protected],original[refs[protected,0].astype(int)])
    elif domain=='FACE':
     valid=candidate_map<original_faces;assert np.array_equal(actual[valid],original[candidate_map[valid]])
    elif domain=='EDGE':
     original_edges={tuple(sorted(v)):i for i,v in enumerate(n[key+'_edges'])};copies=[(i,original_edges[tuple(sorted(v))]) for i,v in enumerate(n[ck+'_edges']) if tuple(sorted(v)) in original_edges];ii,jj=np.array(copies).T;assert np.array_equal(actual[ii],original[jj])
    if domain in ['POINT','CORNER']:
     provenance=point if domain=='POINT' else refs
     aa=provenance[:,0].astype(int);bb=provenance[:,1].astype(int);ff=provenance[:,2];valid=aa>=0
     expected=np.zeros_like(actual)
     if np.issubdtype(actual.dtype,np.integer):expected[~valid]=-1
     if np.issubdtype(actual.dtype,np.floating):
      for idx in np.flatnonzero(valid):expected[idx]=(1-float(ff[idx]))*original[aa[idx]]+float(ff[idx])*original[bb[idx]]
     else:expected[valid]=original[aa[valid]]
     assert np.array_equal(actual,expected),(part,label,name,prop,'original_attribute_provenance')
    fields.append(prop)
   attribute_rows.append({'name':name,'kind':a['kind'],'domain':domain,'fields':fields})
  decoded=np.linalg.norm(n[ck+'_cornerNormals'][protected].astype(float)-n[key+'_cornerNormals'][refs[protected,0].astype(int)].astype(float),axis=1);normal_deltas.append({'part':part,'field':label,'protectedStoredCornerNormalsMaxVectorDifference':float(decoded.max(initial=0)),'nonidenticalDecodedNormals':int(np.count_nonzero(decoded))})
  w=n[ck+'_weights'];assert np.isfinite(w).all() and np.min(w)>=0;slots=(w>0).sum(1);assert label!='four' or slots.max()<=4
  rows.append({'part':part,'field':label,'outsideVertices':len(outside),'changedOriginalPositionIDs':changed_xyz.tolist(),'changedOriginalSemanticWeightIDs':changed_w.tolist(),'candidateVertices':len(w),'newVertices':len(w)-count,'protectedSourceCornerCopies':int(protected.sum()),'nativeFieldsExact':True,'outsidePositionsSemanticWeightsAndRawAttributesExact':True,'maximumSemanticWeightSlots':int(slots.max()),'maximumWeightSumDifferenceFrom1':float(np.abs(w.sum(1,dtype=np.float64)-1).max()),'weightNormalizationScope':'All seam aliases use identical chest0.35/neck0.65 Float32 rows. Full body retains original raw outside control rows, including source rounding; no global renormalization performed.','attributes':attribute_rows})
  # Check topology-stage copies separately from original interpolated ancestry.
  for name,a in attrs(fk).items():
   if name in ['position','.corner_vert','.corner_edge','.edge_verts']:continue
   for prop in a['fields']:
    values=array_attr(fk,name,prop);actual=array_attr(ck,name,prop)
    if a['domain']=='POINT':assert np.array_equal(actual,values)
    elif a['domain']=='CORNER':assert np.array_equal(actual,values[corner_map])
    elif a['domain']=='FACE':assert np.array_equal(actual,values[candidate_map])
 # Validate declared corner references are either exact old loops or splits along one old polygon edge.
 for aa,bb,frac in refs:
  if aa<0:assert bb<0;continue
  aa,bb=int(aa),int(bb);assert 0<=aa<len(n[key+'_loopVertices']) and 0<=bb<len(n[key+'_loopVertices']) and 0<=frac<=1
  if aa!=bb:
   srcface=np.searchsorted(n[key+'_polygonStarts'],aa,side='right')-1;st=n[key+'_polygonStarts'][srcface];sz=n[key+'_polygonCounts'][srcface];assert bb==st+(aa-st+1)%sz
   assert int(srcface) in split
 new=np.arange(count,len(candidate_xyz));edge_new=new[point[new,0]>=0];unparented=new[point[new,0]<0];assert len(unparented)==(1 if part=='head' else 0)
 for v in edge_new:
  aa,bb,frac=point[v];assert int(aa) in allowed and int(bb) in allowed and 0<frac<1
  sid=int(f[part+'SeamPhysicalIDs'][v]);assert sid>=0 and np.array_equal(candidate_xyz[v],f['sharedRestFloat32XYZ'][sid])
 # Confirm exact declared replacement fans and retained seam-only originals.
 for replacement in tr['replacedCheckpointPolygons']:
  i=replacement['checkpointPolygon'];assert i in split;verts=polygon('failed_'+part+'_four',i);pivot=int(np.flatnonzero(verts==replacement['existingFanPivotVertex'])[0]);verts=np.roll(verts,-pivot);expected=np.array([[verts[0],verts[j],verts[j+1]] for j in range(1,len(verts)-1)])
  actual=np.array([polygon('candidate_'+part+'_four',j) for j in replacement['newPolygonIDs']]);assert np.array_equal(actual,expected)
 for i in tr['retainedSeamOnlyCheckpointPolygons']:
  copies=polygon_copies[i];assert len(copies)==1 and np.array_equal(polygon('candidate_'+part+'_four',int(copies[0])),polygon('failed_'+part+'_four',i))
 ancestry.append({'part':part,'declaredSplitOriginalPolygons':len(split),'triangulatedCheckpointPolygons':len(tr['replacedCheckpointPolygons']),'retainedSeamOnlyCheckpointPolygons':tr['retainedSeamOnlyCheckpointPolygons'],'newEdgeSplitVertices':len(edge_new),'newUnparentedVertices':unparented.tolist(),'allNewEdgeEndpointsInsideAdmittedVertexScope':True,'originalSourceLoopsAndCornerInterpolationReferencesValid':True,'candidatePolygonAndCornerCopyMapsExact':True,'triangleOriginalPolygonAncestryAndAllPointCornerAttributeDerivationsExact':True})
 raw=b['domains'][part+'_source'];outside_set=set(map(int,outside));assignments=[x for x in raw['nonBoneAssignments'] if x[0] in outside_set];positive=[x for x in assignments if x[2]>0]
 aux.append({'part':part,'sourceNonBoneGroupCount':len(raw['nonBoneVertexGroups']),'candidateNonBoneGroupCount':len(c['domains'][part+'_four']['nonBoneVertexGroups']),'outsideNonBoneAssignmentsOmitted':len(assignments),'outsidePositiveNonBoneAssignmentsOmitted':len(positive),'outsideDistinctVerticesWithPositiveOmittedAssignments':len({x[0] for x in positive}),'positiveOmittedGroupCounts':dict(Counter(x[1] for x in positive)),'first20PositiveOutsideWitnesses':positive[:20],'sourceGroups':raw['nonBoneVertexGroups'],'meaning':'These raw non-bone vertex groups are not the51skin slots. Baseline objects remain exact, but candidate outside vertex-group metadata is not exact. No visual or motion consequence inferred; parent decides preservation requirement, Agent1 owns any correction.'})
 # The outside above-height triangle boundary is explicit; cheek is immutable original object.
 if part=='head':
  high=np.flatnonzero(np.any(xyz[source_t,2]>1.60,axis=1));assert not (allowed_tri & set(high));assert not set(allowed)&set(source_t[high].ravel())
# Independently reproduce ordering/knots and common seam positions from original fields.
body_order=f['bodyOriginalFrontOrderedIDs'];head_order=f['headOriginalFrontOrderedIDs'];assert len(body_order)==56 and len(head_order)==183
for order,key,kn in [(body_order,'baseline_body_source','bodyOriginalKnots'),(head_order,'baseline_head_source','headOriginalKnots')]:
 p=n[key+'_positions'].astype(float);assert order[0]==order[np.argmax(p[order,0])];length=np.linalg.norm((np.roll(p[order],-1,axis=0)-p[order])[:,:2],axis=1);u=np.r_[0.,np.cumsum(length[:-1])]/length.sum();assert np.array_equal(u,f[kn])
common=np.unique(np.r_[f['bodyOriginalKnots'],f['headOriginalKnots']]);assert np.array_equal(common,f['commonU']);hp=n['baseline_head_source_positions'].astype(float);hu=f['headOriginalKnots'];reconstructed=[]
for u in common:
 j=max(int(np.searchsorted(hu,u,side='right')-1),0);end=hu[j+1] if j+1<len(hu) else 1.;a=(u-hu[j])/(end-hu[j]);reconstructed.append((1-a)*hp[head_order[j]]+a*hp[head_order[(j+1)%len(hu)]])
assert np.array_equal(np.array(reconstructed,dtype=np.float32),f['sharedRestFloat32XYZ']);assert len(common)==238
# The raw source UV alias equivalence is checked independently, not assumed from registry.
_,alias=np.unique(hp,axis=0,return_inverse=True);assert np.array_equal(alias,reg['headPositionAlias'])
physical={};points={};physical_tri=[];offset=238;local_vertex_set=set();area_rows=[]
for part in ['body','head']:
 p=f[part+'RestXYZ'];ids=np.arange(len(p),dtype=np.int64)+offset
 if part=='head':ids[:len(alias)]=alias+offset
 sid=f[part+'SeamPhysicalIDs'];mask=sid>=0;ids[mask]=sid[mask]
 assert set(sid[mask])==set(range(238)) and np.array_equal(p[mask],f['sharedRestFloat32XYZ'][sid[mask]])
 for label in ['Full','Four']:assert np.array_equal(f[part+label+'Weights'][mask],np.tile(f['sharedSemanticWeights'],(mask.sum(),1)))
 physical[part]=ids;physical_tri.append(ids[f[part+'Triangles']]);offset+=len(p)
 for i,v in enumerate(ids):
  if int(v) in points:assert np.array_equal(points[int(v)],p[i])
  else:points[int(v)]=p[i]
 allowed=scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs'];orig=len(n['baseline_'+part+'_source_positions']);t=f[part+'Triangles'];local=np.flatnonzero(np.any(np.isin(t,allowed)|(t>=orig),axis=1));assert np.array_equal(local,f[part+'LocalTriangleIDs']);q=p[t[local]].astype(float);area=.5*np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);assert np.min(area)>1e-14
 local_vertex_set.update(map(int,ids[t[local]].ravel()));area_rows.append({'part':part,'localOneCornerTriangles':len(local),'minimumRestAreaM2':float(area.min()),'zeroOrBelow1e_14M2':int((area<=1e-14).sum())})
t=np.concatenate(physical_tri);edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);unique,inverse,counts=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True);directions=np.where(edges[:,0]<edges[:,1],1,-1);signed=np.bincount(inverse,weights=directions);nonman=np.flatnonzero(counts>2);winding=np.flatnonzero((counts==2)&(signed!=0));collapsed=np.flatnonzero((t[:,0]==t[:,1])|(t[:,1]==t[:,2])|(t[:,2]==t[:,0]));assert not len(nonman) and not len(winding) and not len(collapsed)
seam=(unique<238).all(1)&((np.diff(unique,axis=1).ravel()==1)|((unique[:,0]==0)&(unique[:,1]==237)));assert seam.sum()==238 and np.all(counts[seam]==2) and np.all(signed[seam]==0)
inner_vertices=set(physical['head'][f['headInnerClosurePhysicalIDs']>=0]);inner=np.array([a in inner_vertices and b in inner_vertices for a,b in unique]);assert inner.sum()==383 and np.all(counts[inner]==2) and np.all(signed[inner]==0);assert np.count_nonzero(counts==1)==151
# Link graphs qualify local physical vertex fans beyond edge incidence.
links=defaultdict(list)
for a,bv,cv in t:
 for v,edge in [(int(a),(int(bv),int(cv))),(int(bv),(int(cv),int(a))),(int(cv),(int(a),int(bv)))]:
  if v in local_vertex_set:links[v].append(edge)
fan_fail=[]
for v,es in links.items():
 adj=defaultdict(list)
 for a,bv in es:adj[a].append(bv);adj[bv].append(a)
 seen=set();todo=[next(iter(adj))]
 while todo:
  j=todo.pop()
  if j not in seen:seen.add(j);todo.extend(adj[j])
 degrees=[len(x) for x in adj.values()];valid=len(seen)==len(adj) and (all(d==2 for d in degrees) or (degrees.count(1)==2 and all(d in [1,2] for d in degrees)))
 if not valid:fan_fail.append({'physicalVertex':v,'componentsConnected':len(seen)==len(adj),'degreeHistogram':dict(Counter(degrees))})
report={'status':'UNACCEPTED_REST_TOPOLOGY_VERIFIED_OUTSIDE_AUXILIARY_GROUP_PRESERVATION_GAP','candidateCheckpoint':'c65755e6ffc53d1d529ebfe5e89782b28133970c','validation':{'original34ObjectSnapshotsExact':True,'originalAndFailed38ObjectSnapshotsExact':True,'original51StoredRestBindPoseAndConfigurationExact':True,'original17PackedImagesExact':True,'original18MaterialGraphsExact':True,'candidateFullFourStoredFieldsExact':True,'sameFieldFromFailedNeck97':True,'all15InputPinsUnchanged':True},'scopeAndAttributes':rows,'protectedDecodedNormals':normal_deltas,'ancestry':ancestry,'nonBoneOutsidePreservationGap':aux,'orderedCorrespondence':{'bodyKnots':56,'outerHeadKnots':183,'commonPhysicalKnots':238,'originalMaxXAnchoredXYArcLengthAndUnionExact':True,'derivedBodyRestAndHeadPolylineReferencesHonest':True,'existingBodyPositionsChanged':len(rows[0]['changedOriginalPositionIDs']),'headPositionsChanged':len(rows[2]['changedOriginalPositionIDs']),'newInnerCapSourceIdentity':'None; one new centroid and190new faces, reverse-oriented to original inward boundary.'},'restTopology':{'outerSeam238EdgesTwoOpposedIncidences':True,'outerAliasFloat32PositionsAndBothWeightFieldsIdentical':True,'innerClosure383EdgesTwoOpposedIncidences':True,'originalMouthDiagnosticBoundaryEdges':151,'nonmanifoldEdges':len(nonman),'interiorWindingEdges':len(winding),'collapsedPhysicalTriangles':len(collapsed),'localPhysicalVerticesWithLinkGraphChecked':len(links),'localVertexFanFailures':fan_fail,'areas':area_rows,'qualification':'Actual rest triangle graph under declared outer seam registry and independently recomputed original UV position quotient. This is not global physical head watertightness/containment, geometric T-junction search, self-collision or dynamic seam precision.'},'evidence':{'nativeReadJSON_SHA256':sha(out/'native-read.json'),'nativeReadNPZ_SHA256':sha(out/'native-read.npz'),'recipeSHA256':sha(__file__)},'limits':['Read-only stored rest scope/ancestry/topology only. Agent1 owns all529native/703actual47 attachment/loss/contact/collapse measurements and one matched played proof; no duplicate capture or competing authoring.','Candidate drops non-bone body groups outside the admitted patch; skin and generic mesh attribute preservation must not be described as preservation of every outside vertex field. Parent decides admission/correction, no source change by Agent3.','Original490garment/head contact pairs not waived; source26 garment remains failed. Above1.60m touching head triangles and cheek remain protected. No global body/head replacement or promotion.','Configurable snapshot excludes generic RNA collections not enumerated, animation F-curves/NLA and external linked-file content. Local link/topology counts do not pass visual anatomy.','Parent owns ask275/plan index and played-art acceptance. All M0-M5, engine/device/player and garment-field/hem decisions remain open. No upload, delivery, outbound acknowledgment or publication.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'assessment.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'validation':report['validation'],'restTopology':report['restTopology'],'nonBoneOutsidePreservationGap':[{k:x[k] for k in ['part','sourceNonBoneGroupCount','outsideNonBoneAssignmentsOmitted','outsidePositiveNonBoneAssignmentsOmitted','outsideDistinctVerticesWithPositiveOmittedAssignments']} for x in aux],'protectedDecodedNormals':normal_deltas},indent=2))
