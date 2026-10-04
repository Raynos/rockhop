"""Preserve original auxiliary groups in a new frozen neck28 derivative.

No geometry, topology, semantic bone weights, normals or pose input changes.
Old source controls and failed97/98 objects remain inside the new file.
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

root = Path(__file__).resolve().parents[6]
owned = Path(__file__).resolve().parent
evbase = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = evbase / 'neck-interface100'; out.mkdir(parents=True, exist_ok=True)
source = owned / 'neck-interface27/bounded-neck-join-triangulated.blend'
field_path = source.parent / 'triangulated-neck-fields.npz'
native = owned / 'neck-interface28/auxiliary-restored.blend'
native.parent.mkdir(parents=True, exist_ok=True)
assert not native.exists() and not (out / 'restoration.json').exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/neck62/native-read.json'
pose_path = evbase / 'neck-interface99/pose-witnesses.npz'
helper_path = qa.with_name('read-native.py')
pins = {str(p.relative_to(root)): sha(p) for p in [source, field_path, qa, pose_path, helper_path]}
assert sha(source) == 'eed9a2ceb77eaa5b9a4deb9e686a8519c90bec130cf4a420f141615314900778'
assert sha(field_path) == 'ec1f4a6b72e26978740c27f9787d0d2ed8d73f0a43227c4fd9b02863b470e0d5'
text = helper_path.read_text(); helpers = dict(bpy=bpy, np=np, hashlib=hashlib)
exec(compile(text[text.index('def digest('):text.index('for label,path in paths.items():')], str(helper_path), 'exec'), helpers)


def snapshot():
    return {'objects': {o.name: helpers['state'](o) for o in bpy.data.objects},
        'materials': helpers['materials'](),
        'images': {im.name: {'packed': sha_bytes(bytes(im.packed_file.data)) if im.packed_file else None,
            'colour': im.colorspace_settings.name, 'size': list(im.size), 'filepath': im.filepath} for im in bpy.data.images}}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def definitions(obj):
    return [{'name': g.name, 'lockWeight': g.lock_weight} for g in obj.vertex_groups]


def assignments(obj, bone_names, bone):
    return [[v.index, obj.vertex_groups[g.group].name, float(g.weight)]
        for v in obj.data.vertices for g in v.groups
        if (obj.vertex_groups[g.group].name in bone_names) == bone]


def no_group_state(obj):
    result = helpers['state'](obj)
    result['mesh'].pop('weights'); result['mesh'].pop('groups')
    return result


bpy.ops.wm.open_mainfile(filepath=str(source))
before = snapshot()
rig = bpy.data.objects['Independent anatomical foundation rig']
names = list(rig.data.bones.keys()); assert len(names) == 51
original = bpy.data.objects['Canonical body with hidden head interface']
original_defs = definitions(original); aux = assignments(original, names, False)
qa_data = json.loads(qa.read_text())['snapshots']['baseline']
assert [g['name'] for g in original_defs] == qa_data['objects'][original.name]['mesh']['groups']
assert aux == qa_data['domains']['body_source']['nonBoneAssignments']
assert len([g for g in original_defs if g['name'] not in names]) == 153
proposal = json.loads((root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body59/proposal.json').read_text())['preciseInitialAuthoringMargin']
outside = set(range(len(original.data.vertices))) - set(proposal['bodyExistingRenderedNativeVertices'])
assert len(outside) == 8877
outside_positive = [row for row in aux if row[0] in outside and row[2] > 0]
assert len(outside_positive) == 21424
old_states = {}; old_skin = {}; new_names = {}; rows = []
for label in ['full', 'four']:
    old = bpy.data.objects['Bounded neck27 triangulated body ' + label + ', unaccepted']
    old_states[label] = no_group_state(old)
    old_skin[label] = assignments(old, names, True)
    new = old.copy(); new.data = old.data.copy()
    new.name = 'Bounded neck28 auxiliary-preserved body ' + label + ', unaccepted'
    new.data.name = 'Unaccepted neck28 auxiliary-preserved body ' + label
    bpy.context.collection.objects.link(new)
    active = old.vertex_groups.active.name if old.vertex_groups.active else None
    new.vertex_groups.clear()
    for definition in original_defs:
        group = new.vertex_groups.new(name=definition['name'])
        group.lock_weight = definition['lockWeight']
    for vertex, name, weight in aux + old_skin[label]:
        new.vertex_groups[name].add([vertex], weight, 'REPLACE')
    if active: new.vertex_groups.active_index = new.vertex_groups[active].index
    new.hide_set(True); new.hide_render = True
    assert no_group_state(new) == old_states[label]
    assert definitions(new) == original_defs
    assert assignments(new, names, True) == old_skin[label]
    assert assignments(new, names, False) == aux
    new_names[label] = new.name
    rows.append({'field': label, 'object': new.name, 'originalVertices': len(original.data.vertices),
        'newDerivedVertices': len(new.data.vertices) - len(original.data.vertices),
        'sourceAuxiliaryDefinitions': 153, 'sourceAllDefinitions': len(original_defs),
        'restoredAuxiliaryAssignmentsIncludingZero': len(aux), 'outsideVertices': len(outside),
        'outsidePositiveAuxiliaryAssignments': len(outside_positive),
        'definitionsOrderNameAndLockExact': True, 'allOriginalAuxiliaryMembershipValuesExact': True,
        'semanticBoneMembershipAndWeightsExact': True, 'nonGroupStoredFieldsExact': True,
        'newVertexAuxiliaryPolicy': 'No original source identity: new182vertices have no auxiliary membership. Existing9037memberships restored exactly; semantic authored new-vertex bone fields unchanged.'})
assert snapshot()['objects'] | {}  # No lazy pending mesh update is relied on.
current = snapshot()
assert current['materials'] == before['materials'] and current['images'] == before['images']
for name, state in before['objects'].items(): assert current['objects'][name] == state, name
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)

# Reopen is a separate durability boundary; no post-save RNA is trusted.
bpy.ops.wm.open_mainfile(filepath=str(native))
after = snapshot()
for name, state in before['objects'].items(): assert after['objects'][name] == state, name
assert after['materials'] == before['materials'] and after['images'] == before['images']
for label in ['full', 'four']:
    new = bpy.data.objects[new_names[label]]
    assert no_group_state(new) == old_states[label]
    assert definitions(new) == original_defs
    assert assignments(new, names, True) == old_skin[label]
    assert assignments(new, names, False) == aux

# Three frozen witnesses test actual evaluation equivalence only; no capture.
rig = bpy.data.objects['Independent anatomical foundation rig']
pose = np.load(pose_path); rest = np.array([rig.data.bones[n].matrix_local for n in names])
lookup = {name: i for i, name in enumerate(names)}
order = sorted(names, key=lambda n: len(rig.data.bones[n].parent_recursive))
pose_before = {b.name: {'mode': b.rotation_mode, 'location': b.location[:], 'quaternion': b.rotation_quaternion[:],
    'euler': b.rotation_euler[:], 'axis': b.rotation_axis_angle[:], 'scale': b.scale[:]} for b in rig.pose.bones}
objects = [bpy.data.objects['Bounded neck27 triangulated body ' + label + ', unaccepted'] for label in ['full', 'four']] + [bpy.data.objects[new_names[label]] for label in ['full', 'four']]
hides = {o.name: o.hide_get() for o in [rig] + objects}
for o in [rig] + objects: o.hide_set(False)
checks = []
for domain, source_id in [('native', 0), ('native', 72), ('actual47', 668)]:
    index = int(np.flatnonzero((pose['domains'] == domain) & (pose['sourceIndices'] == source_id))[0])
    desired = pose['rigLocalSkinMatrices'][index] @ rest
    for name in order:
        bone = rig.data.bones[name]; parent = bone.parent
        kw = {} if parent is None else {'parent_matrix': Matrix(desired[lookup[parent.name]].tolist()), 'parent_matrix_local': parent.matrix_local}
        rig.pose.bones[name].matrix_basis = bone.convert_local_to_pose(Matrix(desired[lookup[name]].tolist()), bone.matrix_local, invert=True, **kw)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    for label in ['full', 'four']:
        positions = []
        for name in ['Bounded neck27 triangulated body ' + label + ', unaccepted', new_names[label]]:
            evaluated = bpy.data.objects[name].evaluated_get(dg); mesh = evaluated.to_mesh()
            positions.append(np.array([v.co[:] for v in mesh.vertices], dtype=np.float32)); evaluated.to_mesh_clear()
        assert np.array_equal(*positions), (domain, source_id, label)
        checks.append({'domain': domain, 'sourceIndex': source_id, 'field': label, 'vertices': len(positions[0]),
            'evaluatedObjectLocalPositionsByteExact': True, 'maximumPositionDeltaM': 0.0})
for name, state in pose_before.items():
    b = rig.pose.bones[name]; b.rotation_mode = state['mode']; b.location = state['location']; b.rotation_quaternion = state['quaternion']
    b.rotation_euler = state['euler']; b.rotation_axis_angle = state['axis']; b.scale = state['scale']
for name, hidden in hides.items(): bpy.data.objects[name].hide_set(hidden)
bpy.context.view_layer.update()
# Deliberately no second save: the derivative's saved original pose is untouched.
assert pins == {p: sha(root / p) for p in pins}
report = {'status': 'UNACCEPTED_AUXILIARY_PRESERVATION_RESTORED_NEW_DERIVATIVE', 'native': str(native.relative_to(root)),
    'nativeSHA256': sha(native), 'fieldsUnchangedPath': str(field_path.relative_to(root)), 'fieldsUnchangedSHA256': sha(field_path),
    'recipeSHA256': sha(__file__), 'pins': pins, 'reopenedOriginalAndFailedObjectsExact': len(before['objects']),
    'originalPackedImagesExact': len(before['images']), 'originalMaterialGraphsExact': len(before['materials']),
    'original51RestBindSavedPoseExact': True, 'bodyChecks': rows, 'evaluatedEquivalenceWitnesses': checks,
    'limits': ['Only auxiliary definitions and memberships restored; geometry/topology/UV/PBR/normals/bind and intended semantic deform fields unchanged.',
        'All source97/98/99 files and controls retained. No appearance or motion consequence of old auxiliary omission is inferred.',
        'Three frozen witness equivalences are not an all1232-pose rerun or byte-identical game trace. Original99contact/area-compression/actual47identity failures remain red.',
        'New182body vertices have no original auxiliary identity; no fabricated auxiliary interpolation is claimed. Their authored bone weights are unchanged.',
        'No source field retune, new capture/export/install/GPU/model/worker/upload or promotion. All M0-M5/art/engine/device/player gates open; parent alone judges.']}
(out / 'restoration.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'nativeSHA256', 'reopenedOriginalAndFailedObjectsExact', 'bodyChecks', 'evaluatedEquivalenceWitnesses']}, indent=2))
