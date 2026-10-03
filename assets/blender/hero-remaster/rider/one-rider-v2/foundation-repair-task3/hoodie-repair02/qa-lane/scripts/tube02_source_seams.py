from pathlib import Path
import json, hashlib, sys
import numpy as np
ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
Q = ROOT / 'hoodie-repair02/qa-lane'
OUT = Q / 'uv-lower01'
HERE = ROOT / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
path = HERE / 'source-sleeve-tube-rest02.npz'
loaded = np.load(path)
d = {k: loaded[k] for k in loaded.files}
loaded = np.load(ROOT / 'hoodie-repair02/v7-bind.npz')
b = {k: loaded[k] for k in loaded.files}
cut = np.load(HERE / 'sleeve-cut-inventory.npz')
expand = np.load(HERE / 'expanded-torso-cut-inventory.npz')
sys.path.insert(0, str(ROOT / 'scripts'))
from glb import GLB
g = GLB(Q / 'C19-source.glb')
pr = [p for m in g.j['meshes'] for p in m['primitives']]
original = [g.array(p['attributes']['POSITION']).astype(float) for p in pr]
_, original_alias = np.unique(np.concatenate(original), axis=0, return_inverse=True)
off = np.r_[0, np.cumsum([len(x) for x in original])]
p0facecount = len(b['tr0'])
allowed_deleted = expand['deletedSourceFacesL'] | expand['deletedSourceFacesR']
clipped_set = set(np.r_[cut['clippedTubeFaceIDsL'], cut['clippedTubeFaceIDsR']].tolist())
cancelled = {tuple(x) for x in d['oppositeDuplicateCancelledSourceFaces'].tolist()}
face_inventory = []
for pi in [0, 2]:
    ancestry = d[f'sourceFaceAncestry{pi}']
    present = set(ancestry[ancestry >= 0].tolist())
    removed = sorted(set(range(len(b[f'tr{pi}']))) - present)
    unsupported = []
    for f in removed:
        globalf = f if pi == 0 else p0facecount + f
        if not allowed_deleted[globalf] and globalf not in clipped_set and (pi, f) not in cancelled:
            unsupported.append(f)
    face_inventory.append({'primitive': pi, 'unique_original_faces_retained_or_clipped': len(present), 'removed_original_source_faces': removed, 'removed_faces_outside_declared_cut_clip_cancellation_contract': unsupported})
# Only groups where a referenced old source corner meets a referenced new corner.
points = np.r_[d['p0'], d['p2']]
normals = np.r_[d['n0'], d['n2']]
alias = np.r_[d['physicalWeld0'], d['physicalWeld2']]
old = np.r_[np.arange(len(d['p0'])) < len(b['p0']), np.ones(len(d['p2']), bool)]
used = np.zeros(len(points), bool)
used[np.r_[np.unique(d['tr0']), np.unique(d['tr2']) + len(d['p0'])]] = True
normal_witnesses = []
for physical in np.intersect1d(np.unique(alias[old & used]), np.unique(alias[~old & used])):
    oldids = np.flatnonzero((alias == physical) & old & used)
    newids = np.flatnonzero((alias == physical) & ~old & used)
    oldn = normals[oldids] / np.maximum(np.linalg.norm(normals[oldids], axis=1, keepdims=True), 1e-15)
    newn = normals[newids] / np.maximum(np.linalg.norm(normals[newids], axis=1, keepdims=True), 1e-15)
    angles = np.degrees(np.arccos(np.clip(oldn @ newn.T, -1, 1)))
    normal_witnesses.append({'physical_weld_id': int(physical), 'source_vertices': [[0, int(v)] if v < len(d['p0']) else [2, int(v-len(d['p0']))] for v in oldids], 'new_vertices': newids.tolist(), 'max_source_patch_normal_angle_degrees': float(angles.max()), 'source_normals': normals[oldids].tolist(), 'patch_normals': normals[newids].tolist()})
normal_witnesses.sort(key=lambda x: x['max_source_patch_normal_angle_degrees'], reverse=True)
checks = []
for side in ['L', 'R']:
    torso = d[f'torsoSourceBoundary{side}']
    tube = d[f'tubeRows{side}']
    source_boundary_alias = set(torso.tolist())
    bodycap = d['tr0'][d[f'bodyCapFaceIDs{side}']]
    boundaryaliases = set(d['physicalWeld0'][bodycap].ravel().tolist())
    clipped_nodes = d[f'tubeEndSourceNodes{side}']
    expected = cut[f'ringRestPositions{side}'][clipped_nodes]
    checks.append({'side': side, 'all_referenced_torso_source_boundary_aliases_present_in_body_cap': source_boundary_alias.intersection(set(np.r_[d['physicalWeld0'][np.unique(d['tr0'])],d['physicalWeld2'][np.unique(d['tr2'])]].tolist())).issubset(boundaryaliases), 'unreferenced_source_boundary_aliases_after_cancellation': sorted(source_boundary_alias-set(np.r_[d['physicalWeld0'][np.unique(d['tr0'])],d['physicalWeld2'][np.unique(d['tr2'])]].tolist())), 'tube_end_matches_declared_clipped_source_ring_within_1e_minus12': bool(np.linalg.norm(d['p0'][tube[-1]]-expected, axis=1).max() < 1e-12), 'tube_end_max_difference_m': float(np.linalg.norm(d['p0'][tube[-1]]-expected, axis=1).max()), 'tube_opening_exact_shared_actual_indices': bool(np.array_equal(tube[0], d[f'bodyOpeningVertices{side}'])), 'source_boundary_vertices': len(torso), 'clipped_ring_vertices': tube.shape[1]})
loaded = np.load(ROOT / 'hoodie-repair02/v7-shape-input.npz')
source_normals = {key: loaded[key] for key in loaded.files}
clipped_normals = []
for pi in [0, 2]:
    parents = d[f'sourceVertexParents{pi}']
    bary = d[f'sourceVertexBarycentric{pi}']
    for v in np.flatnonzero((parents >= 0).all(1)):
        expected = bary[v] @ source_normals[f'n{pi}'][parents[v]]
        actual = d[f'n{pi}'][v]
        angle = np.degrees(np.arccos(np.clip(np.dot(expected, actual) / max(np.linalg.norm(expected)*np.linalg.norm(actual), 1e-15), -1, 1)))
        clipped_normals.append({'primitive': pi, 'vertex': int(v), 'source_parents': parents[v].tolist(), 'barycentric_source_normal': expected.tolist(), 'actual_clipped_corner_normal': actual.tolist(), 'angle_to_source_barycentric_normal_degrees': float(angle)})
result = {'clipped_source_NORMAL_corner_witnesses': clipped_normals, 'clipped_source_NORMAL_changed_over1degree': sum(r['angle_to_source_barycentric_normal_degrees']>1 for r in clipped_normals), 'clipped_source_NORMAL_max_angle_degrees': max(r['angle_to_source_barycentric_normal_degrees']for r in clipped_normals), 'candidate_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_face_removal_inventory': face_inventory, 'all_removed_faces_have_declared_cut_clip_or_cancellation_contract': not any(r['removed_faces_outside_declared_cut_clip_cancellation_contract'] for r in face_inventory), 'sewing_checks': checks, 'used_source_to_patch_normal_seam_groups': len(normal_witnesses), 'normal_seam_groups_over_1_degree': sum(r['max_source_patch_normal_angle_degrees'] > 1 for r in normal_witnesses), 'max_source_patch_normal_angle_degrees': normal_witnesses[0]['max_source_patch_normal_angle_degrees'] if normal_witnesses else None, 'all_normal_seam_witnesses': normal_witnesses, 'cancellation_status': 'Pending independent removed-cap witness supplement: post-cancel NPZ includes source face IDs only.', 'limits': ['Source/patch normal differences are shading discontinuities, separate from exact sewn position/weight closure; they require matched gray/textured image review.', 'An allowed local source-face deletion contract is not anatomical or standing appearance acceptance.', 'No pose, support, texture rendering or stock five-influence equivalence claimed.']}
(OUT / 'sleeve-tube02-source-seams.json').write_text(json.dumps(result, indent=2))
print('REMOVAL', result['all_removed_faces_have_declared_cut_clip_or_cancellation_contract'], 'SEWING', checks, 'NORMAL groups', len(normal_witnesses), 'maxangle', result['max_source_patch_normal_angle_degrees'])
