from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';code=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+code[code.index('def decode('):code.index("manifest={'tolerance_m'")],ns);decode,array=ns['decode'],ns['array']
CP=ROOT/'hoodie-repair02/shape-lane/volume-lane/armhole-construction/armhole-chart-outward.npz';MP=CP.with_name('armhole-chart-outward-mapping.npz');NP=np.load(CP);MPN=np.load(MP);AP=Q/'C19-source.glb';BP=ROOT/'hoodie-repair03/construction01/armhole-chart-outward.glb';a,ab,ah=decode(AP);b,bb,bh=decode(BP);pa=[p for m in a['meshes']for p in m['primitives']];pb=[p for m in b['meshes']for p in m['primitives']];rows=[];fail=[];morph=[]
for i,(p0,p1)in enumerate(zip(pa,pb)):
 old=NP[f'oldVertex{i}'];valid=old>=0;targets=[];checks={};
 for key,sem in [('p','POSITION'),('n','NORMAL'),('uv','TEXCOORD_0')]:checks[f'candidate_{sem}_float32_exact']=bool(np.array_equal(array(b,bb,p1['attributes'][sem]),NP[f'{key}{i}'].astype('f4')))
 idx=array(b,bb,p1['attributes']['JOINTS_0']).astype(int);weights=array(b,bb,p1['attributes']['WEIGHTS_0']);W=np.zeros_like(NP[f'W{i}']);np.add.at(W,(np.arange(len(W))[:,None],idx),weights);checks['candidate_W_within_float32']=bool(abs(W-NP[f'W{i}']).max()<1e-7);checks['candidate_triangles_exact']=bool(np.array_equal(array(b,bb,p1['indices']).reshape(-1,3),NP[f'tr{i}']));checks['only_original_two_targets']=len(p1.get('targets',[]))==len(p0.get('targets',[])) and len(p0.get('targets',[]))in[0,2]
 for sem,ac0 in p0['attributes'].items():
  ac1=p1['attributes'][sem];checks[f'{sem}_normalization_flag_exact']=a['accessors'][ac0].get('normalized',False)==b['accessors'][ac1].get('normalized',False)
  if sem.startswith('COLOR'):
   x=array(a,ab,ac0);y=array(b,bb,ac1);checks[f'{sem}_all_original_mapped_rows_exact']=bool(np.array_equal(y[valid],x[old[valid]]))
 for ti,(t0,t1)in enumerate(zip(p0.get('targets',[]),p1.get('targets',[]))):
  for sem,ac0 in t0.items():
   x=array(a,ab,ac0);y=array(b,bb,t1[sem]);expected=np.zeros_like(y);expected[valid]=x[old[valid]];ok=np.array_equal(y,expected);checks[f'morph{ti}_{sem}_source_clones_exact_new_fabric_zero']=bool(ok)
   if sem=='POSITION':targets.append(y)
 morph.append(targets);offsets=MPN[f'oldToNewOffsets{i}'];indices=MPN[f'oldToNewIndices{i}'];n=a['accessors'][p0['attributes']['POSITION']]['count'];checks['old_to_new_CSR_complete']=len(offsets)==n+1 and offsets[0]==0 and offsets[-1]==len(indices) and np.all(np.diff(offsets)>=0) and np.array_equal(old[indices],np.repeat(np.arange(n),np.diff(offsets))) and np.array_equal(np.sort(indices),np.flatnonzero(valid));parents=MPN[f'sourceFaceParents{i}'];checks['all_face_parents_in_source_range']=bool(((parents>=-1)&(parents<len(array(a,ab,p0['indices']))//3)).all());checks['added_fabric_mask_exact']=bool(np.array_equal(MPN[f'addedFabricVertex{i}'],~valid));checks['attribute_donors_in_range']=bool(((MPN[f'attributeDonor{i}']>=0)&(MPN[f'attributeDonor{i}']<n)).all());rows.append({'primitive':i,'vertices':len(old),'checks':checks,'weight_float32_max_error':float(abs(W-NP[f'W{i}']).max())});fail.extend(f'p{i}:{k}'for k,v in checks.items()if not v)
static={'skin_JSON_exact':a['skins']==b['skins'],'node_JSON_exact':a['nodes']==b['nodes'],'materials_JSON_exact':a['materials']==b['materials'],'19_inverse_binds_exact':bool(np.array_equal(array(a,ab,a['skins'][0]['inverseBindMatrices']),array(b,bb,b['skins'][0]['inverseBindMatrices']))),'no_animations_in_render_only_export':'animations'not in b,'all_image_bytes_exact':True,'retop28_29_has_both_source_parents':bool(np.array_equal(MPN['sourceFaceParents2'][[28,29]],[[28,29],[28,29]]))}
for ai,bi in zip(a['images'],b['images']):
 av=a['bufferViews'][ai['bufferView']];bv=b['bufferViews'][bi['bufferView']];static['all_image_bytes_exact']&=ab[av.get('byteOffset',0):av.get('byteOffset',0)+av['byteLength']]==bb[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
fail.extend(k for k,v in static.items()if not v)
states=[('rest_open',np.tile(np.eye(4),(19,1,1)),[0,0]),('rest_closed',np.tile(np.eye(4),(19,1,1)),[1,1])]
for name,path in [('game304_closed',Q/'screenshot01/physical-v5-actual-sample304.npz'),('T_half_closed',ROOT/'hoodie-repair02/poses/v5-raise-0.5.npz'),('T_full_closed',ROOT/'hoodie-repair02/poses/v5-raise-1.npz')]:states.append((name,np.load(path)['matrices'],[1,1]))
refs=[]
for label,D,mw in states:
 expected=[]
 for i in range(5):
  P=NP[f'p{i}'].copy()
  for t,w in zip(morph[i],mw):P+=t*w
  H=np.c_[P,np.ones(len(P))];M=np.einsum('nb,bjk->njk',NP[f'W{i}'],D);posed=np.einsum('nij,nj->ni',M,H)[:,:3];f=OUT/f'construction-{label}-p{i}.f64';posed.astype('<f8').tofile(f);expected.append({'primitive':i,'path':str(f)})
 refs.append({'label':label,'D':D.tolist(),'morph_weights':mw,'expected':expected})
manifest={'path':str(BP),'sha256':bh,'tolerance_m':.00002,'states':refs};(OUT/'construction-stock-matrix-manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'construction-export-static.json').write_text(json.dumps({'source_SHA256':ah,'export_SHA256':bh,'geometry_NPZ_SHA256':hashlib.sha256(CP.read_bytes()).hexdigest(),'mapping_NPZ_SHA256':hashlib.sha256(MP.read_bytes()).hexdigest(),'primitive_rows':rows,'static':static,'failures':fail,'limits':['Render-only export with no animation clip. Stock matrix skinning compared on five explicit states, not runtime animation/controller fixture.','New fabric COLOR values declared original-primitive medians; source aliases retain original values/normalization.','Preserved19bindbasis does not establish anatomically good motion, cloth volume or support.']},indent=2));print('export',bh,'failures',fail)
