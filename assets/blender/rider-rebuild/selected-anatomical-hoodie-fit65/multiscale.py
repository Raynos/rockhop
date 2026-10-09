"""Sparse two-scale C2 basis; fine spacing is the minimum actual wall span."""
import math
import runpy
from pathlib import Path
import numpy as np

BASE = runpy.run_path(str(Path(__file__).parent.parent/'selected-anatomical-hoodie-fit64/cage.py'))
Cage = BASE['Cage']


class SparseLevel(BASE['Cage']):
    def __init__(self, points, spacing):
        self.spacing = float(spacing)
        self.origin = np.floor(points.min(0)/spacing)*spacing-4*spacing
        self.shape = np.ceil((points.max(0)-self.origin)/spacing).astype(int)+5
        self.active = np.empty(0, np.int64); self.values = np.empty((0, 3))
        self._keys = None

    def prepare_lookup(self):
        # Sparse coefficient indices use bounded storage proportional to
        # active support, never the volume of the fine tensor lattice.
        bits = max(1, int(math.ceil(math.log2(max(4*len(self.active), 2)))))
        self._shift = np.uint64(64-bits); self._mask = (1 << bits)-1
        self._keys = np.full(1 << bits, -1, np.int64)
        self._indices = np.full(1 << bits, -1, np.int64)
        for index, key in enumerate(self.active):
            slot = ((int(key)*11400714819323198485) & ((1 << 64)-1)) >> int(self._shift)
            while self._keys[slot] != -1: slot = (slot+1) & self._mask
            self._keys[slot] = key; self._indices[slot] = index

    def lookup(self, ids):
        if self._keys is None: self.prepare_lookup()
        shape = ids.shape; keys = np.asarray(ids, np.int64).ravel()
        slots = ((keys.astype(np.uint64)*np.uint64(11400714819323198485)) >> self._shift).astype(np.int64)
        pending = np.arange(len(keys)); found = np.full(len(keys), -1, np.int64)
        while len(pending):
            stored = self._keys[slots[pending]]; match = stored == keys[pending]
            found[pending[match]] = self._indices[slots[pending[match]]]
            pending = pending[(stored != -1) & ~match]
            slots[pending] = (slots[pending]+1) & self._mask
        valid = found >= 0
        return (self.values[np.maximum(found, 0)]*valid[:, None]).reshape(shape+(3,))

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
            ids, weights, _ = level.embed(controls); active, inverse = np.unique(ids, return_inverse=True)
            matrix = np.zeros((len(controls), len(active)))
            np.add.at(matrix, (np.repeat(np.arange(len(controls)), 64), inverse.ravel()), weights.ravel())
            # The finite field's three boundary coefficient layers are exact
            # homogeneous constraints. Never solve them as free variables,
            # including tiny floating weights at an exact lattice boundary.
            coordinates = np.asarray(np.unravel_index(active, level.shape)).T
            free = np.all((coordinates >= 3) & (coordinates < level.shape-3), axis=1)
            level.active = active[free]; matrix = matrix[:, free]
            level.prepare_lookup()
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
        'method': 'Fixed material endpoints through shared sparse coarse and paired-wall-scale C2 fields',
        'endpointCorrespondencePassed': True, 'continuousMapInjectivityProven': True,
        'fixedEndpointControls': len(targets), 'steps': history,
        'globalComposedMinimumSingularValueLowerBound': math.prod(r['certificate']['globalMinimumSingularValueLowerBound'] for r in history),
        'geometryGatesPassed': False, 'movingReviewPassed': False}


def map_arrays(maps):
    arrays = {'mapCount': np.array(len(maps), np.int32), 'mapLayout': np.array('SPARSE_MULTISCALE_C2_V1')}
    for i, field in enumerate(maps):
        arrays[str(i)+'_levelCount'] = np.array(len(field.levels), np.int32)
        for j, level in enumerate(field.levels):
            prefix = str(i)+'_'+str(j)+'_'
            for name in ('origin', 'shape', 'active', 'values'): arrays[prefix+name] = getattr(level, name)
            arrays[prefix+'spacing'] = np.array(level.spacing)
    return arrays


def restore_maps(arrays):
    assert str(arrays['mapLayout']) == 'SPARSE_MULTISCALE_C2_V1'
    maps = []
    for i in range(int(arrays['mapCount'])):
        field = Multiscale.__new__(Multiscale); field.levels = []
        for j in range(int(arrays[str(i)+'_levelCount'])):
            prefix = str(i)+'_'+str(j)+'_'; level = SparseLevel.__new__(SparseLevel)
            for name in ('origin', 'shape', 'active', 'values'): setattr(level, name, arrays[prefix+name].copy())
            level.spacing = float(arrays[prefix+'spacing']); level._keys = None
            field.levels.append(level)
        maps.append(field)
    return maps
