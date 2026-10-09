"""Reconstruct the frozen connected cap and check its stored linear field.

No second field solve. This is recipe/native admission, never contact or art.
"""
import json
from pathlib import Path
import runpy

import numpy as np

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE/'author.py'))
pin, checked = A['pin'], A['checked']
CONSTRUCTION = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/connected_cap.py',
                'sha256': '3418b3172fbef6bac584d526bb72bd332878050ef473bf05320169096e2c743e'}


def verify(receipt_path):
    helper = runpy.run_path(str(checked(CONSTRUCTION)))
    row = helper['verify'](receipt_path)
    assert row['connectedCapBinding']['recipe'] == CONSTRUCTION
    prior, before, _, body, rest = helper['inputs']()
    expected, construction = helper['construct'](prior, before, body, rest)
    actual = np.load(checked(row['receiver']))
    assert set(actual.files) == set(expected)|{'namedFields'}
    for key, value in expected.items():
        assert np.array_equal(actual[key], value), ('Connected cap reconstruction', key)
    saved = json.loads(checked(row['construction']).read_text())
    for key, value in construction.items():
        # Canonical JSON converts authored tuples to arrays.
        assert saved[key] == json.loads(json.dumps(value)), ('Construction witness', key)
    assert saved['recipe'] == CONSTRUCTION and saved['input'] == helper['INPUT']
    assert saved['bodyGuide'] == helper['BODY'] and saved['linearField']['linearSolveCount'] == 1
    assert saved['sourceWallDomainsQualified'] is False and saved['genuineBakeAtlasPresent'] is False
    _, _, neighbors = runpy.run_path(str(checked(helper['GRAPH'])))['graph'](actual)
    fields = actual['namedFields'].astype(np.float64); maximum = 0.
    for i in np.flatnonzero(actual['fieldUnknown']):
        adjacent = neighbors[i]; total = sum(1/d for _, d in adjacent)
        mean = sum(fields[j]/d for j, d in adjacent)/total
        maximum = max(maximum, float(abs(fields[i]-mean).max()))
    # Stored float32 values have roundoff after the single float64 solve.
    # This dimensionless equation residual is not a geometry acceptance bound.
    assert maximum < 3e-7, ('Stored field is not the constructed harmonic extension', maximum)
    for side, sign in (('L', 1), ('R', -1)):
        allowed = set(helper['TRUNK'])|{'DEF-shoulder.'+side}|{
            'DEF-'+part+'.'+side+suffix for part in ('upper_arm', 'forearm') for suffix in ('', '.001')}
        forbidden = [i for i, n in enumerate(actual['groupNames']) if n not in allowed]
        assert np.all(fields[np.ix_(np.flatnonzero(actual['positions'][:, 0]*sign > 0), forbidden)] == 0)
    return row
