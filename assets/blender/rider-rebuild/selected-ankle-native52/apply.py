"""Parent serial CPU2 only: exact ankle42 initializer, RAW save before scans.

Append missing canonical foot groups only; preserve all existing indices.
Jeans group changes use exact inventory/full-field witnesses; other meshes
retain the complete qualified10 fingerprint.
No native or moving-art pass exists until CPU comparison; art stays unaccepted.
"""
import gc
import gzip
import hashlib
import importlib.util
import inspect
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STATUS = 'UNACCEPTED_ANKLE52_RAW_SAVED_WITNESSES_PENDING'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def checked(value):
    assert set(value) == {'path', 'sha256'}
    path = (ROOT/value['path']).resolve()
    assert path.is_relative_to(ROOT) and pin(path) == value
    return path


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def write(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2)+'\n')


def load():
    config = read(HERE/'input.json')
    assert config['acceptedArt'] is False
    assert config['groupAppendPolicy'] == {'object': 'RiderJeans', 'allowedMissingCanonicalGroups': ['DEF-foot.L', 'DEF-foot.R'],
        'existingGroupIndicesAndNames': 'exact', 'changedNativeVertices': 3318,
        'allUnselectedMemberships': 'exact-including-zero', 'selectedNondeformMemberships': 'exact'}
    for value in config['pins'].values(): checked(value)
    qualified = read(checked(config['pins']['qualified11']))
    assert qualified['accepted'] is False and qualified['status'] == 'SELECTED_FULL_GAMEPLAY_REPLAY_PASS_ART_PENDING'
    assert qualified['native'] == config['pins']['native10']
    assert qualified['recipe'] == config['pins']['generation10']
    assert qualified['qualificationRecipe'] == config['pins']['qualifier11']
    derivation = read(checked(config['pins']['derivation42']))
    assert derivation['acceptedArt'] is False
    assert derivation['namedRows'] == config['pins']['rows42'] and derivation['patch'] == config['pins']['patch42']
    runtime = read(checked(config['pins']['runtime02']))
    assert runtime['patchReceipt'] == config['pins']['derivation42'] and runtime['changedNativeVertices'] == 3318
    rows = read(checked(config['pins']['rows42']))
    validate_rows(rows)
    return config, qualified, derivation, rows


def validate_rows(rows):
    assert len(rows) == len({r['nativeID'] for r in rows}) == 3318
    assert [r['nativeID'] for r in rows] == sorted(r['nativeID'] for r in rows)
    for row in rows:
        assert type(row['nativeID']) is int and row['nativeID'] >= 0
        side = 'L' if 'DEF-foot.L' in row['after'] else 'R'
        assert row['before'] == {'DEF-shin.'+side+'.001': 1}
        assert set(row['after']) == {'DEF-foot.'+side, 'DEF-shin.'+side+'.001'}
        assert all(math.isfinite(w) and w > 0 for w in row['after'].values())
        assert abs(sum(row['after'].values())-1) < 1e-6


def context(config, qualified, native):
    spec = importlib.util.spec_from_file_location('ankle52_frozen10', checked(config['pins']['generation10']))
    frozen = importlib.util.module_from_spec(spec); spec.loader.exec_module(frozen)
    original = {'pins': qualified['sourcePins']}
    helper = frozen.helpers(original)
    bpy = helper.bpy
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(native)), use_scripts=False) == {'FINISHED'}
    rig, objects, contract = frozen.rig_and_objects(helper, original)
    assert all(not obj.data.shape_keys or all(k.value == 0 for k in obj.data.shape_keys.key_blocks) for obj in objects)
    return frozen, helper, rig, objects


def deform_row(obj, index, bones):
    names = {g.index: g.name for g in obj.vertex_groups}
    return {names[g.group]: float(g.weight) for g in obj.data.vertices[index].groups
            if names[g.group] in bones and g.weight > 0}


def group_inventory(obj):
    result = [{'index': g.index, 'name': g.name} for g in obj.vertex_groups]
    assert [g['index'] for g in result] == list(range(len(result)))
    assert len({g['name'] for g in result}) == len(result)
    return result


def group_plan(before, bones, rows):
    """Only missing canonical foot groups may be appended; old indices persist."""
    assert [g['index'] for g in before] == list(range(len(before)))
    names = [g['name'] for g in before]
    assert len(set(names)) == len(names)
    required = {n for row in rows for n in row['after']}
    assert required == {'DEF-foot.L', 'DEF-foot.R', 'DEF-shin.L.001', 'DEF-shin.R.001'}
    assert required <= set(bones), 'Destination support must be actual canonical rig bones'
    assert {n for row in rows for n in row['before']} <= set(names), 'Source shin groups missing'
    missing = sorted(required-set(names))
    assert set(missing) <= {'DEF-foot.L', 'DEF-foot.R'}, 'Only canonical foot groups can be added'
    added = [{'index': len(before)+i, 'name': name} for i, name in enumerate(missing)]
    return {'before': before, 'appended': added, 'after': before+added}


def validate_inventory(plan, rows):
    expected = group_plan(plan['before'], {n for r in rows for n in r['after']}, rows)
    assert plan == expected, 'Unregistered group rename/reindex/addition'


def field_free_fingerprint_source(source):
    """Jeans only: separate the exact original group block from all other data."""
    old = """    digest.update(json.dumps([g.name for g in obj.vertex_groups]).encode())
    for vertex in mesh.vertices:
        digest.update(struct.pack('<I', len(vertex.groups)))
        for group in vertex.groups: digest.update(struct.pack('<If', group.group, group.weight))
"""
    assert source.count(old) == 1, 'Pinned complete field block changed'
    clause = "assert obj.type == 'MESH' and not mesh.shape_keys and obj.animation_data is None"
    assert source.count(clause) == 1, 'Pinned shape-state clause changed'
    # Shape coordinates/states have their existing separate exact witness.
    return source.replace(old, '').replace(clause, "assert obj.type == 'MESH' and obj.animation_data is None")


def jeans_fingerprint(helper, native_helpers):
    source = inspect.getsource(native_helpers['part_fingerprint'])
    namespace = dict(native_helpers)
    exec(field_free_fingerprint_source(source), namespace)
    return lambda obj: namespace['part_fingerprint'](obj, {'np': helper.np})


def save(out):
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-native52') and not out.exists()
    config, qualified, derivation, rows = load()
    frozen, helper, rig, objects = context(config, qualified, config['pins']['native10'])
    jeans = helper.bpy.data.objects['RiderJeans']; bones = set(rig.data.bones.keys())
    inventory = group_plan(group_inventory(jeans), bones, rows)
    with helper.np.load(checked(config['pins']['patch42'])) as patch:
        assert patch['nativeIds'].tolist() == [r['nativeID'] for r in rows]
        names = patch['boneNames'].tolist()
        for ordinal, row in enumerate(rows):
            i = row['nativeID']
            assert jeans.data.attributes['_NATIVE_ID'].data[i].value == i
            assert tuple(jeans.data.vertices[i].co) == tuple(map(float, patch['beforeLocal'][ordinal]))
            assert deform_row(jeans, i, bones) == row['before'], ('Source field mismatch', i)
            assert {n: float(w) for n, w in zip(names, patch['weights'][ordinal]) if w > 0} == row['after']
            assert set(row['after']) <= bones
    for group in inventory['appended']:
        added = jeans.vertex_groups.new(name=group['name'])
        assert {'index': added.index, 'name': added.name} == group
    assert group_inventory(jeans) == inventory['after']
    ids = [r['nativeID'] for r in rows]
    for group in jeans.vertex_groups:
        if group.name in bones: group.remove(ids)
    for row in rows:
        for name, weight in row['after'].items(): jeans.vertex_groups[name].add([row['nativeID']], weight, 'REPLACE')
    # No fingerprints, action trees, full field scans or export before this RAW save.
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-ankle-field42-native52.blend'
    print('ANKLE52_RAW_SAVE_BEFORE_FULL_SCANS', flush=True)
    assert helper.bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream: assert stream.read(7) == b'BLENDER'
    write(out/'pending.json', {'acceptedArt': False, 'status': STATUS, 'native': pin(native),
        'recipe': pin(__file__), 'input': pin(HERE/'input.json'), 'sourcePins': config['pins'],
        'changedNativeVertices': 3318, 'rankPruning': False, 'nativeFileCompressed': False,
        'groupInventory': inventory, 'groupMembershipRule': 'Append missing canonical foot groups only; exact field42 replacements only on3318 declared IDs; all other memberships unchanged',
        'limits': ['Saved initializer only; independent source/saved comparison, engine parity and moving-art acceptance pending.']})


def canonical_digest(obj, replacements=None, bones=(), inventory=None):
    """Exact float32 fields, canonical group order; retain nondeform/zero rows."""
    replacements = replacements or {}
    actual = group_inventory(obj)
    inventory = actual if inventory is None else inventory
    assert inventory[:len(actual)] == actual, 'Virtual groups must append only'
    names = {g['index']: g['name'] for g in inventory}
    lookup = {g['name']: g['index'] for g in inventory}
    h = hashlib.sha256(json.dumps(list(names.values())).encode())
    h.update(struct.pack('<I', len(obj.data.vertices)))
    for vertex in obj.data.vertices:
        values = {g.group: g.weight for g in vertex.groups}
        if vertex.index in replacements:
            values = {i: w for i, w in values.items() if names[i] not in bones}
            values.update({lookup[n]: w for n, w in replacements[vertex.index].items()})
        h.update(struct.pack('<I', len(values)))
        for i, w in sorted(values.items()): h.update(struct.pack('<If', i, w))
    return h.hexdigest()


def shared_source(helper, rig, derivation):
    """Check actual full wearer below24cm against the field42 shared source."""
    reference = helper.bpy.data.objects['RiderBody__FullAnatomyReference']
    named = read(checked(derivation['sources']['canonicalFields']))
    with helper.np.load(checked(derivation['sources']['reference'])) as source:
        basis = source['RiderBody__FullAnatomyReference_basis']
        assert len(basis) == len(reference.data.vertices) == len(named)
        ids = helper.np.flatnonzero(basis[:, 2] < .24).tolist()
        assert len(ids) == derivation['canonicalRowsBelow24cmExactBasisAndNamedFields'] == 2638
        for i in ids:
            assert tuple(reference.data.vertices[i].co) == tuple(map(float, basis[i]))
            assert deform_row(reference, i, set(rig.data.bones.keys())) == named[i], ('Canonical wearer mismatch', i)
    return {'canonicalReferenceRowsBelow24cmExact': len(ids)}


def pending_at(path):
    pending = read(path); config, qualified, derivation, rows = load()
    assert pending['acceptedArt'] is False and pending['status'] == STATUS
    assert pending['recipe'] == pin(__file__) and pending['input'] == pin(HERE/'input.json')
    assert pending['sourcePins'] == config['pins'] and pending['changedNativeVertices'] == 3318
    validate_inventory(pending['groupInventory'], rows)
    checked(pending['native'])
    return pending, config, qualified, derivation, rows


def witness(path, mode):
    pending, config, qualified, derivation, rows = pending_at(path)
    native = config['pins']['native10'] if mode == 'source' else pending['native']
    frozen, helper, rig, objects = context(config, qualified, native)
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    jeans_protected = jeans_fingerprint(helper, native_helpers)
    bones = set(rig.data.bones.keys()); edits = {r['nativeID']: r['after'] for r in rows}
    parts = {}
    for obj in objects:
        print('ANKLE52_WITNESS '+mode+' '+obj.name, flush=True)
        parts[obj.name] = {'protected': jeans_protected(obj) if obj.name == 'RiderJeans' else fingerprint(obj), 'keys': helper.keys_state(obj),
            'fields': canonical_digest(obj) if obj.name == 'RiderJeans' else frozen.source.exact_group_digest(obj)}
    jeans = helper.bpy.data.objects['RiderJeans']
    inventory = group_inventory(jeans)
    assert inventory == pending['groupInventory']['before' if mode == 'source' else 'after']
    for row in rows:
        assert jeans.data.attributes['_NATIVE_ID'].data[row['nativeID']].value == row['nativeID']
        assert deform_row(jeans, row['nativeID'], bones) == row['before' if mode == 'source' else 'after']
    active = rig.animation_data
    actions = {}
    for action in helper.bpy.data.actions:
        state = helper.action_state(action)
        actions[action.name] = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        del state
    gc.collect()
    write(path.parent/(mode+'-witness.json'), {'acceptedArt': False, 'mode': mode, 'native': native,
        'pending': pin(path), 'recipe': pin(__file__), 'parts': parts, 'actions': actions,
        'expectedJeansFields': canonical_digest(jeans, edits, bones, pending['groupInventory']['after']) if mode == 'source' else None,
        'jeansGroupInventory': inventory, 'groupInventory': pending['groupInventory'],
        'protectedJeansDefinition': 'Pinned original geometry/PBR/bind fingerprint minus exact group block; inventory and all memberships qualified separately',
        'sharedSource': shared_source(helper, rig, derivation),
        'rig': {'rest': native_helpers['native_rest'](rig), 'active': active.action.name if active and active.action else None,
                'slot': active.action_slot.identifier if active and active.action_slot else None,
                'pose': {b.name: [list(r) for r in b.matrix_basis] for b in rig.pose.bones}},
        'visibleMeshes': sorted(o.name for o in helper.bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render),
        'selectedNamedRowsExact': 3318})


def validate_witness_pair(pending, before, after, qualified, pending_pin, recipe_pin, source_native, rows):
    """CPU-only exact witness intake shared by compare and the next native merge."""
    validate_rows(rows); validate_inventory(pending['groupInventory'], rows)
    assert pending['acceptedArt'] is False and pending['status'] == STATUS
    assert pending['changedNativeVertices'] == 3318 and pending['rankPruning'] is False
    for mode, state, native in [('source', before, source_native), ('saved', after, pending['native'])]:
        assert state['acceptedArt'] is False and state['mode'] == mode and state['native'] == native
        assert state['pending'] == pending_pin and state['recipe'] == recipe_pin
        assert state['selectedNamedRowsExact'] == 3318
        assert state['groupInventory'] == pending['groupInventory']
        assert state['jeansGroupInventory'] == pending['groupInventory']['before' if mode == 'source' else 'after']
        assert state['protectedJeansDefinition'] == 'Pinned original geometry/PBR/bind fingerprint minus exact group block; inventory and all memberships qualified separately'
    assert set(before['parts']) == set(after['parts']) == set(qualified['visibleMeshes'])|{'RiderBody__FullAnatomyReference'}
    assert before['expectedJeansFields'] and after['expectedJeansFields'] is None
    for name, part in before['parts'].items():
        expected = {**part, 'fields': before['expectedJeansFields']} if name == 'RiderJeans' else part
        assert after['parts'][name] == expected, name
    for key in ('actions', 'rig', 'visibleMeshes', 'sharedSource', 'protectedJeansDefinition'): assert before[key] == after[key], key
    assert before['actions'] and before['visibleMeshes'] == sorted(qualified['visibleMeshes'])


def compare(path):
    pending, config, qualified, derivation, rows = pending_at(path)
    before, after = [read(path.parent/(m+'-witness.json')) for m in ('source', 'saved')]
    validate_witness_pair(pending, before, after, qualified, pin(path), pin(__file__), config['pins']['native10'], rows)
    write(path.parent/'receipt.json', {**pending, 'status': 'ANKLE52_EXACT_REOPENED_FIELDS_PROTECTED_PASS_ART_PENDING',
        'nativeReopened': True, 'protectedValidationPassed': True,
        'witnesses': {m: pin(path.parent/(m+'-witness.json')) for m in ('source', 'saved')},
        'limits': ['Exact saved native initializer only; engine deformation parity, ankle finite contacts and moving art remain unaccepted.']})


def qualify_receipt(path):
    """CPU-only downstream intake: recheck actual files, pins and every witness gate."""
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-native52')
    receipt = read(path)
    assert receipt['status'] == 'ANKLE52_EXACT_REOPENED_FIELDS_PROTECTED_PASS_ART_PENDING'
    assert receipt['acceptedArt'] is False and receipt['nativeReopened'] is True and receipt['protectedValidationPassed'] is True
    pending_path = path.parent/'pending.json'
    pending, config, qualified, derivation, rows = pending_at(pending_path)
    assert receipt['recipe'] == pin(__file__) and receipt['input'] == pin(HERE/'input.json')
    for key, value in pending.items():
        if key not in ('status', 'limits'): assert receipt[key] == value, key
    witnesses = {mode: read(checked(receipt['witnesses'][mode])) for mode in ('source', 'saved')}
    assert receipt['witnesses'] == {mode: pin(path.parent/(mode+'-witness.json')) for mode in ('source', 'saved')}
    validate_witness_pair(pending, witnesses['source'], witnesses['saved'], qualified,
                          pin(pending_path), pin(__file__), config['pins']['native10'], rows)
    return receipt


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 2 and args[0] in ('save', 'source', 'saved', 'compare')
    mode, path = args[0], Path(args[1]).resolve()
    assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-native52')
    save(path) if mode == 'save' else compare(path) if mode == 'compare' else witness(path, mode)
