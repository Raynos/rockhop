"""Pixel-only layout and change audit of hairstyle mockups; no art edits."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[5]
ART = REPO / 'assets/design/hero-remaster/one-rider-v2/hair'
OUT = REPO / 'docs/evidence/hero-remaster/one-rider-v2/hair'
SOURCE = Path('/Users/raynos/Documents/Codex/2026-09-30/task-2/comparison/comfy/input/rider-reference-01.png')
OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 25)
labels = ['1 BUZZ CUT', '2 SHORT CROP', '3 SWEPT BACK']
paths = [ART / n for n in ['01-buzz.png', '02-crop.png', '03-swept.png']]
full = Image.new('RGB', (1200, 670), (24, 27, 31))
close = Image.new('RGB', (1740, 560), (24, 27, 31))
fd, cd = ImageDraw.Draw(full), ImageDraw.Draw(close)
source = np.asarray(Image.open(SOURCE).convert('RGB'), dtype=np.int16)
records = []
for i, path in enumerate(paths):
    image = Image.open(path).convert('RGB')
    assert image.size == (1024, 1536)
    tile = image.copy(); tile.thumbnail((400, 600), Image.Resampling.LANCZOS)
    full.paste(tile, (i * 400, 70)); fd.text((i * 400 + 10, 20), labels[i], font=font, fill='white')
    crop = image.crop((340, 10, 685, 300)).resize((580, 488), Image.Resampling.LANCZOS)
    close.paste(crop, (i * 580, 70)); cd.text((i * 580 + 12, 20), labels[i], font=font, fill='white')
    actual = np.asarray(image, dtype=np.int16)
    difference = np.abs(actual - source)
    records.append({'label': labels[i], 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'size': list(image.size), 'comparisonToOriginal': {
                        'bodyBelowRow300MeanAbsoluteChannelDifference': float(difference[300:].mean()),
                        'bodyBelowRow300ChangedPixelFraction': float(np.any(difference[300:] != 0, axis=2).mean())}})
full.save(OUT / 'full-character-options.jpg', quality=95, subsampling=0)
close.save(OUT / 'hair-closeups.jpg', quality=95, subsampling=0)
(OUT / 'verification.json').write_text(json.dumps({'status': 'concepts only, not model or topology evidence',
    'sourceSHA256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'outputs': records,
    'layout': 'crop/resize/label only; unchanged generated assets',
    'limits': ['Image edits preserve visual identity/clothes/pose but are not pixel-identical outside hair',
               'Crop retains some shallow wavy texture; swept hair retains shallow grooves',
               'All final silhouettes compact; no claim of successful 3D topology']}, indent=2) + '\n')
print(json.dumps(records, indent=2))
