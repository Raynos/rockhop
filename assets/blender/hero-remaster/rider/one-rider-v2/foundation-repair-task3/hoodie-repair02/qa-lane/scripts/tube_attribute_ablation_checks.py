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
parent_path = HERE / 'source-sleeve-tube-rest03-uv.npz'
normal_path = HERE / 'source-sleeve-tube-rest04-normal.npz'
weight_path = ROOT / 'hoodie-repair03/tube03-four-bind/four-cap-carrier03.npz'
a, n, w = [load(p) for p in [parent_path, normal_path, weight_path]]
source = load(ROOT / 'hoodie-repair02/v7-bind.npz')
shape = load(ROOT / 'hoodie-repair02/v7-shape-input.npz')
counts = [len(source[f'p{i}']) for i in range(5)]
# Root's four-influence semantic carrier rule, reconstructed independently.
expected = a['W0'].copy()
rule_rows = []
free_all = []
for side, upperarm, forearm in [('L', 6, 7), ('R', 10, 11)]:
    nodes = np.unique(a['tr0'][a[f'bodyCapFaceIDs{side}']])
    free = nodes[a['sourceUniqueVertex0'][nodes] < 0]
    free_all.extend(free.tolist())
    expected[free, upperarm] += expected[free, forearm]
    expected[free, forearm] = 0
    changed = free[(abs(expected[free]-a['W0'][free]).max(1) > 1e-12)]
    rule_rows.append({'side': side, 'upperarm_slot': upperarm, 'forearm_slot': forearm, 'free_cap_nodes': free.tolist(), 'changed_nodes': changed.tolist(), 'sewn_source_cap_boundary_nodes': nodes[a['sourceUniqueVertex0'][nodes] >= 0].tolist()})
weight_invariants = {k: bool(np.array_equal(a[k], w[k])) for k in a if k != 'W0'}
changed = np.flatnonzero(abs(w['W0']-a['W0']).max(1) > 1e-12)
weight_checks = {'only_declared_W0_field_changed': all(weight_invariants.values()), 'semantic_forearm_to_upperarm_rule_exact': bool(np.array_equal(expected, w['W0'])), 'changed_rows_only_declared_free_caps': set(changed).issubset(set(free_all)), 'all_original_source_WEIGHT_prefixes_exact': all(np.array_equal(w[f'W{i}'][:counts[i]], a[f'W{i}'][:counts[i]]) for i in range(5)), 'all_old_source_sewn_cap_boundaries_WEIGHT_exact': all(np.array_equal(w['W0'][r['sewn_source_cap_boundary_nodes']], a['W0'][r['sewn_source_cap_boundary_nodes']]) for r in rule_rows), 'four_influences_at_1e_minus8': max(int((w[f'W{i}'] > 1e-8).sum(1).max()) for i in range(5)) <= 4, 'all_weight_sums_within_1e_minus12': max(float(abs(w[f'W{i}'].sum(1)-1).max()) for i in range(5)) < 1e-12}
alias = np.r_[w['physicalWeld0'], w['physicalWeld2']]
weights = np.r_[w['W0'], w['W2']]
_, groups = np.unique(alias, return_inverse=True)
low = np.full((groups.max()+1, 19), np.inf)
high = np.full_like(low, -np.inf)
np.minimum.at(low, groups, weights)
np.maximum.at(high, groups, weights)
spread = float(abs(high-low).max())
weight_checks['within_physical_weld_WEIGHT_spread_below1e_minus12'] = spread < 1e-12
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
normal_checks['all428_clipped_endpoint_NORMALs_match_normalized_source_barycentric'] = sum(r['rows'] for r in clipped) == 428 and all(r['max_normal_vector_error'] < 1e-12 for r in clipped)
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
result = {'parent_sha256': hashlib.sha256(parent_path.read_bytes()).hexdigest(), 'four_weight_sha256': hashlib.sha256(weight_path.read_bytes()).hexdigest(), 'normal_only_sha256': hashlib.sha256(normal_path.read_bytes()).hexdigest(), 'four_weight_checks': weight_checks, 'four_weight_rule_rows': rule_rows, 'four_weight_changed_row_count': len(changed), 'four_weight_physical_weld_max_spread': spread, 'normal_only_checks': normal_checks, 'clipped_source_barycentric_normal_checks': clipped, 'normal_changed_used_rows': len(changed_normals), 'normal_changed_used_row_distance_witnesses': changed_normals, 'patch_to_actual_source_seam_normal_max_best_angle_degrees': max(source_seam_spread, default=0), 'independent_graph_method': 'Each sewn physical edge appears once with minimum true length; no duplicate raw UV seam length summation.', 'status': 'ATTRIBUTE_ABLATION_CONTRACT_PASS' if all(weight_checks.values()) and all(normal_checks.values()) else 'FAIL', 'limits': ['Four-weight semantic carrier changes material response; it is not five-weight skinning parity or anatomical truth. Root owns recorded trajectory comparison.', 'Normal04 source-corner and graph-distance contract does not certify normal direction against geometry, gray/PBR standing appearance or motion.', 'No new geometry audit because P/tr/physical welds invariant; no broad pose or render work here.', 'Normal04 and four-cap are separate snapshots of the same parent; an integrated final GLB still needs complete export and stock runtime proof.']}
(OUT / 'tube-four-weight-normal04-contracts.json').write_text(json.dumps(result, indent=2))
print(result['status'], 'Wchanged', len(changed), 'Wchecks', weight_checks, 'Nchecks', normal_checks, 'clipped', clipped)
