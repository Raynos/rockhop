"""Bounded float64 geometry assays; no wearable or full-surface clearance claim.

Distances enumerate ALL triangles. Winding requires an oriented, edge-closed
surface. Self intersections include touching nonadjacent faces and test overlap
beyond legitimate shared vertices/edges. Numerical predicates use caller-visible
tolerances, not exact arithmetic predicates.
"""
import numpy as np


def _mesh(vertices, faces):
    v, f = np.asarray(vertices, dtype=np.float64), np.asarray(faces, dtype=np.int64)
    if v.ndim != 2 or v.shape[1] != 3 or f.ndim != 2 or f.shape[1] != 3:
        raise ValueError('Expected Vx3 vertices and Fx3 faces')
    if not np.isfinite(v).all() or len(f) == 0 or f.min() < 0 or f.max() >= len(v):
        raise ValueError('Invalid mesh')
    return v, f


def _boundary(faces):
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    _, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0,
                                   return_inverse=True, return_counts=True)
    if np.any(counts > 2):
        raise ValueError('Nonmanifold mesh edges')
    # Every interior edge must have opposite directions.
    signs = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    sums = np.bincount(inverse, weights=signs)
    if np.any(sums[counts == 2] != 0):
        raise ValueError('Inconsistent face winding')
    return edges[counts[inverse] == 1]


def close_planar_cuff(vertices, faces, tolerance=1e-9):
    """Return V,F with a mathematical cap on one planar convex/star-shaped cuff.

    Requires the vertex-mean fan to have consistently signed areas; fails closed
    for unsupported cuff geometry. Original triangle indices remain unchanged.
    """
    v, f = _mesh(vertices, faces)
    edges = _boundary(f)
    if len(edges) < 3 or len(np.unique(edges[:, 0])) != len(edges):
        raise ValueError('Expected one simple cuff boundary')
    successor = dict(edges.tolist())
    loop, cursor = [], int(edges[0, 0])
    while cursor not in loop:
        loop.append(cursor)
        if cursor not in successor:
            raise ValueError('Broken boundary')
        cursor = successor[cursor]
    if cursor != loop[0] or len(loop) != len(edges):
        raise ValueError('Expected exactly one cuff loop')
    points = v[loop]
    center = points.mean(axis=0)
    _, _, frame = np.linalg.svd(points - center, full_matrices=False)
    if np.max(np.abs((points - center) @ frame[2])) > tolerance:
        raise ValueError('Cuff is not planar within tolerance')
    areas = np.cross(points - center, np.roll(points, -1, axis=0) - center) @ frame[2]
    if not (np.all(areas > 0) or np.all(areas < 0)):
        raise ValueError('Cuff fan not qualified')
    cap = np.column_stack([edges[:, 1], edges[:, 0], np.full(len(edges), len(v))])
    return np.vstack([v, center]), np.vstack([f, cap])


def closest_points(points, vertices, faces, chunk_size=64):
    """Exact triangle feature minima (float64), exhaustive; return distance,row,XYZ.

    Degenerate triangles are handled by their three segments. Peak temporary
    storage is O(chunk_size * triangle_count); runtime is O(P * F).
    """
    v, f = _mesh(vertices, faces)
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    if not np.isfinite(points).all() or chunk_size < 1:
        raise ValueError('Invalid points or chunk size')
    tri = v[f]
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    ab, ac = b - a, c - a
    normal = np.cross(ab, ac)
    n2 = np.sum(normal * normal, axis=1)
    safe_n2 = np.where(n2 > 0, n2, 1.)
    distances, indices, witnesses = [], [], []
    for start in range(0, len(points), chunk_size):
        p = points[start:start + chunk_size, None, :]
        best = np.full((len(p), len(f)), np.inf)
        nearest = np.zeros((len(p), len(f), 3))
        for e0, e1 in ((a, b), (b, c), (c, a)):
            edge = e1 - e0
            e2 = np.sum(edge * edge, axis=1)
            t = np.clip(np.sum((p - e0) * edge, axis=2) / np.where(e2 > 0, e2, 1), 0, 1)
            q = e0 + t[..., None] * edge
            d2 = np.sum((p - q)**2, axis=2)
            update = d2 < best
            best[update], nearest[update] = d2[update], q[update]
        delta = p - a
        q = p - (np.sum(delta * normal, axis=2) / safe_n2)[..., None] * normal
        qa = q - a
        # Barycentric numerators via cross products avoid a Gram cancellation.
        u = np.sum(np.cross(qa, ac) * normal, axis=2) / safe_n2
        w = np.sum(np.cross(ab, qa) * normal, axis=2) / safe_n2
        inside = (n2 > 0) & (u >= 0) & (w >= 0) & (u + w <= 1)
        d2 = np.sum((p - q)**2, axis=2)
        update = inside & (d2 < best)
        best[update], nearest[update] = d2[update], q[update]
        index = np.argmin(best, axis=1)
        rows = np.arange(len(p))
        distances.append(np.sqrt(best[rows, index]))
        indices.append(index)
        witnesses.append(nearest[rows, index])
    if not distances:
        return np.empty(0), np.empty(0, dtype=int), np.empty((0, 3))
    return np.concatenate(distances), np.concatenate(indices), np.concatenate(witnesses)


def signed_distances(points, vertices, faces, chunk_size=64, surface_tolerance=1e-10):
    """Negative inside; positive outside. Raises on open/inconsistently wound mesh.

    Returns dict with signedDistance, windingNumber, triangleRow, closestPoint,
    closestNormal, ambiguous. Nonintegral winding away from boundary is ambiguous.
    closestNormal is the outward face normal (edge/vertex normals are not unique).
    Close the cuff explicitly first using close_planar_cuff. Distances include cap.
    """
    v, f = _mesh(vertices, faces)
    if len(_boundary(f)):
        raise ValueError('Signed distance requires a closed mesh; close cuff explicitly')
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    distance, index, nearest = closest_points(points, v, f, chunk_size)
    winding = np.zeros(len(points))
    tri = v[f]
    for start in range(0, len(points), chunk_size):
        q = tri[None] - points[start:start + chunk_size, None, None, :]
        lengths = np.linalg.norm(q, axis=3)
        a, b, c = q[:, :, 0], q[:, :, 1], q[:, :, 2]
        numerator = np.sum(a * np.cross(b, c), axis=2)
        denominator = np.prod(lengths, axis=2)
        denominator += np.sum(a * b, axis=2) * lengths[:, :, 2]
        denominator += np.sum(b * c, axis=2) * lengths[:, :, 0]
        denominator += np.sum(c * a, axis=2) * lengths[:, :, 1]
        winding[start:start + len(q)] = np.sum(2 * np.arctan2(numerator, denominator), axis=1) / (4 * np.pi)
    magnitude = np.abs(winding)
    ambiguous = (distance > surface_tolerance) & (np.minimum(magnitude, np.abs(magnitude - 1)) > 1e-6)
    signed = distance * np.where(magnitude > .5, -1., 1.)
    signed[distance <= surface_tolerance] = 0.
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths == 0):
        raise ValueError('Degenerate closed-mesh triangle')
    volume6 = np.sum(tri[:, 0] * np.cross(tri[:, 1], tri[:, 2]))
    if volume6 == 0:
        raise ValueError('Zero oriented volume: occupancy unqualified')
    outward = normals / lengths[:, None] * np.sign(volume6)
    return dict(signedDistance=signed, windingNumber=winding, triangleRow=index,
                closestPoint=nearest, closestNormal=outward[index], ambiguous=ambiguous)


def deformation_metrics(fitted, original, faces, reference_rotations=None):
    """Intrinsic stretches relative to original triangle; no global normal-dot test.

    Surface triangles alone have no intrinsic flip sign in 3D. A caller-supplied
    proper rotation field Fx3x3 permits correspondence-relative normal testing.
    """
    original, faces = _mesh(original, faces)
    fitted, _ = _mesh(fitted, faces)
    src, dst = original[faces], fitted[faces]
    se = np.stack([src[:, 1] - src[:, 0], src[:, 2] - src[:, 0]], axis=2)
    de = np.stack([dst[:, 1] - dst[:, 0], dst[:, 2] - dst[:, 0]], axis=2)
    _, singular, vh = np.linalg.svd(se, full_matrices=False)
    if np.any(singular[:, 1] <= 0):
        raise ValueError('Degenerate original triangle')
    # Inverse of source intrinsic basis; resulting 3x2 Jacobian singular values.
    jacobian = (de @ vh.transpose(0, 2, 1)) / singular[:, None, :]
    stretches = np.linalg.svd(jacobian, compute_uv=False)
    minimum = stretches[:, 1]
    condition = np.full(len(faces), np.inf)
    np.divide(stretches[:, 0], minimum, out=condition, where=minimum > 0)
    result = dict(principalStretches=stretches, areaRatio=np.prod(stretches, axis=1),
                  condition=condition, orientationQualified=False)
    if reference_rotations is not None:
        rotations = np.asarray(reference_rotations, dtype=float)
        if rotations.shape != (len(faces), 3, 3) or not np.allclose(
                rotations @ rotations.transpose(0, 2, 1), np.eye(3), atol=1e-7) or not np.allclose(np.linalg.det(rotations), 1, atol=1e-7):
            raise ValueError('Expected proper per-face reference rotations')
        expected = np.einsum('fij,fj->fi', rotations, np.cross(se[:, :, 0], se[:, :, 1]))
        actual = np.cross(de[:, :, 0], de[:, :, 1])
        result.update(orientationQualified=True, orientationDot=np.sum(expected * actual, axis=1))
    return result


def self_intersections(vertices, faces, tolerance=1e-10, max_candidates=2000000):
    """Complete AABB sweep plus separating axes and shared-simplex wedge tests.

    Touching and coplanar overlap count as intersections. Degenerate input raises.
    Bounded candidate budget raises instead of returning partial pass. Adjacent
    pairs are tested for overlap beyond their legitimately shared simplex.
    """
    v, f = _mesh(vertices, faces)
    tri = v[f]
    edges = np.roll(tri, -1, axis=1) - tri
    normals = np.cross(edges[:, 0], edges[:, 1])
    if np.any(np.linalg.norm(normals, axis=1) == 0):
        raise ValueError('Degenerate triangles: intersection assay unqualified')
    lo, hi = tri.min(axis=1), tri.max(axis=1)
    order = np.argsort(lo[:, 0], kind='stable')
    active, hits, candidates, excluded, adjacent_tests = [], [], 0, 0, 0
    for i in order:
        active = [j for j in active if hi[j, 0] + tolerance >= lo[i, 0]]
        possible = np.asarray(active, dtype=int)
        if len(possible):
            possible = possible[np.all(hi[possible] + tolerance >= lo[i], axis=1) & np.all(hi[i] + tolerance >= lo[possible], axis=1)]
        for j in possible:
            common = np.intersect1d(f[i], f[j])
            if len(common):
                adjacent_tests += 1
                if _shared_simplex_overlap(v, f[i], f[j], common, tolerance):
                    hits.append((int(i), int(j)))
                continue
            candidates += 1
            if candidates > max_candidates:
                raise RuntimeError('Intersection candidate budget exceeded; no qualification')
            axes = np.vstack([normals[i], normals[j],
                              np.cross(edges[i, :, None], edges[j, None, :]).reshape(-1, 3),
                              np.cross(normals[i], edges[i]), np.cross(normals[j], edges[j])])
            norms = np.linalg.norm(axes, axis=1)
            axes = axes[norms > 0] / norms[norms > 0, None]
            pi, pj = tri[i] @ axes.T, tri[j] @ axes.T
            separated = np.any((pi.max(axis=0) + tolerance < pj.min(axis=0)) | (pj.max(axis=0) + tolerance < pi.min(axis=0)))
            if not separated:
                hits.append((int(i), int(j)))
        active.append(int(i))
    return dict(intersectingPairs=np.asarray(hits, dtype=int).reshape(-1, 2),
                testedCandidates=candidates, excludedSharedVertexPairs=excluded,
                nonAdjacentQualified=True, fullSelfIntersectionQualified=True,
                sharedSimplexPairsTested=adjacent_tests,
                numericalTolerance=tolerance)


def _shared_simplex_overlap(vertices, first, second, common, tolerance):
    """Test overlap beyond a legitimate shared edge or vertex, in float64.

    For a shared vertex, nonparallel planes meet on a line through that vertex.
    Their triangles overlap beyond it iff one sign of that line lies in both
    tangent wedges. Coplanar wedges overlap iff either bounding ray lies in the
    other wedge. This avoids shrinking triangles and missing arbitrarily small
    adjacent folds. A shared-edge pair can overlap beyond the edge only when
    coplanar, with both opposite vertices on the same side of the edge.
    """
    if len(common) == 3:
        return True
    origin = vertices[common[0]]
    e1 = vertices[[x for x in first if x != common[0]]] - origin
    e2 = vertices[[x for x in second if x != common[0]]] - origin
    n1, n2 = np.cross(e1[0], e1[1]), np.cross(e2[0], e2[1])
    n1 /= np.linalg.norm(n1); n2 /= np.linalg.norm(n2)
    line = np.cross(n1, n2)
    parallel = np.linalg.norm(line) <= tolerance
    if len(common) == 2:
        if not parallel:
            return False
        edge = vertices[common[1]] - origin
        opposite1 = vertices[next(x for x in first if x not in common)] - origin
        opposite2 = vertices[next(x for x in second if x not in common)] - origin
        return float(np.dot(np.cross(edge, opposite1), np.cross(edge, opposite2))) > 0

    def contains(edges, direction):
        normal = np.cross(edges[0], edges[1]); denominator = np.dot(normal, normal)
        a = np.dot(np.cross(direction, edges[1]), normal) / denominator
        b = np.dot(np.cross(edges[0], direction), normal) / denominator
        return a >= -tolerance and b >= -tolerance and max(a, b) > tolerance

    if parallel:
        return any(contains(e2, direction) for direction in e1) or any(contains(e1, direction) for direction in e2)
    line /= np.linalg.norm(line)
    return any(contains(e1, direction) and contains(e2, direction) for direction in (line, -line))


def certify_clearance(source_vertices, source_faces, target_vertices, target_faces,
                      minimum=.0025, max_depth=5, max_samples=160000):
    """Certify every exterior triangle using the signed-distance Lipschitz bound.

    Every point on a triangle is within its maximum centroid-to-corner distance
    of the centroid. Therefore d(centroid)-radius is a lower bound on that entire
    triangle. Unproven triangles subdivide into four exact source subtriangles;
    a sampled violation fails immediately, and limits yield unqualified rather
    than acceptance. Assumes the target closed oriented surface passes winding
    checks; its own self-intersection remains a separate required qualification.
    """
    vertices, faces = _mesh(source_vertices, source_faces)
    pending = vertices[faces]
    source_rows = np.arange(len(faces))
    samples, certified, levels, failures = 0, 0, [], []
    minimum_sample = np.inf
    worst_bound = np.inf
    for depth in range(max_depth + 1):
        if not len(pending):
            break
        if samples + len(pending) > max_samples:
            levels.append(dict(depth=depth, pending=len(pending), sampleBudgetExceeded=True))
            break
        centers = pending.mean(axis=1)
        radius = np.linalg.norm(pending - centers[:, None], axis=2).max(axis=1)
        query = signed_distances(centers, target_vertices, target_faces)
        samples += len(centers)
        if np.any(query['ambiguous']):
            return dict(qualified=False, reason='Ambiguous target winding', samples=samples, levels=levels)
        distances = query['signedDistance']
        minimum_sample = min(minimum_sample, float(distances.min()))
        lower = distances - radius
        okay = lower >= minimum
        certified += int(okay.sum())
        bad = np.flatnonzero(distances < minimum)
        failures.extend(dict(sourceTriangle=int(source_rows[i]), sample=centers[i].tolist(),
                             signedDistanceM=float(distances[i])) for i in bad[:100])
        levels.append(dict(depth=depth, samples=len(centers), certified=int(okay.sum()),
                           sampledViolations=len(bad), minimumLowerBoundM=float(lower.min())))
        if len(bad):
            return dict(qualified=False, reason='Sampled surface clearance violation', samples=samples,
                        minimumSampleDistanceM=minimum_sample, levels=levels, failures=failures)
        if np.any(okay):
            worst_bound = min(worst_bound, float(lower[okay].min()))
        pending, source_rows = pending[~okay], source_rows[~okay]
        if depth == max_depth or not len(pending):
            break
        a, b, c = pending[:, 0], pending[:, 1], pending[:, 2]
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        pending = np.concatenate([np.stack(rows, axis=1) for rows in
                                  ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))])
        source_rows = np.tile(source_rows, 4)
    return dict(qualified=len(pending) == 0, reason='Certified' if not len(pending) else 'Subdivision/sample limit',
                samples=samples, unresolvedSubtriangles=len(pending), minimumSampleDistanceM=minimum_sample,
                certifiedLowerBoundM=None if not np.isfinite(worst_bound) else worst_bound,
                levels=levels, failures=failures)
