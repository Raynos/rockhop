"""Independent source-boundary and complete-cloth connectivity review."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/local-retopology-design200'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

freeze = json.loads((E / 'freeze.json').read_text())
extension_freeze = json.loads((E / 'whole-cloth-extension-freeze.json').read_text())
assert sha(E / 'freeze.json') == extension_freeze['originalFreezeSHA256']
pin_count = 0
for table in [freeze['inputPins'], freeze['ownedRecipeEvidencePins'],
              extension_freeze['ownedExtensionPins'], extension_freeze['inputPins']]:
    for path, record in table.items():
        assert sha(path) == record['sha256']
        assert Path(path).stat().st_size == record['bytes']
        pin_count += 1
source = B / 'source-preserving-garment185/operator/rider.glb'
assert sha(source) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g = GLB(source)
primitive = g.j['meshes'][0]['primitives'][0]
P = g.array(primitive['attributes']['POSITION'])
F = g.array(primitive['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
receipt = json.loads((E / 'source-domain-boundaries.json').read_text())
removed = np.array(receipt['proposedSourceFaceIDs'])
old_scope = json.loads((B / 'source-seam191/next-construction-contract.json').read_text())
# Domain is literal source191 union plus two exact source stars, not a ROI.
assert set(removed) - {3823, 3824} == set(old_scope['boundaryContract']['unionSourceFaceIDs'])
assert len(removed) == 1235
physical_faces = q[F]
region_faces = physical_faces[removed]
region_vertices = np.unique(region_faces)
edges = np.sort(np.concatenate([region_faces[:, [0, 1]], region_faces[:, [1, 2]], region_faces[:, [2, 0]]]), axis=1)
unique_edges, counts = np.unique(edges, axis=0, return_counts=True)
assert counts.max() == 2
boundary = {tuple(edge) for edge in unique_edges[counts == 1]}
assert len(boundary) == 151 and len(region_vertices) == 693
assert len(region_vertices) - len(unique_edges) + len(region_faces) == 0
rings = [ring['orderedPhysicalIDs'] for ring in receipt['orderedBoundaryRings']]
assert [len(ring) for ring in rings] == [89, 62]
reported_edges = set()
for ring in rings:
    for a, b in zip(ring, ring[1:] + ring[:1]):
        edge = tuple(sorted((a, b)))
        assert edge in boundary and edge not in reported_edges
        reported_edges.add(edge)
assert reported_edges == boundary
ring_nodes = {v for ring in rings for v in ring}
assert len(ring_nodes) == 151
assert not set(receipt['originalCuff65ProtectedIDs']) & set(region_vertices)
# Concatenate actual p0/glove/hood references and weld only exact positions.
positions, faces, offsets = [], [], []
offset = 0
for pi, p in enumerate(g.j['meshes'][0]['primitives']):
    pos = g.array(p['attributes']['POSITION'])
    tri = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
    if pi == 0:
        tri = np.delete(tri, removed, axis=0)
    positions.append(pos)
    faces.append(tri + offset)
    offsets.append(offset)
    offset += len(pos)
whole, inverse = np.unique(np.concatenate(positions), axis=0, return_inverse=True)
T = inverse[np.concatenate(faces)]
referenced = np.unique(T)
edges = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
graph = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(whole), len(whole))).tocsr()
_, labels = connected_components(graph, directed=False)
sizes = sorted(Counter(labels[referenced]).values(), reverse=True)
assert sizes == [19000, 3058]
whole_lookup = {tuple(pos): i for i, pos in enumerate(whole)}
ring_labels = []
for ring in rings:
    ring_ids = [whole_lookup[tuple(U[v])] for v in ring]
    assert len(set(labels[ring_ids])) == 1
    ring_labels.append(int(labels[ring_ids[0]]))
assert ring_labels[0] != ring_labels[1]
seams = []
p0_positions = {tuple(pos) for pos in P}
for pi in (1, 2):
    shared = p0_positions & {tuple(pos) for pos in positions[pi]}
    seams.append(len(shared))
assert seams == [127, 307]
report = {
    'status': 'PARENT_SOURCE_DOMAIN_AND_WHOLE_CLOTH_DISCONNECTION_VERIFIED',
    'pinsVerified': pin_count, 'sourceSHA256': sha(source),
    'sourceFaces': len(removed), 'physicalNodes': len(region_vertices),
    'physicalEdges': len(unique_edges), 'EulerCharacteristic': 0,
    'orderedBoundaryRingLengths': [89, 62], 'all151BoundaryEdgesVerified': True,
    'wholeClothRetainedComponents': sizes, 'exactP0GloveHoodSharedNodes': seams,
    'ringOwnershipSeparate': True, 'separateDiskClosuresRejected': True,
    'candidateGeometryCreated': False,
    'limits': 'Valid source annulus and larger interior budget do not establish a feasible high shoulder join, geometry, appearance, weights or motion. No candidate registered by this domain review.'
}
destination = E / 'parent-review201.json'
assert not destination.exists()
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
