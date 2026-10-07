"""Independent exact-bit UV corner graph against the measured atlas witnesses."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02'
directory, output = [Path(arg).resolve() for arg in sys.argv[1:]]
assert not output.exists()
report = json.loads((directory / 'measurements.json').read_text())
witness = np.load(directory / 'witnesses.npz')
assert hashlib.sha256((directory / 'witnesses.npz').read_bytes()).hexdigest() == report['witnessesSHA256']
checks = {}
for item in ('jeans', 'boots'):
    original = dict(np.load(PREP / item / 'cleaned-donor.npz'))
    f, uv = original['faces'], original['originalCornerUV']
    # An atlas corner is identified by BOTH geometric point and exact UV bits.
    # This independently models the duplicated vertices required by a UV seam.
    keys = np.column_stack([f.reshape(-1), uv.reshape(-1, 2).view(np.uint32)]).astype(np.int64)
    _, indices = np.unique(keys, axis=0, return_inverse=True)
    faces = indices.reshape(-1, 3)
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    edges.sort(axis=1)
    owners = np.tile(np.arange(len(f)), 3)
    packed = edges[:, 0] * (int(indices.max()) + 1) + edges[:, 1]
    order = np.argsort(packed, kind='stable')
    starts = np.r_[0, np.flatnonzero(np.diff(packed[order])) + 1]
    lengths = np.diff(np.r_[starts, len(order)])
    starts = starts[lengths == 2]
    a, b = owners[order[starts]], owners[order[starts+1]]
    graph = coo_matrix((np.ones(len(a), dtype=np.uint8), (a,b)), shape=(len(f), len(f))).tocsr()
    count, labels = connected_components(graph, directed=False)
    corners = labels[witness[item + '_corner_source_faces']]
    mixed = np.any(corners != corners[:, :1], axis=1)
    primary = witness[item + '_corner_source_charts']
    primary_mixed = np.any(primary != primary[:, :1], axis=1)
    assert np.array_equal(mixed, primary_mixed), 'Exact-bit and tolerant geometric-edge charts disagree'
    assert int(mixed.sum()) == report['items'][item]['compactFacesWhoseCornersBorrowDifferentUVCharts']
    assert int(count) == report['items'][item]['denseUVChartTopology']['connectedUVCharts']
    checks[item] = {'independentExactBitUVCharts': int(count), 'mixedCompactFaces': int(mixed.sum()),
                    'exactAndToleranceChartsAgreeOnEveryCompactFace': True,
                    'method': 'UV-seam duplicated corner-vertex identities; shared atlas edges; independent graph components'}
result = {'accepted': False, 'kind': 'Independent atlas connectivity witness verification',
          'validatorSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'measurementSHA256': hashlib.sha256((directory / 'measurements.json').read_bytes()).hexdigest(),
          'items': checks, 'limits': ['Boot ancestry measures source-risk only, not executed boot UV.',
                                     'No visual acceptance or source mutation.']}
output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
