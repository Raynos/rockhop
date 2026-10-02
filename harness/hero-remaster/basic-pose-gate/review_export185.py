"""Parent inspect actual changed GLB and independently test hood surfaces."""
from collections import Counter, defaultdict
from pathlib import Path
import copy
import hashlib
import json
import struct
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path('/Users/raynos/projects/games/rockhop')
E = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185'
SOURCE = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
OUTPUT = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-preserving-garment185/operator/rider.glb')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+n]), raw[28+n:]
def array(doc, binary, index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    dt = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']])
    width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    return np.ndarray((a['count'], width), dtype=dt, buffer=binary,
        offset=v.get('byteOffset', 0)+a.get('byteOffset', 0),
        strides=(v.get('byteStride', width*dt.itemsize), dt.itemsize)).copy()
assert sha(SOURCE) == '186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'
assert sha(OUTPUT) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
before, source_bin = load(SOURCE)
after, binary = load(OUTPUT)
assert binary[:len(source_bin)] == source_bin
restored = copy.deepcopy(after)
assert len(after['accessors']) == len(before['accessors'])+1
assert len(after['bufferViews']) == len(before['bufferViews'])+1
restored['buffers'][0]['byteLength'] = before['buffers'][0]['byteLength']
restored['accessors'] = restored['accessors'][:-1]
restored['bufferViews'] = restored['bufferViews'][:-1]
restored['meshes'][0]['primitives'][2]['indices'] = before['meshes'][0]['primitives'][2]['indices']
assert restored == before
positions, faces, offset = [], [], 0
for primitive in after['meshes'][0]['primitives']:
    p = array(after, binary, primitive['attributes']['POSITION'])
    f = array(after, binary, primitive['indices']).reshape(-1, 3)
    positions.append(p)
    faces.append(f.astype(np.int64)+offset)
    offset += len(p)
original_hood = array(before, source_bin, before['meshes'][0]['primitives'][2]['indices']).reshape(-1, 3)
new_hood = array(after, binary, after['meshes'][0]['primitives'][2]['indices']).reshape(-1, 3)
changed = np.flatnonzero(np.any(original_hood != new_hood, axis=1))
assert changed.tolist() == [28, 29, 3813, 3829, 3847, 3848, 4105, 4106]
p, inverse = np.unique(np.concatenate(positions), axis=0, return_inverse=True)
f = inverse[np.concatenate(faces)]
edges, directions = Counter(), defaultdict(list)
for row in f:
    for a, b in zip(row, np.roll(row, -1)):
        key = tuple(sorted((int(a), int(b))))
        edges[key] += 1
        directions[key].append(bool(a < b))
t = p[f].astype(np.float64)
area = np.linalg.norm(np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]), axis=1)/2
counts = {'physicalVertices': len(np.unique(f)), 'triangles': len(f),
          'degenerateFaces': int((area < 1e-12).sum()),
          'nonmanifoldEdges': sum(n > 2 for n in edges.values()),
          'wrongWindingEdges': sum(n == 2 and directions[e][0] == directions[e][1] for e, n in edges.items()),
          'boundaryEdges': sum(n == 1 for n in edges.values())}
assert counts == dict(physicalVertices=22600, triangles=44969,
                     degenerateFaces=0, nonmanifoldEdges=0, wrongWindingEdges=0, boundaryEdges=237)
centres, lo, hi = t.mean(1), t.min(1), t.max(1)
radius = np.linalg.norm(t-centres[:, None, :], axis=2).max(1)
tree = cKDTree(centres)
hood_start = len(faces[0])+len(faces[1])
pairs = []
for i in range(hood_start, len(f)):
    js = np.asarray(tree.query_ball_point(centres[i], float(radius[i]+radius.max())+1e-12), dtype=np.int64)
    js = js[(js < hood_start) | (js > i)]
    mask = np.linalg.norm(centres[js]-centres[i], axis=1) <= radius[js]+radius[i]+1e-12
    mask &= np.all(lo[js] <= hi[i]+1e-12, axis=1) & np.all(lo[i] <= hi[js]+1e-12, axis=1)
    pairs.extend((i, int(z)) for z in js[mask])
pairs = np.asarray(pairs, dtype=np.int64)
shared = (f[pairs[:, 0], :, None] == f[pairs[:, 1], None, :]).any(2).sum(1)
adjacent_count = int((shared >= 2).sum())
pairs = pairs[shared < 2]
def intersects(a, b):
    result = np.zeros(len(a), dtype=bool)
    for A, B in [(a, b), (b, a)]:
        e1, e2 = B[:, 1]-B[:, 0], B[:, 2]-B[:, 0]
        for lane in range(3):
            origin, direction = A[:, lane], A[:, (lane+1)%3]-A[:, lane]
            h = np.cross(direction, e2)
            det = np.einsum('ij,ij->i', e1, h)
            valid = abs(det) > 1e-12
            safe = np.where(valid, det, 1.)
            s = origin-B[:, 0]
            u = np.einsum('ij,ij->i', s, h)/safe
            q = np.cross(s, e1)
            v = np.einsum('ij,ij->i', direction, q)/safe
            distance = np.einsum('ij,ij->i', e2, q)/safe
            result |= valid & (u > 1e-7) & (v > 1e-7) & (u+v < 1-1e-7) & (distance > 1e-7) & (distance < 1-1e-7)
    return result
hits = intersects(t[pairs[:, 0]], t[pairs[:, 1]])
assert not hits.any()
raw_witnesses = json.loads(Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-preserving-garment184/source-audit/all-strict-witnesses.json').read_text())
old_pairs = []
face_offsets = [0, len(faces[0]), hood_start]
for w in raw_witnesses:
    old_pairs.append([face_offsets[w[side]['sourcePrimitive']]+w[side]['sourceFace'] for side in ['A', 'B']])
old_pairs = np.asarray(old_pairs)
assert not intersects(t[old_pairs[:, 0]], t[old_pairs[:, 1]]).any()
result = {'status': 'PARENT_LITERAL_REST_HOOD_GATE_PASS_NOT_APPEARANCE',
          'sourceSHA256': sha(SOURCE), 'outputSHA256': sha(OUTPUT),
          'completeOriginalBINPrefixExact': True, 'onlyAllowedIndexReferenceAndAppendChanges': True,
          'allSourcePositionsNormalsUVPBRMorphSkinNodesExact': True,
          'changedOriginalHoodFaces': changed.tolist(), 'topology': counts,
          'independentHoodBroadphaseZeroOneSharedPairs': len(pairs),
          'excludedTwoPlusSharedAdjacentPairs': adjacent_count,
          'strictHoodSelfBodyGloveCrossings': 0, 'old11PairsTestedRegardlessAdjacency': 11,
          'limits': 'Coplanar/endpoint excluded in parent transverse checker; independent exact source coplanar classification and builder candidate fold audit remain separate receipts. Body/gloves/head unchanged; no fresh whole head collision, appearance, animation, contact, game or device acceptance.'}
(E / 'parent-review.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'topology': counts, 'independentStrictPairs': len(pairs), 'strictHits': 0, 'old11PairsClear': True}))
