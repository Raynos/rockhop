"""Broad wearer-driven rest registration through shared injective maps.

Every sheet follows the same spatial function. Contact support is closed over
complete affected triangles before projecting; no deficient corner is frozen.
Large tailoring is explicit: the retired45mm repair cap is not used or passed.
"""
import numpy as np


def expand(mask, shape, rings):
    active = mask.reshape(shape).copy()
    for _ in range(rings):
        following = active.copy()
        for axis in range(3):
            lo = [slice(None)]*3; hi = lo.copy()
            lo[axis] = slice(None, -1); hi[axis] = slice(1, None)
            following[tuple(lo)] |= active[tuple(hi)]
            following[tuple(hi)] |= active[tuple(lo)]
        active = following
    return active.ravel()


def closed_support(helper, points, faces, seeds, nearest, settings, progress):
    field = helper.Field(points, settings['fieldCellM'])
    embedding = field.embed(points); live = np.unique(faces)
    gap = np.full(len(points), np.inf); gap[live], _ = nearest(points[live])
    target = settings['clothClearanceM']+settings['contactSolveMarginM']
    unsafe = gap < target+settings['contactReserveM']
    if not np.any(unsafe & seeds): return None, {'noSeedContact': True}
    initial = field.support(embedding, unsafe, seeds)
    additions = []
    # Monotone finite closure, not a cell-count or clearance sweep. Only actual
    # deficient constraints newly reached by the current support extend it.
    while True:
        touched = np.any(field.active[embedding[0]], axis=1)
        face_ids = np.flatnonzero(np.any(touched[faces], axis=1))
        unique = np.unique(faces[face_ids]); centers = points[faces[face_ids]].mean(1)
        samples = np.vstack((points[unique], centers)); sample_embedding = field.embed(samples)
        distance, normal = nearest(samples)
        ids, weights = sample_embedding[:2]
        norm = np.sum((weights*field.active[ids])**2, axis=1)
        frozen = (norm == 0) & (target-distance > 1e-8)
        if not frozen.any(): break
        extra = np.zeros(field.count, bool); extra[ids[frozen].ravel()] = True
        extra = expand(extra, field.shape, 3) & field.interior
        before = int(field.active.sum()); field.active |= extra
        assert field.active.sum() > before, 'Actual deficient contact cannot acquire supported field nodes'
        additions.append({'frozenConstraints': int(frozen.sum()), 'addedNodes': int(field.active.sum())-before})
        progress('CLOSE actual contact frontier '+str(additions[-1]))
    return {'field': field, 'embedding': embedding, 'sampleEmbedding': sample_embedding,
            'samples': samples, 'distance': distance, 'normal': normal,
            'touched': touched, 'faceIds': face_ids, 'unique': unique}, {
        'initial': initial, 'closure': additions, 'activeNodes': int(field.active.sum()),
        'constraintVertices': len(unique), 'constraintCentroids': len(centers),
        'frozenDeficientConstraints': 0}


def jacobians(field, embedding, corners):
    """Exact trilinear I+Dd at input points, evaluated in bounded chunks."""
    ids, weights = embedding[:2]
    result = np.empty((len(ids), 3, 3), dtype=float)
    # Recover fractions from the partition weights; sum weights of corners
    # with bit1 is exactly that coordinate's barycentric fraction.
    for start in range(0, len(ids), 8192):
        end = start+8192; ww = weights[start:end]
        fraction = np.column_stack([ww[:, corners[:, k] == 1].sum(1) for k in range(3)])
        values = field.values[ids[start:end]]
        matrix = np.broadcast_to(np.eye(3), (len(values), 3, 3)).copy()
        for axis in range(3):
            derivative = np.broadcast_to(np.where(corners[:, axis] == 1, 1., -1.), ww.shape).copy()
            for other in range(3):
                if other != axis:
                    derivative *= np.where(corners[None, :, other] == 1,
                        fraction[:, None, other], 1-fraction[:, None, other])
            matrix[:, :, axis] += np.sum(values*derivative[:, :, None], axis=1)/field.spacing
        result[start:end] = matrix
    return result


def register(helper, source_points, triangles, arm_seeds, nearest, settings, progress):
    current = source_points.copy(); seeds = arm_seeds.copy()
    total_jacobian = np.broadcast_to(np.eye(3), (len(current), 3, 3)).copy()
    target = settings['clothClearanceM']+settings['contactSolveMarginM']
    history = []; fields = []; affected_faces = np.zeros(len(triangles), bool)
    minimum = float('inf')
    for step in range(settings['contactPasses']):
        state, support = closed_support(helper, current, triangles, seeds, nearest, settings, progress)
        if state is None: break
        affected_faces[state['faceIds']] = True
        minimum = float(state['distance'].min())
        progress('REGISTER proximal '+str(step)+' actual minimum '+str(minimum))
        if minimum >= target-settings['numericalContactToleranceM']: break
        field = state['field']
        solve = field.solve_planes(state['sampleEmbedding'], state['normal'],
                                   target-state['distance'], settings['projectionIterations'])
        proposed = field.jacobian_bound()
        bound = proposed['globalDisplacementLipschitzUpperBound']
        # One analytically determined continuation fraction. This changes no
        # contact target and tests no alternative geometric parameter.
        allowed = np.nextafter(settings['maximumDerivativeBound'], 0.)
        fraction = min(1., allowed/bound) if bound else 1.
        field.values *= fraction
        certificate = field.jacobian_bound()
        # Recomputed differences/norms can round one ulp upward. Normalize
        # that arithmetic against the same bound; no geometry is evaluated or
        # moved until the unchanged certificate limit is actually satisfied.
        while certificate['globalDisplacementLipschitzUpperBound'] > settings['maximumDerivativeBound']:
            correction = np.nextafter(settings['maximumDerivativeBound']/
                certificate['globalDisplacementLipschitzUpperBound'], 0.)
            field.values *= correction; fraction *= correction
            certificate = field.jacobian_bound()
        assert certificate['positiveJacobianProvenForContinuousField']
        step_jacobian = jacobians(field, state['embedding'], helper.CORNERS)
        total_jacobian = np.matmul(step_jacobian, total_jacobian)
        delta = field.evaluate(state['embedding'])
        assert np.any(delta), 'No broad registration progress'
        current += delta; seeds |= state['touched']
        fields.append(field)
        history.append({'step': step, 'beforeMinimumM': minimum, 'support': support,
                        'solve': solve, 'proposedDerivativeBound': bound,
                        'continuationFraction': fraction, 'certificate': certificate,
                        'maximumStepDisplacementM': float(np.linalg.norm(delta, axis=1).max())})
        # No detached scratch from earlier nearest/BVH queries survives a step.
        del state, step_jacobian, delta
    used = np.unique(triangles[affected_faces])
    assert len(used) and fields, 'No broad proximal rest tailoring was constructed'
    final_samples = np.vstack((current[used], current[triangles[affected_faces]].mean(1)))
    final_distance, _ = nearest(final_samples); minimum = float(final_distance.min())
    displacement = np.linalg.norm(current-source_points, axis=1)
    changed = np.flatnonzero(displacement > 0)
    # Boundary is measured on the actual retained triangle graph. New support
    # cannot silently freeze a deficient outer corner or centroid.
    touched = np.zeros(len(current), bool); touched[changed] = True
    frontier = triangles[np.any(touched[triangles], axis=1) & ~np.all(touched[triangles], axis=1)]
    fixed = np.unique(frontier[~touched[frontier]])
    assert len(fixed), 'No healthy retained chest/back/arm transition boundary remains'
    boundary_gap, _ = nearest(source_points[fixed])
    healthy_boundary = float(boundary_gap.min()) >= target-settings['numericalContactToleranceM']
    lower = float(np.prod([r['certificate']['globalMinimumSingularValueLowerBound'] for r in history]))
    upper = float(np.prod([1+r['certificate']['globalDisplacementLipschitzUpperBound'] for r in history]))
    report = {'method': 'Broad actual-wearer contact registration through composed shared injective spatial maps',
        'retired45mmRepairGateClaimed': False, 'constructionContactSamplesPassed': bool(
            minimum >= target-settings['numericalContactToleranceM'] and healthy_boundary),
        'finalActualFullWearerMinimumM': minimum, 'contactTargetM': target,
        'healthyRetainedBoundaryPassed': healthy_boundary, 'sourceBoundaryMinimumM': float(boundary_gap.min()),
        'sourceBoundaryVertices': len(fixed), 'changedSourceVertices': len(changed),
        'affectedOriginalTriangles': int(affected_faces.sum()), 'fullConstraintSamples': len(final_samples),
        'maximumOriginalSourceDisplacementM': float(displacement.max()),
        'sourceDisplacementPercentilesM': np.percentile(displacement[changed], [50, 90, 99, 100]).tolist(),
        'continuousMapInjectivityProven': all(r['certificate']['positiveJacobianProvenForContinuousField'] for r in history),
        'globalComposedMinimumSingularValueLowerBound': lower,
        'globalComposedMaximumSingularValueUpperBound': upper, 'registrationSteps': history,
        'restOnly': True, 'geometryGatesPassed': False, 'poseEnclosurePassed': False,
        'limits': ['Large source-shape change is explicit and requires played judgment.',
                   'Continuous-map injectivity does not prove piecewise-linear triangles avoid crossings.',
                   'Actual full triangle/self/body/glove checks and independent generic/bike motion remain mandatory.']}
    return current, total_jacobian, changed, fields, report
