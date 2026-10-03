"""Literal native/four-weight surface witnesses and simultaneously played views."""
import argparse
import hashlib
import json
import math
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
ap.add_argument('--render', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, driver_path, out = map(lambda x: Path(x).resolve(), [a.source, a.driver, a.out])
out.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
driver_hash = hashlib.sha256(driver_path.read_bytes()).hexdigest()
driver = json.loads(driver_path.read_text())
assert source_hash == driver['conditionedMasterSHA256']
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
regions = {r['region']: r for r in driver['meshRows']}


def set_pose(target, row):
    for name, trs in row['poseBasisBlender'].items():
        pb = target.pose.bones[name]
        pb.location = trs['location']
        pb.rotation_quaternion = trs['quaternionWXYZ']
        pb.scale = trs['scale']
    bpy.context.view_layer.update()


def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vv = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    ff = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return vv, ff, BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)


sample_indices = sorted(set(range(0, len(driver['frames']), 12)) | {242, 360, 384})
rows = []
for index in sample_indices:
    frame = driver['frames'][index]
    set_pose(rig, frame)
    for kind, name_key in [('native-full', 'nativeName'), ('native-four', 'exportName')]:
        body = bpy.data.objects[regions['body'][name_key]]
        cloth = bpy.data.objects[regions['cloth'][name_key]]
        bv, bf, bb = surface(body)
        cv, cf, cb = surface(cloth)
        cross = cb.overlap(bb)
        self_pairs = [(i, j) for i, j in cb.overlap(cb)
                      if i < j and not set(cf[i]).intersection(cf[j])]
        signed = []
        for vid, p in enumerate(cv):
            q, normal, triangle, distance = bb.find_nearest(Vector(p))
            signed.append((float((Vector(p) - q).dot(normal)), vid, triangle, float(distance)))
        signed.sort()
        worst = signed[0]
        rows.append({'frame': index, 'timeS': frame['timeS'], 'endpoint': frame['endpoint'],
            'weights': kind, 'clothBodyTriangleContactPairs': len(cross),
            'clothNonadjacentSelfContactPairs': len(self_pairs),
            'nearestBodyNormalDotNegativeVertices': sum(s[0] < -1e-6 for s in signed),
            'worstNearestNormalWitness': {'normalDotM': worst[0], 'clothNativeVertexID': worst[1],
                'bodyTriangleID': worst[2], 'unsignedDistanceM': worst[3],
                'clothBlenderWorldM': cv[worst[1]].tolist()},
            'firstContactPairs': cross[:8], 'firstSelfPairs': self_pairs[:8]})
report = {'status': 'UNACCEPTED literal surface witnesses; parent judges played shape',
    'masterSHA256': source_hash, 'driverSHA256': driver_hash,
    'surfaceSampleCount': len(sample_indices), 'rows': rows,
    'limits': ['Triangle overlap is a contact/intersection witness, not penetration depth.',
        'Nearest-normal dot is local; negative values are not global signed inside classification.',
        '46 sampled times are not exhaustive continuous clearance.',
        'Synthetic FK riding is not actual bike support.',
        'Flat structural PBR colors and gray native head are not approved identity.']}
(out / 'surface-witnesses.json').write_text(json.dumps(report, indent=2) + '\n')
print('SURFACE_WITNESSES', json.dumps({
    k: {'maxCrossPairs': max(r['clothBodyTriangleContactPairs'] for r in rows if r['weights'] == k),
        'maxSelfPairs': max(r['clothNonadjacentSelfContactPairs'] for r in rows if r['weights'] == k),
        'worstLocalNormalDotM': min(r['worstNearestNormalWitness']['normalDotM'] for r in rows if r['weights'] == k)}
    for k in ['native-full', 'native-four']}), flush=True)

if a.render:
    # Original and derived geometry play simultaneously, four views per row.
    # Original source/weights are never changed; presentation copies are disposable.
    original_meshes = [o for o in list(bpy.data.objects) if o.type == 'MESH']
    for obj in original_meshes:
        obj.hide_render = True
    rigs = []
    for row_index, (kind, key) in enumerate([('native-full', 'nativeName'), ('native-four', 'exportName')]):
        for col, yaw in enumerate([0, 90, 180, 270]):
            clone_root = root.copy()
            bpy.context.collection.objects.link(clone_root)
            clone_root.location = (.65, (col - 1.5) * 1.7, (1 - row_index) * 2.15)
            clone_root.rotation_euler.z = math.radians(yaw)
            clone_rig = rig.copy()
            clone_rig.data = rig.data.copy()
            clone_rig.name = f'{kind} played rig yaw{yaw}'
            bpy.context.collection.objects.link(clone_rig)
            clone_rig.parent = clone_root
            for region in ['body', 'cloth', 'jeans']:
                obj = bpy.data.objects[regions[region][key]]
                clone = obj.copy()
                bpy.context.collection.objects.link(clone)
                clone.parent = clone_rig
                clone.hide_render = False
                for mod in clone.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = clone_rig
            rigs.append(clone_rig)
    scene = bpy.context.scene
    world = bpy.data.worlds.new('Matched diagnostic neutral studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.11, .11, .11, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .65
    scene.world = world
    for name, pos, power in [('Key', (4, -4, 7), 1600), ('Fill', (3, 5, 5), 1200), ('Rim', (-4, 0, 6), 1200)]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.size = power, 7
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (Vector((.65, 0, 2)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Native full above, conditioned four below')
    camera = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = (10, 0, 2.05)
    camera.rotation_euler = (Vector((.65, 0, 2.05)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.type, data.ortho_scale = 'ORTHO', 7.2
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 4
    scene.cycles.use_denoising = True
    scene.render.threads_mode, scene.render.threads = 'FIXED', 4
    scene.render.resolution_x, scene.render.resolution_y = 1280, 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    frames_path = out / 'played-frames'
    frames_path.mkdir(exist_ok=True)
    render_indices = list(range(0, len(driver['frames']), 4))
    for number, index in enumerate(render_indices):
        for clone_rig in rigs:
            set_pose(clone_rig, driver['frames'][index])
        scene.render.filepath = str(frames_path / f'{number:04d}.png')
        bpy.ops.render.render(write_still=True)
        if number % 12 == 0:
            print('PLAYED_DIAGNOSTIC', number, 'driver', index, flush=True)
    report['played'] = {'frames': len(render_indices), 'fps': 12, 'driverFrameIndices': render_indices,
        'yawDegrees': [0, 90, 180, 270], 'rows': ['native-full', 'native-four'],
        'cameraBlenderM': list(camera.location), 'orthoScaleM': data.ortho_scale,
        'sourceColors': 'gray body, mustard sweatshirt, blue trousers; native flat structural PBR',
        'CPUThreads': 4, 'samples': 4}
    (out / 'surface-witnesses.json').write_text(json.dumps(report, indent=2) + '\n')
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
