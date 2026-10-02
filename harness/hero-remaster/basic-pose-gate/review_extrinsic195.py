"""Parent source-topology review before the single local scalar trial."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

freeze = json.loads((E / 'freeze.json').read_text())
counts = {}
for group in ('recipeAndEvidenceFiles', 'inputPins'):
    for name, record in freeze[group].items():
        data = Path(name).read_bytes()
        assert len(data) == record['bytes']
        assert hashlib.sha256(data).hexdigest() == record['sha256']
    counts[group] = len(freeze[group])
g = GLB(B / 'source-preserving-garment185/operator/rider.glb')
pr = g.j['meshes'][0]['primitives'][0]
P = g.array(pr['attributes']['POSITION'])
F = g.array(pr['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
T = q[F]
old = json.loads((B / 'source-seam191/next-construction-contract.json').read_text())
path = old['orderedProspectiveSeamPhysicalIDs']
faces = np.flatnonzero(np.isin(T, path).any(axis=1)).tolist()
assert len(faces) == 168
reference = json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-review.json').read_text())
assert faces == reference['removedSourceFaceIDs']
edges = Counter(tuple(sorted((int(t[k]), int(t[(k+1) % 3])))) for t in T[faces] for k in range(3))
border_edges = {e for e, n in edges.items() if n == 1}
border = {v for e in border_edges for v in e}
interior = set(T[faces].ravel().tolist()) - border
assert len(border) == len(border_edges) == 78
assert interior == set(path) | {4041}
assert not [e for e in edges if set(e) <= border and e not in border_edges]
assert not [fi for fi in faces if set(T[fi]) <= border]
proposal = json.loads((E / 'prospective-contract.json').read_text())
assert sorted(interior) == proposal['exactReleasedInteriorPhysicalIDs']
assert sorted(set(faces) - set(old['boundaryContract']['unionSourceFaceIDs'])) == [3823, 3824]
alias = json.loads((E / 'source-interior-aliases.json').read_text())
for v in sorted(interior):
    a = alias['sourceRowAliases'][str(v)]
    assert a['originalSourceAccessorRows'] == np.flatnonzero(q == v).tolist()
    incident = np.flatnonzero((T == v).any(axis=1)).tolist()
    assert set(incident) <= set(faces)
    assert not a['incidentRetainedSourceFaceIDs']
    assert a['removedSourceCornerRows'] == sorted({int(r) for fi in incident for r in F[fi] if q[r] == v})
neighbors = {b if a == 4041 else a for a, b in edges if 4041 in (a, b)}
assert neighbors & set(path) == {3674, 3717, 4279, 4393}
assert neighbors - set(path) == {3951}
assert list(map(float, U[[1488, 13448], 1])) == proposal['exactFormula']['literalEndpointY_M']
# Validate original stations only; no prospective candidate coordinates are made.
lengths = np.linalg.norm(np.diff(U[path].astype(np.float64), axis=0), axis=1)
stations = np.r_[0., np.cumsum(lengths)] / lengths.sum()
assert len(stations) == 45 and np.all(np.diff(stations) > 0)
report = {
    'status': 'ONE_SOURCE_STAR_SCALAR_TRIAL_REGISTERED_UNACCEPTED',
    'frozenPinsVerified': counts, 'sourceFaces': 168,
    'additionalExplicitScopeFaces': [3823, 3824],
    'fixedBoundaryVertices': 78, 'releasedInteriorVertices': 46,
    'allReleasedIncidentFacesInScope': True, 'allSourceRowAliasesVerified': True,
    'boundaryOnlyTriangles': 0, 'interiorBoundaryToBoundaryEdges': 0,
    'originalPathStations': stations.tolist(),
    'normalDiagnosis': 'All18 failed194 chart-donor normals actually match retained numeric source normals; UV islands and normal continuity must be tracked independently.',
    'originalXZProjection': 'Frozen exact projection has55 overlaps; this is multilayer source sculpt, never a graph-surface guarantee.',
    'noCandidateGeometryCreated': True,
    'next': 'One append-only source-row clone trial with original XZ and168-face incidence; exact prescribed Y, no tuning. Preserve all original buffers/fields; record interior source-normal chart groups separately from UV. All rest, Float32, rooted routes and moving gates required.',
    'limits': 'Read-only registration is not construction, skin, art, gameplay/contact or mobile acceptance.'
}
assert not (E / 'parent-review.json').exists()
(E / 'parent-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
