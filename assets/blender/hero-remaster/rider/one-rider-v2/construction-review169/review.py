"""Read-only integration-owner receipt review; no duplicated garment repair."""
from pathlib import Path
import hashlib,json
ROOT=Path('/Users/raynos/projects/games/rockhop')
SOURCE=ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3'
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/construction-review169'
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[SOURCE/'hoodie-repair02/rig-lane/construction-weights'/n for n in ['STATUS.json','finite-gates.json','weights-provenance.json']]
paths += [SOURCE/'hoodie-repair03/construction01/armhole-chart-outward.json',SOURCE/'hoodie-repair03/renders/construction/armhole01/render-provenance.json',SOURCE/'hoodie-repair03/evidence/authoritative-168-input-equivalence.json']
sources={str(p):{'SHA256':sha(p),'bytes':p.stat().st_size}for p in paths}
status=json.loads(paths[0].read_text());gate=json.loads(paths[1].read_text());provenance=json.loads(paths[2].read_text());construction=json.loads(paths[3].read_text());render=json.loads(paths[4].read_text());equiv=json.loads(paths[5].read_text())
geometry=Path(gate['geometryPath']);digest=sha(geometry)
assert digest==gate['geometrySHA256']==status['sameGeometrySHA256']==provenance['geometrySHA256']==construction['candidateSHA256']==render['candidateSHA256']
sources[str(geometry)]={'SHA256':digest,'bytes':geometry.stat().st_size}
for variant,rec in provenance['variants'].items():
 p=Path(rec['path']);assert sha(p)==rec['SHA256'];sources[str(p)]={'SHA256':rec['SHA256'],'bytes':p.stat().st_size}
glb=Path(construction['output']);assert sha(glb)==construction['sha256']==render['glbSHA256'];sources[str(glb)]={'SHA256':sha(glb),'bytes':glb.stat().st_size}
rows=[]
for r in gate['rows']:
 if r['probe']=='neutral' or (r['probe']=='actual_source34' and r['fraction']==304):
  rows.append({k:r[k]for k in ['variant','probe','fraction','holdout','worldMatricesSHA256','strictNonadjacentCrossings','strictOneCornerCrossings','collapsedNewFabricFaces25Pct','maxEdgeMinRest2mm','physicalSeamAliasMaxGapM']})
assert rows and status['status']=='REJECTED_POSED_CROSSINGS_COLLAPSE_STRETCH'
allPoses={}
for variant in ['shape_control','fabric-ownership','fabric-anatomical']:
 group=[r for r in gate['rows']if r['variant']==variant];assert len(group)==12
 allPoses[variant]={'poses':len(group),'maximumCrossings':max(r['strictNonadjacentCrossings']for r in group),'maximumCollapsedNewFabricFaces25Pct':max(r['collapsedNewFabricFaces25Pct']for r in group),'maximumStretchRestEdgesAtLeast2mm':max(r['maxEdgeMinRest2mm']for r in group)}
for name in ['rest-front-gray.png','rest-side-gray.png','recorded304-exact-side-gray.png']:
 p=SOURCE/'hoodie-repair03/renders/construction/armhole01'/name;sources[str(p)]={'SHA256':sha(p),'bytes':p.stat().st_size}
authoritative=Path(equiv['authoritativeReport']);assert sha(authoritative)==equiv['authoritativeReportSHA256']
for key,dkey in [('newAuthoritativeInput','newAuthoritativeInputSHA256'),('ownPortableInput','ownSHA256')]:
 p=Path(equiv[key]);assert sha(p)==equiv[dkey];sources[str(p)]={'SHA256':sha(p),'bytes':p.stat().st_size}
assert equiv['snapshots']==[35,114,186,304,426,445,446,447]
result={'status':'REJECTED_FOR_INTEGRATION_NOT_A_NEW_REPAIR','sources':sources,'geometrySHA256':digest,'selectedRows':rows,'finitePoseSummary':allPoses,'owner':'Independent task3 foundation-repair-task3; parent integration and acceptance only','protectedSourceReceipt':{'sameRestGeometryJointsUVsTextures':provenance['sameRestGeometryJointsUVsTextures'],'protectedHeadGlovesSourceRowsExact':provenance['protectedHeadGlovesSourceRowsExact'],'newFabricOnly':provenance['newFabricOnly']},'parentDiagnosticReview':'Corrected referenced-vertex neutral front/side and literal recorded304 gray render inspected. Neutral appearance alone is plausible; posed shoulder shows a large open/folded join and unacceptable cloth volume. These are diagnostics, not a played-motion gate pass. Existing actual matched films remain rejected.','decision':'Do not integrate the render-only GLB or repeat static added-fabric weight tuning as a finished repair. Task3 retains ownership of a different construction/material-response technique. Require a complete rest-valid garment and the existing exported continuous Three pose gate before cosmetics.','sourceOfNextTechnique':status['nextTechniqueRequiresParentCoordination'],'limits':['Receipt/hash review authenticates existing finite tests; parent did not re-exhaust their intersection search.','Twelve finite poses are not continuous collision or appearance acceptance.','Topology ancestry and small seam gaps do not guarantee cloth area/volume or absence of visible openings.','Historical V7 baked upper-cloth result remains distinct; no replacement of selected head, physics driver or current normal player asset.']}
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'inputHashes':len(sources),'selectedRows':rows,'finitePoseSummary':allPoses}))
