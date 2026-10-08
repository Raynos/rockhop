"""Persist finished glove geometry before the separate protected-mesh scan."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PENDING = 'UNACCEPTED_GLOVES_SAVED_PROTECTED_VALIDATION_PENDING'


def pin(path):
    path = Path(path).resolve(); assert path.is_relative_to(ROOT) and path.is_file()
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1048576): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest()}


def checked(row):
    path = ROOT/row['path']; assert pin(path) == row, ('Changed input', row['path'])
    return path


def save_pending(out, recipe, state, inputs, input_pin, bpy):
    out = Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild') and out.is_dir()
    native = out/'UNACCEPTED-gloves-only-checkpoint.blend'
    receipt = out/'gloves-only-pending.json'; witness = out/'protected-before-gloves.json'
    assert not any(p.exists() for p in (native, receipt, witness))
    assert state and set(state['names']) == set(state['fingerprints'])
    assert 'RiderHoodie' in state['names'] and 'RiderBody__FullAnatomyReference' in state['names']
    assert json.loads(checked(input_pin).read_text()) == inputs
    assert Path(bpy.data.filepath).resolve() == checked(inputs['master'])
    assert pin(ROOT/recipe['path']) == recipe
    objects = bpy.data.objects; rig = objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and state['rest'](rig) == state['rig']
    for name in state['names']:
        assert objects[name].name == name and objects[name].type == 'MESH'
    ancestry = {}
    for side in ('L', 'R'):
        name = 'ActualSelectedGlove.'+side; obj = objects[name]
        assert obj.type == 'MESH' and obj.vertex_groups
        ancestry[name] = {**pin(out/(name+'-ancestry.npz')),
                          'vertices': len(obj.data.vertices), 'polygons': len(obj.data.polygons)}
    expected = {'status': 'EXPECTED_PRE_GLOVE_WITNESS_ONLY', 'protectedValidationPassed': False,
                'sourceMaster': inputs['master'], 'sourceRecipe': recipe, 'sourceInput': input_pin,
                'geometryHelper': inputs['geometryHelper'], 'restHelper': inputs['restHelper'],
                'protectedNames': state['names'], 'expectedProtectedGeometry': state['fingerprints'],
                'expectedRest': state['rig'], 'exact75RestUnchangedBeforeSave': True}
    witness.write_text(json.dumps(expected, indent=2)+'\n')
    print('GLOVE_CHECKPOINT_SAVE '+json.dumps({'compress': False, 'protectedValidationPassed': False}), flush=True)
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    assert native.is_file(), 'No final native file'
    with native.open('rb') as f: assert f.read(7) == b'BLENDER', 'Native is not uncompressed'
    report = {'status': PENDING, 'acceptedArt': False, 'protectedValidationPassed': False,
              'geometryGatesPassed': False, 'movingReviewPassed': False,
              'sourceMaster': inputs['master'], 'sourceRecipe': recipe,
              'gloveObjects': ancestry, 'native': pin(native), 'expectedWitness': pin(witness),
              'exact75RestUnchangedBeforeSave': True,
              'nativeStorage': {'compressed': False, 'bytes': native.stat().st_size,
                                'saveOperatorFinished': True, 'rawHeaderChecked': True,
                                'reopenVerified': False}}
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    print('GLOVE_CHECKPOINT_SAVED_PENDING '+json.dumps(report['native']), flush=True)
    return report


def qualify(pending_path, bpy, load_helper):
    pending_path = Path(pending_path).resolve()
    assert pending_path.is_relative_to(ROOT/'harness/out/rider-rebuild')
    qualified_path = pending_path.with_name('gloves-only-qualified.json')
    assert not qualified_path.exists()
    report = json.loads(pending_path.read_text()); assert report['status'] == PENDING
    assert report['protectedValidationPassed'] is False
    assert set(report['gloveObjects']) == {'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
    expected = json.loads(checked(report['expectedWitness']).read_text())
    assert expected['sourceMaster'] == report['sourceMaster'] and expected['sourceRecipe'] == report['sourceRecipe']
    inputs = json.loads(checked(expected['sourceInput']).read_text())
    assert inputs['master'] == expected['sourceMaster']
    checked(inputs['master'])
    for name in ('geometryHelper', 'restHelper'): assert inputs[name] == expected[name]
    checked(expected['sourceRecipe'])
    geometry = load_helper(str(checked(expected['geometryHelper'])))['geometry']
    rest = load_helper(str(checked(expected['restHelper'])))['rest']
    for row in report['gloveObjects'].values(): checked({k: row[k] for k in ('path', 'sha256')})
    native = checked(report['native'])
    assert bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False) == {'FINISHED'}
    objects = bpy.data.objects; rig = objects['RiderSkeleton']
    assert len(rig.data.bones) == 75
    assert json.loads(json.dumps(rest(rig))) == expected['expectedRest'], 'Reopened native75 rest mismatch'
    assert set(expected['protectedNames']) == set(expected['expectedProtectedGeometry'])
    assert {'RiderHoodie', 'RiderBody__FullAnatomyReference'} <= set(expected['protectedNames'])
    for name in expected['protectedNames']:
        print('GLOVE_CHECKPOINT_QUALIFY '+name, flush=True)
        assert geometry(objects[name]) == expected['expectedProtectedGeometry'][name], ('Protected mismatch', name)
    for name, row in report['gloveObjects'].items():
        obj = objects[name]
        assert obj.type == 'MESH' and obj.vertex_groups
        assert len(obj.data.vertices) == row['vertices'] and len(obj.data.polygons) == row['polygons']
    report.update(status='UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED',
                  protectedValidationPassed=True, protectedValidationStage='SEPARATE_REOPENED_NATIVE',
                  protectedGeometryUnchanged=expected['expectedProtectedGeometry'], exact75RestUnchanged=True,
                  originalHoodieUnchangedBeforeSave=True, pendingReceipt=pin(pending_path))
    report['nativeStorage']['reopenVerified'] = True
    qualified_path.write_text(json.dumps(report, indent=2)+'\n')
    return report
