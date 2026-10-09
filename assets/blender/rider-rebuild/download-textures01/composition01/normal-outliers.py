#!/usr/bin/env python3
"""Bounded-row normal outlier counts; no UV, alpha or padding exclusion."""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
source = Image.open(args.directory / 'original/image-12.png').convert('RGBA')
width, height = source.size
decoded = np.memmap(args.directory / 'uastc-rdo05-astc-decoded-rgba/image-12.rgba',
                    dtype=np.uint8, mode='r', shape=(height, width, 4))
thresholds = [5, 10, 30, 60, 90]
counts = {str(t): 0 for t in thresholds}
worst = []
for y in range(0, height, 64):
    a = np.asarray(source.crop((0, y, width, min(y + 64, height))))
    b = np.asarray(decoded[y:y + 64])
    av, bv = a[:, :, :3].astype(np.float64) / 127.5 - 1, b[:, :, :3].astype(np.float64) / 127.5 - 1
    al, bl = np.linalg.norm(av, axis=2), np.linalg.norm(bv, axis=2)
    angles = np.degrees(np.arccos(np.clip(np.sum(av * bv, axis=2) / np.maximum(al * bl, 1e-10), -1, 1)))
    for t in thresholds:
        counts[str(t)] += int(np.count_nonzero(angles > t))
    flat = np.argpartition(angles.ravel(), -8)[-8:]
    for i in flat:
        yy, xx = np.unravel_index(i, angles.shape)
        worst.append({'x': int(xx), 'y': int(y + yy), 'degrees': float(angles[yy, xx]),
                      'sourceRGBA': a[yy, xx].tolist(), 'decodedRGBA': b[yy, xx].tolist(),
                      'sourceVectorLength': float(al[yy, xx]), 'decodedVectorLength': float(bl[yy, xx])})
    worst = sorted(worst, key=lambda r: r['degrees'], reverse=True)[:8]
report = {'image': 12, 'pixels': width * height, 'mask': 'All source pixels; no UV or alpha exclusion',
          'countsAboveDegrees': counts, 'fractionsAboveDegrees': {k: v / (width * height) for k, v in counts.items()},
          'worstPixels': worst, 'accepted': False}
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
