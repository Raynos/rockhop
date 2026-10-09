"""Small restart/corruption fixtures; no production transport or native job."""
import ast
import io
import json
import runpy
import shutil
import tempfile
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
W = runpy.run_path(str(HERE/'worker.py'))
H = runpy.run_path(str(HERE/'component.py'))
D = W['D']; M = W['math65'](); started = time.monotonic(); checks = []


def rejected(call):
    try: call()
    except (AssertionError, FileNotFoundError, ValueError): return
    raise AssertionError('Invalid transport was admitted')


rng = np.random.default_rng(72)
original = rng.uniform(-.04, .04, (31, 3)).astype(np.float32)
controls = original[:9].astype(float)
targets = controls+np.column_stack((.002*np.sin(controls[:, 1]*40),
    .0015*np.cos(controls[:, 2]*31), .003*np.sin(controls[:, 0]*35)))
_, _, maps, _ = M['fixed_targets'](original.astype(float), controls, targets, .04, .85, lambda _: None, .013)
stream = io.BytesIO(); np.savez_compressed(stream, **M['map_arrays'](maps)); stream.seek(0)
restored = M['restore_maps'](np.load(stream)); maps = restored+restored
uninterrupted, uninterrupted_j = W['carry_chunk'](original.astype(float), maps, np)
job = {'sourceVertexCount': len(original), 'chunkSize': 12,
       'workerRecipe': W['pin'](HERE/'worker.py'), 'storageRecipe': W['pin'](HERE/'durable.py'),
       'fixture': True, 'carryRecipe69': W['WORKER69']}

with tempfile.TemporaryDirectory(prefix='rockhop72-small-fixture-') as temporary:
    base = Path(temporary); root = base/'resumed'; store = D['Spans'](root, job, np, create=True)
    for start in (0, 12):
        p, j = W['carry_chunk'](original[start:start+12].astype(float), maps, np)
        store.seal(start, p, j, original)
    # A killed process can leave output bytes but no sealed commit. They must
    # neither count as progress nor block recomputing this one active span.
    pending = root/'spans'/'.pending-span-interrupted'; pending.mkdir()
    np.save(pending/'positions.npy', uninterrupted[24:])
    del store
    reopened = D['Spans'](root, json.loads((root/'job.json').read_text()), np)
    at, seals = reopened.scan(original)
    assert at == 24 and len(seals) == 2
    rejected(lambda: reopened.scan(original, complete=True))
    rejected(lambda: reopened.assemble(original))
    checks.append('Interrupted unsealed bytes do not count; valid contiguous sealed prefix24/31 survives reopening and rejects complete admission')
    p, j = W['carry_chunk'](original[at:].astype(float), maps, np)
    reopened.seal(at, p, j, original)
    assembly = reopened.assemble(original)
    final_p, final_j = reopened.arrays(reopened.checked(assembly['positions']), reopened.checked(assembly['jacobians']), len(original))
    assert np.array_equal(final_p, uninterrupted) and np.array_equal(final_j, uninterrupted_j)
    checks.append('Explicit resume from durable prefix including short final span matches uninterrupted positions and composed Jacobians bit-exactly')
    before = D['sha'](root/'complete/assembly.json')
    assert reopened.assemble(original) == assembly and D['sha'](root/'complete/assembly.json') == before
    checks.append('Completed assembly verifies idempotently without changing immutable output or sealed spans')

    corrupt = base/'corrupt'; shutil.copytree(root, corrupt)
    file = corrupt/'spans/0000000-0000012/positions.npy'
    with file.open('r+b') as f: f.seek(-1, 2); value = f.read(1); f.seek(-1, 2); f.write(bytes([value[0]^1]))
    rejected(lambda: D['Spans'](corrupt, job, np).scan(original))
    checks.append('Corrupted sealed position bytes reject by checksum before prefix reuse or native admission')

    incomplete = base/'incomplete'; shutil.copytree(root, incomplete)
    (incomplete/'spans/0000012-0000024/jacobians.npy').unlink()
    rejected(lambda: D['Spans'](incomplete, job, np).scan(original))
    checks.append('A sealed span missing its Jacobian payload rejects; partial data is never promoted')

    gapped = base/'gapped'; shutil.copytree(root, gapped)
    shutil.rmtree(gapped/'spans/0000000-0000012')
    rejected(lambda: D['Spans'](gapped, job, np).scan(original))
    checks.append('Missing earlier span with later seals rejects as a noncontiguous prefix')

    changed = dict(job); changed['workerRecipe'] = {**job['workerRecipe'], 'sha256': '0'*64}
    rejected(lambda: D['Spans'](root, changed, np))
    reordered = original[::-1].copy()
    rejected(lambda: reopened.scan(reordered))
    checks.append('Changed executing-source job or original source vertex order rejects on resume')

    incorrect = base/'incorrect'; shutil.copytree(root, incorrect)
    file = incorrect/'complete/jacobians.npy'
    with file.open('r+b') as f: f.seek(-1, 2); value = f.read(1); f.seek(-1, 2); f.write(bytes([value[0]^1]))
    rejected(lambda: D['Spans'](incorrect, job, np).verify_assembly(original))
    checks.append('Corrupt assembled whole-domain Jacobian rejects despite valid sealed source spans')

    tail = base/'tail'; shutil.copytree(root, tail)
    seal_path = tail/'spans/0000024-0000031/seal.json'
    seal = json.loads(seal_path.read_text()); seal['end'] = 32; seal_path.write_text(json.dumps(seal))
    rejected(lambda: D['Spans'](tail, job, np).scan(original))
    checks.append('Wrong sealed tail bound rejects; completion requires exactly all source vertices')

# Verify exact source lineage without reading the full original arrays/maps.
assert W['pin'](W['ROOT']/W['SOLVE69']['path']) == W['SOLVE69']
solved = W['read'](W['SOLVE69'])
assert solved['workerRecipe'] == W['WORKER69'] and len(solved['anatomicalRegistration']['steps']) == 28
assert W['carry_chunk'].__code__.co_filename.endswith('selected-anatomical-hoodie-fit69/worker.py')
actual_job = W['job_for'](solved)
assert actual_job['workerRecipe'] == W['pin'](HERE/'worker.py') != W['WORKER69']
assert actual_job['carryRecipe69'] == W['WORKER69'] and actual_job['solveReceipt'] == W['SOLVE69']
assert actual_job['automaticRestart'] is False
checks.append('Truthful72 execution and storage provenance retain pinned actual69 solve and unchanged69 carry helper; no forged69 worker identity')

source = W['checked'](W['PINS']['component65']).read_text(); adapted = H['transformed_component']()
a, b = ast.parse(source), ast.parse(adapted)
for name in ('invariant', 'corner_normals', 'qualify', 'qualify_receipt'):
    first = next(n for n in a.body if isinstance(n, ast.FunctionDef) and n.name == name)
    second = next(n for n in b.body if isinstance(n, ast.FunctionDef) and n.name == name)
    assert ast.dump(first) == ast.dump(second)
start = source.index('    transformed = np.empty_like(normals)\n')
end = source.index("    mesh.vertices.foreach_set('co'", start)
assert source[start:end] in adapted
assert 'target_helper.make(' not in adapted and 'cage.fixed_targets(' not in adapted
_, intake = H['transformed_source']()
assert "ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72'" in intake
assert H['QUALIFIED'] == 'UNACCEPTED_ANATOMICAL72_REOPENED_DISTAL_AND_MOTION_PENDING'
checks.append('Native72 retains AST-exact65 preservation/reopen/admission and exact normal transport, with truthful72 output/status and no repeated solve')

for path in HERE.glob('*.py'): ast.parse(path.read_text(), feature_version=(3, 9))
checks.append('All72 source parses as Python3.9; fixture performed no production transport or native job')
print(json.dumps({'acceptedArt': False, 'passed': True, 'productionTransportExecuted': False,
    'nativeExecuted': False, 'checks': checks, 'elapsedSeconds': time.monotonic()-started}, indent=2))
