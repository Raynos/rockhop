"""Actual source section connectivity and ordered underarm material curves.

Only diagnostic/control curves are sampled. No donor vertex/face is deleted,
sorted into a replacement surface, or assigned new UV or skin correspondence.
"""
import numpy as np


def section(points, faces, depth):
    y = points[:, 1]-depth
    candidate = np.flatnonzero((y[faces].min(1) < 0) & (y[faces].max(1) > 0))
    nodes, edge_nodes, segments, adjacency = [], {}, [], {}
    for face_id in candidate:
        face = faces[face_id]; triangle = points[face]; hits = []
        normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
        if not np.linalg.norm(normal): continue
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if y[face[a]]*y[face[b]] >= 0: continue
            # Exact original coordinates join UV-split copies of the SAME
            # source edge. This does not join merely nearby material sheets.
            key = tuple(sorted((tuple(triangle[a]), tuple(triangle[b]))))
            if key not in edge_nodes:
                t = -y[face[a]]/(y[face[b]]-y[face[a]])
                bary = np.zeros(3); bary[a] = 1-t; bary[b] = t
                edge_nodes[key] = len(nodes)
                nodes.append({'point': bary@triangle, 'face': int(face_id), 'bary': bary})
            hits.append(edge_nodes[key])
        if len(hits) != 2 or hits[0] == hits[1]: continue
        index = len(segments); segments.append((hits[0], hits[1], int(face_id), normal))
        for node in hits: adjacency.setdefault(node, []).append(index)
    return nodes, segments, adjacency


def trace(nodes, segments, adjacency, apex, first_segment, sign, chest_z, elbow_x):
    path = [apex]; current, previous = apex, None; segment = first_segment
    for _ in range(len(segments)+1):
        a, b, _, _ = segments[segment]; following = b if a == current else a
        if following in (apex, previous): return None
        path.append(following); p = nodes[following]['point']
        if p[2] <= chest_z: return 'torso', path
        if sign*p[0] >= elbow_x: return 'sleeve', path
        outgoing = [i for i in adjacency[following] if i != segment]
        if len(outgoing) != 1: return None
        previous, current, segment = current, following, outgoing[0]
    return None


def underarm(points, faces, depth, side, frames):
    sign = 1 if side == 'L' else -1
    nodes, segments, adjacency = section(points, faces, depth)
    bones = {b['name']: b for b in frames['authoringBones']}
    root = np.asarray(bones['AUTHOR_UpperArm.'+side]['sourceHead'])
    elbow = np.asarray(bones['AUTHOR_Forearm.'+side]['sourceHead'])
    chest_z = bones['AUTHOR_Chest']['sourceHead'][2]
    chest_x = abs(bones['AUTHOR_ShoulderBridge.'+side]['sourceHead'][0])
    lower = frames['landmarks']['lowerAxilla.'+side]['source'][2]
    candidates = []
    for node, incident in adjacency.items():
        p = nodes[node]['point']
        if len(incident) != 2 or not (chest_x <= sign*p[0] <= sign*root[0] and lower <= p[2] <= root[2]): continue
        other = [segments[i][1] if segments[i][0] == node else segments[i][0] for i in incident]
        if all(nodes[k]['point'][2] <= p[2] for k in other) and sum(segments[i][3][2] for i in incident) < 0:
            candidates.append(node)
    # The highest connected exterior crotch joining the actual torso and sleeve
    # meridians. Decorative folds which return to the same branch are excluded.
    for apex in sorted(candidates, key=lambda n: nodes[n]['point'][2], reverse=True):
        branches = [trace(nodes, segments, adjacency, apex, i, sign, chest_z, sign*elbow[0]) for i in adjacency[apex]]
        if all(branches) and {b[0] for b in branches} == {'torso', 'sleeve'}:
            return nodes, {kind: path for kind, path in branches}, {
                'side': side, 'sourceDepth': depth, 'sourceApex': nodes[apex]['point'].tolist(),
                'sourceApexFace': nodes[apex]['face'], 'sourceApexBarycentric': nodes[apex]['bary'].tolist(),
                'connectedSectionSegments': len(segments), 'materialBranchIdentity': 'ACTUAL_SOURCE_SECTION_CONNECTIVITY'}
    raise AssertionError(('No connected actual exterior crotch', side, depth, len(candidates)))


def sample_path(nodes, path, positions, faces, count):
    # Original material arclength determines order. No nearest-body query can
    # assign stations or clamp a proximal interval onto the crotch apex.
    source = np.array([nodes[i]['point'] for i in path])
    distance = np.r_[0., np.cumsum(np.linalg.norm(np.diff(source, axis=0), axis=1))]
    assert np.all(np.diff(distance) > 0)
    stations = np.linspace(0, distance[-1], count)
    rows = []
    for station in stations:
        index = min(len(path)-2, int(np.searchsorted(distance, station, side='right')-1))
        fraction = (station-distance[index])/(distance[index+1]-distance[index])
        first, second = (nodes[path[index+k]] for k in (0, 1))
        values = []
        for points in positions:
            a = first['bary']@points[faces[first['face']]]; b = second['bary']@points[faces[second['face']]]
            values.append(a*(1-fraction)+b*fraction)
        rows.append({'fraction': float(station/distance[-1]), 'points': values,
            'parents': [{'sourceFace': n['face'], 'barycentric': n['bary'].tolist()} for n in (first, second)],
            'segmentFraction': float(fraction)})
    return rows
