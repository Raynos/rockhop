#!/usr/bin/env python3
"""Freeze read-only bounded accounting evidence; no owner or GPU writes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
ROOT = Path('/Users/raynos/projects/games/rockhop')
OWNER = ROOT/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3'
SHAPE = OWNER/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
OUT = ROOT/'docs/evidence/hero-remaster/one-rider-v2/construction-bounds177'

def file(p):
 d=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}

def candidate(n):
 ps=list(SHAPE.glob(f'source-sleeve-tube-rest{n:02d}*.npz')) if n!=1 else [SHAPE/'source-sleeve-tube-rest.npz']
 assert len(ps)==1
 p=ps[0];q=p.with_name(p.stem+'-provenance.json')
 j=json.loads(q.read_text());f=file(p)
 assert f['sha256']==j['candidateSHA256']
 return {'variant':n,'source':f,'provenance':file(q),'provenance_content':j},p

rows=[]
for n in [1,5,8,9,11,12,13,14,15,16,17]:
 row,p=candidate(n);g=p.with_name(p.stem+'.rest-gate.json') if n!=1 else SHAPE/'source-sleeve-tube-rest-gate.json'
 j=json.loads(g.read_text()); assert j['candidateSHA256']==row['source']['sha256']
 assert j['strictNonadjacentCrossings']+j['strictOneCornerCrossings']>0
 row.update({'failure_stage':'rest','failure_receipt':file(g),'nonadjacent':j['strictNonadjacentCrossings'],'one_corner':j['strictOneCornerCrossings']});rows.append(row)
status=SHAPE/'CONSTRUCTION-STATUS10.json'
checkpoint=ROOT/'docs/evidence/hero-remaster/one-rider-v2/foundation-repair-task3/current-construction03-checkpoint.txt'
for n,r,e in [(2,status,'Root02 pipe thin with atlas stripes rejected'),(7,status,'07fuller sleeve stilllongbackgroundgaps front/back, rejected byowner'),(10,checkpoint,'Standing comparison rejects tube10')]:
 assert e in r.read_text();row,_=candidate(n)
 row.update({'failure_stage':'standing','failure_receipt':file(r),'explicit_rejection_excerpt':e});rows.append(row)
row,_=candidate(6)
carrier=OWNER/'hoodie-repair03/tube03-four-bind/four-cap-carrier06-envelope.npz'
carrier_report=carrier.with_name(carrier.stem+'-report.json')
j=json.loads(carrier_report.read_text()); assert j['sourceSHA256']==row['source']['sha256'] and j['candidateSHA256']==file(carrier)['sha256']
export=ROOT/'docs/evidence/hero-remaster/one-rider-v2/candidate-export172/export-report.json';j=json.loads(export.read_text());assert j['npzSHA256']==file(carrier)['sha256']
motion=ROOT/'docs/evidence/hero-remaster/one-rider-v2/tube-motion173/README.md'
assert 'short moving appearance remains rejected' in motion.read_text()
row.update({'failure_stage':'motion','failure_receipt':file(motion),'carrier':file(carrier),'carrier_receipt':file(carrier_report),'export_receipt':file(export),'export_content':j});rows.append(row)
assert len(rows)==15 and len({x['source']['sha256'] for x in rows})==15
pending=[]
for n in range(18,22):
 row,p=candidate(n);g=p.with_name(p.stem+'.rest-gate.json')
 if g.exists():
  j=json.loads(g.read_text());assert j['candidateSHA256']==row['source']['sha256']
  row.update({'rest_receipt':file(g),'stored_rest':{k:v for k,v in j.items() if k!='witnessCombinedFacePairs'}})
 pending.append(row)
policy=ROOT/'docs/plans/sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md'
ledger=ROOT/'docs/evidence/hero-remaster/rider-search-v1/defect-ledger.json'
read=json.loads(ledger.read_text())
report={'snapshot_utc':datetime.now(timezone.utc).isoformat(),'status':'CONSERVATIVE_15_DISTINCT_FAILED_SOURCE_OUTPUTS_RECONSTRUCTED_NO_FORMAL_OWNER_COUNTER',
 'family_definition':'Source-preserving proximal sleeve reconstruction: retained V7 torso boundary + harmonic torso cap/opening + independently transported RMF tube to exact cuff-connected cut ring; source profiles and variants remain descendants.',
 'failure_entries':sorted(rows,key=lambda x:x['variant']),'failure_count_lower_bound':15,
 'failed_rest_count':11,'failed_standing_count':3,'failed_motion_count':1,'failed_setup_count_included':0,
 'classification':'Auditor reconstruction for parent decision; no owner-approved stable defect/approach/family IDs or per-approach counter found. One failed output counted once; different test cases and reports are not additional attempts.',
 'five_attempt_finding':'Exact per-approach count is not reliably recorded. Parameter-only curve/control/radius changes cannot reset approach counts; wider harmonic opening/collar/dart interventions alter mechanics but retain the source/tube family.',
 'fifteen_attempt_recommendation':'Treat same unresolved shoulder/underarm structural construction family as exhausted on this conservative15 record, freeze it and select clean continuous garment architecture before further family repairs. Parent owns final classification. Missing historical setup/texture trials can only increase count; do not use missing ledger to authorize attempt16.',
 'pending_descendants':pending,
 'policy_file':file(policy),'root_ledger_file':file(ledger),'root_recorded_context':{k:read[k] for k in ['failurePolicy','constructionReview169','tubeMotion173','constructionSnapshot175']},
 'alternative':'New source lineage: author one continuous, regular topology upper hoodie shell (torso, shoulders and proximal sleeves) over clean anatomy, using a raglan seam/gusset pattern or continuous sculpt/retopology instead of another retained concave-root annulus/RMF strip. Retain liked head/hood silhouette and distal cuff donor boundaries only with explicit sewing/protected contracts. Bind via anatomy mapping, then corrective shapes/pose driver exported to Three.js for continuous validation.',
 'limits':['Read-only receipts and hash verification, no collision rerun, art playback or acceptance.','17 now fails44strict nonadjacent crossings, distinct from pending17 at receipt175.','18 has stored0+0rest crossings;19-21normal/UV derivatives have no new accepted standing/motion result identified. Rest-only progress never certifies fallback architecture or runtime.','No automatic count of variant filenames, successful source transfers, pending sources, repeated evidence views or earlier different annulus/native-template architectures.']}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'snapshot_utc':report['snapshot_utc'],'failed_unique_outputs':15,'rest':11,'standing':3,'motion':1,'report_sha256':file(OUT/'report.json')['sha256']}))
