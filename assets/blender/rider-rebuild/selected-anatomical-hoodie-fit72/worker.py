"""Explicit parent start/resume of durable exact65 cloth transport.

No solver rerun, native import, subprocess, monitor or automatic restart.
Original69 partial transport arrays are never inputs. Only committed69 maps
and original47 source coordinates are used. Original parent guard unchanged.
"""
import json
import runpy
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72'
SOLVE69 = {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit69/solve01/solve.json',
    'sha256': 'c3f8c60ed4ed75cefa712f0edffa1318e8cead54041fe1c7b1026e51bdd339c7'}
WORKER69 = {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit69/worker.py',
    'sha256': '33a3f0cf7764b1226bc380cf4686b595a33b48b9f9a4580dfb7233ae390445bf'}
D = runpy.run_path(str(HERE/'durable.py'))
assert D['sha'](ROOT/WORKER69['path']) == WORKER69['sha256']
W69 = runpy.run_path(str(ROOT/WORKER69['path']))
PINS, CHUNK = W69['PINS'], W69['CHUNK']
sha, pin, checked, read = (W69[k] for k in ('sha', 'pin', 'checked', 'read'))
config65, math65, carry_chunk = (W69[k] for k in ('config65', 'math65', 'carry_chunk'))
CARRIED = 'UNACCEPTED_ANATOMICAL72_COMPLETE_CLOTH_CARRIED_NATIVE_PENDING'


def solve_gate():
    solved = W69['solve_gate'](checked(SOLVE69))
    assert solved['workerRecipe'] == WORKER69
    return solved


def job_for(solved):
    return {'schema': 'EXACT65_DURABLE_TRANSPORT72', 'acceptedArt': False,
        'workerRecipe': pin(__file__), 'storageRecipe': pin(HERE/'durable.py'),
        'carryRecipe69': WORKER69, 'solveReceipt': SOLVE69,
        'registrationMaps': solved['registrationMaps'], 'original47Arrays': solved['original47Arrays'],
        'sourceVertexCount': 716971, 'sourceTriangleCount': 921722, 'chunkSize': CHUNK,
        'nativeExecuted': False, 'automaticRestart': False}


def original_points(solved, np):
    with np.load(checked(solved['original47Arrays'])) as saved: original = saved['points']
    assert original.shape == (716971, 3) and original.dtype == np.float32
    assert np.array_equal(np.asarray(solved['originalBounds']), np.vstack((original.min(0), original.max(0))))
    return original


def receipt_for(out, solved):
    return {'status': CARRIED, 'acceptedArt': False, 'workerRecipe': pin(__file__),
        'storageRecipe': pin(HERE/'durable.py'), 'carryRecipe69': WORKER69,
        'solveReceipt': SOLVE69, 'job': pin(out/'job.json'),
        'assembly': pin(out/'complete/assembly.json'),
        'positions': pin(out/'complete/positions.npy'), 'jacobians': pin(out/'complete/jacobians.npy'),
        'original47Arrays': solved['original47Arrays'], 'sourceVertexCount': 716971,
        'sourceTriangleCount': 921722, 'allOriginalVerticesCarried': True,
        'originalSourceVertexOrderUnchanged': True, 'allSpansSealedAndVerified': True,
        'chunkSize': CHUNK, 'nativeExecuted': False, 'geometryGatesPassed': False}


def transport(output, resume):
    import numpy as np
    started = time.monotonic(); solved = solve_gate()
    out = Path(output).resolve(); assert out.is_relative_to(OUT)
    store = D['Spans'](out, job_for(solved), np, create=not resume)
    original = original_points(solved, np)
    at, _ = store.scan(original)
    print('EXPLICIT '+('RESUME' if resume else 'START')+' verified sealed prefix '+str(at)+'/716971', flush=True)
    if at < len(original):
        math = math65()
        with np.load(checked(solved['registrationMaps'])) as saved: maps = math['restore_maps'](saved)
        for start in range(at, len(original), CHUNK):
            end = min(start+CHUNK, len(original))
            moved, derivative = carry_chunk(original[start:end].astype(float), maps, np)
            store.seal(start, moved, derivative, original)
            print('SEALED exact65 original vertices '+str(end)+'/716971', flush=True)
    store.assemble(original)
    result = receipt_for(out, solved)
    if (out/'transport.json').exists(): assert json.loads((out/'transport.json').read_text()) == result
    else: D['atomic_json'](out/'transport.json', result)
    print(json.dumps({'status': CARRIED, 'receipt': pin(out/'transport.json'),
                      'elapsedSeconds': time.monotonic()-started}), flush=True)


def transport_gate(path):
    """Native admission requires the full sealed source domain and full arrays."""
    import numpy as np
    path = Path(path).resolve(); assert path.is_relative_to(OUT) and path.name == 'transport.json'
    row = json.loads(path.read_text()); solved = solve_gate(); out = path.parent
    assert row == receipt_for(out, solved)
    store = D['Spans'](out, job_for(solved), np)
    store.verify_assembly(original_points(solved, np))
    return row, solved


if __name__ == '__main__':
    args = sys.argv[1:]; assert len(args) == 2 and args[0] in ('start', 'resume')
    transport(args[1], resume=args[0] == 'resume')
