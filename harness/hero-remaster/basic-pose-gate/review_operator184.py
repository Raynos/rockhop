"""Parent validate the frozen local edge list without evaluating new faces."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
E = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184'
C = E / 'operator-proposal/hood185-candidates.json'
candidate = json.loads(C.read_text())
source = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == candidate['sourceSHA256']
n = struct.unpack_from('<I', raw, 12)[0]
j, binary = json.loads(raw[20:20+n]), raw[28+n:]
def array(index):
    a = j['accessors'][index]
    v = j['bufferViews'][a['bufferView']]
    dt = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']])
    width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    return np.ndarray((a['count'], width), dtype=dt, buffer=binary,
        offset=v.get('byteOffset', 0)+a.get('byteOffset', 0),
        strides=(v.get('byteStride', width*dt.itemsize), dt.itemsize)).copy()
parts = j['meshes'][0]['primitives']
positions = [array(p['attributes']['POSITION']) for p in parts]
physical, inverse = np.unique(np.concatenate(positions), axis=0, return_inverse=True)
hood = parts[2]
f = array(hood['indices']).reshape(-1, 3)
hood_map = inverse[len(positions[0])+len(positions[1]):]
pf = hood_map[f]
edge_faces = defaultdict(list)
for i, t in enumerate(pf):
    for a, b in zip(t, np.roll(t, -1)):
        edge_faces[tuple(sorted((int(a), int(b))))].append(i)
seed = set(candidate['seedSourceHoodFaces'])
allowed = set(seed)
for owners in edge_faces.values():
    if seed.intersection(owners):
        allowed.update(owners)
assert allowed == set(candidate['allowedSourceFaceSlots'])
assert len(allowed) == 28
for c in candidate['initialCandidates']:
    owners = c['sourceFaces']
    edge = tuple(c['physicalEdgeIDs'])
    assert edge_faces[edge] == owners and len(owners) == 2
    assert set(owners).issubset(allowed)
    assert set(hood_map[c['sourceEdgeRows']]) == set(edge)
    assert set(c['sourceEdgeRows']).issubset(set(f[owners[0]]))
    assert set(c['sourceEdgeRows']).issubset(set(f[owners[1]]))
    opposite = [int(next(v for v in f[i] if v not in c['sourceEdgeRows'])) for i in owners]
    assert opposite == c['oppositeSourceRows']
assert len(candidate['initialCandidates']) == 23
first = next(c for c in candidate['initialCandidates'] if c['sourceEdgeRows'] == [49, 66])
assert first['sourceFaces'] == [4105, 4106] and first['oppositeSourceRows'] == [59, 50]
result = {'status': 'READ_ONLY_OPERATOR_SCOPE_VERIFIED_NO_NEW_TRIANGLES',
          'sourceSHA256': candidate['sourceSHA256'],
          'candidateListSHA256': hashlib.sha256(C.read_bytes()).hexdigest(),
          'seedFaces': 13, 'allowedOneRingFaceSlots': 28, 'initialEdges': 23,
          'firstOriginalEdge': [49, 66], 'firstOriginalFaceSlots': [4105, 4106],
          'parentGeometryGo': True,
          'goEffective': 'Only after this round184 finding is committed and explicit Go185 delivered.',
          'bounds': {'acceptedFlips': 32, 'candidateTests': 128, 'CPUThreads': 2, 'minutes': 12},
          'protected': 'All positions and active attributes/UV/PBR/binds/weights/morphs fixed; p0/head/gloves exact, 307+237 hood boundary and cuff edges fixed.',
          'requiredFirstGate': 'No old11 strict pairs, new hood/body/adjacent/coplanar overlaps, topology failures or source changes. One output, no hidden vertex move/scope expansion.',
          'limits': 'Candidate list is not a geometry, area, crossing or silhouette pass. Existing imported V5/V7 shape/weight changes remain separate unaccepted comparisons.'}
(E / 'operator-contract.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'allowedFaces': 28, 'initialEdges': 23, 'goAfterCommit': True}))
