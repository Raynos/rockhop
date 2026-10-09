"""Save completed original28 cloth before expensive protected after-scans.

The pending native is never a qualification. A separate process must reopen
and compare every original protected fingerprint before construction.json is
issued for the unchanged six dense relation workers.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PENDING = 'UNACCEPTED_SLEEVE_SAVED_PROTECTED_VALIDATION_PENDING'
ORIGINAL = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/author.py',
            'sha256': 'e6a13cd8bc1d0ec18776da9fb4c8ec83598f7365807478ec9de6a87b394fa6e1'}


def pin(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT) and path.is_file()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest.hexdigest()}


def checked(row):
    assert set(row) == {'path', 'sha256'}
    path = (ROOT/row['path']).resolve()
    assert pin(path) == row, ('Changed input', row['path'])
    return path


def write(path, value):
    assert not path.exists(), ('Existing output', str(path))
    path.write_text(json.dumps(value, indent=2)+'\n')


def source_identity(config, report):
    current = {'constructor38': pin(HERE/'sleeve38.py'),
               'checkpointHelper38': pin(HERE/'sleeve_checkpoint.py')}
    assert all(config['pins'][name] == row for name, row in current.items())
    assert report['recipeSHA256'] == config['pins']['constructor38']['sha256']
    assert report['originalConstructor'] == ORIGINAL
    checked(ORIGINAL)
    return current


def save_pending(out, config_path, config, expected, report, bpy):
    out = Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28')
    assert out.is_dir() and report['acceptedArt'] is False
    source_identity(config, report)
    assert set(expected['geometry']) >= {'ActualSelectedGlove.L', 'ActualSelectedGlove.R',
                                         'RiderBody__FullAnatomyReference'}
    assert 'RiderHoodie' not in expected['geometry']
    assert json.loads(checked(pin(config_path)).read_text()) == config
    assert Path(bpy.data.filepath).resolve() == checked(config['pins']['gloveNative'])
    assert len(bpy.data.objects['RiderSkeleton'].data.bones) == 75
    assert all(bpy.data.objects[name].type == 'MESH' for name in expected['geometry'])
    checked(report['ancestry']['ancestry'])
    native = out/'UNACCEPTED-selected-sleeve-rebuild38.blend'
    witness = out/'protected-before-sleeve.json'
    pending = out/'construction-pending.json'
    assert not any(path.exists() for path in (native, witness, pending, out/'construction.json'))
    write(witness, {'acceptedArt': False, 'protectedValidationPassed': False,
                    'input': pin(config_path), 'sourcePins': config['pins'], **expected})
    print('SLEEVE38_SAVE_PENDING_UNCOMPRESSED', flush=True)
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream:
        assert stream.read(7) == b'BLENDER', 'Expected uncompressed native'
    result = {**report, 'status': PENDING, 'protectedValidationPassed': False,
              'geometryGatesPassed': False, 'poseEnclosurePassed': False, 'movingReviewPassed': False,
              'sourcePins': config['pins'], 'inputSHA256': pin(config_path)['sha256'],
              'native': pin(native), 'expectedWitness': pin(witness),
              'nativeStorage': {'compressed': False, 'saveOperatorFinished': True,
                                'rawHeaderChecked': True, 'reopenVerified': False}}
    assert 'protectedGeometryUnchanged' not in result and 'exact75RestUnchanged' not in result
    write(pending, result)
    print(json.dumps({'status': result['status'], 'native': result['native']}), flush=True)
    return result


def qualify(pending_path, bpy, load_helper):
    pending_path = Path(pending_path).resolve()
    assert pending_path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28')
    result = json.loads(pending_path.read_text())
    assert result['status'] == PENDING and result['protectedValidationPassed'] is False
    assert not (pending_path.parent/'construction.json').exists()
    expected = json.loads(checked(result['expectedWitness']).read_text())
    config = json.loads(checked(expected['input']).read_text())
    assert expected['sourcePins'] == result['sourcePins'] == config['pins']
    current = source_identity(config, result)
    for row in config['pins'].values():
        checked(row)
    prior = json.loads(checked(config['pins']['priorInputs']).read_text())
    glove = json.loads(checked(config['pins']['gloveReceipt']).read_text())
    assert glove['native'] == config['pins']['gloveNative']
    assert glove['status'] == 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED'
    assert glove['protectedValidationPassed'] is True
    assert glove['protectedValidationStage'] == 'SEPARATE_REOPENED_NATIVE'
    assert glove['sourceMaster'] == prior['master']
    checked(prior['master'])
    geometry = load_helper(str(checked(prior['geometryHelper'])))['geometry']
    rest = load_helper(str(checked(prior['restHelper'])))['rest']
    checked(result['ancestry']['ancestry'])
    checked(result['field'])
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(result['native'])), use_scripts=False) == {'FINISHED'}
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and json.loads(json.dumps(rest(rig))) == expected['rest']
    for name, signature in expected['geometry'].items():
        print('SLEEVE38_QUALIFY '+name, flush=True)
        assert geometry(bpy.data.objects[name]) == signature, ('Protected mismatch', name)
    result.update(status='UNACCEPTED_CONSTRUCTION_DENSE_AND_MOTION_PENDING',
                  protectedValidationPassed=True, protectedValidationStage='SEPARATE_REOPENED_NATIVE',
                  protectedGeometryUnchanged=expected['geometry'], exact75RestUnchanged=True,
                  pendingReceipt=pin(pending_path),
                  qualifiedBy={'qualifierRecipe': pin(HERE/'qualify-sleeve38.py'),
                               'sourcePins': current, 'originalConstructor': ORIGINAL})
    result['nativeStorage']['reopenVerified'] = True
    write(pending_path.parent/'construction.json', result)
    return result
