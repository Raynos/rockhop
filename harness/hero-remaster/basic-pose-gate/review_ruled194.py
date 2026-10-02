"""Parent judgement of one frozen panel mesh, independently checking witnesses."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/source-ruled194'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


freeze = json.loads((E / 'freeze.json').read_text())
def verify_pins(records):
    pairs = records.items() if isinstance(records, dict) else [(r['path'], r) for r in records]
    for path, record in pairs:
        assert digest(path) == record['sha256'] and Path(path).stat().st_size == record['bytes']


for category in ['inputPins', 'recipePins', 'evidencePins', 'privateArtifactPins']:
    verify_pins(freeze[category])
source = B / 'source-preserving-garment185/operator/rider.glb'
assert digest(source) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g = GLB(source)
p = g.j['meshes'][0]['primitives'][0]
attrs = {k: g.array(ai) for k, ai in p['attributes'].items()}
P = attrs['POSITION']
F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
z = np.load(B / 'source-ruled194/construction.npz')
assert digest(B / 'source-ruled194/construction.npz') == 'ee45bb5e0e9612c9b8a3e7ac433fc02824f5ebff319f8da0217692164dd69777'
contract = json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-construction-contract.json').read_text())
assert z['removedSourceFaceIDs'].tolist() == contract['exactRemovedSourceFaceIDs']
kept = np.setdiff1d(np.arange(len(F)), z['removedSourceFaceIDs'])
assert np.array_equal(kept, z['sourceKeptFaceIDs'])
assert np.array_equal(z['indices'][:len(kept)], F[kept])
for key, original in attrs.items():
    assert np.array_equal(z['attribute_' + key][:len(P)], original)
assert np.array_equal(z['positions'], z['attribute_POSITION'])
for ti, target in enumerate(p.get('targets', [])):
    for key, ai in target.items():
        assert np.array_equal(z[f'morph_{ti}_{key}'][:len(P)], g.array(ai))
assert len(z['positions']) == len(P) + 4107
assert len(z['indices']) == len(kept) + 1369
assert np.count_nonzero(z['newDiscardedWeightMass']) == 0

# Independent directed physical cut incidence on actual Float32 output.
U, q = np.unique(z['positions'], axis=0, return_inverse=True)
tri_phys = q[z['indices']]
edges = defaultdict(list)
for fi, t in enumerate(tri_phys):
    for a, b in zip(t, np.roll(t, -1)):
        edges[tuple(sorted((int(a), int(b))))].append((int(a), int(b), fi))
assert not any(len(v) > 2 for v in edges.values())
assert not any(len(v) == 2 and v[0][:2] == v[1][:2] for v in edges.values())
boundary = contract['fixedOrientedBoundaryPhysicalIDs']
oldU, oldq = np.unique(P, axis=0, return_inverse=True)
coord_to_new = {tuple(v): i for i, v in enumerate(U)}
for a, b in zip(boundary, boundary[1:] + boundary[:1]):
    key = tuple(sorted((coord_to_new[tuple(oldU[a])], coord_to_new[tuple(oldU[b])])) )
    faces = edges[key]
    assert len(faces) == 2 and faces[0][:2] == tuple(reversed(faces[1][:2]))
    assert sum(fi < len(kept) for _, _, fi in faces) == 1


def crosses(a, b):
    """Open segment/triangle Moller witnesses; relative parallel tolerance."""
    for aa, bb in [(a, b), (b, a)]:
        e1, e2 = bb[1] - bb[0], bb[2] - bb[0]
        for start, end in zip(aa, np.roll(aa, -1, axis=0)):
            d = end - start
            h = np.cross(d, e2)
            det = float(e1 @ h)
            scale = np.linalg.norm(e1) * np.linalg.norm(e2) * np.linalg.norm(d)
            if abs(det) <= 1e-12 * scale:
                continue
            offset = start - bb[0]
            u = float(offset @ h) / det
            v0 = np.cross(offset, e1)
            v = float(d @ v0) / det
            t = float(e2 @ v0) / det
            if min(u, v, 1 - u - v, t, 1 - t) > 1e-10:
                return True
    return False


provenance = json.loads((B / 'source-ruled194/construction-provenance.json').read_text())
crossing_data = json.loads((B / 'source-ruled194/rest-crossing-evidence.json').read_text())
witnesses = crossing_data['strictCrossings']
assert len(witnesses) == 127
pair_classes = Counter()
source_faces = set()
for witness in witnesses:
    triangles = []
    kinds = []
    for ancestry in witness['ancestry']:
        assert (ancestry['mesh'], ancestry['primitive']) == (0, 0)
        if ancestry['newTriangle'] is None:
            fi = ancestry['sourceFace']
            assert fi in kept
            triangles.append(P[F[fi]].astype(float))
            kinds.append('retained')
            source_faces.add(fi)
        else:
            i = ancestry['newTriangle']
            triangles.append(z['positions'][z['indices'][len(kept) + i]].astype(float))
            kinds.append(provenance['fragments'][i]['panel'])
    assert np.array_equal(np.array(triangles), np.array(witness['trianglesM']))
    assert crosses(*triangles)
    pair_classes[tuple(kinds)] += 1
assert pair_classes == {('retained', 'central'): 42, ('retained', 'lateral'): 55, ('central', 'lateral'): 30}

audit = json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/source-weight-audit194/freeze.json').read_text())
for category in ['files', 'sourceInputPins']:
    verify_pins(audit[category])
star = set(json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-review.json').read_text())['removedSourceFaceIDs'])
report = {
    'status': 'REJECTED_ACTUAL_RULED_SURFACE_CROSSINGS_AND_BOUNDARY_NORMAL_PROVENANCE',
    'geometryAttempts': 1,
    'constructionSHA256': digest(B / 'source-ruled194/construction.npz'),
    'frozenFilesVerified': sum(len(freeze[k]) for k in ['recipePins', 'evidencePins', 'privateArtifactPins']),
    'inputPinsVerified': len(freeze['inputPins']),
    'originalSourceAccessorAndMorphRowsExact': True,
    'retainedOriginalFacesExact': True,
    'actualFixedCutEdgesOpposedAndUnsplit': len(boundary),
    'newTriangles': 1369,
    'newCornerRows': 4107,
    'strictWitnessesIndependentlyVerified': 127,
    'pairClasses': {str(k): v for k, v in pair_classes.items()},
    'crossedRetainedSourceFaceIDs': sorted(source_faces),
    'crossedRetainedFacesInsideAlternativeStar168': sorted(source_faces & star),
    'crossedRetainedFacesOutsideAlternativeStar168': sorted(source_faces - star),
    'boundaryNormalAliasesRejected': 18,
    'newSkinDiscardedMass': 0,
    'weightAuditFrozenFilesVerified': len(audit['files']),
    'weightAuditInputPinsVerified': len(audit['sourceInputPins']),
    'verifierSchemaCorrection': 'Corrected assumed generic freeze keys to actual recipe/evidence/private/input records before verification. No new candidate or dump changes.',
    'limits': 'No GLB, render, rig/weight adaptation, animation or art acceptance. Parent independently checks all127 strict witnesses, original arrays and cut incidence; complete rest broadphase/topology/UV and canonical newfield certification remain frozen sibling evidence. Star168 is not automatically a solution: it still requires an extrinsic surface and source-aware parameter map.',
    'next': 'Diagnose extrinsic panel overlap before another geometry trial; do not repeat the same straight-chord ruled embedding or repair normals alone. Keep all failed artifacts and source fields intact.',
}
assert not (E / 'parent-review.json').exists()
(E / 'parent-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if not k.startswith('crossedRetained')}))
