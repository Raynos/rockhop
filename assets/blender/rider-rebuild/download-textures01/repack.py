#!/usr/bin/env python3
"""Replace embedded PNG payloads only; geometry views/EXT_meshopt stay byte-identical."""
import argparse, copy, hashlib, json, struct
from pathlib import Path


def read_glb(path):
    blob = path.read_bytes()
    assert blob[:4] == b'glTF' and struct.unpack_from('<I', blob, 4)[0] == 2
    json_size = struct.unpack_from('<I', blob, 12)[0]
    return json.loads(blob[20:20+json_size]), blob[28+json_size:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--maps', type=Path, default=Path('harness/out/rider-rebuild/download-opt01/textures01/uastc'))
    parser.add_argument('--png', action='store_true', help='Lossless PNG repack, without basis extension')
    args = parser.parse_args()
    doc, binary = read_glb(args.source)
    before = copy.deepcopy(doc)
    image_views = {image['bufferView']:i for i,image in enumerate(doc['images'])}
    # Rebuild buffer0 by logical regions, so unused original image bytes really disappear.
    regions = {}
    for index, view in enumerate(doc['bufferViews']):
        if index in image_views:
            regions[('image', index)] = (view.get('byteOffset', 0), view['byteLength'])
        elif view.get('buffer', 0) == 0:
            regions[('view', index)] = (view.get('byteOffset', 0), view['byteLength'])
        meshopt = view.get('extensions', {}).get('EXT_meshopt_compression')
        if meshopt and meshopt['buffer'] == 0:
            regions[('meshopt', index)] = (meshopt.get('byteOffset', 0), meshopt['byteLength'])
    result = bytearray()
    copied = {}
    for key, (offset, length) in regions.items():
        if key[0] == 'image':
            image_index = image_views[key[1]]
            replacement = args.maps / f"image-{image_index:02d}.{'png' if args.png else 'ktx2'}"
            data = replacement.read_bytes()
        else:
            data = binary[offset:offset+length]
        # Shared regions retain one copy; image regions are intentionally independent.
        cache_key = (offset, length, key[0]=='image')
        if key[0] != 'image' and cache_key in copied:
            new_offset = copied[cache_key]
        else:
            result.extend(b'\0' * ((-len(result)) % 4))
            new_offset = len(result)
            result.extend(data)
            copied[cache_key] = new_offset
        view = doc['bufferViews'][key[1]]
        target = view['extensions']['EXT_meshopt_compression'] if key[0]=='meshopt' else view
        target['byteOffset'], target['byteLength'] = new_offset, len(data)
        if key[0] != 'image':
            assert data == binary[offset:offset+length]
    doc['buffers'][0]['byteLength'] = len(result)
    if not args.png:
        for image in doc['images']:
            image['mimeType'] = 'image/ktx2'
        for texture in doc['textures']:
            image_index = texture.pop('source')
            texture.setdefault('extensions', {})['KHR_texture_basisu'] = {'source': image_index}
        for field in ['extensionsUsed', 'extensionsRequired']:
            values = doc.setdefault(field, [])
            if 'KHR_texture_basisu' not in values:
                values.append('KHR_texture_basisu')
    for key in ['nodes','scenes','scene','skins','animations','meshes','accessors','materials','samplers']:
        assert doc.get(key) == before.get(key), f"Semantic field changed: {key}"
    encoded = json.dumps(doc,separators=(',',':')).encode()
    encoded += b' ' * ((-len(encoded)) % 4)
    result.extend(b'\0' * ((-len(result)) % 4))
    output = struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(result))
    output += struct.pack('<I4s',len(encoded),b'JSON')+encoded
    output += struct.pack('<I4s',len(result),b'BIN\0')+result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(json.dumps({'output':str(args.output),'bytes':len(output),'sha256':hashlib.sha256(output).hexdigest(),
                      'unchangedSemanticFields':['nodes','scenes','scene','skins','animations','meshes','accessors','materials','samplers'],
                      'nonImagePayloadsUnchanged':True}, indent=2))

if __name__ == '__main__':
    main()
