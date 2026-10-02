"""Parent checks design obstruction evidence and an alternative source cut."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/authored-panel202'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

freeze = json.loads((E / 'freeze.json').read_text())
extension_freeze = json.loads((E / 'high-path-extension-freeze.json').read_text())
assert sha(E / 'freeze.json') == extension_freeze['originalAuthoringObstructionFreezeSHA256']
counts = []
for table in [freeze['files'], freeze['inputs'], extension_freeze['files'], extension_freeze['inputs']]:
    for path, record in table.items():
        assert sha(path) == record['sha256']
        assert Path(path).stat().st_size == record['bytes']
    counts.append(len(table))
source = B / 'source-preserving-garment185/operator/rider.glb'
assert sha(source) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g = GLB(source)
p = g.j['meshes'][0]['primitives'][0]
P = g.array(p['attributes']['POSITION'])
F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
physical_faces = q[F]
extension = json.loads((E / 'high-path-extension.json').read_text())
cut = extension['closed61']
removed = np.array(cut['removedSourceFaceIDs'])
assert len(removed) == 61 and len(set(removed)) == 61
assert set(removed) == set(extension['source47']['removedSourceFaceIDs']) | set(extension['crossed12SourceFaces']) | {8350, 8351}
T = physical_faces[removed]
vertices = np.unique(T)
edges, edge_counts = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0, return_counts=True)
assert len(vertices) == 58 and len(edges) == 118 and edge_counts.max() == 2
assert len(vertices) - len(edges) + len(T) == 1
boundary = edges[edge_counts == 1]
assert len(boundary) == 53
degree = np.bincount(boundary.ravel(), minlength=len(U))
assert np.all(degree[np.unique(boundary)] == 2)
path = np.array(cut['sourceP0PhysicalPath'])
assert len(path) == 49 and np.array_equal(U[path].astype(float), np.array(cut['pathPositionsM']))
assert float(U[path, 1].max()) == cut['firstRootedAttachmentY_M']
assert 1.30 <= float(U[path, 1].max()) <= 1.32
support = set()
for a, b in zip(path[:-1], path[1:]):
    incident = np.flatnonzero(np.any(physical_faces == a, axis=1) & np.any(physical_faces == b, axis=1))
    retained = set(incident) - set(removed)
    assert retained
    support.update(retained)
assert support == set(cut['protectedRetainedP0FaceIDs']) and len(support) == 82
assert 1420 in boundary and 13550 in boundary
report = {
    'status': 'PARENT_AUTHORING_OBSTRUCTION_AND_ALTERNATIVE_SOURCE61_VERIFIED',
    'freezeFilesInputsExtensionFilesInputs': counts,
    'geometryAttempts': 0, 'newWeights': 0, 'exports': 0,
    'removedSourceFaces': len(removed), 'sourceNodes': len(vertices),
    'sourceEdges': len(edges), 'removedEuler': 1, 'cutBoundaryEdges': len(boundary),
    'boundaryDegreesTwo': True, 'retainedPathPhysicalNodes': len(path),
    'all82PathSupportingFacesRetained': True,
    'retainedPathMaximumY_M': float(U[path, 1].max()),
    'exactPathSourcePositionsVerified': True,
    'source47Plus12CollisionContextPlusTwoIslandFaces': True,
    'limits': 'Author failed to define a credible1235 panel, not a mathematical infeasibility proof.61 is an unsealed source cut with a retained path, not candidate geometry or art/skin/motion success.194 self-folds remain unresolved; no ruled-panel reuse.'
}
destination = E / 'parent-review202.json'
assert not destination.exists()
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
