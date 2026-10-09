"""Parent serial CPU2 only: exact ankle42 initializer, RAW save before scans.

Separate source/saved witnesses reuse the qualified10 protected fingerprints.
No native or moving-art pass exists until CPU comparison; art stays unaccepted.
"""
import gc
import gzip
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STATUS = 'UNACCEPTED_ANKLE45_RAW_SAVED_WITNESSES_PENDING'


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
    spec = importlib.util.spec_from_file_location('ankle45_frozen10', checked(config['pins']['generation10']))
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


def save(out):
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-native45') and not out.exists()
    config, qualified, derivation, rows = load()
    frozen, helper, rig, objects = context(config, qualified, config['pins']['native10'])
    jeans = helper.bpy.data.objects['RiderJeans']; bones = set(rig.data.bones.keys())
    with helper.np.load(checked(config['pins']['patch42'])) as patch:
        assert patch['nativeIds'].tolist() == [r['nativeID'] for r in rows]
        names = patch['boneNames'].tolist()
        for ordinal, row in enumerate(rows):
            i = row['nativeID']
            assert jeans.data.attributes['_NATIVE_ID'].data[i].value == i
            assert tuple(jeans.data.vertices[i].co) == tuple(map(float, patch['beforeLocal'][ordinal]))
            assert deform_row(jeans, i, bones) == row['before'], ('Source field mismatch', i)
            assert {n: float(w) for n, w in zip(names, patch['weights'][ordinal]) if w > 0} == row['after']
            assert set(row['after']) <= bones and all(n in jeans.vertex_groups for n in row['after'])
    ids = [r['nativeID'] for r in rows]
    for group in jeans.vertex_groups:
        if group.name in bones: group.remove(ids)
    for row in rows:
        for name, weight in row['after'].items(): jeans.vertex_groups[name].add([row['nativeID']], weight, 'REPLACE')
    # No fingerprints, action trees, full field scans or export before this RAW save.
    out.mkdir(parents=True)
    native = out/'UNACCEPTED-ankle-field42-native45.blend'
    print('ANKLE45_RAW_SAVE_BEFORE_FULL_SCANS', flush=True)
    assert helper.bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False) == {'FINISHED'}
    with native.open('rb') as stream: assert stream.read(7) == b'BLENDER'
    write(out/'pending.json', {'acceptedArt': False, 'status': STATUS, 'native': pin(native),
        'recipe': pin(__file__), 'input': pin(HERE/'input.json'), 'sourcePins': config['pins'],
        'changedNativeVertices': 3318, 'rankPruning': False, 'nativeFileCompressed': False,
        'limits': ['Saved initializer only; independent source/saved comparison, engine parity and moving-art acceptance pending.']})


def canonical_digest(obj, replacements=None, bones=()):
    """Exact float32 fields, canonical group order; retain nondeform/zero rows."""
    replacements = replacements or {}
    names = {g.index: g.name for g in obj.vertex_groups}
    lookup = {g.name: g.index for g in obj.vertex_groups}
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
    checked(pending['native'])
    return pending, config, qualified, derivation, rows


def witness(path, mode):
    pending, config, qualified, derivation, rows = pending_at(path)
    native = config['pins']['native10'] if mode == 'source' else pending['native']
    frozen, helper, rig, objects = context(config, qualified, native)
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    bones = set(rig.data.bones.keys()); edits = {r['nativeID']: r['after'] for r in rows}
    parts = {}
    for obj in objects:
        print('ANKLE45_WITNESS '+mode+' '+obj.name, flush=True)
        parts[obj.name] = {'protected': fingerprint(obj), 'keys': helper.keys_state(obj),
            'fields': canonical_digest(obj) if obj.name == 'RiderJeans' else frozen.source.exact_group_digest(obj)}
    jeans = helper.bpy.data.objects['RiderJeans']
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
        'expectedJeansFields': canonical_digest(jeans, edits, bones) if mode == 'source' else None,
        'sharedSource': shared_source(helper, rig, derivation),
        'rig': {'rest': native_helpers['native_rest'](rig), 'active': active.action.name if active and active.action else None,
                'slot': active.action_slot.identifier if active and active.action_slot else None,
                'pose': {b.name: [list(r) for r in b.matrix_basis] for b in rig.pose.bones}},
        'visibleMeshes': sorted(o.name for o in helper.bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render),
        'selectedNamedRowsExact': 3318})


def compare(path):
    pending, config, qualified, derivation, rows = pending_at(path)
    before, after = [read(path.parent/(m+'-witness.json')) for m in ('source', 'saved')]
    for mode, state, native in [('source', before, config['pins']['native10']), ('saved', after, pending['native'])]:
        assert state['acceptedArt'] is False and state['mode'] == mode and state['native'] == native
        assert state['pending'] == pin(path) and state['recipe'] == pin(__file__)
        assert state['selectedNamedRowsExact'] == 3318
    assert set(before['parts']) == set(after['parts']) == set(qualified['visibleMeshes'])|{'RiderBody__FullAnatomyReference'}
    for name, part in before['parts'].items():
        expected = {**part, 'fields': before['expectedJeansFields']} if name == 'RiderJeans' else part
        assert after['parts'][name] == expected, name
    for key in ('actions', 'rig', 'visibleMeshes', 'sharedSource'): assert before[key] == after[key], key
    assert before['actions'] and before['visibleMeshes'] == sorted(qualified['visibleMeshes'])
    write(path.parent/'receipt.json', {**pending, 'status': 'ANKLE45_EXACT_REOPENED_FIELDS_PROTECTED_PASS_ART_PENDING',
        'nativeReopened': True, 'protectedValidationPassed': True,
        'witnesses': {m: pin(path.parent/(m+'-witness.json')) for m in ('source', 'saved')},
        'limits': ['Exact saved native initializer only; engine deformation parity, ankle finite contacts and moving art remain unaccepted.']})


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 2 and args[0] in ('save', 'source', 'saved', 'compare')
    mode, path = args[0], Path(args[1]).resolve()
    assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-ankle-native45')
    save(path) if mode == 'save' else compare(path) if mode == 'compare' else witness(path, mode)
