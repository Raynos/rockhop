"""One frozen CPU triangle/alias comparison. No pose synthesis or acceptance.
Usage: python frozen_pose_gate.py manifest.json
New shell cloth topology may differ; require explicit physical weld IDs, hashes,
controlled source D and protected primitive selectors. No fixture expansion.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane'
config=json.loads(Path(sys.argv[1]).read_text());out=Path(config['output']);out.parent.mkdir(parents=True,exist_ok=True)
def load(spec):
 p=Path(spec['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==spec['sha256'],'Frozen input changed: '+str(p)
 with np.load(p) as z:return {k:z[k] for k in z.files}
rest=load(config['rest']);candidate=load(config['candidate_pose']);control=load(config['control_pose']);ns={};s=(Q/'scripts/tube06_rest_qualify.py').read_text();exec(s[:s.index('\nsource_weld =')],ns);audit=ns['audit'];mapped_aliases=np.r_[rest.get('embedSourceAliasesL',[]),rest.get('embedSourceAliasesR',[])].astype(int);declared_global=np.union1d(rest.get('embedAffectedSourceFacesL',[]),rest.get('embedAffectedSourceFacesR',[])).astype(int)
checks={};protected=config.get('protected_primitives',[1,3]);tri=[rest[f'tr{i}'] for i in range(5)];weld=[rest[f'physicalWeld{i}'] for i in range(5)];anc=[rest[f'sourceFaceAncestry{i}'] for i in range(5)];kind=[rest[f'faceKind{i}'] for i in range(5)];masks={};results=[]
for i in [0,2]:
 offset=0 if i==0 else len(rest['tr0']);masks[i]={'declared':np.isin(np.arange(len(tri[i]))+offset,declared_global),'active_alias':np.isin(weld[i][tri[i]],mapped_aliases).any(1)}
for i in protected:checks[f'protected_primitive{i}_pose_exact_control']=np.array_equal(candidate[f'p{i}'],control[f'p{i}'])
for i in range(5):
 checks[f'p{i}_finite_and_expected_count']=candidate[f'p{i}'].shape==rest[f'p{i}'].shape and np.isfinite(candidate[f'p{i}']).all()
 if len(mapped_aliases):
  outside=~np.isin(weld[i],mapped_aliases);checks[f'p{i}_outside_material_aliases_exact_control']=bool(np.array_equal(candidate[f'p{i}'][outside],control[f'p{i}'][outside]))
for label,pose in [('same-source-LBS-control',control),('candidate',candidate)]:
 P=[pose[f'p{i}'] for i in range(5)];A,_=audit(label,P,tri,weld,anc,kind);A.pop('full_upper_crossing_count',None);regional={mask:sum(any(masks[f['primitive']][mask][f['face']] for f in h['faces']) for h in A['all_crossing_witnesses']) for mask in ['declared','active_alias']};metrics=[]
 for i in [0,2]:
  t=tri[i];a=rest[f'p{i}'][t];b=P[i][t];area0=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1);area1=np.linalg.norm(np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]),axis=1);ratio=area1/np.maximum(area0,1e-30);e=np.unique(np.sort(np.r_[t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]],axis=1),axis=0);l0=np.linalg.norm(rest[f'p{i}'][e[:,1]]-rest[f'p{i}'][e[:,0]],axis=1);l1=np.linalg.norm(P[i][e[:,1]]-P[i][e[:,0]],axis=1);stretch=l1[l0>=.005]/l0[l0>=.005];metrics.append({'primitive':i,'all_quarter_area_collapse':int((ratio<.25).sum()),'declared_affected_faces':int(masks[i]['declared'].sum()),'declared_quarter_area_collapse':int(((ratio<.25)&masks[i]['declared']).sum()),'active_alias_faces':int(masks[i]['active_alias'].sum()),'active_alias_quarter_area_collapse':int(((ratio<.25)&masks[i]['active_alias']).sum()),'edge_minimum_rest_length_m':.005,'edge_stretch_max':float(stretch.max()),'edge_stretch_p99':float(np.quantile(stretch,.99))})
 groups={}
 for i in range(5):
  for v in np.unique(tri[i]):groups.setdefault(int(weld[i][v]),[]).append((i,int(v)))
 gap=0;witness=None
 for uid,vs in groups.items():
  for a in range(len(vs)):
   for b in range(a+1,len(vs)):
    pi,v=vs[a];pj,w=vs[b];d=float(np.linalg.norm(P[pi][v]-P[pj][w]))
    if d>gap:gap=d;witness={'physicalWeld':uid,'vertices':[vs[a],vs[b]]}
 results.append({'variant':label,'literal_audit':A,'affected_pair_counts_corrected_all_cloth':regional,'metrics':metrics,'referenced_all_primitive_seam_max_m':gap,'seam_witness':witness})
r={'status':'FROZEN_POSE_CONTRACT_TRACE_PASS_GEOMETRY_REJECTED' if all(checks.values()) else 'CONTRACT_TRACE_FAIL','manifest':config,'checks':{k:bool(v) for k,v in checks.items()},'variants':results,'mask_definition':'Declared combined source-face indices are split at primitive0 face count and include primitive2. Active-alias mask separately includes each triangle incident to material-mapped physical aliases. Same masks and shared-edge exclusions for candidate/control.','limits':['Exactly one supplied frozen pose; no pose synthesis,fixture expansion or new moving render.','Output requires original owning fixture/driver trace for full D/rig/runtime proof; this checker does not infer D from vertices.','Strict transverse cloth0+2 only; coplanar/tangent contact,collar-head,cuff-glove triangle contact,thickness,volume and support unqualified.','Future shell may replace cloth topology: use its own explicit physical weld/region/protected mappings and matched reference manifest; original cloth P/tri equality is not a required shell contract.']};out.write_text(json.dumps(r,indent=2));print(r['status']);print([(v['variant'],v['literal_audit']['strict_zero_shared_weld_crossings'],v['literal_audit']['strict_one_shared_weld_crossings'],v['affected_pair_counts_corrected_all_cloth'],v['metrics'],v['referenced_all_primitive_seam_max_m']) for v in results])
