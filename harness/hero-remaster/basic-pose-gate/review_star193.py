"""Parent checks the external closed-star proposal without running its scripts."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/physical-cut193'
X = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/panel-surgery192')
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

pins = {}


def pin(path, expected=None):
    data = Path(path).read_bytes()
    h = hashlib.sha256(data).hexdigest()
    assert expected is None or h == expected
    pins[str(path)] = {'sha256': h, 'bytes': len(data)}
    return data


receipt = json.loads(pin(X / 'next-operator-receipt.json', 'd696726dd830fe419f6db4ad556180fc50e3f61b316804809f4055aed0625b5e'))
for record in receipt['evidence']:
    pin(X / record['file'], record['sha256'])
source = B / 'source-preserving-garment185/operator/rider.glb'
pin(source, receipt['sourceSHA256'])
g = GLB(source)
pr = g.j['meshes'][0]['primitives'][0]
P = g.array(pr['attributes']['POSITION'])
F = g.array(pr['indices']).reshape(-1, 3).astype(np.int64)
U, quotient = np.unique(P, axis=0, return_inverse=True)
U = U.astype(np.float64)
T = quotient[F]
contract = json.loads(pin(B / 'source-seam191/next-construction-contract.json'))
seam = contract['orderedProspectiveSeamPhysicalIDs']
assert len(seam) == len(set(seam)) == 45
removed = set(np.flatnonzero(np.isin(T, seam).any(axis=1)).tolist())
assert len(removed) == 168
assert sorted(removed) == receipt['nextOperator']['removedSourceFaceIDs']
scope = set(contract['boundaryContract']['unionSourceFaceIDs'])
assert sorted(removed - scope) == [3823, 3824]

edges = defaultdict(list)
for fi, t in enumerate(T):
    for a, b in zip(t, np.roll(t, -1)):
        a, b = int(a), int(b)
        edges[tuple(sorted((a, b)))].append((a, b, fi))
boundary = []
dual = defaultdict(set)
for key, owners in edges.items():
    gone = [x for x in owners if x[2] in removed]
    kept = [x for x in owners if x[2] not in removed]
    if len(gone) == 2:
        a, b = [x[2] for x in gone]
        dual[a].add(b)
        dual[b].add(a)
    elif len(gone) == 1:
        assert len(kept) == 1
        # Reverse the retained direction: this is new-panel fill winding.
        a, b, fi = kept[0]
        boundary.append((b, a, gone[0][2], fi))


def components(nodes, graph):
    left = set(nodes)
    result = []
    while left:
        stack = [min(left)]
        found = set()
        while stack:
            v = stack.pop()
            if v in found:
                continue
            found.add(v)
            left.discard(v)
            stack.extend(graph.get(v, set()) - found)
        result.append(sorted(found))
    return result


assert len(components(removed, dual)) == 1
domain_vertices = set(T[sorted(removed)].ravel().tolist())
domain_edges = {key for key, owners in edges.items() if any(x[2] in removed for x in owners)}
euler = len(domain_vertices) - len(domain_edges) + len(removed)
assert euler == 1
assert len(boundary) == 78
outgoing = defaultdict(list)
incoming = Counter()
for a, b, *_ in boundary:
    outgoing[a].append(b)
    incoming[b] += 1
assert all(len(v) == 1 and incoming[k] == 1 for k, v in outgoing.items())
start = min(outgoing)
loop = [start]
v = outgoing[start][0]
while v != start:
    assert v not in loop
    loop.append(v)
    v = outgoing[v][0]
assert len(loop) == 78
external_loop = receipt['nextOperator']['newLoopOrderedPhysicalIDs']
assert set(zip(loop, loop[1:] + loop[:1])) == set(zip(external_loop, external_loop[1:] + external_loop[:1]))
for v in loop:
    link = defaultdict(set)
    for fi in np.flatnonzero((T == v).any(axis=1)):
        if int(fi) in removed:
            continue
        a, b = [int(x) for x in T[fi] if x != v]
        link[a].add(b)
        link[b].add(a)
    assert len(components(link, link)) == 1
    assert sum(len(ns) == 1 for ns in link.values()) == 2
assert not {1571, 13219} & set(loop)
assert {1488, 13448} <= set(loop)
assert min(U[[1488, 13448], 1]) >= 1.30

# Independent sublevel union-find, all source faces except the declared cut.
graph = defaultdict(set)
for key, owners in edges.items():
    if any(x[2] not in removed for x in owners):
        a, b = key
        graph[a].add(b)
        graph[b].add(a)
section = json.loads(pin(B / 'source-axilla189/section-fixed-03.json'))
roots = {l['geometricClass']: {v for seg in l['segments'] for ep in seg['endpoints'] for v in ep.get('sourcePhysicalEdge', []) if U[v, 1] < 1.13} for l in section['loops']}
parents = np.arange(len(U))
active = np.zeros(len(U), bool)
tags = np.zeros(len(U), np.uint8)
for bit, label in [(1, 'central_Z0_straddling'), (2, 'positiveZ_lateral')]:
    for v in roots[label]:
        tags[v] |= bit


def find(v):
    while int(parents[v]) != v:
        parents[v] = parents[int(parents[v])]
        v = int(parents[v])
    return v


attachment = None
for y in np.unique(U[:, 1]):
    ids = np.flatnonzero(U[:, 1] == y)
    active[ids] = True
    for a in ids:
        for b in graph[int(a)]:
            if active[b]:
                x, z = find(int(a)), find(b)
                if x != z:
                    parents[z] = x
                    tags[x] |= tags[z]
    if any(tags[find(int(a))] == 3 for a in ids):
        attachment = float(y)
        break
assert attachment == receipt['nextOperator']['unsealedOriginalPositionAttachmentY_M']
assert 1.30 <= attachment <= 1.32
for path, record in pins.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == record['sha256']
E.mkdir(parents=True, exist_ok=True)
report = {
    'status': 'CLOSED_STAR_SOURCE_CUT_DOMAIN_PASS_ONLY_NO_RESEAL_OR_ASSET',
    'pins': pins,
    'removedSourceFaceIDs': sorted(removed),
    'additionalScopeFacesExplicitlyRequired': [3823, 3824],
    'sourcePositionsChanged': False,
    'removedRegionEdgeDualComponents': 1,
    'removedRegionEuler': euler,
    'orientedFillBoundaryPhysicalIDs': loop,
    'boundaryEdges': 78,
    'retainedVertexLinkPinches': 0,
    'oldChordEndpointsInterior': [1571, 13219],
    'newHighPerimeterEndpoints': [1488, 13448],
    'unsealedAttachmentY_M': attachment,
    'windingLabelClarification': 'Receipt loop agrees with fill winding, opposite retained faces. Parent initially expected the ancillary retained-oriented label; literal directed-edge check corrected this verifier assumption before report generation. No geometry generated.',
    'limits': 'Original-position cut-domain diagnostics only. No generated mesh, cap, UV, normals, rig, motion, skin/contact or visual acceptance. External scripts were inspected/pinned, never executed or modified. A reseal must recompute all gates on its actual Float32 output.',
}
assert not (E / 'parent-review.json').exists()
(E / 'parent-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ['pins', 'removedSourceFaceIDs', 'orientedFillBoundaryPhysicalIDs']}))
