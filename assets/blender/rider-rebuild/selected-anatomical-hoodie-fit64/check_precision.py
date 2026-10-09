"""Recorded60 nanometre comparison failure, without Blender/native changes."""
import json
import runpy
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
H = runpy.run_path(str(HERE/'component.py'))
M = runpy.run_path(str(HERE/'meridian.py'))
OLD = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit60/meridian.py'))
G = runpy.run_path(str(HERE/'geometry.py'))
FAILURE = {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit60/component01/construction-failure.json',
    'sha256': 'a54762e60054f5f366c44bd0abc054ecd5a45bbe4db608816a3879e20277c680'}
failure = H['read'](FAILURE); c = failure['targetContext']
config = H['read'](H['SOURCE47']); field = config['field']
minimum = field['clothClearanceM']+field['contactSolveMarginM']
tolerance = field['numericalContactToleranceM']; assert minimum == .0026 and tolerance == .00002
apex = np.asarray(c['fixedApexPair']); end = np.asarray(c['healthy50EndpointPair'])
recorded_apex = .0025999972131103277; recorded_end = c['endpointActual3DClearanceM']
assert str(recorded_apex) in failure['message']
body_pin = config['pins']['referenceSamples']; data = np.load(H['checked'](body_pin))
body = G['Mesh'](data['RiderBody__FullAnatomyReference_basis'], data['RiderBody__FullAnatomyReference_triangles'])
precision = float(np.spacing(np.float32(max(abs(body.points).max(), 1.))))
actual_cpu = [float(body.nearest(pair)[0].min()) for pair in (apex, end)]
assert abs(actual_cpu[0]-recorded_apex) <= precision
assert abs(actual_cpu[1]-recorded_end) <= precision


def measured(apex_gap):
    def nearest(points):
        if np.array_equal(points, apex): gap = apex_gap
        elif np.array_equal(points, end): gap = recorded_end
        else: return body.nearest(points)
        return np.full(len(points), gap), np.zeros(len(points), np.int32)
    return nearest


args = (M['Axis'](c['canonicalAxisControlPoints']), apex, end, body,
    measured(recorded_apex), minimum, precision, {k: c[k] for k in ('side', 'sourceDepth', 'role')})
try: OLD['Meridian'](*args)
except AssertionError: pass
else: raise AssertionError('The recorded60 strict comparison did not reproduce')
current = M['Meridian'](*args, tolerance)
assert current.eases == [recorded_apex, recorded_end]
assert current.construction_eases == [minimum, recorded_end]
assert np.array_equal(current.at(0., apex-apex.mean(0)), apex)
assert np.array_equal(current.at(1., end-end.mean(0)), end)
assert min(current.desired_clearance(float(t)) for t in np.linspace(0, 1, 33)) >= minimum
checks = ['Exact actual60 measured apex reproduces old rejection and passes existing20µm measurement policy',
    'Actual fullbody CPU distances agree within native float32 coordinate precision',
    'Fixed source apex/healthy endpoint remain exact; measured ease retained; every prescribed ease is at least nominal2.6mm']

boundary = minimum-tolerance
for value, accepted in ((boundary, True), (float(np.nextafter(boundary, -np.inf)), False)):
    changed = list(args); changed[4] = measured(value)
    try: candidate = M['Meridian'](*changed, tolerance)
    except AssertionError: assert not accepted
    else:
        assert accepted
        assert candidate.desired_clearance(0.) == minimum
checks.append('Existing tolerance boundary admits equality and rejects the very next smaller representable measurement')

for name in ('intervals.py', 'geometry.py', 'sections.py', 'qualify.py'):
    assert (HERE/name).read_bytes() == (HERE.parent/'selected-anatomical-hoodie-fit60'/name).read_bytes()
assert (HERE/'cage.py').read_text().replace('anatomical64', 'anatomical60') == (HERE.parent/'selected-anatomical-hoodie-fit60/cage.py').read_text()
checks.append('Analytic geometric interval solver, actual reference queries, original material sections, C2 math and reopened qualification remain unchanged')
print(json.dumps({'passed': True, 'nativeExecuted': False, 'sourceRecipe': H['pin'](__file__),
    'actual60Failure': FAILURE, 'fullBody': body_pin, 'recordedApexGapM': recorded_apex,
    'nominalClearanceM': minimum, 'existingNumericalToleranceM': tolerance,
    'shortfallM': minimum-recorded_apex, 'nativeCoordinatePrecisionM': precision,
    'actualCPUFixedPairMinimumsM': actual_cpu, 'checks': checks}, indent=2))
