"""Exact shared native full/four corrective garment streams and coefficients."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
for n in ['master', 'controller', 'driver', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
master, controller_path, driver_path, out = [Path(getattr(a, n)).resolve() for n in ['master', 'controller', 'driver', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
controller = json.loads(controller_path.read_text()); driver = json.loads(driver_path.read_text())
assert sha(master) == controller['candidateMasterSHA256'] and sha(driver_path) == controller['poseDriverSHA256']
out.mkdir(parents=True, exist_ok=True)
if (out / 'expanded-driver.json').exists():
    raise RuntimeError('Frozen corrective streams exist')
bpy.ops.wm.open_mainfile(filepath=str(master))
rig = bpy.data.objects['Independent anatomical foundation rig']
objects = {r['region']: bpy.data.objects[r['exportName']] for r in driver['meshRows']}
full = {r['region']: bpy.data.objects[r['nativeName']] for r in driver['meshRows']}
for config in controller['configs']:
    src, dst = objects[config['region']], full[config['region']]
    assert len(src.data.vertices) == len(dst.data.vertices)
    assert np.array_equal([list(v.co) for v in src.data.vertices], [list(v.co) for v in dst.data.vertices])
    dst.shape_key_add(name='Basis', from_mix=False)
    for name in config['keys']:
        key = dst.shape_key_add(name=name, from_mix=False)
        for vertex, reference in zip(key.data, src.data.shape_keys.key_blocks[name].data):
            vertex.co = reference.co

def distance(a, b, names):
    return math.sqrt(sum((2 * math.acos(min(1, abs(float(np.dot(a[n]['quaternionWXYZ'], b[n]['quaternionWXYZ'])))))) ** 2 for n in names))
def coefficients(frame, config):
    centers = [0] + config['frames']
    distances = [distance(frame['poseBasisBlender'], driver['frames'][f]['poseBasisBlender'], config['joints']) for f in centers]
    if min(distances) < 1e-5:
        return [float(i == distances.index(min(distances))) for i in range(1, len(centers))]
    values = np.array(distances) ** -4; values /= sum(values)
    return values[1:].tolist()

streams = {(region, kind): (out / f'{region}-corrective-{kind}.f64').open('wb') for region in ['cloth', 'jeans'] for kind in ['native-full', 'native-four']}
frames = []
try:
    for frame in driver['frames']:
        for name, trs in frame['poseBasisBlender'].items():
            pb = rig.pose.bones[name]
            pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
        row = {'frame': frame['index'], 'timeS': frame['timeS'], 'coefficients': {}}
        for config in controller['configs']:
            values = coefficients(frame, config); row['coefficients'][config['region']] = dict(zip(config['keys'], values))
            for obj in [objects[config['region']], full[config['region']]]:
                for name, value in zip(config['keys'], values):
                    obj.data.shape_keys.key_blocks[name].value = value
        bpy.context.view_layer.update()
        for (region, kind), stream in streams.items():
            obj = (objects if kind == 'native-four' else full)[region]
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = evaluated.to_mesh()
            vertices = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
            evaluated.to_mesh_clear()
            yup = np.column_stack((vertices[:, 0], vertices[:, 2], -vertices[:, 1]))
            stream.write(yup.astype('<f8').tobytes())
        frames.append(row)
finally:
    for stream in streams.values():
        stream.close()
assert all(value == 0 for values in frames[0]['coefficients'].values() for value in values.values())
report = {'status': 'UNACCEPTED exact native full/four local corrective streams; no art or clearance pass',
    'masterSHA256': sha(master), 'GLBSHA256': controller['candidateGLBSHA256'], 'controllerSHA256': sha(controller_path),
    'poseDriverSHA256': sha(driver_path), 'samplingRecipeSHA256': sha(__file__), 'frames': frames,
    'centers': {config['region']: [{'frame': f, 'jointLocalQuaternionsWXYZ': {n: driver['frames'][f]['poseBasisBlender'][n]['quaternionWXYZ'] for n in config['joints']}} for f in [0] + config['frames']] for config in controller['configs']},
    'configs': controller['configs'], 'distance': controller['metric'], 'blend': controller['blend'],
    'streamLayout': 'little-endianFloat64[frame][nativeSourceID][XYZ], glTF file world, metres; full existing native weights versus explicit4 on same key deltas/controller',
    'pins': {path.name: {'sha256': sha(path), 'bytes': path.stat().st_size} for path in sorted(out.glob('*.f64'))},
    'bodyReference': 'Unchanged body streams and driver already pinned in diagnostic02; sourceID attribute remains exact on prototype garments',
    'limits': ['Native-full applies identical authored morph deltas but retains more weights; full/four discrepancy is separate from runtime export parity.',
        'Full529shared syntheticFKframes, not bike-supported physics; controller explicitly applied in diagnostics only.',
        'No reconstruction parameter loop, altered source, or player promotion.']}
(out / 'expanded-driver.json').write_text(json.dumps(report, indent=2) + '\n')
assert sha(master) == controller['candidateMasterSHA256'] and sha(driver_path) == controller['poseDriverSHA256']
print('CORRECTIVE_STREAMS', sha(out / 'expanded-driver.json'), len(frames), report['pins'], flush=True)
