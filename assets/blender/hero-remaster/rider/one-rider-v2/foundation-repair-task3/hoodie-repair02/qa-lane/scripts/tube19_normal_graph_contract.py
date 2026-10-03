from pathlib import Path
import json, hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q = ROOT / 'hoodie-repair02/qa-lane'
OUT = Q / 'uv-lower01'
HERE = ROOT / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
def load(path):
    archive = np.load(path)
    return {k: archive[k] for k in archive.files}
def unit(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-15)
parent_path = HERE / 'source-sleeve-tube-rest18-dart.npz'
normal_path = HERE / 'source-sleeve-tube-rest19-normal.npz'
a,n = [load(p) for p in [parent_path,normal_path]]
source = load(ROOT / 'hoodie-repair02/v7-bind.npz')
shape = load(ROOT / 'hoodie-repair02/v7-shape-input.npz')
counts = [len(source[f'p{i}']) for i in range(5)]
# Normal04: only n0/n2 may differ, all original source n rows held exactly.
normal_invariants = {k: bool(np.array_equal(a[k], n[k])) for k in a if k not in ['n0', 'n2']}
normal_checks = {'all_non_NORMAL_fields_exact_parent': all(normal_invariants.values()), 'all_original_normal_prefixes_exact': all(np.array_equal(n[f'n{i}'][:counts[i]], shape[f'n{i}']) for i in range(5))}
clipped = []
refs = {}
for i in [0, 2]:
    parents, bary = n[f'sourceVertexParents{i}'], n[f'sourceVertexBarycentric{i}']
    ids = np.flatnonzero((np.arange(len(parents)) >= counts[i]) & (parents >= 0).all(1))
    expected_n = unit((shape[f'n{i}'][parents[ids]] * bary[ids, :, None]).sum(1))
    clipped.append({'primitive': i, 'rows': len(ids), 'max_normal_vector_error': float(abs(n[f'n{i}'][ids]-expected_n).max()) if len(ids) else 0})
    active = np.unique(n[f'tr{i}'])
    source_controls = active[(active < counts[i]) | np.isin(active, ids)]
    for v in source_controls:
        refs.setdefault(int(n[f'physicalWeld{i}'][v]), []).append(n[f'n{i}'][v])
normal_checks['all222_retained_clipped_NORMALs_match_normalized_source_barycentric'] = sum(r['rows'] for r in clipped) == 222 and all(r['max_normal_vector_error'] < 1e-12 for r in clipped)
# Independent physical-edge graph: min length per unique physical edge.
edge_length = {}
for i in [0, 2]:
    p, weld, tris = n[f'p{i}'], n[f'physicalWeld{i}'], n[f'tr{i}']
    edges = np.unique(np.sort(np.concatenate([tris[:, [0,1]], tris[:, [1,2]], tris[:, [2,0]]]), axis=1), axis=0)
    for x, y in edges:
        pair = tuple(sorted([int(weld[x]), int(weld[y])]))
        if pair[0] == pair[1]:
            continue
        length = max(float(np.linalg.norm(p[x]-p[y])), 1e-9)
        edge_length[pair] = min(edge_length.get(pair, np.inf), length)
physical = np.unique(np.array(list(edge_length)).ravel())
lookup = {int(v): i for i, v in enumerate(physical)}
pairs = np.array([[lookup[x], lookup[y]] for x, y in edge_length], int)
lengths = np.array(list(edge_length.values()))
graph = coo_matrix((np.r_[lengths,lengths], (np.r_[pairs[:,0],pairs[:,1]], np.r_[pairs[:,1],pairs[:,0]])), shape=(len(physical),len(physical))).tocsr()
seeds = np.array([lookup[v] for v in refs if v in lookup])
distance = dijkstra(graph, indices=seeds, min_only=True)
changed_normals = []
source_seam_spread = []
for i in [0, 2]:
    delta = np.linalg.norm(n[f'n{i}']-a[f'n{i}'], axis=1)
    active = np.unique(n[f'tr{i}'])
    changed_used = active[delta[active] > 1e-9]
    for v in changed_used:
        group = int(n[f'physicalWeld{i}'][v])
        changed_normals.append({'primitive': i, 'vertex': int(v), 'distance_to_actual_source_seed_m': float(distance[lookup[group]])})
    for v in active[active >= counts[i]]:
        group = int(n[f'physicalWeld{i}'][v])
        if group in refs:
            controls = unit(np.array(refs[group]))
            actual = unit(n[f'n{i}'][v])
            angle = float(np.degrees(np.arccos(np.clip(controls @ actual, -1,1))).min())
            source_seam_spread.append(angle)
normal_checks['every_changed_used_NORMAL_row_inside_true20mm_sewn_distance'] = all(r['distance_to_actual_source_seed_m'] <= .020 + 1e-12 for r in changed_normals)
normal_checks['every_patch_seam_control_matches_an_actual_source_normal'] = max(source_seam_spread, default=0) < 1e-4
result={'status':'NORMAL19_SOURCE_AND_SEWN_GRAPH_PASS' if all(normal_checks.values()) else 'FAIL','parent18_sha256':hashlib.sha256(parent_path.read_bytes()).hexdigest(),'normal19_sha256':hashlib.sha256(normal_path.read_bytes()).hexdigest(),'checks':normal_checks,'clipped_source_barycentric_normal_checks':clipped,'normal_changed_used_rows':len(changed_normals),'changed_normal_true_sewn_distance_witnesses':changed_normals,'patch_to_actual_source_normal_max_best_angle_degrees':max(source_seam_spread,default=0),'limits':['Source normal ancestry/20mm sewn blend is not normal-to-geometry or shading/appearance acceptance.','Geometry/collision gates evaluated independently on frozen21; no new poses or broad tests.']}
(OUT/'sleeve-tube19-normal-graph-contract.json').write_text(json.dumps(result,indent=2));print(result['status'],'failed',[k for k,v in normal_checks.items() if not v],'changed',len(changed_normals),'clipped',clipped)
