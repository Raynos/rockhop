#!/usr/bin/env python3
"""Inventory exact two-K selected-source component maps before guarded encoding."""
import argparse, hashlib, json, shutil
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('component', choices=['boot-L', 'boot-R', 'glove-L', 'glove-R'])
parser.add_argument('--bake', type=Path)
parser.add_argument('--out', type=Path)
args = parser.parse_args()
bake = args.bake or Path('harness/out/rider-rebuild/mobile-mesh02') / args.component / 'bake01'
out = args.out or Path('harness/out/rider-rebuild/mobile-textures02/components01') / args.component
metadata_bytes = (bake / 'bake.json').read_bytes()
metadata = json.loads(metadata_bytes)
assert metadata['sourceSHA256'] == '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649'
assert metadata['bake']['size'] == 2048
(out / 'original').mkdir(parents=True, exist_ok=True)
rows = []
for index, (kind, slot) in enumerate([('albedo', 'baseColorTexture'), ('orm', 'metallicRoughnessTexture'), ('normal', 'normalTexture')]):
    source = bake / f'{kind}.png'
    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    assert digest == metadata[kind]['sha256'] and len(payload) == metadata[kind]['bytes']
    destination = out / 'original' / f'image-{index:02d}.png'
    shutil.copy2(source, destination)
    with Image.open(source) as png:
        assert png.size == (2048, 2048)
        rows.append({'image': index, 'name': args.component + '_' + kind, 'path': str(destination),
                     'bytes': len(payload), 'sha256': digest, 'size': list(png.size), 'mode': png.mode,
                     'alphaExtrema': list(png.convert('RGBA').getchannel('A').getextrema()),
                     'usage': [{'material': 0, 'name': args.component, 'slot': slot}], 'srgb': kind == 'albedo'})
report = {'accepted': False, 'component': args.component, 'source': str(bake / 'bake.json'),
          'sourceSha256': hashlib.sha256(metadata_bytes).hexdigest(), 'sourceOriginalSelectedSHA256': metadata['sourceSHA256'],
          'currentOptimizedSourceSHA256': 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af',
          'sourceBytes': len(metadata_bytes), 'originalTextureBytes': sum(r['bytes'] for r in rows), 'images': rows,
          'scope': 'Original selected source-detail component PNGs; bake metadata SHA is distinct from GLB and compiled native-rest SHA. Field/motion acceptance remains with parent.'}
(out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
