"""Compare real compact/dense jeans material sections before cavity fitting.

A closed C material contour can enclose fabric while leaving the wearer in
air. It is not a missing mesh contour and cannot be relabelled as a nested
cavity. This audit keeps every actual section, including directional gaps.
Run with the parent's serial model guard, two threads and fresh harness output.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/jeans'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def material_rays(contours, center, count=720):
    """All actual material intersections; never fill a directional source gap."""
    polygons = [c['polygon'][:, [0, 2]] for c in contours]
    a = np.concatenate(polygons) - center
    b = np.concatenate([np.roll(p, -1, axis=0) for p in polygons]) - center
    e = b - a
    cross = lambda p, q: p[..., 0] * q[..., 1] - p[..., 1] * q[..., 0]
    rows = []
    for angle in np.linspace(0, 2*np.pi, count, endpoint=False):
        direction = np.array([np.cos(angle), np.sin(angle)])
        denominator = cross(direction, e); valid = np.abs(denominator) > 1e-13
        t = np.divide(cross(a, e), denominator, out=np.zeros(len(a)), where=valid)
        u = np.divide(cross(a, direction), denominator, out=np.zeros(len(a)), where=valid)
        ids = np.flatnonzero(valid & (t > 1e-10) & (u >= 0) & (u < 1))
        ids = ids[np.argsort(t[ids])]
        rows.append({'angleRadians': float(angle), 'hitCount': len(ids),
                     'distances': t[ids].tolist(), 'sectionEdgeRows': ids.tolist()})
    return rows


def angular_material_coverage(contours, center):
    """Segment cone union detects gaps narrower than the sampled ray grid.

    Every noncritical ray crosses one segment for each active angular cone.
    This is a Float64 event arrangement, not a manufactured cavity polygon.
    Endpoint directions and actual segment rows remain explicit witnesses.
    """
    polygons = [c['polygon'][:, [0, 2]] for c in contours]
    a = np.concatenate(polygons) - center
    b = np.concatenate([np.roll(p, -1, axis=0) for p in polygons]) - center
    assert np.all(np.linalg.norm(a, axis=1) > 1e-10), 'Air centre touches actual material boundary'
    first = np.mod(np.arctan2(a[:, 1], a[:, 0]), 2*np.pi)
    second = np.mod(np.arctan2(b[:, 1], b[:, 0]), 2*np.pi)
    delta = (second-first+np.pi)%(2*np.pi)-np.pi
    assert np.all(np.abs(delta) < np.pi-1e-10), 'Air centre lies on/too near a material segment'
    lo = np.where(delta >= 0, first, second)
    hi = lo+np.abs(delta)
    events = {0.: [], float(2*np.pi): []}
    for row, (start, end) in enumerate(zip(lo, hi)):
        intervals = [(start, end)] if end <= 2*np.pi else [(start, 2*np.pi), (0., end-2*np.pi)]
        for lower, upper in intervals:
            if upper == lower:
                continue
            events.setdefault(float(lower), []).append([row, 1])
            events.setdefault(float(upper), []).append([row, -1])
    angles = sorted(events)
    active = set(); intervals = []
    for index, angle in enumerate(angles[:-1]):
        # Process exact coincident starts/ends together; critical rays themselves
        # remain in the sampled witness family and do not prove open intervals.
        for row, sign in events[angle]:
            if sign < 0:
                active.discard(row)
        for row, sign in events[angle]:
            if sign > 0:
                active.add(row)
        following = angles[index+1]
        if following > angle and not active:
            intervals.append({'startRadians': angle, 'endRadians': following,
                              'widthRadians': following-angle,
                              'startEventActualSegmentRows': events[angle],
                              'endEventActualSegmentRows': events[following]})
    return {'eventDirections': len(angles), 'gapIntervals': intervals,
            'totalGapRadians': float(sum(row['widthRadians'] for row in intervals)),
            'method': 'Float64 actual-segment angular cone event arrangement; no gap-grid approximation'}


def topology(vertices, faces):
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    unique, count = np.unique(edges, return_counts=True, axis=0)
    return {'vertices': len(vertices), 'triangles': len(faces),
            'boundaryEdges': int(np.sum(count == 1)), 'nonmanifoldEdges': int(np.sum(count > 2)),
            'bounds': [vertices.min(0).tolist(), vertices.max(0).tolist()]}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args(); out = Path(args.out).resolve()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild') and not out.exists()
    section_path = ROOT / 'assets/blender/rider-rebuild/glove-charts01/audit-hand-anatomy.py'
    section = load(section_path, 'source_slit_sections')
    registration = load(HERE / 'register-sections.py', 'source_slit_registration')
    report = {'accepted': False, 'status': 'ACTUAL_SOURCE_MATERIAL_SECTION_AUDIT',
              'recipeSHA256': sha(__file__), 'sectionHelperSHA256': sha(section_path),
              'sources': {}, 'limits': [
                  'No source fit, body change, native garment, bake, or moving-art acceptance.',
                  'Failed-plane centres interpolate genuine measured neighbouring cavities; they are proposals, not fictitious nested contours.',
                  'Directional gaps are retained explicitly, with actual original face/edge witnesses.']}
    witnesses = {}
    levels = [.605, .6416666666666666, .6783333333333333, .715]
    out.mkdir(parents=True)
    for label, filename in [('compact', 'retopology-prototype.npz'), ('dense', 'cleaned-donor.npz')]:
        path = PREP / filename; pin = sha(path); source = dict(np.load(path))
        vertices, faces = source['vertices'], source['faces']
        record = {'path': str(path.relative_to(ROOT)), 'sha256': pin,
                  'keys': list(source), 'topology': topology(vertices, faces), 'sections': []}
        report['sources'][label] = record
        measured = {}
        for y in levels:
            measured[y] = section.all_contours(vertices, faces, np.array([0, y, 0]), np.array([0, 1., 0]))
        anchor_centers = []
        for y in (levels[0], levels[-1]):
            _, inner = registration.cavity(measured[y])
            anchor_centers.append(inner['centroid'][[0, 2]])
        for y in levels:
            contours = measured[y]
            fraction = (y-levels[0])/(levels[-1]-levels[0])
            proposal = anchor_centers[0]*(1-fraction)+anchor_centers[1]*fraction
            try:
                outer, inner = registration.cavity(contours)
                center = inner['centroid'][[0, 2]]; kind = 'ACTUAL_NESTED_CAVITY_CENTROID'
            except AssertionError:
                center = proposal; kind = 'INTERPOLATED_MEASURED_NEIGHBOUR_CAVITY_PROPOSAL'
            rows = material_rays(contours, center)
            entry = {'sourceY': y, 'contourCount': len(contours), 'center': center.tolist(),
                     'centerAuthority': kind,
                     'contourMaterialOccupancyAtCenter': [bool(registration.inside([center], c['polygon'][:, [0, 2]])[0]) for c in contours],
                     'materialParityAtCenter': sum(bool(registration.inside([center], c['polygon'][:, [0, 2]])[0]) for c in contours)%2,
                     'gapAnglesRadians': [r['angleRadians'] for r in rows if r['hitCount'] == 0],
                     'completeAngularMaterialVisibility': angular_material_coverage(contours, center),
                     'rayCount': len(rows), 'rayIntersectionWitnesses': rows, 'contours': []}
            record['sections'].append(entry)
            for index, contour in enumerate(contours):
                key = label+'-'+str(y)+'-'+str(index)
                witnesses[key] = contour['polygon']
                face_ids = np.array(contour['sourceHandTriangles'], dtype=np.int64)
                row = {'areaM2': contour['areaM2'], 'centroid': contour['centroid'].tolist(),
                       'pointCount': len(contour['polygon']), 'actualSourceFaceRows': face_ids.tolist(),
                       'actualSourceEdges': contour['sourceEdges'],
                       'actualSourceEdgeFractions': contour['sourceEdgeFractions'], 'polygonWitnessKey': key}
                if 'originalCornerUV' in source:
                    uv = source['originalCornerUV'][face_ids]
                    row['sourceCornerUVBounds'] = [uv.min((0, 1)).tolist(), uv.max((0, 1)).tolist()]
                entry['contours'].append(row)
        assert sha(path) == pin
    np.savez_compressed(out / 'actual-section-polygons.npz', **witnesses)
    report['witnessSHA256'] = sha(out / 'actual-section-polygons.npz')
    (out / 'source-material-sections.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({label: [{k: row[k] for k in ('sourceY', 'contourCount', 'centerAuthority', 'materialParityAtCenter')} |
        {'gapRays': len(row['gapAnglesRadians'])} for row in data['sections']] for label, data in report['sources'].items()}))


if __name__ == '__main__':
    main()
