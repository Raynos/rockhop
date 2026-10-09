"""Closed-form feature and signed-domain fixtures for all-radius feasibility."""
import json
import runpy
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
I = runpy.run_path(str(HERE/'intervals.py'))
Mesh = runpy.run_path(str(HERE/'geometry.py'))['Mesh']
checks = []


def merged(rows):
    result = []
    for a, b in sorted(rows):
        if result and a <= result[-1][1]: result[-1][1] = max(b, result[-1][1])
        else: result.append([a, b])
    return np.asarray(result)


# Triangle face prism: line perpendicular through an interior point.
mesh = Mesh(np.array([[0., 0., 0.], [2., 0., 0.], [0., 2., 0.]]), np.array([[0, 1, 2]]))
blocked, _ = I['forbidden'](mesh, np.array([.5, .5, 0.]), np.array([0., 0., 1.]), -2., 2., .1)
assert np.max(abs(merged(blocked)-[[-.1, .1]])) < 1e-14
checks.append('Face-interior prism roots equal signed plane offsets')

# Outside the triangle near an edge: only the finite edge cylinder matters.
blocked, _ = I['forbidden'](mesh, np.array([.5, -.06, 0.]), np.array([0., 0., 1.]), -2., 2., .1)
assert np.max(abs(merged(blocked)-[[-.08, .08]])) < 1e-14
checks.append('Finite edge-cylinder roots follow exact Pythagorean clearance')

# Beyond both incident edges: the vertex sphere supplies the rounded corner.
blocked, _ = I['forbidden'](mesh, np.array([-.06, -.03, 0.]), np.array([0., 0., 1.]), -2., 2., .1)
radius = np.sqrt(.1**2-.06**2-.03**2)
assert np.max(abs(merged(blocked)-[[-radius, radius]])) < 1e-14
checks.append('Vertex sphere rounds triangle corners without missing interval')

# Three independent closed boxes make two disjoint exterior intervals. Deep
# interior has large unsigned distance, so a tube-only implementation fails.
vertices, faces = [], []
for cx in (0., 3., 6.):
    n = len(vertices)
    vertices.extend([[cx+x, y, z] for x in (-1., 1.) for y in (-1., 1.) for z in (-1., 1.)])
    # Explicit outward triangles in xyz lexicographic vertex order.
    faces.extend([[n+i for i in tri] for tri in [(0,1,3),(0,3,2),(4,6,7),(4,7,5),
        (0,4,5),(0,5,1),(2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]])
mesh = Mesh(np.asarray(vertices), np.asarray(faces))
offsets = np.array([[-.05, 0., 0.], [.05, 0., 0.]])
found, report = I['feasible'](mesh, mesh.nearest, np.zeros(3), np.array([1., 0., 0.]), offsets, .1, 7.5, .1)
assert np.max(abs(np.asarray(found)-[[1.15, 1.85], [4.15, 4.85], [7.15, 7.5]])) < 1e-14
assert not any(a < 3 < b for a, b in found)
checks.append('Both wall signed ray exteriors exclude deep solid and retain every disjoint/open interval')

# A branch midpoint may be blocked even though an arbitrarily narrow actual
# component exists away from it. Analytic intervals do not require a sample.
found, _ = I['feasible'](mesh, mesh.nearest, np.zeros(3), np.array([1., 0., 0.]), offsets, .1, 7.5, .449999)
assert len(found) == 3 and abs((found[0][1]-found[0][0])-2e-6) < 1e-14
assert float(mesh.nearest(np.array([[3.8, 0., 0.]]))[0][0]) < 0
checks.append('Narrow off-midpoint feasible components are found without sampling or target changes')

print(json.dumps({'passed': True, 'checks': checks}, indent=2))
