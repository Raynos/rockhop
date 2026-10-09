"""Read-only source-triangle diagnosis of construction01's rejected z90 cut.

Parent original guard only. No Blender, mesh edit, fit, or construction retry.
Analytical clipping preserves source IDs and separates each failed predicate.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'harness/out/rider-rebuild/selected-boot-wearer80'
PINS = {
    'source': ('harness/out/rider-rebuild/selected-boot-family75/cpu01/source.json',
               '22236d6c2f4a874a57c7f945a4e1b186d6d400dab04c006f3658f96afc8e7ed1'),
    'inspection': ('harness/out/rider-rebuild/selected-boot-wearer80/inspect02/inspection.json',
                   '2e3500f0d12f15001db6bcdb9fbf680fe3f1528c932a6c57d5a4fc1c11256bf8'),
    'failure': ('harness/out/rider-rebuild/selected-boot-wearer80/native01/construction.json',
                '238c5cbf3719c37af2a716a81ec349926186162151eafc25a36161bf13bf26c2'),
}
PLANE = .090


def read_pin(row):
    raw = (ROOT/row[0]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row[1], row[0]
    return json.loads(raw)


def ray_hits(tri):
    """Exact vertical line/triangle barycentrics at the original heel seed."""
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    e, f = b-a, c-a
    q = np.array([-.030, -.010])-a[:, :2]
    det = e[:, 0]*f[:, 1]-e[:, 1]*f[:, 0]
    good = np.abs(det) > 1e-18
    u = np.divide(q[:, 0]*f[:, 1]-q[:, 1]*f[:, 0], det,
                  out=np.full(len(tri), np.inf), where=good)
    v = np.divide(e[:, 0]*q[:, 1]-e[:, 1]*q[:, 0], det,
                  out=np.full(len(tri), np.inf), where=good)
    ids = np.flatnonzero(good & (u >= -1e-10) & (v >= -1e-10) & (u+v <= 1+1e-10))
    z = a[ids, 2]+u[ids]*e[ids, 2]+v[ids]*f[ids, 2]
    return sorted([(int(i), float(h)) for i, h in zip(ids, z) if h < .35], key=lambda x: -x[1])


def cut_rings(p, faces, chosen):
    """Plane intersections keyed by ORIGINAL shared edges, not spatial proximity."""
    nodes, links, owner = {}, {}, {}
    for i in chosen:
        f = faces[i]
        if not p[f, 2].min() < PLANE < p[f, 2].max():
            continue
        keys = []
        for j, k in ((0, 1), (1, 2), (2, 0)):
            a, b = p[f[j]], p[f[k]]
            if (a[2]-PLANE)*(b[2]-PLANE) < 0:
                key = tuple(sorted((int(f[j]), int(f[k]))))
                nodes[key] = a+(PLANE-a[2])/(b[2]-a[2])*(b-a)
                keys.append(key)
        assert len(keys) == 2
        a, b = keys
        links.setdefault(a, []).append(b)
        links.setdefault(b, []).append(a)
        owner[frozenset(keys)] = int(i)
    assert all(len(v) == 2 for v in links.values()), 'Cut contains a non-degree-two junction'
    remaining, result = set(nodes), []
    while remaining:
        start = min(remaining)
        ring, parents, prior, cursor = [], [], None, start
        while cursor in remaining:
            remaining.remove(cursor)
            ring.append(nodes[cursor])
            nxt = next(k for k in links[cursor] if k != prior)
            parents.append(owner[frozenset((cursor, nxt))])
            prior, cursor = cursor, nxt
        assert cursor == start
        q = np.array(ring)
        area = abs(float(np.sum(q[:, 0]*np.roll(q[:, 1], -1)-q[:, 1]*np.roll(q[:, 0], -1))*.5))
        result.append({'areaM2': area, 'boundsLocalM': [q.min(0).tolist(), q.max(0).tolist()],
                       'sourceTriangleIds': parents, 'localPointsM': q.tolist()})
    return sorted(result, key=lambda r: r['areaM2'])


def diagnose(p, faces):
    tri = p[faces]
    hits = ray_hits(tri)
    seed, hit_z = hits[0]
    assert .006 < hit_z < .025
    near_plane = np.flatnonzero(np.abs(p[:, 2]-PLANE) <= 1e-8)
    # Exact analytical clipping is unambiguous only away from the BMesh tolerance.
    assert not len(near_plane), 'Record and review near-plane vertices before comparing to BMesh'
    edge = faces[:, ((0, 1), (1, 2), (2, 0))].reshape(-1, 2)
    edge.sort(axis=1)
    key = edge[:, 0].astype(np.int64)*len(p)+edge[:, 1]
    order = np.argsort(key)
    paired = order.reshape(-1, 2)
    assert np.array_equal(key[paired[:, 0]], key[paired[:, 1]])
    assert np.all(key[paired[1:, 0]] != key[paired[:-1, 0]]), 'Source is not closed two-manifold'
    adjacent = np.full(len(edge), -1, np.int32)
    below = p[edge[paired[:, 0]], 2].min(1) < PLANE
    pair = paired[below]
    adjacent[pair[:, 0]] = pair[:, 1]//3
    adjacent[pair[:, 1]] = pair[:, 0]//3
    adjacent = adjacent.reshape(-1, 3)
    previous = np.full(len(faces), -1, np.int32)
    depth = np.full(len(faces), -1, np.int32)
    previous[seed] = seed
    depth[seed] = 0
    pending = deque([seed])
    while pending:
        i = pending.popleft()
        for j in adjacent[i]:
            if j >= 0 and previous[j] < 0:
                previous[j] = i
                depth[j] = depth[i]+1
                pending.append(int(j))
    chosen = np.flatnonzero(previous >= 0)
    assert np.all(tri[chosen, :, 2].min(1) < PLANE)
    maximum_u = np.where(tri[:, :, 2] < PLANE, tri[:, :, 0], -np.inf).max(1)
    for j, k in ((0, 1), (1, 2), (2, 0)):
        a, b = tri[:, j], tri[:, k]
        cross = (a[:, 2]-PLANE)*(b[:, 2]-PLANE) < 0
        ids = np.flatnonzero(cross)
        u = a[ids, 0]+(PLANE-a[ids, 2])/(b[ids, 2]-a[ids, 2])*(b[ids, 0]-a[ids, 0])
        maximum_u[ids] = np.maximum(maximum_u[ids], u)
    rings = cut_rings(p, faces, chosen)
    vertices = np.unique(faces[chosen])
    cloud = [p[vertices[p[vertices, 2] < PLANE]]]
    cloud.extend(np.array(r['localPointsM']) for r in rings)
    cloud = np.concatenate(cloud)
    row = {'seedTriangleId': seed, 'heelRayHits': hits, 'selectedOriginalTriangles': len(chosen),
           'sourceTriangleCount': len(faces), 'boundsLocalM': [cloud.min(0).tolist(), cloud.max(0).tolist()],
           'cutRings': rings, 'failedPredicates': {}, 'shortestPaths': {}}
    for name, bad in [('belowMinus1mm', tri[:, :, 2].min(1) <= -.001),
                      ('beyondForward110mm', maximum_u >= .11)]:
        ids = chosen[bad[chosen]]
        row['failedPredicates'][name] = {'fails': bool(len(ids)), 'sourceTriangles': len(ids)}
        if len(ids):
            # Previous is a breadth-first tree; select the nearest offending face.
            path = [int(ids[np.argmin(depth[ids])])]
            while path[-1] != seed:
                path.append(int(previous[path[-1]]))
            path.reverse()
            row['shortestPaths'][name] = [{'sourceTriangleId': i, 'localCentroidM': tri[i].mean(0).tolist()}
                                          for i in path]
    return row, chosen


def main():
    assert len(sys.argv) == 2
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(OUT) and not out.exists()
    out.mkdir(parents=True)
    source, inspection, failure = [read_pin(PINS[k]) for k in ('source', 'inspection', 'failure')]
    assert failure['recipeSHA256'] == '8ddea96db75b58180b05aa1a06ccc27f8c457e2abe3224a7cd962b58ab2b733c'
    package = source['arrays']
    raw = (ROOT/package['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == package['sha256']
    arrays = {k: np.frombuffer(raw, dtype=v['dtype'], count=v['byteLength']//np.dtype(v['dtype']).itemsize,
                             offset=v['byteOffset']).reshape(v['shape']) for k, v in package['layout'].items()}
    report = {'status': 'READ_ONLY_REJECTED_SELECTION_DIAGNOSTIC', 'acceptedArt': False, 'pins': PINS,
              'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'sides': {}}
    for side in ('L', 'R'):
        frame = inspection['sides'][side]
        p = (arrays[side+'Positions'].astype(float)-np.array(frame['origin']))@np.array(frame['basisColumns']).T
        row, chosen = diagnose(p, arrays[side+'Triangles'])
        ids_path = out/(side+'-selected-source-triangles.npy')
        np.save(ids_path, chosen.astype('<i4'))
        row['selectedIds'] = {'path': str(ids_path.relative_to(ROOT)),
                              'sha256': hashlib.sha256(ids_path.read_bytes()).hexdigest()}
        report['sides'][side] = row
    report['limits'] = ('Source geometry and analytical plane clipping only. Not a native BMesh replay; '
        'construction01 did not save its selected faces. No deletion, field edit, fit, art, or wearable pass.')
    (out/'selection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(out)}))


if __name__ == '__main__':
    main()
