#!/usr/bin/env python3
"""Prove new base-level RGBA equals the native ASTC decode of its retained source mip."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/orm2k01'))
args = parser.parse_args()
source = Path('harness/out/rider-rebuild/download-opt01/textures01/atlas01')
budget = json.loads((args.out / 'budget.json').read_text())
rows = []
for row in budget['maps']:
    image = row['image']
    name = f'image-{image:02d}'
    level = int(row['droppedLargestMip'])
    if level:
        native = source / 'uastc-rdo05-native-astc' / name / f'{name}_unpacked_rgba_ASTC_LDR_4X4_RGBA_level_1_face_0_layer_0000.png'
        with Image.open(native) as png:
            assert list(png.size) == row['size']
            old = png.convert('RGBA').tobytes()
    else:
        old = (source / 'uastc-rdo05-astc-decoded-rgba' / f'{name}.rgba').read_bytes()
    current = (args.out / 'orm2k-decoded-rgba' / f'{name}.rgba').read_bytes()
    assert current == old, f'Native ASTC decode differs for image {image}/sourceLevel{level}'
    rows.append({'image': image, 'sourceMip': level, 'size': row['size'], 'rgbaBytes': len(current),
                 'nativeASTCLinearPixelsMatchPinnedRGBA': True, 'sha256': hashlib.sha256(current).hexdigest()})
report = {'accepted': False, 'pass': True, 'candidateSHA256': budget['outputSHA256'], 'maps': rows,
          'scope': 'Native source ASTC linear-profile software decode at retained mip versus actual pinned runtime RGBA; not sRGB hardware filtering or moving acceptance.'}
(args.out / 'native-pixel-proof.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'pass': True, 'maps': len(rows)}))
