from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
r=json.loads((root/'comparison-validation.json').read_text())
c=json.loads((root/'conditioning.json').read_text())
s={'date':r['date'],'engine':r['engine'],'method':r['method'],'tolerance_m':r['tolerance_m'],'failures':r['failures'],'total_vertex_comparisons':sum(v['parity_summary']['vertex_comparisons']for v in r['variants']),'variants':[],'production_compatible':False,'compatibility_note':'C19/C prefixed bones need an isolated named driver adapter; C additionally has 23 bones with half-angle helpers. GLTFLoader handles both. Gameplay driver/contact compatibility not asserted.','skinning':'Installed Three.js r186 CPU/shader weighted matrix LBS, four influences; Blender preserve volume/DQ is not transferred by standard glTF.','conditioning_note':'Actual installed sleeve conditioning changes zero hip ROI vertices in baseline/A/B/C19/C. Fresh names skip the conditioning function.','conditioning_cuff_witness_gaps':c['witness_gaps'],'visual_acceptance_asserted':False}
for v in r['variants']:
 actual_hash=hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()
 if actual_hash!=v['sha256']:raise ValueError(f'{v["id"]}: validation stale; source GLB changed')
 s['variants'].append({'id':v['id'],'sha256':v['sha256'],'joint_counts':v['raw_skin_joint_counts'],'clips':len(v['clips']),'sampled_poses':sum(x['sample_count']for x in v['clips']),'parity':v['parity_summary'],'true_endpoint_samples':sum(x['kind']=='true_endpoint'for cl in v['clips']for x in cl['samples']),'holdout_samples':sum(x['kind']=='interpolation_holdout'for cl in v['clips']for x in cl['samples']),'conditioning_changed_vertices':sum(x['changed_vertices']for x in c['rows']if x['variant']==v['id']),'conditioning_hip_roi_changed_vertices':sum(x['hip_roi_changed']for x in c['rows']if x['variant']==v['id'])})
(root/'summary.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({'failures':s['failures'],'vertices':s['total_vertex_comparisons'],'variants':[(v['id'],v['sha256'],v['parity']['max_m'])for v in s['variants']]},indent=2))
