"""Pixel-only additive 2.1 layouts; never overwrite the fifteen-body gallery."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--design', choices=['01', '02', '03', '04', '05', 'all'], required=True)
a = p.parse_args()
REPO = Path(__file__).resolve().parents[5]
ROOT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
OUT = REPO / 'docs/evidence/hero-remaster/rider-search-v1/hunyuan21/review'
OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
big = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 30)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fit(path, w, h):
    im = Image.open(path).convert('RGBA')
    im.thumbnail((w, h), Image.Resampling.LANCZOS)
    tile = Image.new('RGBA', (w, h), (88, 88, 88, 255))
    tile.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
    return tile.convert('RGB')


designs = [f'{n:02d}' for n in range(1, 6)] if a.design == 'all' else [a.design]
layouts = []
for design in designs:
    n = int(design)
    inputs = [REPO / f'assets/design/hero-remaster/rider-search-v1/targets/{design}.png']
    inputs += [ROOT / 'rendered' / e / design / 'working/board.png'
               for e in ['hunyuan', 'trellis', 'pixal', 'hunyuan21']]
    labels = [f'TARGET{n} approximate views', f'H{n} older turbo', f'T{n} TRELLIS.2',
              f'P{n} Pixal3D', f'H21-{n} Hunyuan3D 2.1']
    image = Image.new('RGB', (3000, 990), (24, 27, 31))
    draw = ImageDraw.Draw(image)
    for j, (path, label) in enumerate(zip(inputs, labels)):
        image.paste(fit(path, 600, 940), (j * 600, 50))
        draw.text((j * 600 + 10, 15), label, font=font, fill='white')
    output = OUT / f'design-{design}-comparison.jpg'
    image.save(output, quality=95, subsampling=0)
    layouts.append({'file': output.name, 'sha256': sha(output),
                    'sources': [{'path': str(path), 'sha256': sha(path)} for path in inputs]})
if a.design == 'all':
    for native in [False, True]:
        image = Image.new('RGB', (1800, 3034), (24, 27, 31))
        draw = ImageDraw.Draw(image)
        draw.text((18, 16), 'RIDER SEARCH — twenty bodies, all four lanes', font=big, fill='white')
        draw.text((18, 54), 'Native geometry' if native else 'Same-camera working exports / metallic0 diagnostic', font=font, fill='white')
        sources = []
        for row, engine in enumerate(['reference', 'hunyuan', 'trellis', 'pixal', 'hunyuan21']):
            for n in range(1, 6):
                design = f'{n:02d}'
                if engine == 'reference':
                    source = REPO / f'assets/blender/hero-remaster/rider/search-v1/refs/{design}.png'
                    label = f'REF{n}'
                else:
                    tier = 'native-gray' if native else 'working'
                    source = ROOT / 'rendered' / engine / design / tier / '0000.png'
                    label = f'H21-{n}' if engine == 'hunyuan21' else f'{engine[0].upper()}{n}'
                x, y = (n - 1) * 360, 84 + row * 590
                image.paste(fit(source, 360, 540), (x, y + 50))
                draw.text((x + 10, y + 15), label, font=font, fill='white')
                sources.append({'path': str(source), 'sha256': sha(source)})
        output = OUT / ('native-overview.jpg' if native else 'front-overview.jpg')
        image.save(output, quality=95, subsampling=0)
        layouts.append({'file': output.name, 'sha256': sha(output), 'sources': sources})
(OUT / ('layout-all.json' if a.design == 'all' else f'layout-{a.design}.json')).write_text(
    json.dumps({'status': 'resized pixel-only comparison; no body retouch', 'files': layouts,
                'limits': ['Approximate target angles; actual render angles exact',
                           'Settings differ across generators; see prepared and generation manifests']}, indent=2) + '\n')
print('Additive H21 layouts composed:', a.design)
