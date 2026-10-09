#!/usr/bin/env python3
"""Compose verified component KTX maps; prune only unused delivery records."""
import argparse, copy, hashlib, json, struct
from pathlib import Path

SELECTED_SHA = 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af'
MASTER_SHA = '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649'
def sha(data):
    return hashlib.sha256(data).hexdigest()
def json_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
def walk_textures(material):
    for key, value in material.items():
        if key.endswith('Texture') and isinstance(value, dict) and 'index' in value:
            yield key, value
        elif isinstance(value, dict):
            yield from walk_textures(value)
def image_of(texture):
    return texture.get('source', texture.get('extensions', {}).get('KHR_texture_basisu', {}).get('source'))

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--source-sha', required=True)
parser.add_argument('--graft-receipt', type=Path, required=True)
parser.add_argument('--components', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/components01'))
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/combined01'))
args = parser.parse_args()
blob = args.source.read_bytes()
assert sha(blob) == args.source_sha
receipt = json.loads(args.graft_receipt.read_text())
assert receipt['source']['sha256'] == SELECTED_SHA and receipt['output']['sha256'] == args.source_sha
js = struct.unpack_from('<I', blob, 12)[0]
source = json.loads(blob[20:20 + js])
binary = blob[28 + js:]
doc = copy.deepcopy(source)
assert not any('KHR_materials_variants' in p.get('extensions', {}) for m in doc['meshes'] for p in m['primitives'])
live_materials = sorted({p['material'] for m in doc['meshes'] for p in m['primitives']})
live_textures = sorted({t['index'] for i in live_materials for _, t in walk_textures(doc['materials'][i])})
live_images = sorted({image_of(doc['textures'][i]) for i in live_textures})
assert len(live_images) == 21
material_map = {old: new for new, old in enumerate(live_materials)}
texture_map = {old: new for new, old in enumerate(live_textures)}
image_map = {old: new for new, old in enumerate(live_images)}
doc['materials'] = [doc['materials'][i] for i in live_materials]
doc['textures'] = [doc['textures'][i] for i in live_textures]
doc['images'] = [doc['images'][i] for i in live_images]
for mesh in doc['meshes']:
    for primitive in mesh['primitives']:
        primitive['material'] = material_map[primitive['material']]
for material in doc['materials']:
    for _, info in walk_textures(material):
        info['index'] = texture_map[info['index']]
for texture in doc['textures']:
    old_image = image_of(texture)
    texture.pop('source', None)
    texture.setdefault('extensions', {})['KHR_texture_basisu'] = {'source': image_map[old_image]}
for image in doc['images']:
    image['mimeType'] = 'image/ktx2'
for field in ['extensionsUsed', 'extensionsRequired']:
    if 'KHR_texture_basisu' not in doc[field]:
        doc[field].append('KHR_texture_basisu')

component_images = {}
for part in receipt['components']:
    component = part['name']
    intake = json.loads((args.components / component / 'inventory.json').read_text())
    assert intake['sourceOriginalSelectedSHA256'] == MASTER_SHA
    encoded = json.loads((args.components / component / 'uastc-rdo05-encode.json').read_text())
    assert len(encoded) == 3
    for local, kind in enumerate(['albedo', 'orm', 'normal']):
        assert intake['images'][local]['sha256'] == part['images'][kind]['sha256']
        component_images[part['images'][kind]['image']] = (component, kind, encoded[local])
assert len(component_images) == 12
donor_root = Path('harness/out/rider-rebuild/mobile-textures02/orm2k02')
donor_budget = json.loads((donor_root / 'budget.json').read_text())
donor = next(r for r in donor_budget['maps'] if r['image'] == 11)
assert donor_budget['sourceSHA256'] == SELECTED_SHA
args.out.mkdir(parents=True, exist_ok=True)
maps = args.out / 'uastc-rdo05'
maps.mkdir(exist_ok=True)
replacements, rows = {}, []
for old in live_images:
    new = image_map[old]
    image = source['images'][old]
    view = source['bufferViews'][image['bufferView']]
    assert view.get('buffer', 0) == 0
    original = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    if old in component_images:
        component, kind, encoded = component_images[old]
        assert image['mimeType'] == 'image/png'
        assert sha(original) == next(p['images'][kind]['sha256'] for p in receipt['components'] if p['name'] == component)
        data = Path(encoded['path']).read_bytes()
        assert sha(data) == encoded['sha256']
        method = 'source-detail component PNG to verified UASTC/RDO0.5'
    elif old == 11:
        assert sha(original) == donor['sourceSHA256']
        data = Path(donor['path']).read_bytes()
        assert sha(data) == donor['sha256']
        method = 'jeans ORM exact source mip1 promotion; existing measured resolution trial'
    else:
        assert image['mimeType'] == 'image/ktx2'
        data = original
        method = 'source KTX2 byte-exact reuse'
    width, height = struct.unpack_from('<2I', data, 20)
    path = maps / f'image-{new:02d}.ktx2'
    path.write_bytes(data)
    replacements[image['bufferView']] = data
    rows.append({'image': new, 'sourceImage': old, 'sourceImageAliases': [old], 'name': image.get('name'), 'path': str(path),
                 'sourceBytes': len(original), 'sourceSHA256': sha(original), 'bytes': len(data), 'sha256': sha(data),
                 'size': [width, height], 'levels': struct.unpack_from('<I', data, 40)[0],
                 'method': method, 'wholeKTXByteExact': data == original})
naive_texture_bytes = sum(r['bytes'] for r in rows)
canonical, unique_rows, canonical_old_images = {}, [], []
for row in rows:
    old = row['sourceImage']
    key = row['sha256']  # Includes dimensions, transfer/alpha semantics and every mip.
    if key not in canonical:
        canonical[key] = len(unique_rows)
        unique_rows.append(row)
        canonical_old_images.append(old)
    else:
        original = unique_rows[canonical[key]]
        assert replacements[source['images'][original['sourceImage']]['bufferView']] == replacements[source['images'][old]['bufferView']]
        original['sourceImageAliases'].append(old)
    image_map[old] = canonical[key]
rows = unique_rows
doc['images'] = [copy.deepcopy(source['images'][old]) for old in canonical_old_images]
for image in doc['images']:
    image['mimeType'] = 'image/ktx2'
for old, new in texture_map.items():
    doc['textures'][new]['extensions']['KHR_texture_basisu']['source'] = image_map[image_of(source['textures'][old])]
for new, row in enumerate(rows):
    path = maps / f'image-{new:02d}.ktx2'
    path.write_bytes(replacements[source['images'][row['sourceImage']]['bufferView']])
    row['image'], row['path'] = new, str(path)
live_views = sorted({a['bufferView'] for a in doc['accessors']} | {i['bufferView'] for i in doc['images']})
view_map = {old: new for new, old in enumerate(live_views)}
views, result, protected = [], bytearray(), []
def append(data):
    result.extend(b'\0' * (-len(result) % 4))
    at = len(result)
    result.extend(data)
    return at
for old in live_views:
    view = copy.deepcopy(source['bufferViews'][old])
    ext = view.get('extensions', {}).get('EXT_meshopt_compression')
    if ext:
        data = binary[ext.get('byteOffset', 0):ext.get('byteOffset', 0) + ext['byteLength']]
        ext['byteOffset'] = append(data)
        protected.append({'sourceView': old, 'kind': 'meshopt', 'bytes': len(data), 'sha256': sha(data), 'exact': True})
    else:
        assert view.get('buffer', 0) == 0
        original = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
        data = replacements.get(old, original)
        view['byteOffset'] = append(data)
        view['byteLength'] = len(data)
        if old not in replacements:
            assert data == original
            protected.append({'sourceView': old, 'kind': 'raw', 'bytes': len(data), 'sha256': sha(data), 'exact': True})
    views.append(view)
for accessor in doc['accessors']:
    accessor['bufferView'] = view_map[accessor['bufferView']]
for image in doc['images']:
    image['bufferView'] = view_map[image['bufferView']]
doc['bufferViews'] = views
doc['buffers'][0]['byteLength'] = len(result)
for key in ['nodes', 'skins', 'animations', 'scenes', 'scene', 'cameras', 'samplers']:
    assert doc.get(key) == source.get(key)
assert sum(len(s['joints']) for s in doc['skins']) == 75
assert sum(len(a['channels']) for a in doc['animations']) == 225
# Independently undo live-reference remaps before comparing shader/geometry metadata.
for old, new in material_map.items():
    restored = copy.deepcopy(doc['materials'][new])
    reverse = {new: old for old, new in texture_map.items()}
    for _, info in walk_textures(restored):
        info['index'] = reverse[info['index']]
    assert restored == source['materials'][old]
restored_meshes = copy.deepcopy(doc['meshes'])
reverse_material = {new: old for old, new in material_map.items()}
for mesh in restored_meshes:
    for primitive in mesh['primitives']:
        primitive['material'] = reverse_material[primitive['material']]
assert restored_meshes == source['meshes']
for old, new in texture_map.items():
    original, candidate = source['textures'][old], doc['textures'][new]
    assert image_of(candidate) == image_map[image_of(original)]
    assert {k:v for k,v in original.items() if k not in ['source', 'extensions']} == {k:v for k,v in candidate.items() if k not in ['source', 'extensions']}
    assert {k:v for k,v in original.get('extensions', {}).items() if k != 'KHR_texture_basisu'} == {k:v for k,v in candidate.get('extensions', {}).items() if k != 'KHR_texture_basisu'}
encoded = json.dumps(doc, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
result.extend(b'\0' * (-len(result) % 4))
output = struct.pack('<3I', 0x46546c67, 2, 28 + len(encoded) + len(result))
output += struct.pack('<2I', len(encoded), 0x4e4f534a) + encoded
output += struct.pack('<2I', len(result), 0x004e4942) + result
path = args.out / 'rider.glb'
assert not path.exists(), 'Use a fresh numbered composition'
path.write_bytes(output)
report = {'accepted': False, 'sourceGraft': {'path': str(args.source), 'sha256': args.source_sha, 'bytes': len(blob)},
          'selectedSourceSHA256': SELECTED_SHA, 'originalMasterSHA256': MASTER_SHA,
          'candidate': {'path': str(path), 'sha256': sha(output), 'bytes': len(output)},
          'sourceFullMetadataCanonicalJSON_SHA256': json_sha(source), 'candidateFullMetadataCanonicalJSON_SHA256': json_sha(doc),
          'sourceRawJSONChunkSHA256': sha(blob[20:20 + js]), 'candidateRawJSONChunkSHA256': sha(encoded),
          'hashScope': 'Canonical full glTF metadata includes storage/remapped delivery records; raw chunk hashes cover exact JSON bytes including padding. Neither is compiled native-rest SHA.',
          'nativeRigAndAnimationJSONExact': True, 'meshMetadataExactAfterMaterialReferenceUndo': True,
          'liveMaterialPBRFactorsAndTextureInfoExactAfterReferenceUndo': True, 'nativeJoints': sum(len(s['joints']) for s in doc['skins']),
          'nativeAnimationChannels': sum(len(a['channels']) for a in doc['animations']),
          'removedUnreferencedMaterials': sorted(set(range(len(source['materials']))) - set(live_materials)),
          'removedUnreferencedTextures': sorted(set(range(len(source['textures']))) - set(live_textures)),
          'removedUnreferencedImages': sorted(set(range(len(source['images']))) - set(live_images)),
          'materialMap': material_map, 'textureMap': texture_map, 'imageMap': image_map, 'viewMap': view_map,
          'nonImagePayloadsExact': protected, 'textureBytes': sum(r['bytes'] for r in rows), 'maps': rows,
          'textureBytesBeforeExactDedup': naive_texture_bytes, 'uniqueImageRecords': len(rows),
          'identicalKTXDedupBytesSaved': naive_texture_bytes - sum(r['bytes'] for r in rows),
          'limits': 'Component field/native motion and compression are independent unaccepted measurements; parent moving/device qualification required. Hoodie maps/identity images reused exact; jeans ORM is measured2K trial.'}
(args.out / 'composition.json').write_text(json.dumps(report, indent=2) + '\n')
(args.out / 'uastc-rdo05-encode.json').write_text(json.dumps(rows, indent=2) + '\n')
print(json.dumps({'candidate': report['candidate'], 'maps': len(rows), 'textureBytes': report['textureBytes'], 'accepted': False}))
