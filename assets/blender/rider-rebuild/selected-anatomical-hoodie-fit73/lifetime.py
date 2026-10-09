"""Cached73 source authority; empty-process wall preparation, exact73 solve.

Committed input02 and all numerical/normal-transport functions stay unchanged.
Original normals are bound by the original native file SHA, read at actual
apply, transported by frozen73, and checked by its independent saved reopen.
"""
import ast
import hashlib
import json
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
FROZEN = {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit73/input02.json',
          'sha256': '19faf247e80d5c6dec38db409b7f7bddb4e44afd2b8571cd24a5c31a7945b167'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576): h.update(block)
    return h.hexdigest()


def checked(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], row['path']; return path


def read(row): return json.loads(checked(row).read_text())


def pin(path):
    path = Path(path).resolve(); return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


JOB = read(FROZEN)
W = runpy.run_path(str(checked(JOB['worker'])))
N = runpy.run_path(str(checked(JOB['native'])))


def durable_json(path, value):
    path = Path(path).resolve(); assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.partial'); assert not temporary.exists()
    with temporary.open('w') as stream:
        stream.write(json.dumps(value, indent=2)+'\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(directory)
    finally: os.close(directory)


def authority(evidence):
    """Join recorded assertions only; never qualify72's failed body contact."""
    import numpy as np
    config = read(JOB['input65']); N['H']['source_gate'](config)
    intake = read(evidence['intake47']); component41 = N['C']['intake_gate'](intake)
    assert evidence['intake47'] == config['pins']['gloveReceipt'] and intake['native'] == JOB['native47']
    original = read(evidence['original54'])
    assert original['variant'] == 'original' and original['native'] == JOB['native47']
    assert original['actualGeometry'] == JOB['original47Arrays']
    original_recipe = checked(original['recipe']).read_text()
    assert 'assert obj.matrix_world.is_identity' in original_recipe
    assert 'points, faces = geometry(hoodie)' in original_recipe
    report = read(evidence['reopened72']); pending = read(report['pendingReceipt'])
    witness = read(report['expectedWitness']); actual_config = read(report['input'])
    assert report['sourceIntake47'] == evidence['intake47'] and pending['native'] == report['native']
    assert pending['sourceRecipe'] == report['sourceRecipe'] and pending['input'] == report['input']
    assert actual_config['pins']['gloveNative'] == JOB['native47']
    assert actual_config['pins']['referenceSamples'] == JOB['bodyReference']
    assert actual_config['pins']['original47Arrays'] == JOB['original47Arrays']
    assert all(report[k] for k in ('sourceInvariantExact', 'exact75RestUnchanged',
        'fullReferenceUnchanged', 'protectedValidationPassed', 'topologyAndSourceVertexOrderUnchanged'))
    assert report['nativeStorage']['reopenVerified'] is True
    assert report['anatomicalRegistration']['constructionContactSamplesPassed'] is False
    assert witness['rest'] == intake['expectedRest'] == component41['protectedBefore']['rest']
    assert witness['protectedGeometry'] == report['protectedGeometryUnchanged']
    assert witness['protectedGeometry']['RiderBody__FullAnatomyReference'] == component41['protectedBefore']['fullReference']
    for name, signature in component41['expectedConstructedGeometry'].items():
        assert witness['protectedGeometry'][name] == signature
    assert witness['sourceInvariant']['metadata'] == intake['expectedHoodieMetadata']
    saved = np.load(checked(JOB['original47Arrays']))
    assert saved['points'].shape == (witness['sourceInvariant']['vertices'], 3)
    assert hashlib.sha256(saved['faces'].tobytes()).hexdigest() == witness['sourceInvariant']['topology']
    reference = read(evidence['reference05']); assert reference['arrays'] == JOB['bodyReference']
    with np.load(checked(JOB['bodyReference'])) as body:
        for name, signature in reference['arraySHA256'].items():
            assert hashlib.sha256(body[name].tobytes()).hexdigest() == signature
    # The saved72 construction/reopen reached this same-SHA native intake.
    # These assertions precede its build/save and were not replaced by72.
    module72 = runpy.run_path(str(checked(report['sourceRecipe'])))
    _, prefix = module72['transformed_source']()
    required = ["bpy.ops.wm.open_mainfile(filepath=str(pin(config['pins']['gloveNative'])), use_scripts=False)",
        "_, bp = B.A['points'](wearer); bf = B.A['faces'](wearer)",
        "assert np.array_equal(bp, reference[key+'_basis']), 'Actual full-reference Basis differs from witness'",
        "assert np.array_equal(bf, reference[key+'_triangles']), 'Actual full-reference triangles differ from witness'",
        'build({**globals(), **locals()})']
    positions = [prefix.index(value) for value in required]
    assert positions == sorted(positions) and all(prefix.count(value) == 1 for value in required)
    return {'rest': witness['rest'], 'sourceInvariant': witness['sourceInvariant'],
        'hoodieGeometry': intake['expectedHoodieGeometry'], 'protectedGeometry': witness['protectedGeometry']}


def bind(output):
    W['load_job'](checked(FROZEN))
    evidence = {
        'intake47': pin(ROOT/'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json'),
        'original54': pin(ROOT/'harness/out/rider-rebuild/selected-proximal-fit-review54/original01/render.json'),
        'reference05': pin(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.json'),
        'reopened72': pin(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72/component01/component-qualified.json')}
    witness = authority(evidence)
    row = {'acceptedArt': False, 'status': 'CACHED_ACTUAL47_IDENTITY_BOUND_NO_NEW_NATIVE_OPEN',
        'originalInput73': FROZEN, 'lifetimeRecipe': pin(__file__), 'evidence': evidence,
        'sourceWitness': witness, 'originalNormalsBoundByNativeFileSHA': JOB['native47'],
        'sourceCacheMatchesActualNative47Exactly': True, 'bodyCacheMatchesActualNative47WorldExactly': True,
        'originalCornerNormalHashInvented': False, 'nativeIntakeExecuted': False,
        'limits': ['72 contact failed; only its exact source/protected/native-intake observations are reused.',
            'Original standalone corner-normal hash was not recorded. Exact original47 bytes bind it; actual73 apply reads those normals.',
            'Actual apply rechecks original points/faces, body cache and identity matrices before deformation.',
            'Frozen73 full before/expected witness and independently reopened normal fingerprint remain mandatory.']}
    output = Path(output).resolve(); assert output.is_relative_to(HERE)
    durable_json(output, row); print(json.dumps({'cachedInput': pin(output), 'nativeIntakeExecuted': False}), flush=True)


def stage(path):
    path = Path(path).resolve(); value = json.loads(path.read_text())
    assert value['originalInput73'] == FROZEN and value['lifetimeRecipe'] == pin(__file__)
    W['load_job'](checked(FROZEN))
    assert value['sourceWitness'] == authority(value['evidence'])
    assert value['originalNormalsBoundByNativeFileSHA'] == JOB['native47']
    assert value['originalCornerNormalHashInvented'] is False
    return value, {'input': pin(path), 'recipe': pin(__file__), 'originalInput73': FROZEN,
                   'originalNormalsBoundByNativeFileSHA': JOB['native47']}


def function_source(row, name):
    source = checked(row).read_text(); tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])+'\n'


def prepared_function(value, execution):
    source = function_source(JOB['worker'], 'prepare')
    start = source.index("    h = runpy.run_path(str(HERE/'native.py'))\n")
    end = source.index("    retained = np.load(checked(job['retained72']))", start)
    source = source[:start]+"    assert not bpy.data.filepath, 'Wall preparation requires an empty Blender process'\n    before, p, f, bp, bf = cached_intake(np)\n"+source[end:]
    old = "'worldTransformsIdentity': True, 'wallLinks': len(pair_ids)"
    assert source.count(old) == 1
    source = source.replace(old, "'worldCoordinateAuthority': 'CACHED_ACTUAL47_WORLD_POINTS; MATRIX_IDENTITY_RECHECKED_AT_APPLY', 'cachedLifetime': execution, 'wallLinks': len(pair_ids)")
    def cached_intake(np):
        original = np.load(checked(JOB['original47Arrays'])); body = np.load(checked(JOB['bodyReference']))
        key = 'RiderBody__FullAnatomyReference'
        return value['sourceWitness'], original['points'], original['faces'], body[key+'_basis'], body[key+'_triangles']
    namespace = {**W, 'cached_intake': cached_intake, 'execution': execution}
    exec(compile(source, str(checked(JOB['worker'])), 'exec'), namespace)
    return namespace['prepare'], source


def applied_function(value, execution):
    source = function_source(JOB['native'], 'apply')
    old = "    assert before == prepared['sourceWitness']\n"
    assert source.count(old) == 1
    source = source.replace(old, '    verify_cached_source(before, prepared, hoodie, body, np)\n')
    old = "'sourceRestProtectedInvariantPassed': True, 'normalTransport':"
    assert source.count(old) == 1
    source = source.replace(old, "'sourceRestProtectedInvariantPassed': True, 'cachedPreparationAuthority': execution, 'actualOriginalCornerNormals': before['cornerNormals'], 'normalTransport':")
    def verify_cached_source(before, prepared, hoodie, body, np):
        proven = value['sourceWitness']
        assert set(before) == set(proven)|{'cornerNormals'}
        assert prepared['sourceWitness'] == proven and prepared['cachedLifetime'] == execution
        assert {key: before[key] for key in proven} == proven
        # The complete original47 file was hash-checked/opened by frozen73.
        # Normals are sampled from those bytes, not compared to an invented cache.
        assert isinstance(before['cornerNormals'], str) and len(before['cornerNormals']) == 64
        assert hoodie.matrix_world.is_identity and body.matrix_world.is_identity
        p, f = N['geometry_arrays'](hoodie, np); bp, bf = N['geometry_arrays'](body, np)
        original = np.load(checked(JOB['original47Arrays'])); reference = np.load(checked(JOB['bodyReference']))
        assert np.array_equal(p, original['points']) and np.array_equal(f, original['faces'])
        key = 'RiderBody__FullAnatomyReference'
        assert np.array_equal(bp, reference[key+'_basis']) and np.array_equal(bf, reference[key+'_triangles'])
    namespace = {**N, 'verify_cached_source': verify_cached_source, 'execution': execution}
    exec(compile(source, str(checked(JOB['native'])), 'exec'), namespace)
    return namespace['apply'], source


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'bind': bind(args[1])
    elif args[0] in ('prepare', 'apply'):
        value, execution = stage(args[1])
        if args[0] == 'prepare': prepared_function(value, execution)[0](checked(FROZEN), args[2])
        else: applied_function(value, execution)[0](checked(FROZEN), args[2], args[3])
    else: raise AssertionError(args)
