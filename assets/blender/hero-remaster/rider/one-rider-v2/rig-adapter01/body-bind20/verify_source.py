"""Independent protected-surface coverage gate on frozen CPU graft data."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/construction01')
source_file=ROOT/'body-bind11/guarded-correction01/rider.glb';old_raw=source_file.read_bytes();n=struct.unpack_from('<I',old_raw,12)[0]
doc=json.loads(old_raw[20:20+n]);binary=old_raw[28+n:]
def array(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*item),item)).copy()
p=doc['meshes'][1]['primitives'][0];before_attrs={key:array(i) for key,i in p['attributes'].items()}
positions=before_attrs['POSITION'];faces=array(p['indices']).reshape(-1,3)
saved=np.load(ROOT/'body-bind20/construction01/geometry-preexport.npz')
after_attrs={key:saved['attribute_'+key] for key in before_attrs};updated_faces=saved['sourceTriangles'];origins=saved['sourceTriangleProvenance'];mapped_positions=saved['positions']
for key,old in before_attrs.items():assert np.array_equal(after_attrs[key][:len(old)],old)
assert np.array_equal(mapped_positions,after_attrs['POSITION'])
assert len(origins)==len(updated_faces) and ((origins>=0)&(origins<len(faces))).all()
selection=np.load(ROOT/'body-bind20/sheet-preflight01/sheet-selection.npz')
inner=set(map(int,selection['inwardSourceFaces']));outer=set(map(int,selection['exteriorSourceFaces']))
outside=np.ones(len(faces),dtype=bool)
xyz=positions[faces]
for fid in inner|outer:
    width,height,minimum_x=(.022,.017,.69) if fid in inner else (.018,.009,.72)
    for y,z in [(1.6965,.032),(1.697,-.0332)]:
        t=xyz[fid]
        if t[:,0].min()>minimum_x and t[:,1].min()<=y+height and t[:,1].max()>=y-height and t[:,2].min()<=z+width and t[:,2].max()>=z-width:outside[fid]=False
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
assert exact_count+len(rows) == int(outside.sum())

assert source_file.read_bytes()==old_raw
assert len(doc['skins'][0]['joints'])==19
report={'status':'PASS protected source coverage and attributes within explicit float32 bounds; pre-export only',
    'sourceSHA256':hashlib.sha256(old_raw).hexdigest(),'outsideDeclaredSurgicalBoundsFaces':int(outside.sum()),
    'exactProtectedFaces':exact_count,'subdividedProtectedFaces':len(rows),'removedProtectedFaces':0,
    'allOriginalHeadAttributePrefixesExact':True,'source19RigUnchanged':True,
    'maximumPlaneErrorM':max((r['maxPlaneDistanceM'] for r in rows),default=0.),
    'maximumRelativeAreaError':max((r['relativeAreaError'] for r in rows),default=0.),
    'budget':'Two float32 ULPs; propagated barycentric/area/UV/normal/weight bounds, not fitted after measurements.',
    'coverage':'Independent convex intersections, overlap and union lower bound.',
    'subdivisionDetails':rows,
    'limits':['CPU geometry gate. GLB prefix/nodes/animations/body/cheek accessor preservation must be checked after export.','Protected region conservatively excludes the declared source-sheet-dependent axis-aligned surgical bounds.']}
(OUT/'source-conservation-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='subdivisionDetails'},indent=2))
