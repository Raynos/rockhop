"""Fixed anatomical targets from connected selected cloth meridians.

Nearest-body DISTANCE validates a prescribed section target; its point/normal
never selects the anatomical destination or moves a garment vertex.
"""
import runpy
from pathlib import Path
import numpy as np

S = runpy.run_path(str(Path(__file__).with_name('sections.py')))


def smooth(t):
    t = np.clip(t, 0., 1.); return t*t*t*(10+t*(-15+6*t))


def make(context, original, broad, faces, nearest, target):
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    c = context; controls = c['controls']; source = c['source']
    xyz = source*np.asarray(controls['sourceDisplayAffine']['scale'])+controls['sourceDisplayAffine']['translation']
    source_tree = BVHTree.FromPolygons([Vector(p) for p in original], faces.tolist(), all_triangles=True)
    body_points, body_faces = c['bp'], c['bf']
    body_triangles = body_points[body_faces]
    body_minimum, body_maximum = body_triangles.min(1), body_triangles.max(1)
    precision = float(np.spacing(np.float32(max(abs(body_points).max(), 1.))))
    source_controls, targets, records, omissions = [], [], [], []

    def pair(row):
        point, broad_point = row['points']
        q, n, face, distance = source_tree.find_nearest(Vector(point))
        assert distance <= 2*precision, ('Material point is not on original surface', distance)
        normal = np.asarray(n); start = point-normal*precision
        inside, _, inner_face, length = source_tree.ray_cast(Vector(start), Vector(-normal))
        assert inside is not None and length > precision, 'Actual selected paired wall is missing'
        inside = np.asarray(inside)
        triangle = original[faces[inner_face]]; matrix = (triangle[1:]-triangle[0]).T
        uv = np.linalg.lstsq(matrix, inside-triangle[0], rcond=None)[0]
        bary = np.r_[1-uv.sum(), uv]
        assert np.min(bary) >= -8*np.finfo(np.float32).eps
        broad_inside = bary@broad[faces[inner_face]]
        return np.array([point, inside]), np.array([broad_point, broad_inside]), {
            'outerMaterial': {k: row[k] for k in ('parents', 'segmentFraction')},
            'innerOriginalFace': int(inner_face), 'innerOriginalBarycentric': bary.tolist(),
            'sourceWallSpanM': float(np.linalg.norm(inside-point))}

    def gap(y, z, sign):
        # Exact triangle intersections with a prescribed world X-line. Source
        # branch identity was settled by connectivity before this body query.
        origin = np.array([0., y, z]); direction = np.array([sign, 0., 0.])
        tri = body_triangles
        ids = np.flatnonzero((body_minimum[:, 1] <= y) & (body_maximum[:, 1] >= y)
            & (body_minimum[:, 2] <= z) & (body_maximum[:, 2] >= z))
        t = tri[ids]; e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
        cross = np.cross(direction, e2); det = np.einsum('ij,ij->i', e1, cross)
        valid = abs(det) > np.finfo(float).eps; inverse = 1/np.where(valid, det, 1.)
        delta = origin-t[:, 0]; u = np.einsum('ij,ij->i', delta, cross)*inverse
        q = np.cross(delta, e1); v = q@direction*inverse
        distance = np.einsum('ij,ij->i', e2, q)*inverse
        good = np.flatnonzero(valid & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance > 0))
        rows = sorted((float(distance[i]), float(np.cross(e1[i], e2[i])@direction)) for i in good)
        for (left, a), (right, b) in zip(rows[:-1], rows[1:]):
            if a > 0 and b < 0 and right-left > precision:
                return left, right
        return None

    def clearance(center, offsets): return float(nearest(center+offsets)[0].min())

    def feasible_interval(y, z, sign, offsets):
        bounds = gap(y, z, sign)
        if bounds is None: return None
        left, right = bounds; middle = (left+right)/2
        def good(x): return clearance(np.array([sign*x, y, z]), offsets) >= target
        if not good(middle): return None
        result = []
        for boundary in (left, right):
            outside, inside = boundary, middle
            # A root of the fixed actual3D clearance, not an ease/target sweep.
            while abs(outside-inside) > precision:
                value = (outside+inside)/2
                if good(value): inside = value
                else: outside = value
            result.append(inside)
        return result

    bones = {b['name']: b for b in controls['authoringBones']}
    canonical = {}
    for name in ('DEF-spine.003', 'DEF-spine.004', 'DEF-upper_arm.L', 'DEF-upper_arm.R', 'DEF-forearm.L', 'DEF-forearm.R'):
        bone = c['rig'].data.bones[name]
        canonical[name] = {'head': list(bone.head_local), 'tail': list(bone.tail_local)}
    for side, sign in (('L', 1), ('R', -1)):
        center = controls['landmarks']['lowerAxilla.'+side]['source'][1]
        front = controls['landmarks']['frontArmhole.'+side]['source'][1]
        rear = controls['landmarks']['rearArmhole.'+side]['source'][1]
        found = 0
        for depth in np.linspace(front, rear, 13):
            try: nodes, branches, record = S['underarm'](xyz, faces, float(depth), side, controls)
            except AssertionError as error:
                omissions.append({'side': side, 'depth': float(depth), 'reason': str(error)})
                continue
            paths = {role: S['sample_path'](nodes, path, (original, broad), faces, 9) for role, path in branches.items()}
            pairs = {role: [pair(row) for row in rows] for role, rows in paths.items()}
            original_apex, _, apex_ancestry = next(iter(pairs.values()))[0]
            offsets = original_apex-original_apex.mean(0); apex = original_apex.mean(0)
            upper = min(apex[2], canonical['DEF-upper_arm.'+side]['head'][2])
            lower = max(row[-1][1].mean(0)[2] for row in pairs.values())
            assert lower < upper
            interval = feasible_interval(apex[1], lower, sign, offsets)
            assert interval is not None, ('No feasible actual3D gap on connected meridian branch', side, depth)
            if feasible_interval(apex[1], upper, sign, offsets) is not None:
                lower = upper
            else:
                while upper-lower > precision:
                    mid = (upper+lower)/2; candidate = feasible_interval(apex[1], mid, sign, offsets)
                    if candidate is None: upper = mid
                    else: lower = mid; interval = candidate
            interval = feasible_interval(apex[1], lower, sign, offsets)
            target_apex = np.array([sign*np.mean(interval), apex[1], lower])
            source_controls.extend(original_apex); targets.extend(target_apex+offsets)
            record.update(actualOriginalApexPair=original_apex.tolist(), targetApexPair=(target_apex+offsets).tolist(),
                pairedWall=apex_ancestry, target3DClearanceM=clearance(target_apex, offsets), branches={})
            for role, rows in paths.items():
                branch_pairs = pairs[role]; end_pair = branch_pairs[-1][1]; end = end_pair.mean(0)
                assert end[2] < target_apex[2], ('No ordered target meridian', side, depth, role)
                endpoint_interval = feasible_interval(end[1], end[2], sign, end_pair-end)
                assert endpoint_interval is not None
                width = endpoint_interval[1]-endpoint_interval[0]
                assert width > 0
                end_fraction = (sign*end[0]-endpoint_interval[0])/width
                assert 0 <= end_fraction <= 1, ('Healthy50 material anchor is not in the corresponding exterior branch', side, depth, role)
                # Trace the prescribed body-gap branch, then use its normalized
                # arclength for ALL original stations. No station is clamped to
                # the apex; paired sections share exactly the same station.
                curve = []
                for fraction in np.linspace(0, 1, 33):
                    z = target_apex[2]*(1-fraction)+end[2]*fraction
                    y = target_apex[1]*(1-fraction)+end[1]*fraction
                    k = min(7, int(fraction*8)); blend = fraction*8-k
                    first, last = branch_pairs[k][0], branch_pairs[k+1][0]
                    vector = (first-first.mean(0))*(1-blend)+(last-last.mean(0))*blend
                    vector = vector*(1-smooth(fraction))+(end_pair-end)*smooth(fraction)
                    valid = feasible_interval(y, z, sign, vector)
                    assert valid is not None, ('Actual body-gap branch disconnected', side, depth, role, fraction)
                    position = (1-smooth(fraction))*.5+smooth(fraction)*end_fraction
                    x = sign*(valid[0]*(1-position)+valid[1]*position)
                    curve.append([x, y, z])
                curve = np.asarray(curve); length = np.r_[0., np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
                assert np.all(np.diff(length) > 0); length /= length[-1]
                rows_report = []
                for index, row in enumerate(rows[1:], 1):
                    fraction = row['fraction']; p, broad_pair, ancestry = branch_pairs[index]
                    center_target = np.array([np.interp(fraction, length, curve[:, a]) for a in range(3)])
                    wall = (p-p.mean(0))*(1-smooth(fraction))+(broad_pair-broad_pair.mean(0))*smooth(fraction)
                    valid = feasible_interval(center_target[1], center_target[2], sign, wall)
                    assert valid is not None, ('No transverse room at ordered material station', side, depth, role, index)
                    across = (1-smooth(fraction))*.5+smooth(fraction)*end_fraction
                    center_target[0] = sign*(valid[0]*(1-across)+valid[1]*across)
                    # Preserve paired-wall orientation and native ancestry;
                    # the continuous cage subsequently carries both sheets.
                    destination = center_target+wall
                    assert float(nearest(destination)[0].min()) >= target, ('Prescribed paired target violates actual3D clearance', side, depth, role, index)
                    source_controls.extend(p); targets.extend(destination)
                    rows_report.append({'materialFraction': fraction, 'sourcePair': p.tolist(), 'targetPair': destination.tolist(), 'ancestry': ancestry})
                record['branches'][role] = rows_report
            records.append(record); found += 1
        assert found >= 2, ('Missing ordered source cavity sections', side, found)
    # Coarse original-material cells anchor already useful50 regions. The
    # reconstructed connected axilla is excluded by authored shoulder frames,
    # never by a strain percentile or a newly invented art acceptance cap.
    owned = np.zeros(len(original), bool)
    for side, sign in (('L', 1), ('R', -1)):
        root = bones['AUTHOR_UpperArm.'+side]['sourceHead']; elbow = bones['AUTHOR_Forearm.'+side]['sourceHead']
        chest = bones['AUTHOR_ShoulderBridge.'+side]['sourceHead']
        front = controls['landmarks']['frontArmhole.'+side]['source'][1]; rear = controls['landmarks']['rearArmhole.'+side]['source'][1]
        owned |= (sign*xyz[:, 0] >= abs(chest[0])) & (sign*xyz[:, 0] <= abs(elbow[0])) \
            & (xyz[:, 2] >= bones['AUTHOR_Chest']['sourceHead'][2]) & (xyz[:, 2] <= root[2]) \
            & (xyz[:, 1] >= front) & (xyz[:, 1] <= rear)
    eligible = np.flatnonzero(~owned); cells = np.floor(xyz[eligible]/(2*c['config']['field']['fieldCellM'])).astype(int)
    _, first = np.unique(cells, axis=0, return_index=True); anchors = eligible[first]
    health = nearest(broad[anchors])[0] >= target
    omitted_anchors = anchors[~health]; anchors = anchors[health]
    source_controls.extend(original[anchors]); targets.extend(broad[anchors])
    return np.asarray(source_controls), np.asarray(targets), {'sourceMeridians': records,
        'sourceSectionWithoutConnectedCrotch': omissions, 'healthy50OriginalNativeAnchorIds': anchors.tolist(),
        'unhealthy50AnchorsNotAdmittedOriginalNativeIds': omitted_anchors.tolist(),
        'anatomicalOwnershipOriginalVertexCount': int(owned.sum()),
        'exactCanonical75SectionLandmarks': canonical,
        'targetMethod': 'Actual source cavity bifurcation and connected ordered meridians to highest true3D feasible paired-wall body gap',
        'bodyClearanceTargetM': target, 'nearestBodyDirectionsUsedForConstruction': False,
        'newAcceptanceThresholdInvented': False}
