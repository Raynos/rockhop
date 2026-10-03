"""Measure every native FK/ankle sample and freeze matched old/new wearable streams."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'driver', 'expanded', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, dp, ep, out = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'expanded', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, dp, ep]}
out.mkdir(parents=True, exist_ok=True)
if (out/'motion.json').exists():
    raise RuntimeError('Frozen footwear motion exists')
start = time.monotonic(); bpy.ops.wm.open_mainfile(filepath=str(source)); driver, expanded = json.loads(dp.read_text()), json.loads(ep.read_text())
rig = bpy.data.objects['Independent anatomical foundation rig']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
objects = {'old': bpy.data.objects['Registered boots from bounded foot accessory regions'], 'new': bpy.data.objects['Complete worn boot volume on own canonical feet'],
    'bodyVisible': bpy.data.objects['Canonical body with hidden head interface'], 'jeans': bpy.data.objects['Separate fitted native trousers control']}
cloth = bpy.data.objects['Sewn clean hoodie with dropped hood']
regions = {}; streams = {n: [] for n in objects}; samples = []; metrics = []
for name, o in objects.items():
    faces = [p for p in o.data.polygons if name in ['old', 'new'] or max(o.data.vertices[i].co.z for i in p.vertices) < .320]
    ids = sorted({i for p in faces for i in p.vertices}); lookup = {old: new for new, old in enumerate(ids)}
    regions[name] = {'object': o.name, 'nativeVertexIDs': ids, 'polygonIDs': [p.index for p in faces], 'faces': [[lookup[i] for i in p.vertices] for p in faces],
        'materialSlots': [p.material_index for p in faces], 'UVLayers': [[[list(l.data[k].uv) for k in p.loop_indices] for p in faces] for l in o.data.uv_layers]}
witnesses = {side: [v.index for v in body.data.vertices if v.co.z < .125 and v.co.y * sign > .075] for side, sign in [('L', -1), ('R', 1)]}
def evaluated(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = e.to_mesh(); mesh.calc_loop_triangles()
    v = np.array([e.matrix_world @ p.co for p in mesh.vertices]); f = [list(t.vertices) for t in mesh.loop_triangles]
    slots = [mesh.polygons[t.polygon_index].material_index for t in mesh.loop_triangles]; e.to_mesh_clear()
    return v, f, slots
def proxy_tree(v, faces):
    counts = {}
    for face in faces:
        for i, j in zip(face, face[1:]+face[:1]):
            key = tuple(sorted((i, j))); counts[key] = counts.get(key, 0)+1
    # Weld seam duplicates solely for the virtual closure classification.
    key_map = {}; welded = []; ids = []
    for p in v:
        key = tuple(np.round(p*1e6).astype(int))
        if key not in key_map:
            key_map[key] = len(welded); welded.append(p)
        ids.append(key_map[key])
    ff = [[ids[i] for i in face] for face in faces]; counts = {}
    for face in ff:
        for i, j in zip(face, face[1:]+face[:1]):
            key = tuple(sorted((i, j))); counts[key] = counts.get(key, 0)+1
    adjacency = {}
    for (i, j), count in counts.items():
        if count == 1:
            adjacency.setdefault(i, set()).add(j); adjacency.setdefault(j, set()).add(i)
    remaining = set(adjacency); cap_vertices = list(welded)
    while remaining:
        first = remaining.pop(); loop = [first]; previous = None; current = first
        for _ in range(len(adjacency)+1):
            choices = adjacency[current]-({previous} if previous is not None else set())
            nxt = next((n for n in choices if n == first or n in remaining), None)
            if nxt is None:
                raise RuntimeError('Virtual cuff closure branch; no enclosure guess')
            if nxt == first:
                break
            remaining.remove(nxt); loop.append(nxt); previous, current = current, nxt
        center = np.mean([welded[i] for i in loop], axis=0); center_id = len(cap_vertices); cap_vertices.append(center)
        ff.extend([[loop[i], loop[(i+1)%len(loop)], center_id] for i in range(len(loop))])
    return BVHTree.FromPolygons([Vector(p) for p in cap_vertices], ff, all_triangles=True)
def ray_inside(tree, point, direction):
    p = Vector(point); hits = 0
    for _ in range(100):
        hit, normal, index, distance = tree.ray_cast(p, direction, 3.)
        if hit is None:
            return bool(hits % 2)
        hits += 1; p = hit + direction*1e-6
    raise RuntimeError('Ambiguous ray classification')
poses = []
for frame in driver['frames']:
    poses.append({'phase': 'original FK', 'driverFrame': frame['index'], 'timeS': frame['timeS'], 'pose': frame['poseBasisBlender']})
for i in range(1, 97):
    pose = json.loads(json.dumps(driver['frames'][0]['poseBasisBlender'])); phase = i/96*2*math.pi
    for side in ['L', 'R']:
        for bone_name, angle in [('foot.'+side, math.sin(phase)*math.radians(20)), ('ball.'+side, math.sin(phase*2)*math.radians(15))]:
            axis = rig.data.bones[bone_name].matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))
            pose[bone_name]['quaternionWXYZ'] = list(Quaternion(axis.normalized(), angle))
    poses.append({'phase': 'explicit ankle20deg/toe15deg', 'driverFrame': None, 'timeS': 11+i/48, 'pose': pose})
for index, frame in enumerate(poses):
    if time.monotonic()-start > 300:
        raise RuntimeError('Bounded300second own footwear measurement cap; no foreign job affected')
    for name, trs in frame['pose'].items():
        pb = rig.pose.bones[name]; pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
    for config in expanded['configs']:
        o = cloth if config['region'] == 'cloth' else objects['jeans']
        for name in config['keys']:
            o.data.shape_keys.key_blocks[name].value = expanded['frames'][frame['driverFrame']]['coefficients'][config['region']][name] if frame['driverFrame'] is not None else 0.
    bpy.context.view_layer.update(); bv, bf, bs = evaluated(body); body_tree = BVHTree.FromPolygons([Vector(p) for p in bv], bf, all_triangles=True)
    record = {'index': index, 'phase': frame['phase'], 'driverFrame': frame['driverFrame'], 'timeS': frame['timeS'], 'versions': {}}
    vertices = {}
    for name in ['old', 'new']:
        vv, ff, slots = evaluated(objects[name]); vertices[name] = vv
        parts = [('appearance', ff)] if name == 'old' else [('upper', [f for f,s in zip(ff,slots) if s == 0]), ('outsole', [f for f,s in zip(ff,slots) if s == 1])]
        rows = []
        for part, faces in parts:
            tree = BVHTree.FromPolygons([Vector(p) for p in vv], faces, all_triangles=True); pairs = tree.overlap(body_tree)
            rows.append({'part': part, 'bodyTriangleContactPairs': len(pairs), 'firstPairs': pairs[:4]})
        record['versions'][name] = {'parts': rows, 'finite': bool(np.isfinite(vv).all())}
        if index % 4 == 0:
            upper = ff if name == 'old' else [f for f,s in zip(ff,slots) if s == 0]; closed = proxy_tree(vv, upper); coverage = {}
            for side, ids in witnesses.items():
                outside = []
                for i in ids:
                    votes = [ray_inside(closed, bv[i], Vector(d)) for d in [(1, 0, 0), (0, 1, 0), (0, 0, 1)]]
                    if sum(votes) < 2:
                        outside.append(i)
                coverage[side] = {'testedNativeBodyVertices': len(ids), 'outsideMajorityRayProxy': len(outside), 'firstOutsideBodyIDs': outside[:12]}
            record['versions'][name]['sampledEnclosureProxy'] = coverage
    metrics.append(record)
    if index % 4 == 0:
        for name, o in objects.items():
            vv = vertices[name] if name in vertices else evaluated(o)[0]
            streams[name].append(vv[regions[name]['nativeVertexIDs']])
        samples.append({'displayFrame': len(samples), 'measurementIndex': index, 'timeS': frame['timeS'], 'phase': frame['phase']})
    if index % 48 == 0:
        print('FOOTWEAR_MEASURED', index, record['versions'], flush=True)
np.savez_compressed(out/'streams.npz', **{name: np.array(v) for name,v in streams.items()})
assert pins == {str(p): sha(p) for p in [source, dp, ep]}
report = {'status': 'UNACCEPTED matched old/new footwear native movement and wearer proxies; parent judges', 'pins': pins,
    'recipeSHA256': sha(__file__), 'streamsSHA256': sha(out/'streams.npz'), 'nativeRegions': regions, 'frames': metrics, 'sampledFrames': samples,
    'measuredFrames': len(metrics), 'FPS': 12, 'elapsedS': time.monotonic()-start,
    'limits': ['All529 original48Hz FK samples plus96 explicit ankle/toe samples measured; renderer plays every fourth sample.',
        'Virtual cuff closure and three-axis majority rays classify fixed below125mm foot witnesses; not complete signed clearance or anatomical collar-fit acceptance.',
        'Native source08 retains old05 boot control; old/new share exact body/rig/pose/controller. No recoloring hides coverage failures.',
        'Footwear-only synthetic bike-free test, not supported game peg contact or live collision response. Parent judges moving wearable form; all garments remain unaccepted.']}
(out/'motion.json').write_text(json.dumps(report, indent=2)+'\n'); print('FOOTWEAR_MOTION_READY', len(metrics), len(samples), report['elapsedS'], flush=True)
