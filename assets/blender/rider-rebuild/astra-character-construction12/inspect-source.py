"""One bounded original-source contour/component diagnosis; no scene/model edits."""
import hashlib
import json
import struct
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(row):
    p = ROOT/row['path']
    assert sha(p) == row['sha256'], row['path']
    return p


def read_source(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    primitive = doc['meshes'][0]['primitives'][0]
    def accessor(index, width):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
        item = np.dtype(dtype).itemsize
        return np.ndarray((a['count'], width), dtype=dtype, buffer=raw,
            offset=28+size+view.get('byteOffset', 0)+a.get('byteOffset', 0),
            strides=(view.get('byteStride', width*item), item)).copy()
    vertices = accessor(primitive['attributes']['POSITION'], 3).astype(float)[:, [0, 2, 1]]
    vertices[:, 1] *= -1
    return vertices, accessor(primitive['indices'], 1).reshape(-1, 3).astype(np.int32)


def inside(point, polygon):
    a, b = polygon, np.roll(polygon, -1, axis=0)
    y = b[:, 1]-a[:, 1]
    x = a[:, 0]+(point[1]-a[:, 1])*(b[:, 0]-a[:, 0])/np.where(y != 0, y, 1)
    return bool(np.sum(((a[:, 1] > point[1]) != (b[:, 1] > point[1])) & (point[0] < x)) % 2)


def section(xyz, faces, scalar, station, head, u, v, axis):
    d = scalar-station
    fd = d[faces]
    ids = np.flatnonzero((fd.min(axis=1) <= 0) & (fd.max(axis=1) >= 0))
    segments, ancestry, orientation = [], [], []
    for i in ids:
        f = faces[i]; hits = []
        for a, b in zip(f, np.roll(f, -1)):
            if d[a] == 0:
                hits.append(xyz[a])
            if d[a]*d[b] < 0:
                t = d[a]/(d[a]-d[b]); hits.append(xyz[a]+t*(xyz[b]-xyz[a]))
        hits = np.unique(np.asarray(hits), axis=0) if hits else []
        if len(hits) == 2 and np.linalg.norm(hits[1]-hits[0]) > 1e-9:
            normal = np.cross(xyz[f[1]]-xyz[f[0]], xyz[f[2]]-xyz[f[0]])
            direction = np.cross(normal, axis)
            if float(np.sum((hits[1]-hits[0])*direction)) < 0:
                hits = hits[::-1]
            planar = np.column_stack((np.sum((hits-head)*u, axis=1), np.sum((hits-head)*v, axis=1)))
            segments.append(planar); ancestry.append(int(i))
        elif len(hits) > 2:
            raise AssertionError(('Coplanar triangle', int(i), station))
    endpoints, remap = np.unique(np.round(np.asarray(segments).reshape(-1, 2), 8), axis=0, return_inverse=True)
    edges = remap.reshape(-1, 2)
    graph = defaultdict(list); byedge = defaultdict(list)
    for index, (a, b) in enumerate(edges):
        if a != b:
            key = tuple(sorted((int(a), int(b))))
            byedge[key].append(index)
    for (a, b) in byedge:
        graph[a].append(b); graph[b].append(a)
    bad = {int(i): len(row) for i, row in graph.items() if len(row) != 2}
    if bad:
        return {'stationM': station, 'closed': False, 'badDegrees': bad, 'exactPlaneVertexCount': int(np.sum(d == 0))}, []
    unseen, loops, arrays = set(graph), [], []
    while unseen:
        start = min(unseen); chain = [start]; old, at = None, start
        while True:
            nxt = next(n for n in graph[at] if n != old)
            if nxt == start:
                break
            assert nxt not in chain
            chain.append(nxt); old, at = at, nxt
        unseen.difference_update(chain)
        members = [j for a, b in zip(chain, chain[1:]+chain[:1]) for j in byedge[tuple(sorted((a, b)))]]
        oriented = np.asarray(segments)[members]
        signed_area = float(np.sum(oriented[:, 0, 0]*oriented[:, 1, 1]-oriented[:, 1, 0]*oriented[:, 0, 1])/2)
        p = endpoints[chain]
        cross = p[:, 0]*np.roll(p[:, 1], -1)-p[:, 1]*np.roll(p[:, 0], -1)
        centroid = np.sum((p+np.roll(p, -1, axis=0))*cross[:, None], axis=0)/(3*cross.sum())
        rows = np.array(sorted(set(np.asarray(ancestry)[members])), dtype=np.int32)
        loops.append({'vertices': len(p), 'signedAreaM2FromSourceWinding': signed_area,
                      'unsignedAreaM2': float(abs(cross.sum())/2), 'centroidUV': centroid.tolist(),
                      'centroidInsideSelf': inside(centroid, p), 'sourceFaceCount': len(rows),
                      'firstSourceFaces': rows[:12].tolist()})
        arrays.append((p, rows))
    for i, row in enumerate(loops):
        row['allVerticesInsideLoops'] = [j for j, (polygon, _) in enumerate(arrays)
                                      if j != i and all(inside(point, polygon) for point in arrays[i][0])]
    return {'stationM': station, 'closed': True, 'loopCount': len(loops), 'loops': loops,
            'exactPlaneVertexCount': int(np.sum(d == 0))}, arrays


def components(faces, weld, scalar, station, loop_faces):
    # Restrict adjacency to the geometrical portion on the distal side of the
    # plane. A shared edge connects clipped faces only when it has positive
    # length beyond the plane. This is the cut topology, not nearest-point fitting.
    distinct = np.all(np.diff(np.sort(weld[faces], axis=1), axis=1) != 0, axis=1)
    eligible = np.flatnonzero((np.max(scalar[faces], axis=1) > station) & distinct)
    excluded = np.flatnonzero((np.max(scalar[faces], axis=1) > station) & ~distinct)
    edges = defaultdict(list)
    for row in eligible:
        f = faces[row]
        for a, b in zip(f, np.roll(f, -1)):
            if max(scalar[a], scalar[b]) > station and weld[a] != weld[b]:
                edges[tuple(sorted((int(weld[a]), int(weld[b]))))].append(int(row))
    adjacency = defaultdict(list)
    nonmanifold = []
    for rows in edges.values():
        if len(rows) > 2:
            nonmanifold.append(rows)
        for a in rows:
            adjacency[a].extend(b for b in rows if b != a)
    result, memberships = [], []
    eligible_set = set(eligible.tolist())
    for seeds in loop_faces:
        reached = set(int(i) for i in seeds if i in eligible_set)
        queue = deque(reached)
        while queue:
            for other in adjacency[queue.popleft()]:
                if other not in reached:
                    reached.add(other); queue.append(other)
        rows = np.array(sorted(reached), dtype=np.int32)
        points = np.unique(faces[rows])
        result.append({'faces': len(rows), 'sourceVertices': len(points),
                       'sourceAxialRangeM': [float(scalar[points].min()), float(scalar[points].max())],
                       'containsOtherLoopSourceFaces': [bool(set(seed.tolist()) & reached) for seed in loop_faces],
                       'excludedPositionDegenerateSourceFaces': excluded.tolist(),
                       'nonmanifoldCutEdges': len(nonmanifold), 'firstNonmanifoldEdgeSourceFaces': nonmanifold[:4]})
        memberships.append(rows)
    return result, memberships


def main():
    args = sys.argv[1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-character-construction12') and not out.exists()
    cfg = json.loads((HERE/'input.json').read_text())
    prior = json.loads(pin(cfg['priorInputs']).read_text())
    source_path = pin(prior['originalHoodie']); controls_path = pin(prior['hoodieSourceFrames'])
    source, faces = read_source(source_path)
    controls = json.loads(controls_path.read_text())
    xyz = source*np.asarray(controls['sourceDisplayAffine']['scale'])+np.asarray(controls['sourceDisplayAffine']['translation'])
    _, weld = np.unique(source, axis=0, return_inverse=True)
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'source': prior['originalHoodie'],
              'frames': prior['hoodieSourceFrames'], 'recipeSHA256': sha(Path(__file__)),
              'method': 'Full original source plane contours; exact source-position weld for distal face adjacency; contour nesting and original triangle winding. No mesh/model edits.',
              'sides': {}}
    for side in ('L', 'R'):
        bone = next(b for b in controls['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
        head, tail = np.asarray(bone['sourceHead']), np.asarray(bone['sourceTail'])
        axis = (tail-head)/np.linalg.norm(tail-head)
        u = np.array([0., 0., 1.])-axis[2]*axis; u /= np.linalg.norm(u); v = np.cross(axis, u)
        delta = xyz-head; scalar = np.sum(delta*axis, axis=1)
        radial = np.linalg.norm(delta-scalar[:, None]*axis, axis=1)
        own = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
        selected = own & (scalar > .4*np.linalg.norm(tail-head)) & (radial < .15)
        start = float(scalar[selected].min()); end = float(scalar[selected].max())-.02
        stations = np.linspace(start, end-1e-5, 9)
        rows, payload = [], {}
        for index, station in enumerate(stations):
            row, arrays = section(xyz, faces, scalar, float(station), head, u, v, axis)
            rows.append(row)
            for j, (polygon, source_faces) in enumerate(arrays):
                payload[f'section{index}_loop{j}_UV'] = polygon
                payload[f'section{index}_loop{j}_sourceFaces'] = source_faces
            if index == 0 and row['closed']:
                parts, members = components(faces, weld, scalar, float(station), [a[1] for a in arrays])
                row['distalComponents'] = parts
                for j, membership in enumerate(members):
                    payload[f'section0_loop{j}_distalSourceFaces'] = membership
            print(side, index, json.dumps(row), flush=True)
        path = out/f'source-sleeve-{side}.npz'; np.savez_compressed(path, **payload)
        report['sides'][side] = {'sections': rows, 'arrays': {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}}
        (out/'source-topology.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(out/'source-topology.json')}), flush=True)


if __name__ == '__main__':
    main()
