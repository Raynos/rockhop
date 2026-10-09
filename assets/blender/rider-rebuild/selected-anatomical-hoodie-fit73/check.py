"""Small numerical checks before the single actual-source construction."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/python'))
import numpy as np
D = runpy.run_path(str(HERE/'dense.py'))
NUMERICAL = {'primalToleranceM': .000005, 'equationTolerance': 1e-6, 'cgAtol': 1e-8}


def fixture(points, faces, nearest, pairs=None):
    pairs = pairs or (np.empty(0, int), np.empty(0, int), np.empty((0, 3)))
    g = D['graph'](points, faces, np.arange(len(faces)), *pairs,
                   np.empty(0, int), np.empty((0, 3)), np.empty((0, 3)), .04)
    initial, info = D['initialize'](g, NUMERICAL['cgAtol'])
    state = {'d': initial, 'inner': 0}
    history = []
    for outer in range(8):
        gap, normal, lower = D['linearize'](g, state['d'], nearest, .0026)
        if gap.min() >= .00258 and history and D['converged'](history[-1], NUMERICAL): break
        image = g['contact']@state['d']
        state.update(inner=0, normal=normal, lower=lower,
                     z=D['halfspaces'](image, normal, lower), dual=np.zeros_like(image))
        for i in range(256):
            row = D['iterate'](g, state, NUMERICAL['cgAtol'])
            if D['converged'](row, NUMERICAL): break
        history.append(row)
    gap, _, _ = D['linearize'](g, state['d'], nearest, .0026)
    assert gap.min() >= .00258 and D['converged'](history[-1], NUMERICAL), (gap.min(), history)
    return g['original'][g['inverse']]+state['d'][g['inverse']], {'minimumM': float(gap.min()), 'steps': history,
        'constraintVertices': g['constraintVertices'], 'constraintCentroids': g['constraintCentroids']}


def objective_fixture():
    from scipy.sparse.linalg import spsolve
    n = 12
    points = np.array([[i*.003, j*.003, -.02] for i in range(n) for j in range(n)])
    faces = np.array([[i*n+j, (i+1)*n+j, (i+1)*n+j+1] for i in range(n-1) for j in range(n-1)]
        +[[i*n+j, (i+1)*n+j+1, i*n+j+1] for i in range(n-1) for j in range(n-1)])
    graph = D['graph'](points, faces, np.arange(len(faces)), np.empty(0, int), np.empty(0, int),
        np.empty((0, 3)), np.array([60]), np.full((1, 3), 1/3), np.array([[.03, 0., 0.]]), .04)
    def plane(query): return query[:, 2], np.broadcast_to([0., 0., 1.], query.shape).copy()
    exact = spsolve(graph['energy'], graph['rhs'][:, 0]); results = {}
    for mode in ('zero', 'objectiveMinimum'):
        initial = np.zeros_like(graph['original']) if mode == 'zero' else D['initialize'](graph, NUMERICAL['cgAtol'])[0]
        state = {'d': initial, 'inner': 0}
        gap, normal, lower = D['linearize'](graph, initial, plane, .0026)
        image = graph['contact']@initial
        state.update(normal=normal, lower=lower, z=D['halfspaces'](image, normal, lower), dual=np.zeros_like(image))
        for i in range(256):
            row = D['iterate'](graph, state, NUMERICAL['cgAtol'])
            if D['converged'](row, NUMERICAL): break
        results[mode] = {**row, 'objectiveConverged': D['converged'](row, NUMERICAL),
            'maximumActualCoordinateErrorAgainstIndependentSparseSolveM': float(abs(state['d'][:, 0]-exact).max()),
            'guideXM': float((graph['guide']@state['d'])[0, 0]), 'meanXM': float(state['d'][:, 0].mean())}
    assert not results['zero']['objectiveConverged'], 'Feasible256-step iterate was mislabeled converged'
    assert results['objectiveMinimum']['objectiveConverged']
    assert results['objectiveMinimum']['maximumActualCoordinateErrorAgainstIndependentSparseSolveM'] < 1e-7
    return results


def main(output):
    p = np.array([[0., 0., -.02], [.003, 0., -.02], [0., .003, -.02],
                  [0., 0., -.014], [.003, 0., -.014], [0., .003, -.014]])
    f = np.array([[0, 1, 2], [3, 5, 4]])
    def plane(q): return q[:, 2], np.broadcast_to([0., 0., 1.], q.shape).copy()
    pairs = (np.arange(6), np.array([1, 1, 1, 0, 0, 0]),
             np.array([[1., 0, 0], [0, 0, 1.], [0, 1., 0], [1., 0, 0], [0, 1., 0], [0, 0, 1.]]))
    moved, plane_report = fixture(p, f, plane, pairs)
    separation = moved[3:]-moved[:3]
    assert np.all(separation[:, 2] > 0), 'Opposing walls reversed'
    assert np.allclose(moved[:, :2], p[:, :2])
    # The second triangle's orientation is irrelevant to body contact normals.
    plane_report['sourceWallSpanM'] = .006
    plane_report['constructedWallSpansM'] = np.linalg.norm(separation, axis=1).tolist()
    angle = np.arange(3)*2*np.pi/3
    points = np.column_stack((1.1*np.cos(angle), 1.1*np.sin(angle), np.full(3, .01)))
    def sphere(q):
        length = np.linalg.norm(q, axis=1)
        return length-1, q/length[:, None]
    assert sphere(points)[0].min() > 0 and sphere(points.mean(0)[None])[0][0] < 0
    _, centroid_report = fixture(points, np.array([[0, 1, 2]]), sphere)
    normal = np.array([.1, .2, 1.]); normal /= np.linalg.norm(normal)
    base = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    face = np.array([[0, 1, 2]]); source_normals = np.broadcast_to(normal, (1, 3, 3)).copy()
    transform = np.array([[2., .3, 0], [0, .5, 0], [0, 0, 1.]])
    moved_normals, unsupported = D['tangent_normals'](base, base@transform.T, face, source_normals)
    expected = np.linalg.inv(transform).T@normal; expected /= np.linalg.norm(expected)
    assert not unsupported and np.allclose(moved_normals, expected)
    output = Path(output); assert not output.exists()
    result = {'actualGarmentConstructed': False, 'acceptedArt': False,
        'planeWithPairedWalls': plane_report, 'allVerticesOutsideButCentroidInsideSphere': centroid_report,
        'independent144VertexTangentialGuideObjective': objective_fixture(),
        'actualTangentInverseTranspose': True,
        'limits': 'Small algebra/contact checks; actual source native and complete contact remain untested.'}
    output.write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result))


if __name__ == '__main__': main(sys.argv[1])
