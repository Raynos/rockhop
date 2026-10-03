"""Analytic colour-gradient and sparse-support checks; no model input consumed."""
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from sample_native_attrs import sample

coords = np.array(list(itertools.product((0, 1), repeat=3)), dtype=np.int32)
centres = coords + .5
attrs = np.column_stack([centres, np.ones(8), centres[:, 0] * 2 + centres[:, 2]])
queries = np.array([[.5, .5, .5], [1, 1, 1], [.75, 1.2, 1.4], [1.5, 1.5, 1.5]])
expected = np.column_stack([queries, np.ones(4), queries[:, 0] * 2 + queries[:, 2]])
values, support = sample(attrs, coords, queries, chunk_size=2)
error = float(np.max(np.abs(values - expected)))
assert error < 1e-6 and np.allclose(support, 1)
permutation = np.array([7, 0, 5, 2, 6, 1, 4, 3])
shuffled, shuffled_support = sample(attrs[permutation], coords[permutation], queries)
assert np.array_equal(values, shuffled) and np.array_equal(support, shuffled_support)
# One known sample at cube centre contributes1/8. Renormalize that colour,
# retaining1/8 support rather than inventing the missing7/8 field.
sparse, sparse_support = sample(attrs[:1], coords[:1], np.array([[1, 1, 1], [20, 20, 20]]))
assert np.array_equal(sparse[0], attrs[0]) and sparse_support[0] == .125
assert np.all(sparse[1] == 0) and sparse_support[1] == 0
rejected = False
try:
    sample(attrs[[0, 0]], coords[[0, 0]], queries)
except ValueError:
    rejected = True
assert rejected
report = {'accepted': False, 'analyticLinearFieldMaxError': error,
          'shuffledVoxelRowsByteIdentical': True, 'partialSupport': .125,
          'outsideSupport': 0, 'duplicateVoxelRejected': True,
          'modelRuns': 0, 'realDonorsConsumed': 0,
          'limits': ['Analytic preparation only; no actual appearance or wearable acceptance'],
          'recipeSHA256': hashlib.sha256(Path(__file__).with_name('sample_native_attrs.py').read_bytes()).hexdigest()}
Path(sys.argv[1]).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
