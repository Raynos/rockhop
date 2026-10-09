"""Save measured dressed actions before full scans; qualify in separate jobs.

The frozen08 geometry, field, action, rest and replay gates are unchanged.
No successful receipt exists until both independent native snapshots and the
saved-file replay pass. Each expensive stage can resume from the saved native.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
HELPER_SHA = '2399678e7c7fff60f2bc7a3aa609dc439e869a5dc6d6287d8b94f1c98180d1a5'
spec = importlib.util.spec_from_file_location('frozen_gameplay08', HERE/'append-measured-gameplay08.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
assert source.sha(spec.origin) == HELPER_SHA


def load_input(path):
    config = json.loads(path.read_text())
    assert config['accepted'] is False and set(config['pins']) == {'sourceInput', 'sourceRecipe'}
    assert config['pins']['sourceRecipe'] == {'path': str(Path(spec.origin).relative_to(ROOT)), 'sha256': HELPER_SHA}
    for pin in config['pins'].values():
        source.pinned(pin)
    original, package = source.read_input(source.pinned(config['pins']['sourceInput']))
    return config, original, package


def helpers(original):
    path = source.pinned(original['pins']['inspectionHelper'])
    module_spec = importlib.util.spec_from_file_location('checkpoint10_inspection', path)
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)
    assert Path(helper.sculpt.__file__).resolve() == source.pinned(original['pins']['sculptRecipe'])
    assert Path(helper.base.__file__).resolve() == source.pinned(original['pins']['baseRecipe'])
    return helper


def fresh(path):
    assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    assert not path.exists(), path


def records(package):
    return [{key: value for key, value in action.items() if key != 'nativeWorldMatrices'}
            for action in package['actions']]


def rig_and_objects(helper, original):
    bpy = helper.bpy
    contract = json.loads(source.pinned(original['pins']['contract']).read_text())
    rig = bpy.data.objects['RiderSkeleton']
    names = list(contract['specification']['meshNames'].values())
    assert len(names) == len(set(names)) == 7
    assert rig.matrix_world.is_identity and len(rig.data.bones) == 75
    assert all(not bone.constraints for bone in rig.pose.bones)
    assert not rig.animation_data or (not rig.animation_data.drivers and not rig.animation_data.nla_tracks)
    _, native = helper.sculpt.protected_signature()
    assert native['native_rest'](rig) == contract['nativeRest']['bones']
    assert {obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render} == set(names)
    objects = [bpy.data.objects[name] for name in names+[source.REFERENCE]]
    assert all(obj.matrix_world.is_identity for obj in objects)
    assert bpy.data.objects[source.REFERENCE].hide_render
    assert bpy.data.objects['RiderBody']['outfitFullBodyReference'] == source.REFERENCE
    return rig, objects, contract


def save(path, out):
    fresh(out)
    config, original, package = load_input(path)
    helper = helpers(original)
    bpy, np = helper.bpy, helper.np
    bpy.ops.wm.open_mainfile(filepath=str(source.pinned(original['pins']['native'])), use_scripts=False)
    rig, objects, contract = rig_and_objects(helper, original)
    scene = bpy.context.scene
    scene.frame_set(1)
    for action in bpy.data.actions:
        action.use_fake_user = True
    actions = records(package)
    deactivated = source.zero_old_shapes(bpy, objects, 241)
    scene.render.fps = 24
    scene.render.fps_base = 1
    rig.animation_data_create()
    names = package['boneNames']
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    for record, captured in zip(actions, package['actions']):
        samples, previous = [], {}
        for pose in captured['nativeWorldMatrices']:
            worlds = {name: helper.Matrix(matrix) for name, matrix in zip(names, pose)}
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
            samples.append(local)
        values = np.asarray(samples, dtype=np.float64)
        assert values.shape == (241, 75, 10) and np.isfinite(values).all()
        source.action_from_local(bpy, np, record['name'], names, values)
    source.activate(bpy, rig, actions[0]['name'])
    scene.frame_start, scene.frame_end = 1, 241
    scene.frame_set(1)
    source.assert_zero_shapes(bpy, deactivated)
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-selected-gameplay-checkpoint10.blend'
    print('CHECKPOINT10_SAVE_BEFORE_FULL_GEOMETRY_SCANS', flush=True)
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream:
        assert stream.read(7) == b'BLENDER'
    source.write_json(out/'pending.json', {'accepted': False,
        'status': 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING',
        'native': source.pin_file(native), 'input': source.pin_file(path),
        'recipe': source.pin_file(Path(__file__)), 'sourceRecipe': config['pins']['sourceRecipe'],
        'sourceInput': config['pins']['sourceInput'], 'sourcePins': original['pins'],
        'nativeFileCompressed': False, 'shapeActivation': 0, 'shapeZeroActions': deactivated,
        'visibleMeshes': [obj.name for obj in objects if obj.name != source.REFERENCE],
        'actions': actions, 'limits': ['Saved checkpoint only. Full source/saved preservation, reopened replay, surface and moving art gates remain pending.']})


def pending_at(path):
    pending = json.loads(path.read_text())
    assert pending['accepted'] is False
    assert pending['status'] == 'SELECTED_FULL_GAMEPLAY_SAVED_PROTECTED_AND_REPLAY_PENDING'
    assert pending['recipe'] == source.pin_file(Path(__file__))
    config, original, package = load_input(source.pinned(pending['input']))
    assert pending['sourcePins'] == original['pins'] and pending['sourceRecipe'] == config['pins']['sourceRecipe']
    assert pending['sourceInput'] == config['pins']['sourceInput'] and pending['actions'] == records(package)
    source.pinned(pending['native'])
    return pending, original, package


def snapshot(path, which, out):
    assert which in {'source', 'saved'}
    fresh(out)
    pending, original, package = pending_at(path)
    helper = helpers(original)
    bpy = helper.bpy
    native = original['pins']['native'] if which == 'source' else pending['native']
    bpy.ops.wm.open_mainfile(filepath=str(source.pinned(native)), use_scripts=False)
    rig, objects, contract = rig_and_objects(helper, original)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    out.mkdir(parents=True)
    state = {'accepted': False, 'kind': which, 'native': native,
        'pending': source.pin_file(path), 'recipe': source.pin_file(Path(__file__)),
        'protected': {}, 'fields': {}, 'keys': source.key_coordinates(helper, objects),
        'actions': {action.name: helper.action_state(action) for action in bpy.data.actions},
        'rest': native_helpers['native_rest'](rig), 'visibleMeshes': pending['visibleMeshes']}
    for obj in objects:
        print('CHECKPOINT10_SNAPSHOT '+which+' '+obj.name, flush=True)
        state['protected'][obj.name] = fingerprint(obj)
        state['fields'][obj.name] = source.exact_group_digest(obj)
        source.write_json(out/'partial.json', state)
    source.write_json(out/'snapshot.json', state)


def compare_snapshots(before, after, pending_pin, source_native, saved_native):
    assert before['accepted'] is after['accepted'] is False
    assert before['kind'] == 'source' and after['kind'] == 'saved'
    assert before['pending'] == after['pending'] == pending_pin
    assert before['native'] == source_native and after['native'] == saved_native
    for key in ('protected', 'fields', 'keys', 'rest', 'visibleMeshes', 'recipe'):
        assert before[key] == after[key], key
    assert before['actions'], 'Original action snapshot must not be empty'
    assert all(name in after['actions'] and state == after['actions'][name]
               for name, state in before['actions'].items()), 'Original actions changed'


def qualify(path, before_path, after_path, out):
    fresh(out)
    pending, original, package = pending_at(path)
    before, after = [json.loads(p.read_text()) for p in (before_path, after_path)]
    compare_snapshots(before, after, source.pin_file(path), original['pins']['native'], pending['native'])
    assert before['recipe'] == source.pin_file(Path(__file__))
    helper = helpers(original)
    bpy, np = helper.bpy, helper.np
    bpy.ops.wm.open_mainfile(filepath=str(source.pinned(pending['native'])), use_scripts=False)
    rig, objects, contract = rig_and_objects(helper, original)
    actions = records(package)
    poses = [np.asarray(action['nativeWorldMatrices'], dtype=np.float64) for action in package['actions']]
    out.mkdir(parents=True)
    replay = source.replay_actions(bpy, np, rig, actions, package['boneNames'], poses, objects, pending['shapeZeroActions'])
    checks = {'matrixReplay': replay, 'allOriginalProtectedFieldsExact': True,
        'allVertexGroupNamesAndFieldsExact': True, 'originalActionsExact': True,
        'originalKeyCoordinatesExact': True, 'native75RestExact': True,
        'visibleMeshesExact': True, 'shapeActivation': 0, 'checksUseReopenedNative': True}
    source.write_json(out/'checks.json', {'accepted': False, 'checks': checks})
    assert all(row['maximumAffineBoundWithin2mM'] < source.AFFINE_BOUND_M for row in replay), replay
    surfaces, samples = source.save_body_surfaces(helper, rig, actions, pending['shapeZeroActions'], out)
    source.pinned(pending['native'])
    source.write_json(out/'receipt.json', {**pending,
        'status': 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING',
        'recipeSHA256': source.sha(__file__), 'inputSHA256': pending['input']['sha256'],
        'checks': checks, 'bodySurfaceArrays': surfaces, 'surfaceSamples': samples,
        'preservationSnapshots': {'source': source.pin_file(before_path), 'saved': source.pin_file(after_path)},
        'appearanceReview': 'Actual complete-outfit profile/rear film and finite contacts remain pending.'})


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'save' and len(args) == 3:
        save(*map(lambda value: Path(value).resolve(), args[1:]))
    elif args[0] == 'snapshot' and len(args) == 4:
        snapshot(Path(args[1]).resolve(), args[2], Path(args[3]).resolve())
    elif args[0] == 'qualify' and len(args) == 5:
        qualify(*map(lambda value: Path(value).resolve(), args[1:]))
    else:
        raise AssertionError('Use save INPUT OUT | snapshot PENDING source|saved OUT | qualify PENDING SOURCE_JSON SAVED_JSON OUT')


if __name__ == '__main__':
    main()
