from pathlib import Path
import numpy as np, json, hashlib, sys, io
from PIL import Image
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q=ROOT/'hoodie-repair02/qa-lane'; HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
sys.path.insert(0,str(ROOT/'scripts')); from glb import GLB
ap=HERE/'source-sleeve-tube-rest20-endpointuv.npz'; bp=HERE/'source-sleeve-tube-rest21-uvchart.npz'
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
a,b=read(ap),read(bp); source=GLB(Q/'C19-source.glb'); pr=[p for m in source.j['meshes'] for p in m['primitives']]
checks={}; mapping=np.arange(len(b['p0'])); clones=[]
for side in ['L','R']:
 old=a['tubeRows'+side]; new=b['tubeRows'+side]; grid=b['tubeUVRows'+side]
 mapping[new[0]]=old[0]; mapping[grid[:,-1]]=old[:,0]
 checks[side+'_root_source_map']=np.array_equal(b['tubeUVRootSourceCapVertices'+side],old[0])
 checks[side+'_seam_closed_in_physical_ids']=np.array_equal(b['physicalWeld0'][grid[:,0]],b['physicalWeld0'][grid[:,-1]])
 for label,ids in [('root',new[0]),('seam',grid[:,-1])]:
  clones.append({'side':side,'kind':label,'count':len(ids),'candidate_vertices':ids.tolist(),'parent_vertices':mapping[ids].tolist()})
 checks[side+'_grid_body_matches_rows']=np.array_equal(grid[:,:-1],new)
for i in range(5):
 m=mapping if i==0 else np.arange(len(b['p'+str(i)])); t=b['tr'+str(i)]; at=a['tr'+str(i)]
 checks[f'p{i}_mapped_indices_exact']=np.array_equal(m[t],at)
 for key in ['p','W','n','physicalWeld','physicalGarment','sourceVertexParents','sourceVertexBarycentric','sourceUniqueVertex','oldVertex']:
  checks[f'p{i}_{key}_all_rows_mapped_exact']=np.array_equal(b[key+str(i)],a[key+str(i)][m])
  checks[f'p{i}_{key}_used_corners_exact']=np.array_equal(b[key+str(i)][t],a[key+str(i)][at])
 for key in ['faceKind','sourceFaceAncestry','restDoubleArea']:
  checks[f'p{i}_{key}_exact']=np.array_equal(b[key+str(i)],a[key+str(i)])
 original_uv=source.array(pr[i]['attributes']['TEXCOORD_0']).astype(float)
 checks[f'p{i}_source_UV_prefix_exact']=np.array_equal(b['uv'+str(i)][:len(original_uv)],original_uv)
 if i!=0:checks[f'p{i}_all_UV_exact']=np.array_equal(b['uv'+str(i)],a['uv'+str(i)])
# Original, retained source-clipped face corners keep the parent chart.
retained=np.array([not str(x).startswith(('body-cap','new-tube')) for x in b['faceKind0']])
checks['retained_source_triangle_UV_exact']=np.array_equal(b['uv0'][b['tr0'][retained]],a['uv0'][a['tr0'][retained]])
# Endpoint original clipped UV rows remain exact even where fabric gets a separate chart.
for side in ['L','R']:
 ids=b['tubeEndpointRetainedVertices'+side]
 checks[side+'_retained_clip_UV_exact']=np.array_equal(b['uv0'][ids],a['uv0'][ids])
# Independently test chart orientation and absence of zero-area UV triangles.
charts=[]
for side in ['L','R']:
 for label in ['bodyCapFaceIDs','newTubeFaceIDs']:
  ids=b[label+side]; uv=b['uv0'][b['tr0'][ids]]; edges=uv[:,1:]-uv[:,:1]
  signed=edges[:,0,0]*edges[:,1,1]-edges[:,0,1]*edges[:,1,0]; expected=-1 if label=='bodyCapFaceIDs' and side=='R' else 1
  checks[label+side+'_consistent_nonzero_orientation']=bool((signed*expected>1e-14).all())
  charts.append({'region':label+side,'face_count':len(ids),'minimum_absolute_double_UV_area':float(abs(signed).min()),'positive':int((signed>1e-14).sum()),'negative':int((signed<-1e-14).sum()),'zero_at_1e-14':int((abs(signed)<=1e-14).sum())})
tex=source.j['materials'][pr[0]['material']]['pbrMetallicRoughness']['baseColorTexture']['index']; im=source.j['textures'][tex]['source']; bv=source.j['bufferViews'][source.j['images'][im]['bufferView']]; blob=bytes(source.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]); atlas=np.asarray(Image.open(io.BytesIO(blob)).convert('RGBA'))
ids=np.flatnonzero(~retained); uv=b['uv0'][b['tr0'][ids]]; bary=np.array([[1,0,0],[0,1,0],[0,0,1],[1/3]*3,[.5,.5,0],[.5,0,.5],[0,.5,.5]])
samples=np.einsum('sv,fvu->fsu',bary,uv);xy=np.rint(samples*np.array([atlas.shape[1]-1,atlas.shape[0]-1])).astype(int)
checks['sample_UV_inside_atlas']=bool(((samples>=0)&(samples<=1)).all());xy=np.clip(xy,[0,0],[atlas.shape[1]-1,atlas.shape[0]-1]);rgba=atlas[xy[:,:,1],xy[:,:,0]];rgb=rgba[:,:,:3].astype(float)
gold=(rgb[:,:,0]>110)&(rgb[:,:,1]>70)&(rgb[:,:,2]<rgb[:,:,1]*.75)&(rgb[:,:,0]>rgb[:,:,1]*1.05)&(rgb[:,:,0]<rgb[:,:,1]*2.2)&(rgba[:,:,3]==255)
checks['seven_samples_all_opaque']=bool((rgba[:,:,3]==255).all()); checks['seven_samples_all_gold_by_declared_RGB_test']=bool(gold.all())
r={'status':'UV_CHART_AND_CLONE_INVARIANTS_PASS' if all(checks.values()) else 'FAIL','parent_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'checks':{k:bool(v) for k,v in checks.items()},'added_uv_clone_vertices':len(b['p0'])-len(a['p0']),'clones':clones,'charts':charts,'atlas':{'original_image_bytes_sha256':hashlib.sha256(blob).hexdigest(),'sampled_faces':len(ids),'samples_per_face':7,'opaque_fraction':float((rgba[:,:,3]==255).mean()),'gold_fraction':float(gold.mean())},'carry_forward_geometry':'Exact mapped triangle P/W/N and physical corner IDs carry forward18 geometric shape; independently21 dense+float32 rest literal0+0; no unchanged geometry rerun.','runtime_note':'Dense parent W still has five-influence caps. Apply explicit four-cap carrier rule to all physical clones, then verify stock exported bind/attrs. No top4 truncation or present stock-runtime claim.','limits':['No full chart-overlap proof; finite texel sampling does not certify every fragment or mip/filter output.','UV change does not certify standing appearance, source sleeve silhouette, shader normal parity, animation, collisions in motion, contacts or saddle support.']}
(Q/'uv-lower01/sleeve-tube21-UV-chart-invariants.json').write_text(json.dumps(r,indent=2));print(r['status'],'clones',r['added_uv_clone_vertices'],'failed',[k for k,v in checks.items() if not v]);print(json.dumps(charts,indent=2));print(r['atlas'])
