"""CPU-only surgical scalp preflight; dense source remains immutable.

Clip triangles against an anatomy-shaped contour, with shared intersections.
This stage is diagnostic, not an accepted compact scalp or texture bake.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out / 'cut.npz').exists(): raise RuntimeError('Do not overwrite a trial')
source = Path(a.input)
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()
before = sha(source); start = time.monotonic()
p = np.load(source); v = p['vertices']; f = p['faces']
# Native Y is up; +Z faces the nose. The contour avoids a planar hood cut.
azimuth = np.arctan2(v[:, 0], v[:, 2] + .035)
cosine = np.cos(azimuth)
height = np.where(cosine >= 0, .14 + .095 * cosine,
                  .14 + .22 * cosine)
d = v[:, 1] - height
inside = d <= 0
flags = inside[f]; count = flags.sum(axis=1)
kept = [f[count == 3]]
parts = []; crossings = []
for n in (1, 2):
    tri = f[count == n]
    mask = inside[tri]
    pivot = np.argmax(mask if n == 1 else ~mask, axis=1)
    tri = np.take_along_axis(tri, (pivot[:, None] + np.arange(3)) % 3, axis=1)
    pairs = np.stack((tri[:, [0, 1]], tri[:, [0, 2]]), axis=1)
    crossings.append(pairs.reshape(-1, 2)); parts.append((n, tri))
all_edges = np.sort(np.concatenate(crossings), axis=1)
edges, inverse = np.unique(all_edges, axis=0, return_inverse=True)
t = d[edges[:, 0]] / (d[edges[:, 0]] - d[edges[:, 1]])
new_v = v[edges[:, 0]] + t[:, None] * (v[edges[:, 1]] - v[edges[:, 0]])
offset = 0
for n, tri in parts:
    indices = inverse[offset:offset + len(tri) * 2].reshape(-1, 2) + len(v)
    offset += len(tri) * 2
    x, y = indices.T
    if n == 1: kept.append(np.stack((tri[:, 0], x, y), axis=1))
    else:
        kept.append(np.stack((x, tri[:, 1], tri[:, 2]), axis=1))
        kept.append(np.stack((x, tri[:, 2], y), axis=1))
vertices = np.concatenate((v, new_v)).astype(np.float32)
faces = np.concatenate(kept)
used, mapping = np.unique(faces, return_inverse=True)
faces = mapping.reshape(-1, 3).astype(np.int32)
vertices = vertices[used]
# Record exact retained source identities, including untouched face coordinates.
np.savez(out / 'cut.npz', vertices=vertices, faces=faces,
         source_vertex_indices=used, cut_edge_vertices=edges,
         cut_vertex_positions=new_v, source_sha256=before)
boundary_edges = np.sort(np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]],
                                        faces[:, [2, 0]])), axis=1)
unique, counts = np.unique(boundary_edges, axis=0, return_counts=True)
np.savez(out / 'boundary.npz', edges=unique[counts == 1],
         nonmanifold_edges=unique[counts > 2])
report = dict(status='UNACCEPTED diagnostic cut; no scalp/repair/bake',
              source=str(source), sourceSHA256=before,
              sourceSHA256After=sha(source), sourceVertices=len(v),
              sourceFaces=len(f), retainedVertices=len(vertices),
              retainedFaces=len(faces), cutEdgeIntersections=len(new_v),
              boundaryEdges=int(np.sum(counts == 1)),
              nonmanifoldEdges=int(np.sum(counts > 2)),
              contour=dict(frontHeight=.235, sideHeight=.14,
                           rearHeight=-.08, azimuthCenterZ=-.035),
              wallSeconds=time.monotonic() - start,
              limits=['Contour is provisional and must preserve brows/ears.',
                      'Boundary topology alone does not imply visual quality.',
                      'No decimation, whole-head voxel operation, or GPU work.'])
assert report['sourceSHA256After'] == before
(out / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
