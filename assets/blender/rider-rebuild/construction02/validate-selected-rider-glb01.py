"""Decode every selected author primitive and its actual skin joint order."""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
directory, native_receipt, output = [Path(p).resolve() for p in sys.argv[1:]]
assert not output.exists(), 'Preserve previous decoded receipts'
native = json.loads(native_receipt.read_text())
assert native['jointCount'] == 75 and set(native['authorObjects']) == EXPECTED
assert hashlib.sha256((directory / 'rider-assembled.blend').read_bytes()).hexdigest() == native['native']['sha256']
raw = (directory / 'rider.glb').read_bytes()
assert raw[:4] == b'glTF' and struct.unpack_from('<II', raw, 4) == (2, len(raw))
size, kind = struct.unpack_from('<II', raw, 12); assert kind == 0x4e4f534a
gltf = json.loads(raw[20:20 + size])
binary_size, kind = struct.unpack_from('<II', raw, 20 + size); assert kind == 0x004e4942
binary = raw[28 + size:]; assert len(binary) == binary_size
contract = json.loads((directory / 'rider-contract.json').read_text())
assert contract['glbSHA256'] == hashlib.sha256(raw).hexdigest()
formats = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
columns = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
def accessor(index):
    item = gltf['accessors'][index]; view = gltf['bufferViews'][item['bufferView']]
    assert not item.get('sparse') and not item.get('normalized')
    fmt = '<' + formats[item['componentType']] * columns[item['type']]
    offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', struct.calcsize(fmt))
    return [struct.unpack_from(fmt, binary, offset + i * stride) for i in range(item['count'])]
def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def matrix(node):
    if 'matrix' in node: return [[node['matrix'][4*j+i] for j in range(4)] for i in range(4)]
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    rotation = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    scale = node.get('scale', [1, 1, 1]); position = node.get('translation', [0, 0, 0])
    return [[rotation[i][j]*scale[j] for j in range(3)] + [position[i]] for i in range(3)] + [[0, 0, 0, 1]]
parents = {child: i for i, node in enumerate(gltf['nodes']) for child in node.get('children', [])}
worlds = {}
def world(index):
    if index not in worlds:
        local = matrix(gltf['nodes'][index])
        worlds[index] = multiply(world(parents[index]), local) if index in parents else local
    return worlds[index]

assert len(gltf['skins']) == 1
skin = gltf['skins'][0]
joint_names = [gltf['nodes'][index]['name'] for index in skin['joints']]
assert len(joint_names) == len(set(joint_names)) == 75
assert set(joint_names) == {bone['name'] for bone in contract['nativeRest']['bones']}
names = {node['name']: i for i, node in enumerate(gltf['nodes']) if 'name' in node}
rest_head_error = 0.
for bone in contract['nativeRest']['bones']:
    index = names[bone['name']]
    assert gltf['nodes'][parents[index]]['name'] == (bone['parent'] or 'RiderSkeleton')
    assert gltf['nodes'][index].get('scale', [1, 1, 1]) == [1, 1, 1]
    x, y, z = bone['head']
    rest_head_error = max(rest_head_error, math.dist([world(index)[i][3] for i in range(3)], [x, z, -y]))
assert rest_head_error < 1e-6
rest_skin = []; inverse_error = 0.
for index, values in zip(skin['joints'], accessor(skin['inverseBindMatrices'])):
    inverse = [[values[4*j+i] for j in range(4)] for i in range(4)]
    product = multiply(world(index), inverse); rest_skin.append(product)
    inverse_error = max(inverse_error, max(abs(product[i][j] - (i == j)) for i in range(4) for j in range(4)))
assert inverse_error < 1e-5

mesh_nodes = [node for node in gltf['nodes'] if 'mesh' in node]
assert len(mesh_nodes) == 7 and {node['name'] for node in mesh_nodes} == EXPECTED
assert set(contract['specification']['meshNames']) == EXPECTED
primitives, max_rest_error, max_field_error, material_names, field_hashes = {}, 0., 0., set(), {}
body_native_ids, body_source_ids, body_identity_rows = set(), set(), {}
for node in mesh_nodes:
    assert node.get('skin') == 0, ('Unbound author object', node['name'])
    object_materials, rows, named_fields_by_id = [], [], {}
    for primitive in gltf['meshes'][node['mesh']]['primitives']:
        assert primitive.get('mode', 4) == 4
        attrs = primitive['attributes']
        required = {'POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0', '_NATIVE_ID'}
        assert required <= set(attrs), (node['name'], required - set(attrs))
        positions = accessor(attrs['POSITION']); normals = accessor(attrs['NORMAL'])
        uv = accessor(attrs['TEXCOORD_0']); slots = accessor(attrs['JOINTS_0']); fields = accessor(attrs['WEIGHTS_0'])
        assert len(positions) == len(normals) == len(uv) == len(slots) == len(fields)
        current_ids = [int(row[0]) for row in accessor(attrs['_NATIVE_ID'])]
        assert len(current_ids) == len(positions)
        indices = [row[0] for row in accessor(primitive['indices'])]
        assert len(indices) % 3 == 0 and all(0 <= index < len(positions) for index in indices)
        for identity, point, normal, coord, joints, weights in zip(current_ids, positions, normals, uv, slots, fields):
            assert all(math.isfinite(value) for value in (*point, *normal, *coord, *weights))
            assert all(0 <= int(joint) < 75 for joint in joints) and all(weight >= 0 for weight in weights)
            max_field_error = max(max_field_error, abs(sum(weights) - 1))
            named = sorted((joint_names[int(joint)], weight) for joint, weight in zip(joints, weights) if weight > 0)
            assert all(weight > .0001 and weight * (1 << 24) == int(weight * (1 << 24)) for _, weight in named)
            assert identity not in named_fields_by_id or named_fields_by_id[identity] == named
            named_fields_by_id[identity] = named
            posed = [0., 0., 0.]
            for joint, weight in zip(joints, weights):
                transform = rest_skin[int(joint)]
                for axis in range(3):
                    posed[axis] += weight * sum(transform[axis][k] * (*point, 1)[k] for k in range(4))
            max_rest_error = max(max_rest_error, math.dist(point, posed))
        mat = gltf['materials'][primitive['material']]
        object_materials.append(mat['name']); material_names.add(mat['name'])
        if node['name'] != 'RiderBody':
            assert 'baseColorTexture' in mat['pbrMetallicRoughness']
        if node['name'] == 'RiderBody':
            assert {'_SOURCE_VERTEX_ID', '_NATIVE_ID'} <= set(attrs)
            current = [int(row[0]) for row in accessor(attrs['_NATIVE_ID'])]
            original = [int(row[0]) for row in accessor(attrs['_SOURCE_VERTEX_ID'])]
            assert len(current) == len(original) == len(positions)
            for identity, source_id, point in zip(current, original, positions):
                row = (source_id, point)
                assert identity not in body_identity_rows or body_identity_rows[identity] == row
                body_identity_rows[identity] = row
            body_native_ids.update(current); body_source_ids.update(original)
        rows.append({'vertices': len(positions), 'triangles': len(indices)//3, 'material': mat['name'],
                     'attributes': sorted(attrs)})
    assert set(object_materials) == set(native['materialsByAuthorObject'][node['name']])
    assert set(named_fields_by_id) == set(range(len(named_fields_by_id)))
    field_rows = [named_fields_by_id[i] for i in range(len(named_fields_by_id))]
    field_hashes[node['name']] = hashlib.sha256(json.dumps(field_rows, separators=(',', ':')).encode()).hexdigest()
    assert field_hashes[node['name']] == native['canonicalNamedFieldsByNativeIDSHA256'][node['name']]
    primitives[node['name']] = rows
assert max_field_error < 2e-7 and max_rest_error < .0001
assert body_native_ids == set(range(max(body_native_ids) + 1)) and len(body_native_ids) > 10582
assert -1 in body_source_ids and any(identity >= 1000000 for identity in body_source_ids)
identity_sha = hashlib.sha256(b''.join(struct.pack('<i', body_identity_rows[i][0]) for i in sorted(body_native_ids))).hexdigest()
position_sha = hashlib.sha256(b''.join(struct.pack('<3f', *body_identity_rows[i][1]) for i in sorted(body_native_ids))).hexdigest()
assert identity_sha == native['bodySourceIDByNativeIDSHA256']
assert position_sha == native['bodyGLTFPositionByNativeIDSHA256']
images = []
for image in gltf['images']:
    assert 'bufferView' in image and image['mimeType'] in ('image/png', 'image/jpeg')
    view = gltf['bufferViews'][image['bufferView']]
    data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0)+view['byteLength']]
    assert data.startswith(b'\x89PNG\r\n\x1a\n') or data.startswith(b'\xff\xd8')
    images.append({'name': image.get('name'), 'mimeType': image['mimeType'], 'bytes': len(data),
                   'sha256': hashlib.sha256(data).hexdigest()})
assert images
for material in gltf['materials']:
    for role, texture in list(material.get('pbrMetallicRoughness', {}).items()) + list(material.items()):
        if not role.endswith('Texture') or not isinstance(texture, dict): continue
        image_index = gltf['textures'][texture['index']]['source']
        assert 0 <= image_index < len(images)
report = {'accepted': False, 'kind': 'independent decoded complete selected rider source transport',
          'validatorSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'nativeReceiptSHA256': hashlib.sha256(native_receipt.read_bytes()).hexdigest(),
          'glbSHA256': hashlib.sha256(raw).hexdigest(), 'glbBytes': len(raw), 'skinCount': 1,
          'jointCount': 75, 'actualSkinJointOrder': joint_names, 'authorObjectPrimitives': primitives,
          'allNativeMaterialPartsPreserved': True, 'maxRestHeadErrorM': rest_head_error,
          'maxInverseBindIdentityError': inverse_error, 'maxRestSkinPositionErrorM': max_rest_error,
          'maxWeightNormalizationError': max_field_error, 'bodyCurrentNativeIDCount': len(body_native_ids),
          'bodyNativeSourceIDAndPositionArraysByteIdentical': True,
          'canonicalNamedNativeAndGPUFieldsByteIdentical': True, 'canonicalNamedFieldSHA256ByObject': field_hashes,
          'bodySourceIDCount': len(body_source_ids), 'embeddedPBRImages': images,
          'limits': ['Decoded rest and material transport only; parent judges actual played art/contact.',
                     'Image embedding is measured; source pixel identity and runtime map shrink are separate checks.',
                     'The native breath clip exists; this static receipt does not certify sampled runtime motion.']}
output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key not in ('actualSkinJointOrder', 'authorObjectPrimitives', 'embeddedPBRImages')}))
