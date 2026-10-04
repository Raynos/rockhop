"""Read-only actual Blender evaluation at all529native/all703actual47 fields.

Same frozen neck27 construction; full/four, current/frozen tessellation and
garment/body/head targets remain explicit. No saved pose or geometry change.
"""
import gzip
import hashlib
import json
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

root = Path(__file__).resolve().parents[6]
owned = Path(__file__).resolve().parent
ev = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = ev / 'neck-interface99'
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'motion.json').exists()
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
auth = json.loads((ev / 'neck-interface97/authoring.json').read_text())
freeze = json.loads((ev / 'neck-interface98/triangulation.json').read_text())
native = root / freeze['native']
field_path = native.parent / 'triangulated-neck-fields.npz'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native) == freeze['nativeSHA256'] and sha(field_path) == freeze['fieldsSHA256']
f = np.load(field_path)
native_fields = np.load(qa / 'body52/native-fields.npz')
export_fields = np.load(qa / 'body52/export-fields.npz')
proposal_path = qa / 'body59/proposal.json'
assert sha(proposal_path) == '5f563c032791a9426c0447a2b8c818b140fd62e56a621fd4b81efd461cfdefa6'
scope = json.loads(proposal_path.read_text())['preciseInitialAuthoringMargin']
driver_path = ev / 'diagnostic02/driver.json'
assert sha(driver_path) == '8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b'
driver = json.loads(driver_path.read_text())
actual_path = qa / 'garment47/first.weights.ndjson.gz'
assert sha(actual_path) == '9db354f3ab54f9b860be83a2f372aceafb9b7d682a8c5e6bf42afd5153b82758'
with gzip.open(actual_path, 'rt') as stream: actual = [json.loads(line) for line in stream]
assert len(driver['frames']) == 529 and len(actual) == 703
pins = {str(p.relative_to(root)): sha(p) for p in [native, field_path, proposal_path, driver_path, actual_path,
    qa / 'body52/native-fields.npz', qa / 'body52/export-fields.npz', ev / 'neck-interface98/reopen-rest.json']}
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
rig = bpy.data.objects['Independent anatomical foundation rig']
names = f['boneNames'].tolist()
assert names == [b.name for b in rig.data.bones] and len(names) == 51
assert all(not b.constraints for b in rig.pose.bones)
objects = {(key, label): bpy.data.objects['Bounded neck27 triangulated ' + key + ' ' + label + ', unaccepted']
    for key in ['body', 'head'] for label in ['full', 'four']}
garment = bpy.data.objects['Actual donor explicit native-four skin, unaccepted']
old_head = bpy.data.objects['Protected textured head above hidden neck interface']
for obj in [rig, garment, old_head] + list(objects.values()): obj.hide_set(False)
bpy.context.view_layer.update()
world = np.array(rig.matrix_world)
world_inv = np.linalg.inv(world)
C = np.array([[1., 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
normalize = lambda name: name.replace('.', '').replace('_', '')
game_order = [list(map(normalize, export_fields['jointNames'])).index(normalize(name)) for name in names]
rest_bones = np.array([np.array(rig.data.bones[name].matrix_local) for name in names])
parent_order = sorted(names, key=lambda name: len(rig.data.bones[name].parent_recursive))
fixed_triangles = {key: f[key + 'Triangles'] for key in ['body', 'head']}
physical = {}; base = len(f['commonU'])
registry = np.load(ev / 'neck-interface96/ordered-boundaries.npz')
for key in ['body', 'head']:
    p = f[key + 'RestXYZ']; ids = np.arange(len(p), dtype=np.int64) + base
    if key == 'head': ids[:len(registry['headPositionAlias'])] = registry['headPositionAlias'] + base
    sid = f[key + 'SeamPhysicalIDs']; ids[sid >= 0] = sid[sid >= 0]
    physical[key] = ids; base += len(p)
body_count = len(f['bodyRestXYZ'])
physical_both = np.r_[physical['body'], physical['head']]
fixed_combined = np.vstack([fixed_triangles['body'], fixed_triangles['head'] + body_count])
rest_area = {}
sparse = {}
for key in ['body', 'head']:
    xyz = f[key + 'RestXYZ'].astype(float)
    q = xyz[fixed_triangles[key]]
    rest_area[key] = .5 * np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1)
    for label in ['full', 'four']:
        w = f[key + label.title() + 'Weights'].astype(float); w /= w.sum(axis=1)[:, None]
        sparse[key, label] = [(np.flatnonzero(w[:, j] > 0), w[w[:, j] > 0, j]) for j in range(51)]

def manual(key, label, matrices):
    rest = np.column_stack([f[key + 'RestXYZ'], np.ones(len(f[key + 'RestXYZ']))])
    points = np.zeros_like(rest, dtype=float)
    for j, (ids, weights) in enumerate(sparse[key, label]):
        if len(ids): points[ids] += (rest[ids] @ matrices[j].T) * weights[:, None]
    return (points @ np.array(objects[key, label].matrix_world).T)[:, :3]

def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(); mesh.calc_loop_triangles()
    points = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
    polygons = np.array([t.polygon_index for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return points, triangles, polygons

def tree(points, triangles):
    return BVHTree.FromPolygons([Vector(p) for p in points], triangles.tolist(), all_triangles=True)

def local_ids(key, triangles, polygons):
    old_vertices = next(p['originalVertices'] for p in auth['parts'] if p['part'] == key)
    allowed = scope['bodyExistingRenderedNativeVertices' if key == 'body' else 'headInitialBoundaryLedNativeVertexIDs']
    return np.flatnonzero(np.isin(triangles, allowed).any(axis=1) | (triangles >= old_vertices).any(axis=1))

def collision_counts(points, triangles, local):
    whole = tree(points, triangles); patch = tree(points, triangles[local])
    triangle_phys = [frozenset(row) for row in physical_both[triangles]]
    pairs = set()
    for i, j in patch.overlap(whole):
        a = int(local[i]); b = int(j)
        if a != b and triangle_phys[a].isdisjoint(triangle_phys[b]): pairs.add(tuple(sorted((a, b))))
    body_t = len(current_body_triangles)
    classes = {'bodySelf': [], 'headSelf': [], 'bodyHead': []}
    for pair in sorted(pairs):
        kind = 'bodySelf' if pair[1] < body_t else 'headSelf' if pair[0] >= body_t else 'bodyHead'
        classes[kind].append(list(pair))
    return {k: {'pairs': len(v), 'firstWitnesses': v[:4]} for k, v in classes.items()}

def set_actual_pose(matrices):
    desired = matrices @ rest_bones
    lookup = {name: i for i, name in enumerate(names)}
    for name in parent_order:
        bone = rig.data.bones[name]; parent = bone.parent
        keywords = {} if parent is None else {'parent_matrix': Matrix(desired[lookup[parent.name]].tolist()), 'parent_matrix_local': parent.matrix_local}
        rig.pose.bones[name].matrix_basis = bone.convert_local_to_pose(Matrix(desired[lookup[name]].tolist()), bone.matrix_local, invert=True, **keywords)

records = []; skin_matrices = []; witnesses = {}; start = time.monotonic()
for domain, source_ids in [('native', range(529)), ('actual47', range(1, 704))]:
    for source_id in source_ids:
        if domain == 'native':
            frame = driver['frames'][source_id]
            for name, trs in frame['poseBasisBlender'].items():
                bone = rig.pose.bones[name]; bone.rotation_mode = 'QUATERNION'
                bone.location = trs['location']; bone.rotation_quaternion = trs['quaternionWXYZ']; bone.scale = trs['scale']
            requested = None
        else:
            game_k = np.array(actual[source_id - 1]['matrices']).reshape(51, 4, 4).transpose(0, 2, 1)[game_order]
            requested = world_inv @ C.T @ game_k @ C @ world
            set_actual_pose(requested)
        bpy.context.view_layer.update()
        matrices = np.array([np.array(rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()) for name in names])
        skin_matrices.append(matrices)
        record = {'domain': domain, 'sourceIndex': source_id, 'sourceTimeS': frame['timeS'] if domain == 'native' else source_id / 120,
            'actualRigVsRequestedMatrixMaximumComponentDifference': None if requested is None else float(np.abs(matrices - requested).max()), 'variants': {}}
        surfaces = {(key, label): surface(obj) for (key, label), obj in objects.items()}
        gp, gt, _ = surface(garment); garment_tree = tree(gp, gt)
        ohp, oht, _ = surface(old_head)
        old_pairs = garment_tree.overlap(tree(ohp, oht))
        record['unchangedGarmentVsOriginalProtectedHeadNativePairs'] = len(old_pairs)
        for label in ['full', 'four']:
            variant = {'parts': {}, 'seamMaximumDriftM': 0., 'seamWorstPhysicalKnot': None}
            combined_points = np.vstack([surfaces['body', label][0], surfaces['head', label][0]])
            current_body_triangles = surfaces['body', label][1]
            current_triangles = np.vstack([current_body_triangles, surfaces['head', label][1] + body_count])
            current_local = np.r_[local_ids('body', current_body_triangles, surfaces['body', label][2]),
                local_ids('head', surfaces['head', label][1], surfaces['head', label][2]) + len(current_body_triangles)]
            variant['localNativeCollision'] = collision_counts(combined_points, current_triangles, current_local)
            fixed_local = np.r_[f['bodyLocalTriangleIDs'], f['headLocalTriangleIDs'] + len(fixed_triangles['body'])]
            if np.array_equal(current_triangles, fixed_combined): variant['localFixedCollision'] = variant['localNativeCollision']
            else:
                current_body_triangles = fixed_triangles['body']
                variant['localFixedCollision'] = collision_counts(combined_points, fixed_combined, fixed_local)
            seam_points = [[] for _ in f['commonU']]
            for key in ['body', 'head']:
                p, t, polys = surfaces[key, label]
                expected = manual(key, label, matrices)
                parity = np.linalg.norm(expected - p, axis=1)
                assert parity.max() <= 2e-6, (domain, source_id, key, label, parity.max())
                sid = f[key + 'SeamPhysicalIDs']
                for vertex in np.flatnonzero(sid >= 0): seam_points[int(sid[vertex])].append(p[vertex])
                local = f[key + 'LocalTriangleIDs']; q = p[fixed_triangles[key][local]]
                area = .5 * np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1)
                native_local = local_ids(key, t, polys); nq = p[t[native_local]]
                narea = .5 * np.linalg.norm(np.cross(nq[:, 1] - nq[:, 0], nq[:, 2] - nq[:, 0]), axis=1)
                raw_pairs = garment_tree.overlap(tree(p, t))
                source_map = f[key + 'CandidatePolygonToCheckpointPolygon']
                ancestry_pairs = [(int(a), int(source_map[polys[b]])) for a, b in raw_pairs]
                if key == 'head': ancestry_pairs = [(a, b if b < 71826 else -1) for a, b in ancestry_pairs]
                variant['parts'][key] = {'manualNativeLBSParityMaxM': float(parity.max()), 'currentRetessellatedTriangleRows': int(np.any(t != fixed_triangles[key], axis=1).sum()),
                    'fixedLocalMinimumAreaM2': float(area.min()), 'fixedLocalMinimumAreaRatio': float((area / rest_area[key][local]).min()),
                    'fixedLocalBelow1e_14M2': int((area <= 1e-14).sum()), 'currentLocalMinimumAreaM2': float(narea.min()),
                    'currentLocalBelow1e_14M2': int((narea <= 1e-14).sum()), 'garmentNativePairs': len(raw_pairs),
                    'garmentOriginalSourcePolygonPairs': len(set(ancestry_pairs)), 'garmentFirstRawWitnesses': raw_pairs[:4]}
                if domain == 'native' and source_id == 0:
                    witnesses[label + key + 'RestGarmentNativePairs'] = np.array(raw_pairs, dtype=np.int32)
                    witnesses[label + key + 'RestGarmentSourcePolygonPairs'] = np.array(ancestry_pairs, dtype=np.int32)
            drifts = [float(np.linalg.norm(np.array(points) - points[0], axis=1).max()) for points in seam_points]
            variant['seamMaximumDriftM'] = max(drifts); variant['seamWorstPhysicalKnot'] = int(np.argmax(drifts))
            assert variant['seamMaximumDriftM'] <= 2e-6, (domain, source_id, label, max(drifts))
            record['variants'][label] = variant
        record['fullVsFourLoss'] = {}
        for key in ['body', 'head']:
            delta = np.linalg.norm(surfaces[key, 'full'][0] - surfaces[key, 'four'][0], axis=1)
            original_count = next(p['originalVertices'] for p in auth['parts'] if p['part'] == key)
            allowed = scope['bodyExistingRenderedNativeVertices' if key == 'body' else 'headInitialBoundaryLedNativeVertexIDs']
            patch_vertices = np.r_[allowed, np.arange(original_count, len(delta))]
            record['fullVsFourLoss'][key] = {'allVerticesMaxM': float(delta.max()), 'allVerticesWorstID': int(np.argmax(delta)),
                'admittedAndNewVerticesMaxM': float(delta[patch_vertices].max()), 'admittedAndNewVerticesWorstID': int(patch_vertices[np.argmax(delta[patch_vertices])])}
        if (domain == 'native' and source_id in [0, 72, 144, 168, 192]) or (domain == 'actual47' and source_id in [512, 668, 703]):
            for (key, label), (p, t, _) in surfaces.items():
                witnesses[domain + str(source_id) + key + label + 'ActualWorld'] = p.astype(np.float32)
                witnesses[domain + str(source_id) + key + label + 'ActualTriangles'] = t
        records.append(record)
        if len(records) % 12 == 1:
            print('NECK_STREAM', domain, source_id, 'seamUm', record['variants']['four']['seamMaximumDriftM'] * 1e6,
                'local', {k: v['pairs'] for k, v in record['variants']['four']['localNativeCollision'].items()},
                'seconds', round(time.monotonic() - start, 1), flush=True)
            (out / 'progress.json').write_text(json.dumps({'completed': len(records), 'target': 1232, 'domain': domain,
                'sourceIndex': source_id, 'elapsedS': time.monotonic() - start}, indent=2) + '\n')
        # Stable per-sample journal survives interruption without claiming a
        # complete result; final JSON is written only after all identities.
        with (out / 'partial.ndjson').open('a') as stream: stream.write(json.dumps(record) + '\n')
assert len(records) == 1232
summaries = {}
for domain in ['native', 'actual47']:
    rows = [r for r in records if r['domain'] == domain]
    summaries[domain] = {'samples': len(rows), 'variants': {},
        'originalProtectedHeadGarmentMaxPairs': max(r['unchangedGarmentVsOriginalProtectedHeadNativePairs'] for r in rows),
        'fullVsFourLossMaxM': {key: max(r['fullVsFourLoss'][key]['allVerticesMaxM'] for r in rows) for key in ['body', 'head']},
        'admittedAndNewFullVsFourLossMaxM': {key: max(r['fullVsFourLoss'][key]['admittedAndNewVerticesMaxM'] for r in rows) for key in ['body', 'head']}}
    for label in ['full', 'four']:
        summaries[domain]['variants'][label] = {'seamMaxDriftM': max(r['variants'][label]['seamMaximumDriftM'] for r in rows),
            'localNativeCollisionMaxPairs': {key: max(r['variants'][label]['localNativeCollision'][key]['pairs'] for r in rows) for key in ['bodySelf', 'headSelf', 'bodyHead']},
            'parts': {key: {'minFixedLocalAreaM2': min(r['variants'][label]['parts'][key]['fixedLocalMinimumAreaM2'] for r in rows),
                'framesWithBelow1e_14M2': sum(r['variants'][label]['parts'][key]['fixedLocalBelow1e_14M2'] > 0 for r in rows),
                'maxManualNativeParityM': max(r['variants'][label]['parts'][key]['manualNativeLBSParityMaxM'] for r in rows),
                'maxGarmentNativePairs': max(r['variants'][label]['parts'][key]['garmentNativePairs'] for r in rows)} for key in ['body', 'head']}}
archive = out / 'pose-witnesses.npz'
np.savez_compressed(archive, rigLocalSkinMatrices=np.array(skin_matrices), rigWorldRows=world, boneNames=np.array(names),
    domains=np.array([r['domain'] for r in records]), sourceIndices=np.array([r['sourceIndex'] for r in records]), **witnesses)
assert pins == {p: sha(root / p) for p in pins}
report = {'status': 'UNACCEPTED_ALL_ARCHIVED_NECK_FIELDS_MEASURED_CONTACT_AND_ART_OPEN', 'pins': pins, 'recipeSHA256': sha(__file__),
    'archiveSHA256': sha(archive), 'samples': len(records), 'elapsedS': time.monotonic() - start, 'summaries': summaries, 'frames': records,
    'methods': ['529exact archived native poseBasis identities and703actual47primary51skin matrices converted through unchanged rig/file/glTF frames; no interpolation/controller run.',
        'Actual evaluated Blender Armature positions/full-four groups. Manual normalized LBS parity checked every sample/part/field.',
        'Shared physical outer seam aliases measured in actual native world at every sample; <=2micrometres is a precision bar only.',
        'BVH.overlap local vs whole body/head, including all incident one-corner faces; exclude same or shared physical/sourceUV-alias vertex adjacency. Native-current and fixed-rest triangles reported separately.',
        'Frozen garment26 FOUR remains unmodified; contacts against new body/head and original protected head remain distinct. Raw intersections are not signed depth or visible-hole judgement.'],
    'limits': ['No between-sample collision certificate, alpha/culling visibility certificate or art acceptance; counts do not qualify appearance.',
        'Full body control retains original full weights outside patch; four retains original primary-four. Full applied to actual47matrices is a labelled counterfactual, not an actual game full trace.',
        'Rest construction topology pass is separate from attachment/collision/garment contacts.490preexisting head contacts are not waived.',
        'No native save, source edit, field retry, body/head replacement, new worker/model/GPU job, package install, engine admission, publication or promotion. All M0-M5 open.']}
(out / 'motion.json').write_text(json.dumps(report, indent=2) + '\n')
print('NECK_ALL_STREAMS_READY', json.dumps(summaries), flush=True)
