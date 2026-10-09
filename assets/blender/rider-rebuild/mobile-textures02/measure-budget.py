#!/usr/bin/env python3
"""Measure ORM resolution loss against authored PNG and existing ASTC level0."""
import argparse, json, math
from pathlib import Path
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/orm2k01'))
args = parser.parse_args()
source = Path('harness/out/rider-rebuild/download-opt01/textures01/atlas01')
budget = json.loads((args.out / 'budget.json').read_text())
runtime = json.loads((args.out / 'orm2k-runtime-transcode.json').read_text())
assert len(runtime) == 13 and all(f['allLevelsSucceeded'] for r in runtime for f in r['formats'])
blocks = []
for row in budget['maps']:
    image = row['image']
    for level in range(row['levels']):
        old_level = level + int(row['droppedLargestMip'])
        name = f'image-{image:02d}-level-{level}.blocks'
        old_name = f'image-{image:02d}-level-{old_level}.blocks'
        assert (args.out / 'orm2k-astc-blocks' / name).read_bytes() == (source / 'uastc-rdo05-astc-blocks' / old_name).read_bytes()
        blocks.append({'image': image, 'candidateLevel': level, 'sourceLevel': old_level, 'ASTCByteExact': True})
rows = []
for image in [r['image'] for r in budget['maps'] if r['droppedLargestMip']]:
    original = Image.open(source / 'original' / f'image-{image:02d}.png').convert('RGBA')
    baseline = np.memmap(source / 'uastc-rdo05-astc-decoded-rgba' / f'image-{image:02d}.rgba',
                         dtype=np.uint8, mode='r', shape=(4096, 4096, 4))
    raw = (args.out / 'orm2k-decoded-rgba' / f'image-{image:02d}.rgba').read_bytes()
    small = Image.frombytes('RGBA', (2048, 2048), raw)
    # Data maps use independent linear channels. Premultiplied-alpha RGB
    # interpolation would corrupt an unused-alpha ORM; resize channels separately.
    reconstructed = Image.merge('RGBA', [c.resize((4096, 4096), Image.Resampling.BILINEAR) for c in small.split()])
    comparisons = {}
    for label in ['authoredPNG', 'sourceASTCLevel0']:
        hist = np.zeros((4, 256), dtype=np.int64)
        masked_hist = np.zeros((3, 256), dtype=np.int64)
        sums, masked_sums = np.zeros(4), np.zeros(3)
        bias = np.zeros(4)
        count = authored = 0
        for y in range(0, 4096, 64):
            png = np.asarray(original.crop((0, y, 4096, y + 64)))
            a = png if label == 'authoredPNG' else np.asarray(baseline[y:y + 64])
            b = np.asarray(reconstructed.crop((0, y, 4096, y + 64)))
            delta = b.astype(np.int16) - a.astype(np.int16)
            mask = png[:, :, 3] > 0
            count += delta.shape[0] * delta.shape[1]
            authored += int(np.count_nonzero(mask))
            for c in range(4):
                values = np.abs(delta[:, :, c])
                hist[c] += np.bincount(values.ravel(), minlength=256)
                sums[c] += float(np.sum(delta[:, :, c].astype(np.float64) ** 2))
                bias[c] += int(np.sum(delta[:, :, c]))
                if c < 3:
                    masked_hist[c] += np.bincount(values[mask], minlength=256)
                    masked_sums[c] += float(np.sum(delta[:, :, c][mask].astype(np.float64) ** 2))
        channels = []
        for c, name in enumerate(['R', 'roughnessG', 'metallicB', 'alpha']):
            cumulative = np.cumsum(hist[c])
            row = {'channel': name, 'rmse8bit': math.sqrt(sums[c] / count), 'meanSigned8bit': bias[c] / count,
                   'p95Absolute8bit': int(np.searchsorted(cumulative, count * .95)),
                   'p99Absolute8bit': int(np.searchsorted(cumulative, count * .99)),
                   'maxAbsolute8bit': int(np.nonzero(hist[c])[0][-1]), 'changedPixels': int(count - hist[c, 0])}
            if c < 3:
                row['sourceAuthoredAlphaPositive'] = {'pixels': authored, 'rmse8bit': math.sqrt(masked_sums[c] / authored),
                    'p99Absolute8bit': int(np.searchsorted(np.cumsum(masked_hist[c]), authored * .99)),
                    'maxAbsolute8bit': int(np.nonzero(masked_hist[c])[0][-1])}
            channels.append(row)
        comparisons[label] = channels
    rows.append({'image': image, 'source': [4096, 4096], 'candidate': [2048, 2048],
                 'reconstruction': 'Independent-channel linear bilinear upsample, texel proxy; not a shader/render equivalence claim',
                 'comparisons': comparisons})
    print(json.dumps(rows[-1]), flush=True)
gpu = {f['name']: sum(next(x['totalMipBytes'] for x in r['formats'] if x['name'] == f['name']) for r in runtime) for f in runtime[0]['formats']}
report = {'accepted': False, 'sourceSHA256': budget['sourceSHA256'], 'candidateSHA256': budget['outputSHA256'],
          'candidateBytes': budget['outputBytes'], 'textureBytes': budget['candidateTextureBytes'],
          'fullMipGPUTextureBytes': gpu, 'pinnedTranscodes': sum(r['levels'] * len(r['formats']) for r in runtime),
          'retainedASTCBlocksByteExact': blocks, 'ORMResolutionComparisons': rows,
          'unchangedHoodieNormalOutlierQualification': {'meanDegrees': .2992693007690832, 'p99Degrees': 2.11,
              'maxDegrees': 98.92657025408023, 'pixelsAbove30Degrees': 46, 'normalTextureByteExact': True},
          'limits': ['Resolution loss is measured, not accepted; parent moving closeups and actual phone remain gates.',
                     'All alpha differences are recorded; ORM alpha is unused by current opaque materials.',
                     'Source raw glTF semantic SHA is distinct from compiled rest; no compiled-rest equivalence claim.']}
(args.out / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')
