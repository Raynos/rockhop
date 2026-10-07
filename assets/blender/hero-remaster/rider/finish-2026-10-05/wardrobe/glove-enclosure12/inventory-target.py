"""Exact wrist-clipped target/chart inventory; no glove or source body authoring."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clip_mesh(xyz, triangles, origin, normal):
    signed = ((xyz - origin) * normal).sum(1)
    points, ancestry = xyz.tolist(), [[i, i, 0.] for i in range(len(xyz))]
    edge_points, faces, owners = {}, [], []

    def crossing(a, b):
        if signed[a] == 0:
            return int(a)
        if signed[b] == 0:
            return int(b)
        a, b = sorted((int(a), int(b)))
        assert signed[a] * signed[b] < 0
        key = (a, b)
        if key not in edge_points:
            fraction = float(signed[a] / (signed[a] - signed[b]))
            edge_points[key] = len(points)
            points.append((xyz[a] + fraction * (xyz[b] - xyz[a])).tolist())
            ancestry.append([a, b, fraction])
        return edge_points[key]

    for row, triangle in enumerate(triangles):
        polygon = []
        for a, b in zip(triangle, np.roll(triangle, -1)):
            inside_a, inside_b = signed[a] >= 0, signed[b] >= 0
            if inside_a:
                polygon.append(int(a))
            if inside_a != inside_b:
                polygon.append(crossing(a, b))
        polygon = list(dict.fromkeys(polygon))
        if len(polygon) >= 3:
            for i in range(1, len(polygon) - 1):
                faces.append([polygon[0], polygon[i], polygon[i + 1]])
                owners.append(row)
    return np.array(points), np.array(faces, np.int32).reshape(-1, 3), np.array(owners, np.int32), np.array(ancestry), signed


def edge_graph(faces):
    edges = {}
    for row, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            edges.setdefault(tuple(sorted((int(a), int(b)))), []).append(row)
    neighbors = [[] for _ in faces]
    for rows in edges.values():
        if len(rows) == 2:
            a, b = rows
            neighbors[a].append(b)
            neighbors[b].append(a)
    labels = np.full(len(faces), -1, np.int32)
    sizes = []
    for start in range(len(faces)):
        if labels[start] >= 0:
            continue
        component, queue, count = len(sizes), [start], 0
        while queue:
            row = queue.pop()
            if labels[row] >= 0:
                continue
            labels[row] = component
            count += 1
            queue.extend(neighbors[row])
        sizes.append(count)
    return edges, labels, sizes


def boundary_inventory(faces):
    edges, labels, sizes = edge_graph(faces)
    boundary = [edge for edge, rows in edges.items() if len(rows) == 1]
    adjacency = {}
    for a, b in boundary:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
    remaining, loops, unsupported = set(adjacency), [], []
    while remaining:
        first, queue, reached = min(remaining), [min(remaining)], set()
        while queue:
            current = queue.pop()
            if current in reached:
                continue
            reached.add(current)
            queue.extend(adjacency[current])
        remaining -= reached
        if any(len(adjacency[v]) != 2 for v in reached):
            unsupported.append(sorted(reached))
            continue
        loop, previous, current = [first], -1, first
        while True:
            nxt = next(v for v in adjacency[current] if v != previous)
            if nxt == first:
                break
            if nxt in loop:
                unsupported.append(sorted(reached))
                loop = []
                break
            loop.append(nxt)
            previous, current = current, nxt
        if loop:
            loops.append(loop)
    stats = {'faceComponentTriangleCounts': sizes, 'boundaryEdges': len(boundary), 'boundaryLoopCounts': len(loops), 'boundaryLoopEdgeCounts': [len(loop) for loop in loops], 'nonmanifoldEdges': [list(edge) for edge, rows in edges.items() if len(rows) > 2], 'boundaryVerticesWithNonTwoDegree': [v for v, rows in adjacency.items() if len(rows) != 2], 'unsupportedBoundaryVertexComponents': unsupported}
    return loops, edges, stats


def corner_ancestry(edge_ancestry, faces, triangle_owners, canonical_triangles):
    """Exact original canonical triangle/corner coordinates, without a weld."""
    barycentric = np.zeros((len(faces), 3, 3), np.float64)
    for row, (face, owner) in enumerate(zip(faces, triangle_owners)):
        source = canonical_triangles[owner].tolist()
        for corner, vertex in enumerate(face):
            a, b, t = edge_ancestry[vertex]
            barycentric[row, corner, source.index(int(a))] += 1 - t
            barycentric[row, corner, source.index(int(b))] += t
    return barycentric


def field_inventory(weights, faces, columns):
    """Complete field counts; all thresholds are declared inventory hints."""
    normalized = weights.astype(np.float64) / weights.sum(1)[:, None]
    corner_mass = normalized[faces][:, :, columns]
    face_mass = corner_mass.mean(1)
    digit_mass = np.array([face_mass[:, 1 + i * 3:1 + (i + 1) * 3].sum(1) for i in range(5)]).T
    active_digits = (digit_mass > 0).sum(1)
    total = face_mass.sum(1)
    top_two = np.sort(digit_mass, axis=1)[:, -2:]
    counts = {
        'allSelectedFaces': len(faces),
        'zeroMeanHand15Mass': int((total == 0).sum()),
        'positiveMeanHand15MassBelow015': int(((total > 0) & (total < .15)).sum()),
        'meanHand15MassAtLeast015': int((total >= .15).sum()),
        'facesByPositiveMeanDigitBranches': {str(i): int((active_digits == i).sum()) for i in range(6)},
        'mixedPositiveDigitBranches': int((active_digits >= 2).sum()),
        'twoDigitBranchesEachAbove002': int(((top_two[:, 0] > .02) & (top_two[:, 1] > .02)).sum()),
        'facesWithAnyZeroHand15Corner': int((corner_mass.sum(2) == 0).any(1).sum()),
        'rawRowSumMaxAbsoluteResidual': float(abs(weights.sum(1) - 1).max()),
        'countPolicy': 'All actual selected triangles retained; positive means >0. 0.15 weak and 0.02 mixed-web flags are hints, never inclusion thresholds.',
    }
    assert counts['zeroMeanHand15Mass'] + counts['positiveMeanHand15MassBelow015'] + counts['meanHand15MassAtLeast015'] == len(faces)
    assert sum(counts['facesByPositiveMeanDigitBranches'].values()) == len(faces)
    return face_mass, digit_mass, counts


def main():
    parser = argparse.ArgumentParser()
    for key in ['full', 'foundation', 'contract', 'display-fields', 'out', 'evidence']:
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    assert not Path(args.evidence).exists(), 'Fresh evidence required'
    assert Path(args.evidence).parent.is_dir(), 'Evidence directory must exist'
    pins = [(args.full, 'deb04faa6a5ca85ca9617cb963d84d5e62074aee281507c5a755fcbe8387d91c'), (args.foundation, 'b6eaa2ccee77a9e6f6395daa1fc473da3f6099f26f79895f288e1300b3fba3ae'), (args.contract, '1cae63bda363c79d70b37c8cf317696d02007ae17b8a8ecc4e990901eb1bab0e'), (args.display_fields, 'ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a')]
    assert all(sha(path) == expected for path, expected in pins)
    full, foundation, display = [np.load(path) for path in [args.full, args.foundation, args.display_fields]]
    contract = json.loads(Path(args.contract).read_text())
    names = full['boneNames'].tolist()
    assert names == foundation['boneNames'].tolist() == display['boneNames'].tolist() == contract['boneNames'] and len(names) == 51
    xyz, triangles = full['originalFullXYZ'].astype(np.float64), full['originalFullTriangles']
    assert xyz.shape == (13380, 3) and np.array_equal(xyz, foundation['canonicalXYZ'])
    assert np.array_equal(triangles, foundation['canonicalTriangles'])
    assert np.array_equal(full['rigRest'], foundation['boneRest'])
    assert np.array_equal(full['rigRest'], np.array([row['rest'] for row in contract['hierarchy']]))
    assert np.array_equal(full['rigWorld'], full['originalFullWorld'])
    assert np.array_equal(full['rigWorld'], full['canonicalFourWorld'])
    assert np.array_equal(full['rigWorld'], np.array(contract['rigWorld']))
    raw = {'FULL': full['originalFullWeights'], 'FOUR': foundation['canonicalWeights']}
    assert all(weights.shape == (13380, 51) and np.isfinite(weights).all() and (weights >= 0).all() and (weights.sum(1) > 0).all() for weights in raw.values())
    rest = full['rigRest'].astype(np.float64)
    refs = display['bodyAttributeEdgeSources']
    identity = np.flatnonzero((refs[:, 0] == refs[:, 1]) & (refs[:, 2] == 0))
    source_display_rows = {}
    for row in identity:
        source_display_rows.setdefault(int(refs[row, 0]), []).append(int(row))
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    output_arrays, records = {'boneNames': np.array(names), 'rigRest': rest, 'rigWorld': full['rigWorld'], 'originalFULLSourceAttributeIDs': full['originalFullSourceIDs'], 'originalConditionedFOURSourceAttributeIDs': full['canonicalFourSourceIDs']}, {}
    digits = ['thumb', 'index', 'middle', 'ring', 'pinky']
    for side in ['R', 'L']:
        hand_name = 'hand.' + side
        digit_names = [f'{digit}_{joint:02}.{side}' for digit in digits for joint in [1, 2, 3]]
        columns = [names.index(hand_name)] + [names.index(name) for name in digit_names]
        wrist = rest[names.index(hand_name), :3, 3]
        mcp = np.array([rest[names.index(f'{digit}_01.{side}'), :3, 3] for digit in ['index', 'middle', 'ring', 'pinky']])
        longitudinal = mcp.mean(0) - wrist
        longitudinal /= np.linalg.norm(longitudinal)
        origin = wrist - .010 * longitudinal
        p, f, source_triangle, edge_ancestry, signed = clip_mesh(xyz, triangles, origin, longitudinal)
        # Freeze first clip before any connectivity/loop/seed qualification.
        first_clip = out / (side + '-first-wrist-halfspace.npz')
        np.savez_compressed(first_clip, sourceXYZ=p, sourceTriangles=f, canonicalTriangleOwners=source_triangle, canonicalEdgeAncestry=edge_ancestry, canonicalSignedWristDistance=signed, planeOrigin=origin, planeNormal=longitudinal)
        records[side] = {'status': 'FIRST_TARGET_CLIP_CAPTURED_UNQUALIFIED', 'firstClippedTarget': {'path': str(first_clip), 'sha256': sha(first_clip)}, 'wristJoint': hand_name, 'wristSourceXYZ': wrist.tolist(), 'planeOriginSourceXYZ': origin.tolist(), 'planeNormalTowardMCPs': longitudinal.tolist(), 'forearmExtensionM': .010, 'sourceHandUVSeamsMeasured': False, 'sourceHandUVSeamLimitation': 'Foundation source contains canonicalUV0/canonicalCornerVertexIDs and displayBodyUV0/displayBodyCornerVertexIDs. This draft does not check hand UV continuity or transport UV through exact triangle-to-loop ancestry. Exact position alias/split attribute boundaries remain separate and unsupported; no UV continuity or final anatomical seam acceptance is inferred.'}
        edges, components, sizes = edge_graph(f)
        records[side]['wholeHalfspaceTopology'] = {'faceComponentTriangleCounts': sizes, 'nonmanifoldEdges': [list(edge) for edge, rows in edges.items() if len(rows) > 2], 'canonicalTrianglesBeforeClip': len(triangles), 'retainedCanonicalTriangleOwners': int(len(np.unique(source_triangle))), 'clippedHalfspaceTriangles': len(f), 'droppedCanonicalTriangleOwners': int(len(triangles) - len(np.unique(source_triangle)))}
        seed_records, selected_components = [], []
        for name, column in zip([hand_name] + digit_names, columns):
            eligible = np.flatnonzero(signed > 0)
            maximum = float(raw['FULL'][eligible, column].max())
            if maximum <= 0:
                seed_records.append({'bone': name, 'canonicalVertex': None, 'sourceFULLPeakWithinHalfspace': maximum, 'componentIDs': []})
                continue
            choices = eligible[raw['FULL'][eligible, column] >= maximum - 1e-8]
            joint = rest[column, :3, 3]
            seed = int(choices[np.argmin(((xyz[choices] - joint) ** 2).sum(1))])
            incident = np.flatnonzero((f == seed).any(1))
            component_ids = sorted(set(components[incident].tolist()))
            selected_components.extend(component_ids)
            seed_records.append({'bone': name, 'canonicalVertex': seed, 'sourceFULLPeakWithinHalfspace': maximum, 'componentIDs': component_ids})
        records[side]['allHand15FieldSeedCoverage'] = seed_records
        if len(set(selected_components)) != 1 or any(len(seed['componentIDs']) != 1 for seed in seed_records):
            records[side]['status'] = 'UNSUPPORTED_SPLIT_OR_MISSING_HAND15_FIELD_SEED_COVERAGE'
            records[side]['authoringStopped'] = True
            continue
        component = selected_components[0]
        selected = np.flatnonzero(components == component)
        vertices, local_faces = np.unique(f[selected].ravel(), return_inverse=True)
        local_faces = local_faces.reshape(-1, 3)
        points, ancestry = p[vertices], edge_ancestry[vertices]
        loops, local_edges, topology = boundary_inventory(local_faces)
        records[side]['selectedTargetTopology'] = topology
        boundary_vertices = sorted({vertex for edge, owners in local_edges.items() if len(owners) == 1 for vertex in edge})
        plane_distance = ((points[boundary_vertices] - origin) * longitudinal).sum(1)
        topology['boundaryOffWristPlaneVertices'] = [boundary_vertices[i] for i in np.flatnonzero(abs(plane_distance) > 1e-12)]
        _, alias_ids, alias_counts = np.unique(points, axis=0, return_inverse=True, return_counts=True)
        topology['exactCoincidentPositionAliasGroups'] = int((alias_counts > 1).sum())
        topology['verticesInExactCoincidentPositionAliasGroups'] = int(alias_counts[alias_counts > 1].sum())
        topology['coincidentPositionAliasCountPolicy'] = 'Exact Float64 XYZ only; no weld or tolerance merges. Canonical/source rows remain distinct.'
        alias_order = np.argsort(alias_ids, kind='stable')
        alias_ends = np.cumsum(alias_counts)
        alias_starts = np.concatenate(([0], alias_ends[:-1]))
        alias_vertices = [alias_order[start:end].tolist() for start, end in zip(alias_starts, alias_ends) if end - start > 1]
        topology['exactCoincidentPositionAliasVertexGroups'] = alias_vertices
        loop = np.array(loops[0], np.int32) if len(loops) == 1 else np.empty(0, np.int32)
        cross = np.cross(points[local_faces[:, 1]] - points[local_faces[:, 0]], points[local_faces[:, 2]] - points[local_faces[:, 0]])
        topology['zeroAreaTargetTriangles'] = np.flatnonzero(np.linalg.norm(cross, axis=1) == 0).tolist()
        a, b, t = ancestry[:, 0].astype(int), ancestry[:, 1].astype(int), ancestry[:, 2]
        weights = {field: raw[field][a].astype(np.float64) + t[:, None] * (raw[field][b].astype(np.float64) - raw[field][a].astype(np.float64)) for field in ['FULL', 'FOUR']}
        assert np.array_equal(points, xyz[a] + t[:, None] * (xyz[b] - xyz[a]))
        source_owners = source_triangle[selected]
        corner_barycentric = corner_ancestry(ancestry, local_faces, source_owners, triangles)
        # Preserve the complete selected geometry/fields/ancestry before outcome
        # qualification. Multiple loops or source attribute seams never weld.
        selected_path = out / (side + '-selected-unqualified-target.npz')
        np.savez_compressed(selected_path, targetXYZ=points, targetTriangles=local_faces, canonicalHalfspaceVertexRows=vertices, canonicalEdgeAncestry=ancestry, canonicalTriangleOwners=source_owners, canonicalCornerBarycentric=corner_barycentric, rawFULLWeights=weights['FULL'], conditionedFOURWeights=weights['FOUR'], boundaryEdges=np.array([edge for edge, owners in local_edges.items() if len(owners) == 1], np.int32).reshape(-1, 2), boundaryLoopVertexCounts=np.array([len(row) for row in loops], np.int32), boundaryLoopVertexRows=np.array([v for row in loops for v in row], np.int32))
        records[side]['selectedUnqualifiedTarget'] = {'path': str(selected_path), 'sha256': sha(selected_path)}
        records[side]['targetVertices'] = len(points)
        records[side]['targetTriangles'] = len(local_faces)
        records[side]['wristBoundaryEdges'] = topology['boundaryEdges']
        records[side]['wristBoundaryLoopCount'] = len(loops)
        unsupported = []
        if len(loops) != 1:
            unsupported.append('MULTIPLE_OR_MISSING_WRIST_BOUNDARY_LOOPS')
        if topology['nonmanifoldEdges'] or topology['boundaryVerticesWithNonTwoDegree'] or topology['unsupportedBoundaryVertexComponents']:
            unsupported.append('NONMANIFOLD_OR_UNTRACEABLE_SOURCE_BOUNDARY')
        if topology['boundaryOffWristPlaneVertices']:
            unsupported.append('SOURCE_ATTRIBUTE_BOUNDARY_OFF_WRIST_PLANE')
        if alias_vertices:
            unsupported.append('COINCIDENT_SOURCE_ATTRIBUTE_ROWS_UNRESOLVED_NO_WELD')
        if topology['zeroAreaTargetTriangles']:
            unsupported.append('ZERO_AREA_TARGET_TRIANGLES')
        original_vertices = a[a == b]
        display_map = []
        for vertex in original_vertices:
            rows = source_display_rows.get(int(vertex), [])
            assert rows and all(np.array_equal(display['bodyRestXYZ'][row], full['originalFullXYZ'][vertex]) for row in rows)
            assert all(np.array_equal(display['bodyFullWeights'][row], raw['FULL'][vertex]) and np.array_equal(display['bodyFourWeights'][row], raw['FOUR'][vertex]) for row in rows)
            display_map.append([int(vertex), min(rows)])
        unique_owners = np.unique(source_owners)
        cross_wrist_owners = unique_owners[(signed[triangles[unique_owners]].min(1) < 0) & (signed[triangles[unique_owners]].max(1) > 0)]
        display_faces = display['bodyCanonicalTriangleAncestry']
        assert all(np.count_nonzero(display_faces == row) == 1 for row in unique_owners)
        # Complete geometry precedes semantic chart hints: weak/mixed/zero hand
        # mass faces are retained in the selected component without a threshold.
        face_mass, digit_mass, full_counts = field_inventory(weights['FULL'], local_faces, columns)
        _, _, four_counts = field_inventory(weights['FOUR'], local_faces, columns)
        dominant_digit = digit_mass.argmax(1)
        chart = np.where(digit_mass.max(1) > face_mass[:, 0], dominant_digit + 1, 0).astype(np.int32)
        seam_edges = [edge for edge, owners in local_edges.items() if len(owners) == 2 and chart[owners[0]] != chart[owners[1]]]
        top_two = np.sort(digit_mass, axis=1)[:, -2:]
        web_candidate = (top_two[:, 0] > .02) & (top_two[:, 1] > .02)
        geometric_half = np.zeros(len(local_faces), np.int32)
        lateral = mcp[0] - mcp[-1]
        lateral -= float((lateral * longitudinal).sum()) * longitudinal
        lateral /= np.linalg.norm(lateral)
        half_normal = np.cross(longitudinal, lateral)
        center = points[local_faces].mean(1)
        geometric_half[((center - wrist) * half_normal).sum(1) >= 0] = 1
        output_arrays.update({side + 'TargetXYZ': points, side + 'TargetTriangles': local_faces, side + 'CanonicalEdgeAncestry': ancestry, side + 'CanonicalTriangleOwners': source_owners, side + 'CanonicalCornerBarycentric': corner_barycentric, side + 'CrossWristCanonicalTriangleIDs': cross_wrist_owners, side + 'OriginalCanonicalToDisplayVertexRows': np.array(display_map), side + 'RawFULLWeights': weights['FULL'], side + 'ConditionedFOURWeights': weights['FOUR'], side + 'WristBoundaryLoop': loop, side + 'JointFieldColumns': np.array(columns), side + 'FaceHandDigitMass': face_mass, side + 'CandidateDigitChart': chart, side + 'CandidateFieldSeamEdges': np.array(seam_edges, np.int32).reshape(-1, 2), side + 'MixedWebCandidateFaces': np.flatnonzero(web_candidate), side + 'PalmDorsalGeometricHalf': geometric_half})
        records[side].update({'status': 'UNSUPPORTED_TARGET_TOPOLOGY_OR_SOURCE_ATTRIBUTE_SEAMS' if unsupported else 'GEOMETRIC_TARGET_INVENTORY_COMPLETE_UV_SEAMS_UNMEASURED', 'unsupportedReasons': unsupported, 'authoringStopped': True, 'selection': 'Actual wrist halfspace clipping, then unique edge-connected component containing hand and all15sourceFULL joint-field seeds. Inclusion has no mass threshold.', 'canonicalTriangleOwners': len(unique_owners), 'clippedCrossWristCanonicalTriangles': len(cross_wrist_owners), 'allHand15FieldSeedsInOneComponent': seed_records, 'discardedHalfspaceComponentTriangleCounts': [size for index, size in enumerate(sizes) if index != component], 'wristBoundaryPlaneMaxResidualM': float(abs(plane_distance).max()) if len(plane_distance) else None, 'sourceDisplayOriginalHandXYZFULLFOURExact': True, 'sourceCanonicalHandTrianglesOccurOnceInDisplay': True, 'completeWeakMixedGeometryRetained': True, 'completeFaceFieldInventory': {'FULL': full_counts, 'FOUR': four_counts}, 'candidateDigitChartCounts': {('palmCuff' if i == 0 else digits[i - 1]): int((chart == i).sum()) for i in range(6)}, 'mixedWebCandidateFaces': int(web_candidate.sum()), 'candidateFieldChartSeamEdges': len(seam_edges), 'jointRestFrames': {name: rest[names.index(name)].tolist() for name in [hand_name] + digit_names}, 'palmDorsalHalfNormal': half_normal.tolist(), 'limits': ['Complete target-only clipped skin patch; no garment geometry, source edit, hand/body acceptance or clearance result.', 'Digit field chart/seam and mixed-web flags are inventory hints, not a final anatomical seam or source appearance mapping. Geometric palm/dorsal half orientation requires parent interpretation.', 'FULL source and conditionedFOUR are independently interpolated in Float64. No source field conditioning, rig change, native/engine skin or bake performed.']})
    assert all(sha(path) == expected for path, expected in pins)
    raw_path = out / 'hand-target-charts.npz'
    np.savez_compressed(raw_path, **output_arrays)
    unsupported_hands = [side for side, record in records.items() if record['status'].startswith('UNSUPPORTED')]
    report = {'acceptedWearable': False, 'status': 'TARGET_INVENTORY_CAPTURED_WITH_UNSUPPORTED_OUTCOMES' if unsupported_hands else 'GEOMETRIC_TARGET_INVENTORY_COMPLETE_UV_SEAMS_UNMEASURED', 'unsupportedHands': unsupported_hands, 'authoringStopped': True, 'recipeSHA256': sha(__file__), 'inputPins': [{'path': path, 'sha256': expected} for path, expected in pins], 'sourceCanonicalGeometryXYZTrianglesExactAcrossFULLFOUR': True, 'named51RestWorldExactAcrossSourcePins': True, 'raw': {'path': str(raw_path), 'sha256': sha(raw_path)}, 'hands': records, 'limits': ['Target-only inventory; no glove construction, fit, body/hand acceptance, skeleton/source edit, bake, skin, render, cavity or wearable qualification.', 'Actual hand UV seam continuity is not checked by this draft despite available canonical/display body UV and corner vertex arrays. Exact source triangle-to-loop/corner lineage must be established and preserved before UV transport or garment authoring; no coordinate matching or weld is an acceptable substitute. A geometric one-loop result does not admit garment authoring.']}
    with Path(args.evidence).open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'hands': {side: {'status': record['status'], 'vertices': record.get('targetVertices'), 'triangles': record.get('targetTriangles'), 'wristBoundary': record.get('wristBoundaryEdges')} for side, record in records.items()}}))


if __name__ == '__main__':
    main()
