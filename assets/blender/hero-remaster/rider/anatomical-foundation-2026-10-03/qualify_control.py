"""Read-only source qualification: literal surface witnesses and moving views."""
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
ap.add_argument('--out', required=True)
ap.add_argument('--render', action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(a.source).resolve(), Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
cloth = bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
rig = bpy.data.objects['Independent anatomical foundation rig']
root = bpy.data.objects['Foundation file frame, game x0.65']
scene = bpy.context.scene


def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vv = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    ff = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    bvh = BVHTree.FromPolygons([Vector(v) for v in vv], ff.tolist(), all_triangles=True)
    evaluated.to_mesh_clear()
    return vv, ff, bvh


rows = []
for frame in range(1, 194, 4):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    cv, cf, cb = surface(cloth)
    bv, bf, bb = surface(body)
    pairs = [(i, j) for i, j in cb.overlap(cb)
             if i < j and not set(cf[i]).intersection(cf[j])]
    cross = cb.overlap(bb)
    minimum_area = float(np.linalg.norm(np.cross(cv[cf[:, 1]] - cv[cf[:, 0]],
        cv[cf[:, 2]] - cv[cf[:, 0]]), axis=1).min() / 2)
    signed, unsigned = [], []
    for p in cv:
        q, normal, index, distance = bb.find_nearest(Vector(p))
        if q is not None:
            signed.append(float((Vector(p) - q).dot(normal)))
            unsigned.append(float(distance))
    rows.append({'frame': frame, 'timeS': (frame - 1) / 24,
        'allFinite': bool(np.isfinite(cv).all() and np.isfinite(bv).all()),
        'clothMinTriangleAreaM2': minimum_area,
        'clothNonadjacentBVHOverlapPairs': len(pairs),
        'clothBodyBVHOverlapPairs': len(cross),
        'nearestBodyUnsignedDistanceM': {'min': min(unsigned), 'max': max(unsigned)},
        'nearestBodyNormalDotM': {'min': min(signed), 'max': max(signed),
            'negativeVertexCount': sum(s < -1e-6 for s in signed)},
        'firstClothSelfPairs': pairs[:10], 'firstClothBodyPairs': cross[:10]})
report = {'status': 'UNACCEPTED surface and motion witnesses; no all-pose clearance pass',
    'source': str(source), 'sourceSHA256': source_sha, 'sampledFrames': len(rows), 'rows': rows,
    'limits': ['BVH overlaps are triangle contact witnesses, not penetration depth.',
        'Nearest-normal dot is a local signed diagnostic, not guaranteed global inside classification.',
        'Cage topology/weights are native; no corrective, shrinkwrap or sourceA field is applied.',
        'Generic FK stress is not accepted bike choreography or exact requested endpoint poses.']}
(out / 'surface-motion.json').write_text(json.dumps(report, indent=2) + '\n')
print('SURFACE_MOTION', json.dumps({
    'frames': len(rows), 'maxClothSelfPairs': max(r['clothNonadjacentBVHOverlapPairs'] for r in rows),
    'maxClothBodyPairs': max(r['clothBodyBVHOverlapPairs'] for r in rows),
    'worstLocalNormalDotM': min(r['nearestBodyNormalDotM']['min'] for r in rows)}), flush=True)

if a.render:
    # Four actual concurrently played viewpoints of the SAME unmodified source.
    pants = bpy.data.objects['Separate fitted native trousers control']
    boxers = bpy.data.objects['Opaque boxer fitting garment']
    roots = []
    for index, yaw in enumerate([0, 90, 180, 270]):
        if index == 0:
            clone_root, clone_rig = root, rig
        else:
            clone_root = root.copy()
            bpy.context.collection.objects.link(clone_root)
            clone_rig = rig.copy()
            clone_rig.data = rig.data.copy()
            bpy.context.collection.objects.link(clone_rig)
            clone_rig.parent = clone_root
            for obj in [body, cloth, pants, boxers]:
                clone = obj.copy()
                bpy.context.collection.objects.link(clone)
                clone.parent = clone_rig
                for mod in clone.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = clone_rig
        clone_root.location = (.65, (index - 1.5) * 1.6, 0)
        clone_root.rotation_euler.z = math.radians(yaw)
        roots.append(clone_root)
    world = bpy.data.worlds.new('Foundation neutral studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.11, .11, .11, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .65
    scene.world = world
    for name, pos, power, size in [('Key', (4, -4, 5), 900, 6),
                                  ('Fill', (3, 4, 3), 600, 6), ('Rim', (-3, 0, 4), 800, 6)]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.size = power, size
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = pos
        obj.rotation_euler = (Vector((.65, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Four simultaneously played views')
    camera = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = (8, 0, .93)
    camera.rotation_euler = (Vector((.65, 0, .93)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.type, data.ortho_scale = 'ORTHO', 6.6
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 4
    scene.cycles.use_denoising = True
    scene.render.threads_mode, scene.render.threads = 'FIXED', 4
    scene.render.resolution_x, scene.render.resolution_y = 1200, 400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    frames = out / 'played-frames'
    frames.mkdir(exist_ok=True)
    for index, frame in enumerate(range(1, 194, 2)):
        scene.frame_set(frame)
        scene.render.filepath = str(frames / f'{index:04d}.png')
        bpy.ops.render.render(write_still=True)
        if index % 12 == 0:
            print('PLAYED_FRAME', index, 'source_frame', frame, flush=True)
    report['movieRecipe'] = {'frames': 97, 'fps': 12, 'sourceFrames': list(range(1, 194, 2)),
        'anglesDegrees': [0, 90, 180, 270], 'CPUThreads': 4, 'samples': 4,
        'limits': 'Four source views played together; gray anatomy/native flat-color garment only, no likeness acceptance.'}
assert source_sha == hashlib.sha256(source.read_bytes()).hexdigest()
report['sourceSHA256After'] = source_sha
(out / 'surface-motion.json').write_text(json.dumps(report, indent=2) + '\n')
