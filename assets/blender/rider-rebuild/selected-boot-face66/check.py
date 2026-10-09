"""CPU-only exhaustive actual63 evidence and numerical/mutation checks."""
import ast
import copy
import json
from pathlib import Path

import numpy as np

import diagnose as d

for path in Path(__file__).parent.glob('*.py'): ast.parse(path.read_text())
d.main()
report = json.loads((d.EVIDENCE/'finding.json').read_text())
receipt = json.loads(d.a.RECEIPT.read_text())
s = d.a.array_package(receipt['sourceArrayPackage']); c = d.a.array_package(receipt['candidate'])
with np.load(d.ROOT/report['sampleArrays']['path']) as package:
    z = {key: package[key] for key in package.files}
d.verify_report(report, s, c, z)
assert report['summary']['exactInheritedOrientedSourceFaces'] == 1
assert report['summary']['newFaces'] == 94
checks = ['All 26,528 native dot values reproduce exactly; all 95 failures classified as 1 inherited and 94 new faces']


def reject(fn, expected=''):
    try: fn()
    except AssertionError as error: assert expected in str(error), (expected, str(error))
    else: raise AssertionError('Mutation accepted: '+expected)


mutated = copy.deepcopy(report); mutated['failures'].pop()
reject(lambda: d.verify_report(mutated, s, c, z), 'Failure census incomplete')
mutated = copy.deepcopy(report); mutated['failures'][0]['nativeBearingSourceFaceId'] += 1
reject(lambda: d.verify_report(mutated, s, c, z), 'Actual native bearing changed')
mutated = copy.deepcopy(report); mutated['failures'][0]['exactSourceFaceId'] = 7055
reject(lambda: d.verify_report(mutated, s, c, z), 'False inherited-face claim')
mutated = copy.deepcopy(report); mutated['failures'][0]['nativeNormalDot'] = 1
reject(lambda: d.verify_report(mutated, s, c, z))
mutated = copy.deepcopy(report); mutated['proposedConstructionConstraint']['requestedOriginalFanCenters'].pop()
reject(lambda: d.verify_report(mutated, s, c, z), 'Not all target and bearing fans retained')
checks.append('Missing failure, changed actual bearing/dot, invented inheritance and omitted fan-center mutations reject')

triangle = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
for scale in [1., 1e-3, 1e-6]:
    interior = d.closest(np.array([.25, .25, 1.])*scale, triangle*scale)
    exterior = d.closest(np.array([2., 0., 0.])*scale, triangle*scale)
    assert np.isclose(interior['distanceM']/scale, 1., rtol=0, atol=1e-15)
    assert interior['planeProjectionInside'] and interior['planeBarycentric'] == [.5, .25, .25]
    assert np.isclose(exterior['distanceM']/scale, 1., rtol=0, atol=1e-15)
    assert not exterior['planeProjectionInside']
reject(lambda: d.closest(np.zeros(3), np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])))
inherited = next(row for row in report['failures'] if row['exactSourceFaceId'] is not None)
assert inherited['targetFaceId'] == 15560 and inherited['exactSourceFaceId'] == 278671
assert inherited['nativeBearingSourceFaceId'] == 278672
assert inherited['exactAncestor']['ownSourceCentroidDistanceM'] == 0
assert inherited['exactAncestor']['ownSourceAtNativeRoundedQuery']['distanceM'] < inherited['cpuDistanceToRecordedBearingAtNativeQuery']['distanceM']
assert inherited['exactAncestor']['ownSourceNormalDot'] >= .25
checks.append('Scaled point-triangle interior/edge fixtures pass; collinear rejection and actual inherited micro-face rounding distinction verified')

proposed = d.a.array_package(report['proposedConstructionConstraint']['arrays'])
prior = d.a.array_package(receipt['finalFanProtection'])
sf = s['triangles'].reshape(-1,3)
for key in ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds']:
    assert np.isin(prior[key], proposed[key]).all()
centers = np.union1d(prior['centerOriginalVertexIds'], report['proposedConstructionConstraint']['requestedOriginalFanCenters'])
independent_mask = np.isin(sf, centers).any(axis=1)
assert np.array_equal(np.flatnonzero(independent_mask), proposed['requiredSourceFaceIds'])
assert len(centers) == 912 and len(proposed['requiredSourceFaceIds']) == 4264
assert len(proposed['lockedOriginalVertexIds']) == 3775 and len(proposed['requiredEdgesOriginal'])//2 == 7827
source_keys = {d.a.oriented_key(face) for face in sf[independent_mask]}
for row in report['failures']:
    if row['exactSourceFaceId'] is None:
        assert set(row['originalVertexIds']) <= set(centers)
        assert d.a.oriented_key(row['originalVertexIds']) not in source_keys
checks.append('Proposed whole-fan union includes every failing new target/bearing patch and every prior 62 fan; all 94 current new faces forbidden')

(d.EVIDENCE/'fixtures.json').write_text(json.dumps({'status':'CPU_DIAGNOSIS_FIXTURES_PASSED_UNACCEPTED',
    'checks':checks, 'limits':'No native proof/metric change, simplification or qualification.'},indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
