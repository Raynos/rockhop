"""Independent mask, graph and maxflow check; no geometry construction."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import json
import sys
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/physical-cut193'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

pins = {}


def read(path):
    data = path.read_bytes()
    pins[str(path)] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return json.loads(data)


x = read(B / 'physical-cut193/literal-separator.json')
source = B / 'source-preserving-garment185/operator/rider.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == x['sourceSHA256']
g = GLB(source)
pr = g.j['meshes'][0]['primitives'][0]
P = g.array(pr['attributes']['POSITION'])
F = g.array(pr['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
U = U.astype(float)
T = q[F]
contract = read(B / 'source-seam191/next-construction-contract.json')
scope = set(contract['boundaryContract']['unionSourceFaceIDs'])
edges = defaultdict(list)
for fi, t in enumerate(T):
    for a, b in zip(t, np.roll(t, -1)):
        edges[tuple(sorted((int(a), int(b))))].append((int(a), int(b), fi))
eligible = {e for e, owners in edges.items() if max(U[list(e), 1]) < 1.30 and len(owners) == 2 and all(v[2] in scope for v in owners)}
assert eligible == {tuple(v['physicalEdge']) for v in x['eligibleUnitEdges']}
cut = {tuple(v['physicalEdge']) for v in x['cutEdges']}
assert len(cut) == 46 and cut <= eligible
removed = {v[2] for e in cut for v in edges[e]}
assert removed == set(x['finalMaskAudit']['removedFaces']) and len(removed) == 47 and removed <= scope
assert not x['fanCompletionSteps']
section = read(B / 'source-axilla189/section-fixed-03.json')
roots = {l['geometricClass']: {v for s in l['segments'] for ep in s['endpoints'] for v in ep.get('sourcePhysicalEdge', []) if U[v, 1] < 1.13} for l in section['loops']}
for label in ['central_Z0_straddling', 'positiveZ_lateral']:
    assert roots[label] == set(x['roots'][label])

# Independently reconstruct protected connected components, then solve maxflow.
parent = np.arange(len(U))


def find(a):
    while int(parent[a]) != a:
        parent[a] = parent[int(parent[a])]
        a = int(parent[a])
    return a


for e in sorted(edges):
    if max(U[list(e), 1]) < 1.30 and e not in eligible:
        a, b = map(find, e)
        if a != b:
            parent[max(a, b)] = min(a, b)
keys = sorted({find(v) for e in edges if max(U[list(e), 1]) < 1.30 for v in e})
ids = {v: i for i, v in enumerate(keys)}
capacity = Counter()
for a, b in eligible:
    a, b = find(a), find(b)
    if a != b:
        capacity[(ids[a], ids[b])] += 1
        capacity[(ids[b], ids[a])] += 1
s, t = len(ids), len(ids) + 1
for v in {find(v) for v in roots['central_Z0_straddling']}:
    capacity[(s, ids[v])] = len(eligible) + 1
for v in {find(v) for v in roots['positiveZ_lateral']}:
    capacity[(ids[v], t)] = len(eligible) + 1
entries = sorted(capacity)
matrix = csr_matrix(([capacity[v] for v in entries], ([v[0] for v in entries], [v[1] for v in entries])), shape=(t + 1, t + 1), dtype=np.int64)
result = maximum_flow(matrix, s, t)
assert result.flow_value == x['flow'] == len(cut) == 46

boundary = []
domain_edges = set()
for e, owners in edges.items():
    gone = [v for v in owners if v[2] in removed]
    if gone:
        domain_edges.add(e)
    if len(gone) == 1:
        assert len(owners) == 2
        boundary.append(gone[0])
assert len(boundary) == 49
outgoing = defaultdict(list)
incoming = Counter()
for a, b, _ in boundary:
    outgoing[a].append(b)
    incoming[b] += 1
assert all(len(v) == incoming[k] == 1 for k, v in outgoing.items())
loop = [min(outgoing)]
v = outgoing[loop[0]][0]
while v != loop[0]:
    assert v not in loop
    loop.append(v)
    v = outgoing[v][0]
assert len(loop) == 49
vertices = set(T[sorted(removed)].ravel().tolist())
assert len(vertices) - len(domain_edges) + len(removed) == 1
for v in vertices:
    link = defaultdict(set)
    for fi in np.flatnonzero((T == v).any(axis=1)):
        if int(fi) in removed:
            continue
        a, b = [int(k) for k in T[fi] if k != v]
        link[a].add(b)
        link[b].add(a)
    if not link:
        continue
    seen = set()
    todo = [min(link)]
    while todo:
        a = todo.pop()
        if a in seen:
            continue
        seen.add(a)
        todo.extend(link[a] - seen)
    assert seen == set(link)

graph = defaultdict(set)
for e, owners in edges.items():
    if any(v[2] not in removed for v in owners):
        a, b = e
        graph[a].add(b)
        graph[b].add(a)
parent = np.arange(len(U))
active = np.zeros(len(U), bool)
tags = np.zeros(len(U), np.uint8)
for bit, label in [(1, 'central_Z0_straddling'), (2, 'positiveZ_lateral')]:
    for v in roots[label]:
        tags[v] |= bit
for y in np.unique(U[:, 1]):
    nodes = np.flatnonzero(U[:, 1] == y)
    active[nodes] = True
    for a in nodes:
        for b in graph[int(a)]:
            if active[b]:
                i, j = find(int(a)), find(b)
                if i != j:
                    parent[j] = i
                    tags[i] |= tags[j]
    if any(tags[find(int(a))] == 3 for a in nodes):
        attachment = float(y)
        break
assert attachment == 1.301290512084961 and attachment == x['finalMaskAudit']['unsealedFirstLeftAttachmentY_M']

# Verify the other specialist's read-only evidence pins; no art judgement.
f = read(R / 'docs/evidence/hero-remaster/one-rider-v2/independent-update193/freeze.json')
for record in f['files'] + f['inputPins']:
    path = Path(record['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'] and path.stat().st_size == record['bytes']
report = {'status': 'PHYSICAL_MINCUT47_UNSEALED_DOMAIN_VERIFIED_NO_ASSET', 'pins': pins, 'independentScipyMaxflow': int(result.flow_value), 'removedSourceFaces': sorted(removed), 'newFillBoundaryPhysicalIDs': loop, 'boundaryEdges': 49, 'Euler': 1, 'retainedLinkPinches': 0, 'outsideScopeRemovedFaces': [], 'sourcePositionMoves': 0, 'unsealedAttachmentY_M': attachment, 'independentUpdate193FrozenFilesVerified': len(f['files']), 'independentUpdate193InputAndMeshPinsVerified': len(f['inputPins']), 'verifierSchemaCorrection': 'All65 source/mesh pins are in inputPins, not a separate meshReceipts key; corrected before report generation. No candidate generated.', 'limits': 'Cut-domain graph checks only; no new mesh, geometry, cap, UV, normal, skin, motion, contact or visual acceptance. Audit reports were inspected and hashes verified, not their movies replayed.'}
assert not (E / 'parent-separator-review.json').exists()
(E / 'parent-separator-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in ['pins', 'removedSourceFaces', 'newFillBoundaryPhysicalIDs']}))
