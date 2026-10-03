from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
ap=HERE/'source-sleeve-tube-rest19-normal.npz';bp=HERE/'source-sleeve-tube-rest20-endpointuv.npz';a,b=read(ap),read(bp);mapping=np.arange(len(b['p0']));checks={};clones=[]
for side in ['L','R']:
 old=b['tubeEndpointRetainedVertices'+side];new=b['tubeEndpointOwnedUVVertices'+side];mapping[new]=old;checks[side+'_endpoint_retained_mapping_matches19lastrow']=np.array_equal(old,a['tubeRows'+side][-1]);checks[side+'_tube_endpoint_uses_UVclone']=np.array_equal(new,b['tubeRows'+side][-1]);checks[side+'_original_clipUV_exact']=np.array_equal(b['uv0'][old],a['uv0'][old]);clones.append({'side':side,'count':len(new),'retained':old.tolist(),'UV_clones':new.tolist()})
for i in range(5):
 m=mapping if i==0 else np.arange(len(b['p'+str(i)]));t=b['tr'+str(i)];at=a['tr'+str(i)]
 checks[f'p{i}_mapped_indices_exact']=np.array_equal(m[t],at)
 for key in ['p','W','n','physicalWeld','physicalGarment','sourceVertexParents','sourceVertexBarycentric','sourceUniqueVertex','oldVertex']:
  checks[f'p{i}_{key}_all_rows_mapped_exact']=np.array_equal(b[key+str(i)],a[key+str(i)][m]);checks[f'p{i}_{key}_all_used_facecorners_exact']=np.array_equal(b[key+str(i)][t],a[key+str(i)][at])
 for key in ['sourceFaceAncestry','faceKind','restDoubleArea']:checks[f'p{i}_{key}_exact']=np.array_equal(b[key+str(i)],a[key+str(i)])
 retained=np.array([not str(x).startswith(('body-cap','new-tube')) for x in b['faceKind'+str(i)]]);checks[f'p{i}_retained_source_facecorner_UV_exact']=np.array_equal(b['uv'+str(i)][t[retained]],a['uv'+str(i)][at[retained]])
r={'status':'ENDPOINT_UV_CLONE_INVARIANTS_PASS' if all(checks.values()) else 'FAIL','parent19_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'endpoint20_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'added_endpoint_UV_vertices':len(b['p0'])-len(a['p0']),'checks':{k:bool(v) for k,v in checks.items()},'clones':clones,'limits':'Clone/used-corner invariants only; standing/material/movement/runtime acceptance separate.'};(Q/'uv-lower01/sleeve-tube20-endpoint-UV-invariants.json').write_text(json.dumps(r,indent=2));print(r['status'],'clones',r['added_endpoint_UV_vertices'],'failed',[k for k,v in checks.items() if not v])
