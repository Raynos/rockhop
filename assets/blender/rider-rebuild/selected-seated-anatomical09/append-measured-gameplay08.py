"""Append measured gameplay-native75 actions to the exact selected dressed master.

Parent CPU2 only. A complete dressed checkpoint is saved and reopened before
pose qualification. No old seated diagnostic, shape edit or rig replacement.
"""
import hashlib
import importlib.util
import json
import math
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REFERENCE = 'RiderBody__FullAnatomyReference'
BIKES = ('rookie', 'pro')
AFFINE_BOUND_M = .0001
STATUS = 'MEASURED_GAMEPLAY_NATIVE_POSES_UNACCEPTED'
INPUT_PINS = {'native', 'contract', 'inspectionHelper', 'sculptRecipe', 'baseRecipe',
              'gameplayReceipt', 'gameplayPoses', 'gameplayConverter'}


def sha(filename):
    digest = hashlib.sha256()
    with Path(filename).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def pinned(pin):
    assert set(pin) == {'path', 'sha256'}
    relative = Path(pin['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    assert re.fullmatch('[0-9a-f]{64}', pin['sha256'])
    path = (ROOT/relative).resolve()
    assert path.is_relative_to(ROOT) and path.is_file(), pin
    assert sha(path) == pin['sha256'], pin
    return path


def pin_file(path):
    return {'path': str(path.resolve().relative_to(ROOT)), 'sha256': sha(path)}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def read_input(path):
    """Validate actual capture provenance without importing or launching Blender."""
    config = json.loads(path.read_text())
    assert config['accepted'] is False and set(config['pins']) == INPUT_PINS
    for pin in config['pins'].values():
        pinned(pin)
    read = lambda name: json.loads(pinned(config['pins'][name]).read_text())
    contract, receipt, package = [read(name) for name in ('contract', 'gameplayReceipt', 'gameplayPoses')]
    assert receipt['accepted'] is False and package['accepted'] is False
    assert receipt['status'] == package['status'] == STATUS
    assert receipt['nativePoseJSON'] == config['pins']['gameplayPoses']
    assert receipt['recipe'] == config['pins']['gameplayConverter']
    assert receipt['source'] == package['source'] == json.loads(pinned(receipt['input']).read_text())
    source = package['source']
    assert source['accepted'] is False and source['selectedNative'] == config['pins']['native']
    assert set(source['recipes']) == {'commonBuild', 'controls', 'gameplayControls', 'gameplayConverter'}
    assert source['recipes']['gameplayConverter'] == config['pins']['gameplayConverter']
    for pin in source['recipes'].values():
        pinned(pin)
    selected_contract = json.loads(pinned(source['selectedContract']).read_text())
    assert selected_contract['qualificationState'] == 'UNACCEPTED_GAMEPLAY_LEAN_REVIEW'
    assert not selected_contract.get('previewClip')
    assert set(source['reports']) == set(BIKES)
    for bike in BIKES:
        report = json.loads(pinned(source['reports'][bike]).read_text())
        assert report['bike'] == bike and not report.get('failure') and not report['errors']
        assert not report['played']['faults'] and report['played']['ticks'] == 1200
    for pin in selected_contract['gameplayLeanReview']['sourcePins']:
        pinned(pin)
    assert package['nativeRest'] == receipt['nativeRest'] == selected_contract['nativeRest'] == contract['nativeRest']
    names = [row['name'] for row in contract['nativeRest']['bones']]
    assert package['boneNames'] == receipt['boneNames'] == names and len(names) == len(set(names)) == 75
    assert package['shapeActivation'] == receipt['shapeActivation'] == 0
    assert len(package['actions']) == len(receipt['actions']) == 2
    for bike, action, receipt_action in zip(BIKES, package['actions'], receipt['actions']):
        assert {key: value for key, value in action.items() if key != 'nativeWorldMatrices'} == receipt_action
        assert action['name'] == 'RiderGameplayLean'+bike.title() and action['bike'] == bike
        assert action['fps'] == 24 and action['seconds'] == 10 and action['frameRange'] == [1, 241]
        assert action['playback'] == 'ONCE' and action['loop'] is False and action['shapeActivation'] == 0
        assert action['sourceTicks'] == list(range(0, 1201, 5))
        assert action['surfaceWitnessFrames'] == [1, 49, 121, 193, 241]
        assert action['hierarchyMaximumAffineBoundWithin2mM'] < AFFINE_BOUND_M
        assert len(action['physicsWitnesses']) == len(action['nativeWorldMatrices']) == 241
        assert [(row['name'], row['ticks'], row['lean']) for row in action['phases']] == [
            ('neutral', 240, 0), ('forward', 360, 1), ('backward', 360, -1), ('neutral-return', 240, 0)]
        for index, (witness, matrices) in enumerate(zip(action['physicsWitnesses'], action['nativeWorldMatrices'])):
            assert witness['tick'] == index*5 and witness['timeSeconds'] == index/24
            assert witness['physicalPose'] is True and witness['stageClip'] is None and witness['shapeActivation'] == 0
            frame = witness['frame']
            assert frame['riderBody']['present'] and witness['comProvenanceErrorM'] < 1e-6
            assert witness['crashStateMeasured'] is isinstance(frame.get('crashed'), bool)
            assert witness['ragdollStateMeasured'] is isinstance(frame.get('ragdoll'), list)
            if witness['crashStateMeasured']:
                assert frame['crashed'] is False
            if witness['ragdollStateMeasured']:
                assert frame['ragdoll'] == []
            assert len(matrices) == 75
            assert all(len(matrix) == 4 and all(len(row) == 4 and all(math.isfinite(value) for value in row)
                       for row in matrix) for matrix in matrices)
    return config, package


def exact_group_digest(obj):
    """Stream the complete field; do not retain millions of weight dictionaries."""
    digest = hashlib.sha256()
    digest.update(json.dumps([group.name for group in obj.vertex_groups]).encode())
    digest.update(struct.pack('<I', len(obj.data.vertices)))
    for vertex in obj.data.vertices:
        digest.update(struct.pack('<I', len(vertex.groups)))
        for group in vertex.groups:
            digest.update(struct.pack('<If', group.group, group.weight))
    return digest.hexdigest()


def key_coordinates(helper, objects):
    return {obj.name: {key.name: helper.digest(helper.base.xyz(key.data))
            for key in obj.data.shape_keys.key_blocks}
            for obj in objects if obj.data.shape_keys}


def action_from_local(bpy, np, name, names, samples):
    assert name not in bpy.data.actions, ('Action would replace source work', name)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    slot = action.slots.new('OBJECT', 'RiderSkeleton')
    bag = action.layers.new('Measured gameplay native pose').strips.new(type='KEYFRAME').channelbags.new(slot)
    for bone_index, bone in enumerate(names):
        for prop, width, offset in [('location', 3, 0), ('rotation_quaternion', 4, 3), ('scale', 3, 7)]:
            for axis in range(width):
                curve = bag.fcurves.new(f'pose.bones["{bone}"].{prop}', index=axis)
                curve.keyframe_points.add(len(samples))
                values = np.column_stack([np.arange(1, len(samples)+1), samples[:, bone_index, offset+axis]])
                curve.keyframe_points.foreach_set('co', values.ravel())
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
                curve.update()
    return action


def zero_old_shapes(bpy, objects, final_frame):
    deactivated = []
    for obj in objects:
        keys = obj.data.shape_keys
        if keys is None:
            continue
        assert set(key.name for key in keys.key_blocks) == {'Basis', 'A09_SeatedVolume'}
        assert not keys.animation_data or (not keys.animation_data.drivers and not keys.animation_data.nla_tracks)
        if keys.animation_data and keys.animation_data.action:
            keys.animation_data.action.use_fake_user = True
        name = 'Gameplay08ShapeZero.'+obj.name
        assert name not in bpy.data.actions
        keys.animation_data_create()
        keys.animation_data.action = bpy.data.actions.new(name)
        keys.animation_data.action.use_fake_user = True
        key = keys.key_blocks['A09_SeatedVolume']
        key.value = 0.
        key.mute = False
        for frame in (1, final_frame):
            key.keyframe_insert('value', frame=frame)
        deactivated.append(obj.name)
    return deactivated


def assert_zero_shapes(bpy, names):
    assert all(bpy.data.objects[name].data.shape_keys.key_blocks['A09_SeatedVolume'].value == 0
               for name in names), 'Rejected seated corrective activated'


def activate(bpy, rig, name):
    action = bpy.data.actions[name]
    assert len(action.slots) == 1
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]


def replay_actions(bpy, np, rig, records, names, poses, objects, deactivated):
    visibility = [(obj, obj.hide_viewport, obj.hide_get()) for obj in objects]
    try:
        for obj, _, _ in visibility:
            obj.hide_viewport = True
        checks = []
        for index, record in enumerate(records):
            activate(bpy, rig, record['name'])
            worst = {'maximumAffineBoundWithin2mM': 0., 'frame': None, 'bone': None}
            for frame in range(1, record['frameRange'][1]+1):
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()
                assert_zero_shapes(bpy, deactivated)
                for bone_index, name in enumerate(names):
                    delta = np.asarray(rig.pose.bones[name].matrix)-poses[index][frame-1, bone_index]
                    bound = float(np.linalg.norm(delta[:3, :3], 2)*2+np.linalg.norm(delta[:3, 3]))
                    if bound > worst['maximumAffineBoundWithin2mM']:
                        worst = {'maximumAffineBoundWithin2mM': bound, 'frame': frame, 'bone': name}
            checks.append({'action': record['name'], 'frames': record['frameRange'][1], **worst})
        return checks
    finally:
        for obj, hidden_viewport, hidden_get in visibility:
            obj.hide_viewport = hidden_viewport
            obj.hide_set(hidden_get)


def save_body_surfaces(helper, rig, records, deactivated, out):
    bpy, np, base = helper.bpy, helper.np, helper.base
    objects = [bpy.data.objects[name] for name in (REFERENCE, 'RiderBody', 'RiderJeans')]
    visibility = [(obj, obj.hide_viewport, obj.hide_get()) for obj in objects]
    arrays, samples = {}, []
    try:
        for obj in objects:
            obj.hide_viewport = False
            obj.hide_set(False)
            obj.data.calc_loop_triangles()
            arrays[obj.name+'_basis'] = base.xyz(obj.data.vertices)
            arrays[obj.name+'_triangles'] = np.asarray([list(t.vertices) for t in obj.data.loop_triangles], dtype=np.int32)
        for record in records:
            activate(bpy, rig, record['name'])
            for frame in record['surfaceWitnessFrames']:
                bpy.context.scene.frame_set(frame)
                bpy.context.view_layer.update()
                assert_zero_shapes(bpy, deactivated)
                for obj in objects:
                    values = base.evaluated_positions(obj)
                    arrays[record['name']+'_'+str(frame)+'_'+obj.name] = values
                    samples.append({'action': record['name'], 'frame': frame, 'object': obj.name,
                                    'vertices': len(values), 'sha256': helper.digest(values)})
        path = out/'selected-gameplay-body-surfaces.npz'
        np.savez_compressed(path, **arrays)
        return pin_file(path), samples
    finally:
        for obj, hidden_viewport, hidden_get in visibility:
            obj.hide_viewport = hidden_viewport
            obj.hide_set(hidden_get)


def append_gameplay(input_path, config, out, package):
    """Save the complete source outfit first; qualify the reopened native file."""
    spec = importlib.util.spec_from_file_location('selected_gameplay_inspection', pinned(config['pins']['inspectionHelper']))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert Path(helper.sculpt.__file__).resolve() == pinned(config['pins']['sculptRecipe'])
    assert Path(helper.base.__file__).resolve() == pinned(config['pins']['baseRecipe'])
    bpy, np, base = helper.bpy, helper.np, helper.base
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    contract = json.loads(pinned(config['pins']['contract']).read_text())
    records = [{key: value for key, value in action.items() if key != 'nativeWorldMatrices'} for action in package['actions']]
    poses = [np.asarray(action['nativeWorldMatrices'], dtype=np.float64) for action in package['actions']]
    names = [row['name'] for row in contract['nativeRest']['bones']]
    bpy.ops.wm.open_mainfile(filepath=str(pinned(config['pins']['native'])), use_scripts=False)
    scene = bpy.context.scene
    rig = bpy.data.objects['RiderSkeleton']
    assert rig.matrix_world.is_identity and len(rig.data.bones) == 75
    assert not rig.animation_data or (not rig.animation_data.drivers and not rig.animation_data.nla_tracks)
    assert all(not bone.constraints for bone in rig.pose.bones)
    assert native_helpers['native_rest'](rig) == contract['nativeRest']['bones']
    mesh_names = list(contract['specification']['meshNames'].values())
    assert len(mesh_names) == len(set(mesh_names)) == 7
    assert {obj.name for obj in scene.objects if obj.type == 'MESH' and not obj.hide_render} == set(mesh_names)
    protected_names = mesh_names+[REFERENCE]
    objects = [bpy.data.objects[name] for name in protected_names]
    assert all(obj.matrix_world.is_identity for obj in objects)
    assert bpy.data.objects[REFERENCE].hide_render
    assert bpy.data.objects['RiderBody']['outfitFullBodyReference'] == REFERENCE
    scene.frame_set(1)
    bpy.context.view_layer.update()
    before = {obj.name: fingerprint(obj) for obj in objects}
    fields = {obj.name: exact_group_digest(obj) for obj in objects}
    original_actions = {action.name: helper.action_state(action) for action in bpy.data.actions}
    original_keys = key_coordinates(helper, objects)
    for action in bpy.data.actions:
        action.use_fake_user = True
    final_frame = max(record['frameRange'][1] for record in records)
    deactivated = zero_old_shapes(bpy, objects, final_frame)
    scene.render.fps = records[0]['fps']
    scene.render.fps_base = 1
    rig.animation_data_create()
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    for record, measured in zip(records, poses):
        local_samples, previous = [], {}
        assert measured.shape == (record['frameRange'][1], 75, 4, 4)
        for pose in measured:
            worlds = {name: helper.Matrix(pose[index]) for index, name in enumerate(names)}
            local = []
            for name in names:
                bone = rig.data.bones[name]
                options = {'parent_matrix': worlds[bone.parent.name], 'parent_matrix_local': bone.parent.matrix_local} if bone.parent else {}
                matrix = bone.convert_local_to_pose(worlds[name], bone.matrix_local, invert=True, **options)
                position, quaternion, scale = matrix.decompose()
                if name in previous and quaternion.dot(previous[name]) < 0:
                    quaternion.negate()
                previous[name] = quaternion.copy()
                local.append([*position, *quaternion, *scale])
            local_samples.append(local)
        samples = np.asarray(local_samples, dtype=np.float64)
        assert samples.shape == (record['frameRange'][1], 75, 10)
        assert np.isfinite(samples).all()
        action_from_local(bpy, np, record['name'], names, samples)
    activate(bpy, rig, records[0]['name'])
    scene.frame_start = 1
    scene.frame_end = final_frame
    scene.frame_set(1)
    assert_zero_shapes(bpy, deactivated)
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-selected-full-gameplay-actions.blend'
    # Parent measured compressed full-outfit saves crossing the memory guard.
    # Uncompressed storage preserves the selected maps/geometry/actions exactly.
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    saved = pin_file(native)
    checkpoint = {'accepted': False, 'status': 'SELECTED_FULL_GAMEPLAY_SAVED_REPLAY_AND_ART_PENDING',
        'sourcePins': config['pins'], 'recipeSHA256': sha(__file__), 'inputSHA256': sha(input_path),
        'native': saved, 'nativeFileCompressed': False, 'shapeActivation': 0, 'shapeZeroActions': deactivated,
        'visibleMeshes': mesh_names, 'actions': records,
        'limits': ['Complete selected outfit saved before pose qualifiers; no body/clothing geometry edit.',
            'Original action curves, geometry, maps and weights retained; rejected seated volume inactive.',
            'Sampled actual physics-driver poses; observed endpoints are not guaranteed profile extrema.',
            'Crash/ragdoll frame fields are measured only where upstream witness flags say so; report fault history is checked separately.',
            'Baked replay is inspection evidence, not permission to replace the live gameplay physics driver.',
            'Parent played full-outfit profile/rear review is required before coupled Body/Jeans sculpt.']}
    write_json(out/'checkpoint.json', checkpoint)
    print(json.dumps({'checkpoint': saved, 'actions': [record['name'] for record in records]}), flush=True)

    # Read back the saved file, so every subsequent qualifier includes actual
    # serialization, slot retention and the complete dressed native checkpoint.
    bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']
    scene = bpy.context.scene
    objects = [bpy.data.objects[name] for name in protected_names]
    replay = replay_actions(bpy, np, rig, records, names, poses, objects, deactivated)
    checks = {'matrixReplay': replay,
        'allOriginalProtectedFieldsExact': before == {obj.name: fingerprint(obj) for obj in objects},
        'allVertexGroupNamesAndFieldsExact': fields == {obj.name: exact_group_digest(obj) for obj in objects},
        'originalActionsExact': original_actions == {name: helper.action_state(bpy.data.actions[name]) for name in original_actions},
        'originalKeyCoordinatesExact': original_keys == key_coordinates(helper, objects),
        'native75RestExact': native_helpers['native_rest'](rig) == contract['nativeRest']['bones'],
        'visibleMeshesExact': {obj.name for obj in scene.objects if obj.type == 'MESH' and not obj.hide_render} == set(mesh_names),
        'shapeActivation': 0, 'checksUseReopenedNative': True}
    write_json(out/'checks.json', {'accepted': False, 'checks': checks})
    # Keep failure evidence and the native checkpoint even if a later surface
    # extraction or bound fails. No failed result emits a successful receipt.
    assert all(row['maximumAffineBoundWithin2mM'] < AFFINE_BOUND_M for row in replay), replay
    for name in ('allOriginalProtectedFieldsExact', 'allVertexGroupNamesAndFieldsExact', 'originalActionsExact',
                 'originalKeyCoordinatesExact', 'native75RestExact', 'visibleMeshesExact'):
        assert checks[name], name
    surfaces, samples = save_body_surfaces(helper, rig, records, deactivated, out)
    activate(bpy, rig, records[0]['name'])
    scene.frame_set(1)
    assert pin_file(native) == saved
    for pin in config['pins'].values():
        pinned(pin)
    write_json(out/'receipt.json', {**checkpoint,
        'status': 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING', 'checks': checks,
        'bodySurfaceArrays': surfaces, 'surfaceSamples': samples,
        'appearanceReview': 'Actual profile/rear complete-outfit film pending; no moving art or finite contact acceptance.'})


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if len(args) == 2 and args[0] == '--validate-input':
        input_path = Path(args[1]).resolve()
        config, package = read_input(input_path)
        print(json.dumps({'accepted': False, 'status': 'GAMEPLAY08_INPUT_PROVENANCE_VALID_NATIVE_RUN_PENDING',
            'input': pin_file(input_path), 'sourcePins': config['pins'],
            'actions': [{'name': action['name'], 'frameRange': action['frameRange']} for action in package['actions']]}))
        return
    assert len(args) == 2, 'Use -- INPUT.json FRESH_OUTPUT, or --validate-input INPUT.json'
    input_path, out = [Path(arg).resolve() for arg in args]
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    config, package = read_input(input_path)
    append_gameplay(input_path, config, out, package)


if __name__ == '__main__':
    main()
