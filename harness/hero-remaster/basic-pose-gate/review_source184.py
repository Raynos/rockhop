"""Verify source audit provenance, topology and literal crossing witnesses."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import struct
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
E = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184'
report = json.loads((E / 'source-audit/report.json').read_text())
verified = []
for record in report['inputHashes'] + report['privateOutputs']:
    p = Path(record['path'])
    assert p.stat().st_size == record['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == record['SHA256']
    verified.append(record)
source = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
raw = source.read_bytes()
length = struct.unpack_from('<I', raw, 12)[0]
doc, binary = json.loads(raw[20:20 + length]), raw[28 + length:]
def accessor(index):
    a = doc['accessors'][index]
    view = doc['bufferViews'][a['bufferView']]
    dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']])
    width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
        offset=view.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize)).copy()
parts = []
positions, faces, offset = [], [], 0
for primitive in doc['meshes'][0]['primitives']:
    p = accessor(primitive['attributes']['POSITION'])
    f = accessor(primitive['indices']).reshape(-1, 3)
    parts.append((p, f))
    positions.append(p)
    faces.append(f.astype(np.int64) + offset)
    offset += len(p)
p, inverse = np.unique(np.concatenate(positions), axis=0, return_inverse=True)
f = inverse[np.concatenate(faces)]
edges, directions = Counter(), defaultdict(list)
for row in f:
    for a, b in zip(row, np.roll(row, -1)):
        e = tuple(sorted((int(a), int(b))))
        edges[e] += 1
        directions[e].append(bool(a < b))
t = p[f].astype(np.float64)
areas = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
counts = {'degenerateFaces': int((areas < 1e-12).sum()),
          'nonmanifoldEdges': sum(n > 2 for n in edges.values()),
          'wrongWindingEdges': sum(n == 2 and directions[e][0] == directions[e][1] for e, n in edges.items()),
          'boundaryEdges': sum(n == 1 for n in edges.values())}
assert counts == dict(degenerateFaces=0, nonmanifoldEdges=0, wrongWindingEdges=0, boundaryEdges=237)
witnesses = json.loads(Path(report['privateOutputs'][1]['path']).read_text())
assert isinstance(witnesses, list) and len(witnesses) == 11
largest_error = 0.
for witness in witnesses:
    triangles = {}
    for side in ['A', 'B']:
        face = witness[side]
        vertices, indices = parts[face['sourcePrimitive']]
        ids = indices[face['sourceFace']]
        assert ids.tolist() == face['sourceVertexIDs']
        triangle = vertices[ids].astype(np.float64)
        assert np.array_equal(triangle, np.asarray(face['sourceFloat32Positions']))
        triangles[side] = triangle
    hit = witness['strictInteriorWitness']
    owner = hit['edgeOwner']
    opposite = 'B' if owner == 'A' else 'A'
    a, b = hit['edgeVertexLanes']
    parameter = hit['edgeParameter']
    barycentric = np.asarray(hit['oppositeTriangleBarycentric'])
    assert 0 < parameter < 1 and np.all(barycentric > 0)
    edge_point = triangles[owner][a] * (1 - parameter) + triangles[owner][b] * parameter
    face_point = barycentric @ triangles[opposite]
    error = float(np.linalg.norm(edge_point - face_point))
    assert error < 1e-12
    largest_error = max(largest_error, error)
for i in [0, 1]:
    played = json.loads((E / 'parent-playback' / f'played-{i}.json').read_text())
    assert played['video']['ended'] and played['video']['muted'] and not played['errors']
result = {'status': 'SOURCE_TOPOLOGY_AND_LITERAL_HOOD_WITNESSES_VERIFIED',
          'verifiedInputPrivateHashes': verified, 'parentDirectSourceTopology': counts,
          'parentLiteralSourceCrossingWitnessesVerified': len(witnesses),
          'maxWitnessPointErrorM': largest_error,
          'specialistFullSourceBroadphase': report['strictCrossings']['candidateCounts'],
          'specialistRestStrictPairs': 11, 'parentWholeBroadphaseRerun': False,
          'parentMovingEvidence': 'Both source neutral orbits played to end; 48 ordered decoded gray/PBR frames inspected. Source silhouette promising; not arbitrary pose or target-score acceptance.',
          'limits': 'Head/cheek and glove self/hood contacts not exhaustively tested; coplanar/endpoint excluded. No repair, rig, weights, seated motion, art score, game or device acceptance.'}
(E / 'parent-review.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'hashes': len(verified), 'topology': counts, 'witnesses': len(witnesses), 'maxErrorM': largest_error}))
