"""Decode actual neck source PNG pixels, independently of Blender color access."""
import io
import json
import struct
import sys
from pathlib import Path
import numpy as np
from PIL import Image

source = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')
raw = source.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
gltf = json.loads(raw[20:20+size]); binary = raw[28+size:]

def accessor(index):
    a = gltf['accessors'][index]; view = gltf['bufferViews'][a['bufferView']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']]
    columns = {'VEC2': 2, 'VEC3': 3, 'SCALAR': 1}[a['type']]; width = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], columns), dtype=dtype, buffer=binary,
        offset=view.get('byteOffset', 0)+a.get('byteOffset', 0),
        strides=(view.get('byteStride', columns*width), width)).copy()

primitive = gltf['meshes'][1]['primitives'][0]
points = accessor(primitive['attributes']['POSITION']); uv = accessor(primitive['attributes']['TEXCOORD_0'])
faces = accessor(primitive['indices']).reshape(-1, 3)
unique, identities = np.unique(points, axis=0, return_inverse=True)
section = {}; adjacency = {}
for triangle in faces:
    cut = []
    for a, b in zip(triangle, np.roll(triangle, -1)):
        da, db = points[a, 1]-1.56, points[b, 1]-1.56
        if da*db >= 0: continue
        t = float(da/(da-db)); key = tuple(sorted((int(identities[a]), int(identities[b]))))
        section.setdefault(key, (points[a]*(1-t)+points[b]*t, uv[a]*(1-t)+uv[b]*t))
        cut.append(key)
    if len(cut) == 2:
        adjacency.setdefault(cut[0], set()).add(cut[1]); adjacency.setdefault(cut[1], set()).add(cut[0])
assert all(len(row) == 2 for row in adjacency.values())
remaining = set(section); rings = []
while remaining:
    start = next(iter(remaining)); ring = [start]; remaining.remove(start); previous = None; current = start
    while True:
        following = next(v for v in adjacency[current] if v != previous)
        if following == start: break
        ring.append(following); remaining.remove(following); previous, current = current, following
    rings.append(ring)
def area(ring):
    rows = [section[v][0] for v in ring]
    return abs(sum(a[0]*b[2]-b[0]*a[2] for a, b in zip(rows, rows[1:]+rows[:1]))/2)
outer = max(rings, key=area)
material = gltf['materials'][primitive['material']]
texture = gltf['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
image = gltf['images'][texture['source']]; view = gltf['bufferViews'][image['bufferView']]
png = Image.open(io.BytesIO(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB')
samples = []
for key in outer:
    u, v = section[key][1]
    x = min(png.width-1, max(0, int(u*png.width)))
    y = min(png.height-1, max(0, png.height-1-int((1-v)*png.height)))
    samples.append(png.getpixel((x, y)))
encoded = np.median(np.asarray(samples)/255, axis=0)
linear = np.where(encoded <= .04045, encoded/12.92, ((encoded+.055)/1.055)**2.4)
report = {'accepted': False, 'actualOuterSectionVertexCount': len(outer),
          'originalPNG': image['name'], 'textureSize': [png.width, png.height],
          'medianOriginalEncodedSRGB': encoded.tolist(), 'medianConvertedLinearRGB': linear.tolist(),
          'glTFBaseColorRole': 'sRGB encoded PNG; Blender constant Base Color needs linear values',
          'limits': ['Material numeric interpretation only; moving outfit appearance remains parent judged.']}
Path(sys.argv[1]).write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report))
