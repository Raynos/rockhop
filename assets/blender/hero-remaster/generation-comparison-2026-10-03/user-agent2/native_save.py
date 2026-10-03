"""Save decoded arrays without lossy dtype conversion or display processing."""
import hashlib
import json
from pathlib import Path

import numpy as np


def array(value):
    if hasattr(value, 'detach'):
        value = value.detach().cpu().numpy()
    return np.array(value, copy=True)


def save_native(mesh, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / 'native.npz'
    receipt = output / 'native.json'
    if archive.exists() or receipt.exists():
        raise FileExistsError('Native checkpoint must be fresh')
    arrays = {key: array(getattr(mesh, key)) for key in
              ('vertices', 'faces', 'attrs', 'coords')}
    for key in ('origin', 'fdg_coords', 'fdg_dual_vertices',
                'fdg_intersected', 'fdg_split_weight'):
        value = getattr(mesh, key, None)
        if value is not None:
            arrays[key] = array(value)
    # Geometry validation follows persistence so invalid decoder output survives.
    np.savez_compressed(archive, **arrays)
    fingerprints = {key: {'dtype': str(value.dtype), 'shape': list(value.shape),
                          'sha256CBytes': hashlib.sha256(value.tobytes(order='C')).hexdigest()}
                    for key, value in arrays.items()}
    report = {'schemaVersion': 1, 'accepted': False,
              'definition': 'decoded arrays, copied to CPU without dtype conversion',
              'archiveSHA256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'arrays': fingerprints, 'voxelSize': float(mesh.voxel_size),
              'layout': {key: [span.start, span.stop, span.step]
                         for key, span in mesh.layout.items()},
              'cleanup': False, 'reduction': False, 'exportRotation': False}
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    with np.load(archive, allow_pickle=False) as saved:
        for key, original in arrays.items():
            if saved[key].dtype != original.dtype or saved[key].shape != original.shape:
                raise ValueError('Native checkpoint changed dtype or shape: ' + key)
            if saved[key].tobytes(order='C') != original.tobytes(order='C'):
                raise ValueError('Native checkpoint changed bytes: ' + key)
    return report
