"""Measure color/normal discontinuity at actual shared head/cheek positions."""
from pathlib import Path
import hashlib
import io
import json
import struct
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

source, output = map(Path, sys.argv[1:])
raw = source.read_bytes()
length = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + length])
binary = raw[28 + length:]


def array(index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    k = {'VEC2': 2, 'VEC3': 3}[a['type']]
    assert a['componentType'] == 5126
    return np.ndarray((a['count'], k), dtype='<f4', buffer=binary,
                      offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
                      strides=(v.get('byteStride', k * 4), 4))


def bitmap(index):
    v = doc['bufferViews'][doc['images'][index]['bufferView']]
    return np.asarray(Image.open(io.BytesIO(binary[v.get('byteOffset', 0):
        v.get('byteOffset', 0) + v['byteLength']])).convert('RGB'))


def sample(image, uv):
    # glTF loader sets flipY=false: image row0 is texture v0.
    h, w = image.shape[:2]
    x = np.clip(uv[:, 0] * w - .5, 0, w - 1)
    y = np.clip(uv[:, 1] * h - .5, 0, h - 1)
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    jx, jy = np.minimum(ix + 1, w - 1), np.minimum(iy + 1, h - 1)
    fx, fy = (x - ix)[:, None], (y - iy)[:, None]
    return ((image[iy, ix] * (1 - fx) + image[iy, jx] * fx) * (1 - fy)
            + (image[jy, ix] * (1 - fx) + image[jy, jx] * fx) * fy)


head, cheek = doc['meshes'][1]['primitives']
hp, cp = [array(p['attributes']['POSITION']) for p in [head, cheek]]
distance, nearest = cKDTree(hp).query(cp)
shared = distance < 2e-6
hn = array(head['attributes']['NORMAL'])[nearest[shared]]
cn = array(cheek['attributes']['NORMAL'])[shared]
angles = np.degrees(np.arccos(np.clip((hn * cn).sum(1) /
    (np.linalg.norm(hn, axis=1) * np.linalg.norm(cn, axis=1)), -1, 1)))
huv = array(head['attributes']['TEXCOORD_0'])[nearest[shared]]
cuv = array(cheek['attributes']['TEXCOORD_0'])[shared]
hc, cc = sample(bitmap(5), huv), sample(bitmap(6), cuv)
rows = [{'cheekVertex': int(i), 'sourceHeadVertex': int(j),
         'distanceM': float(distance[i]), 'normalAngleDeg': float(angle),
         'headRGB255': a.tolist(), 'cheekRGB255': b.tolist(),
         'rgbDistance': float(np.linalg.norm(a - b))}
        for i, j, angle, a, b in zip(np.flatnonzero(shared), nearest[shared], angles, hc, cc)]
report = {'sourceSHA256': hashlib.sha256(raw).hexdigest(), 'sharedPositions': len(rows),
          'maximumPositionGapM': float(distance[shared].max()),
          'normalAngleP50P90Max': np.percentile(angles, [50, 90, 100]).tolist(),
          'headRGBMean': hc.mean(0).tolist(), 'cheekRGBMean': cc.mean(0).tolist(),
          'headSamplesAnyChannelBelow32': int((hc.min(1) < 32).sum()),
          'rows': rows, 'limits': 'Read-only exact source join probe. Base-level bilinear sampling is not engine mip/post reproduction; normal nearest-match may select one UV duplicate. Diagnostic, not appearance acceptance.'}
assert source.read_bytes() == raw
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
