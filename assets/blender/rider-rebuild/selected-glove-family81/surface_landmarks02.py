"""Actual41 exposed joint surfaces and ancestry-owned nonplanar cuff features."""
import numpy as np
from construct import unit


def first_surface_faces(points, triangles, center, axis, preferred):
    """Intersect the actual source with the joint plane, then its first surfaces.

    The eight rays select existing face ancestry. Radii and field ownership are
    measured freely; neither a circular section nor an isolated digit is assumed.
    """
    p = points.astype(np.float64); axis = unit(axis)
    x = unit(preferred-np.dot(preferred, axis)*axis); z = np.cross(axis, x)
    signed = (p-center)@axis; face_signed = signed[triangles]
    crossing = np.flatnonzero((face_signed.min(axis=1) <= 0) & (face_signed.max(axis=1) >= 0))
    segments, owners, coefficients = [], [], []
    for face in crossing:
        ids = triangles[face]; values = signed[ids]
        assert not np.all(values == 0), ('Actual joint plane has a coplanar source face; inspect it explicitly', int(face))
        intersections = {}
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if values[i] == 0:
                bary = np.zeros(3); bary[i] = 1; intersections[('vertex', int(ids[i]))] = bary
            if values[i]*values[j] < 0:
                fraction = values[i]/(values[i]-values[j]); bary = np.zeros(3)
                bary[i], bary[j] = 1-fraction, fraction
                intersections[('edge', *sorted((int(ids[i]), int(ids[j]))))] = bary
        if len(intersections) == 1: continue  # A tangent point does not cross this joint section.
        assert len(intersections) == 2, (int(face), len(intersections))
        bary = np.asarray(list(intersections.values())); segment = bary@p[ids]-center
        segments.append(np.column_stack((segment@x, segment@z))); owners.append(int(face)); coefficients.append(bary)
    segments, coefficients = np.asarray(segments), np.asarray(coefficients); owners = np.asarray(owners, np.int32)
    assert len(segments), 'No actual source joint-plane section'
    start, edge = segments[:, 0], segments[:, 1]-segments[:, 0]
    cross2 = lambda a, b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
    selected, hits = [], []
    for ray in range(8):
        angle = 2*np.pi*ray/8; direction = np.asarray([np.cos(angle), np.sin(angle)])
        denominator = cross2(direction, edge); distance = np.full(len(edge), np.inf); fraction = np.full(len(edge), np.inf)
        nonparallel = denominator != 0
        distance[nonparallel] = cross2(start[nonparallel], edge[nonparallel])/denominator[nonparallel]
        fraction[nonparallel] = cross2(start[nonparallel], direction)/denominator[nonparallel]
        eligible = (distance > 0) & (fraction >= 0) & (fraction <= 1)
        assert eligible.any(), ('Actual source plane ray has no surface; no invented fallback', ray)
        nearest = distance[eligible].min(); tied = np.flatnonzero(eligible & (distance == nearest))
        for index in tied:
            bary = (1-fraction[index])*coefficients[index, 0]+fraction[index]*coefficients[index, 1]
            face = int(owners[index]); selected.extend(triangles[face].tolist())
            hits.append({'ray': ray, 'sourceFaceId': face, 'distanceM': float(nearest),
                         'sourceVertexIds': triangles[face].tolist(), 'barycentric': bary.tolist()})
    return np.unique(np.asarray(selected, np.uint32)), hits, len(segments)


def cuff_circuits(triangles, ancestry, expected_sizes):
    roles = ancestry['authoredVertexRoles']; face_roles = ancestry['authoredFaceRoles']; corner_roles = roles[triangles]
    # Exact41 first sewn-rim triangle: two retained exterior vertices and one
    # duplicated inner vertex(role3). The paired triangle has two role3 corners.
    first = np.flatnonzero((face_roles == 2) & ((corner_roles == 3).sum(axis=1) == 1))
    adjacency = {}
    for face in first:
        pair = triangles[face][corner_roles[face] != 3]; assert len(pair) == 2
        a, b = map(int, pair); adjacency.setdefault(a, set()).add(b); adjacency.setdefault(b, set()).add(a)
    assert all(len(neighbors) == 2 for neighbors in adjacency.values()), 'Actual rim is not the qualified degree2 circuits'
    remaining = set(adjacency); circuits = []
    while remaining:
        start = min(remaining); previous = None; current = start; ring = []
        while True:
            ring.append(current); remaining.remove(current)
            following = min(adjacency[current]) if previous is None else next(v for v in adjacency[current] if v != previous)
            if following == start: break
            assert following in remaining, 'Actual rim circuits join or repeat'
            previous, current = current, following
        circuits.append(np.asarray(ring, np.uint32))
    assert sorted(map(len, circuits)) == sorted(expected_sizes) == [71, 1688]
    return sorted(circuits, key=len), len(first)


def landmarks(points, fields, names, used, rest, side, triangles, ancestry, hand_receipt):
    bones = {row[0]: row for row in rest}
    bone = lambda stem: bones[stem+'.'+side]
    weight = lambda stems: fields[:, [names.index(stem+'.'+side) for stem in stems]].sum(axis=1)
    selected, records = [], []

    def save(label, ids, center, policy):
        ids = np.asarray(ids, np.uint32)
        assert len(ids) and used[ids].all(), label
        selected.extend(ids.tolist())
        records.append({'landmark': label, 'centerM': np.asarray(center).tolist(),
                        'originalVertexIds': ids.tolist(), 'sourcePositionsM': points[ids].tolist(), 'policy': policy})

    def ring(label, center, axis, preferred, mask, band):
        axis = unit(axis); x = unit(preferred-np.dot(preferred, axis)*axis); z = np.cross(axis, x)
        relative = points.astype(np.float64)-center
        axial, rx, rz = relative@axis, relative@x, relative@z
        radius2 = rx*rx+rz*rz
        eligible = used & mask & (np.abs(axial) <= band) & (radius2 > 0)
        sectors = np.floor((np.arctan2(rz, rx)+np.pi)*(8/(2*np.pi))).astype(np.int32) % 8
        ids = []
        for sector in range(8):
            group = np.flatnonzero(eligible & (sectors == sector))
            assert len(group), ('Missing actual source sector; no weaker fallback', label, sector)
            # Existing vertices nearest the real anatomical cross-section center;
            # sectors prevent all locks landing on one side of a joint or cuff.
            score = axial[group]**2+radius2[group]
            ids.append(int(group[np.argmin(score)]))
        save(label, ids, center, 'Eight real source sectors; complete incident fans; no invented target points.')

    for digit in ('thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'):
        stems = [f'DEF-{digit}.{index:02}' for index in (1, 2, 3)]
        support = weight(stems) >= .2
        for index, stem in enumerate(stems, 1):
            b = bone(stem); head, tail = np.asarray(b[2]), np.asarray(b[3]); axis = tail-head
            preferred = np.asarray(b[4])[:3, 0]
            if index == 1:
                ids, hits, segments = first_surface_faces(points, triangles, head, axis, preferred)
                save(f'{digit}-joint1', ids, head, 'Actual joint-plane first surface triangles and their complete source fans; real palm/hand ownership allowed.')
                records[-1].update(sourceSectionSegments=segments, firstSurfaceHits=hits,
                    actualNamedOwnership=[{names[j]: float(value) for j, value in enumerate(np.asarray(hit['barycentric'])@fields[hit['sourceVertexIds']]) if value > 0} for hit in hits])
            else:
                ring(f'{digit}-joint{index}', head, axis, preferred, support, np.linalg.norm(axis)*.35)
        tip = bone(stems[-1]); head, tail = np.asarray(tip[2]), np.asarray(tip[3]); axis = unit(tail-head)
        distal = used & (weight([stems[-1]]) >= .2)
        candidates = np.flatnonzero(distal); assert len(candidates)
        apex = candidates[np.argmax((points[candidates]-tail)@axis)]
        save(digit+'-tip-apex', [apex], tail, 'Distal semantic field longitudinal extreme from this side only.')
        ring(digit+'-tip-rim', tail, axis, np.asarray(tip[4])[:3, 0], distal,
             max(.002, np.linalg.norm(tail-head)*.6))

    hand = bone('DEF-hand'); wrist, palm_end = np.asarray(hand[2]), np.asarray(hand[3])
    across = unit(np.asarray(bone('DEF-f_pinky.01')[2])-bone('DEF-f_index.01')[2])
    palm_normal = unit(np.cross(unit(palm_end-wrist), across))
    web_pairs = [('thumb', 'f_index'), ('f_index', 'f_middle'), ('f_middle', 'f_ring'), ('f_ring', 'f_pinky')]
    for first, second in web_pairs:
        a, b = bone('DEF-'+first+'.01'), bone('DEF-'+second+'.01')
        center = (np.asarray(a[3] if first == 'thumb' else a[2])+b[2])/2
        mask = used & (weight(['DEF-'+first+'.01', 'DEF-'+second+'.01']) >= .2)
        relative = points-center; dorsal, transverse = relative@palm_normal, relative@across
        ids = []
        for sign_d in (-1, 1):
            for sign_t in (-1, 1):
                group = np.flatnonzero(mask & (dorsal*sign_d >= 0) & (transverse*sign_t >= 0))
                assert len(group), ('Missing real web quadrant', first, second, sign_d, sign_t)
                ids.append(int(group[np.argmin(np.einsum('ij,ij->i', relative[group], relative[group]))]))
        save(first+'-'+second+'-web', ids, center, 'Both actual adjacent digit fields, dorsal/palmar and both transverse halves.')

    forearm = bones['DEF-forearm.'+side+'.001']; axis = unit(np.asarray(forearm[3])-forearm[2])
    cuff_names = ['DEF-hand.'+side, 'DEF-forearm.'+side, 'DEF-forearm.'+side+'.001']
    cuff_mask = used & (fields[:, [names.index(name) for name in cuff_names]].sum(axis=1) >= .2)
    assert cuff_mask.any()
    preferred = np.asarray(forearm[4])[:3, 0]
    band = max(.003, np.linalg.norm(np.asarray(forearm[3])-forearm[2])*.1)
    ring('wrist-cuff-junction', wrist, axis, preferred, cuff_mask, band)
    circuits, sewn_triangles = cuff_circuits(triangles, ancestry, hand_receipt['returnOwnership']['actualAuthoredBoundaryCircuitVertices'])
    assert 2*sewn_triangles == hand_receipt['newNonplanarRimTriangles']
    for circuit in circuits:
        if len(circuit) == 71:
            anchors = circuit  # Preserve the complete small inherited-handle rim.
            policy = 'Every vertex of the actual71-edge inherited-handle rim, with complete source fans.'
        else:
            lengths = np.linalg.norm(points[np.roll(circuit, -1)]-points[circuit], axis=1)
            cumulative = np.r_[0, np.cumsum(lengths)]; assert cumulative[-1] > 0
            anchors = circuit[np.searchsorted(cumulative, np.arange(16)*cumulative[-1]/16, side='right')-1]
            assert len(np.unique(anchors)) == 16
            policy = 'Sixteen arc-ordered anchors on the actual nonplanar1688-edge rim; no axial-plane or circular-section invention.'
        save('actual-cuff-rim-'+str(len(circuit)), anchors, wrist, policy)
        records[-1].update(actualCircuitVertices=len(circuit), sewnFirstTriangleCount=sewn_triangles,
                          originalCircuitVertexIds=circuit.tolist())
    return np.unique(np.asarray(selected, np.uint32)), records
