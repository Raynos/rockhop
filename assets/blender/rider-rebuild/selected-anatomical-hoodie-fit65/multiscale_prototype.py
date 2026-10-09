"""Sparse two-scale C2 basis; fine spacing is the minimum actual wall span."""
import math
import runpy
from pathlib import Path
import numpy as np

BASE = runpy.run_path(str(Path(__file__).parent.parent/'selected-anatomical-hoodie-fit64/cage.py'))


class SparseLevel(BASE['Cage']):
    def __init__(self, points, spacing):
        self.spacing = float(spacing)
        self.origin = np.floor(points.min(0)/spacing)*spacing-4*spacing
        self.shape = np.ceil((points.max(0)-self.origin)/spacing).astype(int)+5
        self.active = np.empty(0, np.int64); self.values = np.empty((0, 3))

    def lookup(self, ids):
        at = np.searchsorted(self.active, ids); valid = at < len(self.active)
        at = np.minimum(at, len(self.active)-1)
        valid &= self.active[at] == ids
        return self.values[at]*valid[..., None]

    def evaluate(self, points, differential=False):
        moved = np.empty_like(points); jac = np.empty((len(points), 3, 3)) if differential else None
        for start in range(0, len(points), 4096):
            end = start+4096; ids, weights, gradients = self.embed(points[start:end])
            values = self.lookup(ids)
            moved[start:end] = points[start:end]+np.einsum('nk,nkj->nj', weights, values)
            if differential: jac[start:end] = np.eye(3)+np.einsum('nki,nkj->nij', values, gradients)
        return moved, jac

    def certificate(self):
        coordinates = np.asarray(np.unravel_index(self.active, self.shape)).T
        assert np.all(coordinates >= 3) and np.all(coordinates < self.shape-3)
        strides = [self.shape[1]*self.shape[2], self.shape[2], 1]
        bounds = []
        for stride in strides:
            starts = np.union1d(self.active, self.active-stride)
            difference = self.lookup(starts+stride)-self.lookup(starts)
            bounds.append(float(np.linalg.norm(difference, axis=1).max())/self.spacing)
        return bounds


class Multiscale:
    def __init__(self, points, spacings):
        self.levels = [SparseLevel(points, h) for h in spacings]

    def interpolate(self, controls, residual):
        matrices = []
        for level in self.levels:
            ids, weights, _ = level.embed(controls); level.active, inverse = np.unique(ids, return_inverse=True)
            matrix = np.zeros((len(controls), len(level.active)))
            np.add.at(matrix, (np.repeat(np.arange(len(controls)), 64), inverse.ravel()), weights.ravel())
            matrices.append(matrix)
        matrix = np.concatenate(matrices, axis=1)
        coefficients, _, rank, singular = np.linalg.lstsq(matrix, residual, rcond=None)
        error = float(np.linalg.norm(matrix@coefficients-residual, axis=1).max())
        at = 0
        for level in self.levels:
            level.values = coefficients[at:at+len(level.active)].copy(); at += len(level.active)
        return error, {'constraintRank': int(rank), 'constraintRows': len(controls),
            'smallestSingularValue': float(singular[-1]), 'largestSingularValue': float(singular[0]),
            'activeCoefficientCount': len(coefficients), 'spacingsM': [p.spacing for p in self.levels]}

    def scale(self, amount):
        for level in self.levels: level.values *= amount

    def certificate(self):
        per_level = [p.certificate() for p in self.levels]
        columns = np.sum(per_level, axis=0); upper = float(np.linalg.norm(columns))
        return {'basis': 'C2 tensor cubic B-spline', 'derivativeColumnUpperBounds': columns.tolist(),
            'globalDisplacementLipschitzUpperBound': upper,
            'globalMinimumSingularValueLowerBound': 1-upper,
            'positiveJacobianProvenForContinuousField': upper < 1,
            'compactC2ZeroExtensionProven': True, 'levelDerivativeColumnUpperBounds': per_level,
            'proof': 'Each sparse level has implicit zero coefficients and exact adjacent differences. Sum of per-level column bounds bounds the sum field; Frobenius bounds spectral norm.'}

    def evaluate(self, points, differential=False):
        moved = points.copy(); jac = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy() if differential else None
        for level in self.levels:
            step, derivative = level.evaluate(points, differential)
            moved += step-points
            if differential: jac += derivative-np.eye(3)
        return moved, jac


def fixed_targets(original, source_controls, targets, spacing, bound, progress, fine_spacing):
    assert 0 < fine_spacing < spacing
    current = source_controls.copy(); maps = []; history = []
    precision = float(np.spacing(np.float32(max(abs(targets).max(), 1.))))
    for iteration in range(64):
        residual = targets-current; error = float(np.linalg.norm(residual, axis=1).max())
        if error <= precision: break
        cage = Multiscale(np.vstack((original.min(0), original.max(0), current, targets)), [spacing, fine_spacing])
        interpolation_error, system = cage.interpolate(current, residual)
        assert interpolation_error <= precision, ('Fixed controls not interpolated', interpolation_error, system)
        proposed = cage.certificate()['globalDisplacementLipschitzUpperBound']
        fraction = min(1., np.nextafter(bound, 0.)/proposed) if proposed else 1.
        cage.scale(fraction); certificate = cage.certificate()
        while certificate['globalDisplacementLipschitzUpperBound'] > bound:
            correction = np.nextafter(bound/certificate['globalDisplacementLipschitzUpperBound'], 0.)
            cage.scale(correction); fraction *= correction; certificate = cage.certificate()
        current, _ = cage.evaluate(current); maps.append(cage)
        history.append({'step': iteration, 'endpointResidualBeforeM': error, 'continuationFraction': fraction,
            'certificate': certificate, 'linearSystem': system, 'interpolationResidualM': interpolation_error})
        progress('C2 sparse65 endpoint '+str(iteration)+' residual '+str(error)+' fraction '+str(fraction))
    final = float(np.linalg.norm(targets-current, axis=1).max())
    assert final <= precision, ('Fixed anatomical endpoints not reached', final)
    moved = original.copy(); differential = np.broadcast_to(np.eye(3), (len(moved), 3, 3)).copy()
    for i, cage in enumerate(maps):
        moved, step = cage.evaluate(moved, True); differential = np.matmul(step, differential)
        progress('CARRY original paired cloth through sparse C2 map '+str(i))
    return moved, differential, maps, {'maximumEndpointResidualM': final, 'nativeCoordinatePrecisionM': precision,
        'endpointCorrespondencePassed': True, 'continuousMapInjectivityProven': True,
        'fixedEndpointControls': len(targets), 'steps': history,
        'globalComposedMinimumSingularValueLowerBound': math.prod(r['certificate']['globalMinimumSingularValueLowerBound'] for r in history),
        'geometryGatesPassed': False, 'movingReviewPassed': False}
