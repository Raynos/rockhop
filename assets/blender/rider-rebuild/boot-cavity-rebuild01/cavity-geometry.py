"""Exact source ownership and coherent cavity geometry for selected boots."""
import numpy as np


def cut_only_inner(vertices, faces, inner_mask, height):
    """Clip only certified inner triangles; never cut source exterior details."""
    vertices = np.asarray(vertices, dtype=np.float64)
    points = list(vertices)
    original_ids = list(range(len(points)))
    edge_ids = [[-1, -1] for _ in points]
    edge_t = [0. for _ in points]
    intersections = {}
    rows, owners = [], []
    for owner, triangle in enumerate(faces):
        if not inner_mask[owner]:
            rows.append(list(triangle)); owners.append(owner)
            continue
        polygon = []
        for a, b in zip(triangle, np.roll(triangle, -1)):
            da, db = vertices[a, 1] - height, vertices[b, 1] - height
            if da >= 0:
                polygon.append(int(a))
            if da * db < 0:
                key = tuple(sorted((int(a), int(b))))
                if key not in intersections:
                    i, j = key
                    t = (height - vertices[i, 1]) / (vertices[j, 1] - vertices[i, 1])
                    point = vertices[i] + t * (vertices[j] - vertices[i])
                    point[1] = height
                    intersections[key] = len(points)
                    points.append(point); original_ids.append(-1)
                    edge_ids.append([i, j]); edge_t.append(t)
                polygon.append(intersections[key])
        for i in range(1, len(polygon) - 1):
            rows.append([polygon[0], polygon[i], polygon[i + 1]])
            owners.append(owner)
    rows = np.asarray(rows, dtype=np.int32)
    used = np.unique(rows)
    remap = np.full(len(points), -1, dtype=np.int32)
    remap[used] = np.arange(len(used))
    return dict(vertices=np.asarray(points)[used], faces=remap[rows],
                sourceVertexIDs=np.asarray(original_ids)[used],
                sourceEdgeVertexIDs=np.asarray(edge_ids)[used],
                sourceEdgeInterpolationT=np.asarray(edge_t)[used],
                sourceFaceIDs=np.asarray(owners, dtype=np.int32))


def topology(vertices, faces):
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    unique, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0,
                                        return_inverse=True, return_counts=True)
    signs = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    sums = np.bincount(inverse, weights=signs)
    return dict(vertices=len(vertices), triangles=len(faces),
                boundaryEdges=int((counts == 1).sum()),
                nonmanifoldEdges=int((counts > 2).sum()),
                sameDirectionInteriorEdges=int((sums[counts == 2] != 0).sum()))


def one_boundary(faces):
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    _, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0,
                                   return_inverse=True, return_counts=True)
    rows = edges[counts[inverse] == 1]
    successor = dict(rows.tolist())
    assert len(successor) == len(rows) >= 3
    assert len(set(successor.values())) == len(rows)
    loop, cursor = [], int(rows[0, 0])
    while cursor not in loop:
        loop.append(cursor); cursor = successor[cursor]
    assert cursor == loop[0] and len(loop) == len(rows), 'Not exactly one source cavity cycle'
    return np.asarray(loop, dtype=np.int32)


def ray_radius(points, center, angles):
    """Actual closed planar contour ray intersections; no fitted ellipse proxy."""
    polygon = points[:, :2] - center[:2]
    a, edge = polygon, np.roll(polygon, -1, axis=0) - polygon
    values = []
    for angle in angles:
        ray = np.array([np.cos(angle), np.sin(angle)])
        denominator = ray[0] * edge[:, 1] - ray[1] * edge[:, 0]
        radius = np.divide(a[:, 0] * edge[:, 1] - a[:, 1] * edge[:, 0],
                           denominator, out=np.full(len(a), np.nan), where=abs(denominator) > 1e-14)
        t = np.divide(a[:, 0] * ray[1] - a[:, 1] * ray[0], denominator,
                      out=np.full(len(a), np.nan), where=abs(denominator) > 1e-14)
        good = (radius > 0) & (t >= -1e-9) & (t <= 1 + 1e-9)
        assert good.any(), 'Actual cuff is not star-shaped from declared center'
        # Coincident shared-edge hits are one contour point, not a second branch.
        hits = np.unique(np.round(radius[good], 10))
        assert len(hits) == 1, 'Multiple cuff ray branches; unsupported anatomy'
        values.append(float(hits[0]))
    return np.asarray(values)


def solve_displacement(a, b, weights, penalty, goal, count):
    rhs = penalty[:, None] * goal
    degree = penalty + np.bincount(np.r_[a, b], np.r_[weights, weights], minlength=count)
    def apply(x):
        diff = (x[a] - x[b]) * weights[:, None]
        value = penalty[:, None] * x
        for axis in range(3):
            value[:, axis] += np.bincount(a, diff[:, axis], minlength=count)
            value[:, axis] -= np.bincount(b, diff[:, axis], minlength=count)
        return value
    x = np.zeros_like(goal)
    residual = rhs.copy(); z = residual / degree[:, None]; direction = z.copy()
    rz = float((residual * z).sum())
    for _ in range(180):
        product = apply(direction)
        alpha = rz / max(float((direction * product).sum()), 1e-30)
        x += alpha * direction; residual -= alpha * product
        if np.linalg.norm(residual) < 1e-8:
            break
        z = residual / degree[:, None]
        updated = float((residual * z).sum())
        direction = z + updated / max(rz, 1e-30) * direction; rz = updated
    return x, float(np.linalg.norm(residual))


def orientation_path(before, after, faces):
    """Reject any intermediate zero/reversed reference-projected triangle area."""
    e1 = before[faces[:, 1]] - before[faces[:, 0]]
    e2 = before[faces[:, 2]] - before[faces[:, 0]]
    delta = after - before
    d1 = delta[faces[:, 1]] - delta[faces[:, 0]]
    d2 = delta[faces[:, 2]] - delta[faces[:, 0]]
    normal = np.cross(e1, e2)
    c = (normal * normal).sum(1)
    a = (np.cross(d1, d2) * normal).sum(1)
    b = ((np.cross(d1, e2) + np.cross(e1, d2)) * normal).sum(1)
    minimum = np.minimum(c, a + b + c)
    t = np.divide(-b, 2 * a, out=np.zeros_like(a), where=a > 0)
    mask = (a > 0) & (t > 0) & (t < 1)
    minimum[mask] = np.minimum(minimum[mask], (a * t * t + b * t + c)[mask])
    return bool((minimum > 1e-26).all())


def annulus(outer, outer_faces, inner, inner_faces):
    """Join actual two planar cuff cycles with preserved directed winding."""
    ol, il = one_boundary(outer_faces), one_boundary(inner_faces)
    center = inner[il].mean(0)
    def ordered(points, loop):
        angles = np.arctan2(points[loop, 1] - center[1], points[loop, 0] - center[0])
        turns = (np.roll(angles, -1) - angles + np.pi) % (2 * np.pi) - np.pi
        assert (turns > 0).all() or (turns < 0).all(), 'Cuff correspondence is not radial'
        sign = float(np.sign(turns.sum()))
        angles = (sign * angles) % (2 * np.pi)
        start = int(np.argmin(angles))
        loop, angles = np.roll(loop, -start), np.roll(angles, -start)
        assert (np.diff(angles) > 0).all()
        return loop, np.r_[angles, angles[0] + 2 * np.pi], sign
    ol, oa, direction = ordered(outer, ol)
    il, ia, inner_direction = ordered(inner, il)
    assert direction == inner_direction
    offset = len(outer); bridge = []; i = j = 0
    while i < len(ol) or j < len(il):
        a, b = int(ol[i % len(ol)]), int(il[j % len(il)]) + offset
        if j == len(il) or (i < len(ol) and oa[i + 1] <= ia[j + 1]):
            bridge.append([int(ol[(i + 1) % len(ol)]), a, b]); i += 1
        else:
            bridge.append([a, b, int(il[(j + 1) % len(il)]) + offset]); j += 1
    return np.asarray(bridge, dtype=np.int32)
