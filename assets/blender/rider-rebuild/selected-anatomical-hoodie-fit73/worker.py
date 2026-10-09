"""Explicit parent-guarded prepare/solve/resume lifetimes; no auto restarts."""
import hashlib
import json
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73'
sys.path.insert(0, str(OUT/'python'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while block := f.read(1048576): h.update(block)
    return h.hexdigest()


def pin(path):
    path = Path(path).resolve(); return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], row['path']; return path


def read(row): return json.loads(checked(row).read_text())


def write(path, value):
    assert not path.exists(); path.write_text(json.dumps(value, indent=2)+'\n')


def freeze(output):
    import scipy
    old = json.loads((HERE.parent/'selected-anatomical-hoodie-fit65/input01.json').read_text())
    job = {'acceptedArt': False, 'operation': 'DENSE_SOURCE_MATERIAL_GRAPH_AND_ACTUAL_BODY_CONTACT73',
        'native47': old['pins']['gloveNative'], 'input65': pin(HERE.parent/'selected-anatomical-hoodie-fit65/input01.json'),
        'original47Arrays': old['pins']['original47Arrays'], 'bodyReference': old['pins']['referenceSamples'],
        'retained72': pin(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72/component01/qualification-inputs.npz'),
        'targets65': pin(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65/component01/fixed-material-targets.npz'),
        'worker': pin(__file__), 'dense': pin(HERE/'dense.py'), 'native': pin(HERE/'native.py'),
        'settings': old['field'], 'scipyVersion': scipy.__version__,
        'numerical': {'primalToleranceM': old['field']['numericalContactToleranceM']/4,
                      'equationTolerance': 1e-6, 'cgAtol': 1e-8},
        'limits': ['One source-relative dense material solve; no continuous injectivity certificate.',
                   'Full contact in every linearization; clearance/tolerance unchanged65.',
                   'Graph smoothness and measured source-wall vectors are construction energies, not geometry pass thresholds.',
                   'Original native source/UV/PBR/skin and75bone rest stay exact; source detail normals use measured triangle derivatives.',
                   'No art, self-crossing, moving, game or device acceptance is implied.']}
    for row in job.values():
        if isinstance(row, dict) and 'sha256' in row: checked(row)
    output = Path(output).resolve(); assert output.is_relative_to(HERE)
    write(output, job); print(json.dumps({'input': pin(output)}), flush=True)


def load_job(path):
    path = Path(path).resolve(); job = json.loads(path.read_text())
    assert job['acceptedArt'] is False and job['worker'] == pin(__file__)
    assert job['dense'] == pin(HERE/'dense.py') and job['native'] == pin(HERE/'native.py')
    for row in job.values():
        if isinstance(row, dict) and 'sha256' in row: checked(row)
    assert job['settings'] == read(job['input65'])['field'], 'Existing contact policy changed'
    return job


def prepare(input_path, output):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    job = load_job(input_path); out = Path(output).resolve()
    assert out.is_relative_to(OUT) and not out.exists(); out.mkdir(parents=True)
    h = runpy.run_path(str(HERE/'native.py'))
    rig, hoodie, body, config, before = h['open_original'](job, bpy, np)
    p, f = h['geometry_arrays'](hoodie, np); bp, bf = h['geometry_arrays'](body, np)
    frozen = np.load(checked(job['original47Arrays']))
    assert np.array_equal(p, frozen['points']) and np.array_equal(f, frozen['faces'])
    cached = np.load(checked(job['bodyReference'])); key = 'RiderBody__FullAnatomyReference'
    assert np.array_equal(bp, cached[key+'_basis']) and np.array_equal(bf, cached[key+'_triangles'])
    assert hoodie.matrix_world.is_identity and body.matrix_world.is_identity
    retained = np.load(checked(job['retained72']))['retainedOriginalFaceIds']
    unique, first, inverse = np.unique(p, axis=0, return_index=True, return_inverse=True)
    tri = p[f].astype(float); tn = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    vn = np.zeros_like(unique, dtype=float)
    for axis in range(3): vn[:, axis] = np.bincount(inverse[f].ravel(), weights=np.repeat(tn[:, axis], 3), minlength=len(unique))
    length = np.linalg.norm(vn, axis=1); vn = np.divide(vn, length[:, None], out=np.zeros_like(vn), where=length[:, None] > 0)
    tree = BVHTree.FromPolygons([Vector(point) for point in p], f.tolist(), all_triangles=True)
    precision = float(np.spacing(np.float32(max(abs(p).max(), 1.))))
    pair_ids, pair_faces, pair_bary, missing, orientation = [], [], [], [], []
    for index, (point, normal) in enumerate(zip(unique, vn)):
        if not length[index]: missing.append(int(first[index])); continue
        q, n, face, distance = tree.ray_cast(Vector(point-normal*precision), Vector(-normal))
        if face is None: missing.append(int(first[index])); continue
        if np.dot(np.asarray(n), -normal) <= 0:
            orientation.append(int(first[index])); continue
        triangle = tri[face]; uv = np.linalg.lstsq((triangle[1:]-triangle[0]).T, np.asarray(q)-triangle[0], rcond=None)[0]
        bary = np.r_[1-uv.sum(), uv]
        if bary.min() < -8*np.finfo(np.float32).eps:
            orientation.append(int(first[index])); continue
        pair_ids.append(int(first[index])); pair_faces.append(int(face)); pair_bary.append(bary)
        if index % 65536 == 0: print('MEASURE actual source wall links '+str(index)+'/'+str(len(unique)), flush=True)
    targets = np.load(checked(job['targets65'])); guide_faces, guide_bary = [], []
    assert pair_ids, 'No measured source-wall correspondences'
    for point in targets['controlSource']:
        q, n, face, distance = tree.find_nearest(Vector(point))
        assert distance <= 2*precision, ('Source guide off actual selected material', distance)
        triangle = tri[face]; uv = np.linalg.lstsq((triangle[1:]-triangle[0]).T, np.asarray(q)-triangle[0], rcond=None)[0]
        guide_faces.append(face); guide_bary.append(np.r_[1-uv.sum(), uv])
    np.savez(out/'prepared.npz', points=p, faces=f, bodyPoints=bp, bodyFaces=bf, retained=retained,
        pairIds=np.asarray(pair_ids), pairFaces=np.asarray(pair_faces), pairBary=np.asarray(pair_bary),
        guideFaces=np.asarray(guide_faces), guideBary=np.asarray(guide_bary),
        guideDelta=targets['controlTargets']-targets['controlSource'])
    write(out/'prepared.json', {'acceptedArt': False, 'status': 'ACTUAL47_DENSE_INPUTS_EXTRACTED_NO_FIT',
        'input': pin(input_path), 'arrays': pin(out/'prepared.npz'), 'sourceWitness': before,
        'bodyCacheMatchesActualNative47Exactly': True, 'sourceCacheMatchesActualNative47Exactly': True,
        'worldTransformsIdentity': True, 'wallLinks': len(pair_ids), 'missingWallRays': missing,
        'unclassifiedWallRays': orientation, 'sourceUniquePositions': len(unique),
        'retainedContactFaces': len(retained), 'nativeConstructionExecuted': False})
    print(json.dumps({'prepared': pin(out/'prepared.json'), 'wallLinks': len(pair_ids),
                      'missing': len(missing), 'unclassified': len(orientation)}), flush=True)


def snapshot(out, binding, state, history):
    import numpy as np
    # Two complete generations: state bytes and their checksum-bound receipt
    # are atomically swapped only after both are durable.
    previous = []
    if (out/'checkpoint.json').exists():
        old_pin = json.loads((out/'checkpoint.json').read_text())
        old_row = read(old_pin); previous = [checked(old_pin), checked(old_row['state'])]
    generation = int(state.get('serial', -1))+1; state['serial'] = generation
    data = out/('state-'+str(generation)+'.npz'); receipt = out/('state-'+str(generation)+'.json')
    # A kill before swapping the pointer may leave the next unreferenced pair.
    # Pick a new sequence rather than overwriting any possibly referenced bytes.
    while data.exists() or receipt.exists():
        generation += 1; state['serial'] = generation
        data = out/('state-'+str(generation)+'.npz'); receipt = out/('state-'+str(generation)+'.json')
    with data.open('wb') as stream:
        np.savez(stream, **state); stream.flush(); os.fsync(stream.fileno())
    row = {'binding': binding, 'state': pin(data), 'history': history,
           'acceptedArt': False, 'status': 'UNACCEPTED_DENSE73_NUMERICAL_CHECKPOINT'}
    receipt.write_text(json.dumps(row, indent=2)+'\n')
    with receipt.open('rb') as stream: os.fsync(stream.fileno())
    pointer = out/'checkpoint.next'
    with pointer.open('w') as stream:
        stream.write(json.dumps(pin(receipt))+'\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(pointer, out/'checkpoint.json')
    directory = os.open(out, os.O_RDONLY)
    try: os.fsync(directory)
    finally: os.close(directory)
    for old in out.glob('state-*'):
        if old not in (data, receipt, *previous): old.unlink()


def solve(input_path, prepared_path, output, resume=False):
    import numpy as np
    import scipy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    job = load_job(input_path); assert scipy.__version__ == job['scipyVersion']
    prepared_path = Path(prepared_path).resolve(); prepared = json.loads(prepared_path.read_text())
    assert prepared['input'] == pin(input_path) and prepared['bodyCacheMatchesActualNative47Exactly']
    arrays = np.load(checked(prepared['arrays'])); out = Path(output).resolve()
    assert out.is_relative_to(OUT)
    if not resume: assert not out.exists(); out.mkdir(parents=True)
    else: assert out.is_dir()
    binding = {'input': pin(input_path), 'prepared': pin(prepared_path)}
    math = runpy.run_path(str(HERE/'dense.py')); settings = job['settings']; numerical = job['numerical']
    system = math['graph'](arrays['points'], arrays['faces'], arrays['retained'], arrays['pairIds'],
        arrays['pairFaces'], arrays['pairBary'], arrays['guideFaces'], arrays['guideBary'],
        arrays['guideDelta'], settings['fieldCellM'])
    body_points, body_faces = arrays['bodyPoints'], arrays['bodyFaces']
    origin = (body_points.min(0)+body_points.max(0))*.5
    tree = BVHTree.FromPolygons([Vector(p-origin) for p in body_points], body_faces.tolist(), all_triangles=True)
    def nearest(query):
        gap, normals = np.empty(len(query)), np.empty_like(query)
        for i, p in enumerate(query):
            q, normal, face, distance = tree.find_nearest(Vector(p-origin))
            delta = p-origin-np.asarray(q); outward = np.asarray(normal)
            sign = 1 if delta@outward >= 0 else -1; gap[i] = sign*distance
            length = np.linalg.norm(delta); normals[i] = sign*delta/length if length > 1e-12 else outward
        return gap, normals
    target = settings['clothClearanceM']+settings['contactSolveMarginM']; tolerance = settings['numericalContactToleranceM']
    if resume:
        row = read(json.loads((out/'checkpoint.json').read_text())); assert row['binding'] == binding
        with np.load(checked(row['state'])) as saved: state = {k: saved[k].copy() for k in saved.files}
        history = row['history']; print('EXPLICIT RESUME checked dense73 state', int(state['outer']), int(state['inner']), flush=True)
    else:
        initial, initial_info = math['initialize'](system, numerical['cgAtol'])
        state = {'d': initial, 'outer': 0, 'inner': 0, 'objectiveConverged': False,
                 'initialCGInfo': np.asarray(initial_info)}; history = []
    for outer in range(int(state['outer']), settings['contactPasses']):
        if int(state['inner']) == 0:
            gap, normal, lower = math['linearize'](system, state['d'], nearest, target)
            print('DENSE73 all '+str(len(gap))+' contacts: minimum '+str(gap.min())+' deficient '+str(int((gap < target-tolerance).sum())), flush=True)
            history.append({'outer': outer, 'minimumBeforeM': float(gap.min()),
                            'deficientBefore': int((gap < target-tolerance).sum())})
            if gap.min() >= target-tolerance and bool(state['objectiveConverged']): break
            # A feasible iterate still needs to minimize the material energy.
            # Retain its ADMM multipliers/linearization across numerical blocks.
            retain = gap.min() >= target-tolerance and 'normal' in state
            history[-1]['retainedLinearizationForObjectiveConvergence'] = bool(retain)
            if not retain:
                image = system['contact']@state['d']
                state.update(normal=normal, lower=lower, z=math['halfspaces'](image, normal, lower),
                    dual=np.zeros_like(image), objectiveConverged=False)
            snapshot(out, binding, state, history)
        while int(state['inner']) < settings['projectionIterations'] and not bool(state['objectiveConverged']):
            row = math['iterate'](system, state, numerical['cgAtol'])
            state['objectiveConverged'] = math['converged'](row, numerical)
            if int(state['inner']) % 16 == 0:
                print('DENSE73 '+str(outer)+' '+str(row), flush=True)
                snapshot(out, binding, state, history)
            if bool(state['objectiveConverged']): break
        row = math['residuals'](system, state)
        history[-1]['linearSolve'] = row
        state.update(outer=outer+1, inner=0); snapshot(out, binding, state, history)
    gap, _, _ = math['linearize'](system, state['d'], nearest, target)
    positions = system['original']+state['d']
    np.save(out/'positions.npy', positions[system['inverse']])
    wall_delta = system['wall']@state['d']
    contact_passed = bool(gap.min() >= target-tolerance); objective_passed = bool(state['objectiveConverged'])
    status = 'UNACCEPTED_DENSE73_CONTACT_FAILED' if not contact_passed else (
        'UNACCEPTED_DENSE73_CONTACT_PASSED_OBJECTIVE_UNCONVERGED' if not objective_passed else
        'UNACCEPTED_DENSE73_CONTACT_SAMPLES_PASSED_NATIVE_PENDING')
    report = {'acceptedArt': False, 'status': status,
        **binding, 'positions': pin(out/'positions.npy'), 'history': history,
        'constructionContactSamplesPassed': contact_passed, 'linearizedObjectiveConverged': objective_passed,
        'numericalConvergence': math['residuals'](system, state),
        'numericalResidualLimit': 'Dual and stationarity are raw equation residuals, not bounds on vertex position error.',
        'minimumActualBodyGapM': float(gap.min()), 'deficientSamples': int((gap < target-tolerance).sum()),
        'constraintVertices': system['constraintVertices'], 'constraintCentroids': system['constraintCentroids'],
        'wallDisplacementMismatchPercentilesM': np.percentile(np.linalg.norm(wall_delta, axis=1), [0, 50, 90, 99, 100]).tolist(),
        'continuousMapInjectivityClaimed': False, 'geometryGatesPassed': False, 'movingReviewPassed': False}
    write(out/'solve.json', report); print(json.dumps(report), flush=True)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze': freeze(args[1])
    elif args[0] == 'prepare': prepare(*args[1:])
    elif args[0] in ('solve', 'resume'): solve(*args[1:], resume=args[0] == 'resume')
    else: raise AssertionError(args)
