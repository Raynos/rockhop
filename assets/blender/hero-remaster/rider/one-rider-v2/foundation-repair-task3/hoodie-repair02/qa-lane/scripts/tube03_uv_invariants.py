from pathlib import Path
import json, hashlib
import numpy as np
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q = ROOT / 'hoodie-repair02/qa-lane'
OUT = Q / 'uv-lower01'
HERE = ROOT / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
AP = HERE / 'source-sleeve-tube-rest02.npz'
BP = HERE / 'source-sleeve-tube-rest03-uv.npz'
loaded = np.load(AP)
a = {k: loaded[k] for k in loaded.files}
loaded = np.load(BP)
b = {k: loaded[k] for k in loaded.files}
loaded = np.load(ROOT / 'hoodie-repair02/v7-bind.npz')
source = {k: loaded[k] for k in loaded.files}
map0 = np.arange(len(b['p0']))
endpoints = []
for side in ['L', 'R']:
    old = b[f'tubeEndpointRetainedVertices{side}']
    new = b[f'tubeEndpointOwnedUVVertices{side}']
    map0[new] = old
    checks = {key: bool(np.array_equal(b[f'{key}0'][new], a[f'{key}0'][old])) for key in ['p', 'W', 'n', 'physicalWeld', 'physicalGarment', 'sourceVertexParents', 'sourceVertexBarycentric', 'sourceUniqueVertex', 'oldVertex']}
    checks['tube_endpoint_last_row_uses_owned_UV_clones'] = bool(np.array_equal(b[f'tubeRows{side}'][-1], new))
    checks['original_retained_clip_UV_unchanged'] = bool(np.array_equal(b['uv0'][old], a['uv0'][old]))
    checks['all_endpoint_UV_clones_have_distinct_UV'] = bool((abs(b['uv0'][new] - a['uv0'][old]).max(1) > 1e-12).all())
    endpoints.append({'side': side, 'clone_count': len(new), 'checks': checks, 'retained_endpoint_vertices': old.tolist(), 'new_UV_endpoint_vertices': new.tolist()})
rows = []
for i in range(5):
    n = len(a[f'p{i}'])
    mapping = map0 if i == 0 else np.arange(len(b[f'p{i}']))
    checks = {}
    for key in ['p', 'W', 'n', 'uv', 'physicalWeld', 'physicalGarment', 'sourceUniqueVertex', 'oldVertex', 'sourceVertexParents', 'sourceVertexBarycentric']:
        checks[f'old_prefix_{key}_exact'] = bool(np.array_equal(b[f'{key}{i}'][:n], a[f'{key}{i}']))
    checks['mapped_triangle_indices_exact'] = bool(np.array_equal(mapping[b[f'tr{i}']], a[f'tr{i}']))
    for key in ['p', 'W', 'n', 'physicalWeld', 'physicalGarment']:
        checks[f'all_used_face_corner_{key}_exact'] = bool(np.array_equal(b[f'{key}{i}'][b[f'tr{i}']], a[f'{key}{i}'][a[f'tr{i}']]))
    for key in ['sourceFaceAncestry', 'faceKind', 'restDoubleArea']:
        checks[f'face_{key}_exact'] = bool(np.array_equal(b[f'{key}{i}'], a[f'{key}{i}']))
    if i == 0:
        kinds = a['faceKind0']
        retained = ~np.char.startswith(kinds.astype(str), 'new-tube')
        checks['all_retained_source_body_face_corner_UV_exact'] = bool(np.array_equal(b['uv0'][b['tr0'][retained]], a['uv0'][a['tr0'][retained]]))
    rows.append({'primitive': i, 'checks': checks})
# Verify supplied independent cancellation witnesses against exact source and final snapshot.
supp_path = HERE / 'opposite-face-cancellation-witness.json'
supp = json.loads(supp_path.read_text())
cancellations = []
for pair in supp['pairs']:
    fa, fb = pair['faces']
    oa, ob = np.array(fa['physicalWeldOrder']), np.array(fb['physicalWeldOrder'])
    ca, cb = np.array(fa['restPositions']), np.array(fb['restPositions'])
    source_face = fa if fa['sourceFaceAncestry'] >= 0 else fb
    sp, sf = source_face['primitive'], source_face['sourceFaceAncestry']
    coords = {int(w): p for w, p in zip(oa, ca)}
    actual_coords = {int(w): p for w, p in zip(ob, cb)}
    same_coords = all(np.array_equal(coords[k], actual_coords[k]) for k in coords)
    na = np.cross(ca[1]-ca[0], ca[2]-ca[0])
    nb = np.cross(cb[1]-cb[0], cb[2]-cb[0])
    checks = {'opposite_oriented_physical_weld_order': any(np.array_equal(ob, np.roll(oa[::-1], j)) for j in range(3)), 'same_three_coordinates_by_physical_weld_exact': same_coords, 'source_vertex_triangle_exact_to_frozen_input': np.array_equal(source_face['vertexIDs'], source[f'tr{sp}'][sf]), 'source_position_triangle_exact_to_frozen_input': np.array_equal(source_face['restPositions'], source[f'p{sp}'][source[f'tr{sp}'][sf]]), 'source_face_absent_in_final_ancestry': not (b[f'sourceFaceAncestry{sp}'] == sf).any()}
    for face in [fa, fb]:
        pi, ids = face['primitive'], np.array(face['vertexIDs'])
        checks[f"p{pi}_face{face['preCancelFaceIndex']}_coordinates_match_stored_rows"] = bool(np.array_equal(b[f'p{pi}'][ids], face['restPositions']))
        checks[f"p{pi}_face{face['preCancelFaceIndex']}_physical_order_matches_stored_rows"] = bool(np.array_equal(b[f'physicalWeld{pi}'][ids], face['physicalWeldOrder']))
    present = 0
    for i in [0, 2]:
        welded = b[f'physicalWeld{i}'][b[f'tr{i}']]
        present += int((np.sort(welded, axis=1) == np.sort(oa)[None]).all(1).sum())
    checks['both_coincident_orientations_absent_final_triangles'] = present == 0
    cancellations.append({'source_primitive_face': [sp, sf], 'checks': {k: bool(v) for k, v in checks.items()}, 'geometric_normal_dot': float(np.dot(na, nb) / (np.linalg.norm(na)*np.linalg.norm(nb)))})
all_checks = [v for r in rows for v in r['checks'].values()] + [v for r in endpoints for v in r['checks'].values()] + [v for r in cancellations for v in r['checks'].values()]
result = {'parent_sha256': hashlib.sha256(AP.read_bytes()).hexdigest(), 'candidate_sha256': hashlib.sha256(BP.read_bytes()).hexdigest(), 'appended_endpoint_clone_count': len(b['p0'])-len(a['p0']), 'rows': rows, 'endpoint_clones': endpoints, 'opposite_cancellation_supplement_sha256': hashlib.sha256(supp_path.read_bytes()).hexdigest(), 'opposite_cancellation_checks': cancellations, 'status': 'UV_ONLY_GEOMETRY_WEIGHT_NORMAL_TOPOLOGY_INVARIANTS_PASS' if all(all_checks) else 'FAIL', 'limits': ['Exact face-corner invariants carry forward parent dense and float32 literal rest tests; no repeated unchanged geometry job.', 'UV clone normal values preserve parent geometric normals and its reported clipped-source normal changes; this is not original source-normal preservation.', 'The845 five-influence cap rows remain incompatible with stock four-influence runtime. No shader or pose acceptance.', 'Images and UV appearance still need root matched rendering; source prefix identity does not mean altered standing silhouette is accepted.']}
(OUT / 'sleeve-tube03-UV-invariants.json').write_text(json.dumps(result, indent=2))
print(result['status'], 'clones', result['appended_endpoint_clone_count'], 'failedchecks', [(r['primitive'],k) for r in rows for k,v in r['checks'].items() if not v], 'cancel', cancellations)
