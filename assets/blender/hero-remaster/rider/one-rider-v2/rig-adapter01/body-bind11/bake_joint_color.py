"""Bake a shared physical color field into existing head/cheek UVs, CPU only.

Geometry and all rig buffers remain immutable. The head edit is confined to a
6mm surface band; the repaired cheek uses the same graph solution. No polynomial
fit, global remesh or UV-proximity painting. Original source buffers are retained.
"""
from pathlib import Path
import copy
import hashlib
import heapq
import io
import json
import struct
import sys
import time
import numpy as np
from PIL import Image
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.ndimage import distance_transform_edt

start = time.monotonic()
source, destination, evidence = map(Path, sys.argv[1:])
assert not destination.exists(), 'Never overwrite a frozen candidate'
destination.parent.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
raw = source.read_bytes()
length = struct.unpack_from('<I', raw, 12)[0]
document = json.loads(raw[20:20 + length])
binary = raw[28 + length:]


def accessor(index):
    a = document['accessors'][index]
    v = document['bufferViews'][a['bufferView']]
    dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
    lanes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
    width = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], lanes), dtype=dtype, buffer=binary,
                      offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
                      strides=(v.get('byteStride', width * lanes), width)).copy()


def bitmap(index):
    v = document['bufferViews'][document['images'][index]['bufferView']]
    return np.asarray(Image.open(io.BytesIO(binary[v.get('byteOffset', 0):
        v.get('byteOffset', 0) + v['byteLength']])).convert('RGBA')).copy()


def linear(rgb):
    c = rgb / 255
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def srgb(c):
    return np.clip(np.where(c <= .0031308, c * 12.92,
                           1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055) * 255, 0, 255)


def sample(image, uv):
    h, w = image.shape[:2]
    x = np.clip(uv[:, 0] * w - .5, 0, w - 1)
    y = np.clip(uv[:, 1] * h - .5, 0, h - 1)
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    jx, jy = np.minimum(ix + 1, w - 1), np.minimum(iy + 1, h - 1)
    fx, fy = (x - ix)[:, None], (y - iy)[:, None]
    return ((image[iy, ix, :3] * (1 - fx) + image[iy, jx, :3] * fx) * (1 - fy)
            + (image[jy, ix, :3] * (1 - fx) + image[jy, jx, :3] * fx) * fy)


primitives = document['meshes'][1]['primitives']
assert [p['material'] for p in primitives] == [3, 4]
positions = [accessor(p['attributes']['POSITION']) for p in primitives]
uvs = [accessor(p['attributes']['TEXCOORD_0']) for p in primitives]
triangles = [accessor(p['indices']).ravel().reshape(-1, 3) for p in primitives]
images = [bitmap(5), bitmap(6)]
assert all(i.shape[:2] == (1024, 1024) for i in images)
ids, vertices, maps = {}, [], []
for p in positions:
    m = []
    for v in p:
        key = tuple(v)
        if key not in ids:
            ids[key] = len(vertices)
            vertices.append(v)
        m.append(ids[key])
    maps.append(np.array(m))
vertices = np.array(vertices)
shared = set(maps[0]) & set(maps[1])
assert len(shared) > 100
graph = [dict() for _ in vertices]
for t in [m[tri] for m, tri in zip(maps, triangles)]:
    for a, b in np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]):
        if a == b:
            continue
        distance = float(np.linalg.norm(vertices[a] - vertices[b]))
        assert distance > 0
        graph[a][b] = distance
        graph[b][a] = distance

band = .006
distance = np.full(len(vertices), np.inf)
queue = []
for v in shared:
    distance[v] = 0
    heapq.heappush(queue, (0, v))
while queue:
    d, v = heapq.heappop(queue)
    if d != distance[v] or d >= band:
        continue
    for neighbor, length in graph[v].items():
        candidate = d + length
        if candidate < distance[neighbor]:
            distance[neighbor] = candidate
            heapq.heappush(queue, (candidate, neighbor))

head_colors = linear(sample(images[0], uvs[0]))
colors = np.zeros((len(vertices), 3))
count = np.zeros(len(vertices))
np.add.at(colors, maps[0], head_colors)
np.add.at(count, maps[0], 1)
valid = count > 0
colors[valid] /= count[valid, None]
unknown = (distance < band)
unknown[maps[1]] = True
indices = np.flatnonzero(unknown)
lookup = {v: i for i, v in enumerate(indices)}
row, column, values = [], [], []
rhs = np.zeros((len(indices), 3))
anchor_edges = 0
for v, i in lookup.items():
    diagonal = 0
    for neighbor, length in graph[v].items():
        weight = 1 / length
        diagonal += weight
        if unknown[neighbor]:
            row.append(i)
            column.append(lookup[neighbor])
            values.append(-weight)
        else:
            assert count[neighbor] > 0
            rhs[i] += weight * colors[neighbor]
            anchor_edges += 1
    row.append(i)
    column.append(i)
    values.append(diagonal)
assert anchor_edges > 100
matrix = csr_matrix((values, (row, column)), shape=(len(indices), len(indices)))
solution = spsolve(matrix, rhs)
assert np.isfinite(solution).all()
assert solution.min() >= colors[valid & ~unknown].min() - 1e-8
assert solution.max() <= colors[valid & ~unknown].max() + 1e-8
colors[indices] = solution

updated_images, reports = [], []
for part, (image, uv, tri, mapping) in enumerate(zip(images, uvs, triangles, maps)):
    result = image.copy()
    h, w = image.shape[:2]
    covered = np.zeros((h, w), dtype=bool)
    changed_region = np.zeros((h, w), dtype=bool)
    tri_ids = np.arange(len(tri)) if part == 1 else np.flatnonzero(unknown[mapping[tri]].any(axis=1))
    for t in tri[tri_ids]:
        points = uv[t] * [w, h] - .5
        a, b, c = points
        transform = np.stack([b - a, c - a], axis=1)
        if abs(np.linalg.det(transform)) < 1e-10:
            continue
        low = np.maximum(np.ceil(points.min(axis=0)).astype(int), 0)
        high = np.minimum(np.floor(points.max(axis=0)).astype(int), [w - 1, h - 1])
        if np.any(high < low):
            continue
        yy, xx = np.mgrid[low[1]:high[1]+1, low[0]:high[0]+1]
        xy = np.stack([xx.ravel(), yy.ravel()], axis=1)
        delta = xy - a
        eb, ec = b - a, c - a
        determinant = eb[0] * ec[1] - eb[1] * ec[0]
        bc = np.stack([(delta[:, 0] * ec[1] - delta[:, 1] * ec[0]) / determinant,
                       (eb[0] * delta[:, 1] - eb[1] * delta[:, 0]) / determinant], axis=1)
        assert np.isfinite(bc).all(), 'Reject nonfinite UV barycentrics'
        weights = np.stack([1 - bc.sum(axis=1), bc[:, 0], bc[:, 1]], axis=1)
        inside = (weights.min(axis=1) >= -1e-7)
        xy, weights = xy[inside], weights[inside]
        if not len(xy):
            continue
        field = np.einsum('ij,jk->ik', weights, colors[mapping[t]], optimize=False)
        assert np.isfinite(field).all(), 'Reject nonfinite baked color'
        if part == 0:
            distances = np.minimum(distance[mapping[t]], band)
            d = np.minimum(np.sum(weights * distances, axis=1), band) / band
            blend = 1 - d * d * (3 - 2 * d)
            original = linear(image[xy[:, 1], xy[:, 0], :3])
            field = original * (1 - blend[:, None]) + field * blend[:, None]
        assert np.isfinite(field).all()
        result[xy[:, 1], xy[:, 0], :3] = np.round(srgb(field)).astype(np.uint8)
        covered[xy[:, 1], xy[:, 0]] = True
        changed_region[xy[:, 1], xy[:, 0]] = True
    if part == 1:
        d, nearest = distance_transform_edt(~covered, return_indices=True)
        margin = (~covered) & (d <= 16)
        result[margin, :3] = result[nearest[0][margin], nearest[1][margin], :3]
        changed_region |= margin
    assert np.array_equal(result[~changed_region], image[~changed_region])
    assert np.array_equal(result[:, :, 3], image[:, :, 3])
    changed = np.any(result != image, axis=2)
    reports.append({'part': part, 'trianglesBaked': len(tri_ids), 'changedTexels': int(changed.sum()),
                    'permittedRegionTexels': int(changed_region.sum()), 'outsideRegionExact': True})
    updated_images.append(result)

updated = copy.deepcopy(document)
new_binary = binary
for index, bitmap in zip([5, 6], updated_images):
    encoded = io.BytesIO()
    Image.fromarray(bitmap).save(encoded, format='PNG')
    data = encoded.getvalue()
    updated['images'][index]['bufferView'] = len(updated['bufferViews'])
    updated['images'][index]['mimeType'] = 'image/png'
    updated['bufferViews'].append({'buffer': 0, 'byteOffset': len(new_binary), 'byteLength': len(data)})
    new_binary += data
    new_binary += b'\0' * (-len(new_binary) % 4)
    Image.fromarray(bitmap).save(evidence / f'joint-albedo-{index}.png')
updated['buffers'][0]['byteLength'] = len(new_binary)
encoded_json = json.dumps(updated, separators=(',', ':')).encode()
encoded_json += b' ' * (-len(encoded_json) % 4)
total = 12 + 8 + len(encoded_json) + 8 + len(new_binary)
result = (struct.pack('<III', 0x46546c67, 2, total) + struct.pack('<II', len(encoded_json), 0x4e4f534a)
          + encoded_json + struct.pack('<II', len(new_binary), 0x004e4942) + new_binary)
for key in ['meshes', 'accessors', 'skins', 'nodes', 'materials', 'animations', 'textures', 'samplers']:
    assert updated.get(key) == document.get(key), key
assert new_binary[:len(binary)] == binary
assert source.read_bytes() == raw
destination.write_bytes(result)
report = {'sourceSHA256': hashlib.sha256(raw).hexdigest(),
          'destinationSHA256': hashlib.sha256(result).hexdigest(),
          'mechanism': 'Physical graph harmonic color with Dirichlet source anchors; head6mm band and whole repaired cheek, common vertex color at shared positions; original UV bake.',
          'sharedCanonicalVertices': len(shared), 'unknownVertices': len(indices),
          'anchorEdges': anchor_edges, 'bandM': band, 'images': reports,
          'originalBinaryRetainedExact': True, 'allGeometryRigUVMaterialDataExact': True,
          'seconds': time.monotonic() - start, 'CPUOnly': True,
          'limits': 'Appearance unaccepted. Raster filtering may leave seams despite the shared vertex field. Source color anchors include generated lighting; no eye anatomy or hair improvement.'}
(evidence / 'bake-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
