"""Synthetic byte-preservation check; no model import or GPU allocation."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from native_save import save_native

parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True)
args = parser.parse_args()
output = Path(args.out)
attrs = np.array([[0.123456789, 0.99999994, -0.33333334]], dtype=np.float32)
mesh = SimpleNamespace(vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32),
                       faces=np.array([[0, 1, 2]], dtype=np.int64), attrs=attrs,
                       coords=np.array([[1, 2, 3]], dtype=np.int32), voxel_size=0.125,
                       layout={'albedo': slice(0, 3)})
receipt = save_native(mesh, output / 'finite')
legacy = attrs.astype(np.float16).astype(np.float32)
assert not np.array_equal(legacy, attrs), 'Fixture must expose old lossy save'
try:
    save_native(mesh, output / 'finite')
except FileExistsError:
    overwrite_refused = True
else:
    raise AssertionError('Checkpoint overwrite was allowed')
mesh.vertices[1, 0] = np.nan
save_native(mesh, output / 'invalid')
with np.load(output / 'invalid/native.npz', allow_pickle=False) as saved:
    assert np.isnan(saved['vertices'][1, 0]), 'Invalid raw sample was lost'
report = {'accepted': False, 'inferenceExecuted': False,
          'finiteArraysByteIdentical': True, 'faceDtypePreserved': receipt['arrays']['faces']['dtype'],
          'attributeDtypePreserved': receipt['arrays']['attrs']['dtype'],
          'legacyFloat16MaxError': float(np.abs(legacy - attrs).max()),
          'overwriteRefused': overwrite_refused, 'invalidRawRetained': True,
          'limit': 'Synthetic NumPy mesh only; no model/runtime/fit pass'}
(output / 'check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
