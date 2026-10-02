"""Parent audit of a frozen local shell; no solver, export or writes to sources."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import sys
import numpy as np
import ipctk

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
parser = argparse.ArgumentParser()
parser.add_argument('--round', type=int, required=True)
args = parser.parse_args()
name = f'local-shell{args.round}'
E = R / 'docs/evidence/hero-remaster/one-rider-v2' / name
S = B / name
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB, worlds

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

freeze = json.loads((E / 'freeze.json').read_text())
child = json.loads((E / 'report.json').read_text())
for table in (freeze['files'], child['inputPins']):
    for path, record in table.items():
        data = Path(path).read_bytes()
        assert len(data) == record['bytes'] and digest(path) == record['sha256'], path
source = B / 'source-preserving-garment185/operator/rider.glb'
assert digest(source) == 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
g, z = GLB(source), np.load(S / 'construction.npz')
p = g.j['meshes'][0]['primitives'][0]
attrs = {key: g.array(i) for key, i in p['attributes'].items()}
P = attrs['POSITION']
F = g.array(p['indices']).reshape(-1, 3).astype(np.int64)
U, q = np.unique(P, axis=0, return_inverse=True)
assert np.array_equal(z['sourceIndices'], F)
assert np.array_equal(z['sourcePhysicalPositions'], U)
path = json.loads((B / 'source-seam191/next-construction-contract.json').read_text())['orderedProspectiveSeamPhysicalIDs']
scope = np.flatnonzero(np.isin(q[F], path).any(axis=1))
assert len(scope) == 168 and np.array_equal(z['changedSourceFaceIDs'], scope)
contract = json.loads((R / 'docs/evidence/hero-remaster/one-rider-v2/ipc-admission197/parent-construction-contract199.json').read_text())
inside = np.array(contract['freePhysicalIDs'])
assert np.array_equal(inside, z['interiorPhysicalIDs'])
clones = np.flatnonzero(np.isin(q, inside))
assert len(clones) == 88 and np.array_equal(clones, z['clonedSourceRows'])
assert np.array_equal(z['clonedNewRows'], np.arange(len(P), len(P) + len(clones)))
all_rows = np.r_[np.arange(len(P)), clones]
for key, original in attrs.items():
    assert np.array_equal(z['attribute_' + key][:len(P)], original)
    if key not in ('POSITION', 'NORMAL'):
        assert np.array_equal(z['attribute_' + key], original[all_rows])
for ti, target in enumerate(p.get('targets', [])):
    for key, accessor in target.items():
        assert np.array_equal(z[f'morph_{ti}_{key}'], g.array(accessor)[all_rows])
row_ids = np.r_[q, q[clones]]
assert np.array_equal(row_ids, z['attributeRowPhysicalIDs'])
assert np.array_equal(row_ids[z['indices']], q[F])
outside = np.setdiff1d(np.arange(len(F)), scope)
assert np.array_equal(z['indices'][outside], F[outside])
expected = U.copy()
expected[inside] = z['finalFreeXYZFloat64'].astype(np.float32)
assert np.array_equal(expected, z['physicalPositions'])
assert np.array_equal(z['positions'], np.r_[P, expected[q[clones]]])
assert len(np.unique(expected, axis=0)) == len(U)
trace = np.load(S / 'trace.npz')
assert np.array_equal(trace['acceptedFreeXYZ'][-1], z['finalFreeXYZFloat64'])
lengths = np.linalg.norm(np.diff(U[path].astype(float), axis=0), axis=1)
cumulative = np.r_[0., np.cumsum(lengths)]
u = dict(zip(path, cumulative / cumulative[-1]))
u[4041] = np.mean([u[i] for i in (3674, 3717, 4279, 4393)])
targets = np.array([float(U[1488, 1]) + u[int(v)] * (float(U[13448, 1]) - float(U[1488, 1])) for v in inside])
assert np.array_equal(targets, z['targetYFloat64'])
error = float(np.max(abs(expected[inside, 1].astype(float) - targets)))
assert error == child['maximumTargetErrorM']
tri = z['positions'][z['indices']].astype(float)
vectors = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
assert np.all(np.isfinite(tri)) and np.all(np.linalg.norm(vectors, axis=1) > 0)
provenance = json.loads((S / 'construction-provenance.json').read_text())
for group in provenance['normalGroups']:
    pid, bits = group['physicalID'], group['originalNormalBits']
    fs = [fi for fi in scope if any(int(q[row]) == pid and attrs['NORMAL'][row].view(np.uint32).tolist() == bits for row in F[fi])]
    total = np.sum(vectors[fs], axis=0)
    normal = (total / np.linalg.norm(total)).astype(np.float32)
    assert np.array_equal(z['attribute_NORMAL'][group['newRows']], np.repeat(normal[None], len(group['newRows']), axis=0))
    assert all(attrs['NORMAL'][row].view(np.uint32).tolist() == bits for row in group['originalRows'])
# Independently construct all five primitives with actual node transforms.
W = worlds(g.j)
points, targets_world, faces = [], [], []
offset = 0
for mi, mesh in enumerate(g.j['meshes']):
    nodes = [i for i, n in enumerate(g.j['nodes']) if n.get('mesh') == mi]
    assert len(nodes) == 1
    mat = W[nodes[0]]
    for pi, primitive in enumerate(mesh['primitives']):
        position = g.array(primitive['attributes']['POSITION'])
        indices = g.array(primitive['indices']).reshape(-1, 3).astype(np.int64)
        target = expected[q] if (mi, pi) == (0, 0) else position
        def world(values):
            return np.sum(values.astype(float)[:, None, :] * mat[:3, :3][None], axis=2) + mat[:3, 3]
        points.append(world(position))
        targets_world.append(world(target))
        faces.append(indices + offset)
        offset += len(position)
source_raw, target_raw, F_all = np.concatenate(points), np.concatenate(targets_world), np.concatenate(faces)
whole, inverse = np.unique(source_raw, axis=0, return_inverse=True)
final = whole.copy()
for v in np.flatnonzero(np.any(source_raw != target_raw, axis=1)):
    pid = inverse[v]
    assert np.all(target_raw[inverse == pid] == target_raw[v])
    final[pid] = target_raw[v]
T = inverse[F_all]
edges = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)
ipctk.set_num_threads(2)
mesh = ipctk.CollisionMesh(whole, edges, T)
ccd = ipctk.TightInclusionCCD(tolerance=1e-8, max_iterations=1000000, conservative_rescaling=.8)
assert not ipctk.has_intersections(mesh, whole)
final_clear = not ipctk.has_intersections(mesh, final)
source_final_step = ipctk.compute_collision_free_stepsize(mesh, whole, final, narrow_phase_ccd=ccd)
body_node = next(i for i, n in enumerate(g.j['nodes']) if n.get('mesh') == 0)
body_world = W[body_node]
free_rest_world = np.sum(U[inside].astype(float)[:, None, :] * body_world[:3, :3][None], axis=2) + body_world[:3, 3]
whole_lookup = {tuple(v): i for i, v in enumerate(whole)}
free_global = np.array([whole_lookup[tuple(v)] for v in free_rest_world])
previous = whole.copy()
trace_checks = []
for index, free in enumerate(trace['acceptedFreeXYZ'][1:], 1):
    next_state = whole.copy()
    next_state[free_global] = np.sum(free[:, None, :] * body_world[:3, :3][None], axis=2) + body_world[:3, 3]
    prefix_clear = ipctk.is_step_collision_free(mesh, previous, next_state, narrow_phase_ccd=ccd)
    endpoint_clear = not ipctk.has_intersections(mesh, next_state)
    assert prefix_clear and endpoint_clear, index
    trace_checks.append({'acceptedUpdate': index, 'fullDefaultContinuousClear': bool(prefix_clear), 'fullDefaultEndpointClear': endpoint_clear})
    previous = next_state
cast_clear = ipctk.is_step_collision_free(mesh, previous, final, narrow_phase_ccd=ccd)
assert cast_clear
diagnostic_result = None
if args.round == 199:
    diagnostic = json.loads((E / 'ccd-stop-diagnostic.json').read_text())
    event = diagnostic['cappedSegmentCandidateEvents'][0]
    start = np.array(event['acceptedStartXYZ'])
    end = np.array(event['cappedQueryXYZ'])
    candidate = ipctk.EdgeEdgeCandidate(0, 1)
    ee = np.array([[0, 1], [2, 3]], dtype=np.int32)
    empty = np.empty((0, 3), dtype=np.int32)
    def query(values):
        return candidate.ccd(candidate.dof(start, ee, empty), candidate.dof(values, ee, empty), narrow_phase_ccd=ccd)
    hit, toi = query(end)
    half_hit, half_toi = query(start + .5 * (end - start))
    assert hit and toi == event['reportedTOI'] and not half_hit
    diagnostic_result = {'fullCapEEReportedHit': bool(hit), 'fullCapEEConservativeTOI': toi, 'halfCapEEReportedHit': bool(half_hit), 'candidateDumpUnmodified': True}
assert final_clear
report = {
    'status': 'PARENT_FROZEN_LOCAL_SHELL_REVIEW_NOT_ACCEPTED',
    'round': args.round, 'ownedPinsVerified': len(freeze['files']), 'inputPinsVerified': len(child['inputPins']),
    'sourceSHA256': digest(source), 'dumpSHA256': digest(S / 'construction.npz'),
    'originalAttrsMorphsExact': True, 'clonedNonGeometryLiteral': True,
    'sourcePhysicalFaceIncidenceExact': True, 'outsideIndicesExact': True,
    'finalFloat32CastAndTraceExact': True, 'normalsIndependentlyRecomputed': len(provenance['normalGroups']),
    'sourceFaces': len(scope), 'freePhysicalVertices': len(inside), 'clonedRows': len(clones),
    'maximumTargetErrorM': error, 'targetProxyPass': error <= .002,
    'allFiveTriangles': len(T), 'wholePhysicalVertices': len(whole),
    'fullDefaultSourceClear': True, 'fullDefaultActualFloat32FinalClear': final_clear,
    'fullDefaultSourceToFinalCCDStep': source_final_step, 'pythonCallbackOrFilterUsed': False,
    'independentlyCheckedAcceptedSegments': trace_checks,
    'finalFloat64ToFloat32CastContinuousClear': bool(cast_clear),
    'CCDStopWitness': diagnostic_result,
    'limits': 'Static numerical review only. Original bad weights preserved. No export, anatomy, appearance, played pose, gameplay contacts or mobile acceptance. Incomplete199 solve does not prove domain infeasibility.'
}
destination = E / 'parent-review.json'
assert not destination.exists()
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
