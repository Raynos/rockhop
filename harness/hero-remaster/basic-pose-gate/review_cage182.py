"""Parent check of the actual frozen GLB; no mesh repair or rendering."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
EVIDENCE = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-guided-cage182'
MASTERS = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182')
SOURCE = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    raw = path.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + length]), raw[28 + length:]

def accessor(doc, binary, index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']])
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
                      offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
                      strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize)).copy()

manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
verified = []
for filename, record in manifest['files'].items():
    path = Path(filename)
    assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256'], filename
    verified.append(filename)
assert digest(SOURCE) == manifest['sourceDonorSHA256']
source, before = load(SOURCE)
doc, binary = load(MASTERS / 'neutral-assembly01.glb')
assert binary[:len(before)] == before
assert doc['meshes'][1:len(source['meshes'])] == source['meshes'][1:]
assert doc['meshes'][0]['primitives'][1:] == source['meshes'][0]['primitives'][1:]
for key in ['accessors', 'bufferViews', 'materials', 'images', 'textures', 'samplers']:
    assert doc.get(key, [])[:len(source.get(key, []))] == source.get(key, [])
for old, new in zip(source['nodes'], doc['nodes']):
    assert {k: v for k, v in old.items() if k != 'skin'} == new
assert not doc.get('skins') and not doc.get('animations')
assert all('skin' not in node for node in doc['nodes'])
data = np.load(MASTERS / 'bodydata01.npz')
cage = np.load(MASTERS / 'cage01.npz')
primitives = doc['meshes'][0]['primitives'] + doc['meshes'][-1]['primitives']
positions, faces, offset = [], [], 0
for i, primitive in enumerate(primitives):
    p = accessor(doc, binary, primitive['attributes']['POSITION'])
    f = accessor(doc, binary, primitive['indices']).reshape(-1, 3)
    prefix = 'p' + str(i) if i < 3 else 'newShellP'
    face_key = 'f' + str(i) if i < 3 else 'newShellF'
    assert np.array_equal(p, data[prefix]) and np.array_equal(f, data[face_key])
    positions.append(p)
    faces.append(f.astype(np.int64) + offset)
    offset += len(p)
p = np.concatenate(positions)
f = np.concatenate(faces)
physical, inverse = np.unique(p, axis=0, return_inverse=True)
f = inverse[f]
edges, directions = Counter(), defaultdict(list)
for triangle in f:
    for a, b in zip(triangle, np.roll(triangle, -1)):
        edge = tuple(sorted((int(a), int(b))))
        edges[edge] += 1
        directions[edge].append(bool(a < b))
t = physical[f].astype(np.float64)
area = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
counts = dict(referencedPhysicalVertices=len(np.unique(f)), triangles=len(f),
              degenerateFaces=int((area < 1e-12).sum()),
              nonmanifoldEdges=sum(n > 2 for n in edges.values()),
              wrongWindingEdges=sum(n == 2 and directions[e][0] == directions[e][1] for e, n in edges.items()),
              boundaryEdges=sum(n == 1 for n in edges.values()))
expected = json.loads((EVIDENCE / 'export-audit.json').read_text())
for key, other in [('degenerateFaces', 'combinedDegenerateBelow1e12'), ('nonmanifoldEdges', 'combinedNonmanifoldEdges'), ('wrongWindingEdges', 'combinedWrongWindingEdges'), ('boundaryEdges', 'combinedBoundaryEdges')]:
    assert counts[key] == expected[other]
lookup = {tuple(row): i for i, row in enumerate(physical)}
seams = {}
for name in ['hoodIDs', 'hemIDs', 'cuffLIDs', 'cuffRIDs']:
    q = cage['p'][cage[name]]
    ids = [lookup[tuple(row)] for row in q]
    good = 0
    for a, b in zip(ids, ids[1:] + ids[:1]):
        e = tuple(sorted((a, b)))
        good += edges[e] == 2 and directions[e][0] != directions[e][1]
    seams[name] = {'edges': len(ids), 'pairedOpposite': int(good)}
    assert good == expected['seamCoverage'][name]['pairedOpposite']
report = {'status': 'REJECTED_BEFORE_RENDER', 'verifiedFiles': verified,
          'sourceSHA256': digest(SOURCE), 'originalBINHeadHoodGlovePBRPreserved': True,
          'originalNodeTransformsPreserved': True, 'allActualGLBClothArraysMatchCombinedFreeze': True,
          'exportedReferencedPhysicalTopology': counts, 'finalSeams': seams,
          'movingEvidence': 'Not run: predecessor literal gate failed.',
          'limits': 'No repair, independent crossing rerun, appearance score, rig, weights, motion, game or device acceptance. Builder crossing counts are retained separately.'}
(EVIDENCE / 'parent-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'verifiedFiles': len(verified), 'topology': counts, 'seams': seams}))
