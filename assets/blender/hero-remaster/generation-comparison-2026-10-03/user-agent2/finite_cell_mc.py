"""Owned extraction derivative: never interpolate a cell with missing corners."""
import numpy as np
from skimage import measure


def finite_cell_mask(volume, level=0.0, evaluated=None):
    """skimage's step_size=1 mask addresses each cell at its upper corner."""
    assert volume.ndim == 3 and min(volume.shape) >= 2
    finite = np.isfinite(volume)
    if evaluated is not None:
        assert evaluated.shape == volume.shape and evaluated.dtype == np.bool_
        assert finite[evaluated].all(), 'Nonfinite explicitly evaluated neural sample'
        finite &= evaluated
    valid = np.ones(tuple(n - 1 for n in volume.shape), dtype=bool)
    below = np.zeros_like(valid)
    above = np.zeros_like(valid)
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                part = volume[x:x + valid.shape[0], y:y + valid.shape[1],
                              z:z + valid.shape[2]]
                valid &= finite[x:x + valid.shape[0], y:y + valid.shape[1],
                                z:z + valid.shape[2]]
                below |= part < level
                above |= part >= level
    crossing = valid & below & above
    mask = np.zeros(volume.shape, dtype=bool)
    mask[1:, 1:, 1:] = valid
    return mask, {'finiteSamples': int(finite.sum()),
                  'missingSamples': int((~finite).sum()),
                  'finiteCells': int(valid.sum()),
                  'finiteCrossingCells': int(crossing.sum())}


def extract(volume, level=0.0, evaluated=None):
    """Return grid-coordinate geometry without filling NaNs or mesh cleanup."""
    mask, counts = finite_cell_mask(volume, level, evaluated)
    if not counts['finiteCrossingCells']:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.int32), counts
    vertices, faces, _, _ = measure.marching_cubes(
        volume, level, method='lewiner', mask=mask, step_size=1)
    assert np.isfinite(vertices).all(), 'Finite-cell extraction produced nonfinite vertices'
    return vertices, faces, counts
