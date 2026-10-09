"""One selected41 R panel net; source-surface samples, explicit sewn topology."""
import heapq
import math
from collections import defaultdict, deque

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

DIGITS = ('thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky')
RING_POINTS = 32
CUFF_POINTS = 64
PANEL_SPACING_M = .0025


def unit(x):
    x = np.asarray(x, np.float64); length = np.linalg.norm(x)
    assert np.isfinite(length) and length > 0
    return x/length


def closest_bary(q, p):
    # Translated cross-product projection plus all three bounded edges.
    ab, ac, aq = p[1]-p[0], p[2]-p[0], q-p[0]
    normal = np.cross(ab, ac); denominator = normal@normal
    assert denominator > 0
    b = np.cross(aq, ac)@normal/denominator; c = np.cross(ab, aq)@normal/denominator
    candidates = []
    if b >= 0 and c >= 0 and b+c <= 1: candidates.append(np.array([1-b-c, b, c]))
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = p[j]-p[i]; t = min(1., max(0., (q-p[i])@edge/(edge@edge)))
        weights = np.zeros(3); weights[i] = 1-t; weights[j] = t; candidates.append(weights)
    return min(candidates, key=lambda w: np.sum((w@p-q)**2))


class Surface:
    def __init__(self, a, ancestry):
        self.p = a['positions'].astype(np.float64); self.f = a['triangles']
        roles = ancestry['authoredVertexRoles']; face_roles = ancestry['authoredFaceRoles']
        inner = (roles[self.f] == 3).all(1)
        self.faces = {'outer': np.flatnonzero(face_roles != 2),
                      'inner': np.flatnonzero(inner), 'rim': np.flatnonzero((face_roles == 2) & ~inner)}
        self.trees = {wall: BVHTree.FromPolygons(self.p.tolist(), self.f[ids].tolist(), all_triangles=True)
                      for wall, ids in self.faces.items()}
        self.extent = float(np.linalg.norm(np.ptp(self.p, axis=0)))
        edges = np.sort(np.concatenate([self.f[self.faces['outer']][:, pair] for pair in ([0, 1], [1, 2], [2, 0])]), axis=1)
        edges = np.unique(edges, axis=0)
        self.adj = defaultdict(list); self.edge_faces = {}; self.vertex_faces = {}
        for x, y in edges:
            distance = float(np.linalg.norm(self.p[x]-self.p[y]))
            self.adj[int(x)].append((int(y), distance)); self.adj[int(y)].append((int(x), distance))
        for wall, faces in self.faces.items():
            self.edge_faces[wall] = {}; self.vertex_faces[wall] = {}
            for face in faces:
                t = self.f[face]
                for v in t: self.vertex_faces[wall].setdefault(int(v), int(face))
                for x, y in zip(t, np.roll(t, -1)): self.edge_faces[wall].setdefault(tuple(sorted((int(x), int(y)))), int(face))

    def sample(self, face, point):
        weights = closest_bary(np.asarray(point, np.float64), self.p[self.f[face]])
        return int(face), weights

    def point(self, sample):
        face, weights = sample; return weights@self.p[self.f[face]]

    def vertex(self, v, wall='outer'):
        face = self.vertex_faces[wall][int(v)]
        weights = np.zeros(3); weights[np.flatnonzero(self.f[face] == v)[0]] = 1.
        return face, weights

    def ray(self, origin, direction, wall='outer'):
        hit = self.trees[wall].ray_cast(Vector(origin), Vector(unit(direction)), self.extent*3)
        assert hit[0] is not None, ('Selected source wall ray missed', wall, np.asarray(origin).tolist(), np.asarray(direction).tolist())
        return self.sample(int(self.faces[wall][hit[2]]), np.asarray(hit[0], np.float64))

    def nearest(self, point, wall):
        hit = self.trees[wall].find_nearest(Vector(point)); assert hit[0] is not None
        return self.sample(int(self.faces[wall][hit[2]]), np.asarray(hit[0], np.float64))

    def path(self, start, end):
        # Actual exterior edge geodesic; no ambient shortcut across a web or wall.
        vertices = [int(self.f[s[0]][np.argmax(s[1])]) for s in (start, end)]
        first, last = vertices; distance = {first: 0.}; previous = {}; queue = [(0., first)]
        while queue:
            cost, v = heapq.heappop(queue)
            if cost != distance[v]: continue
            if v == last: break
            for w, length in self.adj[v]:
                proposed = cost+length
                if proposed < distance.get(w, math.inf):
                    distance[w] = proposed; previous[w] = v; heapq.heappush(queue, (proposed, w))
        assert last in distance, 'Source outer wall has no connecting path'
        route = [last]
        while route[-1] != first: route.append(previous[route[-1]])
        route.reverse()
        samples = [start, *[self.vertex(v) for v in route], end]
        # Each step is on one original triangle/edge. Preserve endpoints exactly.
        return self.resample(samples, PANEL_SPACING_M, closed=False)

    def resample(self, samples, spacing, closed=False, count=None, wall='outer'):
        points = np.array([self.point(s) for s in samples]); points2 = np.roll(points, -1, axis=0) if closed else points[1:]
        lengths = np.linalg.norm(points2-(points if closed else points[:-1]), axis=1)
        arc = np.r_[0., np.cumsum(lengths)]; assert arc[-1] > 0
        count = count or max(2, int(math.ceil(arc[-1]/spacing))+1)
        stations = np.linspace(0, arc[-1], count, endpoint=not closed); output = []
        for d in stations:
            if not closed and d == arc[-1]: output.append(samples[-1]); continue
            i = min(len(lengths)-1, np.searchsorted(arc, d, side='right')-1)
            while lengths[i] == 0: i += 1
            t = (d-arc[i])/lengths[i]; j = (i+1)%len(samples)
            q = (1-t)*points[i]+t*points[j]
            # Both edge endpoints must have a common actual source face.
            ids = set(self.f[samples[i][0]][samples[i][1] > 0]) | set(self.f[samples[j][0]][samples[j][1] > 0])
            if len(ids) == 2 and tuple(sorted(ids)) in self.edge_faces[wall]:
                a,b = sorted(ids); owner = self.edge_faces[wall][(a,b)]
                edge = self.p[b]-self.p[a]; fraction = min(1.,max(0.,(q-self.p[a])@edge/(edge@edge)))
                weights = np.zeros(3); weights[np.flatnonzero(self.f[owner]==a)[0]]=1-fraction
                weights[np.flatnonzero(self.f[owner]==b)[0]]=fraction
                output.append((owner,weights))
            elif ids <= set(self.f[samples[i][0]]): output.append(self.sample(samples[i][0], q))
            elif ids <= set(self.f[samples[j][0]]): output.append(self.sample(samples[j][0], q))
            else: raise AssertionError('Curve segment lacks a common original source face')
        if not closed: output[0], output[-1] = samples[0], samples[-1]
        return output


class Net:
    def __init__(self, surface): self.surface = surface; self.samples = []; self.faces = []; self.parts = []; self.labels = []
    def add(self, sample, label):
        self.samples.append(sample); self.labels.append(label); return len(self.samples)-1
    def p(self, vertex): return self.surface.point(self.samples[vertex])
    def face(self, vertices, part):
        assert len(set(vertices)) == len(vertices)
        if len(vertices) == 3: self.faces.append(tuple(vertices)); self.parts.append(part)
        else:
            assert len(vertices) == 4
            self.face(vertices[:3], part); self.face((vertices[0], vertices[2], vertices[3]), part)
    def strip(self, a, b, part):
        assert len(a) == len(b)
        for i in range(len(a)): self.face((a[i], a[(i+1)%len(a)], b[(i+1)%len(a)], b[i]), part)
    def curve(self, begin, end, label):
        samples = self.surface.path(self.samples[begin], self.samples[end])
        return [begin, *[self.add(s, label) for s in samples[1:-1]], end]


def loops(edges):
    adjacent = defaultdict(list)
    for a, b in edges: adjacent[int(a)].append(int(b)); adjacent[int(b)].append(int(a))
    assert all(len(v) == 2 for v in adjacent.values())
    remaining = set(adjacent); result = []
    while remaining:
        begin = min(remaining); previous = None; current = begin; loop = []
        while True:
            remaining.remove(current); loop.append(current)
            following = next(v for v in adjacent[current] if v != previous)
            if following == begin: break
            assert following in remaining
            previous, current = current, following
        result.append(loop)
    return result


def panel(net, boundary, origin, u, v, normal, sign, joints, label):
    def xy(p): return np.array([(p-origin)@v, (p-origin)@u])
    polygon = np.array([xy(net.p(i)) for i in boundary]); n = len(polygon)
    if np.sum(polygon[:, 0]*np.roll(polygon[:, 1], -1)-polygon[:, 1]*np.roll(polygon[:, 0], -1)) < 0:
        boundary = boundary[::-1]; polygon = polygon[::-1]
    def inside(q):
        x, y = q; result = False
        for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
            if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: result = not result
        return result
    coords = list(polygon); originals = list(boundary); constraints = []
    def interior(q):
        if not inside(q): return None
        if any(np.array_equal(q, p) for p in coords): return next(i for i,p in enumerate(coords) if np.array_equal(q,p))
        center = origin+q[0]*v+q[1]*u
        sample = net.surface.ray(center+sign*normal*net.surface.extent, -sign*normal)
        coords.append(q); originals.append(net.add(sample, label)); return len(coords)-1
    for center, width, tangent in joints:
        row = [interior(xy(center+offset*width*tangent)) for offset in (-1., 0., 1.)]
        constraints.extend((a,b) for a,b in zip(row,row[1:]) if a is not None and b is not None and a != b)
    low, high = polygon.min(0), polygon.max(0)
    for y in np.arange(low[1]+PANEL_SPACING_M, high[1], PANEL_SPACING_M):
        for x in np.arange(low[0]+PANEL_SPACING_M, high[0], PANEL_SPACING_M): interior(np.array([x,y]))
    # CDT only connects authored panel points/edges; it never moves their 3D source samples.
    result = delaunay_2d_cdt([Vector(p) for p in coords], constraints, [list(range(n))], 1, 1e-8, True)
    _, _, triangles, provenance, _, _ = result
    assert all(len(ids) == 1 for ids in provenance), 'Panel constraints intersect or merge; no repair fallback'
    remap = [originals[ids[0]] for ids in provenance]
    for triangle in triangles: assert len(triangle) == 3; net.face(tuple(remap[i] for i in triangle), label)


def orient(net):
    incidence = defaultdict(list)
    for face, triangle in enumerate(net.faces):
        for a, b in zip(triangle, triangle[1:]+triangle[:1]): incidence[tuple(sorted((a,b)))].append((face, a < b))
    assert all(len(rows) <= 2 for rows in incidence.values()), 'Authored net is nonmanifold'
    neighbours = defaultdict(list)
    for rows in incidence.values():
        if len(rows) == 2:
            (a, x), (b, y) = rows; neighbours[a].append((b, x == y)); neighbours[b].append((a, x == y))
    parity = {0: False}; queue = deque([0])
    while queue:
        f = queue.popleft()
        for g, different in neighbours[f]:
            value = parity[f] ^ different
            if g in parity: assert parity[g] == value, 'Authored net is not orientable'
            else: parity[g] = value; queue.append(g)
    assert len(parity) == len(net.faces), 'Authored glove is disconnected'
    for f, flip in parity.items():
        if flip: a,b,c = net.faces[f]; net.faces[f] = (a,c,b)
    first = net.faces[0]; p = np.array([net.p(i) for i in first]); source = net.surface.p[net.surface.f[net.samples[first[0]][0]]]
    if np.cross(p[1]-p[0], p[2]-p[0])@np.cross(source[1]-source[0], source[2]-source[0]) < 0:
        net.faces = [(a,c,b) for a,b,c in net.faces]
    return incidence


def construct(a, ancestry, rest, proof, progress=lambda *args: None):
    surface = Surface(a, ancestry); net = Net(surface)
    bones = {b['name']: b for b in rest}; bone = lambda name: bones['DEF-'+name+'.R']
    wrist = np.array(bone('hand')['head']); u = unit(np.array(bone('hand')['tail'])-wrist)
    v = unit(np.array(bone('f_pinky.01')['head'])-bone('f_index.01')['head']); v = unit(v-(v@u)*u); normal = unit(np.cross(v,u))
    roots = []; joints = []; anatomy = []
    for digit in DIGITS:
        b = [bone(f'{digit}.{i:02}') for i in (1,2,3)]
        centers = [np.array(b[1]['head']), np.array(b[2]['head']), np.array(b[2]['tail'])]
        axis2, axis3 = unit(centers[1]-centers[0]), unit(centers[2]-centers[1])
        tip_witness = next(r for r in proof['landmarks'] if r['landmark'] == digit+'-tip-apex')
        apex = surface.vertex(tip_witness['originalVertexIds'][0]); apex_point = surface.point(apex)
        # Exposed PIP/distal strip only. Embedded first joint is a panel constraint below.
        stations = [(centers[0]+t*(centers[1]-centers[0]), unit((1-t)*axis2+t*axis3)) for t in (0.,.15,.35,.6,.85,1.)]
        end = centers[1]+.85*((apex_point-centers[1])@axis3)*axis3
        stations += [(centers[1]+t*(end-centers[1]), axis3) for t in (.25,.5,.75,1.)]
        rings = []
        for center, axis in stations:
            x = unit(v-(v@axis)*axis); z = unit(np.cross(axis,x))
            if z@normal < 0: z = -z
            ring = [net.add(surface.ray(center, math.cos(t)*x+math.sin(t)*z), digit+'-strip') for t in np.arange(RING_POINTS)*2*np.pi/RING_POINTS]
            if rings: net.strip(rings[-1],ring,digit+'-strip')
            rings.append(ring)
        tip = net.add(apex,digit+'-tip')
        for i in range(RING_POINTS): net.face((rings[-1][i],rings[-1][(i+1)%RING_POINTS],tip),digit+'-tip')
        roots.append(rings[0]); width = np.linalg.norm(net.p(rings[0][0])-net.p(rings[0][RING_POINTS//2]))/2
        tangent=unit(np.cross(np.array(b[0]['tail'])-b[0]['head'],normal))
        joints.append((np.array(b[0]['head']),width,tangent)); anatomy.append({'digit':digit,'exposedStripJoint':'02','rows':len(rings),'circumferenceSamples':RING_POINTS})
        progress(digit+'-strip', net, {'completedDigitStrips':len(roots)})
    cuff = next(r for r in proof['landmarks'] if r['landmark'] == 'actual-cuff-rim-1688')
    def ordered(loop):
        pp=surface.p[loop]; axis=unit(np.array(bones['DEF-forearm.R.001']['tail'])-bones['DEF-forearm.R.001']['head'])
        if np.sum(np.cross(pp-pp.mean(0),np.roll(pp,-1,axis=0)-pp.mean(0)),axis=0)@axis<0:loop=loop[::-1]
        start=int(np.argmax(surface.p[loop]@v));return loop[start:]+loop[:start]
    outer_loop = ordered(cuff['originalCircuitVertexIds'])
    outer = surface.resample([surface.vertex(i) for i in outer_loop],None,True,CUFF_POINTS)
    cuff_ids = [net.add(s,'cuff-rim') for s in outer]
    transverse = np.array([net.p(i)@v for i in cuff_ids]); left, right = int(transverse.argmin()),int(transverse.argmax())
    def arc(loop, first, last, step):
        result = [loop[first]]
        while first != last: first = (first+step)%len(loop); result.append(loop[first])
        return result
    cuff_arcs = [arc(cuff_ids,right,left,step) for step in (1,-1)]
    cuff_arcs.sort(key=lambda row: np.mean([(net.p(i)-wrist)@normal for i in row]),reverse=True)
    outer_left = net.curve(cuff_ids[left],roots[0][RING_POINTS//2],'thumb-outer-edge')
    outer_right = net.curve(roots[-1][0],cuff_ids[right],'pinky-outer-edge')
    webs = []
    for i in range(4):
        witness=next(r for r in proof['landmarks'] if r['landmark']==DIGITS[i]+'-'+DIGITS[i+1]+'-web')
        center=np.asarray(witness['centerM'])
        direction = unit((np.array(bone(DIGITS[i]+'.01')['tail'])-bone(DIGITS[i]+'.01')['head'])+
                         (np.array(bone(DIGITS[i+1]+'.01')['tail'])-bone(DIGITS[i+1]+'.01')['head']))
        web = net.add(surface.ray(center+direction*surface.extent,-direction),'web-'+str(i))
        webs.append(net.curve(roots[i][0],web,'web-'+str(i))[:-1]+net.curve(web,roots[i+1][RING_POINTS//2],'web-'+str(i)))
    for sign, label, cuff_arc in ((1,'dorsal-panel',cuff_arcs[0]),(-1,'palmar-panel',cuff_arcs[1])):
        boundary = list(outer_left[:-1])
        for i, ring in enumerate(roots):
            # Both semicircles have identical end IDs; web/side curves are shared seams.
            boundary += arc(ring,RING_POINTS//2,0,-1 if sign==1 else 1)[:-1]
            if i < 4: boundary += webs[i][:-1]
        boundary += outer_right[:-1]+cuff_arc[:-1]
        assert len(boundary) == len(set(boundary))
        panel(net,boundary,wrist,u,v,normal,sign,joints,label)
        progress(label, net, {'surfaceProjectedPanel':label})
    # Rebuild actual lining between its measured mouth and its single1029-edge wrist opening.
    inner_faces = surface.f[surface.faces['inner']]
    edges = np.sort(np.concatenate([inner_faces[:, pair] for pair in ([0,1],[1,2],[2,0])]),axis=1)
    edges, count = np.unique(edges,axis=0,return_counts=True); inner_loops = loops(edges[count==1])
    assert sorted(map(len,inner_loops)) == [71,1029,1688]
    mouth = next(x for x in inner_loops if len(x)==1688); end = next(x for x in inner_loops if len(x)==1029)
    parent_key = lambda i: (tuple(ancestry['vertexParentSourceIds'][i]), tuple(ancestry['vertexParentCoefficients'][i]))
    inner_by_parent = {parent_key(i):i for i in mouth}; assert len(inner_by_parent)==len(mouth)
    paired = {i:inner_by_parent[parent_key(i)] for i in outer_loop}; mouth_samples=[]
    for face, weights in outer:
        ids=surface.f[face]; selected=weights>0; inner_ids=[paired[int(i)] for i in ids[selected]]
        owner=surface.vertex_faces['inner'][inner_ids[0]] if len(inner_ids)==1 else surface.edge_faces['inner'][tuple(sorted(inner_ids))]
        paired_weights=np.zeros(3)
        for i,w in zip(inner_ids,weights[selected]): paired_weights[np.flatnonzero(surface.f[owner]==i)[0]]=w
        mouth_samples.append((owner,paired_weights))
    end_samples=surface.resample([surface.vertex(i,'inner') for i in ordered(end)],None,True,CUFF_POINTS,wall='inner')
    last=cuff_ids
    for t in np.linspace(0,1,13):
        samples=mouth_samples if t==0 else end_samples if t==1 else [surface.nearest((1-t)*surface.point(x)+t*surface.point(y),'inner') for x,y in zip(mouth_samples,end_samples)]
        ring=[net.add(s,'cuff-lining') for s in samples];net.strip(last,ring,'cuff-return' if t==0 else 'cuff-lining');last=ring
    orient(net)
    return net, {'anatomy':anatomy,'panelSpacingM':PANEL_SPACING_M,'cuffCircumferenceSamples':CUFF_POINTS,
        'liningRows':13,'expectedOpenBoundaryVertices':last,'inheritedSmallHandleBoundaryReplaced':71,
        'limits':'New coherent surface topology; source71-edge secondary cuff handle is not retained as an extra hole. Source detail/bake, full surface/contact/deformation and moving appearance remain mandatory.'}
