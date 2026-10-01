"""Read the unchanged GLB's embedded maps and measured facial UV density."""
from pathlib import Path
import hashlib
import io
import json
import struct
import sys
import numpy as np
from PIL import Image

source, output = map(Path, sys.argv[1:])
output.mkdir(parents=True, exist_ok=True)
raw = source.read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
binary = raw[28 + size:]


def accessor(index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
    lanes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    width = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], lanes), dtype=dtype, buffer=binary,
                      offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                      strides=(view.get('byteStride', width * lanes), width)).copy()


images = []
for index, image in enumerate(doc['images']):
    view = doc['bufferViews'][image['bufferView']]
    data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    bitmap = Image.open(io.BytesIO(data))
    images.append({'index': index, 'name': image['name'], 'size': list(bitmap.size),
                   'encodedSHA256': hashlib.sha256(data).hexdigest()})
    if index in [5, 6]:
        bitmap.save(output / f'source-head-map-{index}.png')

regions = []
for mesh in doc['meshes']:
    for primitive in mesh['primitives']:
        if primitive['material'] not in [3, 4]:
            continue
        p = accessor(primitive['attributes']['POSITION'])
        uv = accessor(primitive['attributes']['TEXCOORD_0'])
        triangles = accessor(primitive['indices']).ravel().reshape(-1, 3)
        pt, ut = p[triangles], uv[triangles]
        areas = np.linalg.norm(np.cross(pt[:, 1] - pt[:, 0], pt[:, 2] - pt[:, 0]), axis=1) / 2
        delta1, delta2 = ut[:, 1] - ut[:, 0], ut[:, 2] - ut[:, 0]
        uv_areas = np.abs(delta1[:, 0] * delta2[:, 1] - delta1[:, 1] * delta2[:, 0]) / 2
        centers = pt.mean(axis=1)
        material = doc['materials'][primitive['material']]
        texture = material['pbrMetallicRoughness']['baseColorTexture']['index']
        image = images[doc['textures'][texture]['source']]
        texels = np.prod(image['size'])
        masks = {'whole-material': np.ones(len(triangles), dtype=bool),
                 'front-face-spatial-window': ((centers[:, 0] > .710) &
                     (centers[:, 1] > 1.61) & (centers[:, 1] < 1.76) &
                     (np.abs(centers[:, 2]) < .085))}
        for name, mask in masks.items():
            mask &= (areas > 1e-12) & (uv_areas > 1e-12)
            if not np.any(mask):
                continue
            density = np.sqrt(uv_areas[mask] * texels / areas[mask])
            regions.append({'material': material['name'], 'region': name,
                            'triangles': int(mask.sum()), 'image': image['index'],
                            'surfaceAreaM2': float(areas[mask].sum()),
                            'summedUVArea': float(uv_areas[mask].sum()),
                            'aggregateTexelsPerMeter': float(np.sqrt(uv_areas[mask].sum() * texels / areas[mask].sum())),
                            'triangleDensityP10MedianP90': np.percentile(density, [10, 50, 90]).tolist()})

report = {'source': str(source), 'sourceSHA256': hashlib.sha256(raw).hexdigest(),
          'images': images, 'regions': regions,
          'limits': 'Read-only source audit. Spatial face window is a declared diagnostic region, not semantic facial topology. UV area sums may include overlap; density is not a quality score. Source head maps already1024; increasing the loader cap alone cannot add detail.'}
(output / 'source-atlas-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
