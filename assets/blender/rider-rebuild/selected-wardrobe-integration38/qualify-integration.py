"""One saved native per process; compare actual data after the raw checkpoint.

Parent serial modes: target, source, merged, compare. The last mode is CPU-light.
No single witness, complete comparison or source static gate accepts moving art.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineage as h
from integrate import PENDING, rest


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def witness(mode, pending_path):
    pending = json.loads(pending_path.read_text())
    assert pending['status'] == PENDING and pending['protectedValidationPassed'] is False
    config, target, sleeve, contract = h.read_input(h.checked(pending['input']))
    assert pending['sourcePins'] == config['pins']
    assert pending['recipe'] == config['pins']['integrationRecipe']
    native = pending['native'] if mode == 'merged' else config['pins'][mode+'Native' if mode == 'target' else 'sleeveNative']
    helper = module(h.checked(target['sourcePins']['inspectionHelper']), 'wardrobe38_inspection')
    assert h.pin(helper.sculpt.__file__) == target['sourcePins']['sculptRecipe']
    assert h.pin(helper.base.__file__) == target['sourcePins']['baseRecipe']
    # This stream-only weight function belongs to the original checked helper,
    # independently of the latest destination save/replay wrapper generation.
    full_path = h.ROOT/'assets/blender/rider-rebuild/selected-seated-anatomical09/append-measured-gameplay08.py'
    assert h.pin(full_path)['sha256'] == '2399678e7c7fff60f2bc7a3aa609dc439e869a5dc6d6287d8b94f1c98180d1a5'
    full = module(full_path, 'wardrobe38_group_digest')
    bpy = helper.bpy
    assert bpy.ops.wm.open_mainfile(filepath=str(h.checked(native)), use_scripts=False) == {'FINISHED'}
    rig = bpy.data.objects['RiderSkeleton']
    assert rest(rig) == contract['nativeRest']['bones'] and len(rig.data.bones) == 75
    fingerprint, _ = helper.sculpt.protected_signature()
    names = list(h.WARDROBE)+[h.REFERENCE] if mode == 'source' else target['visibleMeshes']+[h.REFERENCE]
    parts = {}
    for name in names:
        obj = bpy.data.objects[name]
        print('WARDROBE38_WITNESS '+mode+' '+name, flush=True)
        parts[name] = {'geometryPBRBind': fingerprint(obj), 'namedFieldsSHA256': full.exact_group_digest(obj),
                       'keys': helper.keys_state(obj)}
    actions = {} if mode == 'source' else {action.name: digest(helper.action_state(action)) for action in bpy.data.actions}
    active = rig.animation_data
    rig_state = None if mode == 'source' else {
        'rest': rest(rig), 'matrix': [list(row) for row in rig.matrix_world],
        'activeAction': active.action.name if active and active.action else None,
        'activeSlot': active.action_slot.identifier if active and active.action_slot else None,
        'poseBasis': {bone.name: [list(row) for row in bone.matrix_basis] for bone in rig.pose.bones}}
    result = {'acceptedArt': False, 'status': 'SINGLE_SAVED_NATIVE_WITNESS_ONLY',
              'mode': mode, 'native': native, 'input': pending['input'], 'pending': h.pin(pending_path),
              'recipe': h.pin(__file__), 'parts': parts, 'actions': actions, 'rig': rig_state,
              'visibleMeshes': sorted(obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render),
              'referenceHidden': bpy.data.objects[h.REFERENCE].hide_render,
              'maskReference': bpy.data.objects['RiderBody']['outfitFullBodyReference']}
    h.io['write'](pending_path.parent/(mode+'-witness.json'), result)


def compare(pending_path):
    pending = json.loads(pending_path.read_text())
    assert pending['status'] == PENDING and pending['protectedValidationPassed'] is False
    config, target, sleeve, contract = h.read_input(h.checked(pending['input']))
    assert pending['sourcePins'] == config['pins'] and pending['recipe'] == config['pins']['integrationRecipe']
    expected_pins = {'target': config['pins']['targetNative'], 'source': config['pins']['sleeveNative'], 'merged': pending['native']}
    reports, pins = {}, {}
    for mode in ('target', 'source', 'merged'):
        path = pending_path.parent/(mode+'-witness.json'); pins[mode] = h.pin(path)
        row = json.loads(path.read_text()); reports[mode] = row
        assert row['mode'] == mode and row['status'] == 'SINGLE_SAVED_NATIVE_WITNESS_ONLY'
        assert row['native'] == expected_pins[mode] and row['input'] == pending['input']
        assert row['pending'] == h.pin(pending_path) and row['recipe'] == h.pin(__file__)
        h.checked(row['native'])
    original, source, merged = [reports[mode] for mode in ('target', 'source', 'merged')]
    assert set(original['parts']) == set(merged['parts']) == set(target['visibleMeshes'])|{h.REFERENCE}
    assert set(source['parts']) == set(h.WARDROBE)|{h.REFERENCE}
    for name in original['parts']:
        expected = source['parts'][name] if name in h.WARDROBE else original['parts'][name]
        assert merged['parts'][name] == expected, ('Saved part mismatch', name)
    assert source['parts'][h.REFERENCE] == original['parts'][h.REFERENCE], 'Source static checks refer to a different complete wearer'
    assert original['actions'] == merged['actions'] and original['rig'] == merged['rig']
    assert merged['rig']['rest'] == contract['nativeRest']['bones']
    assert original['visibleMeshes'] == source['visibleMeshes'] == merged['visibleMeshes'] == sorted(target['visibleMeshes'])
    assert all(row['referenceHidden'] is True and row['maskReference'] == h.REFERENCE for row in reports.values())
    result = {**pending, 'status': 'SELECTED_WARDROBE_TRANSFER_EXACT_SAVED_COMPARISON_PASS_ART_PENDING',
              'protectedValidationPassed': True, 'protectedValidationStage': 'THREE_SEPARATE_REOPENED_NATIVES',
              'nativeStorage': {'compressed': False, 'reopenVerified': True}, 'witnesses': pins,
              'checks': {'sourceWardrobeGeometryPBRUVNamedFieldsExact': True, 'targetOtherMeshesKeysNamedFieldsExact': True,
                         'targetOriginalActionsRigExact': True, 'sameCompleteWearerForSourceStaticChecks': True},
              'pendingReceipt': h.pin(pending_path)}
    h.io['write'](pending_path.parent/'receipt.json', result)
    print(json.dumps({'status': result['status'], 'native': result['native'], 'acceptedArt': False}))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 2 and args[0] in ('target', 'source', 'merged', 'compare')
    mode, pending_path = args[0], Path(args[1]).resolve()
    assert pending_path.is_relative_to(h.ROOT/'harness/out/rider-rebuild/selected-wardrobe-integration38')
    compare(pending_path) if mode == 'compare' else witness(mode, pending_path)
