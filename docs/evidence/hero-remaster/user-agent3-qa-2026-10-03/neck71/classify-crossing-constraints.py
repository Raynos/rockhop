"""Separate authoring-scope freedom from tangent-operator degrees of freedom."""
import json,hashlib
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface102';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck70/preparation.json').read_text());native=json.loads((out/'native-preservation-crossings.json').read_text());w=dict(np.load(ev/'solve-witnesses.npz'));c=dict(np.load(ev/'candidate-fields-ancestry-corrected.npz'));NB=len(c['bodyRestXYZ']);mapping=w['physicalRawToNode'];active=set(map(int,w['freePhysicalNodes'][w['variableOwner']]));scope_free=set(map(int,w['freePhysicalNodes']));counts={};examples={}
for kind,parts in [('bodySelf',('body','body')),('headSelf',('head','head')),('bodyHead',('body','head'))]:
 rows=native['contacts'][kind]['witnesses'];n_dof=n_noncap=0;examples[kind]=[]
 for row in rows:
  vertices=[];dims=[]
  for part,triangle in zip(parts,row['triangleIDs']):
   ids=mapping[:NB] if part=='body' else mapping[NB:];nodes=ids[c[part+'Triangles'][triangle]];vertices.append(nodes.tolist());dims.append([int((w['variableOwner']==np.flatnonzero(w['freePhysicalNodes']==node)[0]).sum()) if node in scope_free else 0 for node in nodes])
  nonzero=all(all(d>0 for d in face) for face in dims);n_dof+=nonzero;n_noncap+=nonzero and not row['innerCapParticipates']
  if nonzero and not row['innerCapParticipates'] and len(examples[kind])<3:examples[kind].append({**row,'physicalNodesByFace':vertices,'tangentDegreesOfFreedomByFace':dims})
 counts[kind]={'properFinitePairs':len(rows),'scopeFreeFreePairs':native['contacts'][kind]['freeFreePairs'],'allVerticesHaveNonzeroTangentDOFPairs':int(n_dof),'allVerticesHaveNonzeroTangentDOFNonCapPairs':int(n_noncap),'innerCapParticipatingPairs':native['contacts'][kind]['innerCapParticipatingPairs']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
report={'status':'UNACCEPTED_FROZEN_CROSSING_SCOPE_AND_OPERATOR_CLASSIFICATION','recipeSHA256':sha(__file__),'nativeCrossingReportSHA256':sha(out/'native-preservation-crossings.json'),'scopeFreePhysicalNodes':len(scope_free),'nonzeroTangentDOFPhysicalNodes':len(active),'scopeFreeButRank3ZeroDOFNodes':len(scope_free-active),'counts':counts,'nonCapNonzeroDOFFiniteExamples':examples,'normalProtectionRefinement':[x for x in native['decodedNormalDifferences'] if x['field']=='four'],'limits':['Free/free685/263 is scope freedom.124scope-free nodes have rank3 tangent clamps and zero operator DOFs. More conservative523/243crossings still have nonzero tangent DOFs at every corner;360/181also exclude cap faces.','These finite witnesses reject an explanation based only on exterior pins or only the cap. They do not identify a unique repair, prove scope insufficiency, or establish necessity/sufficiency of the464ID collar.','Decoded normal counts include the60 admitted aliases explicitly pinned by scope, in addition to outside-authoring vertices. No source normals were edited and no appearance judgment is implied.']}
(out/'crossing-constraint-classification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='nonCapNonzeroDOFFiniteExamples'},indent=2))
