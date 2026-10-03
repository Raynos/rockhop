"""One bounded eased sleeve-pattern/body/self-collision trial, never runtime cloth."""
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
for n in ['source', 'driver', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, dp, out = [Path(getattr(a, n)).resolve() for n in ['source', 'driver', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, dp]}
out.mkdir(parents=True, exist_ok=True)
if (out / 'comparison.json').exists():
    raise RuntimeError('Frozen sleeve trial exists; no parameter sweep')
start = time.monotonic(); bpy.ops.wm.open_mainfile(filepath=str(source))
driver = json.loads(dp.read_text()); rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
body.data.calc_loop_triangles(); bv = np.array([v.co[:] for v in body.data.vertices]); bf = np.array([t.vertices[:] for t in body.data.loop_triangles])
ownership = np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in ['upperArm.L', 'forearm.L']) for v in body.data.vertices])
arm_faces = bf[np.mean(ownership[bf], axis=1) > .5]
elbow = np.array(rig.data.bones['forearm.L'].head_local); upper = np.array(rig.data.bones['upperArm.L'].head_local); wrist = np.array(rig.data.bones['hand.L'].head_local)
du = elbow - upper; du /= np.linalg.norm(du); df = wrist - elbow; df /= np.linalg.norm(df)
vertices = []; rings = []; measurements = []; weights = []
for row in range(12):
    t = row / 11 * 2 - 1; center = elbow + (du * (.140 * t) if t <= 0 else df * (.160 * t))
    blend = max(0, min(1, (t + .30) / .60)); axis = du * (1 - blend) + df * blend; axis /= np.linalg.norm(axis)
    u = np.array([1., 0, 0]); u -= axis * np.dot(u, axis); u /= np.linalg.norm(u); v = np.cross(axis, u)
    # Measure true triangle/plane section of the native arm, with the selected
    # arm ownership. A prescribed22mm radial pattern ease is construction,
    # not an iterative nearest-surface gap or weight conditioning operation.
    section = []
    for face in arm_faces:
        p = bv[face]; signed = (p - center) @ axis
        for aa, bb in [(0, 1), (1, 2), (2, 0)]:
            if signed[aa] * signed[bb] < 0:
                factor = signed[aa] / (signed[aa] - signed[bb]); q = p[aa] + (p[bb] - p[aa]) * factor
                if np.linalg.norm(q - center) < .15:
                    section.append(q)
    if len(section) < 8:
        raise RuntimeError('Missing actual arm cross-section; do not guess fit')
    radius = max(np.linalg.norm(p - center) for p in section) + .022
    if radius > .115:
        raise RuntimeError('Arm section does not qualify local sleeve proportions')
    ring = []
    for col in range(24):
        phi = col / 24 * 2 * math.pi; p = center + radius * (u * math.cos(phi) + v * math.sin(phi))
        ring.append(len(vertices)); vertices.append(p.tolist()); weights.append({'upperArm.L': 1-row/11, 'forearm.L': row/11})
    rings.append(ring); measurements.append({'row': row, 'centerNativeM': center.tolist(), 'axis': axis.tolist(), 'nativeSectionPoints': len(section), 'radiusM': radius, 'prescribedRadialEaseM': .022})
faces = []
for row in range(11):
    for col in range(24):
        nxt = (col + 1) % 24; faces.append([rings[row][col], rings[row][nxt], rings[row+1][nxt], rings[row+1][col]])
mesh = bpy.data.meshes.new('Clean separately authored eased elbow sleeve panel'); mesh.from_pydata(vertices, [], faces); mesh.update()
pattern = bpy.data.objects.new('Eased sleeve same-pattern skinned control', mesh); bpy.context.collection.objects.link(pattern); pattern.parent = root
for name in ['upperArm.L', 'forearm.L']:
    pattern.vertex_groups.new(name=name)
for i, row in enumerate(weights):
    for name, value in row.items():
        if value:
            pattern.vertex_groups[name].add([i], value, 'REPLACE')
layer = mesh.uv_layers.new(name='UVMap')
for face in mesh.polygons:
    row, col = divmod(face.index, 24)
    for loop, uv in zip(face.loop_indices, [(col/24, row/11), ((col+1)/24, row/11), ((col+1)/24, (row+1)/11), (col/24, (row+1)/11)]):
        layer.data[loop].uv = uv
armature = pattern.modifiers.new('Own frozen anatomical bind', 'ARMATURE'); armature.object = rig
mat = bpy.data.materials.new('Neutral sleeve comparison fabric'); mat.diffuse_color = (.25, .3, .36, 1); mesh.materials.append(mat)
for face in mesh.polygons:
    face.use_smooth = True
pin_group = pattern.vertex_groups.new(name='Proximal sewn ring pins'); pin_group.add(rings[0], 1., 'REPLACE'); pin_group.add(rings[1], .5, 'REPLACE')
physics = pattern.copy(); physics.data = pattern.data.copy(); physics.name = 'Same eased sleeve WITH body self cloth'; bpy.context.collection.objects.link(physics)
cloth = physics.modifiers.new('ONE bounded eased-pattern collision trial', 'CLOTH'); settings = cloth.settings
settings.quality = 8; settings.mass = .3; settings.tension_stiffness = 50; settings.compression_stiffness = 50; settings.shear_stiffness = 5; settings.bending_stiffness = .5
settings.vertex_group_mass = pin_group.name; settings.pin_stiffness = 1.; settings.use_dynamic_mesh = True
cs = cloth.collision_settings; cs.use_collision = True; cs.distance_min = .001; cs.collision_quality = 8; cs.use_self_collision = True; cs.self_distance_min = .001
body.modifiers.new('Kinematic frozen body collision surface', 'COLLISION'); body.collision.thickness_outer = .001; body.collision.thickness_inner = .001
cloth.point_cache.frame_start, cloth.point_cache.frame_end = 1, 49
scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, 49; scene.render.fps = 24

def surface(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh(); m.calc_loop_triangles()
    vv = np.array([e.matrix_world @ x.co for x in m.vertices]); ff = np.array([t.vertices[:] for t in m.loop_triangles]); e.to_mesh_clear()
    return vv, ff, BVHTree.FromPolygons([Vector(p) for p in vv], ff.tolist(), all_triangles=True)

def clearance(o, body_tree):
    vv, ff, own = surface(o); samples = list(vv)
    for ids in ff:
        tri = vv[ids]; samples.extend([tri.mean(0), (tri[0]+tri[1])/2, (tri[1]+tri[2])/2, (tri[2]+tri[0])/2])
    dots = []; unsigned = []
    for p in samples:
        q, normal, tri, distance = body_tree.find_nearest(Vector(p)); dots.append(float(np.dot(p - np.array(q), np.array(normal)))); unsigned.append(distance)
    contacts = own.overlap(body_tree); self_pairs = [(i, j) for i, j in own.overlap(own) if i < j and not set(ff[i]) & set(ff[j])]
    return {'bodyTriangleContactPairs': len(contacts), 'nonadjacentSelfContactPairs': len(self_pairs), 'minimumSampledLocalNormalDotM': min(dots),
        'minimumSampledUnsignedBodyDistanceM': min(unsigned), 'samples': len(samples), 'finite': bool(np.isfinite(vv).all())}, vv, ff

bpy.context.view_layer.update(); _, _, rest_body = surface(body); rest, rest_vertices, pattern_faces = clearance(pattern, rest_body)
qualification = {'rest': rest, 'patternVertices': len(vertices), 'patternTriangles': len(pattern_faces), 'realOpenBoundaryLoops': 2, 'openingVertices': [24, 24],
    'hardProximalPins': 24, 'halfPins': 24, 'freeDistalOpening': True, 'requiredRestSeparationM': .002, 'clothDistanceM': .001, 'bodyOuterM': .001, 'sections': measurements}
qualification['pass'] = rest['bodyTriangleContactPairs'] == 0 and rest['nonadjacentSelfContactPairs'] == 0 and rest['minimumSampledLocalNormalDotM'] >= .002 and rest['minimumSampledUnsignedBodyDistanceM'] >= .002
print('EASED_SLEEVE_REST', qualification, flush=True)
if not qualification['pass']:
    report = {'status': 'STOPPED before simulation: new eased sleeve rest qualification failed; no parameter loop', 'pins': pins, 'recipeSHA256': sha(__file__), 'restQualification': qualification}
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n'); sys.exit(0)
pose0, pose1 = driver['frames'][0]['poseBasisBlender'], driver['frames'][112]['poseBasisBlender']
for frame in range(1, 50):
    fraction = (frame-1)/48
    for name in pose0:
        pb = rig.pose.bones[name]; old, new = pose0[name], pose1[name]
        pb.location = Vector(old['location']).lerp(Vector(new['location']), fraction); pb.rotation_quaternion = Quaternion(old['quaternionWXYZ']).slerp(Quaternion(new['quaternionWXYZ']), fraction)
        pb.scale = Vector(old['scale']).lerp(Vector(new['scale']), fraction)
        for p in ['location', 'rotation_quaternion', 'scale']:
            pb.keyframe_insert(data_path=p, frame=frame)
scene.frame_set(1); bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=str(out / 'comparison.blend'), compress=True)
results = []; streams = {'skin': [], 'collision': [], 'body': []}; complete = True
for frame in range(1, 50):
    if time.monotonic() - start > 90:
        complete = False; break
    scene.frame_set(frame); bpy.context.view_layer.update(); body_v, body_f, body_tree = surface(body); rows = {}
    for name, o in [('skin', pattern), ('collision', physics)]:
        result, vv, ff = clearance(o, body_tree); rows[name] = result; streams[name].append(vv)
    streams['body'].append(body_v); results.append({'frame': frame, 'timeS': (frame-1)/24, 'versions': rows})
    print('EASED_SLEEVE_FRAME', frame, rows, flush=True)
np.savez_compressed(out / 'comparison-streams.npz', **{name: np.array(v) for name, v in streams.items()}, patchFaces=pattern_faces, bodyFaces=body_f)
assert pins == {str(p): sha(p) for p in [source, dp]}
report = {'status': 'UNACCEPTED single bounded eased sleeve collision comparison; played review pending' if complete else 'STOPPED at90second cap; partial bounded comparison is unaccepted',
    'pins': pins, 'recipeSHA256': sha(__file__), 'nativeSetupSHA256': sha(out / 'comparison.blend'), 'streamsSHA256': sha(out / 'comparison-streams.npz'),
    'restQualification': qualification, 'frames': results, 'complete49Frames': complete, 'FPS': 24, 'elapsedSeconds': time.monotonic() - start,
    'settings': {'threads': 1, 'quality': 8, 'collisionQuality': 8, 'clothDistanceM': .001, 'selfDistanceM': .001, 'bodyOuterM': .001, 'mass': .3,
        'tension': 50, 'compression': 50, 'shear': 5, 'bending': .5, 'dynamicMesh': True, 'gravityNative': list(scene.gravity)},
    'bakeAssessment': 'Compare played folds and every-frame contact first. Qualified streams could be baked to authored pose morphs with additional time/history handling; no runtime cloth installed.',
    'limits': ['New clean eased sleeve band only, not whole final hoodie, jeans or complete footwear. Both variants share exact same pattern, ease, UV and native weights.',
        'Original1250 rubber-shell topology is not preserved in this local pattern; canonical body/head/bind and source files remain immutable.',
        'Local normal dots/unsigned samples are proxies, not complete signed-volume clearance. Every-frame triangle/self contacts are reported.',
        'Two-second synthetic bike-free reach/bent-arm trajectory to originalFK112, not actual bike contact.',
        'One fixed construction/physics setting; no old sourceA, density/gap/weight solver or foreign job interruption. Root judges moving fabric.']}
(out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n'); print('EASED_SLEEVE_COMPARISON_READY', complete, report['elapsedSeconds'], flush=True)
