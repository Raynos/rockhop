from pathlib import Path
import json, hashlib
import numpy as np
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q = ROOT / 'hoodie-repair02/qa-lane'
OUT = Q / 'uv-lower01'
HERE = ROOT / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
def load(path):
    archive = np.load(path)
    return {k: archive[k] for k in archive.files}
ap = HERE / 'source-sleeve-tube-rest04-normal.npz'
bp = HERE / 'source-sleeve-tube-rest06-envelope.npz'
a, b = load(ap), load(bp)
source = load(ROOT / 'hoodie-repair02/v7-bind.npz')
sourceq = np.r_[source['p0'][source['tr0']], source['p2'][source['tr2']]]
cut = load(HERE.parent / 'armhole-construction/source-armhole-cut.npz')
checks = {key+'_exact_parent': bool(np.array_equal(a[key], b[key])) for key in a if key not in ['p0','n0','restDoubleArea0','tubeRestRowsL','tubeRestRowsR']}
allowed_position = set()
allowed_normal = set()
ray_rows = []
for side in ['L','R']:
    tube = b[f'tubeRows{side}']
    controls = b[f'curveControlRest{side}']
    faces = b[f'tubeRaySourceFace{side}']
    radii = b[f'tubeRayHitRadius{side}']
    witnesses = []
    position_error = 0.
    source_error = 0.
    max_move = 0.
    for row, vertices in enumerate(tube[1:-1],1):
        fraction = row/(len(tube)-1)
        centre = (1-fraction)**3*controls[0] + 3*(1-fraction)**2*fraction*controls[1] + 3*(1-fraction)*fraction*fraction*controls[2] + fraction**3*controls[3]
        radial = a['p0'][vertices]-centre
        old_radius = np.linalg.norm(radial,axis=1)
        directions = radial/old_radius[:,None]
        factor = 0. if row == 1 else .5 if row == 2 else 1.
        if factor:
            allowed_position.update(vertices.tolist())
            allowed_normal.update(vertices.tolist())
        for column, vertex in enumerate(vertices):
            face = int(faces[row-1,column])
            hit = float(radii[row-1,column])
            predicted = a['p0'][vertex].copy()
            valid = True
            bary = None
            plane_error = 0.
            if face >= 0:
                point = centre+directions[column]*hit
                triangle = sourceq[face]
                uv = np.linalg.lstsq(np.stack([triangle[1]-triangle[0],triangle[2]-triangle[0]],axis=1),point-triangle[0],rcond=None)[0]
                bary = np.r_[1-uv.sum(),uv]
                plane_error = float(np.linalg.norm(bary@triangle-point))
                normal = np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
                valid = bool(cut[f'sleeveFaces{side}'][face] and bary.min() >= -1e-8 and bary.max() <= 1+1e-8 and .005 < hit < .18 and np.dot(normal,directions[column]) > 0 and plane_error < 1e-12)
                step = np.clip(hit-old_radius[column],-.025,.025) * np.sqrt(np.sin(np.pi*fraction)) * factor
                predicted += directions[column]*step
            else:
                valid = bool(np.isnan(hit))
            error = float(np.linalg.norm(predicted-b['p0'][vertex]))
            move = float(np.linalg.norm(b['p0'][vertex]-a['p0'][vertex]))
            position_error = max(position_error,error)
            source_error = max(source_error,plane_error)
            max_move = max(max_move,move)
            witnesses.append({'tube_row':row,'column':column,'vertex':int(vertex),'source_combined_face':face,'source_primitive_face':[0,face]if 0<=face<len(source['tr0'])else[2,face-len(source['tr0'])]if face>=0 else None,'hit_radius_m':hit if np.isfinite(hit)else None,'source_face_barycentric':bary.tolist()if bary is not None else None,'source_hit_plane_error_m':plane_error,'source_outward_hit_valid':valid,'declared_step_prediction_error_m':error,'move_m':move,'collar_blend':factor})
    ray_rows.append({'side':side,'rays':len(witnesses),'recorded_source_hits':sum(r['source_combined_face']>=0 for r in witnesses),'all_recorded_source_hits_valid':all(r['source_outward_hit_valid']for r in witnesses),'max_hit_plane_error_m':source_error,'max_declared_step_prediction_error_m':position_error,'max_displacement_m':max_move,'all_ray_witnesses':witnesses})
changed_p = set(np.flatnonzero(np.linalg.norm(b['p0']-a['p0'],axis=1)>1e-12).tolist())
changed_n = set(np.flatnonzero(np.linalg.norm(b['n0']-a['n0'],axis=1)>1e-12).tolist())
checks['POSITION_changes_only_declared_interior_rows2to11'] = changed_p.issubset(allowed_position)
checks['NORMAL_changes_only_declared_interior_rows2to11'] = changed_n.issubset(allowed_normal)
checks['all_ray_hits_on_recorded_outward_actual_source_sleeve_faces'] = all(r['all_recorded_source_hits_valid']for r in ray_rows)
checks['all_actual_POSITIONs_match_bounded_ray_and_collar_recipe'] = max(r['max_declared_step_prediction_error_m']for r in ray_rows)<1e-12
checks['all_displacements_below25mm'] = max(r['max_displacement_m']for r in ray_rows)<=.025+1e-12
checks['source_head_glove_other_primitive_all_arrays_exact'] = all(np.array_equal(a[f'{key}{i}'],b[f'{key}{i}'])for i in [1,2,3,4]for key in ['p','W','n','uv','tr','physicalWeld'])
checks['both_endpoints_and_root_collar01_POSITION_NORMAL_exact'] = all(np.array_equal(a[key][a[f'tubeRows{s}'][[0,1,-1]]],b[key][b[f'tubeRows{s}'][[0,1,-1]]])for s in ['L','R']for key in ['p0','n0'])
result={'parent_normal04_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'checks':checks,'changed_POSITION_rows':len(changed_p),'changed_NORMAL_rows':len(changed_n),'ray_rows':ray_rows,'status':'SOURCE_RAY_BOUND_AND_PROTECTED_INTERFACE_CONTRACT_PASS'if all(checks.values())else'FAIL','limits':['Recorded rays are checked on actual selected source sleeve faces. This does not measure all directional silhouette error or prove optimal nearest-hit selection.','Collar rows0/1 held and row2 half displacement are explicit construction choices, not anatomical truth.','Normals on interior rows are recomputed geometric values; source-bary seam normals and original source prefixes remain protected.','Five-influence parent binding still requires separately verified carrier integration/export; no motion or standing visual acceptance.']}
(OUT/'sleeve-tube06-ray-source-contract.json').write_text(json.dumps(result,indent=2))
print(result['status'],'failed',[k for k,v in checks.items()if not v],'Pchanged',len(changed_p),'rays',[(r['side'],r['recorded_source_hits'],r['max_declared_step_prediction_error_m'],r['max_displacement_m'])for r in ray_rows])
