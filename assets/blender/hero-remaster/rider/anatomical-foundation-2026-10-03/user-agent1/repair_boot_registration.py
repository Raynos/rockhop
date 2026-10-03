"""One bounded accessory registration repair, preserving appearance01 immutable."""
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
for n in ['source', 'donor', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, donor, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'donor', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {str(p): sha(p) for p in [source, donor]}
assert pins[str(donor)] == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'rider.blend').exists():
    raise RuntimeError('Frozen repair already exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
boots = bpy.data.objects['Registered boots from bounded foot accessory regions']
raw = donor.read_bytes(); length = int.from_bytes(raw[12:16], 'little'); doc = json.loads(raw[20:20 + length]); binary = raw[28 + length:]
def acc(i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; c = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = np.dtype({5126: '<f4', 5123: '<u2', 5121: '<u1', 5125: '<u4'}[a['componentType']])
    return np.ndarray((a['count'], c), dtype=dt, buffer=binary, offset=v.get('byteOffset', 0) + a.get('byteOffset', 0), strides=(v.get('byteStride', c * dt.itemsize), dt.itemsize)).copy()
p = doc['meshes'][0]['primitives'][0]; pos, joints, weights = [acc(p['attributes'][n]) for n in ['POSITION', 'JOINTS_0', 'WEIGHTS_0']]
names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]; foot_ids = [names.index(n) for n in ['foot.L', 'foot.R']]
valid = np.sum(weights * np.isin(joints, foot_ids), axis=1) >= .45
triangles = acc(p['indices']).reshape(-1, 3); used = np.unique(triangles[np.all(valid[triangles], axis=1)])
assert len(used) == len(boots.data.vertices)
points = np.column_stack([pos[:, 0] - .65, -pos[:, 2], pos[:, 1]]).astype(np.float64)
body.data.calc_loop_triangles(); bv = np.array([v.co[:] for v in body.data.vertices]); bf = np.array([t.vertices[:] for t in body.data.loop_triangles])
tree = BVHTree.FromPolygons([Vector(v) for v in bv], bf.tolist(), all_triangles=True)
body_weights = [{body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0 and body.vertex_groups[g.group].name in rig.data.bones} for v in body.data.vertices]
body_mass = lambda side: np.array([sum(value for name, value in w.items() if name in ['foot.' + side, 'ball.' + side]) for w in body_weights])
# Match anatomical foot bounds in ground axes. Full source-bone rotations were
# inappropriate: old/new foot tails encode different toe/sole direction.
registration = []; fitted = points[used].copy()
for side, foot_id in zip(['L', 'R'], foot_ids):
    source_mass = np.sum(weights[used] * (joints[used] == foot_id), axis=1); mask = source_mass > .25
    native = bv[(body_mass(side) > .55) & (bv[:, 2] < .2)]
    assert len(native) > 50
    source_bounds = np.array([fitted[mask].min(0), fitted[mask].max(0)])
    target_bounds = np.array([native.min(0), native.max(0)])
    target_bounds[0, :2] -= .004; target_bounds[1, :2] += .004
    target_bounds[0, 2] = 0.; target_bounds[1, 2] = max(.145, target_bounds[1, 2] + .006)
    scales = (target_bounds[1] - target_bounds[0]) / (source_bounds[1] - source_bounds[0])
    fitted[mask] = (fitted[mask] - source_bounds[0]) * scales + target_bounds[0]
    registration.append({'side': side, 'sourceBoundsNativeM': source_bounds.tolist(), 'targetBoundsNativeM': target_bounds.tolist(), 'axisScales': scales.tolist(), 'vertices': int(mask.sum())})
# One local skin envelope adjustment; this is construction, not a solver sweep.
# The ground-facing sole is held at z0 rather than projected through the floor.
maximum_correction = 0.; corrections = 0
for i, point in enumerate(fitted):
    q, normal, tri, distance = tree.find_nearest(Vector(point)); q, normal = np.array(q), np.array(normal)
    dot = float(np.dot(point - q, normal))
    if dot < .0025 and point[2] > .006:
        delta = normal * (.0025 - dot)
        if np.linalg.norm(delta) > .025:
            raise RuntimeError('Fixed25mm bounded accessory envelope exceeded')
        fitted[i] += delta; fitted[i, 2] = max(0, fitted[i, 2]); maximum_correction = max(maximum_correction, float(np.linalg.norm(delta))); corrections += 1
    boots.data.vertices[i].co = fitted[i]
# New bind weights always come from canonical body, not old donor joints.
for group in boots.vertex_groups:
    group.remove(list(range(len(fitted))))
for i, point in enumerate(fitted):
    q, normal, tri, distance = tree.find_nearest(Vector(point)); ids = bf[tri]
    matrix = np.column_stack([bv[ids[1]] - bv[ids[0]], bv[ids[2]] - bv[ids[0]]]); yz = np.linalg.lstsq(matrix, np.array(q) - bv[ids[0]], rcond=None)[0]
    factors = np.clip([1 - sum(yz), yz[0], yz[1]], 0, 1); factors /= sum(factors); row = {}
    for old, factor in zip(ids, factors):
        for name, value in body_weights[old].items():
            row[name] = row.get(name, 0) + value * factor
    row = sorted(row.items(), key=lambda p: -p[1])[:4]; total = sum(w for n, w in row)
    for name, w in row:
        boots.vertex_groups[name].add([i], w / total, 'REPLACE')
boots.data.update()
# Honour original metallicFactor0: linking texture B without multiplying the
# factor accidentally made the first leather shader metallic. Keep texture G.
leather = bpy.data.materials['Appearance exact donor material 1']; bs = leather.node_tree.nodes['Principled BSDF']
for link in list(bs.inputs['Metallic'].links):
    leather.node_tree.links.remove(link)
bs.inputs['Metallic'].default_value = 0
for o in bpy.data.objects:
    o.select_set(False)
root = bpy.data.objects['Foundation file frame, game x0.65']; root['rockhopAppearanceCandidate'] = 'unaccepted appearance02 bounded boot registration'
selected = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render] + [root, rig]
for o in selected:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'rider.glb'), export_format='GLB', use_selection=True, export_yup=True,
    export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = json.loads((source.parent / 'corrective-driver.json').read_text()); controller.update(status='UNACCEPTED appearance02, same liked local corrective controller',
    candidateMasterSHA256=sha(out / 'rider.blend'), candidateGLBSHA256=sha(out / 'rider.glb'), parentAppearanceMasterSHA256=sha(source))
(out / 'corrective-driver.json').write_text(json.dumps(controller, indent=2) + '\n')
assert pins == {str(p): sha(p) for p in [source, donor]}
report = {'status': 'UNACCEPTED bounded accessory ground-axis registration repair; moving review pending', 'pins': pins,
    'masterSHA256': sha(out / 'rider.blend'), 'GLBSHA256': sha(out / 'rider.glb'), 'recipeSHA256': sha(__file__), 'registration': registration,
    'bootBoundsNativeM': [fitted.min(0).tolist(), fitted.max(0).tolist()], 'envelopeCorrections': corrections, 'maximumEnvelopeCorrectionM': maximum_correction,
    'leatherMetallicFactor': 0, 'limits': ['Only boot rest registration/rebinding and shared leather metallicFactor fidelity change from appearance01; root metadata names derivative.',
        'Protected head, body, native cloth/jeans, hood/glove geometry, UV/images and liked local correctives retained.',
        'Vertex normal envelope is not complete triangle/signed dynamic clearance; boot shaft/sole and ankle fit still need played review.',
        'No normal-player promotion, mobile LOD or root art acceptance.']}
(evidence / 'registration-repair.json').write_text(json.dumps(report, indent=2) + '\n'); print('BOOT_REGISTRATION_REPAIRED', report['bootBoundsNativeM'], report['GLBSHA256'], flush=True)
