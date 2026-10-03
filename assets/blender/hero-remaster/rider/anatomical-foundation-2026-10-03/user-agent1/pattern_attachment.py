"""One directed garment topology/body-attachment experiment, not accepted art."""
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
for name in ['source', 'driver', 'out', 'evidence']:
    ap.add_argument('--' + name, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, dp, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'attachment.blend').exists():
    raise RuntimeError('Frozen experiment exists; no topology/attachment parameter loop')
driver = json.loads(dp.read_text()); source_sha = sha(source)
assert source_sha == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
body = objects['body']
def pose(index):
    for name, trs in driver['frames'][index]['poseBasisBlender'].items():
        pb = rig.pose.bones[name]
        pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
    bpy.context.view_layer.update()
def surface(o):
    oo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = oo.to_mesh(); m.calc_loop_triangles()
    vv = np.array([oo.matrix_world @ v.co for v in m.vertices]); ff = np.array([list(t.vertices) for t in m.loop_triangles], dtype=np.int32)
    oo.to_mesh_clear(); return vv, ff, BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)
def body_signature():
    return hashlib.sha256(json.dumps({'v': [list(v.co) for v in body.data.vertices],
        'f': [list(f.vertices) for f in body.data.polygons],
        'w': [[(g.group, g.weight) for g in v.groups] for v in body.data.vertices]}).encode()).hexdigest()
def boundaries(mesh):
    counts = {}
    for p in mesh.polygons:
        ids = list(p.vertices)
        for i, j in zip(ids, ids[1:] + ids[:1]):
            edge = tuple(sorted((i, j))); counts[edge] = counts.get(edge, 0) + 1
    edges = {e for e, c in counts.items() if c == 1}; loops = []
    while edges:
        edge = min(edges); edges.remove(edge); ids = set(edge); todo = list(edge)
        while todo:
            i = todo.pop()
            for e in [e for e in edges if i in e]:
                edges.remove(e)
                for j in e:
                    if j not in ids:
                        ids.add(j); todo.append(j)
        loops.append(sorted(ids))
    return loops

def barycentric(point, triangle):
    a, b, c = triangle; u, v, w = b - a, c - a, point - a
    uu, uv, vv, wu, wv = u @ u, u @ v, v @ v, w @ u, w @ v
    denom = uu * vv - uv * uv
    assert abs(denom) > 1e-16
    beta, gamma = (vv * wu - uv * wv) / denom, (uu * wv - uv * wu) / denom
    values = np.maximum([1 - beta - gamma, beta, gamma], 0)
    return values / sum(values)

pose(0); original_body = body_signature(); bv, bf, body_rest_tree = surface(body)
deform_names = {bone.name for bone in rig.data.bones if bone.use_deform}
body_weights = [{body.vertex_groups[g.group].name: g.weight for g in v.groups
    if g.weight > 0 and body.vertex_groups[g.group].name in deform_names} for v in body.data.vertices]
assert all(abs(sum(w.values()) - 1) < 1e-6 for w in body_weights)
rows = []
for region in ['cloth', 'jeans']:
    o = objects[region]; original_v, original_f, original_bvh = surface(o)
    original_loops = boundaries(o.data)
    original_hem = min(original_loops, key=lambda ids: np.mean([o.data.vertices[i].co.z for i in ids])) if region == 'cloth' else None
    hem_height = max(o.data.vertices[i].co.z for i in original_hem) if original_hem else None
    # Explicit conforming triangle splits preserve every selected edge midpoint.
    # BMesh BEAUTY retriangulation reconnected ten original long diagonals.
    old_mesh = o.data; old_mesh.calc_loop_triangles()
    vertices = [np.array(v.co) for v in old_mesh.vertices]
    faces = [list(t.vertices) for t in old_mesh.loop_triangles]
    face_materials = [old_mesh.polygons[t.polygon_index].material_index for t in old_mesh.loop_triangles]
    uv_names = [layer.name for layer in old_mesh.uv_layers]
    face_uv = [{layer.name: [np.array(layer.data[i].uv) for i in t.loops] for layer in old_mesh.uv_layers}
               for t in old_mesh.loop_triangles]
    history = []
    for step in range(6):
        edges = {tuple(sorted((i, j))) for f in faces for i, j in zip(f, f[1:] + f[:1])}
        lengths = {edge: np.linalg.norm(vertices[edge[0]] - vertices[edge[1]]) for edge in edges}
        long_edges = sorted(edge for edge in edges if lengths[edge] > .01500001)
        history.append({'pass': step, 'vertices': len(vertices), 'longEdges': len(long_edges), 'maxEdgeM': float(max(lengths.values()))})
        print('REFINEMENT', region, history[-1], flush=True)
        if not long_edges:
            break
        midpoints = {}
        for i, j in long_edges:
            midpoints[(i, j)] = len(vertices); vertices.append((vertices[i] + vertices[j]) / 2)
        new_faces, new_uv, new_mats = [], [], []
        for f, uv, mat in zip(faces, face_uv, face_materials):
            mids = [midpoints.get(tuple(sorted((f[i], f[(i + 1) % 3])))) for i in range(3)]
            count = sum(m is not None for m in mids)
            uv_lookup = {name: dict(zip(f, values)) for name, values in uv.items()}
            for i, mid in enumerate(mids):
                if mid is not None:
                    for name, values in uv.items():
                        uv_lookup[name][mid] = (values[i] + values[(i + 1) % 3]) / 2
            if count == 0:
                children = [f]
            elif count == 3:
                aa, bb, cc = f; ab, bc, ca = mids
                children = [[aa, ab, ca], [ab, bb, bc], [ca, bc, cc], [ab, bc, ca]]
            else:
                i = next(i for i in range(3) if mids[i] is not None and (count == 1 or mids[(i + 1) % 3] is not None))
                aa, bb, cc = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
                ab, bc = mids[i], mids[(i + 1) % 3]
                children = [[aa, ab, cc], [ab, bb, cc]] if count == 1 else [[aa, ab, cc], [ab, bc, cc], [ab, bb, bc]]
            for child in children:
                new_faces.append(child); new_mats.append(mat)
                new_uv.append({name: [lookup[vid] for vid in child] for name, lookup in uv_lookup.items()})
        faces, face_uv, face_materials = new_faces, new_uv, new_mats
        if len(vertices) > 20000:
            raise RuntimeError('Fixed20k garment vertex budget exceeded')
    else:
        final_max = max(np.linalg.norm(vertices[i] - vertices[j]) for f in faces for i, j in zip(f, f[1:] + f[:1]))
        if final_max > .01500001:
            raise RuntimeError(f'Fixed6 refinement passes exceeded: {region} final edge{final_max}')
    mesh = bpy.data.meshes.new(o.name + ' conforming attachment pattern')
    mesh.from_pydata(vertices, [], faces)
    for material in old_mesh.materials:
        mesh.materials.append(material)
    for face, mat in zip(mesh.polygons, face_materials):
        face.material_index = mat; face.use_smooth = True
    for name in uv_names:
        layer = mesh.uv_layers.new(name=name)
        for face, uv in zip(mesh.polygons, face_uv):
            for loop, value in zip(face.loop_indices, uv[name]):
                layer.data[loop].uv = value
    o.data = mesh; o.data.update()
    loops = boundaries(o.data); assert len(loops) == len(original_loops)
    inv = o.matrix_world.inverted()
    # New vertices have explicit pattern ancestry; interpolated old source-ID is invalid.
    if o.data.attributes.get('_SOURCE_ID'):
        o.data.attributes.remove(o.data.attributes['_SOURCE_ID'])
    attrs = {n: o.data.attributes.new(n, 'FLOAT', 'POINT') for n in ['_PATTERN_ID', '_SOURCE_TRI', '_BARY_A', '_BARY_B']}
    for group in list(o.vertex_groups):
        group.remove(list(range(len(o.data.vertices))))
    new_groups = {b.name: o.vertex_groups.get(b.name) or o.vertex_groups.new(name=b.name) for b in rig.data.bones if b.use_deform}
    shifts, discarded, ancestry_residual, anchored = [], [], [], 0
    weights_blob = []
    for vertex in o.data.vertices:
        p = np.array(o.matrix_world @ vertex.co)
        oldq, oldn, oldtri, olddist = original_bvh.find_nearest(Vector(p))
        oldbary = barycentric(np.array(oldq), original_v[original_f[oldtri]])
        ancestry_residual.append(float(np.linalg.norm(oldbary @ original_v[original_f[oldtri]] - p)))
        attrs['_PATTERN_ID'].data[vertex.index].value = vertex.index
        attrs['_SOURCE_TRI'].data[vertex.index].value = oldtri
        attrs['_BARY_A'].data[vertex.index].value = oldbary[0]
        attrs['_BARY_B'].data[vertex.index].value = oldbary[1]
        q, normal, tri, distance = body_rest_tree.find_nearest(Vector(p)); q, normal = np.array(q), np.array(normal)
        bary = barycentric(q, bv[bf[tri]])
        weights = {}
        for bid, b in zip(bf[tri], bary):
            for name, w in body_weights[bid].items():
                weights[name] = weights.get(name, 0) + float(w * b)
        # Diagnosed lowest shirt ring must attach to the pelvis, not either thigh.
        influence = max(0, min(1, (hem_height + .025 - vertex.co.z) / .025)) if hem_height is not None else 0
        if influence > 0:
            weights = {n: w * (1 - influence) for n, w in weights.items()}
            weights['pelvis'] = weights.get('pelvis', 0) + influence; anchored += 1
        ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
        total = sum(w for _, w in ranked[:4]); discarded.append(sum(w for _, w in ranked[4:]))
        kept = [(n, w / total) for n, w in ranked[:4] if w > 1e-10]
        for name, w in kept:
            new_groups[name].add([vertex.index], w, 'REPLACE')
        weights_blob.append(kept)
        # Single local-normal exterior correction at rest, not a multi-pose offset fit.
        target = q + normal * .004 if np.dot(p - q, normal) < 0 or distance < .004 else p
        shifts.append(float(np.linalg.norm(target - p))); vertex.co = inv @ Vector(target)
    o.data.update()
    rows.append({'region': region, 'originalVertices': len(original_v), 'vertices': len(o.data.vertices),
        'originalTriangles': len(original_f), 'triangles': len(o.data.polygons),
        'originalOpeningCount': len(original_loops), 'openingCount': len(loops), 'openingVertexCounts': [len(x) for x in loops],
        'refinement': history, 'maxRestCorrectionM': max(shifts), 'correctedVertices': sum(x > 1e-10 for x in shifts),
        'hemAnchorTransitionVertices': anchored, 'hemHeightLocalM': hem_height,
        'maximumDiscardedBodyTriangleWeight': max(discarded), 'originalPatternMaxAncestryResidualM': max(ancestry_residual),
        'weightsSHA256': hashlib.sha256(json.dumps(weights_blob).encode()).hexdigest()})
    print('ATTACHMENT_PATTERN', rows[-1], flush=True)
assert body_signature() == original_body
review, failures = [], []
for index in [0, 112, 144, 240, 24, 48, 72, 96, 120, 168, 192, 216]:
    pose(index); _, _, tree_body = surface(body)
    for region in ['cloth', 'jeans']:
        vv, ff, tree = surface(objects[region]); pairs = tree.overlap(tree_body)
        self_pairs = [(i, j) for i, j in tree.overlap(tree) if i < j and not set(ff[i]).intersection(ff[j])]
        review.append({'frame': index, 'timeS': driver['frames'][index]['timeS'], 'region': region,
            'bodyTriangleContactPairs': len(pairs), 'nonadjacentSelfPairs': len(self_pairs),
            'firstBodyPairs': pairs[:12], 'firstSelfPairs': self_pairs[:12]})
        if pairs or self_pairs:
            failures.append(f'{region} frame{index}: body{len(pairs)} self{len(self_pairs)}')
        print('ATTACHMENT_REVIEW', review[-1]['frame'], region, len(pairs), len(self_pairs), flush=True)
pose(0); objects['boxers'].hide_render = True; root['rockhopRiderSkinConditioned'] = 1
bpy.ops.object.select_all(action='DESELECT')
for obj in [root, rig, body, objects['cloth'], objects['jeans']]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'attachment.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'attachment.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=False, export_attributes=True, export_extras=True)
assert body_signature() == original_body and sha(source) == source_sha
report = {'status': 'REJECTED directed attachment experiment' if failures else 'UNACCEPTED sampled attachment candidate',
    'sourceMasterSHA256': source_sha, 'driverSHA256': sha(dp), 'masterSHA256': sha(out / 'attachment.blend'),
    'GLBSHA256': sha(out / 'attachment.glb'), 'recipeSHA256': sha(__file__), 'bodySignatureUnchanged': original_body,
    'mechanism': '15mm pattern refinement; nearest native-body triangle barycentric top4 own-bind weights; 4mm local exterior rest correction; pelvis shirt-hem anchor with25mm transition',
    'patterns': rows, 'review': review, 'failures': failures,
    'limits': ['One fixed directed construction experiment; no parameter or body-donor escalation.',
        'Local rest normal is not certified complete-body signed distance; sampled triangle contacts reject before visual acceptance.',
        'New garment topology/weights/rest correction; original UVs interpolate, source ancestry explicitly stored before projection.',
        'Body/51bones/binds untouched, original openings retained; exact head/hood not integrated.',
        'No final art/device/bike-supported motion acceptance; root alone judges M0–M5.']}
(evidence / 'attachment.json').write_text(json.dumps(report, indent=2) + '\n')
print('ATTACHMENT_RESULT', report['status'], failures, flush=True)
