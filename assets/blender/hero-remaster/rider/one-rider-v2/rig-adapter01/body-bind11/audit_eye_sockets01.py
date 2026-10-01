"""Read-only front surface raster and installed CC0 eye geometry audit.

Orthographic CPU source inspection, not moving/game acceptance evidence.
No source changes, decimation, remeshing or texture painting.
"""
from pathlib import Path
import hashlib
import io
import json
import struct
import numpy as np
from PIL import Image, ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
source = root / 'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
out = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/eye-sockets01')
out.mkdir(parents=True, exist_ok=True)
raw = source.read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]


def array(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    step = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(v.get('byteStride', width * step), step)).copy()


primitive = doc['meshes'][1]['primitives'][0]
positions = array(primitive['attributes']['POSITION'])
normals = array(primitive['attributes']['NORMAL'])
uv = array(primitive['attributes']['TEXCOORD_0'])
faces = array(primitive['indices']).reshape(-1, 3)
view = doc['bufferViews'][doc['images'][5]['bufferView']]
atlas = np.asarray(Image.open(io.BytesIO(binary[view['byteOffset']:view['byteOffset'] + view['byteLength']])).convert('RGB'))
main_vertices, main_triangles = len(positions), len(faces)
cheek = doc['meshes'][1]['primitives'][1]
cheek_positions = array(cheek['attributes']['POSITION'])
positions = np.concatenate([positions, cheek_positions])
normals = np.concatenate([normals, array(cheek['attributes']['NORMAL'])])
uv = np.concatenate([uv, array(cheek['attributes']['TEXCOORD_0'])])
faces = np.concatenate([faces, array(cheek['indices']).reshape(-1, 3) + main_vertices])
cheek_view = doc['bufferViews'][doc['images'][6]['bufferView']]
cheek_atlas = np.asarray(Image.open(io.BytesIO(binary[cheek_view['byteOffset']:cheek_view['byteOffset'] + cheek_view['byteLength']])).convert('RGB'))
width, height = 1400, 1600
z_min, z_max, y_min, y_max = -.12, .12, 1.48, 1.82
screen = np.column_stack(((z_max - positions[:, 2]) / (z_max - z_min) * (width - 1),
                         (y_max - positions[:, 1]) / (y_max - y_min) * (height - 1)))
depth = np.full((height, width), -np.inf)
textured = np.zeros((height, width, 3), np.uint8) + 28
gray = textured.copy()
surface_index = np.full((height, width), -1, np.int32)
for fi, face in enumerate(faces):
    p = screen[face].astype(float)
    if p[:, 0].max() < 0 or p[:, 0].min() > width - 1 or p[:, 1].max() < 0 or p[:, 1].min() > height - 1:
        continue
    a, b = p[1] - p[0], p[2] - p[0]
    determinant = a[0] * b[1] - a[1] * b[0]
    if abs(determinant) < 1e-9: continue
    xmin, ymin = np.maximum(np.floor(p.min(0)).astype(int), 0)
    xmax, ymax = np.minimum(np.ceil(p.max(0)).astype(int), [width - 1, height - 1])
    yy, xx = np.mgrid[ymin:ymax + 1, xmin:xmax + 1]
    dx, dy = xx - p[0, 0], yy - p[0, 1]
    u = (dx * (p[2, 1] - p[0, 1]) - dy * (p[2, 0] - p[0, 0])) / determinant
    v = ((p[1, 0] - p[0, 0]) * dy - (p[1, 1] - p[0, 1]) * dx) / determinant
    bary = np.stack([1 - u - v, u, v], axis=-1)
    x = np.einsum('...i,i->...', bary, positions[face, 0])
    region = depth[ymin:ymax + 1, xmin:xmax + 1]
    keep = (bary.min(-1) >= -1e-8) & (x > region)
    if not keep.any(): continue
    tex = np.einsum('...i,ij->...j', bary, uv[face])
    normal = np.einsum('...i,ij->...j', bary, normals[face])
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-12)
    shade = .25 + .75 * np.maximum(0, normal[..., 0] * .92 + normal[..., 1] * .35)
    bitmap = atlas if fi < main_triangles else cheek_atlas
    tx = np.clip((tex[..., 0] * bitmap.shape[1]).astype(int), 0, bitmap.shape[1] - 1)
    ty = np.clip((tex[..., 1] * bitmap.shape[0]).astype(int), 0, bitmap.shape[0] - 1)
    textured[ymin:ymax + 1, xmin:xmax + 1][keep] = bitmap[ty, tx][keep]
    gray[ymin:ymax + 1, xmin:xmax + 1][keep] = np.repeat((shade * 220).clip(0, 255)[..., None], 3, axis=-1)[keep]
    surface_index[ymin:ymax + 1, xmin:xmax + 1][keep] = fi
    region[keep] = x[keep]

for name, values in [('textured', textured), ('gray', gray)]:
    Image.fromarray(values).save(out / f'orthographic-source-{name}.png')
private = root / 'rig-adapter01/body-bind11/eye-sockets01'
private.mkdir(parents=True, exist_ok=True)
np.savez_compressed(private / 'front-surface.npz', depth=depth, faceIndex=surface_index,
                    zBounds=[z_min, z_max], yBounds=[y_min, y_max])
_, canonical = np.unique(np.round(positions.astype(float) / 1e-7).astype(np.int64), axis=0, return_inverse=True)
canonical_faces = canonical[faces]
edges = np.sort(np.concatenate([canonical_faces[:, [0, 1]], canonical_faces[:, [1, 2]], canonical_faces[:, [2, 0]]]), axis=1)
unique_edges, counts = np.unique(edges, axis=0, return_counts=True)
representative = np.zeros((canonical.max() + 1, 3))
representative[canonical] = positions
boundary_midpoints = representative[unique_edges[counts == 1]].mean(axis=1)
eyes = []
for sign in [-1, 1]:
    centre = np.array([.746, 1.694, sign * .033])
    roi = (positions[:, 0] > .72) & (np.abs(positions[:, 1] - centre[1]) < .013) & (np.abs(positions[:, 2] - centre[2]) < .022)
    boundary_roi = (boundary_midpoints[:, 0] > .72) & (np.abs(boundary_midpoints[:, 1] - centre[1]) < .013) & (np.abs(boundary_midpoints[:, 2] - centre[2]) < .022)
    profile = []
    for y in [1.688, 1.694, 1.700, 1.706]:
        row = round((y_max - y) / (y_max - y_min) * (height - 1))
        column = round((z_max - centre[2]) / (z_max - z_min) * (width - 1))
        profile.append({'yM': y, 'zM': centre[2], 'frontXM': float(depth[row, column])})
    eyes.append({'sideZSign': sign, 'approximateFramingCentreM': centre.tolist(),
                 'ROIHalfHeightM': .013, 'ROIHalfWidthM': .022, 'frontMinimumXM': .72,
                 'verticesInROI': int(roi.sum()), 'boundaryEdgesInROI': int(boundary_roi.sum()),
                 'centreDepthProfile': profile})
eye_path = Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/high-poly/high-poly.obj')
verts, polys = [], []
for line in eye_path.read_text().splitlines():
    if line.startswith('v '): verts.append([float(x) for x in line.split()[1:4]])
    if line.startswith('f '): polys.append([int(x.split('/')[0]) - 1 for x in line.split()[1:]])
verts = np.array(verts)
edges = np.array([(a, b) for poly in polys for a, b in zip(poly, poly[1:] + poly[:1])])
adj = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(verts), len(verts))).tocsr()
components, labels = connected_components(adj, directed=False)
parts = []
for i in range(components):
    p = verts[labels == i]
    parts.append({'vertices': len(p), 'minRaw': p.min(0).tolist(), 'maxRaw': p.max(0).tolist(), 'meanRaw': p.mean(0).tolist()})
report = {'sourceSHA256': hashlib.sha256(raw).hexdigest(), 'sourceHeadVertices': len(positions),
    'sourceHeadTriangles': len(faces), 'headBoundsM': [positions.min(0).tolist(), positions.max(0).tolist()],
    'includedPrimitives': ['Original head', 'Reconstructed cheek with shared color bake'],
    'projection': {'front': '+X looking -X', 'horizontal': '-Z', 'vertical': '+Y',
                   'zBoundsM': [z_min, z_max], 'yBoundsM': [y_min, y_max], 'pixels': [width, height]},
    'privateSurfaceData': str(private / 'front-surface.npz'),
    'eyes': eyes, 'boundaryWeldToleranceM': 1e-7,
    'eyeDonor': {'path': str(eye_path), 'sha256': hashlib.sha256(eye_path.read_bytes()).hexdigest(),
        'vertices': len(verts), 'polygons': len(polys), 'components': parts,
        'licenseHeader': eye_path.read_text().splitlines()[:12]},
    'limits': 'Unlit atlas and directional gray CPU source projection, not game PBR/motion acceptance. Eye donor raw coordinates require measured fit. No geometry or textures changed.'}
assert source.read_bytes() == raw
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
