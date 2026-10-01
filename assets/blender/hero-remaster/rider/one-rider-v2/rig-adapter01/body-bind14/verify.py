"""Parent conservation check, independent of the aperture builder's guards."""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np

root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
old_path = root / 'rig-adapter01/body-bind11/guarded-correction01/rider.glb'
initial_path = root / 'rig-adapter01/body-bind13/construction01/rider.glb'
new_path = root / 'rig-adapter01/body-bind14/construction01/rider.glb'
mapping_path = root / 'rig-adapter01/body-bind13/construction01/source-face-provenance.npz'
out = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind14/parent-conservation01.json')


def read(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return raw, json.loads(raw[20:20 + n]), raw[28 + n:]


def array(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    step = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(v.get('byteStride', width * step), step))


def area2(poly):
    if len(poly) < 3: return 0.0
    p = np.asarray(poly, dtype=float)
    return float(abs(np.sum(p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1)))/2)


def intersect(subject, clip):
    """Independent convex intersection in source barycentric plane."""
    polygon = [np.asarray(p, dtype=float) for p in subject]
    for a, b in zip(clip, np.roll(clip, -1, axis=0)):
        if not polygon: break
        edge = b-a
        def side(p):
            d = p-a
            return edge[0]*d[1]-edge[1]*d[0]
        clipped = []
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            dp, dq = side(p), side(q)
            ip, iq = dp >= -1e-15, dq >= -1e-15
            if ip: clipped.append(p)
            if ip != iq: clipped.append(p+(q-p)*dp/(dp-dq))
        polygon = clipped
    return polygon


def ulp_budget(values):
    """Two float32 ULPs per lane: intersection rounding and shared-edge reuse.

    Bounds are specified before measurements, never fitted to observed errors.
    """
    p = np.asarray(values, dtype=np.float32)
    up = abs(np.nextafter(p, np.float32(np.inf)).astype(float)-p.astype(float))
    down = abs(np.nextafter(p, np.float32(-np.inf)).astype(float)-p.astype(float))
    return 2*np.maximum(up, down).max(axis=tuple(range(p.ndim-1)))


old_raw, old, old_binary = read(old_path)
new_raw, new, new_binary = read(new_path)
assert hashlib.sha256(new_raw).hexdigest() == 'a75b8364fb86d123a118e427df19b52088b502d3d86a8f1c34fba543d8062f73'
assert new_binary[:len(old_binary)] == old_binary, 'Retain untouched original binary prefix'
assert old['meshes'][0] == new['meshes'][0], 'Body, hood, gloves and legs retain exact accessors'
assert old['meshes'][1]['primitives'][1] == new['meshes'][1]['primitives'][1], 'Cheek remains exact'
for key in ['nodes', 'skins', 'animations', 'scenes', 'scene']:
    assert old[key] == new[key], key
assert len(new['skins'][0]['joints']) == 19
for key in ['accessors', 'bufferViews', 'images', 'textures', 'samplers', 'materials']:
    assert old[key] == new[key][:len(old[key])], key
old_primitive = old['meshes'][1]['primitives'][0]
new_primitive = new['meshes'][1]['primitives'][0]
protected = {}
for name, index in old_primitive['attributes'].items():
    before = array(old, old_binary, index)
    after = array(new, new_binary, new_primitive['attributes'][name])
    assert np.array_equal(before, after[:len(before)]), name
    protected[name] = len(before)
positions = array(old, old_binary, old_primitive['attributes']['POSITION'])
faces = array(old, old_binary, old_primitive['indices']).reshape(-1, 3)
updated_faces = array(new, new_binary, new_primitive['indices']).reshape(-1, 3)
outside = np.ones(len(faces), dtype=bool)
for y, z in [(1.6965, .032), (1.6970, -.0332)]:
    triangle = positions[faces]
    could_meet = (triangle[:, :, 0].max(1) > .72) & (triangle[:, :, 1].max(1) >= y - .009) & (triangle[:, :, 1].min(1) <= y + .009) & (triangle[:, :, 2].max(1) >= z - .018) & (triangle[:, :, 2].min(1) <= z + .018)
    outside &= ~could_meet
# Reproduce the historical index-equality guard failure against the initial
# candidate. This is a verifier diagnostic, never counted as an art failure.
initial_raw, initial, initial_binary = read(initial_path)
initial_p = initial['meshes'][1]['primitives'][0]
initial_faces = array(initial, initial_binary, initial_p['indices']).reshape(-1, 3)
initial_set = {tuple(map(int, face)) for face in initial_faces}
missing = [int(i) for i in np.flatnonzero(outside) if tuple(map(int, faces[i])) not in initial_set]
assert len(missing) == 40
receipt = {'status': 'Reproduced initial strict guard failure; verifier diagnostic, not art failure',
    'candidate': str(initial_path), 'candidateSHA256': hashlib.sha256(initial_raw).hexdigest(),
    'sourceSHA256': hashlib.sha256(old_raw).hexdigest(),
    'failedAssertion': 'Protected outside triangles remain',
    'rule': 'Every protected original triangle index triple remains exact',
    'protectedSourceTriangles': int(outside.sum()), 'missingExactIndexTriples': missing,
    'reason': 'Subdivisions change index triples; source surface coverage requires an independent proof',
    'limits': 'Historical failure reproduced now; original execution timestamp is not claimed.'}
out.parent.mkdir(parents=True, exist_ok=True)
(out.parent/'parent-conservation-initial-failure.json').write_text(json.dumps(receipt, indent=2)+'\n')

mapping_raw = mapping_path.read_bytes()
with np.load(mapping_path) as mapping:
    origins = mapping['sourceTriangle'].copy()
    mapped_faces = mapping['updatedTriangles'].copy()
    mapped_positions = mapping['positions'].copy()
assert np.array_equal(mapped_faces, updated_faces), 'Provenance maps actual candidate indices'
assert len(origins) == len(updated_faces) and ((origins >= 0) & (origins < len(faces))).all()
after_attrs = {name:array(new,new_binary,index) for name,index in new_primitive['attributes'].items()}
before_attrs = {name:array(old,old_binary,index) for name,index in old_primitive['attributes'].items()}
used = np.unique(mapped_faces)
assert np.array_equal(mapped_positions[used], after_attrs['POSITION'][used]), 'Provenance actual used positions'
order = np.argsort(origins, kind='stable')
counts = np.bincount(origins, minlength=len(faces))
offsets = np.r_[0, np.cumsum(counts)]
domain = np.array([[0.,0.],[1.,0.],[0.,1.]])
rows = []; exact_count = 0
for origin in np.flatnonzero(outside):
    selected = order[offsets[origin]:offsets[origin+1]]
    assert len(selected), (int(origin), 'Protected source face removed')
    if len(selected) == 1 and np.array_equal(updated_faces[selected[0]], faces[origin]):
        exact_count += 1
        continue
    ids = updated_faces[selected]
    xyz = positions[faces[origin]].astype(float)
    q = after_attrs['POSITION'][ids].astype(float)
    edges = np.column_stack([xyz[1]-xyz[0], xyz[2]-xyz[0]])
    inverse = np.linalg.pinv(edges)
    local = np.einsum('cd,tvd->tvc', inverse, q-xyz[0])
    bary = np.concatenate([1-local.sum(2,keepdims=True), local],axis=2)
    reconstructed = np.einsum('tvc,cd->tvd',bary,xyz)
    coordinate_budget = ulp_budget(np.concatenate([xyz,q.reshape(-1,3)]))
    position_budget = float(np.linalg.norm(coordinate_budget))
    coefficient_budget = np.abs(inverse)@coordinate_budget
    bary_budget = np.r_[coefficient_budget.sum(), coefficient_budget]
    plane_error = float(np.linalg.norm(q-reconstructed,axis=2).max())
    assert plane_error <= position_budget, (int(origin),'plane',plane_error,position_budget)
    assert np.all(bary >= -bary_budget) and np.all(bary <= 1+bary_budget), (int(origin),'barycentric containment')
    source_cross = np.cross(edges[:,0],edges[:,1]); source_area = np.linalg.norm(source_cross)/2
    cross = np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0])
    assert np.all(cross@source_cross > 0), (int(origin),'winding')
    areas = np.linalg.norm(cross,axis=1)/2
    assert np.all(areas > 0), (int(origin),'degenerate child')
    # Both triangle edges perturb by <=2*position_budget. The cross-product
    # triangle area bound is delta*(|e1|+|e2|)+2*delta^2 per child.
    area_budget = float(np.sum(position_budget*(np.linalg.norm(q[:,1]-q[:,0],axis=1)+np.linalg.norm(q[:,2]-q[:,0],axis=1))+2*position_budget**2))
    area_error = float(abs(areas.sum()-source_area))
    assert area_error <= area_budget, (int(origin),'area',area_error,area_budget)
    clipped_area = sum(area2(intersect(child,domain)) for child in local)
    projected_area = sum(area2(child) for child in local)
    overlap = sum(area2(intersect(local[a],local[b])) for a in range(len(local)) for b in range(a+1,len(local)))
    # Bonferroni lower bound: independently measured pairwise overlap prevents
    # duplicates from masking uncovered source surface in summed-area checks.
    missing_coverage = max(0.,.5-clipped_area+overlap)
    outside_area = max(0.,projected_area-clipped_area)
    bary_area_budget = area_budget/(2*source_area)
    assert max(overlap,missing_coverage,outside_area) <= bary_area_budget, (int(origin),'coverage',overlap,missing_coverage,outside_area,bary_area_budget)
    interpolation = {}
    for name in ['TEXCOORD_0','WEIGHTS_0','NORMAL']:
        source = before_attrs[name][faces[origin]].astype(float)
        actual = after_attrs[name][ids].astype(float)
        expected = np.einsum('tvc,cd->tvd',bary,source)
        variation = np.max(abs(source-source[0]),axis=0)
        budget = ulp_budget(np.concatenate([source,actual.reshape(-1,source.shape[1])]))+coefficient_budget.sum()*variation
        if name == 'NORMAL':
            lengths = np.linalg.norm(expected,axis=2,keepdims=True)
            assert np.all(lengths > .1)
            expected /= lengths
            budget = 2*np.linalg.norm(budget)/float(lengths.min())+2*np.finfo(np.float32).eps
        error = float(abs(actual-expected).max())
        assert np.all(abs(actual-expected) <= budget), (int(origin),name,error,budget)
        interpolation[name] = {'maxError':error,'maxBudget':float(np.max(budget))}
    old_joints = before_attrs['JOINTS_0'][faces[origin]]
    assert np.all(old_joints == old_joints[0]) and np.all(after_attrs['JOINTS_0'][ids] == old_joints[0]), (int(origin),'joint slots')
    assert np.all(abs(after_attrs['WEIGHTS_0'][ids].sum(2)-1) <= 2*np.finfo(np.float32).eps)
    rows.append({'sourceTriangle':int(origin),'updatedTriangleIndices':selected.tolist(),
        'subdivisionTriangles':len(selected),'windingPositive':True,
        'maxPlaneDistanceM':plane_error,'positionBudgetM':position_budget,
        'minBarycentric':float(bary.min()),'maxBarycentricBudget':float(bary_budget.max()),
        'absoluteAreaErrorM2':area_error,'absoluteAreaBudgetM2':area_budget,
        'relativeAreaError':area_error/source_area,'relativeAreaBudget':area_budget/source_area,
        'overlapAreaM2':overlap*2*source_area,
        'missingCoverageAreaUpperBoundM2':missing_coverage*2*source_area,
        'outsideSourceAreaM2':outside_area*2*source_area,
        'interpolation':interpolation,'jointSlotsExact':True})
assert len(rows) == 40 and exact_count+len(rows) == int(outside.sum())
# Actual last protected subdivision supplies bounded in-memory fault controls.
# They change no file or source asset and prove summed area cannot hide damage.
def coverage_violation(children):
    clipped = sum(area2(intersect(child,domain)) for child in children)
    overlap = sum(area2(intersect(children[a],children[b])) for a in range(len(children)) for b in range(a+1,len(children)))
    return max(overlap,max(0.,.5-clipped+overlap)) > bary_area_budget
largest = int(np.argmax([area2(child) for child in local]))
assert coverage_violation(np.delete(local,largest,axis=0)), 'Removed subdivision rejected'
assert coverage_violation(np.concatenate([local,local[largest:largest+1]])), 'Duplicated overlap rejected'
flipped = q[largest,::-1]
assert np.dot(np.cross(flipped[1]-flipped[0],flipped[2]-flipped[0]),source_cross) < 0, 'Reversed winding rejected'
assert initial_path.read_bytes() == initial_raw and mapping_path.read_bytes() == mapping_raw
assert old_path.read_bytes() == old_raw and new_path.read_bytes() == new_raw
report = {'status':'PASS source conservation within declared float32 budgets; art unaccepted',
    'sourceSHA256': hashlib.sha256(old_raw).hexdigest(),
    'candidateSHA256': hashlib.sha256(new_raw).hexdigest(),
    'originalBinaryPrefixExactBytes': len(old_binary), 'bodyHoodGlovesLegsExact': True,
    'cheekPrimitiveExact': True, 'nodesSkinsAnimationsExact': True,
    'originalHeadAttributePrefixesExact': protected,
    'outsideApertureTrianglesExact': exact_count,
    'protectedOutsideSourceTriangles':int(outside.sum()),
    'protectedSourceTrianglesSubdivided':len(rows),'protectedSourceTrianglesRemoved':0,
    'provenanceSHA256':hashlib.sha256(mapping_raw).hexdigest(),
    'actualCandidateProvenanceExact':True,'skinJointCountExact':19,
    'positiveWindingContainmentCoverageInterpolationPassed':True,
    'maxPlaneDistanceM':max(r['maxPlaneDistanceM'] for r in rows),
    'maxRelativeAreaError':max(r['relativeAreaError'] for r in rows),
    'float32Budget':'Two ULPs per coordinate for intersection rounding and shared-edge reuse; geometry-propagated barycentric, interpolation and area bounds, not fitted to observed errors.',
    'coverageMethod':'Independent barycentric polygon intersections, pairwise overlap, clipped-area union lower bound.',
    'inMemoryFaultControls':{'removedChildRejected':True,'duplicatedChildRejected':True,'reversedWindingRejected':True},
    'subdivisions':rows,
    'limits': ['Conservation only. New tunnel/donor topology, placement, PBR appearance and actual motion require separate review.',
        'Coverage is bounded within explicit float32 quantization; not exact real-number equality.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key:value for key,value in report.items() if key != 'subdivisions'}, indent=2))
