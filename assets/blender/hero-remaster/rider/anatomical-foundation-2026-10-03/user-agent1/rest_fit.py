"""One bounded multi-pose rest-fit trial on the separate native wearable pattern.

Fixed body, weights, bind, topology and UV; clearance is solved through exact
LBS affine maps. Not fused-source repair, cloth simulation or a parameter sweep.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True)
ap.add_argument('--driver', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--evidence', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, driver_path, out, evidence = map(lambda x: Path(x).resolve(), [a.source, a.driver, a.out, a.evidence])
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
if (out / 'fit.blend').exists():
    raise RuntimeError('Frozen trial exists; do not retry parameter variants')
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
driver = json.loads(driver_path.read_text())
assert source_hash == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
body = objects['body']
fit_indices = [0, 112, 144, 240]
held_indices = [24, 48, 72, 96, 120, 168, 192, 216]
margin, cap, max_passes = .003, .020, 4
ray_directions = [Vector(d).normalized() for d in [(1, .371, .127), (-.461, .846, .267), (.153, .243, -.958)]]


def pose(index):
    for name, trs in driver['frames'][index]['poseBasisBlender'].items():
        pb = rig.pose.bones[name]
        pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
    bpy.context.view_layer.update()


def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vv = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    ff = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return vv, ff, BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)


def inside(bvh, p):
    votes = 0
    for direction in ray_directions:
        origin, hits = Vector(p), 0
        for _ in range(64):
            q, normal, triangle, distance = bvh.ray_cast(origin, direction, 4)
            if q is None:
                break
            hits += 1
            # BVH and mathutils are float32; 0.2µm can re-hit the same plane.
            # Advance in original-ray parameter space by a documented10µm.
            parameter = (q - Vector(p)).dot(direction)
            origin = Vector(p) + direction * (parameter + 1e-5)
        else:
            raise RuntimeError('Unbounded ray classification; cannot certify inside')
        votes += hits % 2
    return votes >= 2


def constraint(bvh, p):
    q, normal, triangle, distance = bvh.find_nearest(Vector(p))
    if distance >= margin and not inside(bvh, p):
        return None
    is_inside = inside(bvh, p)
    q, n = np.array(q), np.array(normal)
    if is_inside:
        if np.dot(n, q - p) < 0:
            n = -n
        return n, float(np.dot(q + margin * n - p, n))
    if distance < margin:
        n = (p - q) / distance if distance > 1e-10 else n
        return n, margin - float(distance)
    return None


cache = {}
for index in fit_indices:
    pose(index)
    cache[index] = {'body': surface(body)}
    bone_maps = {pb.name: np.array(rig.matrix_world @ pb.matrix @ rig.data.bones[pb.name].matrix_local.inverted())
                 for pb in rig.pose.bones}
    for region in ['cloth', 'jeans']:
        obj = objects[region]
        vv, ff, _ = surface(obj)
        linear = []
        for v in obj.data.vertices:
            maps = [(bone_maps[obj.vertex_groups[g.group].name], g.weight) for g in v.groups
                    if obj.vertex_groups[g.group].name in bone_maps and g.weight > 0]
            linear.append(sum((m[:3, :3] * w for m, w in maps), np.zeros((3, 3))))
        cache[index][region] = {'base': vv, 'faces': ff, 'linear': np.array(linear)}

history, failures, displacements = [], [], {}
for region in ['cloth', 'jeans']:
    obj = objects[region]
    original = np.array([v.co for v in obj.data.vertices])
    delta = np.zeros_like(original)
    neighbors = [set() for _ in original]
    for edge in obj.data.edges:
        i, j = edge.vertices
        neighbors[i].add(j)
        neighbors[j].add(i)
    for pass_index in range(max_passes):
        violations, worst = 0, 0.
        for index in fit_indices:
            entry = cache[index][region]
            bvh = cache[index]['body'][2]
            linear, base = entry['linear'], entry['base']
            probes = [([i], np.array([1.])) for i in range(len(delta))]
            for face in entry['faces']:
                probes.extend([(face, np.array([1 / 3, 1 / 3, 1 / 3])),
                               (face[:2], np.array([.5, .5])),
                               (face[1:], np.array([.5, .5])),
                               (face[[0, 2]], np.array([.5, .5]))])
            for ids, bary in probes:
                ids = np.array(ids)
                p = ((base[ids] + np.einsum('vij,vj->vi', linear[ids], delta[ids])) * bary[:, None]).sum(axis=0)
                result = constraint(bvh, p)
                if result is None or result[1] <= 2e-5:
                    continue
                n, violation = result
                gradients = np.einsum('vji,j->vi', linear[ids], n) * bary[:, None]
                norm = float((gradients ** 2).sum())
                if norm < 1e-12:
                    failures.append('Singular exact LBS constraint')
                    break
                delta[ids] += violation * gradients / norm
                violations += 1
                worst = max(worst, violation)
        # One fixed graph regularization step; no alternate stiffness variants.
        mean = np.array([delta[list(ns)].mean(axis=0) if ns else delta[i] for i, ns in enumerate(neighbors)])
        delta = .75 * delta + .25 * mean
        maximum = float(np.linalg.norm(delta, axis=1).max())
        history.append({'region': region, 'pass': pass_index + 1, 'constraintsProjected': violations,
                        'worstRequestedStepM': worst, 'maximumRestDisplacementM': maximum})
        print('REST_FIT_PASS', history[-1], flush=True)
        if maximum > cap:
            failures.append(region + ' exceeded fixed20mm rest-displacement cap')
            break
        if not violations:
            break
    if np.linalg.norm(delta, axis=1).max() > cap:
        # Preserve the rejected numerical trial, but bound the diagnostic export.
        lengths = np.linalg.norm(delta, axis=1)
        delta *= np.minimum(1, cap / np.maximum(lengths, 1e-12))[:, None]
    for vertex, p in zip(obj.data.vertices, original + delta):
        vertex.co = p
    obj.data.update()
    displacements[region] = {'maxM': float(np.linalg.norm(delta, axis=1).max()),
        'rmsM': float(np.sqrt((delta ** 2).sum(axis=1).mean())),
        'worstNativeID': int(np.linalg.norm(delta, axis=1).argmax()),
        'restDeltaPerVertex': delta.tolist()}

review = []
for index in fit_indices + held_indices:
    pose(index)
    bv, bf, bb = surface(body)
    for region in ['cloth', 'jeans']:
        vv, ff, tree = surface(objects[region])
        contact = tree.overlap(bb)
        self_pairs = [(i, j) for i, j in tree.overlap(tree) if i < j and not set(ff[i]).intersection(ff[j])]
        review.append({'frame': index, 'timeS': driver['frames'][index]['timeS'],
            'domain': 'fit' if index in fit_indices else 'held-out', 'region': region,
            'bodyTriangleContactPairs': len(contact), 'nonadjacentSelfPairs': len(self_pairs),
            'firstBodyPairs': contact[:12], 'firstSelfPairs': self_pairs[:12]})
        if contact:
            failures.append(f'{region} remaining body contact at frame{index}: {len(contact)}pairs')
pose(0)
objects['boxers'].hide_render = True
root['rockhopRiderSkinConditioned'] = 1  # Already regression-qualified asset-specific declaration.
bpy.ops.object.select_all(action='DESELECT')
for obj in [root, rig, body, objects['cloth'], objects['jeans']]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'fit.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'fit.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=False, export_attributes=True, export_extras=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
report = {'status': 'REJECTED bounded rest-fit trial' if failures else 'UNACCEPTED sampled rest-fit candidate',
    'failures': sorted(set(failures)), 'sourceMasterSHA256': source_hash,
    'driverSHA256': hashlib.sha256(driver_path.read_bytes()).hexdigest(),
    'masterSHA256': hashlib.sha256((out / 'fit.blend').read_bytes()).hexdigest(),
    'GLBSHA256': hashlib.sha256((out / 'fit.glb').read_bytes()).hexdigest(),
    'mechanism': 'Minimal exactLBS halfspace rest-fit with fixedgraph regularization; completebody3ray inside vote; vertices/centroids/edge-midpoint constraints',
    'settings': {'marginM': margin, 'capM': cap, 'maximumPasses': max_passes,
                 'fitFrames': fit_indices, 'heldOutFrames': held_indices, 'regularization': .25,
                 'rayAdvanceM': 1e-5},
    'history': history, 'displacements': displacements, 'review': review,
    'dressedSelection': ['body', 'cloth', 'jeans'], 'excludedLayer': 'boxers (separate fitting variant)',
    'limits': ['One bounded trial; no further parameter sweep after falsification.',
        'Finite constraints are not continuous signed complete-surface clearance.',
        'Clipping cap only bounds rejected diagnostic, not acceptance.',
        'Body, weights, skeleton, UVs and topology unchanged; rest garment positions only.',
        'No head/hood identity integration; gray native control, not promoted.']}
(evidence / 'rest-fit.json').write_text(json.dumps(report, indent=2) + '\n')
print('REST_FIT_RESULT', report['status'], report['failures'], flush=True)
