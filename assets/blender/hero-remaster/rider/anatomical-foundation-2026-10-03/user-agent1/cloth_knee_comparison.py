"""One bounded clean knee-pattern collision comparison, never runtime promotion."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'driver', 'controller', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, dp, cp, out = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'controller', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, dp, cp]}
out.mkdir(parents=True, exist_ok=True)
if (out / 'comparison.json').exists():
    raise RuntimeError('Frozen collision trial exists; no parameter sweep')
start = time.monotonic(); bpy.ops.wm.open_mainfile(filepath=str(source))
driver, controller = json.loads(dp.read_text()), json.loads(cp.read_text())
rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; jeans = bpy.data.objects['Separate fitted native trousers control']
config = next(c for c in controller['configs'] if c['region'] == 'jeans')
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
for key in jeans.data.shape_keys.key_blocks:
    key.value = 0
bpy.context.view_layer.update()
base = np.array([v.co[:] for v in jeans.data.vertices]); jeans.data.calc_loop_triangles(); source_tri = np.array([t.vertices[:] for t in jeans.data.loop_triangles])
source_tree = BVHTree.FromPolygons([Vector(v) for v in base], source_tri.tolist(), all_triangles=True)
seed = set(config['supportIDs']); selected_faces = [i for i, tri in enumerate(source_tri) if any(int(v) in seed for v in tri)]
triangles = source_tri[selected_faces]; used = np.unique(triangles); reverse = {int(old): new for new, old in enumerate(used)}
mesh = bpy.data.meshes.new('One clean local knee pattern'); mesh.from_pydata(base[used].tolist(), [], [[reverse[int(i)] for i in t] for t in triangles]); mesh.update()
layer = mesh.uv_layers.new(name='UVMap')
for face, old_face in zip(mesh.polygons, selected_faces):
    old = jeans.data.loop_triangles[old_face]
    for loop, old_loop in zip(face.loop_indices, old.loops):
        layer.data[loop].uv = jeans.data.uv_layers.active.data[old_loop].uv
bm = bmesh.new(); bm.from_mesh(mesh); bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True); bm.to_mesh(mesh); bm.free(); mesh.update()
patch = bpy.data.objects.new('Qualified knee pattern skinned corrective control', mesh); bpy.context.collection.objects.link(patch); patch.parent = root
for b in rig.data.bones:
    patch.vertex_groups.new(name=b.name)
# Exact source-surface barycentric fields are assigned BEFORE construction gap.
def bary(point, points):
    matrix = np.column_stack([points[1] - points[0], points[2] - points[0]]); yz = np.linalg.lstsq(matrix, point - points[0], rcond=None)[0]
    weights = np.clip([1 - sum(yz), yz[0], yz[1]], 0, 1); return weights / sum(weights)
fields = []; original_weights = [{jeans.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0} for v in jeans.data.vertices]
for v in mesh.vertices:
    q, normal, tri, distance = source_tree.find_nearest(v.co); ids = source_tri[tri]; factors = bary(np.array(q), base[ids]); fields.append((ids, factors)); weights = {}
    for old, factor in zip(ids, factors):
        for name, weight in original_weights[old].items():
            weights[name] = weights.get(name, 0) + factor * weight
    weights = sorted(weights.items(), key=lambda p: -p[1])[:4]; total = sum(w for n, w in weights)
    for name, weight in weights:
        patch.vertex_groups[name].add([v.index], weight / total, 'REPLACE')
body.data.calc_loop_triangles(); bv = np.array([v.co[:] for v in body.data.vertices]); bf = np.array([t.vertices[:] for t in body.data.loop_triangles]); tree = BVHTree.FromPolygons([Vector(v) for v in bv], bf.tolist(), all_triangles=True)
construction = []
for v in mesh.vertices:
    q, normal, tri, distance = tree.find_nearest(v.co); dot = float((v.co - q).dot(normal)); displacement = max(0, .006 - dot)
    if displacement > .012:
        raise RuntimeError('Fixed12mm local clean-rest construction allowance exceeded')
    v.co += normal * displacement; construction.append(displacement)
mesh.update(); patch.shape_key_add(name='Basis')
for name in config['keys']:
    original = jeans.data.shape_keys.key_blocks[name]; delta = np.array([original.data[i].co[:] for i in range(len(base))]) - base
    key = patch.shape_key_add(name=name)
    for i, (ids, weights) in enumerate(fields):
        key.data[i].co = mesh.vertices[i].co + Vector(weights @ delta[ids])
mesh.materials.append(jeans.data.materials[0])
for f in mesh.polygons:
    f.use_smooth = True
armature = patch.modifiers.new('Same own kinematic bind', 'ARMATURE'); armature.object = rig
mesh.calc_loop_triangles(); faces = np.array([t.vertices[:] for t in mesh.loop_triangles]); adjacency = [set() for _ in mesh.vertices]; counts = {}
for f in faces:
    for aa, bb in zip(f, np.roll(f, -1)):
        edge = tuple(sorted((int(aa), int(bb)))); counts[edge] = counts.get(edge, 0) + 1; adjacency[int(aa)].add(int(bb)); adjacency[int(bb)].add(int(aa))
boundary = {v for edge, count in counts.items() if count == 1 for v in edge}; neighbor = {j for i in boundary for j in adjacency[i]} - boundary
pins_group = patch.vertex_groups.new(name='Kinematic sewn boundary pins'); pins_group.add(sorted(boundary), 1., 'REPLACE'); pins_group.add(sorted(neighbor), .5, 'REPLACE')
physics = patch.copy(); physics.data = patch.data.copy(); physics.name = 'Same qualified knee pattern WITH cloth collision'; bpy.context.collection.objects.link(physics)
cloth = physics.modifiers.new('ONE bounded body/self collision trial', 'CLOTH'); settings = cloth.settings; settings.quality = 8; settings.mass = .3
settings.tension_stiffness = 50; settings.compression_stiffness = 50; settings.shear_stiffness = 5; settings.bending_stiffness = .5
settings.vertex_group_mass = pins_group.name; settings.pin_stiffness = 1.; settings.use_dynamic_mesh = True
cs = cloth.collision_settings; cs.use_collision = True; cs.distance_min = .001; cs.collision_quality = 8; cs.use_self_collision = True; cs.self_distance_min = .001
body.modifiers.new('Kinematic body collision surface', 'COLLISION'); body.collision.thickness_outer = .001; body.collision.thickness_inner = .001
cloth.point_cache.frame_start, cloth.point_cache.frame_end = 1, 49
scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, 49; scene.render.fps = 24
# Both controls share the same rest repair, UV, weights and pose-space key field.
def surface(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh(); m.calc_loop_triangles()
    v = np.array([e.matrix_world @ x.co for x in m.vertices]); f = np.array([t.vertices[:] for t in m.loop_triangles]); e.to_mesh_clear()
    return v, f, BVHTree.FromPolygons([Vector(p) for p in v], f.tolist(), all_triangles=True)
def clearance(o, body_tree):
    v, f, own = surface(o); samples = []
    for ids in f:
        tri = v[ids]; samples.extend([tri.mean(0), (tri[0]+tri[1])/2, (tri[1]+tri[2])/2, (tri[2]+tri[0])/2])
    local_dots, unsigned = [], []
    for p in list(v) + samples:
        q, normal, tri, distance = body_tree.find_nearest(Vector(p)); local_dots.append(float(np.dot(p - np.array(q), np.array(normal)))); unsigned.append(distance)
    contacts = own.overlap(body_tree)
    self_pairs = [(i,j) for i,j in own.overlap(own) if i < j and not set(f[i]) & set(f[j])]
    return {'bodyTriangleContactPairs': len(contacts), 'nonadjacentSelfContactPairs': len(self_pairs),
        'minimumSampledLocalNormalDotM': min(local_dots), 'minimumSampledUnsignedBodyDistanceM': min(unsigned),
        'samples': len(local_dots), 'finite': bool(np.isfinite(v).all())}, v
bpy.context.view_layer.update(); _, _, world_body = surface(body); rest, rest_vertices = clearance(patch, world_body)
qualification = {'clothDistanceM': .001, 'bodyOuterThicknessM': .001, 'requiredRestSeparationM': .002,
    'restConstructionTargetM': .006, 'restConstructionCapM': .012, 'maximumRestConstructionM': max(construction),
    'oneSubdivisionOnly': True, 'patchVertices': len(mesh.vertices), 'patchTriangles': len(faces), 'hardPins': len(boundary), 'halfPins': len(neighbor), 'rest': rest}
qualification['pass'] = rest['bodyTriangleContactPairs'] == 0 and rest['nonadjacentSelfContactPairs'] == 0 and rest['minimumSampledLocalNormalDotM'] >= .002 and rest['minimumSampledUnsignedBodyDistanceM'] >= .002
print('CLOTH_REST_QUALIFICATION', qualification, flush=True)
if not qualification['pass']:
    report = {'status': 'STOPPED before simulation: qualified clean rest separation/pin boundary failed; no parameter loop', 'pins': pins, 'recipeSHA256': sha(__file__), 'restQualification': qualification}
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n'); sys.exit(0)
# A bounded two-second bike-free deep knee bend, endpoint from immutable FK240.
pose0, pose1 = driver['frames'][0]['poseBasisBlender'], driver['frames'][240]['poseBasisBlender']
def coeff(pose):
    centers = [0] + config['frames']; distances = []
    for f in centers:
        center = driver['frames'][f]['poseBasisBlender']; distances.append(math.sqrt(sum((2 * math.acos(min(1, abs(float(np.dot(pose[n]['quaternionWXYZ'], center[n]['quaternionWXYZ'])))))) ** 2 for n in config['joints'])))
    if min(distances) < 1e-5:
        values = [float(i == distances.index(min(distances))) for i in range(len(distances))]
    else:
        values = np.array(distances) ** -4; values = values / sum(values)
    return values[1:]
for frame in range(1, 50):
    fraction = (frame-1)/48; pose = {}
    for name in pose0:
        pb = rig.pose.bones[name]; old, new = pose0[name], pose1[name]; q = Quaternion(old['quaternionWXYZ']).slerp(Quaternion(new['quaternionWXYZ']), fraction)
        pb.location = Vector(old['location']).lerp(Vector(new['location']), fraction); pb.rotation_quaternion = q; pb.scale = Vector(old['scale']).lerp(Vector(new['scale']), fraction)
        pose[name] = {'quaternionWXYZ': list(q)}
        for path in ['location', 'rotation_quaternion', 'scale']:
            pb.keyframe_insert(data_path=path, frame=frame)
    for o in [patch, physics]:
        for name, value in zip(config['keys'], coeff(pose)):
            key = o.data.shape_keys.key_blocks[name]; key.value = value; key.keyframe_insert(data_path='value', frame=frame)
scene.frame_set(1); bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=str(out / 'comparison.blend'), compress=True)
# Source simulation streams are the primary measurement; played local rendering
# uses those baked vertices later so capture never changes the simulation.
results = []; streams = {'skin': [], 'collision': [], 'body': []}
for frame in range(1, 50):
    if time.monotonic() - start > 90:
        raise RuntimeError('Fixed90second own CPU simulation cap reached; no foreign job affected')
    scene.frame_set(frame); bpy.context.view_layer.update(); body_v, body_f, body_tree = surface(body); rows = {}
    for name, o in [('skin', patch), ('collision', physics)]:
        row, vertices = clearance(o, body_tree); rows[name] = row; streams[name].append(vertices)
    streams['body'].append(body_v); results.append({'frame': frame, 'timeS': (frame-1)/24, 'versions': rows})
    print('CLOTH_FRAME', frame, rows, flush=True)
np.savez_compressed(out / 'comparison-streams.npz', **{name: np.array(v) for name, v in streams.items()}, patchFaces=faces, bodyFaces=body_f)
assert pins == {str(p): sha(p) for p in [source, dp, cp]}
report = {'status': 'UNACCEPTED single bounded native cloth/body/self collision knee comparison; played review pending',
    'pins': pins, 'recipeSHA256': sha(__file__), 'nativeSetupSHA256': sha(out / 'comparison.blend'), 'streamsSHA256': sha(out / 'comparison-streams.npz'),
    'restQualification': qualification, 'frames': results, 'fps': 24, 'elapsedSeconds': time.monotonic() - start,
    'settings': {'threads': 1, 'quality': 8, 'collisionQuality': 8, 'clothDistanceM': .001, 'selfDistanceM': .001, 'bodyOuterM': .001, 'bodyInnerM': .001,
        'mass': .3, 'tension': 50, 'compression': 50, 'shear': 5, 'bending': .5, 'dynamicMesh': True, 'gravity': list(scene.gravity)},
    'bakeAssessment': 'If played/clearance qualified, inverse ownLBS can bake local streams to pose-space morphs; no real-time cloth installed or approved.',
    'limits': ['Local knee patch only, not whole garment fit or proof physics cannot clip.',
        'Both compared variants share one fixed qualified clean-rest construction; improvement is not attributed to collision vs unchanged original rest.',
        'Every-frame triangle contacts and sampled unsigned/local-normal distances are measured; local normal dots are not complete signed volume clearance.',
        'Two-second synthetic bike-free bend to historicalFK240, not actual bicycle seating/contact.',
        'Own CPU1thread90seconds cap, no global weight optimizer/density/gap sweep or foreign-job interruption; root judges played fabric shape.']}
(out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n'); print('CLOTH_COMPARISON_READY', report['elapsedSeconds'], flush=True)
