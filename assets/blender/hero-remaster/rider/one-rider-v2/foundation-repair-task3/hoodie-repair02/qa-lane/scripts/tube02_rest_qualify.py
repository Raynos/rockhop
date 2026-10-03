from pathlib import Path
import sys, json, hashlib
import numpy as np
from scipy.spatial import cKDTree
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q = ROOT / 'hoodie-repair02/qa-lane'
OUT = Q / 'uv-lower01'
sys.path.insert(0, str(ROOT / 'scripts'))
from glb import GLB
predicate = (Q / 'scripts/geometry_gate.py').read_text()
namespace = {'np': np, 'EPS': 1e-9}
exec(predicate[predicate.index('def crossing'):predicate.index('def region_geom')], namespace)
crossing = namespace['crossing']
path = ROOT / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03/source-sleeve-tube-rest02.npz'
loaded = np.load(path)
d = {key: loaded[key] for key in loaded.files}
source_path = ROOT / 'hoodie-repair02/v7-bind.npz'
loaded = np.load(source_path)
b = {key: loaded[key] for key in loaded.files}
loaded = np.load(ROOT / 'hoodie-repair02/v7-shape-input.npz')
shape = {key: loaded[key] for key in loaded.files}
g = GLB(Q / 'C19-source.glb')
primitives = [p for m in g.j['meshes'] for p in m['primitives']]
original = [g.array(p['attributes']['POSITION']).astype(float) for p in primitives]
source_offsets = np.r_[0, np.cumsum([len(p) for p in original])]
_, source_alias = np.unique(np.concatenate(original), axis=0, return_inverse=True)

def audit(label, positions, triangles, weld, ancestry=None, kind=None):
    points = np.concatenate([positions[0], positions[2]])
    tris = np.concatenate([triangles[0], triangles[2] + len(positions[0])])
    aliases = np.r_[weld[0], weld[2]]
    q = points[tris]
    lower, upper = q.min(1), q.max(1)
    centres = q.mean(1)
    radius = np.linalg.norm(q - centres[:, None], axis=2).max(1)
    tree = cKDTree(centres)
    al = aliases[tris]
    hits = []
    candidate_count = 0
    for start in range(0, len(tris), 64):
        nearby = tree.query_ball_point(centres[start:start+64], radius[start:start+64] + radius.max())
        pairs = np.array([(start+i, j) for i, js in enumerate(nearby) for j in js if start+i < j], int).reshape(-1, 2)
        if not len(pairs):
            continue
        pairs = pairs[((lower[pairs[:, 0]] <= upper[pairs[:, 1]]) & (lower[pairs[:, 1]] <= upper[pairs[:, 0]])).all(1)]
        candidate_count += len(pairs)
        shared = np.array([len(set(al[a]).intersection(al[c])) for a, c in pairs])
        keep = shared < 2
        pairs, shared = pairs[keep], shared[keep]
        if not len(pairs):
            continue
        tested = crossing(q[pairs[:, 0]], q[pairs[:, 1]])
        for pair, count in zip(pairs[tested], shared[tested]):
            faces = []
            for f in pair:
                pi, fi = (0, int(f)) if f < len(triangles[0]) else (2, int(f-len(triangles[0])))
                faces.append({'primitive': pi, 'face': fi, 'source_face': int(ancestry[pi][fi]) if ancestry is not None else fi, 'kind': str(kind[pi][fi]) if kind is not None else 'source', 'triangle_m': q[f].tolist()})
            hits.append({'shared_physical_weld_count': int(count), 'faces': faces})
    wt = aliases[tris]
    directed = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    signed = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    coordinates = {int(i): p for i, p in zip(aliases, points)}
    boundary = {tuple(np.array(sorted([coordinates[int(a)].tolist(), coordinates[int(c)].tolist()])).ravel()) for a, c in edges[counts == 1]}
    _, groups = np.unique(aliases, return_inverse=True)
    low = np.full((groups.max()+1, 3), np.inf)
    high = np.full_like(low, -np.inf)
    np.minimum.at(low, groups, points)
    np.maximum.at(high, groups, points)
    area = np.linalg.norm(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]), axis=1)
    result = {'variant': label, 'all_cloth_triangles': len(tris), 'candidate_phase': 'float64 bounding spheres and AABB; strict six-edge interior narrow phase', 'AABB_candidate_pairs': candidate_count, 'strict_zero_shared_weld_crossings': sum(h['shared_physical_weld_count'] == 0 for h in hits), 'strict_one_shared_weld_crossings': sum(h['shared_physical_weld_count'] == 1 for h in hits), 'full_upper_crossing_count': sum(any(np.array(f['triangle_m'])[:, 1].max() >= 1.08 for f in h['faces']) for h in hits), 'all_crossing_witnesses': hits, 'boundary_edges': int((counts == 1).sum()), 'nonmanifold_edges': int((counts > 2).sum()), 'incoherent_two_face_winding_edges': int(((counts == 2) & (signed != 0)).sum()), 'degenerate_weld_triangles': int(((wt[:, 0] == wt[:, 1]) | (wt[:, 0] == wt[:, 2]) | (wt[:, 1] == wt[:, 2])).sum()), 'same_weld_position_bbox_max_m': float(np.linalg.norm(high-low, axis=1).max()), 'minimum_double_triangle_area_m2': float(area.min()), 'area_below_1e_minus12_count': int((area < 1e-12).sum())}
    print(label, 'crossings', result['strict_zero_shared_weld_crossings'], result['strict_one_shared_weld_crossings'], flush=True)
    return result, boundary

source_weld = [source_alias[source_offsets[i]:source_offsets[i+1]] for i in range(5)]
source_audit, source_boundary = audit('exact-V7-source-input', [b[f'p{i}'] for i in range(5)], [b[f'tr{i}'] for i in range(5)], source_weld)
candidate_audit, candidate_boundary = audit('tube02', [d[f'p{i}'] for i in range(5)], [d[f'tr{i}'] for i in range(5)], [d[f'physicalWeld{i}'] for i in range(5)], [d[f'sourceFaceAncestry{i}'] for i in range(5)], [d[f'faceKind{i}'] for i in range(5)])
quantized_audit, quantized_boundary = audit('tube02-float32-POSITION', [d[f'p{i}'].astype('f4').astype(float) for i in range(5)], [d[f'tr{i}'] for i in range(5)], [d[f'physicalWeld{i}'] for i in range(5)], [d[f'sourceFaceAncestry{i}'] for i in range(5)], [d[f'faceKind{i}'] for i in range(5)])
inventory = []
clipped = []
runtime_bad = []
for i in range(5):
    n = len(b[f'p{i}'])
    uv = g.array(primitives[i]['attributes']['TEXCOORD_0']).astype(float)
    checks = {'original_POSITION_prefix_exact': np.array_equal(d[f'p{i}'][:n], b[f'p{i}']), 'original_WEIGHT_prefix_exact': np.array_equal(d[f'W{i}'][:n], b[f'W{i}']), 'original_NORMAL_prefix_exact': np.array_equal(d[f'n{i}'][:n], shape[f'n{i}']), 'original_UV_prefix_exact': np.array_equal(d[f'uv{i}'][:n], uv), 'original_index_prefix_ancestry_exact': np.array_equal(d[f'oldVertex{i}'][:n], np.arange(n)), 'rest_double_area_matches_actual': np.allclose(d[f'restDoubleArea{i}'], np.linalg.norm(np.cross(d[f'p{i}'][d[f'tr{i}'][:,1]]-d[f'p{i}'][d[f'tr{i}'][:,0]], d[f'p{i}'][d[f'tr{i}'][:,2]]-d[f'p{i}'][d[f'tr{i}'][:,0]]), axis=1), rtol=1e-10, atol=1e-14)}
    retained = d[f'sourceFaceAncestry{i}'] >= 0
    exact_faces = np.array([np.array_equal(d[f'tr{i}'][f], b[f'tr{i}'][a]) for f, a in enumerate(d[f'sourceFaceAncestry{i}']) if a >= 0])
    inventory.append({'primitive': i, 'checks': {k: bool(v) for k, v in checks.items()}, 'source_faces_with_ancestry': int(retained.sum()), 'ancestral_faces_with_exact_original_vertex_triangle': int(exact_faces.sum()), 'new_vertex_count': len(d[f'p{i}'])-n, 'new_face_count': len(d[f'tr{i}'])-len(b[f'tr{i}']), 'original_unused_vertex_count': int(n-len(np.intersect1d(np.unique(d[f'tr{i}']), np.arange(n))))})
    parents = d[f'sourceVertexParents{i}']
    bary = d[f'sourceVertexBarycentric{i}']
    ids = np.flatnonzero((parents >= 0).all(1))
    for v in ids:
        pa = parents[v]
        bc = bary[v]
        clipped.append({'primitive': i, 'vertex': int(v), 'parents': pa.tolist(), 'barycentric': bc.tolist(), 'barycentric_sum_error': float(abs(bc.sum()-1)), 'POSITION_error_m': float(np.linalg.norm(d[f'p{i}'][v]-bc@b[f'p{i}'][pa])), 'WEIGHT_error': float(abs(d[f'W{i}'][v]-bc@b[f'W{i}'][pa]).max()), 'UV_error': float(abs(d[f'uv{i}'][v]-bc@uv[pa]).max())})
    weights = d[f'W{i}']
    indices = np.flatnonzero((weights > 1e-8).sum(1) > 4)
    for v in indices:
        positive = np.flatnonzero(weights[v] > 1e-8)
        runtime_bad.append({'primitive': i, 'vertex': int(v), 'joints': positive.tolist(), 'weights': weights[v, positive].tolist(), 'fifth_largest_weight': float(np.sort(weights[v])[-5]), 'old_vertex': int(d[f'oldVertex{i}'][v])})
# Sewn physical alias POSITION/weight agreement across complete cloth.
alias = np.r_[d['physicalWeld0'], d['physicalWeld2']]
weights = np.r_[d['W0'], d['W2']]
_, groups = np.unique(alias, return_inverse=True)
low = np.full((groups.max()+1, 19), np.inf)
high = np.full_like(low, -np.inf)
np.minimum.at(low, groups, weights)
np.maximum.at(high, groups, weights)
weight_spread = abs(high-low).max(1)
normal_seams = []
for side in ['L', 'R']:
    tube = d[f'tubeRows{side}']
    cap = set(d[f'bodyCapFaceIDs{side}'].tolist())
    tube_faces = set(d[f'newTubeFaceIDs{side}'].tolist())
    root_checks = {'opening_ring_same_indices_as_tube_first_row': np.array_equal(d[f'bodyOpeningVertices{side}'], tube[0]), 'tube_rest_rows_exact_actual_positions': np.array_equal(d[f'tubeRestRows{side}'], d['p0'][tube])}
    normal_seams.append({'side': side, 'ring_size': tube.shape[1], 'rows': tube.shape[0], 'checks': {k: bool(v) for k, v in root_checks.items()}, 'body_cap_faces': len(cap), 'tube_faces': len(tube_faces)})
result = {'candidate_path': str(path), 'candidate_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_input_path': str(source_path), 'source_input_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(), 'source': source_audit, 'candidate': candidate_audit, 'float32_POSITION_candidate': quantized_audit, 'boundary_position_set_exact_to_source': candidate_boundary == source_boundary, 'source_attribute_inventory': inventory, 'clipped_ring_barycentric_vertex_count': len(clipped), 'all_clipped_ring_barycentric_witnesses': clipped, 'tube_sewing_contract': normal_seams, 'within_physical_weld_weight_spread_max': float(weight_spread.max()), 'within_physical_weld_weight_mismatch_groups': int((weight_spread > 1e-9).sum()), 'runtime_stock4_compatible': not runtime_bad, 'runtime_more_than4_influence_vertex_count': len(runtime_bad), 'all_runtime_weight_incompatibility_witnesses': runtime_bad, 'cancelled_source_face_ids': d['oppositeDuplicateCancelledSourceFaces'].tolist(), 'limits': ['All-pair cloth0+2 rest strict transverse evidence only; coplanar/tangent contact and thickness unclassified.', 'Original prefix preservation does not imply original surface topology or standing appearance unchanged; removed/clipped source faces and new tubes require images.', 'Dense five-influence rows are not accepted stock four-influence runtime. No truncation or unmeasured shader equivalence.', 'Final GLB needs original image/normalized attribute/socket/19-bind/grip proof; no clips or pose gate run here.']}
(OUT / 'sleeve-tube02-independent-rest.json').write_text(json.dumps(result, indent=2))
print('RUNTIME', len(runtime_bad), 'bad rows; sewnWspread', result['within_physical_weld_weight_spread_max'], 'boundary exact', result['boundary_position_set_exact_to_source'], 'clipped', len(clipped), flush=True)
