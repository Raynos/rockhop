"""Parent checks literal preservation, scope and witnesses of one frozen sculpt."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import numpy as np
from scipy.spatial import cKDTree

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/source-star196'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

source = B / 'source-preserving-garment185/operator/rider.glb'
assert digest(source) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g = GLB(source)
p = g.j['meshes'][0]['primitives'][0]
attrs = {k: g.array(i) for k, i in p['attributes'].items()}
F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
P = attrs['POSITION']
U, q = np.unique(P, axis=0, return_inverse=True)
z = np.load(B / 'source-star196/construction.npz')
assert np.array_equal(z['positions'], z['attribute_POSITION'])
assert np.array_equal(z['sourceIndices'], F)
assert np.array_equal(z['sourcePhysicalPositions'], U)
contract = json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195/parent-construction-contract.json').read_text())
path = json.loads((B / 'source-seam191/next-construction-contract.json').read_text())['orderedProspectiveSeamPhysicalIDs']
scope = np.flatnonzero(np.isin(q[F], path).any(axis=1))
assert np.array_equal(z['changedSourceFaceIDs'], scope) and len(scope) == 168
inside = contract['exactReleasedInteriorPhysicalIDs']
clones = np.flatnonzero(np.isin(q, inside))
assert np.array_equal(z['clonedSourceRows'], clones)
assert np.array_equal(z['clonedNewRows'], np.arange(len(P), len(P) + len(clones)))
all_rows = np.r_[np.arange(len(P)), clones]
for key, original in attrs.items():
    assert np.array_equal(z['attribute_' + key][:len(P)], original)
    if key not in ('POSITION', 'NORMAL'):
        assert np.array_equal(z['attribute_' + key], original[all_rows])
for ti, target in enumerate(p.get('targets', [])):
    for key, accessor in target.items():
        assert np.array_equal(z[f'morph_{ti}_{key}'], g.array(accessor)[all_rows])
restored = z['indices'].copy()
remap = {int(n): int(s) for s, n in zip(clones, z['clonedNewRows'])}
for new, old in remap.items():
    restored[restored == new] = old
assert np.array_equal(restored, F)
outside = np.setdiff1d(np.arange(len(F)), scope)
assert np.array_equal(z['indices'][outside], F[outside])
assert z['indices'].shape == F.shape
lengths = np.linalg.norm(np.diff(U[path].astype(np.float64), axis=0), axis=1)
cumulative = np.r_[0., np.cumsum(lengths)]
u = dict(zip(path, cumulative / cumulative[-1]))
u[4041] = np.mean([u[i] for i in (3674, 3717, 4279, 4393)])
expected = U.copy()
for v in inside:
    expected[v, 1] = np.float32(float(U[1488, 1]) + u[v] * (float(U[13448, 1]) - float(U[1488, 1])))
assert np.array_equal(z['physicalPositions'], expected)
assert np.array_equal(z['attribute_POSITION'], np.r_[P, expected[q[clones]]])
assert len(np.unique(expected, axis=0)) == len(U)
prov = json.loads((B / 'source-star196/construction-provenance.json').read_text())
for group in prov['normalGroups']:
    normals = z['attribute_NORMAL'][group['newRows']]
    assert np.array_equal(normals, np.repeat(normals[:1], len(normals), axis=0))
    assert all(attrs['NORMAL'][row].view(np.uint32).tolist() == group['originalNormalBits'] for row in group['originalRows'])

def crosses(a, b):
    for aa, bb in ((a, b), (b, a)):
        e1, e2 = bb[1] - bb[0], bb[2] - bb[0]
        for start, end in zip(aa, np.roll(aa, -1, axis=0)):
            d = end - start
            h = np.cross(d, e2)
            det = float(e1 @ h)
            scale = np.linalg.norm(e1) * np.linalg.norm(e2) * np.linalg.norm(d)
            if abs(det) <= 1e-12 * scale:
                continue
            offset = start - bb[0]
            v0 = np.cross(offset, e1)
            u0, v, t = float(offset @ h) / det, float(d @ v0) / det, float(e2 @ v0) / det
            if min(u0, v, 1 - u0 - v, t, 1 - t) > 1e-10:
                return True
    return False

full = []
for mi, mesh in enumerate(g.j['meshes']):
    for pi, primitive in enumerate(mesh['primitives']):
        if (mi, pi) == (0, 0):
            full.extend(z['positions'][z['indices']].astype(np.float64))
        else:
            pos = g.array(primitive['attributes']['POSITION'])
            idx = g.array(primitive['indices']).reshape(-1, 3)
            full.extend(pos[idx].astype(np.float64))
full = np.array(full)
centres = full.mean(axis=1)
radii = np.linalg.norm(full - centres[:, None], axis=2).max(axis=1)
lo, hi = full.min(axis=1), full.max(axis=1)
tree = cKDTree(centres)
pairs = set()
for i in scope:
    for j in tree.query_ball_point(centres[i], radii[i] + radii.max() + 1e-12):
        if i != j and np.all(hi[i] >= lo[j] - 1e-12) and np.all(hi[j] >= lo[i] - 1e-12):
            pairs.add(tuple(sorted((int(i), int(j)))))
parent_hits = {pair for pair in sorted(pairs) if crosses(full[pair[0]], full[pair[1]])}
cross_data = json.loads((B / 'source-star196/rest-crossing-evidence.json').read_text())
pair_classes = Counter()
for w in cross_data['strictCrossings']:
    a, b = [full[i] for i in w['globalFaces']]
    assert np.array_equal(np.array([a, b]), np.array(w['trianglesM']))
    assert crosses(a, b)
    pair_classes[w['physicalSharedCorners']] += 1
reported = {tuple(w['globalFaces']) for w in cross_data['strictCrossings']}
assert reported <= parent_hits
report = {
    'status': 'PARENT_ACTUAL_SCULPT_PRESERVATION_AND_CROSSING_REVIEW',
    'sourceSHA256': digest(source), 'dumpSHA256': digest(B / 'source-star196/construction.npz'),
    'allOriginalAttributeMorphRowsExact': True, 'allClonedNongeometryFieldsLiteralSource': True,
    'outsideFaceIndicesExact': True, 'sourcePhysicalFaceIncidenceExact': True,
    'prescribedFloat32PositionsExact': True, 'releasedPhysicalVertices': 46,
    'sourceFaces': 168, 'newAccessorRows': len(clones),
    'actualStrictWitnessesVerified': len(cross_data['strictCrossings']),
    'independentChangedVersusAllFiveBroadphasePairs': len(pairs),
    'independentRelativeToleranceStrictCrossings': len(parent_hits),
    'additionalParentStrictPairs': sorted(parent_hits - reported),
    'crossingSharedCornerCounts': dict(pair_classes),
    'limits': 'No static number establishes anatomy, appearance or moving/contact/mobile acceptance. Parent must separately judge the frozen full audit and motion before promotion.'
}
assert not (E / 'parent-review.json').exists()
(E / 'parent-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
