"""Parent full-mesh CCD check, using no Python callback or active filter."""
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
import ipctk

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/ipc-admission197'
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB, worlds

ipctk.set_num_threads(2)
start = time.monotonic()
source = B / 'source-preserving-garment185/operator/rider.glb'
dump = B / 'source-star196/construction.npz'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
assert hashlib.sha256(dump.read_bytes()).hexdigest() == '5b54029e8cd59fec2b53e7bdbbf3a3b33f3ff93303a30fedcfa539d2fb336f27'
g, z = GLB(source), np.load(dump)
W = worlds(g.j)
points, targets, faces = [], [], []
offset = 0
for mi, mesh in enumerate(g.j['meshes']):
    node_ids = [i for i, n in enumerate(g.j['nodes']) if n.get('mesh') == mi]
    assert len(node_ids) == 1
    mat = W[node_ids[0]]
    for pi, p in enumerate(mesh['primitives']):
        P = g.array(p['attributes']['POSITION'])
        F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
        Q = P.copy()
        if (mi, pi) == (0, 0):
            physical, inverse = np.unique(P, axis=0, return_inverse=True)
            assert np.array_equal(physical, z['sourcePhysicalPositions'])
            Q = z['physicalPositions'][inverse]
        def world(values):
            return np.sum(values.astype(float)[:, None, :] * mat[:3, :3][None, :, :], axis=2) + mat[:3, 3]
        points.append(world(P))
        targets.append(world(Q))
        faces.append(F + offset)
        offset += len(P)
P, Q, F = np.concatenate(points), np.concatenate(targets), np.concatenate(faces)
U, inverse = np.unique(P, axis=0, return_inverse=True)
next_U = U.copy()
for v in np.flatnonzero(np.any(P != Q, axis=1)):
    old_id = inverse[v]
    assert np.all(Q[inverse == old_id] == Q[v])
    next_U[old_id] = Q[v]
T = inverse[F]
edges = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)
mesh = ipctk.CollisionMesh(U, edges, T)
source_clear = not ipctk.has_intersections(mesh, U)
endpoint_rejected = ipctk.has_intersections(mesh, next_U)
assert source_clear and endpoint_rejected
ccd = ipctk.TightInclusionCCD(tolerance=1e-8, max_iterations=1000000, conservative_rescaling=.8)
step = ipctk.compute_collision_free_stepsize(mesh, U, next_U, min_distance=0., narrow_phase_ccd=ccd)
static = ipctk.compute_collision_free_stepsize(mesh, U, U, min_distance=0., narrow_phase_ccd=ccd)
assert 0 < step < .05 and static == 1.
report = {
    'status': 'PARENT_FULL_DEFAULT_CCD_ADMISSION_PASS_NO_SCULPT',
    'allFiveReferencedFaces': len(F), 'physicalVertices': len(U),
    'actuallyMovingPhysicalVertices': int(np.any(U != next_U, axis=1).sum()),
    'sourceIntersectionFree': source_clear, 'failed196EndpointRejected': bool(endpoint_rejected),
    'fullDefaultSafeStep': step, 'fullDefaultStaticStep': static,
    'filterUsed': False, 'pythonCallbackUsed': False,
    'threads': ipctk.get_num_threads(), 'seconds': time.monotonic() - start,
    'candidateGeometryCreated': False,
    'limits': 'Existing source/failed endpoint used only as CCD input. Library admission is not a solver, construction, skin, art or motion/contact/mobile pass. Float32 final mesh still requires independent audit.'
}
assert not (E / 'parent-review198.json').exists()
(E / 'parent-review198.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
