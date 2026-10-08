"""Small construction-math fixtures; these are not actual rider/contact gates."""
import importlib.util
import json
from pathlib import Path
import numpy as np

path = Path(__file__).with_name('field.py')
spec = importlib.util.spec_from_file_location('sleeve28_fixture_field', path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

points = np.array([[x, y, z] for x in (.02, .06, .10) for y in (.02, .06, .10) for z in (.02, .06, .10)])
field = module.Field(points)
embedding = field.embed(points)
assert np.max(abs(embedding[1].sum(1)-1)) < 1e-14
assert not field.evaluate(embedding).any()
node = np.indices(field.shape).reshape(3, -1).T*field.spacing+field.origin
matrix = np.diag([.1, -.05, .025])
field.values = np.sum(matrix[None]*node[:, None, :], axis=2)
expected = points*np.diag(matrix)
assert np.max(abs(field.evaluate(embedding)-expected)) < 1e-14
bound = field.jacobian_bound()
assert abs(bound['globalDisplacementLipschitzUpperBound']-np.linalg.norm(matrix)) < 1e-14

field = module.Field(points)
field.active = field.interior.copy()
normal = np.tile([0., 1., 0.], (len(points), 1))
result = field.solve_planes(embedding, normal, np.full(len(points), .003), 128)
assert np.max(.003-field.evaluate(embedding)[:, 1]) <= .000011
assert field.jacobian_bound()['positiveJacobianProvenForContinuousField']
assert not field.values[~field.active].any()
# Coincident UV seams and inner/outer locations sample one single function.
duplicate = field.embed(np.vstack((points, points)))
assert np.array_equal(field.evaluate(duplicate)[:len(points)], field.evaluate(duplicate)[len(points):])

# A derivative larger than one is rejected by the analytic guard, even where a
# small set of sampled determinants might miss a local reversed direction.
field.values = np.zeros_like(field.values); field.values[:, 0] = -2*node[:, 0]
assert not field.jacobian_bound()['positiveJacobianProvenForContinuousField']

# A curved two-wall cloth fixture starts 5 mm inside a plane. Complete fit must
# retain earlier active constraints, clear every corner/centroid, leave a healthy
# original boundary and keep its two walls distinct through the shared field.
axis = np.linspace(-.3, .3, 31)
x, z = np.meshgrid(axis, axis, indexing='ij')
y = .009-.014*np.exp(-(x*x+z*z)/.004)
inside = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
outside = inside+np.array([0., .003, 0.]); count = len(inside)
cloth = np.vstack((inside, outside)); faces = []
for i in range(30):
    for j in range(30):
        a = i*31+j; faces.extend([[a, a+31, a+1], [a+1, a+31, a+32]])
faces = np.asarray(faces); faces = np.vstack((faces, faces+count))
seeds = (abs(cloth[:, 0]) < .05) & (abs(cloth[:, 2]) < .05)
def nearest_plane(p): return p[:, 1], np.tile([0., 1., 0.], (len(p), 1))
settings = {'fieldCellM': .04, 'clothClearanceM': .0025, 'contactSolveMarginM': .0001,
            'contactReserveM': .003, 'contactPasses': 8, 'projectionIterations': 256,
            'numericalContactToleranceM': .00002, 'maximumDerivativeBound': .85,
            'maximumDisplacementM': .045}
moved, changed, shared, complete = module.fit(cloth, faces, seeds, nearest_plane, settings, lambda _: None)
assert complete['sampledActualFullWearerMinimumM'] >= .00258
assert complete['sourceBoundaryMinimumM'] > .008
assert np.min(np.linalg.norm(moved[count:]-moved[:count], axis=1)) >= .003*(1-complete['jacobian']['globalDisplacementLipschitzUpperBound'])
assert len(complete['contactIterations']) <= settings['contactPasses']
print(json.dumps({'passed': True, 'fixtures': ['identity partition and affine reproduction',
    'finite contact projection with fixed support', 'one function for coincident source seams',
    'analytic folded-field rejection', 'complete two-wall contact fit and healthy retained boundary'],
    'actualRiderRun': False, 'projection': result,
    'completeFit': {'minimumM': complete['sampledActualFullWearerMinimumM'],
                    'fixedBoundaryMinimumM': complete['sourceBoundaryMinimumM'],
                    'contactPasses': len(complete['contactIterations']),
                    'globalDerivativeBound': complete['jacobian']['globalDisplacementLipschitzUpperBound']}}))
