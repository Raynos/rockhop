"""One continuous trilinear displacement field for the complete selected cloth.

No radial chart, independently moved sheets, smoothing of source vertices, or
anatomical station boundary. Contact support follows measured deficient cloth.
This module uses NumPy only; a caller supplies actual full-wearer nearest faces.
"""
from collections import deque
import numpy as np

CORNERS = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)])


class Field:
    def __init__(self, points, spacing=.04):
        self.spacing = spacing
        self.origin = np.floor(points.min(0)/spacing)*spacing-2*spacing
        self.shape = np.ceil((points.max(0)-self.origin)/spacing).astype(int)+3
        assert np.prod(self.shape) <= 100000, 'Unexpected cloth bounds'
        self.count = int(np.prod(self.shape))
        self.values = np.zeros((self.count, 3), dtype=float)
        self.active = np.zeros(self.count, bool)
        self.contact_rows = np.empty(0, dtype=np.int64)
        xyz = np.indices(self.shape).reshape(3, -1).T
        self.interior = np.all((xyz > 0) & (xyz < self.shape-1), axis=1)

    def embed(self, points):
        coordinate = (points-self.origin)/self.spacing
        cells = np.floor(coordinate).astype(int)
        fraction = coordinate-cells
        assert np.all(cells >= 0) and np.all(cells+1 < self.shape)
        ijk = cells[:, None, :]+CORNERS
        ids = np.ravel_multi_index(ijk.reshape(-1, 3).T, self.shape).reshape(-1, 8)
        weights = np.prod(np.where(CORNERS[None] == 1, fraction[:, None], 1-fraction[:, None]), axis=2)
        colors = (cells[:, 0] % 2)*4+(cells[:, 1] % 2)*2+cells[:, 2] % 2
        keys = np.ravel_multi_index(cells.T, self.shape)
        return ids, weights, keys, colors

    def evaluate(self, embedding):
        ids, weights = embedding[:2]
        return np.sum(self.values[ids]*weights[:, :, None], axis=1)

    def support(self, embedding, unsafe, seeds):
        """Full connected contact support; no original wall separation is used."""
        ids = embedding[0]
        occupied = np.zeros(self.count, bool); occupied[ids[unsafe].ravel()] = True
        start = np.unique(ids[unsafe & seeds])
        assert len(start), 'No measured arm contact seeds'
        graph = occupied.reshape(self.shape); active = np.zeros(self.shape, bool)
        queue = deque(map(tuple, np.array(np.unravel_index(start, self.shape)).T))
        for p in queue: active[p] = True
        while queue:
            p = queue.popleft()
            for k in range(3):
                for step in (-1, 1):
                    q = list(p); q[k] += step; q = tuple(q)
                    if 0 <= q[k] < self.shape[k] and graph[q] and not active[q]:
                        active[q] = True; queue.append(q)
        core = int(active.sum())
        # Three interpolation cells are the compact elastic transition, not an
        # immutable anatomical seam. All touched cloth is constrained afterward.
        for _ in range(3):
            following = active.copy()
            for k in range(3):
                lo = [slice(None)]*3; hi = lo.copy(); lo[k] = slice(None, -1); hi[k] = slice(1, None)
                following[tuple(lo)] |= active[tuple(hi)]; following[tuple(hi)] |= active[tuple(lo)]
            active = following
        self.active = active.ravel() & self.interior
        return {'contactCoreNodes': core, 'elasticSupportNodes': int(self.active.sum())}

    def smooth(self, fraction):
        d = self.values.reshape((*self.shape, 3)); sums = np.zeros_like(d); counts = np.zeros(self.shape)
        for k in range(3):
            lo = [slice(None)]*3; hi = lo.copy(); lo[k] = slice(None, -1); hi[k] = slice(1, None)
            sums[tuple(lo)] += d[tuple(hi)]; sums[tuple(hi)] += d[tuple(lo)]
            counts[tuple(lo)] += 1; counts[tuple(hi)] += 1
        average = (sums/np.maximum(counts[..., None], 1)).reshape(-1, 3)
        self.values[self.active] *= 1-fraction
        self.values[self.active] += fraction*average[self.active]
        self.values[~self.active] = 0

    def solve_planes(self, embedding, normal, lower, iterations=256):
        ids, weights, cells, colors = embedding
        weights = weights*self.active[ids]
        norm = np.sum(weights*weights, axis=1)
        current = np.sum(self.evaluate(embedding)*normal, axis=1)
        assert np.all((norm > 0) | (lower-current <= 1e-8)), 'Deficient constraint reached frozen field boundary'
        usable = norm > 0
        # Add the strongest current contact in each cell/direction octant.
        # Same-color cells have disjoint corner nodes, allowing exact simultaneous
        # row projections without duplicate-index writes. Previously active rows
        # remain active: replacing them would alternate which cloth point clips.
        # Dense contacts are remeasured by fit(), never passed by this subset.
        octants = (normal[:, 0] >= 0)*4+(normal[:, 1] >= 0)*2+(normal[:, 2] >= 0)
        bins = cells*8+octants
        order = np.lexsort((-(lower-current), bins))
        order = order[usable[order]]
        _, first = np.unique(bins[order], return_index=True)
        rows = np.union1d(order[first], self.contact_rows)
        self.contact_rows = rows
        rows = rows[np.argsort(cells[rows], kind='stable')]
        offsets = np.arange(len(rows)); starts = np.r_[True, np.diff(cells[rows]) != 0]
        rank = offsets-np.maximum.accumulate(np.where(starts, offsets, 0))
        groups = [rows[(colors[rows] == color) & (rank == index)]
                  for color in range(8) for index in range(int(rank.max())+1)]
        for iteration in range(iterations):
            if iteration < iterations-64: self.smooth(.025)
            for chosen in groups:
                if not len(chosen): continue
                jj, ww, nn = ids[chosen], weights[chosen], normal[chosen]
                position = np.sum(self.values[jj]*ww[:, :, None], axis=1)
                lack = np.maximum(lower[chosen]-np.sum(position*nn, axis=1), 0)
                change = (lack/norm[chosen])[:, None, None]*ww[:, :, None]*nn[:, None, :]
                self.values[jj.ravel()] += change.reshape(-1, 3)
            if iteration >= iterations-64 and iteration % 8 == 7:
                deficit = lower[rows]-np.sum(self.evaluate(embedding)[rows]*normal[rows], axis=1)
                if float(deficit.max()) <= .00001: break
        return {'constraintRows': len(rows), 'iterations': iteration+1,
                'subsetMaximumDeficitM': float(np.max(lower[rows]-np.sum(self.evaluate(embedding)[rows]*normal[rows], axis=1)))}

    def jacobian_bound(self):
        """A global analytic Lipschitz bound, not a few sampled determinants.

Each trilinear partial derivative is a convex combination of four corner
edge slopes. Bounds on its nine entries give an upper bound on the operator
norm everywhere. A bound below one makes I+d globally injective, since d is
zero outside the padded field. The triangle approximation still needs a gate.
"""
        d = self.values.reshape((*self.shape, 3))
        bounds = np.zeros((*tuple(self.shape-1), 3, 3))
        for k in range(3):
            slopes = abs(np.diff(d, axis=k)/self.spacing)
            for other in range(3):
                if other == k: continue
                lo = [slice(None)]*3; hi = lo.copy(); lo[other] = slice(None, -1); hi[other] = slice(1, None)
                slopes = np.maximum(slopes[tuple(lo)], slopes[tuple(hi)])
            bounds[..., :, k] = slopes
        norms = np.linalg.norm(bounds, axis=(-2, -1))
        witness = np.unravel_index(np.argmax(norms), norms.shape)
        bound = float(norms[witness])
        return {'worstCellDisplacementDerivativeEntryBounds': bounds[witness].tolist(),
                'worstCell': list(map(int, witness)),
                'globalDisplacementLipschitzUpperBound': bound,
                'globalMinimumSingularValueLowerBound': 1-bound,
                'positiveJacobianProvenForContinuousField': bool(bound < 1)}


def fit(points, triangles, arm_seeds, nearest, settings, progress):
    field = Field(points, settings['fieldCellM'])
    embedding = field.embed(points)
    # The constructor supplies only retained source triangles. Material already
    # scheduled for the explicit distal/inner-return deletion never drives fit.
    live = np.unique(triangles)
    gap = np.full(len(points), np.inf)
    gap[live], _ = nearest(points[live])
    target = settings['clothClearanceM']+settings['contactSolveMarginM']
    support = field.support(embedding, gap < target+settings['contactReserveM'], arm_seeds)
    touched = np.any(field.active[embedding[0]], axis=1)
    # Complete affected triangle corners and centroids join the constraint set.
    # The later exact triangle checks remain mandatory.
    face_ids = np.flatnonzero(np.any(touched[triangles], axis=1))
    unique = np.unique(triangles[face_ids]); centers = points[triangles[face_ids]].mean(1)
    samples = np.vstack((points[unique], centers))
    sample_embedding = field.embed(samples)
    history = []
    for step in range(settings['contactPasses']):
        displacement = field.evaluate(sample_embedding)
        actual = samples+displacement
        distance, direction = nearest(actual)
        minimum = float(distance.min())
        progress('volume contact '+str(step)+' min '+str(minimum))
        if minimum >= target-settings['numericalContactToleranceM']: break
        # Linearize the actual full-wearer distance at the current field value.
        lower = target-distance+np.sum(displacement*direction, axis=1)
        result = field.solve_planes(sample_embedding, direction, lower, settings['projectionIterations'])
        history.append(result)
    else:
        distance, _ = nearest(samples+field.evaluate(sample_embedding)); minimum = float(distance.min())
    jacobian = field.jacobian_bound()
    assert jacobian['globalDisplacementLipschitzUpperBound'] < settings['maximumDerivativeBound'], ('Continuous cloth field exceeded strain guard', jacobian)
    assert minimum >= target-settings['numericalContactToleranceM'], ('Complete contact sample set not enclosed', minimum, target)
    moved = points+field.evaluate(embedding)
    changed = np.flatnonzero(np.any(moved != points, axis=1))
    assert len(changed) and np.all(np.linalg.norm(moved[live]-points[live], axis=1) < settings['maximumDisplacementM']), 'Selected garment displacement exceeded artist guard'
    # A measured healthy source boundary consists of retained triangle vertices
    # adjacent to the complete field support, not an elbow/forearm cutoff plane.
    all_edges = np.unique(np.sort(np.concatenate((triangles[face_ids, :2], triangles[face_ids, 1:], triangles[face_ids][:, [2, 0]])), axis=1), axis=0)
    changed_mask = np.zeros(len(points), bool); changed_mask[changed] = True
    crossing = all_edges[changed_mask[all_edges[:, 0]] != changed_mask[all_edges[:, 1]]]
    fixed = np.unique(crossing[~changed_mask[crossing]])
    assert len(fixed), 'Complete cloth fit has no retained boundary witness'
    fixed_gap, _ = nearest(points[fixed])
    assert float(fixed_gap.min()) >= target-settings['numericalContactToleranceM'], ('Original retained boundary is unhealthy', float(fixed_gap.min()))
    report = {'method': 'One continuous shared volumetric displacement of selected outer and inner cloth; no independent sheets',
              'sampledActualFullWearerMinimumM': minimum, 'sourceBoundaryMinimumM': float(fixed_gap.min()),
              'sourceBoundaryVertices': len(fixed), 'changedSourceVertices': len(changed),
              'affectedOriginalTriangles': len(face_ids), 'fullConstraintSamples': len(samples),
              'maximumRetainedSourceDisplacementM': float(np.linalg.norm(moved[live]-points[live], axis=1).max()),
              'retainedSourceConstraintVertices': len(live),
              'support': support, 'jacobian': jacobian, 'contactIterations': history,
              'restOnly': True, 'poseEnclosurePassed': False}
    return moved, changed, field, report
