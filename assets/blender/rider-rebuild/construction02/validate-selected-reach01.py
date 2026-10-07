"""Read back authored clip coverage and unchanged dressed source fields."""
import hashlib
import io
import json
import math
import struct
import sys
from pathlib import Path
from PIL import Image


def read(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+size]), raw[28+size:]


def accessor(gltf, buffer, index):
    item = gltf['accessors'][index]
    view = gltf['bufferViews'][item['bufferView']]
    fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[item['componentType']] * {
        'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[item['type']]
    offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', struct.calcsize(fmt))
    return [struct.unpack_from(fmt, buffer, offset+n*stride) for n in range(item['count'])]


base, output, evidence = [Path(p).resolve() for p in sys.argv[1:]]
a, ab = read(base / 'rider.glb')
b, bb = read(output / 'rider.glb')
assert len(a['skins'][0]['joints']) == len(b['skins'][0]['joints']) == 75
expected = {'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}
assert {m['name'] for m in a['meshes']} == {m['name'] for m in b['meshes']} == expected
assert len(a['meshes']) == len(b['meshes']) == 7
for source_mesh, new_mesh in zip(a['meshes'], b['meshes']):
    assert source_mesh['name'] == new_mesh['name']
    assert len(source_mesh['primitives']) == len(new_mesh['primitives'])
    for source_primitive, new_primitive in zip(source_mesh['primitives'], new_mesh['primitives']):
        assert source_primitive['attributes'].keys() == new_primitive['attributes'].keys()
        assert accessor(a, ab, source_primitive['indices']) == accessor(b, bb, new_primitive['indices'])
        assert source_primitive.get('material') == new_primitive.get('material')
        for field in source_primitive['attributes']:
            assert accessor(a, ab, source_primitive['attributes'][field]) == accessor(
                b, bb, new_primitive['attributes'][field]), (source_mesh['name'], field)
# Animation export cannot substitute or recolor the selected PBR materials.
assert a.get('materials') == b.get('materials')
assert len(a.get('images', [])) == len(b.get('images', []))
for old_image, new_image in zip(a.get('images', []), b.get('images', [])):
    assert old_image['mimeType'] == new_image['mimeType']
    def pixels(document, binary, image):
        view = document['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        decoded = Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert('RGBA')
        return decoded.size, decoded.tobytes()
    assert pixels(a, ab, old_image) == pixels(b, bb, new_image)
assert len(b.get('animations', [])) == 1
animation = b['animations'][0]
assert animation['name'] == 'RiderStandReachGripRelease'
assert len(animation['channels']) == 225
channels = {}
end_error = 0
starts, ends, counts = set(), set(), set()
for channel in animation['channels']:
    node = b['nodes'][channel['target']['node']]['name']
    channels.setdefault(node, set()).add(channel['target']['path'])
    sampler = animation['samplers'][channel['sampler']]
    times = accessor(b, bb, sampler['input'])
    values = accessor(b, bb, sampler['output'])
    starts.add(times[0][0]); ends.add(times[-1][0]); counts.add(len(times))
    assert all(math.isfinite(value) for row in values for value in row)
    end_error = max(end_error, max(abs(x-y) for x, y in zip(values[0], values[-1])))
assert len(channels) == 75
assert all(paths == {'translation', 'rotation', 'scale'} for paths in channels.values())
assert len(starts) == len(ends) == 1 and abs(max(ends)-min(starts)-8) < 1e-6
assert end_error == 0
report = {'accepted': False,
          'glbSHA256': hashlib.sha256((output / 'rider.glb').read_bytes()).hexdigest(),
          'sourceGLBSHA256': hashlib.sha256((base / 'rider.glb').read_bytes()).hexdigest(),
          'animationName': animation['name'], 'channels': 225, 'animatedNodes': 75,
          'everyNodeTRS': True, 'everyDecodedTrackFinite': True,
          'exportStartSeconds': min(starts), 'exportEndSeconds': max(ends),
          'exportSpanSeconds': max(ends)-min(starts), 'sampleCounts': sorted(counts),
          'decodedEndToStartMaxComponentDifference': end_error,
          'allSevenSelectedMeshAttributeAndIndexArraysExactlyEqual': True,
          'allSelectedPBRMaterialsAndDecodedMapPixelsExactlyEqual': True,
          'limits': ['Decoded authored generic action only; actual Garage moving judgment and native/GPU parity remain open.']}
evidence.mkdir(parents=True, exist_ok=True)
(evidence / 'decoded-validation.json').write_text(json.dumps(report, indent=2) + '\n')
for name in ['report.json', 'input-receipt.json']:
    (evidence / name).write_bytes((output / name).read_bytes())
(evidence / 'guard.json').write_bytes((output.parent / (output.name+'-guard') / 'guard.json').read_bytes())
print(json.dumps(report, indent=2))
