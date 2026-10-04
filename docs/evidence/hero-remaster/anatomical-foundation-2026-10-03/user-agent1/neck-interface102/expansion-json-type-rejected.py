"""Confirm failed rest surface witnesses; propose one exact collar, never edit."""
import hashlib,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[6];owned=Path(__file__).resolve().parent
ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';out=ev/'neck-interface102';qa=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report_path=out/'rest-candidate.json';report=json.loads(report_path.read_text());native=root/report['native'];raw_field=root/report['fields'];f=dict(np.load(raw_field));n=np.load(qa/'body52/native-fields.npz');r=np.load(ev/'neck-interface96/ordered-boundaries.npz');scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin']
assert sha(native)==report['nativeSHA256'] and sha(raw_field)==report['fieldsSHA256']
auth=json.loads((ev/'neck-interface97/authoring.json').read_text())
# Initial freeze reader mislabeled inward-cap checkpoint polygons as source IDs.
# Preserve that original receipt/field, supply corrected provenance only.
for row in auth['parts']:
 part=row['part'];ids=f[part+'TriangleSourcePolygonIDs'];f[part+'TriangleCheckpointPolygonIDs']=ids.copy();caps=row['newInwardCapPolygonIDs'];f[part+'TriangleSourcePolygonIDs']=np.where(np.isin(ids,caps),-1,ids).astype(np.int32)
corrected=native.parent/'geometry-only-fields-ancestry-corrected.npz';assert not corrected.exists();np.savez_compressed(corrected,**f)

def proper_crossings(A,B):
 rows=[]
 for source,target in [(A,B),(B,A)]:
  v0,v1,v2=target;nrm=np.cross(v1-v0,v2-v0);length=np.linalg.norm(nrm)
  if length<1e-20:continue
  nrm/=length;e1=v1-v0;e2=v2-v0;aa=e1@e1;ab=e1@e2;bb=e2@e2;det=aa*bb-ab*ab
  for i,j in [(0,1),(1,2),(2,0)]:
   a,b=source[i],source[j];sa=(a-v0)@nrm;sb=(b-v0)@nrm
   if not (sa*sb<0 and abs(sa)>1e-10 and abs(sb)>1e-10):continue
   t=sa/(sa-sb);p=a+t*(b-a);d=p-v0;x=((d@e1)*bb-(d@e2)*ab)/det;y=((d@e2)*aa-(d@e1)*ab)/det
   if x>=-1e-9 and y>=-1e-9 and x+y<=1+1e-9:rows.append({'positionNativeM':p.tolist(),'segmentFraction':float(t),'targetBarycentric':[float(1-x-y),float(x),float(y)]})
 return rows
confirmed={}
for kind,parts in [('headSelf',('head','head')),('bodyHead',('body','head')),('bodySelf',('body','body'))]:
 a,b=parts;pa=f[a+'RestXYZ'].astype(float);pb=f[b+'RestXYZ'].astype(float);ta=f[a+'Triangles'];tb=f[b+'Triangles'];rows=[]
 for i,j in report['restContacts'][kind]['trianglePairs']:
  points=proper_crossings(pa[ta[i]],pb[tb[j]])
  if points:rows.append({'triangleIDs':[i,j],'sourcePolygonIDs':[int(f[a+'TriangleSourcePolygonIDs'][i]),int(f[b+'TriangleSourcePolygonIDs'][j])],'sourceVertexIDs':[ta[i].tolist(),tb[j].tolist()],'properFiniteSegmentCrossings':points})
 confirmed[kind]={'rawBVHPairs':report['restContacts'][kind]['pairs'],'properFiniteCrossingPairs':len(rows),'witnesses':rows}
# Smallest complete ONE adjacency collar of the admitted head patch, with aliases.
# This is a request, not proof of the globally minimal/sufficient repair region.
hp=n['protectedHeadXYZ'];ht=n['protectedHeadTriangles'];alias=r['headPositionAlias'];old=set(scope['headInitialBoundaryLedNativeVertexIDs']);incident=ht[np.isin(ht,list(old)).any(axis=1)]
seed=set(np.unique(incident))-old;classes=set(alias[list(old|seed)]);expanded=set(np.flatnonzero(np.isin(alias,list(classes))));added=sorted(expanded-old)
triangles=np.flatnonzero(np.isin(ht,added).any(axis=1));protected=np.flatnonzero(hp[ht,2].max(axis=1)>1.60)
assert not set(triangles)&set(protected)
all_expanded_triangles=np.flatnonzero(np.isin(ht,sorted(expanded)).any(axis=1));newly_incident=np.setdiff1d(all_expanded_triangles,scope['headInitialBoundaryLedNativeTriangleIDs'])
minimum_collar={'status':'EXACT_ONE_RING_EXPANSION_REQUEST_ROOT_DECISION_REQUIRED_NOT_EDITED','addedHeadNativeVertexIDs':added,'addedHeadIncidentTriangleIDs':triangles.tolist(),'newlyIncidentHeadTriangleIDs':newly_incident.tolist(),'allExpandedHeadNativeVertexIDs':sorted(expanded),'allExpandedHeadIncidentTriangleIDs':all_expanded_triangles.tolist(),'addedHeadSourceDonorVertexIDs':np.load(qa/'body59/neck-witnesses.npz')['headOriginalDonorVertexIDs'][added].tolist(),'positionClassesCompleted':sorted(classes-set(alias[list(old)])),'addedVertices':len(added),'totalHeadEditableVerticesIfAdmitted':len(expanded),'addedIncidentTriangles':len(triangles),'newlyIncidentTriangles':len(newly_incident),'addedNativeBoundsM':[hp[added].min(axis=0).tolist(),hp[added].max(axis=0).tolist()],'protectedAbove1_60TriangleTouches':0,'bodyExpansion':None,'anatomicalJustification':'One complete source adjacency collar releases the current373one-corner head anchors and completes partial UV classes, giving the joint transition one more continuous source band instead of isolated vertex moves. Fixed29738 is50.237mm outside canonical same-height anatomy reference; current short band folds under the single fixed operator. Canonical reference is an objective only, not accepted universal anatomy.','minimalityAndLimits':'Smallest full one-ring topological collar that contains every present fixed one-corner head vertex and completes every resulting exact-position alias class. Not proven globally necessary, minimum-cardinality or sufficient for all1112self/307body-head failures. Contact constraints were not in the screened-biharmonic energy; failure alone does not prove a scope expansion will repair them. Root may reject the request. No move, solve, skin or capture is authorized by this document.'}
(out/'expansion-request.json').write_text(json.dumps(minimum_collar,indent=2)+'\n')
report2={'status':'FAILED_GEOMETRY_ONLY_PROPER_REST_CROSSINGS_RETAINED','recipeSHA256':sha(__file__),'initialRestReceiptSHA256':sha(report_path),'nativeSHA256':sha(native),'initialFieldsSHA256':sha(raw_field),'correctedFields':str(corrected.relative_to(root)),'correctedFieldsSHA256':sha(corrected),'provenanceCorrection':'Initial native freeze fields mislabeled inward-cap checkpoint polygons as original source. Original field/receipt retained; corrected fields label190new inward cap faces -1source and retain explicit checkpoint IDs. Geometry/triangles/weights/attributes unchanged.','confirmedContacts':confirmed,'expansionRequestSHA256':sha(out/'expansion-request.json'),'limits':['Proper crossings certify these finite surface witnesses only, not signed penetration volume or art acceptance.','No second geometry operator, source position/weight/native save/capture or automatic expansion. AllM0-M5 and original99failures remain open.']}
(out/'failure-analysis.json').write_text(json.dumps(report2,indent=2)+'\n');print('CONFIRMED',{k:v['properFiniteCrossingPairs'] for k,v in confirmed.items()});print('ONE_RING_REQUEST',len(added),len(expanded),len(triangles),len(newly_incident))
