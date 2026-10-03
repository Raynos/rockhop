from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
# Reuse only independently written generic predicate/audit; source and candidate snapshots are read-only.
ns={}; code=(Q/'scripts/tube06_rest_qualify.py').read_text();exec(code[:code.index('\nsource_weld =')],ns);audit=ns['audit']
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
ap=HERE/'source-sleeve-tube-rest07-uvchart.npz';bp=HERE/'source-sleeve-tube-rest10-rmf.npz';a,d=read(ap),read(bp)
checks={}; contracts=[]
allowed=np.unique(np.r_[d['tubeRowsL'][1:-1].ravel(),d['tubeRowsR'][1:-1].ravel(),d['tubeUVRowsL'][1:-1,-1],d['tubeUVRowsR'][1:-1,-1]])
for i in range(5):
 for key in ['tr','W','uv','physicalWeld','physicalGarment','sourceVertexParents','sourceVertexBarycentric','sourceUniqueVertex','oldVertex','sourceFaceAncestry','faceKind']:
  checks[f'p{i}_{key}_exact07']=np.array_equal(d[key+str(i)],a[key+str(i)])
 old_count=len(ns['b']['p'+str(i)])
 for key,source in [('p',ns['b']['p'+str(i)]),('W',ns['b']['W'+str(i)]),('n',ns['shape']['n'+str(i)])]:checks[f'p{i}_source_{key}_prefix_exact']=np.array_equal(d[key+str(i)][:old_count],source)
 for key in ['p','n']:
  changed=np.flatnonzero(np.any(d[key+str(i)]!=a[key+str(i)],axis=1));checks[f'p{i}_{key}_changed_only_tube_interior']=bool(np.isin(changed,allowed).all()) if i==0 else len(changed)==0
 actual=np.linalg.norm(np.cross(d['p'+str(i)][d['tr'+str(i)][:,1]]-d['p'+str(i)][d['tr'+str(i)][:,0]],d['p'+str(i)][d['tr'+str(i)][:,2]]-d['p'+str(i)][d['tr'+str(i)][:,0]]),axis=1)
 checks[f'p{i}_rest_area_actual']=np.allclose(actual,d['restDoubleArea'+str(i)],rtol=1e-10,atol=1e-14)
for side in ['L','R']:
 rows=d['tubeRows'+side]; grid=d['tubeUVRows'+side];root=d['bodyOpeningVertices'+side]
 checks[side+'_root_cap_tube_physical_ids_exact']=np.array_equal(d['physicalWeld0'][rows[0]],d['physicalWeld0'][root])
 checks[side+'_root_cap_tube_P_exact']=np.array_equal(d['p0'][rows[0]],d['p0'][root])
 checks[side+'_root_and_end_P_exact07']=np.array_equal(d['p0'][rows[[0,-1]]],a['p0'][a['tubeRows'+side][[0,-1]]])
 checks[side+'_longitudinal_seam_P_exact']=np.array_equal(d['p0'][grid[:,0]],d['p0'][grid[:,-1]])
 checks[side+'_longitudinal_seam_W_exact']=np.array_equal(d['W0'][grid[:,0]],d['W0'][grid[:,-1]])
 checks[side+'_tubeRestRows_actual']=np.array_equal(d['tubeRestRows'+side],d['p0'][rows])
 contracts.append({'side':side,'max_interior_translation_m':float(np.linalg.norm(d['p0'][rows]-a['p0'][a['tubeRows'+side]],axis=2).max())})
pos=[d[f'p{i}'] for i in range(5)];tri=[d[f'tr{i}'] for i in range(5)];weld=[d[f'physicalWeld{i}'] for i in range(5)];ancestry=[d[f'sourceFaceAncestry{i}'] for i in range(5)];kind=[d[f'faceKind{i}'] for i in range(5)]
dense,boundary=audit('tube10',pos,tri,weld,ancestry,kind)
f32,boundary32=audit('tube10-float32', [p.astype('f4').astype(float) for p in pos],tri,weld,ancestry,kind)
# Source boundary set already independently checked against original V7 in06; unchanged exact physical topology plus changed-only interior rows.
checks['boundary364_preserved']=dense['boundary_edges']==364
checks['dense_rest_no_strict_crossings']=dense['strict_zero_shared_weld_crossings']==dense['strict_one_shared_weld_crossings']==0
checks['float32_rest_no_strict_crossings']=f32['strict_zero_shared_weld_crossings']==f32['strict_one_shared_weld_crossings']==0
checks['dense_manifold_winding_nondegenerate']=dense['nonmanifold_edges']==dense['incoherent_two_face_winding_edges']==dense['degenerate_weld_triangles']==0
checks['float32_manifold_winding_nondegenerate']=f32['nonmanifold_edges']==f32['incoherent_two_face_winding_edges']==f32['degenerate_weld_triangles']==0
aliases=np.r_[weld[0],weld[2]];W=np.r_[d['W0'],d['W2']];_,group=np.unique(aliases,return_inverse=True);lo=np.full((group.max()+1,19),np.inf);hi=np.full_like(lo,-np.inf);np.minimum.at(lo,group,W);np.maximum.at(hi,group,W);spread=float(abs(hi-lo).max())
checks['physical_weld_W_agrees']=spread<1e-12;checks['physical_weld_P_agrees']=dense['same_weld_position_bbox_max_m']<1e-12
bad=sum(int(((d['W'+str(i)]>1e-8).sum(1)>4).sum()) for i in range(5))
r={'candidate_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'parent_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'status':'BOUNDED_REST_AND_SOURCE_CONTRACT_PASS' if all(checks.values()) else 'FAIL','checks':{k:bool(v) for k,v in checks.items()},'candidate':dense,'float32_POSITION_candidate':f32,'tube_interior_displacements':contracts,'physical_weld_weight_spread_max':spread,'dense_five_influence_rows':bad,'limits':['Strict transverse all-cloth0+2 pairs only; tangent/coplanar contact/thickness unclassified.','Original prefix/source/clipped seams protected; standing silhouette and shaded appearance still require images.','Donor ray ancestry refers06 shape before declared RMF curve remap; no present source-ray-envelope bound inferred.','Dense W still contains five-influence new caps. Root declared carrier rule and final stock export require separate proof.','No actual304/interpolation/pose/support/saddle/volume acceptance.']}
(Q/'uv-lower01/sleeve-tube10-independent-rest.json').write_text(json.dumps(r,indent=2));print(r['status'], 'failed', [k for k,v in checks.items() if not v], 'five-influence',bad,flush=True)
