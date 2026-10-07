"""Fixed finite source path/cuff/cycle relations; no volume or wearable proof."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def point_segments(point, starts, ends):
    direction = ends - starts
    length2 = (direction * direction).sum(1)
    assert (length2 > 0).all()
    t = np.clip(((point - starts) * direction).sum(1) / length2, 0, 1)
    closest = starts + t[:, None] * direction
    return ((closest - point) ** 2).sum(1), closest, t


def segment_segments(start, end, a, b):
    """All bounded endpoint candidates plus interior stationary line pair."""
    d, e = end - start, b - a
    dd, ee, de = float((d * d).sum()), (e * e).sum(1), (e * d).sum(1)
    assert dd > 0 and (ee > 0).all()
    delta = start - a
    da, ea = (delta * d).sum(1), (delta * e).sum(1)
    denominator = dd * ee - de * de
    active = denominator > 0
    s, t = np.zeros(len(a)), np.zeros(len(a))
    s[active] = (de[active] * ea[active] - ee[active] * da[active]) / denominator[active]
    t[active] = (dd * ea[active] - de[active] * da[active]) / denominator[active]
    interior = active & (s >= 0) & (s <= 1) & (t >= 0) & (t <= 1)
    pa, pb = start + s[:, None] * d, a + t[:, None] * e
    distances = [np.where(interior, ((pa - pb) ** 2).sum(1), np.inf)]
    paths, edges = [pa], [pb]
    for endpoint in [start, end]:
        distance, closest, _ = point_segments(endpoint, a, b)
        distances.append(distance)
        paths.append(np.broadcast_to(endpoint, a.shape))
        edges.append(closest)
    for endpoint in [a, b]:
        fraction = np.clip(((endpoint - start) * d).sum(1) / dd, 0, 1)
        closest = start + fraction[:, None] * d
        distances.append(((closest - endpoint) ** 2).sum(1))
        paths.append(closest)
        edges.append(endpoint)
    matrix = np.stack(distances, 1)
    selected = matrix.argmin(1)
    rows = np.arange(len(a))
    return matrix[rows, selected], np.stack(paths, 1)[rows, selected], np.stack(edges, 1)[rows, selected]


def barycentric(points, triangles):
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    u, v, delta = b - a, c - a, points - a
    uu, uv, vv = (u * u).sum(1), (u * v).sum(1), (v * v).sum(1)
    du, dv = (delta * u).sum(1), (delta * v).sum(1)
    denominator = uu * vv - uv * uv
    assert (denominator > 0).all()
    x, y = (du * vv - dv * uv) / denominator, (dv * uu - du * uv) / denominator
    return np.stack([1 - x - y, x, y], 1)


def segment_triangles(start, end, triangles):
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    normal = np.cross(b - a, c - a)
    nn = (normal * normal).sum(1)
    assert (nn > 0).all()
    direction = end - start
    signed_start = ((start - a) * normal).sum(1)
    denominator = (direction * normal).sum(1)
    active = denominator != 0
    fraction = np.zeros(len(a))
    fraction[active] = -signed_start[active] / denominator[active]
    plane_point = start + fraction[:, None] * direction
    plane_bary = barycentric(plane_point, triangles)
    # No near-parallel rejection: finite nonzero denominators remain measured.
    eligible = active & (fraction >= 0) & (fraction <= 1) & (plane_bary >= -1e-10).all(1)
    distances = [np.where(eligible, 0., np.inf)]
    paths, surfaces = [plane_point], [plane_point]
    for endpoint in [start, end]:
        offset = ((endpoint - a) * normal).sum(1) / nn
        point = endpoint - offset[:, None] * normal
        weights = barycentric(point, triangles)
        within = (weights >= 0).all(1)
        distances.append(np.where(within, ((point - endpoint) ** 2).sum(1), np.inf))
        paths.append(np.broadcast_to(endpoint, a.shape))
        surfaces.append(point)
    for edge_a, edge_b in [(a, b), (b, c), (c, a)]:
        distance, path, surface = segment_segments(start, end, edge_a, edge_b)
        distances.append(distance)
        paths.append(path)
        surfaces.append(surface)
    matrix = np.stack(distances, 1)
    selected, rows = matrix.argmin(1), np.arange(len(a))
    return matrix[rows, selected], np.stack(paths, 1)[rows, selected], np.stack(surfaces, 1)[rows, selected], eligible, fraction, plane_bary, denominator


def main():
    parser = argparse.ArgumentParser()
    for name in ['opening', 'opening-sha256', 'localization', 'localization-sha256', 'preflight', 'preflight-sha256', 'out', 'evidence']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    pins = [(args.opening, args.opening_sha256), (args.localization, args.localization_sha256), (args.preflight, args.preflight_sha256)]
    assert all(sha(path) == expected for path, expected in pins)
    opening = json.loads(Path(args.opening).read_text())
    localization = json.loads(Path(args.localization).read_text())
    preflight = json.loads(Path(args.preflight).read_text())
    source_pin = opening['candidate']
    assert source_pin == localization['source'] and source_pin['sha256'] == '8379004e394bbae110f495c13bfc12a205977061d13cefdcc8ee24c6e5343782'
    assert sha(source_pin['path']) == source_pin['sha256']
    source = np.load(source_pin['path'])
    xyz, faces = source['vertices'].astype(np.float64), source['faces']
    assert len(faces) == 14543 and len(xyz) == 8000
    triangles = xyz[faces]
    assert np.isfinite(triangles).all()
    boundary_ids = opening['topology']['orderedSourceBoundaryVertexIds']
    boundary_a, boundary_b = xyz[boundary_ids], np.roll(xyz[boundary_ids], -1, axis=0)
    assert len(boundary_ids) == 71
    cycles = localization['localizedCycles'][:2]
    assert [cycle['homologyClass'] for cycle in cycles] == [1, 2]
    cycle_incidence = {cycle['homologyClass']: set(cycle['incidentRetainedFaceRows']) for cycle in cycles}

    def lineage(row, point):
        weights = barycentric(point[None, :], triangles[row:row + 1])[0]
        vertices = faces[row]
        return {'retainedFaceRow': int(row), 'prototypeFaceRow': int(source['sourcePrototypeFaceRows'][row]), 'sourceVertexIds': vertices.tolist(), 'witnessSourceXYZ': point.tolist(), 'witnessTriangleBarycentric': weights.tolist(), 'prototypeCornerUV': source['cornerUVPrototype'][row].tolist(), 'witnessPrototypeUV': (source['cornerUVPrototype'][row] * weights[:, None]).sum(0).tolist(), 'denseTriangleRowsByCorner': source['originalTriangleRows'][vertices].tolist(), 'denseBarycentricByCorner': source['barycentric'][vertices].tolist(), 'cycleIncidentClasses': [klass for klass, rows in cycle_incidence.items() if row in rows]}

    # Fixed original five cuff-space hypotheses, never an occupancy assumption.
    anchors = np.array(preflight['anchors'], np.float64)
    assert anchors.shape == (5, 3) and (anchors[:, 1] == -.655137).all()
    ends_y = [-.655137, -.305137, -.105137, .145137, .245137]
    start_y = float(xyz[:, 1].min() - .1)
    records, raw = [], {}
    for anchor_index, anchor in enumerate(anchors):
        start = anchor.copy()
        start[1] = start_y
        for station in ends_y:
            end = anchor.copy()
            end[1] = station
            distance2, path_points, surface_points, hits, fraction, hit_bary, denominators = segment_triangles(start, end, triangles)
            assert np.isfinite(distance2).all() and (distance2 >= 0).all()
            worst = int(distance2.argmin())
            hit_rows = np.flatnonzero(hits)
            hit_rows = hit_rows[np.lexsort((hit_rows, fraction[hit_rows]))]
            hit_records = []
            for row in hit_rows:
                point = start + fraction[row] * (end - start)
                hit_records.append({'pathFraction': float(fraction[row]), 'sourceY': float(point[1]), 'triangleBarycentric': hit_bary[row].tolist(), 'strictInteriorBarycentric': bool((hit_bary[row] > 1e-10).all()), 'nearBoundaryBarycentric': bool((abs(hit_bary[row]) <= 1e-10).any()), 'directionNormalUnnormalized': float(denominators[row]), 'lineage': lineage(row, point)})
            boundary_distance2, boundary_path, boundary_points = segment_segments(start, end, boundary_a, boundary_b)
            boundary_row = int(boundary_distance2.argmin())
            cycle_relations = []
            for cycle in cycles:
                ids = cycle['sourceVertexIds']
                d2, pp, cp = segment_segments(start, end, xyz[ids], np.roll(xyz[ids], -1, axis=0))
                index = int(d2.argmin())
                cycle_relations.append({'class': cycle['homologyClass'], 'minimumDistanceSourceUnits': float(np.sqrt(d2[index])), 'closestSourceEdge': [ids[index], ids[(index + 1) % len(ids)]], 'pathWitness': pp[index].tolist(), 'cycleWitness': cp[index].tolist()})
            minimum = float(np.sqrt(distance2[worst]))
            record = {'anchorIndex': anchor_index, 'endY': station, 'startSourceXYZ': start.tolist(), 'endSourceXYZ': end.tolist(), 'testedAllRetainedTriangles': len(faces), 'surfaceIntersectionFaceCount': len(hit_records), 'allIntersectionFacesIncludingCoincidentEdgeHits': hit_records, 'minimumWholeSegmentSurfaceDistanceSourceUnits': minimum, 'closestPathSourceXYZ': path_points[worst].tolist(), 'closestSurfaceLineage': lineage(worst, surface_points[worst]), 'strictlyPositiveComputedSurfaceMargin': bool(minimum > 1e-10), 'ambiguousContactWithoutNonparallelHit': bool(not len(hit_records) and minimum <= 1e-10), 'boundaryRelation': {'minimumDistanceSourceUnits': float(np.sqrt(boundary_distance2[boundary_row])), 'closestBoundarySourceEdge': [boundary_ids[boundary_row], boundary_ids[(boundary_row + 1) % len(boundary_ids)]], 'pathWitness': boundary_path[boundary_row].tolist(), 'boundaryWitness': boundary_points[boundary_row].tolist()}, 'cycleRelations': cycle_relations}
            records.append(record)
            key = f'anchor{anchor_index}-station{station}'
            raw[key + '-surfaceDistanceSquared'] = distance2
            raw[key + '-surfacePathWitnesses'] = path_points
            raw[key + '-surfaceWitnesses'] = surface_points
            raw[key + '-nonparallelFaceIntersections'] = hits
            raw[key + '-intersectionFractions'] = fraction
            raw[key + '-intersectionBarycentric'] = hit_bary
    assert len(records) == 25 and all(sha(path) == expected for path, expected in pins)
    assert sha(source_pin['path']) == source_pin['sha256']
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    raw_path = out / 'fixed-path-witnesses.npz'
    np.savez_compressed(raw_path, **raw)
    report = {'acceptedWearable': False, 'status': 'FIXED_FINITE_SOURCE_PATH_CUFF_CYCLE_RELATIONS_ONLY', 'recipeSHA256': sha(__file__), 'source': source_pin, 'inputPins': [{'path': path, 'sha256': expected} for path, expected in pins], 'raw': {'path': str(raw_path), 'sha256': sha(raw_path)}, 'fixedAnchorSource': 'The unchanged five cavity05 anchor hypotheses, not recertified occupancy labels.', 'pathFamily': {'outsideStartY': start_y, 'fixedEndpointsY': ends_y, 'anchorCount': 5, 'segments': 25, 'pathDirection': 'Source+Y, fixed original anchor XZ.', 'pathRadius': 0, 'nearContactDisclosureThresholdSourceUnits': 1e-10}, 'records': records, 'limits': ['All14543actual retained source triangle surfaces queried on25declared continuous segments; finite Float64 arithmetic, not interval/exact arithmetic.', 'Positive computed margin means this zero-radius path is separated from the finite source surface. It does not establish endpoint solid/void occupancy, a hand-size capsule, free volume, or entry specifically through the cuff mouth.', 'The actual71edge boundary and two homology cycles are distance references only; no virtual mouth disk, clipping plane or synthetic blocker is inserted.', 'Coincident edge/corner hit face IDs are retained, not deduplicated or parity-counted into occupancy. Tangent/coplanar nearcontacts remain explicit uncertainty.', 'Distances and coordinates use uncalibrated donor units. Per-corner dense lineage cannot in general collapse a prototype face witness to a single dense donor triangle.', 'Genus1 alone is not a defect; no source interpretation/removal mask/fit/skin/render/cut/engine/device acceptance.']}
    Path(args.evidence).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'segments': len(records), 'zeroRadiusPathsWithPositiveComputedMargin': sum(r['strictlyPositiveComputedSurfaceMargin'] for r in records), 'surfaceIntersectingSegments': sum(r['surfaceIntersectionFaceCount'] > 0 for r in records)}))


if __name__ == '__main__':
    main()
