"""Separate collapsed self-edge flags from real donor winding defects."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop')
MASTERS = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182')
E = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/ship183'
E.mkdir(parents=True, exist_ok=True)
data = np.load(MASTERS / 'bodydata01.npz')
positions, faces, offset = [], [], 0
for pk, fk in [('p0', 'f0'), ('p1', 'f1'), ('p2', 'f2'), ('newShellP', 'newShellF')]:
    positions.append(data[pk])
    faces.append(data[fk].astype(np.int64) + offset)
    offset += len(data[pk])
p, inverse = np.unique(np.concatenate(positions), axis=0, return_inverse=True)
f = inverse[np.concatenate(faces)]
edges = defaultdict(list)
for row in f:
    for a, b in zip(row, np.roll(row, -1)):
        edges[tuple(sorted((int(a), int(b))))].append(bool(a < b))
bad = [e for e, d in edges.items() if len(d) == 2 and d[0] == d[1]]
over = [e for e, d in edges.items() if len(d) > 2]
result = {'status': 'REJECTED_COUNTS_CLARIFIED_NO_REPAIR',
          'bodydataSHA256': hashlib.sha256((MASTERS / 'bodydata01.npz').read_bytes()).hexdigest(),
          'directionFlagsIncludingCollapsedSelfEdges': len(bad),
          'collapsedSelfEdgeDirectionFlags': sum(a == b for a, b in bad),
          'nonzeroWrongWindingEdges': sum(a != b for a, b in bad),
          'overIncidenceEdgesIncludingCollapsedSelfEdges': len(over),
          'nonzeroOverIncidenceEdges': sum(a != b for a, b in over),
          'activeMorphAccessorMismatch': {'sourceBaseRows': 22240, 'newBaseRows': 22559,
              'limits': 'Independent Q182 audit reports four unchanged active morph accessors. No runtime or repair acceptance.'},
          'limits': 'Frozen bodydata was independently matched to actual GLB in round182. This refines count definitions; no new asset, crossing or moving validation.'}
assert result['directionFlagsIncludingCollapsedSelfEdges'] == 486
assert result['collapsedSelfEdgeDirectionFlags'] == 25
assert result['nonzeroWrongWindingEdges'] == 461
assert result['overIncidenceEdgesIncludingCollapsedSelfEdges'] == 140
assert result['nonzeroOverIncidenceEdges'] == 120
(E / 'export-count-clarification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
