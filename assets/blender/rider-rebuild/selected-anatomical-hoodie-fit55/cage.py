"""C2 cubic B-spline cage carrying fixed material correspondences together.

Continuation follows one fixed endpoint constraint set. It never queries body
nearest points or chooses new anatomical destinations during deformation.
"""
import math
import numpy as np

OFFSETS = np.array(np.meshgrid(np.arange(4), np.arange(4), np.arange(4), indexing='ij')).reshape(3, -1).T


def basis(t):
    weights = np.stack(((1-t)**3, 3*t**3-6*t*t+4, -3*t**3+3*t*t+3*t+1, t**3), axis=-1)/6
    derivatives = np.stack((-3*(1-t)**2, 9*t*t-12*t, -9*t*t+6*t+3, 3*t*t), axis=-1)/6
    return weights, derivatives


class Cage:
    def __init__(self, points, spacing):
        self.spacing = float(spacing)
        self.origin = np.floor(points.min(0)/spacing)*spacing-4*spacing
        self.shape = np.ceil((points.max(0)-self.origin)/spacing).astype(int)+5
        self.count = int(np.prod(self.shape)); self.values = np.zeros((self.count, 3))

    def embed(self, points):
        q = (points-self.origin)/self.spacing; cell = np.floor(q).astype(int)
        nodes = cell[:, None, :]+OFFSETS[None, :, :]-1
        assert np.all(nodes >= 0) and np.all(nodes < self.shape)
        ids = np.ravel_multi_index(nodes.transpose(2, 0, 1), self.shape)
        w, dw = basis(q-cell)
        weights = np.prod(np.stack([w[:, a, OFFSETS[:, a]] for a in range(3)]), axis=0)
        gradients = np.empty((len(points), 64, 3))
        for axis in range(3):
            gradients[:, :, axis] = np.prod(np.stack([
                (dw if a == axis else w)[:, a, OFFSETS[:, a]] for a in range(3)]), axis=0)/self.spacing
        return ids, weights, gradients

    def evaluate(self, points, differential=False):
        moved = np.empty_like(points); jac = np.empty((len(points), 3, 3)) if differential else None
        for start in range(0, len(points), 4096):
            end = start+4096; ids, weights, gradients = self.embed(points[start:end])
            values = self.values[ids]
            moved[start:end] = points[start:end]+np.einsum('nk,nkj->nj', weights, values)
            if differential:
                jac[start:end] = np.eye(3)+np.einsum('nki,nkj->nij', values, gradients)
        return moved, jac

    def certificate(self):
        grid = self.values.reshape(tuple(self.shape)+(3,))
        # Three zero coefficient layers provide a C2 zero extension outside
        # the finite lattice. The derivative proof therefore covers R^3.
        for axis in range(3):
            assert not np.any(np.take(grid, [0, 1, 2, -3, -2, -1], axis=axis))
        bounds = [float(np.linalg.norm(np.diff(grid, axis=a), axis=-1).max())/self.spacing for a in range(3)]
        upper = float(np.linalg.norm(bounds))
        return {'basis': 'C2 tensor cubic B-spline', 'derivativeColumnUpperBounds': bounds,
            'globalDisplacementLipschitzUpperBound': upper,
            'globalMinimumSingularValueLowerBound': 1-upper,
            'positiveJacobianProvenForContinuousField': upper < 1,
            'compactC2ZeroExtensionProven': True,
            'proof': 'Derivative is a convex combination of adjacent coefficient differences; Frobenius bounds spectral norm.'}


def fixed_targets(original, source_controls, targets, spacing, bound, progress):
    assert source_controls.shape == targets.shape and len(source_controls) >= 4
    current = source_controls.copy(); maps = []; history = []
    precision = float(np.spacing(np.float32(max(abs(targets).max(), 1.))))
    # A finite numerical integration ceiling, not a geometric parameter sweep.
    for iteration in range(64):
        residual = targets-current; error = float(np.linalg.norm(residual, axis=1).max())
        if error <= precision: break
        cage = Cage(np.vstack((original.min(0), original.max(0), current, targets)), spacing)
        ids, weights, _ = cage.embed(current); unique, inverse = np.unique(ids, return_inverse=True)
        matrix = np.zeros((len(current), len(unique)))
        np.add.at(matrix, (np.repeat(np.arange(len(current)), 64), inverse.ravel()), weights.ravel())
        gram = matrix@matrix.T
        # Exact endpoint interpolation to floating-point precision. No penalty
        # or source-art weight can silently relax anatomical correspondence.
        solution = np.linalg.lstsq(gram, residual, rcond=None)[0]
        coefficients = matrix.T@solution
        interpolation_error = float(np.linalg.norm(matrix@coefficients-residual, axis=1).max())
        assert interpolation_error <= precision, ('Cage controls conflict at native precision', interpolation_error)
        cage.values[unique] = coefficients
        proposed = cage.certificate()['globalDisplacementLipschitzUpperBound']
        fraction = min(1., np.nextafter(bound, 0.)/proposed) if proposed else 1.
        cage.values *= fraction
        certificate = cage.certificate()
        while certificate['globalDisplacementLipschitzUpperBound'] > bound:
            correction = np.nextafter(bound/certificate['globalDisplacementLipschitzUpperBound'], 0.)
            cage.values *= correction; fraction *= correction; certificate = cage.certificate()
        assert certificate['positiveJacobianProvenForContinuousField']
        current, _ = cage.evaluate(current)
        maps.append(cage); history.append({'step': iteration, 'endpointResidualBeforeM': error,
            'continuationFraction': fraction, 'certificate': certificate})
        progress('C2 anatomical55 fixed endpoint '+str(iteration)+' residual '+str(error))
    final_error = float(np.linalg.norm(targets-current, axis=1).max())
    assert final_error <= precision, ('Fixed anatomical endpoints not reached', final_error)
    moved = original.copy(); differential = np.broadcast_to(np.eye(3), (len(moved), 3, 3)).copy()
    for index, cage in enumerate(maps):
        moved, step = cage.evaluate(moved, True); differential = np.matmul(step, differential)
        progress('CARRY original paired cloth through C2 map '+str(index))
    return moved, differential, maps, {'method': 'Fixed ordered anatomical material controls through one composed C2 shared cage',
        'fixedEndpointControls': len(targets), 'maximumEndpointResidualM': final_error,
        'nativeCoordinatePrecisionM': precision, 'endpointCorrespondencePassed': final_error <= precision,
        'continuousMapInjectivityProven': True, 'steps': history,
        'globalComposedMinimumSingularValueLowerBound': math.prod(r['certificate']['globalMinimumSingularValueLowerBound'] for r in history),
        'geometryGatesPassed': False, 'movingReviewPassed': False}
