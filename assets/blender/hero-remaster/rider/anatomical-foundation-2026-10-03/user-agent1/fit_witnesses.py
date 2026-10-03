"""Locate dressed-layer contact and seam-weight witnesses at root-reviewed times."""
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
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, driver_path, out = map(lambda s: Path(s).resolve(), [a.source, a.driver, a.out])
out.mkdir(parents=True, exist_ok=True)
driver = json.loads(driver_path.read_text())
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}


def weights(obj, vid):
    return {obj.vertex_groups[g.group].name: g.weight for g in obj.data.vertices[vid].groups
            if g.weight > 0 and obj.vertex_groups[g.group].name in rig.data.bones}


def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vv = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    ff = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return vv, ff, BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)


seams = []
for region, obj in objects.items():
    edge_counts = {}
    for f in obj.data.polygons:
        ids = list(f.vertices)
        for i, j in zip(ids, ids[1:] + ids[:1]):
            key = tuple(sorted([i, j]))
            edge_counts[key] = edge_counts.get(key, 0) + 1
    edges = {e for e, n in edge_counts.items() if n == 1}
    while edges:
        edge = min(edges)
        ids, todo = set(edge), list(edge)
        edges.remove(edge)
        while todo:
            i = todo.pop()
            attached = [e for e in edges if i in e]
            for e in attached:
                edges.remove(e)
                for j in e:
                    if j not in ids:
                        ids.add(j)
                        todo.append(j)
        ids = sorted(ids)
        verts = np.array([obj.data.vertices[i].co for i in ids])
        mass = {}
        for i in ids:
            for n, w in weights(obj, i).items():
                mass[n] = mass.get(n, 0) + w
        seams.append({'region': region, 'nativeVertexIDs': ids,
            'restBlenderLocalBoundsM': [verts.min(axis=0).tolist(), verts.max(axis=0).tolist()],
            'jointMass': mass})

rows = []
for index in [0, 112, 144, 240]:
    frame = driver['frames'][index]
    for name, trs in frame['poseBasisBlender'].items():
        pb = rig.pose.bones[name]
        pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
    bpy.context.view_layer.update()
    surfaces = {n: surface(obj) for n, obj in objects.items()}
    for left, right in [('cloth', 'body'), ('jeans', 'body'), ('boxers', 'jeans'), ('cloth', 'jeans')]:
        lv, lf, lb = surfaces[left]
        rv, rf, rb = surfaces[right]
        pairs = lb.overlap(rb)
        nearest = []
        for vid, p in enumerate(lv):
            q, normal, triangle, distance = rb.find_nearest(Vector(p))
            dot = float((Vector(p) - q).dot(normal))
            if dot < -1e-5:
                nearest.append({'leftNativeID': vid, 'rightTriangle': triangle,
                    'normalDotM': dot, 'unsignedDistanceM': float(distance),
                    'positionBlenderWorldM': p.tolist(), 'weights': weights(objects[left], vid)})
        nearest.sort(key=lambda r: r['normalDotM'])
        witnesses = []
        for i, j in pairs[:30]:
            witnesses.append({'leftTriangle': i, 'rightTriangle': j,
                'leftNativeIDs': lf[i].tolist(), 'rightNativeIDs': rf[j].tolist(),
                'leftCentroidBlenderWorldM': lv[lf[i]].mean(axis=0).tolist(),
                'rightCentroidBlenderWorldM': rv[rf[j]].mean(axis=0).tolist(),
                'leftWeights': [weights(objects[left], int(v)) for v in lf[i]]})
        rows.append({'frame': index, 'timeS': frame['timeS'], 'left': left, 'right': right,
            'triangleContactPairs': len(pairs), 'nearestNegativeNormalVertices': len(nearest),
            'worstLocalNormalWitnesses': nearest[:20], 'contactWitnesses': witnesses})
report = {'status': 'UNACCEPTED focused garment-fit witnesses; root reviewed frames112/144/240',
    'masterSHA256': source_hash, 'driverSHA256': hashlib.sha256(driver_path.read_bytes()).hexdigest(),
    'seams': seams, 'rows': rows,
    'limits': ['Nearest-normal dot is local, not certified globally signed penetration.',
        'Four focused frames locate defects, not all-time clearance.',
        'Native movie hides boxers while the exported diagnostic includes them; both facts preserved.',
        'No isolation/recoloring/source repair applied; head remains native fitting control.']}
(out / 'fit-witnesses.json').write_text(json.dumps(report, indent=2) + '\n')
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
print('FIT_WITNESSES', [(r['frame'], r['left'], r['right'], r['triangleContactPairs'],
    min([w['normalDotM'] for w in r['worstLocalNormalWitnesses']], default=0)) for r in rows], flush=True)
print('SEAMS', [(s['region'], len(s['nativeVertexIDs']), s['restBlenderLocalBoundsM'], s['jointMass']) for s in seams], flush=True)
