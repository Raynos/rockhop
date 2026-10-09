"""Explicit47 component intake/checkpoint; parent serial CPU2 Blender only.

Only hoodie, qualified41 gloves, original75 and full anatomy are present.
No fullmaster claim, dense pass, action authoring, export or accepted art.
"""
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'
io = runpy.run_path(str(ROOT/'assets/blender/rider-rebuild/selected-sleeve-tailoring27/checkpoint04.py'))
pin, checked = io['pin'], io['checked']
COMPONENT41 = {'path': 'assets/blender/rider-rebuild/selected-glove-component41/component.py',
               'sha256': 'ea4d19ff842fb9e5dc65fe27cbd48f76bcc09628f86f86bdfddc996465ebc251'}
SLEEVE38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/sleeve38.py',
            'sha256': 'd41ab8201abd8ca40bae501375af0ce4d40123cd910a82a9f2c7fa0f97e2a23f'}
CHECKPOINT38 = {'path': 'assets/blender/rider-rebuild/selected-wardrobe-integration38/sleeve_checkpoint.py',
                'sha256': 'a7519a567fcabe067f13342a955938553fd97d91ffe8a1c7e3c21b63235c265e'}
REFERENCE05 = {'path': 'harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.npz',
               'sha256': '01f752d72e94dbab81cc7a193adbd2dd7bba26df919b48454d8937fa9665dcc5'}
FROZEN_FREEZE = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/freeze_inputs.py',
                 'sha256': '1011883f199d77b820495920aff4210da5256a4d60dfcea54714f6c774bd0058'}
FIELD28 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/field.py',
           'sha256': '09e24d646bbf013a1adb9a7bedc53dc29510507678dd40abbf11d1fe175e131a'}
GLOVES = ('ActualSelectedGlove.L', 'ActualSelectedGlove.R')
REFERENCE = 'RiderBody__FullAnatomyReference'
MESHES = {'RiderHoodie', *GLOVES}
OBJECTS = MESHES | {'RiderSkeleton', REFERENCE}
PROTECTED = set(GLOVES) | {REFERENCE}
INTAKE_PENDING = 'UNACCEPTED_SLEEVE47_INTAKE_SAVED_REOPEN_PENDING'
INTAKE_QUALIFIED = 'UNACCEPTED_SLEEVE47_INTAKE_REOPENED_CONSTRUCTION_PENDING'
PENDING = 'UNACCEPTED_SLEEVE47_CONSTRUCTED_SAVED_REOPEN_PENDING'
QUALIFIED = 'UNACCEPTED_SLEEVE47_COMPONENT_REOPENED_DENSE_AND_MOTION_PENDING'


def write(path, value):
    assert not path.exists(), ('Refuse overwrite', str(path))
    path.write_text(json.dumps(value, indent=2)+'\n')


def read(row):
    return json.loads(checked(row).read_text())


def component41_gate(row):
    c = runpy.run_path(str(checked(COMPONENT41)))
    assert row['sourceRecipe'] == COMPONENT41 and row['status'] == c['QUALIFIED']
    assert row['methodAncestry'] == c['FROZEN04'] and row['sourceInput'] == c['INPUT10']
    assert set(row['objects']) == set(GLOVES)
    assert row['acceptedArt'] is False and row['protectedValidationPassed'] is True
    assert row['exact75RestUnchanged'] is row['fullReferenceUnchanged'] is True
    assert row['constructedGloveGeometryAndNamedFieldsExactAfterReopen'] is True
    assert row['protectedValidationStage'] == 'SEPARATE_REOPENED_COMPONENT_NATIVE'
    assert row['nativeStorage'] == {'compressed': False, 'reopenVerified': True}
    assert all(r['allSourcePrefixNamedFieldsExact'] and r['allNewSourceParentNamedFieldsExactAfterFloat32Storage']
               for r in row['objects'].values())
    return c


def helpers(prior):
    return (runpy.run_path(str(checked(prior['restHelper']))),
            runpy.run_path(str(checked(prior['geometryHelper'])))['geometry'])


def metadata(obj, packed_maps):
    c = runpy.run_path(str(checked(COMPONENT41)))
    return {**c['metadata'](obj, packed_maps),
            'matrixParentInverse': [list(r) for r in obj.matrix_parent_inverse],
            'groupLocks': [g.lock_weight for g in obj.vertex_groups]}


def canonical(value):
    return json.loads(json.dumps(value))


def scoped(bpy):
    assert {o.name for o in bpy.data.objects} == OBJECTS
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == MESHES
    assert bpy.data.objects[REFERENCE].hide_render
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    return rig


def save_native(out, filename, bpy):
    native = out/filename
    assert not native.exists()
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream: assert stream.read(7) == b'BLENDER'
    return pin(native)


def intake(component_path, out, bpy):
    component_path, out = Path(component_path).resolve(), Path(out).resolve()
    assert out.is_relative_to(OUT) and not out.exists()
    receipt = json.loads(component_path.read_text()); component41_gate(receipt)
    prior = read(receipt['priorInput']); assert receipt['sourceMaster'] == prior['master']
    author, geometry = helpers(prior)
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])), use_scripts=False) == {'FINISHED'}
    assert {o.name for o in bpy.data.objects} == PROTECTED|{'RiderSkeleton'}
    rig = bpy.data.objects['RiderSkeleton']; rest_before = author['rest'](rig)
    assert canonical(rest_before) == receipt['protectedBefore']['rest']
    before = {o.as_pointer() for o in bpy.data.objects}
    with bpy.data.libraries.load(str(checked(prior['master'])), link=False) as (available, loaded):
        assert 'RiderHoodie' in available.objects
        loaded.objects = ['RiderHoodie']
    hoodie = loaded.objects[0]; assert hoodie and hoodie.name == 'RiderHoodie'
    new = [o for o in bpy.data.objects if o.as_pointer() not in before]
    assert all(o == hoodie or o.type == 'ARMATURE' for o in new), 'Unexpected hoodie object dependency'
    assert hoodie.matrix_world.is_identity and not hoodie.data.shape_keys
    assert hoodie.animation_data is None and not hoodie.constraints
    for donor in (o for o in new if o.type == 'ARMATURE'):
        assert donor.matrix_world == rig.matrix_world and author['rest'](donor) == rest_before
    # Preserve exact object world/parent inverse and all mesh/material fields.
    # Only the duplicate original75 dependency is rebound to identical original75.
    world, inverse = hoodie.matrix_world.copy(), hoodie.matrix_parent_inverse.copy()
    assert hoodie.parent is None or hoodie.parent in new
    if hoodie.parent: hoodie.parent = rig
    for mod in hoodie.modifiers:
        if mod.type == 'ARMATURE':
            assert mod.object in new
            mod.object = rig
    hoodie.matrix_parent_inverse = inverse
    assert hoodie.matrix_world == world
    bpy.context.scene.collection.objects.link(hoodie)
    for donor in new:
        if donor != hoodie: bpy.data.objects.remove(donor, do_unlink=True)
    bpy.context.view_layer.update(); scoped(bpy)
    # No complete mesh fingerprint scans happen before the raw intake save.
    expected_meta = metadata(hoodie, author['packed_maps'])
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'status': INTAKE_PENDING, 'sourceRecipe': pin(__file__),
              'componentReceipt': pin(component_path), 'sourceMaster': prior['master'],
              'priorInput': receipt['priorInput'], 'sourceComponentNative': receipt['native'],
              'expectedRest': rest_before, 'expectedHoodieMetadata': expected_meta,
              'native': save_native(out, 'UNACCEPTED-selected-sleeve-intake47.blend', bpy),
              'scope': sorted(OBJECTS), 'protectedValidationPassed': False,
              'geometryGatesPassed': False, 'movingReviewPassed': False,
              'nativeStorage': {'compressed': False, 'reopenVerified': False}}
    write(out/'intake-raw.json', report)
    report['expectedHoodieGeometry'] = geometry(hoodie)
    write(out/'intake-pending.json', report)


def intake_gate(receipt):
    assert receipt['status'] == INTAKE_QUALIFIED and receipt['sourceRecipe'] == pin(__file__)
    assert receipt['acceptedArt'] is False and receipt['protectedValidationPassed'] is True
    assert receipt['originalSelectedHoodieGeometryExactAfterReopen'] is True
    assert receipt['exact75RestUnchanged'] is True and receipt['nativeStorage']['reopenVerified'] is True
    c = read(receipt['componentReceipt']); component41_gate(c)
    assert receipt['sourceMaster'] == c['sourceMaster'] and receipt['priorInput'] == c['priorInput']
    assert receipt['sourceComponentNative'] == c['native']
    assert receipt['expectedRest'] == c['protectedBefore']['rest']
    assert set(receipt['scope']) == OBJECTS
    return c


def qualify_intake(pending_path, bpy):
    pending_path = Path(pending_path).resolve(); assert pending_path.is_relative_to(OUT)
    report = json.loads(pending_path.read_text())
    assert report['status'] == INTAKE_PENDING and report['sourceRecipe'] == pin(__file__)
    c = read(report['componentReceipt']); component41_gate(c)
    prior = read(report['priorInput']); assert prior['master'] == report['sourceMaster'] == c['sourceMaster']
    author, geometry = helpers(prior)
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False) == {'FINISHED'}
    rig = scoped(bpy)
    assert canonical(author['rest'](rig)) == report['expectedRest'] == c['protectedBefore']['rest']
    assert geometry(bpy.data.objects[REFERENCE]) == c['protectedBefore']['fullReference']
    for name in GLOVES: assert geometry(bpy.data.objects[name]) == c['expectedConstructedGeometry'][name]
    hoodie = bpy.data.objects['RiderHoodie']
    assert geometry(hoodie) == report['expectedHoodieGeometry']
    assert canonical(metadata(hoodie, author['packed_maps'])) == report['expectedHoodieMetadata']
    report.update(status=INTAKE_QUALIFIED, protectedValidationPassed=True,
                  originalSelectedHoodieGeometryExactAfterReopen=True, exact75RestUnchanged=True,
                  protectedValidationStage='SEPARATE_REOPENED_COMPONENT_NATIVE', pendingReceipt=pin(pending_path))
    report['nativeStorage']['reopenVerified'] = True
    write(pending_path.parent/'intake-qualified.json', report)


def freeze(intake_path, output):
    intake_path, output = Path(intake_path).resolve(), Path(output).resolve()
    assert output.is_relative_to(HERE) and not output.exists()
    receipt = json.loads(intake_path.read_text()); c = intake_gate(receipt)
    # Reuse the literal frozen28 configuration, including every numeric target.
    source = checked(FROZEN_FREEZE).read_text()
    replacements = {
        "assert not output.exists() and output.is_relative_to(HERE)": "assert not output.exists() and output.is_relative_to(NEW_HERE)",
        "assert glove['status'] == 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED'": "intake_gate(glove)",
        "assert glove['originalHoodieUnchangedBeforeSave'] and glove['exact75RestUnchanged']": "assert glove['exact75RestUnchanged']"}
    for old, new in replacements.items():
        assert source.count(old) == 1
        source = source.replace(old, new)
    namespace = {'__name__': 'sleeve47_exact_freeze28', '__file__': str(checked(FROZEN_FREEZE)),
                 'NEW_HERE': HERE, 'intake_gate': intake_gate}
    exec(compile(source, namespace['__file__'], 'exec'), namespace)
    argv = sys.argv
    try:
        sys.argv = [str(HERE/'component.py'), str(intake_path), str(checked(REFERENCE05)), str(output)]
        namespace['main']()
    finally: sys.argv = argv
    config = json.loads(output.read_text())
    config['pins'].update(component47=pin(__file__), constructor47=pin(HERE/'sleeve47.py'),
                          lifetimeWrapper38=SLEEVE38, checkpointHelper38=CHECKPOINT38,
                          componentReceipt41=receipt['componentReceipt'])
    output.write_text(json.dumps(config, indent=2)+'\n')
    for row in config['pins'].values(): checked(row)
    assert config['pins']['referenceSamples'] == REFERENCE05
    assert config['pins']['fieldHelper'] == FIELD28
    print(json.dumps({'input': pin(output), 'nativeRunExecuted': False}))


def source_identity(config, report):
    assert config['pins']['component47'] == pin(__file__)
    assert config['pins']['constructor47'] == pin(HERE/'sleeve47.py')
    assert config['pins']['lifetimeWrapper38'] == SLEEVE38 and config['pins']['checkpointHelper38'] == CHECKPOINT38
    wrapper = runpy.run_path(str(checked(SLEEVE38)))
    assert report['originalConstructor'] == wrapper['ORIGINAL']
    assert report['recipeSHA256'] == config['pins']['constructor47']['sha256']
    assert config['pins']['referenceSamples'] == REFERENCE05
    assert config['pins']['fieldHelper'] == FIELD28
    for row in config['pins'].values(): checked(row)
    intake = read(config['pins']['gloveReceipt']); intake_gate(intake)
    assert config['pins']['gloveNative'] == intake['native']
    assert config['pins']['priorInputs'] == intake['priorInput']
    assert config['pins']['componentReceipt41'] == intake['componentReceipt']


def save_pending(out, config_path, config, expected, report, bpy):
    out = Path(out).resolve(); assert out.is_relative_to(OUT) and out.is_dir()
    source_identity(config, report)
    assert set(expected['geometry']) == PROTECTED and report['acceptedArt'] is False
    assert json.loads(checked(pin(config_path)).read_text()) == config
    assert Path(bpy.data.filepath).resolve() == checked(config['pins']['gloveNative'])
    rig = scoped(bpy)
    author, geometry = helpers(read(config['pins']['priorInputs']))
    assert canonical(author['rest'](rig)) == canonical(expected['rest'])
    report['hoodieMetadataBeforeSave'] = metadata(bpy.data.objects['RiderHoodie'], author['packed_maps'])
    # Scratch release is inherited verbatim from sleeve38 before this call.
    native = save_native(out, 'UNACCEPTED-selected-sleeve-gloves-component47.blend', bpy)
    result = {**report, 'status': PENDING, 'scope': sorted(OBJECTS),
              'sourcePins': config['pins'], 'input': pin(config_path), 'native': native,
              'protectedValidationPassed': False, 'geometryGatesPassed': False,
              'poseEnclosurePassed': False, 'movingReviewPassed': False,
              'nativeStorage': {'compressed': False, 'reopenVerified': False},
              'preservationScope': 'Only component47 gloves, full anatomy and exact75 rest; absent fullmaster meshes/actions are not claimed.'}
    write(out/'construction-raw.json', result)
    witness = out/'protected-before-sleeve.json'
    write(witness, expected)
    result['expectedWitness'] = pin(witness)
    result['expectedRebuiltHoodieGeometry'] = geometry(bpy.data.objects['RiderHoodie'])
    write(out/'construction-pending.json', result)
    print(json.dumps({'native': native, 'status': PENDING}), flush=True)


def qualify(pending_path, bpy):
    pending_path = Path(pending_path).resolve(); assert pending_path.is_relative_to(OUT)
    report = json.loads(pending_path.read_text()); assert report['status'] == PENDING
    config = read(report['input']); source_identity(config, report)
    expected = read(report['expectedWitness']); assert set(expected['geometry']) == PROTECTED
    assert set(report['scope']) == OBJECTS
    checked(report['ancestry']['ancestry']); checked(report['field'])
    assert report['ancestry']['allSourcePrefixNamedFieldsExact'] is True
    assert report['ancestry']['allNewSourceParentNamedFieldsExactAfterFloat32Storage'] is True
    author, geometry = helpers(read(config['pins']['priorInputs']))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False) == {'FINISHED'}
    rig = scoped(bpy)
    assert canonical(author['rest'](rig)) == expected['rest']
    for name, fingerprint in expected['geometry'].items():
        assert geometry(bpy.data.objects[name]) == fingerprint, ('Changed component object', name)
    hoodie = bpy.data.objects['RiderHoodie']
    assert geometry(hoodie) == report['expectedRebuiltHoodieGeometry']
    assert canonical(metadata(hoodie, author['packed_maps'])) == report['hoodieMetadataBeforeSave']
    original_intake = read(config['pins']['gloveReceipt'])
    assert report['hoodieMetadataBeforeSave'] == original_intake['expectedHoodieMetadata']
    report.update(status=QUALIFIED, protectedValidationPassed=True, exact75RestUnchanged=True,
                  protectedValidationStage='SEPARATE_REOPENED_COMPONENT_NATIVE',
                  protectedGeometryUnchanged=expected['geometry'], pendingReceipt=pin(pending_path),
                  constructedHoodieGeometryAndNamedFieldsExactAfterReopen=True)
    report['nativeStorage']['reopenVerified'] = True
    write(pending_path.parent/'construction.json', report)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze':
        assert len(args) == 3
        freeze(*args[1:])
    else:
        import bpy
        if args[0] == 'intake':
            assert len(args) == 3
            intake(*args[1:], bpy)
        else:
            assert len(args) == 2 and args[0] in {'qualify-intake', 'qualify'}
            {'qualify-intake': qualify_intake, 'qualify': qualify}[args[0]](args[1], bpy)
