"""Read-only actual garment LBS fit estimates driven by existing solver joints."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[4]
UNITS = [
    ('wardrobe', ROOT / 'harness/out/rider-rebuild/construction02/selected-wardrobe01/rider-assembled.blend',
     'f8fd61f677b5ac378fee1494973b4dca832f5f74c07ccff18a9da0d57112de25', ['RiderHoodie', 'RiderJeans']),
    ('boots', ROOT / 'harness/out/rider-rebuild/selected-boot02/selected-boot-checkpoint.blend',
     '2e836f508a9799325225affe2cbf1e6347c818ef3eaac2884c8cf48f56d435df', ['ActualSelectedBoot.L', 'ActualSelectedBoot.R'])]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
pose_path, out = [Path(arg).resolve() for arg in args]
out.mkdir(parents=True, exist_ok=False)
poses = json.loads(pose_path.read_text()); assert poses['sourceAndRestPreserved'] and len(poses['rows']) == 5
assert poses['source']['sha256'] == '58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc'
assert sha(poses['source']['path']) == poses['source']['sha256']
rest = {bone['name']: bone for bone in poses['nativeRest']['bones']}; assert len(rest) == 75
def snapshot(obj):
    assert obj.matrix_world.is_identity
    obj.data.calc_loop_triangles()
    names = {group.index: group.name for group in obj.vertex_groups}
    fields = [{names[g.group]: g.weight for g in vertex.groups if g.weight > 0} for vertex in obj.data.vertices]
    assert all(1 <= len(field) <= 4 and abs(sum(field.values()) - 1) < 2e-5 for field in fields)
    return {'xyz': np.asarray([tuple(vertex.co) for vertex in obj.data.vertices], dtype=np.float64),
            'triangles': [tuple(tri.vertices) for tri in obj.data.loop_triangles], 'fields': fields,
            'uvSHA256': hashlib.sha256(np.asarray([tuple(uv.uv) for uv in obj.data.uv_layers.active.data], dtype='<f4').tobytes()).hexdigest()
                        if obj.data.uv_layers.active else None}
def fingerprint(mesh):
    h = hashlib.sha256(mesh['xyz'].tobytes())
    h.update(np.asarray(mesh['triangles'], dtype='<u4').tobytes())
    h.update(json.dumps(mesh['fields'], sort_keys=True, separators=(',', ':')).encode())
    h.update((mesh['uvSHA256'] or '').encode()); return h.hexdigest()
def transformed(mesh, deltas):
    source = mesh['xyz']; result = np.zeros_like(source); homogeneous = np.column_stack([source, np.ones(len(source))])
    for joint in sorted({name for field in mesh['fields'] for name in field}):
        ids = np.asarray([i for i, field in enumerate(mesh['fields']) if joint in field], dtype=np.int32)
        weights = np.asarray([mesh['fields'][int(i)][joint] for i in ids])
        result[ids] += (homogeneous[ids] @ deltas[joint].T)[:, :3] * weights[:, None]
    assert np.isfinite(result).all(); return result
def tree(points, triangles):
    return BVHTree.FromPolygons([Vector(point) for point in points], triangles, all_triangles=True)
def signed_samples(points, surface):
    values = []
    for point in points:
        p = Vector(point); hit, normal, index, distance = surface.find_nearest(p)
        assert hit is not None and distance is not None
        values.append(float(distance if (p-hit).dot(normal) >= 0 else -distance))
    return np.asarray(values)
def summary(values):
    assert len(values)
    return {'count': len(values), 'minM': float(values.min()), 'p05M': float(np.percentile(values,5)),
            'medianM': float(np.median(values)), 'p95M': float(np.percentile(values,95)), 'maxM': float(values.max())}
def point_tree(points):
    kd = KDTree(len(points))
    for index, point in enumerate(points): kd.insert(Vector(point), index)
    kd.balance(); return kd
def nearest_values(points, targets):
    kd = point_tree(targets); return np.asarray([kd.find(Vector(point))[2] for point in points])
def boundaries(mesh):
    counts = {}
    for triangle in mesh['triangles']:
        for a,b in zip(triangle, triangle[1:] + triangle[:1]):
            edge = tuple(sorted((a,b))); counts[edge] = counts.get(edge,0) + 1
    adjacent = {}
    for (a,b), count in counts.items():
        if count == 1: adjacent.setdefault(a,set()).add(b); adjacent.setdefault(b,set()).add(a)
    remaining = set(adjacent); components = []
    while remaining:
        seed = remaining.pop(); found = {seed}; pending = [seed]
        while pending:
            for i in adjacent[pending.pop()] - found:
                found.add(i); remaining.discard(i); pending.append(i)
        components.append(sorted(found))
    return components
def coverage_ids(name, body, garment):
    result = []
    low, high = garment['xyz'][:,2].min(), garment['xyz'][:,2].max()
    for i, (point, field) in enumerate(zip(body['xyz'], body['fields'])):
        if not low + .010 < point[2] < high - .010: continue
        if name == 'RiderHoodie':
            relevant = lambda n: (n.startswith('DEF-spine') and n not in ('DEF-spine.005','DEF-spine.006')) or any(stem in n for stem in ('shoulder','upper_arm','forearm'))
        elif name == 'RiderJeans':
            relevant = lambda n: n == 'DEF-spine' or any(stem in n for stem in ('pelvis','thigh','shin'))
        else:
            side = name[-1]; relevant = lambda n: n in ('DEF-foot.'+side, 'DEF-toe.'+side, 'DEF-shin.'+side+'.001')
        if sum(weight for joint,weight in field.items() if relevant(joint)) > .55: result.append(i)
    assert result, ('Empty actual limb coverage domain', name)
    return result

units, inputs, same_body = {}, [], None
for kind, path, expected_sha, names in UNITS:
    assert sha(path) == expected_sha
    inputs.append({'path': str(path), 'sha256': expected_sha})
    bpy.ops.wm.open_mainfile(filepath=str(path)); rig = bpy.data.objects['RiderSkeleton']
    native_rest_before = [(bone.name, bone.parent.name if bone.parent else None, tuple(bone.head_local), tuple(bone.tail_local), tuple(tuple(row) for row in bone.matrix_local)) for bone in rig.data.bones]
    assert len(native_rest_before) == 75
    for bone in rig.data.bones:
        expected = rest[bone.name]
        if not bone.name.startswith('SoleSocket.'):
            assert tuple(bone.head_local) == tuple(expected['head']) and tuple(bone.tail_local) == tuple(expected['tail'])
            assert (bone.parent.name if bone.parent else None) == expected['parent']
            assert [list(row) for row in bone.matrix_local] == expected['matrix']
    body = snapshot(bpy.data.objects['RiderBody']); assert len(body['xyz']) == 10582
    if same_body is None: same_body = fingerprint(body)
    else: assert fingerprint(body) == same_body, 'Unit wearers differ'
    units[kind] = {'body': body, 'garments': {name: snapshot(bpy.data.objects[name]) for name in names}}
    assert native_rest_before == [(bone.name, bone.parent.name if bone.parent else None, tuple(bone.head_local), tuple(bone.tail_local), tuple(tuple(row) for row in bone.matrix_local)) for bone in rig.data.bones]

identity = {name: np.eye(4) for name in rest}
rows = [{'name': 'rest', 'lean': None, 'deltas': identity}]
rows += [{'name': row['name'], 'lean': row['lean'], 'deltas': {name: np.asarray(values).reshape(4,4).T for name,values in row['boneDeltaNativeColumnMajor'].items()},
          'solver': {key: row[key] for key in ('gripM','soleM','COMResidualM','spineFlexRadians','localJointRotationFromRestRadians')}} for row in poses['rows']]
report_rows, fingerprints = [], {}
for kind, unit in units.items():
    body = unit['body']; fingerprints[kind] = {'body': fingerprint(body), 'garments': {name: fingerprint(mesh) for name,mesh in unit['garments'].items()}}
    ports = {name: boundaries(mesh) for name,mesh in unit['garments'].items()}
    domains = {name: coverage_ids(name,body,mesh) for name,mesh in unit['garments'].items()}
    edges = {name: sorted({tuple(sorted((a,b))) for t in mesh['triangles'] for a,b in zip(t,t[1:]+t[:1])}) for name,mesh in unit['garments'].items()}
    for pose in rows:
        deltas = pose['deltas']; posed_body = transformed(body,deltas); body_tree = tree(posed_body,body['triangles'])
        item = {'sourceUnit': kind, 'pose': pose['name'], 'lean': pose['lean'], 'solver': pose.get('solver'), 'objects': {}}
        posed_garments = {}
        for name,mesh in unit['garments'].items():
            points = transformed(mesh,deltas); posed_garments[name] = points
            triangles = np.asarray(mesh['triangles'],dtype=np.int32)
            centers = points[triangles].mean(1); samples = np.concatenate([points,centers])
            signed = signed_samples(samples,body_tree)
            garment_tree = tree(points,mesh['triangles']); ids = domains[name]
            outside = signed_samples(posed_body[ids],garment_tree)
            erows = np.asarray(edges[name],dtype=np.int32)
            source_length = np.linalg.norm(mesh['xyz'][erows[:,0]]-mesh['xyz'][erows[:,1]],axis=1)
            pose_length = np.linalg.norm(points[erows[:,0]]-points[erows[:,1]],axis=1)
            ratios = pose_length / np.maximum(source_length,1e-9)
            areas = np.linalg.norm(np.cross(points[triangles[:,1]]-points[triangles[:,0]],points[triangles[:,2]]-points[triangles[:,0]]),axis=1)*.5
            original_areas = np.linalg.norm(np.cross(mesh['xyz'][triangles[:,1]]-mesh['xyz'][triangles[:,0]],mesh['xyz'][triangles[:,2]]-mesh['xyz'][triangles[:,0]]),axis=1)*.5
            worst = np.argsort(signed)[:12]
            witnesses = [{'sample': 'vertex' if i<len(points) else 'triangleCentroid',
                          'index': int(i if i<len(points) else i-len(points)), 'signedNearestBodyM': float(signed[i]),
                          'restNativePositionM': mesh['xyz'][i].tolist() if i<len(points) else mesh['xyz'][triangles[i-len(points)]].mean(0).tolist(),
                          'posedNativePositionM': samples[i].tolist()} for i in worst]
            domain_worst = np.argsort(outside)[-12:][::-1]
            coverage_witnesses = [{'originalBodyVertex': int(ids[i]), 'signedNearestGarmentM': float(outside[i]),
                                   'restNativePositionM': body['xyz'][ids[i]].tolist(), 'posedNativePositionM': posed_body[ids[i]].tolist()} for i in domain_worst]
            seam_ports = []
            for port in ports[name]:
                center = mesh['xyz'][port].mean(0); moving_center = points[port].mean(0)
                result = {'vertices': len(port), 'sourceVertexIDs': port, 'restCenterM': center.tolist(), 'posedCenterM': moving_center.tolist(),
                          'signedNearestBodyM': summary(signed[port])}
                if name == 'RiderHoodie' and abs(center[0]) > .2:
                    side = 'L' if center[0]>0 else 'R'
                    wrist = (deltas['DEF-hand.'+side] @ np.asarray([*rest['DEF-hand.'+side]['head'],1]))[:3]
                    elbow = (deltas['DEF-forearm.'+side] @ np.asarray([*rest['DEF-forearm.'+side]['head'],1]))[:3]
                    axis = (wrist-elbow)/np.linalg.norm(wrist-elbow)
                    result['wristSide'] = side; result['centerToWristM'] = float(np.linalg.norm(moving_center-wrist))
                    result['axialFromWristM'] = summary((points[port]-wrist) @ axis)
                seam_ports.append(result)
            item['objects'][name] = {'vertices': len(points), 'triangleCentroids': len(centers),
                'signedGarmentToBodyEstimateM': summary(signed), 'insideBodyOver2mmSampleCount': int((signed<-.002).sum()),
                'insideBodyOver5mmSampleCount': int((signed<-.005).sum()), 'penetrationWitnesses': witnesses,
                'bodyCoverageDomain': 'Rest anatomical source fields >.55 with actual garment Z bounds inset10mm',
                'signedBodyToGarmentEstimateM': summary(outside), 'bodyOutsideGarmentOver2mmCount': int((outside>.002).sum()),
                'coverageWitnesses': coverage_witnesses, 'sourceBoundaryPorts': seam_ports,
                'sourceNearZeroTriangleAreaCount': int((original_areas<1e-12).sum()),
                'posedNearZeroTriangleAreaCount': int((areas<1e-12).sum()),
                'edgeLengthRatio': {'p01': float(np.percentile(ratios,1)), 'median': float(np.median(ratios)),
                                    'p99': float(np.percentile(ratios,99)), 'min': float(ratios.min()), 'max': float(ratios.max())}}
        if kind == 'wardrobe':
            hoodie, jeans = unit['garments']['RiderHoodie'], unit['garments']['RiderJeans']
            hem = np.flatnonzero(hoodie['xyz'][:,2] < 1.0037942409515381+.025)
            waist = np.flatnonzero(jeans['xyz'][:,2] > 1.0217942409515381-.025)
            assert len(hem)>10 and len(waist)>10
            item['hoodieHemToJeansWaistNearestVertexM'] = summary(nearest_values(posed_garments['RiderHoodie'][hem],posed_garments['RiderJeans'][waist]))
        report_rows.append(item)

assert all(sha(path)==expected for _,path,expected,_ in UNITS)
report = {'accepted': False, 'numericalOnly': True, 'recipeSHA256': sha(__file__), 'poseInput': {'path':str(pose_path),'sha256':sha(pose_path)},
          'sourceInputs': inputs, 'allSourceFileBytesUnchanged': True, 'all75RestBonesUntouched': True,
          'all73NonSoleRestBonesExactlyEqualToSolverSource': True, 'identicalOriginal10582WearerAcrossUnits': True,
          'sourceArrayFingerprints': fingerprints, 'rows': report_rows,
          'limits': ['Nearest oriented triangle distance is a local penetration/coverage estimate, not an exact watertight collision or visibility proof.',
                     'Garment open ports, self-intersections and concave nearest normals can misclassify signs; concrete vertex/triangle witnesses require parent review.',
                     'Native fields remain their verified source FOUR; explicit canonical final derivative has not been applied to these source units.',
                     'Actual solver relative joint deltas drive array LBS; existing glTF serialization residuals are not claimed byte-identical moving native/GPU deformation.',
                     'Five generic ride poses plus rest identify defects; they do not certify complete outfit art, glove coverage, recorded play or device behavior.']}
(out/'measurement.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'accepted':False,'sourceBytesAndRestUnchanged':True,'rows':[{'unit':row['sourceUnit'],'pose':row['pose'],'objects':{name:{'deepInside5mmSamples':obj['insideBodyOver5mmSampleCount'],'bodyOutside2mm':obj['bodyOutsideGarmentOver2mmCount'],'minSignedM':obj['signedGarmentToBodyEstimateM']['minM']} for name,obj in row['objects'].items()}} for row in report_rows]}))
