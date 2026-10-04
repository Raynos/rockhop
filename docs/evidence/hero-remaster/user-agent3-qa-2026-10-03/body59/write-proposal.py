"""Record the bounded independent repair proposal; never author source assets."""
import hashlib,json
from pathlib import Path
out=Path(__file__).resolve().parent;qa=out.parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();r=json.loads((out/'assessment.json').read_text());p=json.loads((out/'pixel-ownership.json').read_text());m=r['proposedMargin'];rows=r['samples'];sample=lambda d,i:next(x for x in rows if x['domain']==d and x['sourceIndex']==i);h668=next(x for x in r['headLowerLoopRelativeAttachment'] if x['domain']=='actual47' and x['sourceIndex']==668);body_faces=set(m['bodyRenderedTrianglesIncidentToMargin']);contacts=set(r['garmentHeadCorrelation']['headTriangles']);hit_head=[x for x in p['rows'] if x['hit'] and x['hit']['part']=='protectedHead'];dark_head=[x for x in hit_head if x['hit']['stablePartWithinPoint2Pixel'] and x['hit'].get('withinLowHeadProxy1_60M') and max(x['RGB'])<100];dark_body=[x for x in p['rows'] if x['hit'] and x['hit']['part']=='renderedBody' and x['hit']['nativeTriangle'] in body_faces and x['hit']['stablePartWithinPoint2Pixel'] and max(x['RGB'])<100];joint_raw=[]
for loop in h668['headLowerLoopIntrinsicRelativeAttachment']:joint_raw.append({'headNativeVertex':loop['worstNativeVertex'],'weights':loop['worstWeightByJoint'],'displacementInNeckFrameM':loop['displacementInNeckRestFrameM']['maximum']})
proposal={'status':'PROPOSED_LOCAL_NECK_INTERFACE_TRIAL_PARENT_ADMISSION_REQUIRED','creationDate':'2026-10-04','owner':'Agent1 authors; Agent3 independent QA; root chooses exact scope and judges played appearance.','recommendation':'Retain the full canonical body and chosen face. Replace the independently cropped neck interface with one explicit local anatomical/material join on a NEW candidate derivative. Rest geometry/topology first, then local attachment on the same patch; no global rig/head transform or weight recovery sweep.','diagnosis':{'restGeometryMismatch':{'bodyCutLoopVertices':56,'bodyCutWidthM':r['bodyAncestry']['boundaryWidthM'],'headLowLoopVertices':[183,190],'headLowLoopWidthsM':[x['widthM'] for x in r['headBoundary']['lowerCutLoops']],'bodyEdgeToAnyHeadTriangleRestDistanceM':r['restPairCorrespondence']['restDistanceM'],'interpretation':'These are distances between independently cut surfaces, not seam weld error or signed penetration. Rest mismatch predates dynamic weight loss; there is no authored common boundary.'},'visibleSurfaceAttribution':{'existingPlayedPixelRays':72,'stableDarkLowHeadWitnesses':len(dark_head),'stableDarkBodyCutMarginWitnesses':len(dark_body),'darkHeadWitnessPixels':[{k:x[k] for k in ['domain','sourceIndex','view','playedPixelXY']} for x in dark_head],'darkBodyWitnessPixels':[{k:x[k] for k in ['domain','sourceIndex','view','playedPixelXY']} for x in dark_body],'interpretation':'Listed stable rays implicate BOTH donor lower-neck surface and canonical-body cut margin. This is not complete pixel segmentation or an alpha/shader visibility proof.'},'relativeAttachment':{'commonBodyHeadObjectWorldExact':True,'sameOwn51Bind':True,'donorVersusOwnBoneOriginDifferencesM':{k:v['originDifferenceM'] for k,v in r['donorVsOwnRestBoneFrames'].items()},'sourceHeadLowerLoopWeights':'Only chest/neck, at most2slots. Mean about52%chest/48%neck; source semantic weights copied exactly, while chest/neck/head rest pivots differ from donor. Lower rim lies below current own neck pivot, not above the original donor pivot.','native72BodyPairDriftM':sample('native',72)['attachmentDriftFromRigidNeckReferenceM']['maximum'],'actual47_668BodyPairDriftM':sample('actual47',668)['attachmentDriftFromRigidNeckReferenceM']['maximum'],'actual47_668HeadLoopWorst':joint_raw,'native72HeadLoopIntrinsicMotion':'Below0.077micrometre relative to neck frame: severe neutral flange is already the cropped/rest assembly, not a new head fold.','actual47_668HeadLoopIntrinsicMotion':'Up to61.027mm relative to neck; chest-versus-neck blend deforms the flared lower rims. The existing own-bind field is algebraically consistent; compatibility of borrowed attachment with this geometry is the local issue.','fullFourNative72CutLoopLossM':sample('native',72)['fullFourBodyCutLoopLossM']['maximum'],'fullFourActual47_668CutLoopLossM':sample('actual47',668)['fullFourBodyCutLoopLossM']['maximum'],'interpretation':'Extra body influences do not repair missing join/rest mismatch, and cannot alter the existing2-slot head lower rims. Fixed nearest-rest drift is not material seam strain or a signed depth.'}},'preciseInitialAuthoringMargin':{'bodyExistingRenderedNativeVertices':m['bodyRenderedNativeVerticesWithinTwoGraphRings'],'bodyExistingFullSourceVertexIDs':m['bodyFullSourceVertices'],'bodyExistingRenderedTriangleIDs':m['bodyRenderedTrianglesIncidentToMargin'],'bodyRestoreFromFrozenCanonicalSourceVertexIDs':m['originalCanonicalNeckRestoreBandSourceVertices1_54To1_60M'],'bodyRestoreCanonicalIncidentTriangleIDsForInspection':m['originalCanonicalTrianglesIncidentToRestoreBand'],'headInitialBoundaryLedNativeVertexIDs':m['headBoundaryLedTwoRingNativeVertices'],'headInitialBoundaryLedNativeTriangleIDs':m['headBoundaryLedTwoRingNativeTriangles'],'counts':{'existingBodyVertices':160,'existingBodyIncidentTriangles':320,'availableCanonicalNeckBandVertices':288,'canonicalIncidentTrianglesForInspection':700,'initialHeadVertices':1243,'initialHeadIncidentTriangles':2188},'upperInspectionEnvelope':'13,392 donor head triangles with all corners nativeZ<=1.60m /8,241 usedvertices are an anatomical proxy/maximum review envelope, NOT an automatic delete/move/weight permission. Expansion beyond initial2ring head margin requires an explicit new root scope decision. All head triangles touchingZ>1.60m and all chosen cheek294vertices/429triangles remain protected.','coordinateFrame':'Native metres+Xforward/+Zup/-Yleft; original fileX0.65 applied once. Lists use body52 current-native indices and explicit canonical source IDs; donor head original vertex/triangle mapping in neck-witnesses.npz.','sourceControlProtection':'Original full13380body, head43707/71826, own51rest/bind/pose/weights, UV/images and every failed source remain immutable controls. Work only a prospective derivative after root admission. The restoration list is input provenance, not permission to expose the old native face.'},'constructionContract':['Author a boundary/face inventory before replacement. The two donor low loops have opposed oriented area vectors and close nested dimensions; determine outer/inner material roles. Do not weld both onto one body ring or assume virtual coordinate aliases establish physical sewing. Four mouth-area loops/cheek and all face identity outside the admitted margin remain unchanged.','Restore the clipped canonical neck/shoulder contour only within the named existing-body margin and available original neck band, then define an explicit anatomical transition to the selected donor neck loop. Use a declared ordered seam parameterization/shared split registry; no global height mask, nearest-point weld/projection, donor-head translation or whole-body rebuild.','Enumerate changed/replaced source faces, added vertices and their physical weld identities. Original-restoring vertices retain source IDs only when positions/weights truly unchanged; new/altered transition geometry records derived/new ancestry, its own rest area and attribute donor separately. Do not claim inherited exact topology for new faces.','Keep authored rest geometry review separate from attachment review. Bind only the admitted transition, using the unchanged own51rest/bind and a coherent declared four-slot field on shared seam identities. Current protected face/cheek fields and all vertices outside margin must remain exact. Existing low-head weight changes, if needed, require explicit root admission as part of that same local derivative; never overwrite baseline weights or perform a global transfer.','No mask, face deletion chosen from the490contact list, normal-only camouflage, contact waiver or new clothing cover may substitute for the exposed neck join. If initial local margin cannot suffice, report the failed local trial and exact needed expansion; do not promote, widen automatically or replace the whole body.'],'measurableAcceptanceProxies':['Rest: explicit physical neck seam has no unmatched boundary/Tjunction/nonmanifold/winding/zero-area defect. Duplicate UV aliases at a declared seam have bit-identical authoredFloat32positions and semantic normalized weights. Verify which inner donor boundary remains and its explicit construction; do not claim full head containment/watertightness.','Existing fields: at every archived529native and703actual47source identity, declared physical seam aliases differ<=2micrometres after identicalLBS; independent full/four labels retained. This is a proposed precision bar, not a passed repaired measurement. Include one-corner triangles in all local collision/collapse checks; old defects outside patch remain recorded.','Exact protection: chosen face/cheek geometry/UV/images/material/bind/weights and source skin field outside admittedmargin match baseline; unchanged body/rig/controls hash-identical. No global offsets, scale, changed51bind or false-source ancestry.','Art: root plays new exposed-body front/side/rear at native72 and actual47_668 and the existing continuous streams. No severe collar flange, dark open neck rim or jagged moving ridge; source-normal/PBR engine equivalence remains a separate gate. QA counts cannot pass appearance.','Garment/head: remeasure against the actual new head/body targets with original failed garment controls kept. Record target/tessellation/pose changes. The preexisting490rear-neck contacts cannot be waived, and source26 remains failed/no engine admission until its separate rest/motion/visual/engine gates pass.'],'garmentCorrelation':{'preexisting490PairIDsAcross24_25_26':True,'contactUniqueHeadTriangles':330,'contactCoordinatesMatchCurrentHeadWithinM':r['garmentHeadCorrelation']['headTriangleCoordinateMaxResidualToCurrentNativeM'],'all330ContactTrianglesInsideUpperLowHeadInspectionEnvelope':r['garmentHeadCorrelation']['allContactHeadTrianglesInsideProposedLowHeadProxy'],'intersectionWithTested11HeadHitTriangleIDs':len({x['hit']['nativeTriangle'] for x in hit_head}&contacts),'interpretation':'Same lower-head anatomical neighborhood, but tested head-hit triangles are distinct from those330rear-neck garment-contact triangles. This does not prove all flange pixels are disjoint or establish a shared cause; methods and visibility remain separate.'},'evidencePins':{str(f.relative_to(qa)):sha(f) for f in [qa/'body58/preparation.json',out/'assessment.json',out/'neck-witnesses.npz',out/'pixel-ownership.json']},'limits':['Proposal only; no source/rig/head/body/weight edit, repair implementation, new Blender/render/export/controller capture, inference/model/GPU/installation, broad test suite, delivery/upload/promotion/publication.','Current native head ancestry is exact; complete oriented currentGLBhead ancestry remains unresolved due co-located export aliases. No scientific-report overwrite; originalbody53/body56/PDF53 unchanged.','Only18listed existing sample identities are diagnosed, not a new complete neck-motion certificate. Actual50 remains separate. Source26 failed motion and unrelated head/body self-contact and boxer/hip issues stay open.','Parent owns asks/index reconciliation and art/repair acceptance. All M0-M5 open; ordinary third-round normal-source gate60 remains separate from diagnosis.']}
(out/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
md=f'''# Severe neck flange: independent local repair proposal

Root verdict: **severe**, already neutral and raised/jagged in riding.
Retain the controlled full body and chosen face; no whole-body replacement
or successful local repair is established. Agent1 authors only after root
admits the precise margin; Agent3 has made no source edits or new capture.

## What is implicated

The current43,707-vertex/71,826-triangle native head is the EXACT selected
original donor mesh1/primitive0: original vertex order, oriented triangles
and semantic weights match. It preserves donor file-world geometry rather
than registering it to the hm08 body. Complete oriented GLB-head ancestry
is still unproven; this new native proof does not overwrite body52/53.

The current body retains9,037 canonical vertices and18,016 exact oriented
source triangles after deleting vertices above1.54m. Four extra triangle ears
are omitted beyond a triangle-only height test, consistent with whole-polygon
vertex deletion. The body has one56-edge cut loop,326.267mm wide. Donor head
has TWO lower cut loops,183/190vertices,227.839/217.145mm wide, with opposed
oriented area vectors. Virtual coordinate aliasing is not a physical weld.

There is no authored common join. At canonical rest, the actual body cut
vertices are **2.413–71.118mm** from the closest point on ANY head triangle
(median30.188mm). These distances are not penetration depth or a material
seam metric. Both independently cropped surfaces are implicated: stable
rays at already-played pixels find{len(dark_head)}dark lower-head witnesses and
{len(dark_body)}dark witnesses on the body cut margin. All72listed rays/misses
remain in `pixel-ownership.json`; no new picture/render was created.

Current head/body object matrices are EXACTLY equal and use the same own51
bind; no double0.65m offset is present. Donor-versus-own rest bone origins
differ by51.032mm(chest),66.410mm(neck),122.115mm(head), while donor vertices
and semantic weights were kept. This identifies a geometry/attachment
compatibility problem; it is not permission to alter the rig or globally
register/translate the chosen face.

Lower head rims have only chest/neck influences, averaging about52/48%;
there are no fifth weights to recover. Their intrinsic motion is below
0.077µm at native72, so the neutral flange preexists pose deformation.
At actual47input668, their neck-reference displacement reaches
**61.027/58.917mm**, with an8.46mm rest rim height span becoming71.91mm.
Worst outer vertex29793 keeps chest0.623411/neck0.376589. Relative chest/neck
attachment deforms the existing flared cut. Fixed rest nearest references
between body/head drift19.467mm(native72),56.393mm(actual668); body full/four
losses there are2.373/4.707mm. These reference pairs are NOT proposed sew
correspondences. Algebra and archived-body parity close below0.198µm.

## Precise first local trial for Agent1

Use a NEW candidate derivative. Preserve full13,380body, original protected
head/face/cheek, own51rest/bind/weights and every failed source as byte-pinned
controls. All index lists and original donor ancestry are in `proposal.json`
and `neck-witnesses.npz`.

- Body:160existing vertices/two graph rings around the56-node cut,320incident
  triangles. Inspect288original canonical neck-band vertices between1.54
  and1.60m and700incident canonical triangles as possible restoration input;
  do not expose the discarded native face or claim all700may be copied.
- Head:initial boundary-led two-ring margin1,243vertices/2,188incident
  triangles around BOTH lower loops. Determine outer/inner material roles
  first; do not weld three loops together or cap arbitrary surfaces.
- Upper inspection envelope:8,241head vertices/13,392all-corner triangles
  at/below1.60m. This is a proxy and maximum review envelope, **not automatic
  authoring permission**. Any expansion beyond the initial head margin
  requires a new explicit root scope. Protect every head triangle touching
  above1.60m and the entire294-vertex cheek patch.

Restore the anatomical neck/shoulder contour and author ONE declared local
transition using ordered boundary correspondence and a shared split/weld
registry. No new horizontal masking, nearest-point projection/weld, global
head transform or body rebuild. Record original/restored versus derived/new
geometry honestly. Review rest geometry before locally binding this same
patch; preserve chosen-face motion and all fields outside the admitted
margin. Any low-head weight change needs explicit root admission in the
prospective derivative. Baseline source weights remain immutable.

Future proxies: no neck seam Tjunction/nonmanifold/winding/zero-area defect;
bit-identical authored seam position/semantic weights; <=2µm alias drift
under all existing529native+703actual47matrices; no new local crossings or
collapse including one-corner faces. Root must play the exact exposed-body
views and judge disappearance of the severe flange. These are proposed
bars, not passed repaired results. If the margin cannot suffice, file the
local failure and precise expansion needed; do not widen or promote.

## Distinct garment/head correlation and limits

All490preexisting rear-neck garment/head pairs across24/25/26 remain a
separate surface-contact finding. Their330head triangles lie in the larger
low-head inspection envelope and coordinates match current native head
within0.120µm. None of the11head-hit triangles in the listed pixel samples
is one of those330; this is not universal visual disjointness or shared-cause
proof. No alpha/culling visibility, signed depth, containment, face deletion
chosen from contact IDs, normal camouflage or contact waiver follows.
Source26 still FAILS motion/no engine admission; keep all controls.

Only18existing pose identities are diagnosed. CurrentGLBhead alias ancestry,
other head/body self-contact, covered proximal hips, boxer breakthrough,
mobile/stranger and all M0–M5 remain open. Original body53/body56/PDF53 are
unchanged. Parent owns asks/index reconciliation, next repair and acceptance;
no upload, user/Library delivery, outbound acknowledgment or publication.
'''
import re
md=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-zµ])', ' ', md)
for old,new in [('body 52','body52'),('body 53','body53'),('body 56','body56'),('PDF 53','PDF53'),('hm 08','hm08'),('M 0–M 5','M0–M5')]:md=md.replace(old,new)
(out/'FINDING.md').write_text(md)
receipt={'status':'UNACCEPTED_BOUNDED_NECK_PROPOSAL_READY_FOR_ROOT_RETRIEVAL','preparationCheckpoint':'495a2d3e7b5eab1c2ede413731dc99d5d7f4aacb','validation':{'originalNativeHeadAncestryExact':True,'bodyVertexAncestryExactAndOrientedTrianglesSourceSubset':True,'rawAndVirtualBoundaryCountsVerified':True,'selectedExistingSamples':len(rows),'maximumBodyFieldParityM':max(s['fourBodyManualStreamParityM'] for s in rows),'maximumAttachmentAlgebraResidualM':max(s['attachmentDecompositionMaxAbsResidualM'] for s in rows),'existingPlayedPixelRays':len(p['rows']),'stableDarkLowHeadHits':len(dark_head),'stableDarkBodyMarginHits':len(dark_body),'garmentWitnessCoordinateResidualM':r['garmentHeadCorrelation']['headTriangleCoordinateMaxResidualToCurrentNativeM']},'evidence':{},'limits':proposal['limits']}
prep=json.loads((qa/'body58/preparation.json').read_text())
for path,pin in prep['pins'].items():
 assert sha(path)==pin['sha256'],path
baseline=json.loads((qa/'body56/finding.json').read_text())
for name,pin in baseline['evidence'].items():
 assert sha(qa/'body56'/name)==pin['sha256'],name
assert sha(qa/'body53/whole-body-assessment.pdf')==baseline['originalPDF53PreservedSHA256']
receipt['validation']['all24PreparationPinsUnchanged']=len(prep['pins'])==24
receipt['validation']['body56StableOutputsUnchanged']=len(baseline['evidence'])
receipt['validation']['originalBody53PDFUnchanged']=True
for file in sorted(out.iterdir()):
 if file.is_file() and file.name!='finding.json':receipt['evidence'][file.name]={'bytes':file.stat().st_size,'sha256':sha(file)}
(out/'finding.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['validation'],indent=2))
