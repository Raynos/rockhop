"""All clearance intervals on a prescribed radius branch, without sampling.

A triangle's closed clearance neighborhood is its normal prism plus its three
finite edge cylinders and vertex spheres. Restricting each convex feature to
a line gives linear bounds and one quadratic interval. Their union is exactly
the line's forbidden unsigned-distance set. Exterior components are selected
by signed distance once per component; source/anatomical branch stays fixed.
"""
import numpy as np


def linear(low, high, a, b):
    """Intersect intervals with a+b*r >=0, vectorized per triangle."""
    positive, negative, zero = b > 0, b < 0, b == 0
    root = -a/np.where(zero, 1., b)
    low = np.where(positive, np.maximum(low, root), low)
    high = np.where(negative, np.minimum(high, root), high)
    high = np.where(zero & (a < 0), -np.inf, high)
    return low, high


def quadratic(low, high, vector, velocity, radius):
    """Intersect ||vector+r*velocity|| <= radius using stable closest approach."""
    a = np.sum(velocity*velocity, axis=1); b = np.sum(vector*velocity, axis=1)
    center = -b/np.where(a > 0, a, 1.)
    closest = vector+center[:, None]*velocity
    remaining = radius*radius-np.sum(closest*closest, axis=1)
    half = np.sqrt(np.maximum(remaining, 0)/np.where(a > 0, a, 1.))
    low = np.where(a > 0, np.maximum(low, center-half), low)
    high = np.where(a > 0, np.minimum(high, center+half), high)
    high = np.where(remaining < 0, -np.inf, high)
    return low, high


def forbidden(mesh, origin, direction, lower, upper, clearance):
    start, end = origin+lower*direction, origin+upper*direction
    ids = np.flatnonzero(np.all((mesh.high >= np.minimum(start, end)-clearance)
        & (mesh.low <= np.maximum(start, end)+clearance), axis=1))
    tri = mesh.triangles[ids]; n = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    length = np.linalg.norm(n, axis=1); good = length > 0
    # Zero-area originals still contribute edge/vertex neighborhoods.
    n /= np.where(good, length, 1.)[:, None]
    base_low, base_high = np.full(len(ids), lower), np.full(len(ids), upper)
    normal_a = np.sum((origin-tri[:, 0])*n, axis=1); normal_b = n@direction
    low, high = linear(base_low, base_high, clearance-normal_a, -normal_b)
    low, high = linear(low, high, clearance+normal_a, normal_b)
    for a, b in ((0, 1), (1, 2), (2, 0)):
        inward = np.cross(n, tri[:, b]-tri[:, a])
        low, high = linear(low, high, np.sum((origin-tri[:, a])*inward, axis=1), inward@direction)
    high = np.where(good, high, -np.inf)
    intervals = [(float(a), float(b)) for a, b in zip(low, high) if a <= b]
    for a, b in ((0, 1), (1, 2), (2, 0)):
        edge = tri[:, b]-tri[:, a]; square = np.sum(edge*edge, axis=1)
        offset = origin-tri[:, a]
        axial_a = np.sum(offset*edge, axis=1)/np.where(square > 0, square, 1.)
        axial_b = (edge@direction)/np.where(square > 0, square, 1.)
        low, high = linear(base_low, base_high, axial_a, axial_b)
        low, high = linear(low, high, 1-axial_a, -axial_b)
        low, high = quadratic(low, high, offset-axial_a[:, None]*edge,
            direction-axial_b[:, None]*edge, clearance)
        intervals.extend((float(x), float(y)) for x, y in zip(low, high) if x <= y)
        low, high = quadratic(base_low, base_high, offset,
            np.broadcast_to(direction, offset.shape), clearance)
        intervals.extend((float(x), float(y)) for x, y in zip(low, high) if x <= y)
    return intervals, len(ids)


def intersect(left, right):
    return [[max(a, c), min(b, d)] for a, b in left for c, d in right if max(a, c) < min(b, d)]


def exterior_domains(mesh, nearest, origin, direction, lower, upper):
    """Exact wall-ray crossings split signed exterior components."""
    hits = mesh.ray_hits(origin, direction)
    boundaries = sorted(set([lower, upper]+[h[0] for h in hits if lower < h[0] < upper]))
    result = []
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        if float(nearest((origin+(a+b)/2*direction)[None])[0][0]) > 0:
            result.append([a, b])
    return result


def feasible(mesh, nearest, center, direction, offsets, lower, upper, clearance):
    """Return every exterior open interval at the exact requested clearance."""
    assert upper > lower and clearance > 0
    blocked, count = [], 0
    for offset in offsets:
        intervals, candidates = forbidden(mesh, center+offset, direction, lower, upper, clearance)
        blocked.extend(intervals); count += candidates
    merged = []
    for a, b in sorted(blocked):
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    complements = []; cursor = lower
    for a, b in merged:
        if a > cursor: complements.append([cursor, a])
        cursor = max(cursor, b)
    if cursor < upper: complements.append([cursor, upper])
    exterior = complements; wall_domains = []
    for offset in offsets:
        domain = exterior_domains(mesh, nearest, center+offset, direction, lower, upper)
        wall_domains.append(domain); exterior = intersect(exterior, domain)
    return exterior, {'method': 'EXACT_TRIANGLE_PRISM_EDGE_CYLINDER_VERTEX_SPHERE_LINE_UNION',
        'requestedClearanceM': float(clearance), 'candidateTriangleWallPairs': count,
        'blockedIntervalsM': merged, 'pairedWallExteriorDomainsM': wall_domains,
        'feasibleExteriorIntervalsM': exterior}
