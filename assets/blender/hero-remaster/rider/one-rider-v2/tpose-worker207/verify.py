"""CPU-only exact preservation-block fixtures; no Torch or model imports."""
import ast
import hashlib
import json
from pathlib import Path
import resource
from types import SimpleNamespace
import time
import numpy as np

R = Path('/Users/raynos/projects/games/rockhop')
A = R / 'assets/blender/hero-remaster/rider/one-rider-v2/tpose-worker207'
E = R / 'docs/evidence/hero-remaster/one-rider-v2/tpose-worker207'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    tree = ast.parse((A / 'shape_only_worker.py').read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    diagnostics = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_diagnostics')
    start = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assert) and ast.unparse(node.test) == 'decoded is not None')
    end = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'display_faces' for target in node.targets))
    module = ast.Module(body=[diagnostics, *main.body[start:end]], type_ignores=[])
    block = compile(ast.fix_missing_locations(module), str(A / 'shape_only_worker.py'), 'exec')
    base = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]], dtype=np.float32)
    faces = np.array([[0, 1, 2]], dtype=np.int64)
    nonfinite = base.copy(); nonfinite[1, 2] = np.nan; nonfinite[2, 0] = np.inf
    fixtures = [('valid', base, faces, True), ('nonfinite_vertices', nonfinite, faces, False),
                ('negative_face', base, np.array([[0, -1, 2]], dtype=np.int64), False),
                ('out_of_range_face', base, np.array([[0, 1, 3]], dtype=np.int64), False),
                ('noninteger_face', base, np.array([[0., 1.5, 2.]], dtype=np.float64), False),
                ('nonfinite_face', base, np.array([[0., np.nan, 2.]], dtype=np.float64), False),
                ('empty_faces', base, np.empty((0, 3), dtype=np.int64), False)]
    results = []
    for name, vertices, triangle_ids, expected in fixtures:
        output = E / 'cpu-fixtures' / name
        assert not output.exists(), 'Preserve existing fixture evidence'
        output.mkdir(parents=True)
        context = {'np': np, 'decoded': SimpleNamespace(mesh_v=vertices, mesh_f=triangle_ids),
                   'output': output, 'record': {}, 'started': time.monotonic(),
                   'time': time, 'resource': resource, 'sha': sha, 'json': json}
        rejected = False
        try:
            exec(block, context)
        except AssertionError as error:
            assert str(error).startswith('Invalid decoded geometry; untouched native arrays')
            rejected = True
        assert rejected == (not expected)
        path = output / 'native-decoded.npz'
        with np.load(path, allow_pickle=False) as saved:
            assert saved['vertices'].dtype == vertices.dtype and saved['faces'].dtype == triangle_ids.dtype
            assert np.array_equal(saved['vertices'], vertices, equal_nan=True)
            assert np.array_equal(saved['faces'], triangle_ids, equal_nan=True)
        report = json.loads((output / 'native-diagnostics.json').read_text())
        assert report['validForDisplay'] == expected
        if not expected:
            generation = json.loads((output / 'generation.json').read_text())
            assert generation['status'] == 'REJECTED_NATIVE_ARRAYS_RETAINED_NO_DISPLAY'
        assert not (output / 'native-display.glb').exists()
        results.append({'fixture': name, 'validForDisplay': expected, 'rejectedAfterSaving': rejected,
                        'dtypeAndValuesRetained': True, 'nativeNPZSHA256': sha(path),
                        'nonfiniteVertexRowIDs': report['nonfiniteVertexRowIDs'],
                        'invalidFaceRowIDs': report['invalidFaceRowIDs']})
    for script in A.glob('*.py'):
        compile(script.read_text(), str(script), 'exec')
    result = {'status': 'CPU_PRESERVATION_BLOCK_FIXTURES_PASS', 'fixtures': results,
              'samplingExecuted': False, 'GPUUsed': False, 'wholeWorkerExecuted': False,
              'limits': 'AST-selected actual save/diagnostic/refusal block only; no model, display exporter or GPU pass.'}
    (E / 'cpu-fixtures.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'fixtures': len(results), 'GPUUsed': False}))


if __name__ == '__main__':
    run()
