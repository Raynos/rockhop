"""Separate process lifetimes for exact65 solve and complete original-cloth carry.

Parent original guard required for real solve/transport. No Blender imports.
Every source/target, spacing, continuation and derivative rule stays frozen65.
"""
import hashlib
import json
import runpy
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit69'
FROZEN = HERE.parent/'selected-anatomical-hoodie-fit65'
PINS = {
    'component65': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit65/component.py', 'sha256': '0338d2b19a99da861a92974e9829db41f9de1dfd2277ce5f0ce1bfaff2159b1b'},
    'input65': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit65/input01.json', 'sha256': '24b887a1617e6c4282f249a3613eea010e92203faac75d6b7d1e656767d8f462'},
    'cage65': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit65/multiscale.py', 'sha256': 'f6c4783d74fd508dd8ff7386eae1ebe9aa3d5a023e9dcbdbd5096113c5c3ab14'},
    'fixedMaterialTargets': {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65/component01/fixed-material-targets.npz', 'sha256': '821f1095759ff60dde341b3235859e88aabd8c4ccb0ab400a23d8abad186608b'},
    'materialTargets': {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65/component01/material-targets.json', 'sha256': 'f1565f44ceb4d79e1f462db8f38a185a0fb05c93607cee508a71acd617b8e357'}}
SOLVED = 'UNACCEPTED_ANATOMICAL69_EXACT65_MAPS_SOLVED_TRANSPORT_PENDING'
CARRIED = 'UNACCEPTED_ANATOMICAL69_COMPLETE_CLOTH_CARRIED_NATIVE_PENDING'
CHUNK = 4096  # Frozen65 SparseLevel.evaluate batch size; no geometric parameter.


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for value in iter(lambda: stream.read(1048576), b''): digest.update(value)
    return digest.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], row['path']; return path


def read(row): return json.loads(checked(row).read_text())


def write(path, value):
    assert not path.exists(), ('Refuse overwrite', str(path))
    path.write_text(json.dumps(value, indent=2)+'\n')


def fresh(path):
    path = Path(path).resolve(); assert path.is_relative_to(OUT) and not path.exists()
    path.mkdir(parents=True); return path


def config65():
    config = read(PINS['input65'])
    for key in ('component65', 'cage65'):
        assert config['pins'][key] == PINS[key]; checked(PINS[key])
    # multiscale65 imports this exact basis implementation.
    checked(config['pins']['denseCage64'])
    return config


def math65():
    return runpy.run_path(str(checked(PINS['cage65'])))


def fine_spacing(report, np):
    pairs = []
    for section in report['sourceMeridians']:
        pairs.append(section['actualOriginalApexPair'])
        for branch in section['branches'].values():
            pairs.extend(row['sourcePair'] for row in branch['controls'])
    # Identical expression and input order to frozen65.build.
    return float(np.linalg.norm(np.diff(np.asarray(pairs), axis=1)[:, 0], axis=1).min())


def carry_chunk(points, maps, np):
    moved = points.copy()
    differential = np.broadcast_to(np.eye(3), (len(moved), 3, 3)).copy()
    for field in maps:
        moved, step = field.evaluate(moved, True)
        differential = np.matmul(step, differential)
    return moved, differential


def solve(output):
    import numpy as np
    started = time.monotonic(); config = config65(); math = math65()
    out = fresh(output)
    with np.load(checked(config['pins']['original47Arrays'])) as original:
        points = original['points']; assert points.shape == (716971, 3) and points.dtype == np.float32
        # Native47 world transform is identity and frozen65's points() promotes
        # float32 coordinates to float64; extrema survive that promotion exactly.
        bounds = np.vstack((points.min(0), points.max(0))).astype(float)
        del points
    with np.load(checked(PINS['fixedMaterialTargets'])) as arrays:
        source = arrays['controlSource']; targets = arrays['controlTargets']
    assert source.shape == targets.shape == (656, 3)
    report = read(PINS['materialTargets']); fine = fine_spacing(report, np)
    def progress(message): print(message, flush=True)
    _, _, maps, registration = math['fixed_targets'](bounds, source, targets,
        config['field']['fieldCellM'], config['field']['maximumDerivativeBound'], progress, fine)
    registration.update(fineSpacingM=fine,
        fineSpacingDerivation='Minimum actual original paired source wall span over all fixed material controls')
    np.savez_compressed(out/'anatomical-cage.npz', **math['map_arrays'](maps),
                        controlSource=source, controlTargets=targets)
    # Validate saved map/endpoint replay before the solve process exits.
    with np.load(out/'anatomical-cage.npz') as saved: restored = math['restore_maps'](saved)
    replay = source.copy()
    for field in restored: replay, _ = field.evaluate(replay)
    error = float(np.linalg.norm(replay-targets, axis=1).max())
    assert error == registration['maximumEndpointResidualM'] <= registration['nativeCoordinatePrecisionM']
    assert [m.certificate() for m in restored] == [r['certificate'] for r in registration['steps']]
    result = {'status': SOLVED, 'acceptedArt': False, 'workerRecipe': pin(__file__),
        'frozen65': PINS, 'original47Arrays': config['pins']['original47Arrays'],
        'registrationMaps': pin(out/'anatomical-cage.npz'), 'anatomicalRegistration': registration,
        'originalBounds': bounds.tolist(), 'sourceVertexCount': 716971,
        'sourceTriangleCount': 921722, 'serializedEndpointReplayExact': True,
        'fullClothTransportExecuted': False, 'nativeExecuted': False,
        'elapsedSeconds': time.monotonic()-started}
    write(out/'solve.json', result)
    print(json.dumps({'status': SOLVED, 'receipt': pin(out/'solve.json'), 'maps': len(maps)}), flush=True)


def solve_gate(path):
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    row = json.loads(path.read_text()); config = config65()
    assert row['status'] == SOLVED and row['acceptedArt'] is False
    assert row['workerRecipe'] == pin(__file__) and row['frozen65'] == PINS
    assert row['original47Arrays'] == config['pins']['original47Arrays']
    assert row['serializedEndpointReplayExact'] and not row['fullClothTransportExecuted'] and not row['nativeExecuted']
    assert row['sourceVertexCount'] == 716971 and row['sourceTriangleCount'] == 921722
    for key in ('fixedMaterialTargets', 'materialTargets'): checked(PINS[key])
    checked(row['registrationMaps']); checked(row['original47Arrays'])
    return row


def transport(solved_path, output):
    import numpy as np
    started = time.monotonic(); solved = solve_gate(solved_path); math = math65()
    out = fresh(output)
    with np.load(checked(solved['registrationMaps'])) as saved: maps = math['restore_maps'](saved)
    with np.load(checked(solved['original47Arrays'])) as saved: original = saved['points']
    assert original.shape == (716971, 3) and original.dtype == np.float32
    assert np.array_equal(np.asarray(solved['originalBounds']), np.vstack((original.min(0), original.max(0))))
    positions = np.lib.format.open_memmap(out/'positions.npy', mode='w+', dtype=np.float64, shape=original.shape)
    jacobians = np.lib.format.open_memmap(out/'jacobians.npy', mode='w+', dtype=np.float64, shape=(len(original), 3, 3))
    for start in range(0, len(original), CHUNK):
        end = min(start+CHUNK, len(original))
        moved, derivative = carry_chunk(original[start:end].astype(float), maps, np)
        assert np.isfinite(moved).all() and np.isfinite(derivative).all()
        positions[start:end] = moved; jacobians[start:end] = derivative
        if start % (CHUNK*8) == 0: print('CARRY exact65 selected original vertices '+str(end)+'/'+str(len(original)), flush=True)
    positions.flush(); jacobians.flush(); del positions, jacobians
    result = {'status': CARRIED, 'acceptedArt': False, 'workerRecipe': pin(__file__),
        'solveReceipt': pin(solved_path), 'positions': pin(out/'positions.npy'),
        'jacobians': pin(out/'jacobians.npy'), 'original47Arrays': solved['original47Arrays'],
        'sourceVertexCount': len(original), 'sourceTriangleCount': solved['sourceTriangleCount'],
        'allOriginalVerticesCarried': True, 'originalSourceVertexOrderUnchanged': True,
        'chunkSize': CHUNK, 'nativeExecuted': False, 'geometryGatesPassed': False,
        'elapsedSeconds': time.monotonic()-started}
    write(out/'transport.json', result)
    print(json.dumps({'status': CARRIED, 'receipt': pin(out/'transport.json')}), flush=True)


def transport_gate(path):
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    row = json.loads(path.read_text()); assert row['status'] == CARRIED and row['acceptedArt'] is False
    assert row['workerRecipe'] == pin(__file__) and row['chunkSize'] == CHUNK
    solved = solve_gate(checked(row['solveReceipt']))
    assert row['sourceVertexCount'] == solved['sourceVertexCount'] == 716971
    assert row['sourceTriangleCount'] == solved['sourceTriangleCount'] == 921722
    assert row['original47Arrays'] == solved['original47Arrays']
    assert row['allOriginalVerticesCarried'] and row['originalSourceVertexOrderUnchanged']
    assert not row['nativeExecuted'] and not row['geometryGatesPassed']
    checked(row['positions']); checked(row['jacobians'])
    return row, solved


if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        if args[0] == 'solve':
            assert len(args) == 2; solve(args[1])
        elif args[0] == 'transport':
            assert len(args) == 3; transport(args[1], args[2])
        else: raise AssertionError('Expected solve or transport')
    except Exception as error:
        output = Path(args[-1]).resolve() if args else None
        if output and output.is_relative_to(OUT) and output.is_dir():
            write(output/'worker-failure.json', {'acceptedArt': False,
                'status': 'UNACCEPTED_ANATOMICAL69_CPU_STAGE_FAILED',
                'stage': args[0], 'sourceRecipe': pin(__file__),
                'exceptionType': type(error).__name__, 'message': str(error),
                'traceback': traceback.format_exc(), 'nativeExecuted': False})
        raise
