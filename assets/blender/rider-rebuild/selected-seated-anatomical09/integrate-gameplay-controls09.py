"""Parent CPU2 only: integrate proven gameplay controls into the selected outfit.

The original selected RiderSkeleton object and its 75 rest bones remain. The
exact qualified controls recipe adds only its declared nondeforming bones.
Actual saved control actions are appended unchanged, never reconstructed here.
"""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIMIT = .0001
PIN_NAMES = {'fullReceipt', 'fullNative', 'fullInput', 'fullRecipe',
             'controlsReceipt', 'gameplayControlsRecipe', 'controlsRecipe', 'commonBuildRecipe'}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def validate_lineage(config, full, control, package, full_config):
    """Strict result gates; source-ready and saved-but-unqualified are invalid."""
    assert config['accepted'] is False and set(config['pins']) == PIN_NAMES
    pins = config['pins']
    assert full['accepted'] is control['accepted'] is package['accepted'] is False
    assert full['status'] == 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING'
    assert control['status'] == 'NATIVE_MEASURED_GAMEPLAY_ACTIONS_UNACCEPTED'
    assert full['native'] == pins['fullNative']
    assert full['recipeSHA256'] == pins['fullRecipe']['sha256']
    assert full['inputSHA256'] == pins['fullInput']['sha256']
    assert full['sourcePins'] == full_config['pins']
    assert control['sourceReceipt'] == full_config['pins']['gameplayReceipt']
    assert control['recipe'] == pins['gameplayControlsRecipe']
    assert control['controlsRecipe'] == pins['controlsRecipe']
    assert control['commonBuildRecipe'] == pins['commonBuildRecipe']
    assert control['nativeRestExactlyPreserved'] is True
    assert control['shapeActivation'] == full['shapeActivation'] == package['shapeActivation'] == 0
    assert full['actions'] == [{key: value for key, value in action.items() if key != 'nativeWorldMatrices'}
                               for action in package['actions']]
    checks = full['checks']
    for key in ('allOriginalProtectedFieldsExact', 'allVertexGroupNamesAndFieldsExact',
                'originalActionsExact', 'originalKeyCoordinatesExact', 'native75RestExact',
                'visibleMeshesExact', 'checksUseReopenedNative'):
        assert checks[key] is True, key
    assert len(checks['matrixReplay']) == len(control['actions']) == len(package['actions']) == 2
    for replay, actual, captured in zip(checks['matrixReplay'], control['actions'], package['actions']):
        assert replay['action'] == actual['name'] == captured['name']
        assert replay['frames'] == 241 and 0 <= replay['maximumAffineBoundWithin2mM'] < LIMIT
        assert actual['controlAction'] == 'Author.'+captured['name']
        assert 0 <= actual['savedControlReplayMaximumAffineBoundWithin2mM'] < LIMIT
        assert 0 <= actual['bakeMaximumAffineBoundWithin2mM'] < LIMIT
        for key, value in captured.items():
            if key != 'nativeWorldMatrices':
                assert actual[key] == value, (actual['name'], key)
        assert len(actual['nativeWitnesses']) == 241
        for frame, witness in enumerate(actual['nativeWitnesses'], 1):
            assert witness['frame'] == frame and witness['sourceTick'] == (frame-1)*5
            assert 0 <= witness['capturedPoseBoundM'] < LIMIT and 0 <= witness['regionalOperatorBoundM'] < LIMIT
    recipes = package['source']['recipes']
    assert recipes['gameplayControls'] == pins['gameplayControlsRecipe']
    assert recipes['controls'] == pins['controlsRecipe']
    assert recipes['commonBuild'] == pins['commonBuildRecipe']


def first_pin(pin):
    """Pin sources with bounded reads, including under the default Python3.9."""
    relative = Path(pin['path'])
    assert set(pin) == {'path', 'sha256'} and not relative.is_absolute() and '..' not in relative.parts
    selected = (ROOT/relative).resolve()
    assert selected.is_relative_to(ROOT) and selected.is_file()
    digest = hashlib.sha256()
    with selected.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    assert digest.hexdigest() == pin['sha256'], pin
    return selected


def read_input(path):
    config = json.loads(path.read_text())
    # This dependency performs no Blender work when imported. Its exact hash is
    # checked before any of its helpers are used for the successful ancestry.
    assert config['accepted'] is False and set(config['pins']) == PIN_NAMES
    for pin in config['pins'].values():
        first_pin(pin)
    pins = config['pins']
    full_helper = module('gameplay08_source', first_pin(pins['fullRecipe']))
    assert first_pin(pins['fullRecipe']) == HERE/'append-measured-gameplay08.py'
    full_config, package = full_helper.read_input(first_pin(pins['fullInput']))
    full = json.loads(first_pin(pins['fullReceipt']).read_text())
    control = json.loads(first_pin(pins['controlsReceipt']).read_text())
    validate_lineage(config, full, control, package, full_config)
    for pin in (control['bakedNative'], control['nativeMatrices'], full['bodySurfaceArrays'],
                *(action['controlNative'] for action in control['actions'])):
        full_helper.pinned(pin)
    return config, full, control, package, full_config, full_helper


def rig_definition(rig, controls, scalar):
    """Compare authored behavior, with self-target identities made explicit.

    Mutable pose matrices and animation evaluation caches are excluded here;
    every resulting native75 matrix is independently checked at every key.
    """
    def self_pointer(value):
        assert value is None or value == rig, ('Unexpected external control target', value)
        return 'SELF' if value is not None else None
    bones = []
    for bone in rig.pose.bones:
        constraints = []
        for constraint in bone.constraints:
            assert constraint.type in {'IK', 'COPY_TRANSFORMS', 'COPY_ROTATION'}
            row = {'type': constraint.type, 'settings': scalar(constraint),
                   'target': self_pointer(constraint.target)}
            if constraint.type == 'IK':
                row['poleTarget'] = self_pointer(constraint.pole_target)
            constraints.append(row)
        properties = {key: {'value': bone[key], 'ui': bone.id_properties_ui(key).as_dict()}
                      for key in bone.keys()}
        bones.append({'name': bone.name, 'data': scalar(bone.bone),
            'rotationMode': bone.rotation_mode, 'ikStretch': bone.ik_stretch,
            'ikSettings': {key: getattr(bone, key) for key in (
                'lock_ik_x', 'lock_ik_y', 'lock_ik_z', 'use_ik_limit_x', 'use_ik_limit_y',
                'use_ik_limit_z', 'ik_min_x', 'ik_max_x', 'ik_min_y', 'ik_max_y',
                'ik_min_z', 'ik_max_z', 'ik_stiffness_x', 'ik_stiffness_y', 'ik_stiffness_z')},
            'constraints': constraints, 'properties': properties})
    drivers = []
    for curve in rig.animation_data.drivers:
        driver = curve.driver
        assert not curve.keyframe_points and not curve.sampled_points
        variables = []
        for variable in driver.variables:
            assert variable.type == 'SINGLE_PROP' and len(variable.targets) == 1
            target = variable.targets[0]
            variables.append({'name': variable.name, 'type': variable.type,
                'id': self_pointer(target.id), 'settings': scalar(target)})
        drivers.append({'path': curve.data_path, 'index': curve.array_index,
            'mute': curve.mute, 'driver': scalar(driver), 'variables': variables,
            'modifiers': [{'type': mod.type, 'settings': scalar(mod)} for mod in curve.modifiers]})
    return {'rest': controls.rest_rows(rig), 'bones': bones,
            'drivers': sorted(drivers, key=lambda row: (row['path'], row['index'])),
            'description': rig['M11_controls']}


def append_actual_action(bpy, scene, record, native_path, target, controls, helper, scalar):
    name = record['controlAction']
    assert name not in bpy.data.actions, ('Would replace an existing action', name)
    with bpy.data.libraries.load(str(native_path), link=False) as (source, data):
        assert 'RiderSkeleton' in source.objects and name in source.actions
        data.objects = ['RiderSkeleton']
        data.actions = [name]
    source_rig, action = data.objects[0], data.actions[0]
    assert source_rig.type == 'ARMATURE' and action.name == name
    assert source_rig.animation_data.action == action and len(action.slots) == 1
    scene.collection.objects.link(source_rig)
    action.use_fake_user = True
    original_action = helper.action_state(action)
    target.animation_data.action = action
    target.animation_data.action_slot = action.slots[0]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    expected, actual = rig_definition(source_rig, controls, scalar), rig_definition(target, controls, scalar)
    assert expected == actual, ('Installed controls differ from actual qualified source', name,
                               helper.exact_difference(expected, actual)[:20])
    data = source_rig.data
    bpy.data.objects.remove(source_rig, do_unlink=True)
    assert data.users == 0
    bpy.data.armatures.remove(data)
    return expected, original_action


def replay(bpy, np, rig, records, names, captured, baked, deactivated, full_helper):
    results = []
    for index, record in enumerate(records):
        # An NpzFile member decompresses on access. Read once per action, not
        # once for each of its 18,075 native joint comparisons.
        qualified = baked[f'pose{index}']
        full_helper.activate(bpy, rig, record['controlAction'])
        maxima = {'captured': {'boundM': 0., 'frame': None, 'bone': None},
                  'qualifiedControls': {'boundM': 0., 'frame': None, 'bone': None}}
        for frame in range(1, 242):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            full_helper.assert_zero_shapes(bpy, deactivated)
            for bone_index, name in enumerate(names):
                actual = np.asarray(rig.pose.bones[name].matrix)
                for kind, expected in (('captured', captured[index][frame-1, bone_index]),
                                       ('qualifiedControls', qualified[frame-1, bone_index])):
                    delta = actual-expected
                    bound = float(np.linalg.norm(delta[:3, :3], 2)*2+np.linalg.norm(delta[:3, 3]))
                    assert math.isfinite(bound)
                    if bound > maxima[kind]['boundM']:
                        maxima[kind] = {'boundM': bound, 'frame': frame, 'bone': name}
        results.append({'action': record['controlAction'], 'frames': 241, **maxima})
    return results


def integrate(input_path, out, bundle):
    config, full, control, package, full_config, full_helper = bundle
    pins = config['pins']
    helper = module('gameplay09_inspection', full_helper.pinned(full_config['pins']['inspectionHelper']))
    assert Path(helper.sculpt.__file__).resolve() == full_helper.pinned(full_config['pins']['sculptRecipe'])
    assert Path(helper.base.__file__).resolve() == full_helper.pinned(full_config['pins']['baseRecipe'])
    bpy, np = helper.bpy, helper.np
    controls = module('gameplay09_exact_controls', full_helper.pinned(pins['controlsRecipe']))
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    contract = json.loads(full_helper.pinned(package['source']['selectedContract']).read_text())
    names = package['boneNames']
    records = control['actions']
    captured = [np.asarray(action['nativeWorldMatrices'], dtype=np.float64) for action in package['actions']]
    baked = np.load(full_helper.pinned(control['nativeMatrices']), allow_pickle=False)
    assert baked['boneNames'].tolist() == names
    assert all(baked[f'pose{i}'].shape == captured[i].shape == (241, 75, 4, 4) for i in range(2))
    bpy.ops.wm.open_mainfile(filepath=str(full_helper.pinned(pins['fullNative'])), use_scripts=False)
    scene = bpy.context.scene
    rig = bpy.data.objects['RiderSkeleton']
    assert controls.rest_rows(rig) == contract['nativeRest']['bones']
    assert rig.matrix_world.is_identity and not rig.animation_data.drivers and not rig.animation_data.nla_tracks
    assert all(not bone.constraints for bone in rig.pose.bones)
    mesh_names = full['visibleMeshes']+[full_helper.REFERENCE]
    objects = [bpy.data.objects[name] for name in mesh_names]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    before = {obj.name: fingerprint(obj) for obj in objects}
    fields = {obj.name: full_helper.exact_group_digest(obj) for obj in objects}
    keys = full_helper.key_coordinates(helper, objects)
    actions = {action.name: helper.action_state(action) for action in bpy.data.actions}
    for action in bpy.data.actions:
        action.use_fake_user = True
    visibility = [(obj.name, obj.hide_viewport, obj.hide_get()) for obj in objects]
    for obj in objects:
        obj.hide_viewport = True
    original_object, original_data = rig, rig.data
    context = controls.install(rig, contract)
    assert rig == original_object and rig.data == original_data
    assert context['names'] == names and controls.rest_rows(rig, set(names)) == contract['nativeRest']['bones']
    assert all(not bone.use_deform for bone in rig.data.bones if bone.name not in names)
    definitions, appended_actions = [], {}
    for record in records:
        definition, action = append_actual_action(bpy, scene, record, full_helper.pinned(record['controlNative']),
                                                   rig, controls, helper, native_helpers['scalar_rna'])
        definitions.append(definition)
        appended_actions[record['controlAction']] = action
    assert definitions[0] == definitions[1], 'Two qualified actions must use one exact control rig'
    expected_definition = definitions[0]
    assert set(bpy.data.actions.keys()) == set(actions)|set(appended_actions), 'Undeclared action appended'
    full_helper.activate(bpy, rig, records[0]['controlAction'])
    scene.frame_start = 1
    scene.frame_end = 241
    scene.render.fps = 24
    scene.render.fps_base = 1
    scene.frame_set(1)
    for name, hidden_viewport, hidden_get in visibility:
        obj = bpy.data.objects[name]
        obj.hide_viewport = hidden_viewport
        obj.hide_set(hidden_get)
    bpy.context.view_layer.update()
    full_helper.assert_zero_shapes(bpy, full['shapeZeroActions'])
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-selected-full-live-gameplay-controls.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    saved = full_helper.pin_file(native)
    checkpoint = {'accepted': False, 'status': 'SELECTED_FULL_LIVE_CONTROLS_SAVED_REOPEN_PENDING',
        'sourcePins': pins, 'recipeSHA256': full_helper.sha(__file__), 'input': full_helper.pin_file(input_path),
        'native': saved, 'nativeFileCompressed': False, 'sourceRigObjectAndArmatureRetained': True,
        'original75RestExact': True, 'addedBoneNames': [bone.name for bone in rig.data.bones if bone.name not in names],
        'actualControlDefinitionsExact': True, 'actualControlActionsUnchanged': list(appended_actions),
        'visibleMeshes': full['visibleMeshes'], 'shapeActivation': 0,
        'limits': ['Full selected outfit with live controls; moving art, surfaces, phone and runtime remain unaccepted.',
            'Original baked actions are retained unchanged as inactive data. Playing deform-only actions requires disabling the live constraints and finger drivers; no action-switch system is added.',
            'The complete native75 is compared directly with actual physics poses and qualified control matrices at all 482 keys, after saving and reopening. Between-key physics was not captured.']}
    full_helper.write_json(out/'checkpoint.json', checkpoint)
    print(json.dumps({'checkpoint': saved, 'controlActions': list(appended_actions)}), flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']
    objects = [bpy.data.objects[name] for name in mesh_names]
    for obj in objects:
        obj.hide_viewport = True
    replay_results = replay(bpy, np, rig, records, names, captured, baked,
                            full['shapeZeroActions'], full_helper)
    full_helper.activate(bpy, rig, records[0]['controlAction'])
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    checks = {'allRecordedNativeMatrices': replay_results,
        'controlDefinitionExactAfterReopen': rig_definition(rig, controls, native_helpers['scalar_rna']) == expected_definition,
        'original75RestExact': controls.rest_rows(rig, set(names)) == contract['nativeRest']['bones'],
        'allProtectedMeshFieldsExact': before == {obj.name: fingerprint(obj) for obj in objects},
        'allVertexGroupFieldsExact': fields == {obj.name: full_helper.exact_group_digest(obj) for obj in objects},
        'allOriginalKeyCoordinatesExact': keys == full_helper.key_coordinates(helper, objects),
        'originalActionsExact': actions == {name: helper.action_state(bpy.data.actions[name]) for name in actions},
        'actualControlActionsExact': appended_actions == {name: helper.action_state(bpy.data.actions[name]) for name in appended_actions},
        'allVisibleMeshNamesExact': {obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render} == set(full['visibleMeshes']),
        'allAddedBonesNondeforming': all(not bone.use_deform for bone in rig.data.bones if bone.name not in names)}
    full_helper.write_json(out/'checks.json', {'accepted': False, 'checks': checks})
    assert all(value is True for key, value in checks.items() if key != 'allRecordedNativeMatrices'), checks
    assert all(row[kind]['boundM'] < LIMIT for row in replay_results for kind in ('captured', 'qualifiedControls')), replay_results
    for name, hidden_viewport, hidden_get in visibility:
        obj = bpy.data.objects[name]
        obj.hide_viewport = hidden_viewport
        obj.hide_set(hidden_get)
    assert full_helper.pin_file(native) == saved
    for pin in pins.values():
        full_helper.pinned(pin)
    full_helper.write_json(out/'receipt.json', {**checkpoint,
        'status': 'SELECTED_FULL_LIVE_CONTROLS_REOPEN_PASS_ART_PENDING', 'checks': checks,
        'declaredControls': context['controls'], 'actions': records})


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if len(args) == 2 and args[0] == '--validate-input':
        path = Path(args[1]).resolve()
        bundle = read_input(path)
        print(json.dumps({'accepted': False, 'status': 'FULL_LIVE_CONTROL_INPUT_VALID_NATIVE_PENDING',
                          'input': bundle[-1].pin_file(path)}))
        return
    assert len(args) == 2, 'Use -- INPUT.json FRESH_OUTPUT, or --validate-input INPUT.json'
    path, out = map(lambda value: Path(value).resolve(), args)
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    integrate(path, out, read_input(path))


if __name__ == '__main__':
    main()
