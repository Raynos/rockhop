from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';src=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+src[src.index('def decode('):src.index("manifest={'tolerance_m'")],ns);decode,array,pose,vertices=[ns[k]for k in ['decode','array','pose','vertices']]
AP=Q/'C19-source.glb';BP=ROOT/'hoodie-repair03/construction01/armhole-chart-outward.glb';CP=ROOT/'hoodie-repair02/shape-lane/volume-lane/armhole-construction/armhole-chart-outward.npz';C=np.load(CP);a,ab,ah=decode(AP);b,bb,bh=decode(BP);pa=[p for m in a['meshes']for p in m['primitives']];pb=[p for m in b['meshes']for p in m['primitives']];rows=[];fail=[]
for i,(x,y)in enumerate(zip(pa,pb)):
 mapping=C[f'oldVertex{i}'];mapped=mapping>=0;n=len(mapping);checks={}
 for semantic,key in [('POSITION','p'),('NORMAL','n'),('TEXCOORD_0','uv')]:checks[semantic+'_exact_quantized_candidate']=bool(np.array_equal(array(b,bb,y['attributes'][semantic]),C[f'{key}{i}'].astype('f4').astype(float)))
 checks['triangle_indices_exact_candidate']=bool(np.array_equal(array(b,bb,y['indices']).astype(int).reshape(-1,3),C[f'tr{i}']))
 joints=array(b,bb,y['attributes']['JOINTS_0']).astype(int);weights=array(b,bb,y['attributes']['WEIGHTS_0']);dense=np.zeros((n,19));np.add.at(dense,(np.arange(n)[:,None],joints),weights);checks['weight_field_within_f32_roundoff']=bool(abs(dense-C[f'W{i}']).max()<1e-7);flagrows=[]
 for semantic,oldaccess in x['attributes'].items():
  newaccess=y['attributes'][semantic];flagrows.append({'semantic':semantic,'normalized_flag_preserved':a['accessors'][oldaccess].get('normalized',False)==b['accessors'][newaccess].get('normalized',False)})
  if semantic.startswith('COLOR_'):checks[semantic+'_all_mapped_rows_exact']=bool(np.array_equal(array(b,bb,newaccess)[mapped],array(a,ab,oldaccess)[mapping[mapped]]))
 checks['all_attribute_normalization_flags_preserved']=all(r['normalized_flag_preserved']for r in flagrows);targets=[]
 for ti,(old,new)in enumerate(zip(x.get('targets',[]),y.get('targets',[]))):
  for semantic,oa in old.items():
   oa=array(a,ab,oa);got=array(b,bb,new[semantic]);expected=np.zeros((n,oa.shape[1]));expected[mapped]=oa[mapping[mapped]];ok=np.array_equal(got,expected);targets.append({'target':ti,'semantic':semantic,'mapped_source_rows_and_new_fabric_zeros_exact':bool(ok)})
 checks['original_morph_count_exact']=len(x.get('targets',[]))==len(y.get('targets',[]));checks['all_morph_clone_rows_exact']=all(r['mapped_source_rows_and_new_fabric_zeros_exact']for r in targets);row={'primitive':i,'vertices':n,'checks':checks,'normalization_flags':flagrows,'targets':targets,'weight_field_max_error':float(abs(dense-C[f'W{i}']).max())};rows.append(row)
 fail.extend(f'p{i}:{k}'for k,v in checks.items()if not v)
def imagebytes(doc,blob):
 return [blob[doc['bufferViews'][im['bufferView']].get('byteOffset',0):doc['bufferViews'][im['bufferView']].get('byteOffset',0)+doc['bufferViews'][im['bufferView']]['byteLength']]for im in doc['images']]
sa,sb=a['skins'][0],b['skins'][0];static={'19_joint_count':len(sb['joints'])==19,'joint_slots_and_skeleton_json_exact':sa==sb,'inverse_bind_array_exact':np.array_equal(array(a,ab,sa['inverseBindMatrices']),array(b,bb,sb['inverseBindMatrices'])),'nodes_json_exact':a['nodes']==b['nodes'],'material_json_exact':a['materials']==b['materials'],'all_embedded_image_bytes_exact':imagebytes(a,ab)==imagebytes(b,bb),'original_target_counts':[len(p.get('targets',[]))for p in pb],'render_only_no_authored_animation':not b.get('animations'),'old_index_prefix_preserved':all(np.array_equal(C[f'oldVertex{i}'][:len(array(a,ab,pa[i]['attributes']['POSITION']))],np.arange(len(array(a,ab,pa[i]['attributes']['POSITION']))))for i in range(5))};fail.extend(k for k,v in static.items()if isinstance(v,bool)and not v)
# Small actual stock loader/morph fixture. Manual grip coefficients, no fabricated clip.
variants=[]
for label,doc,blob,p in [('source-C19',a,ab,AP),('armhole',b,bb,BP)]:
 refs=[]
 for ci,coeff in enumerate([[0,0],[1,0],[1,1]]):
  nodes,world=pose(doc,blob,{'channels':[]},0)
  for node in nodes:
   if 'mesh'in node and doc['meshes'][node['mesh']].get('weights')is not None:node['weights']=coeff
  for mi,pi,vs in vertices(doc,blob,nodes,world):
   name=f'armhole-stock-{label}-{ci}-{mi}-{pi}.f32';vs.astype('<f4').tofile(OUT/name);refs.append({'case':ci,'mesh_index':mi,'primitive_index':pi,'path':name})
 variants.append({'id':label,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'cases':[[0,0],[1,0],[1,1]],'references':refs})
(OUT/'armhole-stock-manifest.json').write_text(json.dumps({'variants':variants,'tolerance_m':2e-5},indent=2));(OUT/'armhole-export-preservation.json').write_text(json.dumps({'source_sha256':ah,'candidate_sha256':bh,'NPZ_sha256':hashlib.sha256(CP.read_bytes()).hexdigest(),'rows':rows,'static':static,'failures':fail,'limits':['Exact render-only export preservation and bounded stock rest/manual grip cases; no motion, armhole appearance or character acceptance.','No inherited49 morph atlas copied. Original two grip targets are algebraically extended from exact source vertex ancestry; new fabric has zero grip deltas.','Socket preservation is original vertex-prefix index preservation, not contact force or whole hand surface acceptance.']},indent=2));print('STATIC',static,'FAILURES',fail)
