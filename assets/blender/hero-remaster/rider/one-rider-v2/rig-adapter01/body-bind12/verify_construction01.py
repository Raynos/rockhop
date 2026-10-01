"""Parent conservation check, independent of the aperture builder's guards."""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
old_path = root / 'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
new_path = root / 'rig-adapter01/body-bind12/construction01/rider.glb'
out = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind12/parent-conservation01.json')


def read(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return raw, json.loads(raw[20:20 + n]), raw[28 + n:]


def array(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    step = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(v.get('byteStride', width * step), step))


old_raw, old, old_binary = read(old_path)
new_raw, new, new_binary = read(new_path)
assert new_binary[:len(old_binary)] == old_binary, 'Retain untouched original binary prefix'
assert old['meshes'][0] == new['meshes'][0], 'Body, hood, gloves and legs retain exact accessors'
assert old['meshes'][1]['primitives'][1] == new['meshes'][1]['primitives'][1], 'Cheek remains exact'
for key in ['nodes', 'skins', 'animations', 'scenes', 'scene']:
    assert old[key] == new[key], key
for key in ['accessors', 'bufferViews', 'images', 'textures', 'samplers', 'materials']:
    assert old[key] == new[key][:len(old[key])], key
old_primitive = old['meshes'][1]['primitives'][0]
new_primitive = new['meshes'][1]['primitives'][0]
protected = {}
for name, index in old_primitive['attributes'].items():
    before = array(old, old_binary, index)
    after = array(new, new_binary, new_primitive['attributes'][name])
    assert np.array_equal(before, after[:len(before)]), name
    protected[name] = len(before)
positions = array(old, old_binary, old_primitive['attributes']['POSITION'])
faces = array(old, old_binary, old_primitive['indices']).reshape(-1, 3)
updated_faces = array(new, new_binary, new_primitive['indices']).reshape(-1, 3)
outside = np.ones(len(faces), dtype=bool)
for y, z in [(1.6965, .032), (1.6970, -.0332)]:
    triangle = positions[faces]
    could_meet = (triangle[:, :, 0].max(1) > .72) & (triangle[:, :, 1].max(1) >= y - .00425) & (triangle[:, :, 1].min(1) <= y + .00425) & (triangle[:, :, 2].max(1) >= z - .013) & (triangle[:, :, 2].min(1) <= z + .013)
    outside &= ~could_meet
updated = {tuple(map(int, face)) for face in updated_faces}
assert all(tuple(map(int, face)) in updated for face in faces[outside]), 'Protected outside triangles remain'
assert old_path.read_bytes() == old_raw and new_path.read_bytes() == new_raw
report = {'sourceSHA256': hashlib.sha256(old_raw).hexdigest(),
    'candidateSHA256': hashlib.sha256(new_raw).hexdigest(),
    'originalBinaryPrefixExactBytes': len(old_binary), 'bodyHoodGlovesLegsExact': True,
    'cheekPrimitiveExact': True, 'nodesSkinsAnimationsExact': True,
    'originalHeadAttributePrefixesExact': protected,
    'outsideApertureTrianglesExact': int(outside.sum()),
    'limits': 'Conservation and source-frame checks only. New topology, normals, donor placement and actual appearance require separate review.'}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
