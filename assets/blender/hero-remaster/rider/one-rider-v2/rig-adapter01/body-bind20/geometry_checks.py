"""CPU-only triangle surface distance, including reciprocal face crossings.

No closed-volume assumption: the actual eye donors have open rear boundaries.
Broadphase AABBs are expanded by the requested distance. For every selected
pair, point/triangle, all nine segment/segment pairs and reciprocal
segment/triangle crossings give a triangle-surface distance. Coplanar overlap
is detected by zero point/face or edge/edge distance, not ignored.
"""
import numpy as np


def point_segment(p, a, b):
    edge = b - a
    t = np.sum((p-a)*edge, axis=1) / np.maximum(np.sum(edge*edge, axis=1), 1e-30)
    return np.sum((p - a - t.clip(0, 1)[:, None]*edge)**2, axis=1)


def point_triangle(p, t):
    a, b = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
    d = p-t[:, 0]
    aa, ab, bb = np.sum(a*a, 1), np.sum(a*b, 1), np.sum(b*b, 1)
    da, db = np.sum(d*a, 1), np.sum(d*b, 1)
    den = aa*bb-ab*ab
    u = (bb*da-ab*db)/np.maximum(den, 1e-30)
    v = (aa*db-ab*da)/np.maximum(den, 1e-30)
    normal = np.cross(a, b)
    plane = np.sum(d*normal, 1)**2/np.maximum(np.sum(normal*normal, 1), 1e-30)
    result = np.where((u >= 0)&(v >= 0)&(u+v <= 1)&(den > 1e-30), plane, np.inf)
    for j in range(3):
        result = np.minimum(result, point_segment(p, t[:, j], t[:, (j+1)%3]))
    return result


def segment_segment(p, q, r, s):
    a, b, w = q-p, s-r, p-r
    aa, ab, bb = np.sum(a*a, 1), np.sum(a*b, 1), np.sum(b*b, 1)
    aw, bw = np.sum(a*w, 1), np.sum(b*w, 1)
    den = aa*bb-ab*ab
    u = (ab*bw-bb*aw)/np.maximum(den, 1e-30)
    v = (aa*bw-ab*aw)/np.maximum(den, 1e-30)
    squared = np.sum((w+u[:, None]*a-v[:, None]*b)**2, 1)
    inside = (den > 1e-30)&(u >= 0)&(u <= 1)&(v >= 0)&(v <= 1)
    result = np.where(inside, squared, np.inf)
    for p0, a0, b0 in [(p,r,s), (q,r,s), (r,p,q), (s,p,q)]:
        result = np.minimum(result, point_segment(p0,a0,b0))
    return result


def segment_triangle(p, q, t):
    direction = q-p
    e1, e2 = t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]
    h = np.cross(direction, e2)
    determinant = np.sum(e1*h, axis=1)
    scale = np.linalg.norm(direction,axis=1)*np.linalg.norm(e1,axis=1)*np.linalg.norm(e2,axis=1)
    good = abs(determinant) > np.maximum(scale*1e-12, 1e-30)
    inverse = np.divide(1., determinant, out=np.zeros_like(determinant), where=good)
    start = p-t[:, 0]
    u = inverse*np.sum(start*h, 1)
    cross = np.cross(start,e1)
    v = inverse*np.sum(direction*cross, 1)
    length = inverse*np.sum(e2*cross, 1)
    eps = 1e-10
    return good&(u >= -eps)&(v >= -eps)&(u+v <= 1+eps)&(length >= -eps)&(length <= 1+eps)


def triangle_distances(a,b):
    result = np.full(len(a),np.inf)
    crossing = np.zeros(len(a),dtype=bool)
    for j in range(3):
        result = np.minimum(result,point_triangle(a[:,j],b))
        result = np.minimum(result,point_triangle(b[:,j],a))
        crossing |= segment_triangle(a[:,j],a[:,(j+1)%3],b)
        crossing |= segment_triangle(b[:,j],b[:,(j+1)%3],a)
        for k in range(3):
            result = np.minimum(result,segment_segment(a[:,j],a[:,(j+1)%3],b[:,k],b[:,(k+1)%3]))
    result[crossing] = 0
    return np.sqrt(np.maximum(result,0))


def surface_clearance(a,b,reach=.001):
    lower, upper = b.min(1), b.max(1)
    candidates = []
    for i,t in enumerate(a):
        ids = np.flatnonzero((t.min(0)-reach <= upper).all(1)&(t.max(0)+reach >= lower).all(1))
        candidates.extend((i,int(j)) for j in ids)
    if not candidates:
        return {'distanceLowerBoundM':reach,'exactMinimumWithinReachM':None,'testedPairs':0,'intersectionPairs':0,'worstPair':None}
    pairs = np.array(candidates)
    distances = np.concatenate([triangle_distances(a[pairs[i:i+4096,0]],b[pairs[i:i+4096,1]]) for i in range(0,len(pairs),4096)])
    k = int(np.argmin(distances))
    return {'distanceLowerBoundM':min(reach,float(distances[k])),
        'exactMinimumWithinReachM':float(distances[k]) if distances[k] <= reach else None,
        'testedPairs':len(pairs),'intersectionPairs':int((distances <= 1e-10).sum()),
        'worstPair':pairs[k].tolist(),
        'worstTrianglesM':[a[pairs[k,0]].tolist(),b[pairs[k,1]].tolist()]}


def topology(points,faces):
    from collections import Counter
    _,canonical = np.unique(points.astype('<f4'),axis=0,return_inverse=True)
    triangles = canonical[faces]
    edges = Counter(tuple(sorted((int(a),int(b)))) for f in triangles for a,b in zip(f,np.roll(f,-1)))
    return {'triangles':len(faces),'physicalVertices':len(np.unique(triangles)),
        'boundaryEdges':sum(v == 1 for v in edges.values()),
        'nonManifoldEdges':sum(v > 2 for v in edges.values()),
        'closed':all(v == 2 for v in edges.values())}


def self_test():
    a = np.array([[[0,0,0],[1,0,0],[0,1,0]]],dtype=float)
    # Coplanar containment, edge crossings and separated parallel faces.
    tests = [(a,np.array([[[.1,.1,0],[.2,.1,0],[.1,.2,0]]]),0),
        (a,np.array([[[-.1,.4,0],[.8,-.1,0],[1.1,1.1,0]]]),0),
        (a,a+np.array([0,0,.001]),.001),
        (a,np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0]]]),0)]
    for left,right,expected in tests:
        measured = triangle_distances(left,right)[0]
        assert abs(measured-expected)<1e-12,(measured,expected)
    return {'syntheticCases':len(tests),'pass':True}
