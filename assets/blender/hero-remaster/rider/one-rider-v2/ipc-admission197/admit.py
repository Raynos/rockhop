"""Immutable, CPU-only IPC admission. No geometry export or deformation solver."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '2'
from pathlib import Path
from collections import Counter
import ast, hashlib, importlib.util, json, platform, re, signal, subprocess, time
import numpy as np
import ipctk
R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R/'docs/evidence/hero-remaster/one-rider-v2/ipc-admission197'
P = B/'ipc-admission197'
start = time.monotonic(); signal.alarm(900); ipctk.set_num_threads(2)
pins = {}; memory = []
def pin(path, expected=None):
    raw = Path(path).read_bytes(); h = hashlib.sha256(raw).hexdigest()
    assert expected is None or h == expected, (path, h)
    pins[str(path)] = {'sha256': h, 'bytes': len(raw)}
    return raw
def save(name, value):
    (E/name).write_text(json.dumps(value, indent=2, allow_nan=False,
        default=lambda x: x.item() if isinstance(x, np.generic) else x.tolist()
        if isinstance(x, np.ndarray) else str(x))+'\n')
def check():
    assert time.monotonic()-start < 870
    s = subprocess.check_output(['vm_stat'], text=True)
    g = int(re.search(r'Anonymous pages:\s+(\d+)', s)[1])*int(re.search(r'page size of (\d+)', s)[1])/1e9
    memory.append(g); assert g < 70
check()
reader = R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py'
pin(reader); spec = importlib.util.spec_from_file_location('reader', reader)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
predicate = R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py'
tree = ast.parse(pin(predicate))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'strict')
exec(compile(ast.Module(body=[node], type_ignores=[]), str(predicate), 'exec'))
source = B/'source-preserving-garment185/operator/rider.glb'
dump = B/'source-star196/construction.npz'
pin(source, 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5')
pin(dump, '5b54029e8cd59fec2b53e7bdbbf3a3b33f3ff93303a30fedcfa539d2fb336f27')
g = module.GLB(source); z = np.load(dump)
contract = json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195/parent-construction-contract.json'))
witness = json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-star196/actual-crossing-witnesses.json'))
def worlds(doc):
    parent = {ch: i for i, n in enumerate(doc['nodes']) for ch in n.get('children', [])}; cache = {}
    def calc(i):
        if i in cache: return cache[i]
        n = doc['nodes'][i]
        if 'matrix' in n: m = np.array(n['matrix']).reshape(4, 4, order='F')
        else:
            x, y, v, w = n.get('rotation', [0, 0, 0, 1])
            rot = np.array([[1-2*(y*y+v*v), 2*(x*y-v*w), 2*(x*v+y*w)],
                [2*(x*y+v*w), 1-2*(x*x+v*v), 2*(y*v-x*w)],
                [2*(x*v-y*w), 2*(y*v+x*w), 1-2*(x*x+y*y)]])
            m = np.eye(4); m[:3,:3] = rot@np.diag(n.get('scale', [1, 1, 1]))
            m[:3,3] = n.get('translation', [0, 0, 0])
        cache[i] = calc(parent[i])@m if i in parent else m
        return cache[i]
    return [calc(i) for i in range(len(doc['nodes']))]
world = worlds(g.j); reference = module.worlds(g.j)
assert all(np.allclose(a, b, rtol=0, atol=1e-15) for a, b in zip(world, reference))
positions = []; endpoints = []; faces = []; origins = []; primitives = []; offset = 0
p0 = g.array(g.j['meshes'][0]['primitives'][0]['attributes']['POSITION'])
U, q = np.unique(p0, axis=0, return_inverse=True)
assert U.tobytes() == z['sourcePhysicalPositions'].tobytes()
for mi, m in enumerate(g.j['meshes']):
    nodes = [i for i, n in enumerate(g.j['nodes']) if n.get('mesh') == mi]
    assert len(nodes) == 1; mat = world[nodes[0]]
    for pi, p in enumerate(m['primitives']):
        a = g.array(p['attributes']['POSITION']); f = g.array(p['indices']).reshape(-1, 3); n = a.copy()
        if (mi, pi) == (0, 0):
            n = z['physicalPositions'][q]
            assert np.array_equal(z['attributeRowPhysicalIDs'][z['indices']], q[f])
            assert np.array_equal(z['positions'][z['indices']], n[f])
        positions.append((np.c_[a, np.ones(len(a))]@mat.T)[:,:3])
        endpoints.append((np.c_[n, np.ones(len(n))]@mat.T)[:,:3])
        faces.append(f.astype(np.int64)+offset); offset += len(a)
        origins.extend({'mesh':mi, 'primitive':pi, 'sourceFace':i} for i in range(len(f)))
        primitives.append({'mesh':mi, 'primitive':pi, 'node':nodes[0], 'worldMatrix':mat, 'faces':len(f), 'rows':len(a)})
assert len(primitives) == 5
raw = np.concatenate(positions); endraw = np.concatenate(endpoints)
X, row = np.unique(raw, axis=0, return_inverse=True); F = row[np.concatenate(faces)].astype(np.int32); Y = X.copy()
for vid in range(len(X)):
    vals = endraw[row == vid]
    assert np.array_equal(vals, np.broadcast_to(vals[0], vals.shape)), ('inconsistent XYZ aliases', vid)
    Y[vid] = vals[0]
active = np.any(X != Y, axis=1); assert int(active.sum()) == 46
canonical_alias_ids = np.r_[np.flatnonzero(active), np.flatnonzero(~active)]
inverse_order = np.empty(len(X), np.int64); inverse_order[canonical_alias_ids] = np.arange(len(X))
X = X[canonical_alias_ids]; Y = Y[canonical_alias_ids]; F = inverse_order[F].astype(np.int32)
active = np.any(X != Y, axis=1)
released = contract['exactReleasedInteriorPhysicalIDs']; assert len(released) == 46
assert set(np.flatnonzero(np.any(U != z['physicalPositions'], axis=1))) == set(released)
Ed = np.unique(np.sort(np.concatenate([F[:,[0,1]], F[:,[1,2]], F[:,[2,0]]]), axis=1), axis=0).astype(np.int32)
mesh = ipctk.CollisionMesh(X, Ed, F)
assert mesh.num_vertices == len(X) and np.array_equal(mesh.faces, F)
ccd = ipctk.TightInclusionCCD(tolerance=1e-8, max_iterations=1000000, conservative_rescaling=.8)
settings = {'CPUThreads':ipctk.get_num_threads(), 'GPU':False, 'platform':platform.platform(),
    'python':platform.python_version(), 'CCD':'TightInclusionCCD', 'tolerance':ccd.tolerance,
    'maxIterations':ccd.max_iterations, 'conservativeRescaling':ccd.conservative_rescaling,
    'minDistance':0., 'broadPhase':'default', 'barrierDhatM':1e-4,
    'sourceAliasRule':'joint all-five exact XYZ after independently verified node-world transform',
    'filter':'at least one released physical vertex; native sewn shared-ID adjacency exclusion'}
save('inputs-and-settings.json', {'schemaVersion':1, 'pins':pins, 'settings':settings,
    'primitives':primitives, 'rawRows':len(raw), 'physicalVertices':len(X), 'faces':len(F),
    'edges':len(Ed), 'releasedPhysicalIDsP0':released, 'releasedGlobalPhysicalIDs':np.flatnonzero(active),
    'scope168':z['changedSourceFaceIDs'], 'independentWorldMaxError':max(float(np.max(abs(a-b)))
    for a, b in zip(world, reference)), 'allMeshWorldMatricesSame':all(np.array_equal(
    primitives[0]['worldMatrix'], p['worldMatrix']) for p in primitives),
    'collisionVertexToCanonicalXYZAliasID':canonical_alias_ids})
# Actual triangle surfaces, clear at both endpoints but colliding in transit.
A = np.array([[0.,0.,0.], [1.,0.,0.], [.5,1.,0.], [.1,.1,.00005], [.9,.1,.00005], [.5,.9,.00005]])
ff = np.array([[0,1,2], [3,4,5]], np.int32)
ee = np.array([[0,1], [1,2], [0,2], [3,4], [4,5], [3,5]], np.int32)
mm = ipctk.CollisionMesh(A, ee, ff); C = A.copy(); C[3:,2] *= -1
nc = ipctk.NormalCollisions(); nc.build(mm, A, 1e-4)
bar = ipctk.BarrierPotential(1e-4, 1000.); energy = float(bar(nc, mm, A))
grad = bar.gradient(nc, mm, A); hess = bar.hessian(nc, mm, A)
direction = np.zeros_like(A); direction[3:,2] = 1; eps = 1e-8
fd = (float(bar(nc, mm, A+eps*direction))-float(bar(nc, mm, A-eps*direction)))/(2*eps)
analytic = float(grad@direction.ravel())
assert energy > 0 and np.isfinite(grad).all() and abs(fd-analytic) < 1e-6*abs(fd)
step = ipctk.compute_collision_free_stepsize(mm, A, C, narrow_phase_ccd=ccd)
static = ipctk.compute_collision_free_stepsize(mm, A, A, narrow_phase_ccd=ccd)
fixtures = {'barrierEnergy':energy, 'gradientNorm':float(np.linalg.norm(grad)),
    'hessianShape':list(hess.shape), 'hessianFinite':bool(np.isfinite(hess.data).all()),
    'finiteDifference':fd, 'analyticDirectionalDerivative':analytic,
    'relativeDerivativeError':abs(fd-analytic)/abs(fd),
    'startIntersections':ipctk.has_intersections(mm,A), 'endIntersections':ipctk.has_intersections(mm,C),
    'middleIntersections':ipctk.has_intersections(mm,(A+C)/2), 'transitSafeStep':step, 'staticSafeStep':static,
    'isStepCollisionFreeTransit':ipctk.is_step_collision_free(mm,A,C,narrow_phase_ccd=ccd),
    'isStepCollisionFreeStatic':ipctk.is_step_collision_free(mm,A,A,narrow_phase_ccd=ccd),
    'pointTriangleTransit':ccd.point_triangle_ccd(A[3],*A[:3],C[3],*C[:3])}
assert not fixtures['startIntersections'] and not fixtures['endIntersections'] and fixtures['middleIntersections']
assert 0 < step < .5 and static == 1 and not fixtures['isStepCollisionFreeTransit'] and fixtures['isStepCollisionFreeStatic']
save('triangle-demo.json', fixtures); check()
# Default all-five preflight: no source defect or source contact is masked.
area = np.linalg.norm(np.cross(X[F[:,1]]-X[F[:,0]], X[F[:,2]]-X[F[:,0]]), axis=1)/2
pre = {'fullDefaultHasIntersections':ipctk.has_intersections(mesh,X), 'zeroAreaFaces':np.flatnonzero(area==0),
    'areaAtMost1e12Faces':np.flatnonzero(area<=1e-12), 'minimumAreaM2':float(area.min())}
def candidate_list(c):
    return [('fv',v) for v in c.fv_candidates]+[('ee',v) for v in c.ee_candidates]+[('ev',v) for v in c.ev_candidates]+[('vv',v) for v in c.vv_candidates]
def record(kind, c):
    ids = [int(v) for v in c.vertex_ids(Ed,F) if v >= 0]
    return {'kind':kind, 'vertexIDs':ids, 'distanceSquaredM2':float(c.compute_distance(X,Ed,F)),
        'atLeastOneReleased':bool(active[ids].any()), 'faceID':int(c.face_id) if kind=='fv' else None,
        'edgeIDs':[int(c.edge0_id),int(c.edge1_id)] if kind=='ee' else None}
full = ipctk.Candidates(); full.build(mesh,X)
records = [record(k,c) for k,c in candidate_list(full)]
zeros = [r for r in records if r['distanceSquaredM2'] <= 1e-24]
pre.update(defaultCandidates=len(records), defaultCandidateKinds=dict(Counter(r['kind'] for r in records)),
    sourceDistanceAtMost1e12MContacts=zeros, sourceExactZeroDistanceCount=sum(r['distanceSquaredM2']==0 for r in records))
save('source-preflight.json',pre); check()
# Compare native released filter with independent filtering of default swept set.
swept = ipctk.Candidates(); swept.build(mesh,X,Y)
key = lambda k,c:(k,tuple(int(v) for v in c.vertex_ids(Ed,F)))
expected = {key(k,c) for k,c in candidate_list(swept) if active[[v for v in c.vertex_ids(Ed,F) if v>=0]].any()}
mesh.can_collide = ipctk.make_static_obstacle_filter(46)
local = ipctk.Candidates(); local.build(mesh,X,Y)
actual = {key(k,c) for k,c in candidate_list(local)}
assert expected == actual, ('filter coverage',len(expected-actual),len(actual-expected))
local_records = []; events = []; static_zero = []
for n,(kind,c) in enumerate(candidate_list(local)):
    r = record(kind,c)
    hit, toi = c.ccd(c.dof(X,Ed,F),c.dof(Y,Ed,F),min_distance=0.,tmax=1.,narrow_phase_ccd=ccd)
    r.update(hit=bool(hit),reportedConservativeTime=float(toi) if hit else None); local_records.append(r)
    if hit: events.append(r)
    if r['distanceSquaredM2'] <= 1e-24: static_zero.append(r)
    if n%500 == 0: check()
local_step = local.compute_collision_free_stepsize(mesh,X,Y,narrow_phase_ccd=ccd)
static_local = local.compute_collision_free_stepsize(mesh,X,X,narrow_phase_ccd=ccd)
tri = X[F]; newtri = Y[F]; pairs = [v['globalFaces'] for v in witness['strictCrossings']]
aa = np.array([p[0] for p in pairs]); bb = np.array([p[1] for p in pairs]); assert len(pairs)==44
source_hit = strict(tri[aa],tri[bb]); end_hit = strict(newtri[aa],newtri[bb]); assert end_hit.all()
strict_review = [{'globalFaces':[i,j], 'ancestry':[origins[i],origins[j]],
    'sharedVertices':len(set(F[i])&set(F[j])), 'sourceStrict':bool(source_hit[k]),
    'endpointStrict':bool(end_hit[k]), 'incidentReleased':[int(v) for v in set(F[i])|set(F[j]) if active[v]]}
    for k,(i,j) in enumerate(pairs)]
save('frozen44-comparison.json',{'all44EndpointStrict':bool(end_hit.all()),'sourceStrictInFrozen44':int(source_hit.sum()),'pairs':strict_review})
blocked = pre['fullDefaultHasIntersections'] or bool(static_zero)
report = {'schemaVersion':1, 'status':'TOOL_ADMITTED_LOCAL_SOLVER_START_BLOCKED' if blocked else 'TOOL_ADMITTED_SOURCE_PRECONDITION_PASSES',
    'candidateGeometryCreated':False, 'GPU':False, 'settings':settings, 'source':pre,
    'sweptDefaultCandidateCount':len(candidate_list(swept)), 'releasedFilterExpectedCount':len(expected),
    'releasedFilterActualCount':len(actual), 'filterCoverageExact':expected==actual,
    'localCCDCount':len(local_records), 'localCCDHitCount':len(events), 'localInitialContactCount':len(static_zero),
    'localReportedSafeStep':float(local_step), 'localStaticReportedSafeStep':float(static_local),
    'earliestReportedConservativeTime':min((r['reportedConservativeTime'] for r in events),default=1.),
    'validCollisionFreePrefix':None if blocked else float(local_step), 'endpoint196Rejected':bool(end_hit.all()),
    'frozen44SourceStrictCount':int(source_hit.sum()), 'elapsedSeconds':time.monotonic()-start,
    'anonymousGBSamples':memory, 'pins':pins,
    'limits':['Safe-step output is diagnostic when the start intersects or has unresolved zero-distance contacts.',
        'Native FV/EE exclude shared-ID adjacency; separate folded-surface and inversion gates remain required.',
        'Existing endpoint196 only; no coordinates solved or exported.',
        'IPC supplies collision primitives and derivatives, not a deformation solver or art/skin/animation guarantee.']}
save('actual-trajectory.json',{'allLocalSweptQueries':local_records,'sourceLocalContacts':static_zero,'collisionEvents':events})
save('report.json',report); check()
assert hashlib.sha256(source.read_bytes()).hexdigest()==pins[str(source)]['sha256']
assert hashlib.sha256(dump.read_bytes()).hexdigest()==pins[str(dump)]['sha256']
print(json.dumps({k:report[k] for k in ['status','localCCDCount','localCCDHitCount','localInitialContactCount',
    'localReportedSafeStep','localStaticReportedSafeStep','earliestReportedConservativeTime',
    'validCollisionFreePrefix','endpoint196Rejected','elapsedSeconds']}))
