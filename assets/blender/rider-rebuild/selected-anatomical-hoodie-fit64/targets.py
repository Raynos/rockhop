"""Fixed anatomical targets from connected selected cloth meridians.

Nearest-body DISTANCE validates a prescribed section target; its point/normal
never selects the anatomical destination or moves a garment vertex.
"""
import runpy
from pathlib import Path
import numpy as np

S = runpy.run_path(str(Path(__file__).with_name('sections.py')))
G = runpy.run_path(str(Path(__file__).with_name('geometry.py')))
M = runpy.run_path(str(Path(__file__).with_name('meridian.py')))
I = runpy.run_path(str(Path(__file__).with_name('intervals.py')))


def smooth(t):
    t = np.clip(t, 0., 1.); return t*t*t*(10+t*(-15+6*t))


def make(context, original, broad, faces, nearest, target, cpu_pair=None, cpu_canonical=None):
    c = context; controls = c['controls']; source = c['source']
    xyz = source*np.asarray(controls['sourceDisplayAffine']['scale'])+controls['sourceDisplayAffine']['translation']
    if cpu_pair is None:
        from mathutils import Vector
        from mathutils.bvhtree import BVHTree
        source_tree = BVHTree.FromPolygons([Vector(p) for p in original], faces.tolist(), all_triangles=True)
    body_points, body_faces = c['bp'], c['bf']
    body_mesh = G['Mesh'](body_points, body_faces)
    body_triangles = body_points[body_faces]
    body_minimum, body_maximum = body_triangles.min(1), body_triangles.max(1)
    precision = float(np.spacing(np.float32(max(abs(body_points).max(), 1.))))
    numerical_tolerance = c['config']['field']['numericalContactToleranceM']
    source_controls, targets, records, omissions = [], [], [], []

    def pair(row):
        if cpu_pair is not None: return cpu_pair(row)
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
        left, right = bounds
        intervals, report = I['feasible'](body_mesh, nearest, np.array([0., y, z]),
            np.array([sign, 0., 0.]), offsets, left, right, target)
        c['failureContext']['target']['lastApexRadiusIntervals'] = report
        if not intervals: return None
        return intervals[0]

    bones = {b['name']: b for b in controls['authoringBones']}
    canonical = {}
    for name in ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003', 'DEF-spine.004', 'DEF-upper_arm.L', 'DEF-upper_arm.R', 'DEF-forearm.L', 'DEF-forearm.R', 'DEF-hand.L', 'DEF-hand.R'):
        if cpu_canonical is not None: canonical[name] = cpu_canonical[name]
        else:
            bone = c['rig'].data.bones[name]
            canonical[name] = {'head': list(bone.head_local), 'tail': list(bone.tail_local)}
    torso_axis = M['Axis']([canonical[n]['head'] for n in ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003', 'DEF-spine.004')])
    for side, sign in (('L', 1), ('R', -1)):
        sleeve_axis = M['Axis']([canonical[n+'.'+side]['head'] for n in ('DEF-upper_arm', 'DEF-forearm', 'DEF-hand')])
        center = controls['landmarks']['lowerAxilla.'+side]['source'][1]
        front = controls['landmarks']['frontArmhole.'+side]['source'][1]
        rear = controls['landmarks']['rearArmhole.'+side]['source'][1]
        found = 0
        for depth in np.linspace(front, rear, 13):
            c['failureContext']['target'] = {'side': side, 'sourceDepth': float(depth), 'stage': 'SOURCE_SECTION'}
            try: nodes, branches, record = S['underarm'](xyz, faces, float(depth), side, controls)
            except AssertionError as error:
                omissions.append({'side': side, 'depth': float(depth), 'reason': str(error)})
                continue
            paths = {role: S['sample_path'](nodes, path, (original, broad), faces, 9) for role, path in branches.items()}
            pairs = {}
            for role, rows in paths.items():
                c['failureContext']['target'].update(role=role, stage='ACTUAL_SOURCE_PAIRED_WALLS')
                pairs[role] = []
                for row in rows:
                    c['failureContext']['target'].update(sourceMaterialStation=row['fraction'],
                        originalOuterPoint=row['points'][0].tolist(), broad50OuterPoint=row['points'][1].tolist())
                    pairs[role].append(pair(row))
            original_apex, _, apex_ancestry = next(iter(pairs.values()))[0]
            offsets = original_apex-original_apex.mean(0); apex = original_apex.mean(0)
            upper = min(apex[2], canonical['DEF-upper_arm.'+side]['head'][2])
            lower = max(row[-1][1].mean(0)[2] for row in pairs.values())
            c['failureContext']['target'] = {'side': side, 'sourceDepth': float(depth), 'role': 'shared_apex',
                'stage': 'HIGHEST_FEASIBLE_PAIRED_APEX', 'originalApexPair': original_apex.tolist(),
                'bodyHeightBracket': [float(lower), float(upper)], 'bodyRayDepth': float(apex[1])}
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
                branch_pairs = pairs[role]; end_pair = branch_pairs[-1][1]
                endpoint_gap = float(nearest(end_pair)[0].min())
                context = {'side': side, 'sourceDepth': float(depth), 'role': role}
                c['failureContext']['target'] = {**context, 'stage': 'PRESCRIBED_ANATOMICAL_OFFSET_MERIDIAN',
                    'healthy50EndpointPair': end_pair.tolist(), 'endpointActual3DClearanceM': endpoint_gap,
                    'fixedApexPair': (target_apex+offsets).tolist(),
                    'canonicalAxisControlPoints': (torso_axis if role == 'torso' else sleeve_axis).points.tolist()}
                assert endpoint_gap >= target-numerical_tolerance, ('Healthy endpoint has insufficient actual3D clearance', c['failureContext']['target'])
                # The shared apex lies in a finite torso/arm cavity, but each
                # incident curve subsequently follows its own named anatomy.
                # A rear sleeve endpoint need not intersect a horizontal arm
                # section, and is retained exactly with its measured ease.
                meridian = M['Meridian'](torso_axis if role == 'torso' else sleeve_axis,
                    target_apex+offsets, end_pair, body_mesh, nearest, target, precision, context, numerical_tolerance)
                try: fitted, meridian_report = meridian.controls(rows, branch_pairs)
                except Exception:
                    c['failureContext']['target']['lastStation'] = meridian.last
                    raise
                for source_pair, destination, row in fitted:
                    source_controls.extend(source_pair); targets.extend(destination)
                record['branches'][role] = {'controls': [row for _, _, row in fitted],
                    'anatomicalMeridian': meridian_report}
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
        'targetMethod': 'Actual source cavity apex to separate canonical torso/sleeve offset meridians with ordered material arclength and exact healthy50 endpoint ease',
        'bodyClearanceTargetM': target, 'nearestBodyDirectionsUsedForConstruction': False,
        'newAcceptanceThresholdInvented': False}
