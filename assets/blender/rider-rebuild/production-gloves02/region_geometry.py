"""Conventional mesh-region duplicate/inset/extrude edits, NumPy only.

Each feature is a connected frozen face patch on the actual fitted shell.
Subdivision interpolates source coordinates, normals and all shared75 fields.
No target search, surface ray, branch label or nearest fallback exists here.
"""
import heapq
import math
import numpy as np


def boundary_edges(faces):
    edges = {}
    for face in faces:
        for a, b in zip(face, np.roll(face, -1)):
            key = tuple(sorted((int(a), int(b))))
            edges.setdefault(key, []).append((int(a), int(b)))
    assert all(len(v) <= 2 for v in edges.values()), 'Nonmanifold selected region'
    return [values[0] for values in edges.values() if len(values) == 1]


def duplicate_inset_extrude(scaffold, normals, fields, full_fields, source_faces, spec):
    selected = source_faces[np.array(spec['faceIds'], dtype=np.int32)]
    ids = sorted(set(map(int, selected.ravel())))
    lookup = {value: i for i, value in enumerate(ids)}
    vertices = [p.copy() for p in scaffold[ids]]
    ns = [n.copy() for n in normals[ids]]
    four = [w.copy() for w in fields[ids]]
    full = [w.copy() for w in full_fields[ids]]
    faces = [[lookup[int(v)] for v in face] for face in selected]
    # Edit subdivision creates useful sculpting loops within the selected
    # anatomical surface, retaining barycentric skin interpolation exactly.
    for _ in range(spec['subdivision']):
        midpoints = {}
        def midpoint(a, b):
            key = tuple(sorted((a, b)))
            if key not in midpoints:
                midpoints[key] = len(vertices)
                vertices.append((vertices[a] + vertices[b]) / 2)
                normal = ns[a] + ns[b]; ns.append(normal / np.linalg.norm(normal))
                four.append((four[a] + four[b]) / 2)
                full.append((full[a] + full[b]) / 2)
            return midpoints[key]
        refined = []
        for a, b, c in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            refined.extend(((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)))
        faces = refined
    vertices, ns, four, full, faces = map(np.asarray, (vertices, ns, four, full, faces))
    edge = boundary_edges(faces)
    boundary = set(v for e in edge for v in e)
    assert boundary, (spec['name'], 'closed region cannot inset')
    adjacency = [set() for _ in vertices]
    for face in faces:
        for a, b in zip(face, np.roll(face, -1)):
            adjacency[a].add(b); adjacency[b].add(a)
    # Geodesic distance is only a sculpt brush falloff across this already
    # authored patch. It neither fits geometry nor selects anatomical support.
    distance = np.full(len(vertices), np.inf)
    queue = []
    for v in boundary:
        distance[v] = 0; heapq.heappush(queue, (0., v))
    while queue:
        value, a = heapq.heappop(queue)
        if value != distance[a]: continue
        for b in adjacency[a]:
            trial = value + np.linalg.norm(vertices[b] - vertices[a])
            if trial < distance[b]:
                distance[b] = trial; heapq.heappush(queue, (trial, b))
    assert np.isfinite(distance).all()
    inset = vertices.copy()
    for v in boundary:
        inward = [i for i in adjacency[v] if i not in boundary]
        # Two subdivisions guarantee interior neighbors at almost every border.
        # Corner rows without an interior neighbor stay in place intentionally.
        if inward:
            direction = vertices[inward].mean(0) - vertices[v]
            direction -= ns[v] * np.dot(direction, ns[v])
            length = np.linalg.norm(direction)
            if length:
                inset[v] += direction / length * min(spec['insetMeters'], length * .35)
    normalized = np.clip(distance / max(distance.max(), 1e-8), 0, 1)
    fullness = np.sin(normalized * math.pi / 2) ** .7
    lift = .00042 + spec['heightMeters'] * fullness
    if spec['ribCount']:
        axis = np.asarray(spec['ribAxisWorld'])
        axial = vertices @ axis
        phase = (axial - axial.min()) / max(np.ptp(axial), 1e-8)
        # Three raised transverse rolls with flexible valleys, sculpted on the
        # actual duplicated joint region rather than stamped over rays.
        wave = np.sin(phase * math.pi * spec['ribCount']) ** 2
        lift = .0007 + spec['heightMeters'] * wave * np.sin(normalized * math.pi / 2)
    top = inset + ns * lift[:, None]
    # Sidewall starts on the actual scaffold edge and ends at the inset lip.
    # These are garment overlays, not a disconnected floating rectangle.
    result_v = top.tolist(); result_f = faces.tolist()
    result_w = four.tolist(); result_full = full.tolist()
    anchors = {}
    for v in sorted(boundary):
        anchors[v] = len(result_v)
        result_v.append(vertices[v].tolist())
        result_w.append(four[v].tolist()); result_full.append(full[v].tolist())
    for a, b in edge:
        result_f.append([anchors[a], anchors[b], b, a])
    seams = [(top[a], top[b], four[a], four[b], full[a], full[b]) for a, b in edge]
    return result_v, result_f, result_w, result_full, seams, {
        'sourceFaceIds': spec['faceIds'], 'connectedSourceFaces': len(selected),
        'subdividedTopTriangles': len(faces), 'boundaryEdges': len(edge),
        'sculptedLiftMeters': [float(lift.min()), float(lift.max())],
        'insetMeters': spec['insetMeters'], 'ribCount': spec['ribCount']}


def seam_edge_geometry(segments, radius, dorsal):
    """Shared tube loops follow exact selected boundary vertices and skin fields."""
    points, fields, full_fields, links = {}, {}, {}, {}
    for start, end, start_w, end_w, start_full, end_full in segments:
        a, b = tuple(start), tuple(end)
        points[a], points[b] = start, end
        fields[a], fields[b] = start_w, end_w
        full_fields[a], full_fields[b] = start_full, end_full
        links.setdefault(a, set()).add(b); links.setdefault(b, set()).add(a)
    assert all(len(neighbors) == 2 for neighbors in links.values()), 'Selected stitch boundary must be simple closed loops'
    unused = set(links)
    vertices, faces, four, full = [], [], [], []
    while unused:
        first = min(unused); loop = [first]; unused.remove(first)
        previous = first; current = min(links[first])
        while current != first:
            assert current in unused, 'Stitch loop crosses another selected boundary'
            loop.append(current); unused.remove(current)
            following = next(iter(links[current] - {previous}))
            previous, current = current, following
        assert len(loop) >= 3
        offset = len(vertices)
        for j, key in enumerate(loop):
            previous, following = points[loop[j - 1]], points[loop[(j + 1) % len(loop)]]
            tangent = following - previous; tangent /= np.linalg.norm(tangent)
            radial = dorsal - tangent * np.dot(tangent, dorsal)
            if np.linalg.norm(radial) < .1:
                radial = np.cross(tangent, np.array([1., .3, .1]))
            radial /= np.linalg.norm(radial); second = np.cross(tangent, radial)
            for i in range(6):
                angle = i * math.tau / 6
                vertices.append((points[key] + radius * (radial * math.cos(angle) + second * math.sin(angle))).tolist())
                four.append(fields[key].tolist()); full.append(full_fields[key].tolist())
        for j in range(len(loop)):
            for i in range(6):
                a = offset + j * 6 + i; b = offset + j * 6 + (i + 1) % 6
                c = offset + ((j + 1) % len(loop)) * 6 + (i + 1) % 6
                d = offset + ((j + 1) % len(loop)) * 6 + i
                faces.append([a, b, c, d])
    return vertices, faces, four, full
