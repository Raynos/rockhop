"""Parent verifies literal future field domain; does not solve any weights."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/anatomical-field-design196'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB, worlds

frozen = json.loads((E / 'freeze.json').read_text())
for group in ('inputPins', 'recipeSettingsEvidencePins'):
    for path, record in frozen[group].items():
        data = Path(path).read_bytes()
        assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256']
scope = json.loads((E / 'source-anchors-and-scope.json').read_text())
source = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-preserving-garment185/operator/rider.glb')
g = GLB(source)
p = g.j['meshes'][0]['primitives'][0]
P = g.array(p['attributes']['POSITION'])
F = g.array(p['indices']).reshape(-1, 3)
U, q = np.unique(P, axis=0, return_inverse=True)
editable = set(scope['proposedEditablePhysicalIDs'])
assert len(editable) == 1328
assert scope['proposedEditableP0Rows'] == np.flatnonzero(np.isin(q, sorted(editable))).tolist()
assert len(scope['proposedEditableP0Rows']) == 1644
protected = set(scope['fixedCuffTwoRingIDs']) | set(scope['fixedHighTwoRingIDs']) | set(scope['fixed78BoundaryIDs'])
assert not editable & protected
for v in editable:
    assert scope['allEditableAliasGroups'][str(v)] == np.flatnonzero(q == v).tolist()
source_edges = {tuple(sorted((int(a), int(b)))) for t in q[F] for a, b in zip(t, np.roll(t, -1))}
assert all(tuple(e) in source_edges for e in scope['retainedOriginalGraphEdges'])
skin = g.j['skins'][0]
wm = worlds(g.j)
centres = {g.j['nodes'][i]['name'].removeprefix('fresh.'): wm[i][:3, 3] for i in skin['joints']}
upper = centres['forearm.L'] - centres['upperArm.L']
lower = centres['hand.L'] - centres['forearm.L']
normal = upper / np.linalg.norm(upper) + lower / np.linalg.norm(lower)
normal /= np.linalg.norm(normal)
signed = np.sum((U.astype(float) - centres['forearm.L']) * normal, axis=1)
assert np.isfinite(signed).all()
crossed = {tuple(e) for e in scope['retainedOriginalGraphEdges'] if signed[e[0]] * signed[e[1]] < 0}
assert len(crossed) == 91
assert crossed == {tuple(record['physicalEdge']) for record in scope['elbowPlaneCrossings']}
for record in scope['elbowPlaneCrossings']:
    a, b = record['physicalEdge']
    fraction = signed[a] / (signed[a] - signed[b])
    assert abs(fraction - record['sourceFractionFromFirst']) < 1e-12
    assert np.max(abs(U[a] + fraction * (U[b].astype(float) - U[a]) - record['sourcePositionM'])) < 1e-12
degree = Counter()
adjacent = {e: set() for e in crossed}
for t in q[F]:
    hits = [tuple(sorted((int(a), int(b)))) for a, b in zip(t, np.roll(t, -1)) if tuple(sorted((int(a), int(b)))) in crossed]
    if len(hits) == 2:
        a, b = hits
        adjacent[a].add(b)
        adjacent[b].add(a)
assert all(len(neighbors) == 2 for neighbors in adjacent.values())
visited, pending = set(), [min(crossed)]
while pending:
    e = pending.pop()
    if e not in visited:
        visited.add(e)
        pending.extend(adjacent[e] - visited)
assert visited == crossed
report = {
    'status': 'DORMANT_FIELD_SCOPE_VERIFIED_NO_WEIGHT_EXECUTION',
    'recipeEvidencePins': len(frozen['recipeSettingsEvidencePins']),
    'sourcePins': len(frozen['inputPins']), 'editablePhysicalNodes': 1328,
    'editableRows': 1644, 'allLiteralSourceAliasesChecked': True,
    'allProposedGraphEdgesSourceLiteral': True, 'protectedGuardsDisjoint': True,
    'independentlyVerifiedBoneBisectorClosedRingEdges': 91,
    'weightsComputed': 0, 'candidateGenerated': False,
    'limits': 'Only future scope/anchor graph verified. Harmonic stations, fades/truncation, anatomy, exported motion and contacts remain untested. Failed construction196 prevents field execution; construction must qualify first.'
}
output = E / (sys.argv[1] if len(sys.argv) > 1 else 'parent-review197.json')
assert not output.exists()
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
