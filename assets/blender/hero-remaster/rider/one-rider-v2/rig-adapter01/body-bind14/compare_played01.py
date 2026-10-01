"""Matched actual engine evidence; no image repainting or injected poses."""
from pathlib import Path
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw

repo = Path('/Users/raynos/projects/games/rockhop')
base = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01'
old = base / 'body-bind11/face-focus02'
new = base / 'body-bind14/played01'
archive = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/decoded-evidence/face-focus02')
reports = {s: json.loads((new / s / 'report.json').read_text()) for s in ['textured', 'gray']}
results = {}
for surface in ['textured', 'gray']:
    before = json.loads((old / surface / 'report.json').read_text())['samples']
    after = reports[surface]['samples']
    assert len(before) == len(after) == 72
    assert not reports[surface].get('failure') and reports[surface]['errors'] == []
    for a, b in zip(before, after):
        assert all(a[k] == b[k] for k in ['state', 'debug', 'hash', 'positions', 'effectiveCamera'])
        assert all(a['surfaceFocus'][k] == b['surfaceFocus'][k]
                   for k in ['vertex', 'rest', 'world', 'headLocal', 'projectedAfter'])
    rows = []
    for i in range(72):
        name = '%04d.png' % i
        a = np.asarray(Image.open(archive / surface / 'frames' / name).convert('RGB'))
        b = np.asarray(Image.open(new / surface / 'frames' / name).convert('RGB'))
        delta = np.abs(a.astype(int) - b.astype(int))
        rows.append({'i': i, 'changedPixels': int(np.any(delta, axis=2).sum()),
                     'maxChannelDelta': int(delta.max()), 'meanChannelDelta': float(delta.mean())})
    results[surface] = rows
    shutil.copy2(new / surface / 'frames/0018.png', new / f'actual-front-{surface}.png')
for a, b in zip(reports['textured']['samples'], reports['gray']['samples']):
    assert all(a[k] == b[k] for k in ['state', 'debug', 'effectiveCamera', 'surfaceFocus'])

# Identical crop, no perspective or content correction; parents judge actuals.
crop = (660, 90, 1830, 1300)
for surface in ['textured', 'gray']:
    board = Image.new('RGB', (2340, 1250), (24, 24, 24)); draw = ImageDraw.Draw(board)
    for col, file in enumerate([archive / surface / 'frames/0018.png', new / surface / 'frames/0018.png']):
        frame = Image.open(file).convert('RGB').crop(crop)
        board.paste(frame, (col * 1170, 0))
        draw.text((col * 1170 + 20, 1220), 'Current body11' if col == 0 else 'Recessed eye trial14 — unaccepted', fill='white')
    board.save(new / f'actual-before-after-{surface}.jpg', quality=96)
(new / 'comparison-proof.json').write_text(json.dumps({
    'pairedStateDebugHashBonesAndCameraExact': 72, 'surfaceFocusExact': 72,
    'pairedPBRGrayStateCameraExact': 72, 'crop': crop, 'pixelDifferenceDiagnostic': results,
    'limits': 'Actual recorded input and camera, lights/rig/physics unchanged. Source face surface changes are expected in gray. Image differences do not establish natural eye anatomy or appearance acceptance.'}, indent=2) + '\n')
print('Matched72 frames with exact state, bones and effective camera')
