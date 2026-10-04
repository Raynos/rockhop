"""Classify archived starting crossings against scope and old tangent DOFs."""
import json
from pathlib import Path
import numpy as np
root = Path(__file__).resolve().parents[6]
ev = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = ev / 'neck-interface103'
r = json.loads((out / 'path-samples.json').read_text())
w = np.load(ev / 'neck-interface102/solve-witnesses.npz')
a = np.load(out / 'path-geometry-and-candidates.npz')
f = np.load(ev / 'neck-interface102/candidate-fields-ancestry-corrected.npz')
nb = len(f['bodyRestXYZ'])
mapping = a['rawPhysicalMap']
triangles = {'body': mapping[:nb][a['bodyReferenceTriangles']],
             'head': mapping[nb:][a['headReferenceTriangles']]}
free = w['freePhysicalNodes']
dof = np.zeros(len(a['P0']), dtype=int)
dof[free] = np.bincount(w['variableOwner'], minlength=len(free))
fixed = set(w['fixedPhysicalNodes'].tolist())
result = {}
for name, (left, right) in {'bodySelf': ('body', 'body'),
                          'headSelf': ('head', 'head'),
                          'bodyHead': ('body', 'head')}.items():
    rows = []
    for i, j in r['startingReferenceProperPairs'][name]:
        nodes = np.r_[triangles[left][i], triangles[right][j]]
        rows.append({'triangleIDs': [i, j], 'physicalNodeIDs': nodes.tolist(),
                     'allScopePinned': all(int(n) in fixed for n in nodes),
                     'allArchivedTangentZeroDOF': bool((dof[nodes] == 0).all()),
                     'tangentDOFByCorner': dof[nodes].tolist()})
    result[name] = {'pairs': len(rows),
                    'allScopePinnedPairs': sum(x['allScopePinned'] for x in rows),
                    'allArchivedTangentZeroDOFPairs': sum(x['allArchivedTangentZeroDOF'] for x in rows),
                    'rows': rows}
path = out / 'starting-contact-constraints.json'
assert result == json.loads(path.read_text()), 'Archived starting classification differs'
print(json.dumps({k: {a: b for a, b in v.items() if a != 'rows'} for k, v in result.items()}))
