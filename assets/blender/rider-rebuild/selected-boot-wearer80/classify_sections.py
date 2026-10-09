"""Scalar read-only measurements of the actual frozen 3D mesh-plane sections."""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'harness/out/rider-rebuild/selected-boot-wearer80/inspect02'
PINS = {
    'inspection.json': '2e3500f0d12f15001db6bcdb9fbf680fe3f1528c932a6c57d5a4fc1c11256bf8',
    'L-sections.json': '99909e28cbf135a8cd4c6851b7bb716f4f3a20ff71caeebc113e2132a5331a63',
    'R-sections.json': '97fd5bc480ecf505ed36c0ee854a7a27a22fc29058ebdb7ad18d08b4edc56c55',
}


def read(name):
    raw = (BASE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[name]
    return json.loads(raw)


def contours(segments, axes):
    # Section endpoints from adjacent triangles differ only by floating arithmetic.
    # 1e-10 m endpoint keys reconstruct connectivity; they do not alter coordinates.
    nodes, adjacency, edges = {}, {}, []
    for segment in segments:
        ids = []
        for p in segment:
            q = tuple(p[i] for i in axes)
            key = tuple(round(x, 10) for x in q)
            nodes.setdefault(key, q)
            adjacency.setdefault(key, [])
            ids.append(key)
        assert ids[0] != ids[1]
        edge = len(edges)
        edges.append(ids)
        for key in ids:
            adjacency[key].append(edge)
    assert all(len(v) == 2 for v in adjacency.values()), 'Section is not closed degree-two contours'
    remaining, result = set(range(len(edges))), []
    while remaining:
        edge = min(remaining)
        start, cursor = edges[edge]
        ring = [nodes[start]]
        remaining.remove(edge)
        while cursor != start:
            ring.append(nodes[cursor])
            choices = [i for i in adjacency[cursor] if i in remaining]
            assert len(choices) == 1
            edge = choices[0]
            remaining.remove(edge)
            cursor = next(k for k in edges[edge] if k != cursor)
        result.append(ring)
    return result


def area(ring):
    return .5*sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1]))


def inside(q, ring):
    crossings = 0
    for a, b in zip(ring, ring[1:]+ring[:1]):
        if (a[1] > q[1]) != (b[1] > q[1]):
            x = a[0]+(q[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            crossings += x > q[0]
    return crossings % 2 == 1


def distance(q, ring):
    best = math.inf
    for a, b in zip(ring, ring[1:]+ring[:1]):
        d = [b[i]-a[i] for i in range(2)]
        t = max(0., min(1., sum((q[i]-a[i])*d[i] for i in range(2))/sum(v*v for v in d)))
        best = min(best, math.hypot(*(q[i]-a[i]-t*d[i] for i in range(2))))
    return best


def vertical_hits(segments, medial):
    hits = []
    for a, b in segments:
        if (a[1] > medial) != (b[1] > medial):
            hits.append(a[2]+(medial-a[1])*(b[2]-a[2])/(b[1]-a[1]))
    return sorted(hits)


def main():
    assert len(sys.argv) == 2
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-boot-wearer80') and not out.exists()
    out.mkdir(parents=True)
    inspection = read('inspection.json')
    report = {'acceptedArt': False, 'status': 'ACTUAL_SECTIONS_LOCAL_CLASSIFICATION_UNACCEPTED',
              'inputPins': PINS, 'sides': {}, 'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for side in ('L', 'R'):
        sections = read(side+'-sections.json')
        row = report['sides'][side] = {'outerOutline': [], 'heelFootbed': []}
        for section in sections:
            axis, value = section['axis'], section['valueM']
            if axis == 2 or (axis == 0 and value in (.150, .195)) or (axis == 1 and value == .045):
                axes = [i for i in range(3) if i != axis]
                rings = contours(section['boot'], axes)
                outer = max(rings, key=lambda r: abs(area(r)))
                # At the medial sagittal section, classify the forefoot only.
                points = {tuple(p) for segment in section['body'] for p in segment if axis != 1 or p[0] >= .12}
                failed = []
                for p in points:
                    q = tuple(p[i] for i in axes)
                    if not inside(q, outer):
                        failed.append({'localM': p, 'distanceToOuterOutlineM': distance(q, outer)})
                row['outerOutline'].append({'axis': axis, 'valueM': value, 'sourceContours': len(rings),
                    'contourAreasM2': sorted(abs(area(r)) for r in rings), 'bodySectionSamples': len(points),
                    'outsideLargestSourceContour': len(failed), 'failures': sorted(failed, key=lambda p: p['localM'])})
            if axis == 0 and value in (-.03, .015):
                for medial in (-.02, -.01, 0.):
                    boot, body = vertical_hits(section['boot'], medial), vertical_hits(section['body'], medial)
                    assert len(boot) >= 2 and body
                    row['heelFootbed'].append({'forwardM': value, 'medialM': medial,
                        'sourceVerticalHitsM': boot, 'bodyVerticalHitsM': body,
                        'plantarToOuterBottomM': body[0]-boot[0],
                        'hiddenFootbedAbovePlantarM': boot[1]-body[0]})
        outside = inspection['sides'][side]['outsideSamples']
        row['priorParityOutsideByHeight'] = {name: sum(low <= p['localM'][2] < high for p in outside)
            for name, low, high in [('below40mm', -math.inf, .04), ('40to80mm', .04, .08),
                                    ('80to107mm', .08, .107), ('above107mm', .107, math.inf)]}
    report['limits'] = ('Saved exact 3D plane sections only. Largest-contour classification distinguishes inner loops '
        'from the external section boundary; it is not exhaustive 3D visibility/contact or a whole-foot fit pass. '
        'Footbed probes are exact named section-line intersections. No native/body/source/field edits, optimizer, bake or art acceptance.')
    (out/'classification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(out)}))


if __name__ == '__main__':
    main()
