"""Parent CPU2 only: measured mode analysis, then exact editable construction.

--analyze INPUT FRESH_OUT
--build INPUT ACTUAL_ANALYSIS_RECEIPT FRESH_OUT
--validate-input INPUT
No appearance mesh is loaded; the complete selected native remains untouched.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIMIT = .0001
PIN_NAMES = {'convertedReceipt', 'capturedPoses', 'selectedNative', 'selectedContract',
             'frozenGameplayControls', 'frozenControls', 'commonBuild', 'conditionedControls',
             'modePolicy', 'nativePlayback', 'actualDiagnostic', 'builder',
             'genericReceipt', 'genericNative', 'genericMatrices', 'genericContract', 'genericProvenance'}
GENERIC = [('RiderIdle', 73), ('RiderWalk', 31), ('RiderJog', 19),
           ('RiderTurn90', 73), ('RiderJumpLand', 61), ('RiderRangeOfMotion', 289)]


def pin_file(path):
    path = path.resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest.hexdigest()}


def pinned(pin):
    path = (ROOT/pin['path']).resolve()
    assert path.is_relative_to(ROOT) and pin_file(path) == pin, pin
    return path


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def read_input(path):
    config = json.loads(path.read_text())
    assert config['accepted'] is False and set(config['pins']) == PIN_NAMES
    pins = config['pins']
    for pin in pins.values():
        pinned(pin)
    assert pinned(pins['builder']) == Path(__file__).resolve()
    read = lambda name: json.loads(pinned(pins[name]).read_text())
    receipt, package, contract, diagnostic = [read(name) for name in (
        'convertedReceipt', 'capturedPoses', 'selectedContract', 'actualDiagnostic')]
    assert receipt['status'] == package['status'] == 'MEASURED_GAMEPLAY_NATIVE_POSES_UNACCEPTED'
    assert receipt['accepted'] is package['accepted'] is diagnostic['accepted'] is False
    assert receipt['nativePoseJSON'] == pins['capturedPoses'] and receipt['source'] == package['source']
    source = package['source']
    assert source['selectedNative'] == pins['selectedNative'] and source['selectedContract'] == pins['selectedContract']
    assert source['recipes']['gameplayControls'] == pins['frozenGameplayControls']
    assert source['recipes']['controls'] == pins['frozenControls'] and source['recipes']['commonBuild'] == pins['commonBuild']
    assert diagnostic['status'] == 'SINGULARITY_DIAGNOSTIC_COMPLETE_NO_CONTROL_OR_ART_PASS'
    assert diagnostic['sourcePins']['capturedPoses'] == pins['capturedPoses']
    observed = {row['stage']: row['maximumAffineBoundWithin2mM'] for row in diagnostic['bounds']}
    assert observed['reopened-ik-off-keyed-prepose'] < LIMIT < observed['reopened-ik-on']
    assert package['nativeRest'] == contract['nativeRest'] and len(package['boneNames']) == 75
    generic, generic_contract, provenance = [read(name) for name in (
        'genericReceipt', 'genericContract', 'genericProvenance')]
    assert generic['accepted'] is False and generic['status'] == 'NATIVE_CONTROL_ACTION_PACKAGE_UNACCEPTED'
    assert generic['bakedNative'] == pins['genericNative']
    assert generic['source']['contract'] == pins['genericContract']
    assert generic_contract['nativeRest'] == contract['nativeRest']
    assert [(row['name'], row['frameRange'][1]) for row in generic['actions']] == GENERIC
    assert all(row['frameRange'][0] == 1 and row['fps'] == 24 and
               row['bakeMaximumAffineBoundWithin2mM'] < LIMIT for row in generic['actions'])
    for role, name in [('nativeReceipt', 'genericReceipt'), ('bakedNative', 'genericNative'),
                       ('nativeMatrices', 'genericMatrices'), ('nativeContract', 'genericContract')]:
        assert provenance['pins'][role] == pins[name]
    assert generic['sources']['build.py'] == pins['commonBuild']['sha256']
    assert generic['sources']['controls.py'] == pins['frozenControls']['sha256']
    assert [row['name'] for row in package['actions']] == ['RiderGameplayLeanRookie', 'RiderGameplayLeanPro']
    for action in package['actions']:
        assert action['frameRange'] == [1, 241] and action['fps'] == 24 and action['shapeActivation'] == 0
        assert action['sourceTicks'] == list(range(0, 1201, 5))
    for pin in [receipt['input'], receipt['recipe'], *source['recipes'].values(), *source['reports'].values(),
                *contract['gameplayLeanReview']['sourcePins']]:
        pinned(pin)
    return config, package, contract


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime(config):
    sys.path.insert(0, str(HERE))
    pins = config['pins']
    original = load_module('frozen_conditioning_gameplay02', pinned(pins['frozenGameplayControls']))
    import build
    import controls
    assert Path(build.__file__).resolve() == pinned(pins['commonBuild'])
    assert Path(controls.__file__).resolve() == pinned(pins['frozenControls'])
    conditioned = load_module('conditioned_controls04', pinned(pins['conditionedControls']))
    policy = load_module('conditioned_policy04', pinned(pins['modePolicy']))
    playback = load_module('native_playback04', pinned(pins['nativePlayback']))
    return original, build, conditioned, policy, playback


def worlds(np, rig, names):
    return np.asarray([list(map(list, rig.pose.bones[name].matrix)) for name in names], dtype=np.float64)


def bounds(np, actual, wanted):
    delta = actual-wanted
    result = np.linalg.norm(delta[:, :3, :3], 2, axis=(1, 2))*2+np.linalg.norm(delta[:, :3, 3], axis=1)
    assert np.isfinite(result).all()
    return result


def activate(rig, action):
    assert len(action.slots) == 1
    rig.animation_data_create()
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]


def reset_native(rig, names):
    for name in names:
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)


def limb_groups(rig, context):
    return {limb['kind']+limb['side']: [i for i, name in enumerate(context['names'])
        if name == limb['uppers'][0] or any(parent.name == limb['uppers'][0]
        for parent in rig.data.bones[name].parent_recursive)] for limb in context['limbs']}


def set_modes(rig, context, modes):
    rig[context['liveProperty']] = 1.
    for limb in context['limbs']:
        rig.pose.bones[limb['targetControl']][context['ikProperty']] = float(modes[limb['kind']+limb['side']])


def analyze(input_path, out, config, package, contract, rt):
    original, build, conditioned, policy, _ = rt
    bpy, np, Matrix = original.bpy, original.np, original.Matrix
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rig = build.load_rig(pinned(config['pins']['selectedNative']))
    assert not bpy.data.meshes
    context = conditioned.install(rig, contract)
    names = context['names']
    groups = limb_groups(rig, context)
    other = sorted(set(range(75))-set(i for indices in groups.values() for i in indices))
    all_ik = {name: 1 for name in groups}
    all_fk = {name: 0 for name in groups}
    out.mkdir(parents=True)
    results = []
    for record in package['actions']:
        measurements = {name: {'ikError': [], 'fkError': [], 'difference': []} for name in groups}
        whole_fk, whole_ik = [], []
        for frame, sample in enumerate(record['nativeWorldMatrices'], 1):
            bpy.context.scene.frame_set(frame)
            reset_native(rig, names)
            set_modes(rig, context, all_ik)
            wanted = {name: Matrix(value) for name, value in zip(names, sample)}
            expected = np.asarray(sample, dtype=np.float64)
            try:
                original.reconstruct(rig, context, wanted)
            except AssertionError as error:
                value = error.args[0]
                assert isinstance(value, tuple) and value[0] == 'Native live controls differ from actual gameplay', error
            ik_world = worlds(np, rig, names)
            set_modes(rig, context, all_fk)
            bpy.context.view_layer.update()
            fk_world = worlds(np, rig, names)
            ik_error, fk_error = bounds(np, ik_world, expected), bounds(np, fk_world, expected)
            difference = bounds(np, ik_world, fk_world)
            row = {'action': record['name'], 'frame': frame, 'sourceTick': (frame-1)*5,
                   'maximumFKBoundM': float(max(fk_error)), 'maximumIKBoundM': float(max(ik_error))}
            if max(fk_error) >= LIMIT or max(ik_error[other], default=0.) >= LIMIT:
                write(out/'failed-analysis.json', {**row, 'accepted': False, 'bones': names,
                    'fkErrorsM': fk_error.tolist(), 'ikErrorsM': ik_error.tolist()})
            assert max(fk_error) < LIMIT, ('Keyed FK does not preserve captured native75', row)
            assert max(ik_error[other], default=0.) < LIMIT, ('Failure outside conditionable limb', row)
            whole_fk.append(float(max(fk_error)))
            whole_ik.append(float(max(ik_error)))
            for name, indices in groups.items():
                for key, array in (('ikError', ik_error), ('fkError', fk_error), ('difference', difference)):
                    measurements[name][key].append(float(max(array[indices])))
        modes = {name: policy.conditioned_modes(values['ikError'], values['fkError'], values['difference'])
                 for name, values in measurements.items()}
        results.append({'name': record['name'], 'bike': record['bike'], 'modes': modes,
            'measurements': measurements, 'maximumFKBoundM': max(whole_fk), 'maximumIKBoundM': max(whole_ik)})
        write(out/'partial-analysis.json', {'accepted': False, 'actions': results})
    assert conditioned.rest_rows(rig, set(names)) == contract['nativeRest']['bones']
    write(out/'receipt.json', {'accepted': False, 'status': 'CONDITIONED_MODE_PLAN_MEASURED_NATIVE_BUILD_PENDING',
        'input': pin_file(input_path), 'recipe': config['pins']['builder'], 'sourcePins': config['pins'],
        'actions': results, 'native75RestExact': True, 'limitM': LIMIT,
        'limits': ['Both FK and IK evaluated once per recorded key; no solver or threshold change.',
            'FK intervals expand to measured agreeing transition keys. No saved-action or full-outfit pass yet.']})


def original_playback_references(bpy, np, build, conditioned, playback, rig, native, names, config, contract):
    with bpy.data.libraries.load(str(native), link=False) as (source, data):
        data.actions = [name for name in source.actions if name not in bpy.data.actions]
    originals = [action for action in bpy.data.actions if playback.eligible(action, set(names))]
    generic_names = [name for name, _ in GENERIC]
    assert not any(name in bpy.data.actions for name in generic_names)
    with bpy.data.libraries.load(str(pinned(config['pins']['genericNative'])), link=False) as (source, data):
        assert set(generic_names) <= set(source.actions)
        data.objects = ['RiderSkeleton']
        data.actions = generic_names
    generic_rig = data.objects[0]
    assert conditioned.rest_rows(generic_rig) == contract['nativeRest']['bones']
    assert generic_rig.matrix_world.is_identity and all(not bone.constraints for bone in generic_rig.pose.bones)
    assert not generic_rig.animation_data or not generic_rig.animation_data.drivers
    generic_actions = data.actions
    assert [action.name for action in generic_actions] == generic_names
    for action in generic_actions:
        assert playback.eligible(action, set(names))
        action.use_fake_user = True
    armature = generic_rig.data
    bpy.data.objects.remove(generic_rig, do_unlink=True)
    assert armature.users == 0
    bpy.data.armatures.remove(armature)
    assert not bpy.data.meshes
    with np.load(pinned(config['pins']['genericMatrices']), allow_pickle=False) as arrays:
        assert arrays['boneNames'].tolist() == names
        generic_poses = {name: arrays[f'pose{index}'].copy() for index, (name, _) in enumerate(GENERIC)}
    actions = originals+generic_actions
    assert actions, 'At least one original native75 clip is required for actual activation checks'
    references = []
    for action in actions:
        action.use_fake_user = True
        start, end = map(float, action.frame_range)
        assert end > start
        is_generic = action.name in generic_poses
        frames = list(range(1, int(end)+1)) if is_generic else [start+(end-start)*value/4 for value in range(5)]
        expected = generic_poses.get(action.name)
        if is_generic:
            assert (start, end) == (1., dict(GENERIC)[action.name])
            assert expected.shape == (int(end), 75, 4, 4) and np.isfinite(expected).all()
        poses = []
        maximum = 0.
        for frame in frames:
            reset_native(rig, names)
            activate(rig, action)
            bpy.context.scene.frame_set(int(frame), subframe=frame-int(frame))
            bpy.context.view_layer.update()
            actual = worlds(np, rig, names)
            if is_generic:
                maximum = max(maximum, float(max(bounds(np, actual, expected[frame-1]))))
                assert maximum < LIMIT, ('Generic05 source does not replay on selected75', action.name, frame, maximum)
            poses.append(expected[frame-1] if is_generic else actual)
        references.append({'action': action, 'signature': playback.signature(action),
                           'frames': frames, 'poses': poses, 'generic05': is_generic,
                           'sourceReplayMaximumBoundM': maximum})
    return references


def build_actions(input_path, plan_path, out, config, package, contract, rt):
    original, build, conditioned, _, playback = rt
    bpy, np, Matrix = original.bpy, original.np, original.Matrix
    plan = json.loads(plan_path.read_text())
    plan_pin = pin_file(plan_path)
    assert plan['accepted'] is False and plan['status'] == 'CONDITIONED_MODE_PLAN_MEASURED_NATIVE_BUILD_PENDING'
    assert plan['input'] == pin_file(input_path) and plan['sourcePins'] == config['pins'] and plan['limitM'] == LIMIT
    assert [row['name'] for row in plan['actions']] == [row['name'] for row in package['actions']]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    native = pinned(config['pins']['selectedNative'])
    rig = build.load_rig(native)
    assert not bpy.data.meshes
    names = package['boneNames']
    references = original_playback_references(bpy, np, build, conditioned, playback, rig, native, names, config, contract)
    context = conditioned.install(rig, contract)
    original_actions = {action.name: playback.signature(action) for action in bpy.data.actions if len(action.slots) == 1}
    copies = []
    for reference in references:
        action, record = playback.playback_copy(bpy, reference['action'], names)
        record.update(generic05=reference['generic05'], sourceReplayMaximumBoundM=reference['sourceReplayMaximumBoundM'])
        reference['copy'] = action
        copies.append(record)
    out.mkdir(parents=True)
    scene = bpy.context.scene
    scene.render.fps = 24
    scene.render.fps_base = 1
    arrays = {'boneNames': np.asarray(names)}
    records = []
    for index, (captured, planned) in enumerate(zip(package['actions'], plan['actions'])):
        action = bpy.data.actions.new('Author.'+captured['name'])
        action.use_fake_user = True
        playback.reset_tracks(action, names, 1, 241, 1.)
        activate(rig, action)
        previous, previous_local, poses, locals_, witnesses = {}, {}, [], [], []
        for frame, sample in enumerate(captured['nativeWorldMatrices'], 1):
            scene.frame_set(frame)
            modes = {name: row['modes'][frame-1] for name, row in planned['modes'].items()}
            set_modes(rig, context, modes)
            wanted = {name: Matrix(value) for name, value in zip(names, sample)}
            try:
                original.reconstruct(rig, context, wanted)
                original.key_controls(rig, context, frame, previous)
                for limb in context['limbs']:
                    rig.pose.bones[limb['targetControl']].keyframe_insert(f'["{conditioned.IK}"]', frame=frame)
                bpy.context.view_layer.update()
                actual = worlds(np, rig, names)
                error = float(max(bounds(np, actual, np.asarray(sample))))
                assert error < LIMIT, ('Conditioned source replay', frame, error)
                regional = max(original.operator_bound(rig.pose.bones[a].matrix@context['rest'][a].inverted(),
                    rig.pose.bones[b].matrix@context['rest'][b].inverted()) for a, b in original.PAIRS)
                assert regional < LIMIT
                local = []
                world_map = {name: rig.pose.bones[name].matrix.copy() for name in names}
                for name in names:
                    bone = rig.data.bones[name]
                    options = {'parent_matrix': world_map[bone.parent.name],
                               'parent_matrix_local': bone.parent.matrix_local} if bone.parent else {}
                    basis = bone.convert_local_to_pose(world_map[name], bone.matrix_local, invert=True, **options)
                    position, quaternion, scale = basis.decompose()
                    if name in previous_local and quaternion.dot(previous_local[name]) < 0:
                        quaternion.negate()
                    previous_local[name] = quaternion.copy()
                    local.append([*position, *quaternion, *scale])
                poses.append(actual)
                locals_.append(local)
                witnesses.append({'frame': frame, 'sourceTick': (frame-1)*5, 'capturedPoseBoundM': error,
                                  'regionalOperatorBoundM': regional, 'limbModes': modes})
            except Exception as error:
                write(out/'failed-action.json', {'accepted': False, 'action': captured['name'], 'frame': frame,
                    'sourceTick': (frame-1)*5, 'limbModes': modes, 'error': repr(error),
                    'poseWitness': context.get('failureWitness')})
                raise
        for curve in build.action_curves(action):
            constant = curve.data_path.endswith(f'["{conditioned.IK}"]') or curve.data_path == f'["{conditioned.LIVE}"]'
            for key in curve.keyframe_points:
                key.interpolation = 'CONSTANT' if constant else 'LINEAR'
        arrays[f'pose{index}'], arrays[f'local{index}'] = np.asarray(poses), np.asarray(locals_)
        baked = build.keyed_action(captured['name'], names, arrays[f'local{index}'])
        record = {key: value for key, value in captured.items() if key != 'nativeWorldMatrices'}
        record.update(controlAction=action.name, nativeWitnesses=witnesses, conditionedModes=planned['modes'])
        scene.frame_start = 1
        scene.frame_end = 241
        scene.frame_set(1)
        control_file = out/(captured['bike']+'-conditioned-editable-controls.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(control_file), compress=False)
        record['controlNative'] = pin_file(control_file)
        records.append(record)
        np.savez_compressed(out/'conditioned-action-matrices.npz', **arrays)
        write(out/'partial-receipt.json', {'accepted': False, 'status': 'CONDITIONED_ACTIONS_SAVED_REOPEN_PENDING',
                                         'actions': records, 'originalPlaybackCopies': copies})
    activate(rig, bpy.data.actions[records[0]['controlAction']])
    scene.frame_set(1)
    control_file = out/'native75-conditioned-controls.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(control_file), compress=False)
    control_pin = pin_file(control_file)
    # All following live and activation checks read the actual combined file.
    bpy.ops.wm.open_mainfile(filepath=str(control_file), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']
    scene = bpy.context.scene
    switches = []
    for index, record in enumerate(records):
        activate(rig, bpy.data.actions[record['controlAction']])
        maximum = 0.
        for frame in range(1, 242):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            maximum = max(maximum, float(max(bounds(np, worlds(np, rig, names),
                np.asarray(package['actions'][index]['nativeWorldMatrices'][frame-1])))))
        record['savedControlReplayMaximumAffineBoundWithin2mM'] = maximum
        write(out/(record['bike']+'-control-readback.json'), {'accepted': False, 'native': control_pin,
              'maximumCapturedPoseBoundM': maximum, 'frames': 241})
        assert maximum < LIMIT, ('Saved conditioned action differs', record['name'], maximum)
        for name, planned in record['conditionedModes'].items():
            for frame in planned['switchFrames']:
                scene.frame_set(frame-1, subframe=.99999)
                bpy.context.view_layer.update()
                before = worlds(np, rig, names)
                scene.frame_set(frame)
                bpy.context.view_layer.update()
                jump = float(max(bounds(np, before, worlds(np, rig, names))))
                switches.append({'action': record['name'], 'limb': name, 'frame': frame,
                                 'leftOffsetFrames': .00001, 'maximumObservedJumpM': jump})
        write(out/'mode-boundaries.json', {'accepted': False, 'switches': switches})
    assert all(row['maximumObservedJumpM'] < LIMIT for row in switches), ('Saved mode-boundary discontinuity', switches)
    activation_checks = []
    for reference, copy in zip(references, copies):
        for sample_index, (frame, expected) in enumerate(zip(reference['frames'], reference['poses'])):
            activate(rig, bpy.data.actions[copy['playbackAction']])
            scene.frame_set(int(frame), subframe=frame-int(frame))
            bpy.context.view_layer.update()
            error = float(max(bounds(np, worlds(np, rig, names), expected)))
            activation_checks.append({'action': copy['playbackAction'], 'frame': frame, 'maximumBoundM': error,
                                      'liveControls': rig[conditioned.LIVE]})
            assert rig[conditioned.LIVE] == 0. and error < LIMIT
            if sample_index not in {round((len(reference['frames'])-1)*i/4) for i in range(5)}:
                continue
            for index, record in enumerate(records):
                activate(rig, bpy.data.actions[record['controlAction']])
                scene.frame_set(51)
                bpy.context.view_layer.update()
                error = float(max(bounds(np, worlds(np, rig, names),
                    np.asarray(package['actions'][index]['nativeWorldMatrices'][50]))))
                activation_checks.append({'action': record['controlAction'], 'frame': 51,
                    'afterNative': copy['playbackAction'], 'maximumBoundM': error, 'liveControls': rig[conditioned.LIVE]})
                assert rig[conditioned.LIVE] == 1. and error < LIMIT
    write(out/'action-activation.json', {'accepted': False, 'checks': activation_checks})
    assert original_actions == {name: playback.signature(bpy.data.actions[name]) for name in original_actions}
    assert conditioned.rest_rows(rig, set(names)) == contract['nativeRest']['bones']
    # Fresh original native75 bake keeps actual control and skin hierarchies
    # separate and verifies total error directly against captured source too.
    data = rig.data
    bpy.data.objects.remove(rig, do_unlink=True)
    assert data.users == 0
    bpy.data.armatures.remove(data)
    rig = build.load_rig(native)
    rig.animation_data_create()
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    for index, record in enumerate(records):
        activate(rig, bpy.data.actions[record['name']])
        maximum = 0.
        for frame in range(1, 242):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            maximum = max(maximum, float(max(bounds(np, worlds(np, rig, names),
                np.asarray(package['actions'][index]['nativeWorldMatrices'][frame-1])))))
        record['bakeMaximumAffineBoundWithin2mM'] = maximum
        assert maximum < LIMIT, ('Fresh native conditioned bake differs', record['name'], maximum)
    baked_file = out/'native75-conditioned-baked.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(baked_file), compress=False)
    for pin in config['pins'].values():
        pinned(pin)
    assert pin_file(plan_path) == plan_pin
    write(out/'receipt.json', {'accepted': False, 'status': 'NATIVE_CONDITIONED_GAMEPLAY_ACTIONS_UNACCEPTED',
        'sourceReceipt': config['pins']['convertedReceipt'], 'input': pin_file(input_path),
        'analysisReceipt': plan_pin, 'sourcePins': config['pins'], 'recipe': config['pins']['builder'],
        'controlsRecipe': config['pins']['conditionedControls'], 'baseControlsRecipe': config['pins']['frozenControls'],
        'commonBuildRecipe': config['pins']['commonBuild'], 'nativeRestExactlyPreserved': True, 'shapeActivation': 0,
        'controlNative': control_pin, 'bakedNative': pin_file(baked_file),
        'nativeMatrices': pin_file(out/'conditioned-action-matrices.npz'), 'actions': records,
        'originalPlaybackCopies': copies, 'originalActionCurvesExact': True,
        'generic05Actions': [name for name, _ in GENERIC], 'generic05KeysVerified': sum(frames for _, frames in GENERIC),
        'actionActivation': pin_file(out/'action-activation.json'), 'modeBoundaries': pin_file(out/'mode-boundaries.json'),
        'limits': ['Explicit visible FK controls govern conditioned intervals; palm/pole IK is not claimed during FK.',
            'Source and playback-copy curves preserve original actions; helper drivers and complete rest channels make activation deterministic.',
            'Only captured24Hz keys and specified mode-boundary limits are measured; no inferred intermediate physics.',
            'Complete dressed integration, moving art, contact, performance and devices remain unaccepted.']})


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert args and args[0] in ('--analyze', '--build', '--validate-input')
    mode = args[0]
    assert len(args) == {'--analyze': 3, '--build': 4, '--validate-input': 2}[mode]
    path = Path(args[1]).resolve()
    config, package, contract = read_input(path)
    if mode == '--validate-input':
        print(json.dumps({'accepted': False, 'status': 'CONDITIONED04_INPUT_VALID_NATIVE_PENDING', 'input': pin_file(path)}))
        return
    out = Path(args[-1]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    rt = runtime(config)
    if mode == '--analyze':
        analyze(path, out, config, package, contract, rt)
    else:
        build_actions(path, Path(args[2]).resolve(), out, config, package, contract, rt)


if __name__ == '__main__':
    main()
