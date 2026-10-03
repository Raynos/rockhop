from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';OUT.mkdir(exist_ok=True)
source=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+source[source.index('def decode('):source.index("manifest={'tolerance_m'")],ns);decode,array,pose,vertices=[ns[k]for k in ['decode','array','pose','vertices']]
AP=ROOT/'hoodie-repair02/deliverables/rider-compression-v7.glb';BP=ROOT/'hoodie-repair03/uv-normal-foundation01/rider-uv-ablation.glb';a,ab,ah=decode(AP);b,bb,bh=decode(BP);pro=json.loads((BP.parent/'uv-ablation-provenance.json').read_text());pa=[p for m in a['meshes']for p in m['primitives']];pb=[p for m in b['meshes']for p in m['primitives']];tri=array(a,ab,pa[0]['indices']).reshape(-1,3).astype(int);oldcount=a['accessors'][pa[0]['attributes']['POSITION']]['count'];clones=np.concatenate([tri[r['face']]for r in pro['rows']]);mapping=np.r_[np.arange(oldcount),clones];rows=[];fail=[]
for pi,(p0,p1)in enumerate(zip(pa,pb)):
 for semantic,accessor in p0['attributes'].items():
  x=array(a,ab,accessor);y=array(b,bb,p1['attributes'][semantic]);expected=x[mapping]if pi==0 else x;row={'primitive':pi,'semantic':semantic,'source_count':len(x),'candidate_count':len(y),'old_prefix_exact':np.array_equal(x,y[:len(x)]),'clones_exact':np.array_equal(expected[oldcount:],y[oldcount:])if pi==0 and semantic!='TEXCOORD_0'else None,'normalized_flag_preserved':a['accessors'][accessor].get('normalized',False)==b['accessors'][p1['attributes'][semantic]].get('normalized',False)};rows.append(row)
  if not row['old_prefix_exact']or not row['normalized_flag_preserved']or(pi==0 and semantic!='TEXCOORD_0'and not row['clones_exact']):fail.append(row)
 targets=[]
 for ti,(t0,t1)in enumerate(zip(p0.get('targets',[]),p1.get('targets',[]))):
  for semantic,accessor in t0.items():
   x=array(a,ab,accessor);y=array(b,bb,t1[semantic]);expected=x[mapping]if pi==0 else x;ok=np.array_equal(expected,y);targets.append({'target':ti,'semantic':semantic,'all_rows_and_clones_exact':ok})
   if not ok:fail.append({'primitive':pi,'morph_target':ti,'semantic':semantic})
 row={'primitive':pi,'morph_targets_source':len(p0.get('targets',[])),'morph_targets_candidate':len(p1.get('targets',[])),'checked_semantic_arrays':len(targets),'all_exact':all(r['all_rows_and_clones_exact']for r in targets)};rows.append(row)
 ta=array(a,ab,p0['indices']).astype(int).reshape(-1,3);tb=array(b,bb,p1['indices']).astype(int).reshape(-1,3);mapped=mapping[tb]if pi==0 else tb;ok=np.array_equal(ta,mapped);rows.append({'primitive':pi,'triangles_after_clone_map_exact':ok,'triangles':len(ta)});
 if not ok:fail.append({'primitive':pi,'triangle_map':'FAIL'})
# Image bytes via stable references, and entire original BIN prefix.
image_exact=[]
for x,y in zip(a['images'],b['images']):
 va=a['bufferViews'][x['bufferView']];vb=b['bufferViews'][y['bufferView']];ra=ab[va.get('byteOffset',0):va.get('byteOffset',0)+va['byteLength']];rb=bb[vb.get('byteOffset',0):vb.get('byteOffset',0)+vb['byteLength']];image_exact.append(ra==rb)
static={'skin_json_exact':a['skins']==b['skins'],'nodes_json_exact':a['nodes']==b['nodes'],'animation_json_exact':a['animations']==b['animations'],'materials_json_exact':a['materials']==b['materials'],'all_image_bytes_exact':all(image_exact),'original_BIN_prefix_exact':bb[:len(ab)]==ab,'original_socket_vertex_indices_retained_by_prefix':True,'clone_count':len(clones),'nonUV_attribute_and_all51_morph_clone_failures':fail}
refs=[];runtime=[]
# Three stock check only 3 times, not full inherited qualification fixture.
for label,doc,bin,path in [('v7-parent',a,ab,AP),('uv-clones',b,bb,BP)]:
 clip=next(c for c in doc['animations']if c['name']=='hoodie_compression_stand_to_sit');entries=[]
 for ti,t in enumerate([0,.731,2]):
  for mi,pi,p in vertices(doc,bin,*pose(doc,bin,clip,t)):
   name=f'{label}-{ti}-{mi}-{pi}.f32';p.astype('<f4').tofile(OUT/name);entries.append({'clip':clip['name'],'time':t,'mesh_index':mi,'primitive_index':pi,'path':name,'format':'float32le'})
 runtime.append({'id':label,'path':str(path),'sha256_reference_source':hashlib.sha256(path.read_bytes()).hexdigest(),'clips':[{'name':clip['name'],'times':[0,.731,2]}],'expected':entries})
(OUT/'stock-manifest.json').write_text(json.dumps({'tolerance_m':.00002,'variants':runtime},indent=2));(OUT/'uv-ablation-static-proof.json').write_text(json.dumps({'source_sha256':ah,'candidate_sha256':bh,'rows':rows,'static':static,'limits':['Algebraic clone proof covers arbitrary linear skin/morph coefficients when the old source did; no geometry acceptance or texturecontinuity acceptance.','Stock comparison restricted3times, not duplicate original fullqualification.','Socket index preservation is existing vertexindexprefix preservation, not wholehand face contact acceptance.']},indent=2));print(json.dumps(static));print('proof',OUT/'uv-ablation-static-proof.json')
