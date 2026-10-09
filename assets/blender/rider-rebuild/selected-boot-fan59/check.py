"""Meaningful exact-fan retention mutations; no construction or Blender."""
import copy
import json

import numpy as np

import diagnose as diagnosis

report, certificate, source, current = diagnosis.diagnose()
assert not diagnosis.retention(certificate, current)['passed']
original = np.asarray(certificate['lockedOriginalVertexIds'], dtype=np.uint32)
inverse = {int(v): i for i, v in enumerate(original)}
fixture = {'originalVertexIds': original,
    'positions': source['positions'].reshape(-1, 3)[original].copy(),
    'namedWeights': source['namedWeights'].reshape(-1, 3)[original].copy(),
    'triangles': np.array([[inverse[v] for v in face] for face in certificate['requiredOrientedTrianglesOriginal']], dtype=np.int32)}
assert diagnosis.retention(certificate, fixture)['passed']
cyclic = copy.deepcopy(fixture); cyclic['triangles'] = np.roll(cyclic['triangles'], 1, axis=1)
assert diagnosis.retention(certificate, cyclic)['passed']
for label in ['delete face', 'reverse face', 'add center face', 'move vertex', 'change field']:
    changed = copy.deepcopy(fixture)
    if label == 'delete face': changed['triangles'] = changed['triangles'][1:]
    if label == 'reverse face': changed['triangles'][0] = changed['triangles'][0, ::-1]
    if label == 'add center face': changed['triangles'] = np.vstack([changed['triangles'], [inverse[80837], inverse[80674], inverse[81373]]])
    if label == 'move vertex': changed['positions'][0, 0] += 1e-6
    if label == 'change field': changed['namedWeights'][0, 0] = .9
    assert not diagnosis.retention(certificate, changed)['passed'], label
checks = ['Actual candidate fails exact fan retention: six vertices and all seven source faces absent',
          'Exact source fan patch passes; cyclic corner order passes without reversing winding',
          'Deleted, reversed or added center faces fail; moved positions and altered named fields fail']
out = diagnosis.ROOT/'docs/evidence/rider-rebuild/selected-boot-fan59'
out.mkdir(parents=True, exist_ok=True)
(out/'fixtures.json').write_text(json.dumps({'status': 'CPU_RETENTION_FIXTURES_PASSED_UNACCEPTED',
    'checks': checks, 'limits': 'The passing patch is a bounded source-fan fixture, never a new production candidate.'}, indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
