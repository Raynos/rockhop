"""Same frozen sleeve/setup/time integration, collision-disabled comparison."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--comparison', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); out = Path(a.comparison).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); parent = json.loads((out / 'comparison.json').read_text())
assert parent['complete49Frames'] and parent['restQualification']['pass']
if (out / 'collision-off.json').exists():
    raise RuntimeError('Frozen collision-off comparison exists')
setup = out / 'comparison.blend'; original_pin = sha(setup); start = time.monotonic(); bpy.ops.wm.open_mainfile(filepath=str(setup))
physics = bpy.data.objects['Same eased sleeve WITH body self cloth']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
cloth = next(m for m in physics.modifiers if m.type == 'CLOTH')
cloth.collision_settings.use_collision = False; cloth.collision_settings.use_self_collision = False
def surface(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = e.to_mesh(); mesh.calc_loop_triangles()
    v = np.array([e.matrix_world @ x.co for x in mesh.vertices]); f = np.array([t.vertices[:] for t in mesh.loop_triangles]); e.to_mesh_clear()
    return v, f, BVHTree.FromPolygons([Vector(p) for p in v], f.tolist(), all_triangles=True)
rows = []; stream = []; on = np.load(out / 'comparison-streams.npz'); maximum_on_off = 0
for frame in range(1, 50):
    if time.monotonic() - start > 90:
        raise RuntimeError('Fixed90second offcomparison cap; no foreign job affected')
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update(); bv, bf, body_tree = surface(body); v, f, tree = surface(physics)
    assert np.array_equal(bv, on['body'][frame-1]), 'Kinematic body timing differs'
    samples = list(v)
    for ids in f:
        tri = v[ids]; samples.extend([tri.mean(0), (tri[0]+tri[1])/2, (tri[1]+tri[2])/2, (tri[2]+tri[0])/2])
    unsigned = []; dots = []
    for p in samples:
        q, normal, ti, distance = body_tree.find_nearest(Vector(p)); unsigned.append(distance); dots.append(float(np.dot(p - np.array(q), np.array(normal))))
    contacts = tree.overlap(body_tree); self_pairs = [(i, j) for i, j in tree.overlap(tree) if i < j and not set(f[i]) & set(f[j])]
    delta = float(np.linalg.norm(v - on['collision'][frame-1], axis=1).max()); maximum_on_off = max(maximum_on_off, delta)
    row = {'frame': frame, 'timeS': (frame-1)/24, 'bodyTriangleContactPairs': len(contacts), 'nonadjacentSelfContactPairs': len(self_pairs),
        'minimumSampledLocalNormalDotM': min(dots), 'minimumSampledUnsignedBodyDistanceM': min(unsigned), 'samples': len(samples),
        'finite': bool(np.isfinite(v).all()), 'onOffMaximumVertexDifferenceM': delta}; rows.append(row); stream.append(v)
    print('COLLISION_DISABLED_FRAME', frame, row, flush=True)
assert np.array_equal(np.array(stream)[0], on['collision'][0]), 'Initial simulation states differ'
np.savez_compressed(out / 'collision-off-streams.npz', collisionOff=np.array(stream), patchFaces=f)
assert sha(setup) == original_pin
report = {'status': 'UNACCEPTED matched collision-disabled cloth simulation; paired played comparison next', 'parentComparisonSHA256': sha(out / 'comparison.json'),
    'nativeSetupSHA256': original_pin, 'recipeSHA256': sha(__file__), 'streamsSHA256': sha(out / 'collision-off-streams.npz'), 'sameInitialVerticesExactly': True,
    'sameKinematicBodyAll49FramesExactly': True, 'settings': 'All original cloth/pin/mass/stiffness/time settings retained; only use_collision/use_self_collision false',
    'maximumOnOffVertexDifferenceM': maximum_on_off, 'frames': rows, 'elapsedSeconds': time.monotonic() - start,
    'limits': ['Local sleeve test; no complete garment, final engine response or arbitrary-pose collision safety claim.', 'Sampled local normal dots are not certified full signed-volume clearance.']}
(out / 'collision-off.json').write_text(json.dumps(report, indent=2) + '\n'); print('COLLISION_OFF_READY', maximum_on_off, flush=True)
