"""Parent CPU2: observe the actual saved controls02 singularity, without repair.

Replay recorded keys from the saved first physical control file. Two read-only
observations surround the original frozen solver activation. Preserve the
failed keyed native and reopened IK-on/IK-off matrices before any correction.
"""
import hashlib
import importlib.util
import inspect
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PINS = {'firstNative', 'firstPoseReceipt', 'failedAction', 'convertedReceipt',
        'capturedPoses', 'gameplayControlsRecipe', 'controlsRecipe', 'commonBuildRecipe'}


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


def read_input(path):
    config = json.loads(path.read_text())
    assert config['accepted'] is False and set(config['pins']) == PINS
    pins = config['pins']
    for row in pins.values():
        pinned(row)
    read = lambda name: json.loads(pinned(pins[name]).read_text())
    first, failure, receipt, package = [read(name) for name in (
        'firstPoseReceipt', 'failedAction', 'convertedReceipt', 'capturedPoses')]
    assert first['accepted'] is failure['accepted'] is receipt['accepted'] is package['accepted'] is False
    assert first['status'] == 'FIRST_MEASURED_PHYSICAL_CONTROLS_UNACCEPTED'
    assert first['native'] == pins['firstNative']
    assert first['sourceReceipt'] == pins['convertedReceipt']
    assert receipt['nativePoseJSON'] == pins['capturedPoses']
    assert receipt['source'] == package['source']
    assert receipt['status'] == package['status'] == 'MEASURED_GAMEPLAY_NATIVE_POSES_UNACCEPTED'
    assert failure['action'] == 'RiderGameplayLeanRookie' and failure['frame'] == 51 and failure['sourceTick'] == 250
    source = package['source']
    assert source['recipes']['gameplayControls'] == pins['gameplayControlsRecipe']
    assert source['recipes']['controls'] == pins['controlsRecipe']
    assert source['recipes']['commonBuild'] == pins['commonBuildRecipe']
    for row in [source['selectedNative'], source['selectedContract'], *source['recipes'].values(), *source['reports'].values()]:
        pinned(row)
    return config, first, failure, package


def inject_observers(source):
    """Insert only callbacks; the original assignments and solves stay exact."""
    before = '    for constraint in iks:\n        constraint.mute = False\n'
    after = '    bpy.context.view_layer.update()\n    all_bones = []\n'
    assert source.count(before) == source.count(after) == 1
    return source.replace(before, "    _snapshot('before-ik', rig, context, wanted)\n"+before).replace(
        after, "    bpy.context.view_layer.update()\n    _snapshot('after-ik', rig, context, wanted)\n    all_bones = []\n")


def installed_context(rig, contract, controls, first_seeds):
    """Recover the actual saved rig's declaration, without installing a new rig."""
    names = [row['name'] for row in contract['nativeRest']['bones']]
    assert controls.rest_rows(rig, set(names)) == contract['nativeRest']['bones']
    rest = {name: rig.data.bones[name].matrix_local.copy() for name in names}
    heads = {name: rig.data.bones[name].head_local.copy() for name in names}
    roles = contract['specification']['roles']
    one = lambda value: value[0] if isinstance(value, list) else value
    fk = [*roles['trunk'], *roles['neck'], one(roles['head']), roles['shoulderLeft'], roles['shoulderRight']]
    control_names = [controls.ctrl(name) for name in fk]
    limbs = []
    # The original context retains math.atan2's Python double while Blender's
    # constraint property stores Float32. Reuse the actual saved context value
    # so this diagnostic does not introduce a new pole-rounding experiment.
    pole_angles = {row['limb']: row['poleAngle'] for row in first_seeds}
    for suffix, role_side in [('L', 'Left'), ('R', 'Right')]:
        for kind, upper_role, lower_role, end_role, socket in (
                ('arm', 'upperArm', 'forearm', 'wrist', 'PalmSocket.'+suffix),
                ('leg', 'thigh', 'shin', 'foot', 'SoleSocket.'+suffix)):
            uppers, lowers = roles[upper_role+role_side], roles[lower_role+role_side]
            end = one(roles[end_role+role_side])
            upper, lower = uppers[0], lowers[0]
            target_control = 'CTRL-'+('palm' if kind == 'arm' else 'sole')+'.'+suffix
            pole_control = 'CTRL-'+('elbow' if kind == 'arm' else 'knee')+'.'+suffix
            mechanism_upper, mechanism_lower = 'MCH-'+upper, 'MCH-'+lower
            iks = [constraint for constraint in rig.pose.bones[mechanism_lower].constraints if constraint.type == 'IK']
            assert len(iks) == 1
            ik = iks[0]
            assert ik.target == rig and ik.pole_target == rig and ik.subtarget == 'MCH-target-'+end
            assert ik.pole_subtarget == pole_control and ik.chain_count == 2 and not ik.use_stretch
            assert ik.iterations == 64
            angle = pole_angles[kind+suffix]
            assert ik.pole_angle == struct.unpack('<f', struct.pack('<f', angle))[0]
            control_names += [target_control, pole_control]
            limbs.append({'kind': kind, 'side': suffix, 'uppers': uppers, 'lowers': lowers, 'end': end,
                'socket': socket, 'targetControl': target_control, 'poleControl': pole_control,
                'target': ik.subtarget, 'mechanismUpper': mechanism_upper, 'mechanismLower': mechanism_lower,
                'poleAngle': angle,
                'lengths': [(heads[lower]-heads[upper]).length, (heads[end]-heads[lower]).length]})
    assert all(name in rig.pose.bones for name in control_names)
    return {'names': names, 'controls': control_names, 'fk': fk, 'limbs': limbs, 'rest': rest,
            'heads': heads, 'roles': roles}


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if len(args) == 2 and args[0] == '--validate-input':
        path = Path(args[1]).resolve()
        read_input(path)
        print(json.dumps({'accepted': False, 'status': 'SINGULARITY_DIAGNOSTIC_INPUT_VALID_NATIVE_PENDING',
                          'input': pin_file(path)}))
        return
    assert len(args) == 2
    path, out = map(lambda value: Path(value).resolve(), args)
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    config, first, original_failure, package = read_input(path)
    pins = config['pins']
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location('frozen_gameplay_controls02', pinned(pins['gameplayControlsRecipe']))
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    import controls
    import build
    assert Path(controls.__file__).resolve() == pinned(pins['controlsRecipe'])
    assert Path(build.__file__).resolve() == pinned(pins['commonBuildRecipe'])
    bpy, Matrix = original.bpy, original.Matrix
    contract = json.loads(pinned(package['source']['selectedContract']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(pinned(pins['firstNative'])), use_scripts=False)
    assert not bpy.data.meshes, 'Only actual saved rig-only diagnostic is allowed'
    rig = bpy.data.objects['RiderSkeleton']
    context = installed_context(rig, contract, controls, first['witness']['mechanismSeeds'])
    record = package['actions'][0]
    assert record['name'] == original_failure['action']
    assert rig.animation_data.action.name == 'Author.'+record['name']
    out.mkdir(parents=True)
    snapshots = []
    frame = 1

    def write(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')

    def snapshot(stage, rig, context, wanted):
        if frame != 51:
            return
        rows = lambda matrix: [list(row) for row in matrix]
        bones = [{'name': name, 'actual': rows(rig.pose.bones[name].matrix), 'wanted': rows(wanted[name]),
                  'basis': rows(rig.pose.bones[name].matrix_basis),
                  'affineBoundWithin2mM': original.operator_bound(rig.pose.bones[name].matrix, wanted[name])}
                 for name in context['names']]
        limbs = []
        for limb in context['limbs']:
            names = [limb[key] for key in ('mechanismUpper', 'mechanismLower', 'target', 'targetControl', 'poleControl')]
            limbs.append({'limb': limb['kind']+limb['side'], 'declaredLengthsM': limb['lengths'],
                'bones': {name: {'actual': rows(rig.pose.bones[name].matrix),
                    'basis': rows(rig.pose.bones[name].matrix_basis), 'rest': rows(rig.data.bones[name].matrix_local),
                    'head': list(rig.data.bones[name].head_local), 'tail': list(rig.data.bones[name].tail_local),
                    'length': rig.data.bones[name].length, 'poseScale': list(rig.pose.bones[name].scale)} for name in names},
                'ik': [{key: getattr(c, key) for key in ('name', 'mute', 'influence', 'pole_angle', 'iterations',
                    'chain_count', 'use_stretch', 'use_rotation', 'weight', 'orient_weight')}
                    for c in rig.pose.bones[limb['mechanismLower']].constraints if c.type == 'IK']})
        snapshots.append({'stage': stage, 'frame': frame, 'sourceTick': 250, 'bones': bones, 'limbs': limbs,
                          'maximumAffineBoundWithin2mM': max(row['affineBoundWithin2mM'] for row in bones)})
        write('observations.json', {'accepted': False, 'status': 'ACTUAL_SINGULARITY_OBSERVATIONS_NOT_A_CONTROL_PASS',
                                   'sourcePins': pins, 'observations': snapshots})

    namespace = dict(original.__dict__)
    namespace['_snapshot'] = snapshot
    source = inject_observers(inspect.getsource(original.reconstruct))
    exec(compile(source, '<read-only-observed-frozen-reconstruct02>', 'exec'), namespace)
    observed = namespace['reconstruct']
    previous = {name: rig.pose.bones[name].rotation_quaternion.copy() for name in context['controls']+
                [limb[key] for limb in context['limbs'] for key in ('mechanismUpper', 'mechanismLower')]}
    failure = None
    for frame in range(2, 52):
        bpy.context.scene.frame_set(frame)
        wanted = {name: Matrix(value) for name, value in zip(context['names'], record['nativeWorldMatrices'][frame-1])}
        try:
            observed(rig, context, wanted)
        except AssertionError as error:
            failure = {'frame': frame, 'sourceTick': record['sourceTicks'][frame-1], 'error': repr(error),
                       'poseWitness': context.get('failureWitness')}
        original.key_controls(rig, context, frame, previous)
        if failure:
            break
    write('replay-result.json', {'accepted': False, 'originalFailure': original_failure, 'replayedFailure': failure,
        'lastFrame': frame, 'observedFrozenRecipe': pins['gameplayControlsRecipe'],
        'limits': ['Only observer calls inserted. Last failed frame is keyed solely to preserve a reopenable diagnostic.']})
    for curve in original.action_curves(rig.animation_data.action):
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    bpy.context.scene.frame_end = frame
    native = out/'REJECTED-gameplay-controls02-frame51.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    saved = pin_file(native)
    write('checkpoint.json', {'accepted': False, 'status': 'REJECTED_CONTROLS02_DIAGNOSTIC_SAVED',
        'native': saved, 'sourcePins': pins, 'input': pin_file(path), 'recipe': pin_file(Path(__file__)),
        'savedFrame': frame, 'replayedFailure': failure})
    assert frame == 51 and failure is not None, 'Expected actual tick250 failure did not reproduce; retain observation'
    bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']
    context = installed_context(rig, contract, controls, first['witness']['mechanismSeeds'])
    bpy.context.scene.frame_set(51)
    bpy.context.view_layer.update()
    snapshot('reopened-ik-on', rig, context, wanted)
    for limb in context['limbs']:
        for constraint in rig.pose.bones[limb['mechanismLower']].constraints:
            if constraint.type == 'IK':
                constraint.mute = True
    bpy.context.view_layer.update()
    snapshot('reopened-ik-off-keyed-prepose', rig, context, wanted)
    assert pin_file(native) == saved
    assert controls.rest_rows(rig, set(context['names'])) == contract['nativeRest']['bones']
    for pin in pins.values():
        pinned(pin)
    write('receipt.json', {'accepted': False, 'status': 'SINGULARITY_DIAGNOSTIC_COMPLETE_NO_CONTROL_OR_ART_PASS',
        'native': saved, 'sourcePins': pins, 'observations': pin_file(out/'observations.json'),
        'bounds': [{'stage': row['stage'], 'maximumAffineBoundWithin2mM': row['maximumAffineBoundWithin2mM']}
                   for row in snapshots],
        'limits': ['No fix applied, no source rest/fields changed and no tolerance/iteration adjustment.',
            'IK-off sample is a diagnostic of keyed FK precision, not accepted live palm/pole behavior.',
            'Generic action activation and explicit editable FK/IK conditioning remain separate implementation work.']})


if __name__ == '__main__':
    main()
