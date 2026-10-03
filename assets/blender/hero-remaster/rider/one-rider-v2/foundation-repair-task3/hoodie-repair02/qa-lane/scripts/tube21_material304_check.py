from pathlib import Path
import sys,json,hashlib,numpy as np
sys.dont_write_bytecode=True
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03';LOCAL=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3');OUT=Q/'uv-lower01/tube21-material304';OUT.mkdir(exist_ok=True)
def load(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
restpath=HERE/'source-sleeve-tube-rest21-uvchart.npz';posepath=LOCAL/'deliverables/tube21-material304.npz';basepath=LOCAL/'v7-snapshot-baseline.npz';driverpath=HERE/'responding_surface22.py';controlpath=ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz'
assert hashlib.sha256(restpath.read_bytes()).hexdigest()=='64af529f13f546d59f58679d96afad13fe99b4dbc4152517cacb319b273bf150'
assert hashlib.sha256(posepath.read_bytes()).hexdigest()=='b9a3f6c6f65726223a4fe52e3875b857a987391fe837d1c6eff28a64038d1ba9'
rest,posed,base,control=[load(p) for p in [restpath,posepath,basepath,controlpath]];index=int(np.flatnonzero(control['sampleIndices']==304)[0]);D=control['D'][index];prior=load(ROOT/'hoodie-repair03/poses/game304-v7-plain.npz');assert abs(prior['matrices']-D).max()<1e-11
# Source morphs are decoded independently from C19; matrix LBS uses the frozen V7 geometry/weights.
code=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+code[code.index('def decode('):code.index("manifest={'tolerance_m'")],ns);doc,bin,_=ns['decode'](Q/'C19-source.glb');pr=[p for m in doc['meshes'] for p in m['primitives']];morph=[];baseline=[]
for i,p in enumerate(pr):
 delta=np.zeros_like(base[f'p{i}'])
 for target in p.get('targets',[]):
  if 'POSITION' in target:delta+=ns['array'](doc,bin,target['POSITION'])
 morph.append(delta);baseline.append(np.einsum('vb,bjk,vk->vj',base[f'W{i}'],D[:,:3,:],np.c_[base[f'p{i}']+delta,np.ones(len(delta))],optimize=False))
# Execute the frozen driver once read-only for trace/identity parity, not a pose family.
sys.path.insert(0,str(HERE));from responding_surface22 import RespondingSleeve
recipe_sha=hashlib.sha256(driverpath.read_bytes()).hexdigest();driver=RespondingSleeve(restpath);replay=driver.deform(D,closed=True);replay[1]=prior['p1'].copy();driver_delta=[float(np.linalg.norm(replay[i]-posed[f'p{i}'],axis=1).max()) for i in range(5)]
# Independent literal checker and physical aliases, same exclusions for both variants.
ns2={};audit_code=(Q/'scripts/tube06_rest_qualify.py').read_text();exec(audit_code[:audit_code.index('\nsource_weld =')],ns2);audit=ns2['audit'];source_alias=ns2['source_alias'];offset=ns2['source_offsets'];bweld=[source_alias[offset[i]:offset[i+1]] for i in range(5)]

def seams(P,F):
 ids=np.r_[F['physicalWeld0'],F['physicalWeld2']];positions=np.r_[P[0],P[2]];active=np.r_[np.unique(F['tr0']),np.unique(F['tr2'])+len(P[0])];groups={}
 for v in active:groups.setdefault(int(ids[v]),[]).append(int(v))
 worst=0;witness=None;count=0
 for k,rows in groups.items():
  if len(rows)<2:continue
  count+=1
  for a in range(len(rows)):
   for b in range(a+1,len(rows)):
    gap=float(np.linalg.norm(positions[rows[a]]-positions[rows[b]]))
    if gap>worst:worst=gap;witness={'physicalWeld':k,'vertices':[[0,v] if v<len(P[0]) else [2,v-len(P[0])] for v in [rows[a],rows[b]]]}
 return {'referenced_cloth_alias_groups':count,'maximum_actual_pair_gap_m':worst,'witness':witness}
def metrics(P,F):
 rows=[]
 for i in [0,2]:
  tri=F[f'tr{i}'];a=F[f'p{i}'][tri];b=P[i][tri];area0=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1);area1=np.linalg.norm(np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]),axis=1);rat=area1/np.maximum(area0,1e-30);new=np.array([str(x).startswith(('body-cap','new-tube')) for x in F[f'faceKind{i}']]);e=np.unique(np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1),axis=0);l0=np.linalg.norm(F[f'p{i}'][e[:,1]]-F[f'p{i}'][e[:,0]],axis=1);l1=np.linalg.norm(P[i][e[:,1]]-P[i][e[:,0]],axis=1);stretch=l1[l0>=.005]/l0[l0>=.005];rows.append({'primitive':i,'quarter_area_collapse_all':int((rat<.25).sum()),'quarter_area_collapse_new_cap_tube':int(((rat<.25)&new).sum()),'edge_rest_threshold_m':.005,'edge_stretch_max':float(stretch.max()),'edge_stretch_p99':float(np.quantile(stretch,.99))})
 return rows
BF=dict(base)
for i in range(5):BF[f'physicalWeld{i}']=bweld[i];BF[f'sourceFaceAncestry{i}']=np.arange(len(base[f'tr{i}']));BF[f'faceKind{i}']=np.full(len(base[f'tr{i}']),'V7-source-control')
results=[]
for label,P,F in [('V7-source-control304',baseline,BF),('tube21-material304',[posed[f'p{i}'] for i in range(5)],rest)]:
 A,_=audit(label,P,[F[f'tr{i}'] for i in range(5)],[F[f'physicalWeld{i}'] for i in range(5)],[F[f'sourceFaceAncestry{i}'] for i in range(5)],[F[f'faceKind{i}'] for i in range(5)])
 # Use rest coordinates to classify upper ROI. Bike-frame posed Y is not anatomical height.
 A['upper_ROI_restY1_08_involved_pairs']=sum(any(F[f'p{f["primitive"]}'][F[f'tr{f["primitive"]}'][f['face']]][:,1].max()>=1.08 for f in h['faces']) for h in A['all_crossing_witnesses']);A.pop('full_upper_crossing_count',None)
 newpairs=sum(any(str(f['kind']).startswith(('body-cap','new-tube')) for f in h['faces']) for h in A['all_crossing_witnesses']);results.append({'variant':label,'literal_audit':A,'new_cap_tube_involved_pairs':newpairs,'referenced_seams':seams(P,F),'area_and_stretch':metrics(P,F)})
checks={'authoritative_D_matches_frozen_previous304':abs(prior['matrices']-D).max()<1e-11,'frozen_driver22_replay_matches_material_snapshot':max(driver_delta)<1e-11,'recorded_closed_glove_control_p1_exact':np.array_equal(posed['p1'],prior['p1']),'protected_source_prefix_P_matches_same_worldD_and_closed_source_morphs':max(float(np.linalg.norm(posed[f'p{i}'][:len(base[f'p{i}'])]-baseline[i],axis=1).max()) for i in range(5))<1e-11}
report={'status':'TRACE_PARITY_PASS_POSED_MATERIAL_REJECTED' if all(checks.values()) else 'TRACE_FAILURE','checks':{k:bool(v) for k,v in checks.items()},'hashes':{'candidate_rest':hashlib.sha256(restpath.read_bytes()).hexdigest(),'candidate_pose':hashlib.sha256(posepath.read_bytes()).hexdigest(),'driver22':recipe_sha,'V7_baseline':hashlib.sha256(basepath.read_bytes()).hexdigest(),'authoritative_controls':hashlib.sha256(controlpath.read_bytes()).hexdigest(),'actual_D304_array':hashlib.sha256(D.tobytes()).hexdigest()},'driver_replay_max_errors_by_primitive_m':driver_delta,'variants':results,'limits':['Exactly one recorded pose; no broad family or continuous/runtime/art certificate.','Strict transverse actual triangles, same physical shared-edge exclusion and one-corner accounting for both variants; coplanar/tangent/thickness unclassified.','Upper ROI uses restY rather than posed bike-frameY.','Current owning-container conditioning174 fix is parent-verified; prior reconditioning damage is historical and is not applied here.','Offline material driver is distinct from stock four-weight LBS and no equivalence is claimed.']}
(OUT/'independent-material304-v7-control.json').write_text(json.dumps(report,indent=2));print(report['status'],checks);print([(r['variant'],r['literal_audit']['strict_zero_shared_weld_crossings'],r['literal_audit']['strict_one_shared_weld_crossings'],r['new_cap_tube_involved_pairs'],r['referenced_seams'],r['area_and_stretch']) for r in results])
