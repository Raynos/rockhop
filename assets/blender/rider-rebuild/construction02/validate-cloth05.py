"""Decode one loose-cloth derivative and prove frozen body/skin preservation."""
import hashlib
import json
import struct
import sys
from pathlib import Path


def read(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+size]), raw[28+size:]


def accessor(gltf, buffer, index):
    item = gltf['accessors'][index]
    view = gltf['bufferViews'][item['bufferView']]
    fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[item['componentType']] * {
        'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[item['type']]
    offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', struct.calcsize(fmt))
    return [struct.unpack_from(fmt, buffer, offset+n*stride) for n in range(item['count'])]


base, output, evidence = [Path(p).resolve() for p in sys.argv[1:]]
a, ab = read(base / 'rider.glb')
b, bb = read(output / 'rider.glb')
old_contract = json.loads((base / 'rider-contract.json').read_text())
new_contract = json.loads((output / 'rider-contract.json').read_text())
assert old_contract['nativeRest'] == new_contract['nativeRest']
assert len(a['skins']) == len(b['skins']) == 1
assert len(a['skins'][0]['joints']) == len(b['skins'][0]['joints']) == 75
old_joint_names = [a['nodes'][i]['name'] for i in a['skins'][0]['joints']]
new_joint_names = [b['nodes'][i]['name'] for i in b['skins'][0]['joints']]
assert old_joint_names == new_joint_names


def mesh(gltf, name):
    node = next(node for node in gltf['nodes'] if node.get('name') == name)
    return gltf['meshes'][node['mesh']]


old_body, new_body = mesh(a, 'RiderBody')['primitives'][0], mesh(b, 'RiderBody')['primitives'][0]
for field in ['_SOURCE_VERTEX_ID', 'POSITION', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0']:
    assert accessor(a, ab, old_body['attributes'][field]) == accessor(
        b, bb, new_body['attributes'][field]), field
assert accessor(a, ab, old_body['indices']) == accessor(b, bb, new_body['indices'])
new_mesh_names = [node['name'] for node in b['nodes'] if 'mesh' in node]
assert len(new_mesh_names) == 24
assert {'RiderHoodie', 'RiderJeans', 'RiderGloves', 'RiderSole.L', 'RiderSole.R',
        'RiderSideSeam.L', 'RiderSideSeam.R'} <= set(new_mesh_names)
triangles = sum(b['accessors'][p['indices']]['count']//3
                for m in b['meshes'] for p in m['primitives'])
report = {'accepted': False, 'kind': 'loose-cloth05 frozen body/skin transport check',
          'glbSHA256': hashlib.sha256((output / 'rider.glb').read_bytes()).hexdigest(),
          'sourceGLBSHA256': hashlib.sha256((base / 'rider.glb').read_bytes()).hexdigest(),
          'nativeRestContractExactlyEqualToFrozen04': True,
          'bodySourceIDPositionNormalJointWeightAndTriangleArraysExactlyEqualToFrozen04': True,
          'skinCount': 1, 'jointCount': 75, 'meshObjectCount': 24, 'actualTriangles': triangles,
          'meshObjectNames': new_mesh_names,
          'limits': ['Rest transport/source identity only; parent actual Garage/game moving judgment required.',
                     'Generic action is a separate derivative; no tiny-weight cleanup performed.']}
evidence.mkdir(parents=True, exist_ok=True)
(evidence / 'decoded-validation.json').write_text(json.dumps(report, indent=2) + '\n')
for name in ['report.json', 'input-receipt.json']:
    (evidence / name).write_bytes((output / name).read_bytes())
(evidence / 'guard.json').write_bytes((output.parent / (output.name+'-guard') / 'guard.json').read_bytes())
print(json.dumps(report, indent=2))
