"""Bounded authored left-underarm/knee pose-space volume prototype."""
import argparse
import hashlib
import json
import math
import sys
from collections import deque
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ap = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'driver', 'out', 'evidence']:
    ap.add_argument('--' + name, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, driver_path, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'prototype.blend').exists():
    raise RuntimeError('Frozen prototype exists; no volume/support/driver parameter loop')
driver = json.loads(driver_path.read_text()); source_hash = sha(source)
assert source_hash == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
body = objects['body']
configs = [dict(region='cloth', label='Left underarm authored volume', seeds=[598, 725, 1022, 630, 843, 1091],
    frames=[112, 144, 240], joints=['shoulder.L', 'upperArm.L', 'forearm.L', 'chest'], volumeM=.012),
    dict(region='jeans', label='Left knee authored volume', seeds=[51, 727, 229],
    frames=[240], joints=['thigh.L', 'shin.L'], volumeM=.014)]

def zero_shapes():
    for region in ['cloth', 'jeans']:
        if objects[region].data.shape_keys:
            for key in objects[region].data.shape_keys.key_blocks:
                key.value = 0

def set_pose(index):
    for name, trs in driver['frames'][index]['poseBasisBlender'].items():
        pb = rig.pose.bones[name]
        pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
    bpy.context.view_layer.update()

def surface(o):
    oo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = oo.to_mesh(); m.calc_loop_triangles()
    vv = np.array([oo.matrix_world @ v.co for v in m.vertices]); ff = np.array([list(t.vertices) for t in m.loop_triangles], dtype=np.int32)
    oo.to_mesh_clear(); return vv, ff, BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)

def signature(o):
    return hashlib.sha256(json.dumps({'v': [list(v.co) for v in o.data.vertices],
        'f': [list(f.vertices) for f in o.data.polygons], 'w': [[(g.group, g.weight) for g in v.groups] for v in o.data.vertices],
        'uv': [[list(item.uv) for item in layer.data] for layer in o.data.uv_layers]}).encode()).hexdigest()

def quaternion_distance(pose_a, pose_b, names):
    return math.sqrt(sum((2 * math.acos(min(1, abs(float(np.dot(pose_a[n]['quaternionWXYZ'], pose_b[n]['quaternionWXYZ'])))))) ** 2 for n in names))

def coefficients(index, config):
    centers = [0] + config['frames']; current = driver['frames'][index]['poseBasisBlender']
    distances = [quaternion_distance(current, driver['frames'][f]['poseBasisBlender'], config['joints']) for f in centers]
    if min(distances) < 1e-5:
        weights = [float(i == distances.index(min(distances))) for i in range(len(centers))]
    else:
        weights = np.array(distances) ** -4; weights = (weights / sum(weights)).tolist()
    return weights[1:]

original_signatures = {r: signature(o) for r, o in objects.items()}
construction = []
for config in configs:
    o = objects[config['region']]; neighbors = [set() for _ in o.data.vertices]
    for edge in o.data.edges:
        aa, bb = edge.vertices; neighbors[aa].add(bb); neighbors[bb].add(aa)
    distances = [1000] * len(neighbors); todo = deque(config['seeds'])
    for seed in config['seeds']:
        distances[seed] = 0
    while todo:
        i = todo.popleft()
        for j in neighbors[i]:
            if distances[j] > distances[i] + 1:
                distances[j] = distances[i] + 1; todo.append(j)
    support = []
    for d in distances:
        t = max(0, min(1, (5 - d) / 2))
        support.append(t * t * (3 - 2 * t))
    config['supportIDs'] = [i for i, w in enumerate(support) if w > 0]
    config['supportWeights'] = [support[i] for i in config['supportIDs']]
    config['keys'] = []
    o.shape_key_add(name='Basis', from_mix=False)
    for index in config['frames']:
        zero_shapes(); set_pose(index)
        vv, ff, _ = surface(o); _, _, body_tree = surface(body)
        bone_maps = {pb.name: np.array(rig.matrix_world @ pb.matrix @ rig.data.bones[pb.name].matrix_local.inverted()) for pb in rig.pose.bones}
        key = o.shape_key_add(name=f"{config['label']} f{index}", from_mix=False)
        max_posed, max_native, worst_condition = 0., 0., 0.
        deltas = []
        for vertex in o.data.vertices:
            weight = support[vertex.index]
            if weight == 0:
                deltas.append([0, 0, 0]); continue
            q, normal, tri, distance = body_tree.find_nearest(Vector(vv[vertex.index]))
            q, normal = np.array(q), np.array(normal)
            dot = float(np.dot(vv[vertex.index] - q, normal))
            posed_delta = normal * weight * (config['volumeM'] + max(0, -dot))
            if np.linalg.norm(posed_delta) > .040:
                raise RuntimeError('Fixed40mm local posed-volume cap exceeded')
            maps = [(bone_maps[o.vertex_groups[g.group].name], g.weight) for g in vertex.groups if o.vertex_groups[g.group].name in bone_maps and g.weight > 0]
            linear = sum((m[:3, :3] * w for m, w in maps), np.zeros((3, 3)))
            condition = float(np.linalg.cond(linear)); worst_condition = max(worst_condition, condition)
            if condition > 100:
                raise RuntimeError('Singular inverse-ownLBS local authoring')
            delta = np.linalg.solve(linear, posed_delta)
            key.data[vertex.index].co = vertex.co + Vector(delta)
            max_posed = max(max_posed, float(np.linalg.norm(posed_delta))); max_native = max(max_native, float(np.linalg.norm(delta)))
            deltas.append(delta.tolist())
        config['keys'].append(key.name)
        row = {'region': config['region'], 'frame': index, 'key': key.name, 'supportVertices': len(config['supportIDs']),
            'maximumPosedVolumeM': max_posed, 'maximumNativeMorphDeltaM': max_native,
            'maximumOwnLBSCondition': worst_condition, 'deltasNativeM': deltas}
        construction.append(row); print('LOCAL_CORRECTIVE_AUTHORED', {k: v for k, v in row.items() if k != 'deltasNativeM'}, flush=True)

review = []
for index in [0, 112, 144, 240, 24, 48, 72, 96, 120, 168, 192, 216]:
    zero_shapes(); set_pose(index); _, _, body_tree = surface(body)
    for config in configs:
        o = objects[config['region']]; support = set(config['supportIDs'])
        versions = []
        for enabled in [False, True]:
            values = coefficients(index, config) if enabled else [0] * len(config['keys'])
            for name, value in zip(config['keys'], values):
                o.data.shape_keys.key_blocks[name].value = value
            bpy.context.view_layer.update(); vv, ff, tree = surface(o)
            pairs = tree.overlap(body_tree)
            local = [(i, j) for i, j in pairs if any(int(v) in support for v in ff[i])]
            witness = []
            for triangle in ([598, 725, 1022], [630, 843, 1091]) if config['region'] == 'cloth' else ([51, 727, 229],):
                p = vv[triangle].mean(0); q, normal, tri, dist = body_tree.find_nearest(Vector(p))
                witness.append({'sourceIDs': triangle, 'centroidLocalNormalDotM': float(np.dot(p - np.array(q), np.array(normal))), 'unsignedDistanceM': float(dist)})
            versions.append({'corrective': enabled, 'coefficients': values, 'localBodyContactPairs': len(local),
                'globalBodyContactPairs': len(pairs), 'firstLocalPairs': local[:12], 'witnesses': witness})
        review.append({'frame': index, 'timeS': driver['frames'][index]['timeS'], 'region': config['region'], 'versions': versions})
        print('LOCAL_CORRECTIVE_REVIEW', index, config['region'], [(r['localBodyContactPairs'], [w['centroidLocalNormalDotM'] for w in r['witnesses']]) for r in versions], flush=True)
        for name in config['keys']:
            o.data.shape_keys.key_blocks[name].value = 0

zero_shapes(); set_pose(0)
assert {r: signature(o) for r, o in objects.items()} == original_signatures
root['rockhopRiderSkinConditioned'] = 1; objects['boxers'].hide_render = True
bpy.ops.object.select_all(action='DESELECT')
for o in [root, rig, body, objects['cloth'], objects['jeans']]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'prototype.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'prototype.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = {'status': 'EXPERIMENTAL pose-space local corrective driver; not installed in player',
    'sourceMasterSHA256': source_hash, 'poseDriverSHA256': sha(driver_path), 'candidateMasterSHA256': sha(out / 'prototype.blend'),
    'candidateGLBSHA256': sha(out / 'prototype.glb'), 'configs': configs,
    'metric': 'sqrt(sum((2 acos(abs(dot(unit quaternion,current/center))))^2)) over listed native local joints',
    'blend': 'centers=[rest0]+authored frames; nearestdistance<1e-5 selects exact cardinal center; otherwise normalize inverse-distance^4 and discard rest zero coefficient',
    'limitation': 'Apply explicitly in diagnostic native/Three replay; exported GLB morph targets alone do not automate rig-angle coupling in player'}
(out / 'corrective-driver.json').write_text(json.dumps(controller, indent=2) + '\n')
report = {'status': 'UNACCEPTED small left-underarm/knee authored pose-volume prototype; moving review pending',
    'sourceMasterSHA256': source_hash, 'poseDriverSHA256': sha(driver_path), 'masterSHA256': sha(out / 'prototype.blend'),
    'GLBSHA256': sha(out / 'prototype.glb'), 'correctiveDriverSHA256': sha(out / 'corrective-driver.json'),
    'originalDataSignaturesUnchanged': original_signatures, 'construction': construction, 'review': review,
    'limits': ['Original body/pattern topology/UV/weights/rest silhouette unchanged; only local morph shape deltas added.',
        'Local nearest-normal evidence is not complete signed clearance. Global/right side/outside support defects remain.',
        'Support5graph rings,3full+2smoothfade;12mm sleeve14mm knee authored posed volume40mm cap; no parameter sweep.',
        'Cardinal rig-angle blend is a prototype, needs matched played before/after and held-out qualification.',
        'No protected identity/hood graft, normal player or device/bike-supported motion acceptance; root alone judges.']}
assert sha(source) == source_hash
(evidence / 'prototype.json').write_text(json.dumps(report, indent=2) + '\n')
print('LOCAL_CORRECTIVE_RESULT', report['status'], report['GLBSHA256'], flush=True)
