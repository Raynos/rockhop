"""Pinned isolated garment metric geometry; experimental appearance guide only."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
input_path, out = Path(a.input).resolve(), Path(a.out).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
image_contract = json.loads(input_path.read_text())
assert sha(input_path) == '321c6b8ac64579f13743a37f80e27daa7b6b939457522828bff80345d9f737c6'
pins = image_contract['pins']
assert all(sha(p) == h for p, h in pins.items())
source = next(p for p in pins if p.endswith('conditioned.blend'))
contract = json.loads(Path(next(p for p in pins if p.endswith('fitting01/contract.json'))).read_text())
donor = Path(next(p for p in pins if p.endswith('rider.glb')))
out.mkdir(parents=True, exist_ok=True)
if (out / 'geometry-contract.json').exists():
    raise RuntimeError('Frozen amendment exists')
bpy.ops.wm.open_mainfile(filepath=source)
rig = bpy.data.objects['Independent anatomical foundation rig']
for name, trs in next(p for p in contract['poses'] if p['label'] == 'true_A')['poseBasisBlender'].items():
    pb = rig.pose.bones[name]
    pb.location, pb.rotation_quaternion, pb.scale = trs['location'], trs['quaternionWXYZ'], trs['scale']
bpy.data.objects['Foundation file frame, game x0.65'].location.x = 0
bpy.context.view_layer.update()

def native(name):
    o = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = o.to_mesh()
    result = {'name': name, 'vertices': np.array([o.matrix_world @ v.co for v in m.vertices]),
        'faces': [list(p.vertices) for p in m.polygons]}
    o.to_mesh_clear()
    return result

raw = donor.read_bytes(); length = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + length]); binary = raw[28 + length:]
def accessor(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']])
    return np.ndarray((a['count'], n), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(v.get('byteStride', n * dtype.itemsize), dtype.itemsize)).copy()
p = doc['meshes'][0]['primitives'][2]; v = accessor(p['attributes']['POSITION'])
hood = {'name': 'Exact b7 static hood guide, DISJOINT NOT fitted',
    'vertices': np.column_stack((v[:, 0].astype(float) - .65, -v[:, 2], v[:, 1])),
    'faces': accessor(p['indices']).reshape(-1, 3).tolist()}
shirt = native('Separate fitted sweatshirt control, hood not constructed')
jeans = native('Separate fitted native trousers control')
rows = []
for label, parts in [('hoodie', [shirt, hood]), ('jeans', [jeans])]:
    verts = np.concatenate([part['vertices'] for part in parts])
    faces = []
    offset = 0
    for part in parts:
        faces.extend([[int(i) + offset for i in f] for f in part['faces']]); offset += len(part['vertices'])
    files = []
    for axes in ['zup', 'yup']:
        xyz = verts if axes == 'zup' else np.column_stack((verts[:, 0], verts[:, 2], -verts[:, 1]))
        lines = ['# EXPERIMENTAL appearance/layout only, metres centered X0; no fit/rig pass',
            '# ' + axes + '; baked true A/action off; disjoint hood not sewn']
        for part in parts:
            values = part['vertices'] if axes == 'zup' else np.column_stack((part['vertices'][:, 0], part['vertices'][:, 2], -part['vertices'][:, 1]))
            lines.extend('v ' + ' '.join(f'{float(x):.10f}' for x in vv) for vv in values)
        face_offset = 0
        for part in parts:
            lines.append('o ' + part['name'].replace(' ', '_'))
            lines.extend('f ' + ' '.join(str(int(i) + face_offset + 1) for i in f) for f in part['faces'])
            face_offset += len(part['vertices'])
        file = out / (label + '-true_A-' + axes + '.obj'); file.write_text('\n'.join(lines) + '\n')
        parsed = np.array([[float(x) for x in line.split()[1:]] for line in lines if line.startswith('v ')])
        error = float(np.abs(parsed - xyz).max()); assert error < 1e-10
        files.append({'path': str(file), 'sha256': sha(file), 'axes': axes, 'minM': xyz.min(0).tolist(),
            'maxM': xyz.max(0).tolist(), 'extentM': np.ptp(xyz, axis=0).tolist(), 'serializedMaxResidualM': error})
    rows.append({'garment': label, 'vertices': len(verts), 'faces': len(faces),
        'parts': [{'name': part['name'], 'vertices': len(part['vertices']), 'faces': len(part['faces'])} for part in parts],
        'polygonIndicesSHA256': hashlib.sha256(json.dumps(faces).encode()).hexdigest(), 'files': files})
assert all(sha(p) == h for p, h in pins.items())
receipt = {'status': 'EXPERIMENTAL isolated metric guide, no wearable fit/rig/topology acceptance',
    'inputContractSHA256': sha(input_path), 'pins': pins, 'pose': 'true_A/action off', 'metres': True,
    'coordinates': 'Centered X0 once; yup [+Xforward,+Yup,+Zleft], zup [+Xforward,+Zup,-Yleft]',
    'registration': 'Use per-garment exact bounds; NEVER scale isolated model to full 1.822571874m body height. Generation coordinates are uncalibrated; orthographic framing is pinned separately.',
    'hood': 'Exact b7 primitive2 raw geometry only; static/disjoint lower patch retained, not attached or sewn',
    'OBJ': 'Geometry only, original polygon indices; no materials/UV/weights exported or invented',
    'garments': rows}
(out / 'geometry-contract.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('GARMENT_GEOMETRY', sha(out / 'geometry-contract.json'), [(r['garment'], r['vertices']) for r in rows], flush=True)
