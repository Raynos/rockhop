"""Compare actual source09 and joint-bake11 under identical replay cameras."""
from pathlib import Path
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw

repo = Path('/Users/raynos/projects/games/rockhop')
base = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01'
old = base / 'body-bind09/face-closeup02'
new = base / 'body-bind11/played01'
archive = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind09/decoded-evidence/face-closeup02')
results = {}
for surface in ['textured', 'gray']:
    before = json.loads((old / surface / 'report.json').read_text())['samples']
    after = json.loads((new / surface / 'report.json').read_text())['samples']
    assert len(before) == len(after) == 72
    assert all(a['state'] == b['state'] and a['debug'] == b['debug'] and
               a['effectiveCamera'] == b['effectiveCamera'] for a, b in zip(before, after))
    rows = []
    for i in range(72):
        name = '%04d.png' % i
        a = np.asarray(Image.open(archive / surface / 'frames' / name).convert('RGB'))
        b = np.asarray(Image.open(new / surface / 'frames' / name).convert('RGB'))
        delta = np.abs(a.astype(int) - b.astype(int))
        rows.append({'i': i, 'changedPixels': int(np.any(delta, axis=2).sum()),
                     'maxChannelDelta': int(delta.max()), 'meanChannelDelta': float(delta.mean())})
    if surface == 'gray':
        assert all(r['changedPixels'] == 0 for r in rows), 'Geometry/lighting must remain exact'
    results[surface] = rows

board = Image.new('RGB', (2000, 1150), (24, 24, 24))
draw = ImageDraw.Draw(board)
for col, file in enumerate([archive / 'textured/frames/0018.png', new / 'textured/frames/0018.png']):
    image = Image.open(file).convert('RGB').crop((440, 250, 1260, 1300))
    image.thumbnail((1000, 1100))
    board.paste(image, (col * 1000, 0))
    draw.text((col * 1000 + 15, 1110), 'Before' if col == 0 else 'Joint physical color bake', fill='white')
board.save(new / 'actual-before-after.jpg', quality=96)
shutil.copy2(new / 'textured/frames/0018.png', new / 'actual-front-textured.png')
(new / 'matched-before-after-report.json').write_text(json.dumps({
    'pairedStatesDebugCamerasExact': 72, 'grayPNGPixelIdentical': 72,
    'crops': [440, 250, 1260, 1300], 'pixelDifferenceDiagnostic': results,
    'scope': 'Same actual input, camera, lights, rig and body. Identical crop and uniform thumbnail only; no repaint or injected pose. Image difference does not prove an appearance score.'}, indent=2) + '\n')
print('72 actual paired states/debug/cameras exact;72grayPNGpixel-identical')
