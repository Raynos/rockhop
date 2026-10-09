"""Small CPU equivalence fixtures only; no production solve/carry/native job."""
import ast
import io
import json
import runpy
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
W = runpy.run_path(str(HERE/'worker.py'))
H = runpy.run_path(str(HERE/'component.py'))
M = W['math65'](); checks = []; started = time.monotonic()
for key in ('component65', 'input65', 'cage65', 'fixedMaterialTargets', 'materialTargets'):
    W['checked'](W['PINS'][key])
checks.append('Frozen65 component/input/solver and actual native65 target/report pins match')

rng = np.random.default_rng(69)
original = np.vstack(([-.055, -.052, -.054], [.055, .052, .054], rng.uniform(-.05, .05, (83, 3))))
controls = rng.uniform(-.024, .024, (14, 3))
targets = controls+3*np.column_stack((.0015*np.sin(controls[:, 1]*45),
    .001*np.cos(controls[:, 2]*38), .0018*np.sin(controls[:, 0]*32)))
bounds = np.vstack((original.min(0), original.max(0)))
whole, whole_j, full_maps, full_report = M['fixed_targets'](original, controls, targets, .04, .85, lambda _: None, .013)
_, _, bound_maps, bound_report = M['fixed_targets'](bounds, controls, targets, .04, .85, lambda _: None, .013)
a, b = M['map_arrays'](full_maps), M['map_arrays'](bound_maps)
assert a.keys() == b.keys() and all(np.array_equal(a[k], b[k]) for k in a)
assert full_report == bound_report
checks.append('Bounds-only versus complete original yields bit-identical every map coefficient, support, grid and full certificate/report')
assert len(full_maps) > 0

stream = io.BytesIO(); np.savez_compressed(stream, **b); stream.seek(0)
restored = M['restore_maps'](np.load(stream))
replay, replay_j = W['carry_chunk'](original, restored, np)
assert np.array_equal(replay, whole) and np.array_equal(replay_j, whole_j)
assert [m.certificate() for m in restored] == [m.certificate() for m in full_maps]
checks.append('Saved/restored frozen65 maps carry every fixture position/Jacobian exactly with identical certificates')

# Exercise composition and batches crossing frozen4096 boundary, including tail.
points = rng.uniform(-.05, .05, (4103, 3))
composed = restored+restored
expected, expected_j = W['carry_chunk'](points, composed, np)
for batch in (127, W['CHUNK']):
    moved = np.empty_like(points); differential = np.empty((len(points), 3, 3))
    for start in range(0, len(points), batch):
        moved[start:start+batch], differential[start:start+batch] = W['carry_chunk'](points[start:start+batch], composed, np)
    assert np.array_equal(moved, expected) and np.array_equal(differential, expected_j)
checks.append('Chunked composition (127 and4096, non-full tails) equals whole position/Jacobian arrays bit for bit')

# Run the actual unmodified65 inverse-transpose normal loop, including a batch
# boundary and repeated per-vertex loop IDs, against direct normalized normals.
source = W['checked'](W['PINS']['component65']).read_text()
normal_start = source.index('    transformed = np.empty_like(normals)\n')
normal_end = source.index("    mesh.vertices.foreach_set('co'", normal_start)
normal_loop = source[normal_start:normal_end]
assert normal_loop in H['transformed_component']()
normals = rng.normal(size=(16401, 3)).astype(np.float32)
normals /= np.linalg.norm(normals, axis=1)[:, None]
vertices = rng.integers(0, len(points), size=len(normals), dtype=np.int32)
env = {'np': np, 'normals': normals, 'loop_vertices': vertices, 'differential': expected_j}
exec(compile('\n'.join(line[4:] for line in normal_loop.splitlines()), '<frozen65-normal-loop>', 'exec'), env)
vectors = np.einsum('nji,nj->ni', np.linalg.inv(expected_j[vertices]), normals.astype(float))
expected_normals = (vectors/np.linalg.norm(vectors, axis=1)[:, None]).astype(np.float32)
assert np.array_equal(env['transformed'], expected_normals)
checks.append('Native inverse-transpose source corner normals remain exact65 and match full-array normalization across16384 boundary')

adapted = H['transformed_component']()
assert 'target_helper.make(' not in adapted and 'cage.fixed_targets(' not in adapted
assert "ingest69(config, out, original, np)" in adapted
for fragment in ("assert np.array_equal(original, frozen['points'])", 'normals_split_custom_set(transformed.tolist())',
    "native = c47['save_native']", "qualifier.measure(report, config, hoodie", "def qualify_receipt(path):"):
    assert fragment in adapted
assert adapted.index("native = c47['save_native']") < adapted.index("write(out/'expected-witness.json'")
checks.append('Native adapter omits target/solver/whole carry, retains exact original-coordinate comparison, normals, raw save and separate qualifier')

base_tree = ast.parse(source)
adapted_tree = ast.parse(adapted)
for name in ('invariant', 'corner_normals', 'qualify', 'qualify_receipt'):
    original_function = next(n for n in base_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    copied_function = next(n for n in adapted_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    assert ast.dump(original_function) == ast.dump(copied_function), name
checks.append('AST-exact frozen65 preservation, corner-normal, independent native qualification and CPU admission functions')

with np.load(W['checked'](W['PINS']['fixedMaterialTargets'])) as actual:
    assert actual['controlSource'].shape == actual['controlTargets'].shape == (656, 3)
fine = W['fine_spacing'](W['read'](W['PINS']['materialTargets']), np)
config = W['config65']()
assert 0 < fine < config['field']['fieldCellM'] == .04
assert config['field']['maximumDerivativeBound'] == .85
assert config['field']['clothClearanceM']+config['field']['contactSolveMarginM'] == .0026
assert config['field']['numericalContactToleranceM'] == .00002
checks.append('Actual native656 targets retain source-pair-derived fine spacing and original40mm/.85/2.6mm/20micrometre policy')

for path in HERE.glob('*.py'): ast.parse(path.read_text(), feature_version=(3, 9))
checks.append('All new source parses with Python3.9 grammar')
print(json.dumps({'acceptedArt': False, 'passed': True, 'productionSolveExecuted': False,
    'productionTransportExecuted': False, 'nativeExecuted': False, 'checks': checks,
    'fixtureMapCount': len(full_maps), 'actualFineSpacingM': fine,
    'elapsedSeconds': time.monotonic()-started}, indent=2))
