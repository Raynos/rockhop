#!/usr/bin/env python3
"""Pinned selective ORM mip budget; remaining KTX blocks and geometry stay exact."""
import argparse, copy, hashlib, json, struct
from pathlib import Path

SOURCE_SHA = 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af'
ORM_IMAGES = {1, 3, 8, 11}
def sha(data):
    return hashlib.sha256(data).hexdigest()
def json_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
def append(blob, data, alignment=4):
    blob.extend(b'\0' * (-len(blob) % alignment))
    offset = len(blob)
    blob.extend(data)
    return offset
def trim_mip(data):
    assert data[:12] == b'\xabKTX 20\xbb\r\n\x1a\n'
    width, height, depth, layers, faces, levels, scheme = struct.unpack_from('<7I', data, 20)
    assert (width, height, depth, layers, faces, scheme) == (4096, 4096, 0, 0, 1, 2)
    do, dl, ko, kl, so, sl = struct.unpack_from('<4I2Q', data, 48)
    assert sl == so == 0 and data[do + 12:do + 15] == bytes([166, 0, 1])
    indexes = [struct.unpack_from('<3Q', data, 80 + 24 * i) for i in range(levels)]
    target = bytearray(data[:80]) + bytearray(24 * (levels - 1))
    nd = append(target, data[do:do + dl])
    nk = append(target, data[ko:ko + kl]) if kl else 0
    struct.pack_into('<2I', target, 20, width // 2, height // 2)
    struct.pack_into('<I', target, 40, levels - 1)
    struct.pack_into('<4I2Q', target, 48, nd, dl, nk, kl, 0, 0)
    kept = []
    for new_level in reversed(range(levels - 1)):
        offset, length, inflated = indexes[new_level + 1]
        payload = data[offset:offset + length]
        new_offset = append(target, payload, 8)
        struct.pack_into('<3Q', target, 80 + 24 * new_level, new_offset, length, inflated)
        assert target[new_offset:new_offset + length] == payload
        kept.append({'level': new_level, 'sourceLevel': new_level + 1, 'payloadBytes': length,
                     'payloadSHA256': sha(payload), 'compressedPayloadByteExact': True})
    return bytes(target), sorted(kept, key=lambda r: r['level'])

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path('harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb'))
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/orm2k01'))
parser.add_argument('--images', default='1,3,8,11', help='Explicit subset of known ORM image indices')
args = parser.parse_args()
selected = set(map(int, args.images.split(',')))
assert selected and selected <= ORM_IMAGES
blob = args.source.read_bytes()
assert sha(blob) == SOURCE_SHA
size = struct.unpack_from('<I', blob, 12)[0]
doc = json.loads(blob[20:20 + size])
binary = blob[28 + size:]
before = copy.deepcopy(doc)
args.out.mkdir(parents=True, exist_ok=True)
maps = args.out / 'orm2k'
maps.mkdir(exist_ok=True)
image_views = {image['bufferView']: i for i, image in enumerate(doc['images'])}
replacements, rows = {}, []
for view_index, image in image_views.items():
    view = doc['bufferViews'][view_index]
    assert view.get('buffer', 0) == 0 and doc['images'][image]['mimeType'] == 'image/ktx2'
    original = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    data, kept = trim_mip(original) if image in selected else (original, [])
    output = maps / f'image-{image:02d}.ktx2'
    output.write_bytes(data)
    replacements[view_index] = data
    width, height = struct.unpack_from('<2I', data, 20)
    rows.append({'image': image, 'path': str(output), 'sourceBytes': len(original), 'bytes': len(data),
                 'sourceSHA256': sha(original), 'sha256': sha(data), 'size': [width, height],
                 'levels': struct.unpack_from('<I', data, 40)[0], 'droppedLargestMip': image in selected,
                 'wholeKTXByteExact': data == original, 'remainingMipPayloads': kept})
regions = {}
for index, view in enumerate(doc['bufferViews']):
    if index in image_views:
        regions[('image', index)] = (view.get('byteOffset', 0), view['byteLength'])
    elif view.get('buffer', 0) == 0:
        regions[('view', index)] = (view.get('byteOffset', 0), view['byteLength'])
    ext = view.get('extensions', {}).get('EXT_meshopt_compression')
    if ext and ext['buffer'] == 0:
        regions[('meshopt', index)] = (ext.get('byteOffset', 0), ext['byteLength'])
result, copied, protected = bytearray(), {}, []
for key, (offset, length) in regions.items():
    original = binary[offset:offset + length]
    data = replacements[key[1]] if key[0] == 'image' else original
    cache_key = (offset, length, key[0] == 'image')
    new_offset = copied.get(cache_key) if key[0] != 'image' else None
    if new_offset is None:
        new_offset = append(result, data)
        copied[cache_key] = new_offset
    view = doc['bufferViews'][key[1]]
    target = view['extensions']['EXT_meshopt_compression'] if key[0] == 'meshopt' else view
    target['byteOffset'], target['byteLength'] = new_offset, len(data)
    if key[0] != 'image':
        assert data == original
        protected.append({'kind': key[0], 'view': key[1], 'bytes': length, 'sha256': sha(data), 'exact': True})
doc['buffers'][0]['byteLength'] = len(result)
semantic_before = {k: v for k, v in before.items() if k not in ['buffers', 'bufferViews']}
semantic_after = {k: v for k, v in doc.items() if k not in ['buffers', 'bufferViews']}
assert semantic_before == semantic_after
assert sum(len(s['joints']) for s in doc['skins']) == 75
assert sum(len(a['channels']) for a in doc['animations']) == 225
encoded = json.dumps(doc, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
result.extend(b'\0' * (-len(result) % 4))
candidate = struct.pack('<3I', 0x46546c67, 2, 28 + len(encoded) + len(result))
candidate += struct.pack('<2I', len(encoded), 0x4e4f534a) + encoded
candidate += struct.pack('<2I', len(result), 0x004e4942) + result
output = args.out / 'rider.glb'
output.write_bytes(candidate)
report = {'accepted': False, 'source': str(args.source), 'sourceSHA256': SOURCE_SHA, 'sourceBytes': len(blob),
          'output': str(output), 'outputSHA256': sha(candidate), 'outputBytes': len(candidate),
          'sourceRawFullJSON_SHA256': json_sha(before), 'candidateRawFullJSON_SHA256': json_sha(doc),
          'preservedSemanticContract_SHA256': json_sha(semantic_before),
          'contractScope': 'Raw glTF JSON excluding storage buffers/bufferViews; all nodes/skins/animation/accessor/material/image/texture/sampler metadata exact. This is not a compiled native-rest SHA.',
          'nonImagePayloads': protected, 'nativeJoints': 75, 'nativeAnimationChannels': 225,
          'sourceTextureBytes': sum(r['sourceBytes'] for r in rows), 'candidateTextureBytes': sum(r['bytes'] for r in rows),
          'resolutionLossy': True, 'retainedMipEncodingLossless': True, 'maps': rows}
(args.out / 'budget.json').write_text(json.dumps(report, indent=2) + '\n')
(args.out / 'orm2k-encode.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['output', 'outputSHA256', 'outputBytes', 'sourceTextureBytes', 'candidateTextureBytes', 'accepted']}))
