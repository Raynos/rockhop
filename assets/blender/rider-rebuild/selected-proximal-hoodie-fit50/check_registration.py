"""One deep paired-sheet fixture and exact differential/closure checks."""
import importlib.util
import json
import runpy
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
core = runpy.run_path(str(HERE/'registration.py'))
spec = importlib.util.spec_from_file_location('original_field28', HERE.parent/'selected-sleeve-rebuild28/field.py')
field = importlib.util.module_from_spec(spec); spec.loader.exec_module(field)
settings = {'fieldCellM': .04, 'clothClearanceM': .0025, 'contactSolveMarginM': .0001,
            'contactReserveM': .003, 'contactPasses': 8, 'projectionIterations': 256,
            'numericalContactToleranceM': .00002, 'maximumDerivativeBound': .85}
def nearest(p): return p[:, 1], np.tile([0., 1., 0.], (len(p), 1))

# Verify actual first-failure mechanism is closed before the first solve.
points = np.array([[0., -.005, 0.], [.01, -.005, 0.], [.6, -.005, 0.]])
state, support = core['closed_support'](field, points, np.array([[0, 1, 2]]),
    np.array([True, True, False]), nearest, settings, lambda _: None)
ids, weights = state['sampleEmbedding'][:2]
norm = np.sum((weights*state['field'].active[ids])**2, axis=1)
assert np.all(norm > 0) and support['closure'] and support['frozenDeficientConstraints'] == 0

# Exact trilinear differential reproduces a known affine deformation.
f = field.Field(points); embedding = f.embed(points)
nodes = np.indices(f.shape).reshape(3, -1).T*f.spacing+f.origin
matrix = np.array([[.1, .04, 0.], [0., -.05, 0.], [.03, 0., .08]])
f.values = nodes@matrix.T
j = core['jacobians'](f, embedding, field.CORNERS)
assert np.max(abs(j-(np.eye(3)+matrix))) < 1e-13

# A69mm-deep selected-like two-sheet rest region exceeds the retired45mm
# scope. Both sheets travel through identical maps to a fixed healthy rim.
axis = np.linspace(-.4, .4, 41); x, z = np.meshgrid(axis, axis, indexing='ij')
y = .009-.078*np.exp(-(x*x+z*z)/.010)
inner = np.column_stack((x.ravel(), y.ravel(), z.ravel())); count = len(inner)
points = np.vstack((inner, inner+np.array([0., .003, 0.])))
faces = []
for i in range(40):
    for k in range(40):
        a = i*41+k; faces.extend([[a, a+41, a+1], [a+1, a+41, a+42]])
faces = np.asarray(faces); faces = np.vstack((faces, faces+count))
seeds = (abs(points[:, 0]) < .05) & (abs(points[:, 2]) < .05)
moved, differential, changed, maps, report = core['register'](field, points, faces, seeds, nearest, settings, lambda _: None)
assert report['constructionContactSamplesPassed'], report
assert report['maximumOriginalSourceDisplacementM'] > .071
assert report['retired45mmRepairGateClaimed'] is False
assert all(r['certificate']['positiveJacobianProvenForContinuousField'] for r in report['registrationSteps'])
assert np.linalg.det(differential).min() > 0
replayed = points.copy()
for f in maps: replayed += f.evaluate(f.embed(replayed))
assert np.array_equal(replayed, moved)
assert np.min(np.linalg.norm(moved[count:]-moved[:count], axis=1)) > 0
assert report['healthyRetainedBoundaryPassed']
print(json.dumps({'passed': True, 'actualRiderRun': False, 'deepPairedSheet': report,
    'checks': ['Frozen deficient vertex/centroid closure before solve', 'Exact affine differential',
               'Deep paired sheets through positive-Jacobian maps', 'Exact composed-map replay',
               'Healthy fixed boundary and explicit displacement beyond retired scope']}))
