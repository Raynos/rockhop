"""Apply exactly the frozen330 shoulder fields to body06; save/reopen body07.

Consume parent-frozen four-row storage correction; retain raw trial45 FULL.
No harmonic recomputation, global normalization, geometry, head, normal, UV, material,
pose or bone edit. Original source/all scenes/global34 stay exact. Unaccepted.
"""
import hashlib
import json
from pathlib import Path
import struct
import time

import bpy
import numpy as np

started = time.monotonic()
root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
owned = root / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction'
source = owned / 'body06/natural-foundation.blend'
fields_path = owned / 'body06/authored-neck-fields.npz'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07'
proposal_root = evidence / 'array-preflight04'
proposal_fields_path = proposal_root / 'frozen-shoulder-fields.npz'
proposal_path = proposal_root / 'preflight.json'
contract_path = evidence / 'parent-preflight45.json'
# Root48 array-only storage authority; separate root native49 admission required.
storage_fields_path = evidence / 'native-transport48/native-storage-fields.npz'
storage_contract_path = evidence / 'native-transport48/scope.json'
storage_pins = {
    storage_fields_path: '0bcf58024d83c84a4d4fea9b7ae5fa69f3b82141758456e664acfd6581fb64e6',
    storage_contract_path: 'cbb696e46d5b332f21a934c93fa72645347a9d3bbaca709ee4d0a2ea0fba35ca',
}
diagnostics_path = evidence / 'native-author49-fields.json'
out = owned / 'body07'
native = out / 'natural-foundation.blend'
new_fields = out / 'authored-neck-fields.npz'
receipt_path = evidence / 'authoring.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not diagnostics_path.exists(), 'Fresh native diagnostic receipt required'
assert not native.exists() and not new_fields.exists() and not receipt_path.exists(), 'Fresh native/fields/receipt required; scripts already inhabit body07'
expected_pins = {
    source: '66c45ab5a76fe592b0b284a5a96dc3e6ba1f74b2854e5dae849aaff03f43bb77',
    fields_path: 'ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a',
    proposal_fields_path: 'dc92e1192a411d0ba90a67ef7144bdf697008164b2f2014c10dff69a149dfd35',
    proposal_path: '18460dcbd0dc1134fec597131ab60076d5004cbed7f641e69a58cdb6b2df551c',
    contract_path: '013cfe056e9d360c3f8cf4f8aabbdfd7eccf237d22cd2515971ba0891895bbf1',
}
expected_pins.update(storage_pins)
for path, digest in expected_pins.items():
    assert sha(path) == digest, str(path)
fields = np.load(fields_path)
proposal = np.load(proposal_fields_path)
report = json.loads(proposal_path.read_text())
contract = json.loads(contract_path.read_text())
storage = np.load(storage_fields_path)
storage_contract = json.loads(storage_contract_path.read_text())
assert storage_contract['status'] == 'ROOT_ADMITS_FOUR_ONE_HOT_STORAGE_REPRESENTATIONS_NOT_NATIVE_PASS'
assert storage_contract['storageFields']['sha256'] == sha(storage_fields_path)
assert storage_contract['trial45']['sha256'] == sha(proposal_fields_path)
assert contract['status'] == 'ROOT_READBACK_ADMITS_ONE_NATIVE_AUTHOR_NOT_ACCEPTED'
assert contract['candidateFieldsSHA256'] == sha(proposal_fields_path)
assert report['status'] == 'UNACCEPTED_ARRAY_ONLY_FIXED_SHOULDER_FIELDS'
assert not report['outcomeFailures'] and not report['aliasConflicts']
assert report['fourSlotMaximum'] == 4
names = fields['boneNames'].tolist()
assert names == proposal['boneNames'].tolist() and len(names) == 51
ids = proposal['mask438NativeIDs'].astype(int)
trial45_raw_full = proposal['productionFullWeights']
assert np.array_equal(storage['trial45RawProductionFullReference'], trial45_raw_full)
assert set(storage.files) == set(proposal.files) | {'trial45RawProductionFullReference'}
for key in proposal.files:
    if key != 'productionFullWeights':
        assert np.array_equal(storage[key], proposal[key]), 'Storage48 changed preserved array: ' + key
expected = {'FULL': storage['productionFullWeights'], 'FOUR': storage['productionFourWeights']}
assert np.array_equal(expected['FOUR'], proposal['productionFourWeights'])
correction_rows = np.flatnonzero(np.any(expected['FULL'] != trial45_raw_full, axis=1))
assert correction_rows.tolist() == [36, 111, 4588, 4661]
for row in correction_rows:
    cols = np.flatnonzero(trial45_raw_full[row])
    assert len(cols) == 1
    col = int(cols[0])
    assert names[col] == ('shoulder.L' if row in [36, 111] else 'shoulder.R')
    assert trial45_raw_full[row, col] == np.float32(1.0000001192092896)
    assert expected['FULL'][row, col] == np.float32(1)
    assert np.count_nonzero(expected['FULL'][row]) == 1
unchanged_storage = np.setdiff1d(np.arange(len(trial45_raw_full)), correction_rows)
assert np.array_equal(expected['FULL'][unchanged_storage], trial45_raw_full[unchanged_storage])
def normalized(value):
    value = value.astype(np.float64)
    return value / value.sum(axis=1)[:, None]
assert np.array_equal(normalized(expected['FULL']), normalized(trial45_raw_full))
assert (expected['FULL'] <= 1).all() and (expected['FOUR'] <= 1).all()
controls = {'FULL': fields['bodyFullWeights'], 'FOUR': fields['bodyFourWeights']}
assert np.array_equal(fields['bodyRestXYZ'], proposal['bodyRestXYZReference'])
assert np.array_equal(fields['bodyTriangles'], proposal['bodyTrianglesReference'])
assert np.array_equal(controls['FULL'], proposal['body06NativeRawFullReference'])
assert np.array_equal(controls['FOUR'], proposal['body06NativeRawFourReference'])
changed = {label: np.flatnonzero(np.any(value != controls[label], axis=1)) for label, value in expected.items()}
changed_ids = changed['FULL']
assert np.array_equal(changed_ids, changed['FOUR']) and len(changed_ids) == 330
assert len(ids) == len(np.unique(ids)) == 438 and np.isin(changed_ids, ids).all()
assert np.array_equal(changed_ids, report['changedNativeIDs']['full'])
assert np.array_equal(changed_ids, report['changedNativeIDs']['four'])
assert np.all(changed_ids < 9037), 'Original derivative body rows only; no derived neck/cut rows'
outside = np.setdiff1d(np.arange(len(fields['bodyRestXYZ'])), changed_ids)
for label, value in expected.items():
    assert value.dtype == np.float32 and np.isfinite(value).all() and np.all(value >= 0)
    assert np.array_equal(value[outside], controls[label][outside])
    for side in ['L', 'R']:
        mask = proposal[side + 'maskNativeIDs'].astype(int)
        boundary = proposal[side + 'boundaryNativeIDs'].astype(int)
        primary = [names.index('chest'), names.index('shoulder.' + side), names.index('upperArm.' + side)]
        other = np.setdiff1d(np.arange(51), primary)
        assert len(mask) == 219 and len(boundary) == 54
        assert np.array_equal(value[mask][:, other], controls[label][mask][:, other])
        assert np.array_equal(value[boundary], controls[label][boundary])
assert np.max(np.count_nonzero(expected['FOUR'], axis=1)) == 4
pins = {str(p.relative_to(root)): digest for p, digest in expected_pins.items()}
helper_path = root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/verify_extended_protected_data.py'
assert sha(helper_path) == '8a5c9159909655ae728a7e1b3095ee88fd4bbe4f4516bb3e5c63b421143e1512'
helper_text = helper_path.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(helper_text[helper_text.index('def value('):helper_text.index('def snapshot(')], str(helper_path), 'exec'), helpers)
pins[str(helper_path.relative_to(root))] = sha(helper_path)
original_inventory_path = root / 'docs/evidence/hero-remaster/finish-2026-10-05/runtime/body05-preservation.json'
assert sha(original_inventory_path) == '8e089744d4c5701dae701bed752a76e6d44c8544ef0ff61710d7f2c7fe424f31'
original_inventory = json.loads(original_inventory_path.read_text())
original_names = sorted(original_inventory['originalObjectChecks'])
assert len(original_names) == 34 and all(original_inventory['originalObjectChecks'].values())
pins[str(original_inventory_path.relative_to(root))] = sha(original_inventory_path)


def membership_hash(obj, omitted=(), auxiliary_only=False):
    omitted = set(map(int, omitted))
    digest = hashlib.sha256()
    for vertex in obj.data.vertices:
        if vertex.index in omitted:
            continue
        for item in vertex.groups:
            if auxiliary_only and obj.vertex_groups[item.group].name in names:
                continue
            digest.update(struct.pack('<IIf', vertex.index, item.group, item.weight))
    return digest.hexdigest()


def mesh_snapshot(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    return {'xyz': helpers['array_digest'](mesh.vertices, 'co', 3),
        'loopVertices': helpers['array_digest'](mesh.loops, 'vertex_index', dtype=np.int32),
        'polygonStarts': helpers['array_digest'](mesh.polygons, 'loop_start', dtype=np.int32),
        'polygonSizes': helpers['array_digest'](mesh.polygons, 'loop_total', dtype=np.int32),
        'triangles': helpers['array_digest'](mesh.loop_triangles, 'vertices', 3, np.int32),
        'triangleCorners': helpers['array_digest'](mesh.loop_triangles, 'loops', 3, np.int32),
        'materialIndices': helpers['array_digest'](mesh.polygons, 'material_index', dtype=np.int32),
        'smoothFlags': helpers['array_digest'](mesh.polygons, 'use_smooth', dtype=np.bool_),
        'UV': {uv.name: helpers['array_digest'](uv.data, 'uv', 2) for uv in mesh.uv_layers},
        'attributesAndAllNormals': helpers['mesh_extra'](mesh),
        'materials': [m.name if m else None for m in mesh.materials],
        'groupNames': [g.name for g in obj.vertex_groups]}


def rig_snapshot(obj):
    return {'object': helpers['object_state'](obj), 'scale': list(obj.scale),
        'rest': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
            'matrix': helpers['value'](b.matrix_local), 'head': list(b.head_local),
            'tail': list(b.tail_local), 'deform': b.use_deform} for b in obj.data.bones],
        'poses': {b.name: {'basis': helpers['value'](b.matrix_basis),
            'matrix': helpers['value'](b.matrix), 'properties': helpers['properties'](b),
            'constraints': [helpers['properties'](c) for c in b.constraints]} for b in obj.pose.bones}}


def snapshot():
    saved_scene = bpy.context.window.scene
    result = {'activeScene': saved_scene.name, 'scenes': {}, 'sceneProperties': {}, 'meshes': {}, 'weights': {}, 'rigs': {}}
    for scene_name in sorted(bpy.data.scenes.keys()):
        bpy.context.window.scene = bpy.data.scenes[scene_name]
        bpy.context.view_layer.update()
        result['sceneProperties'][scene_name] = helpers['properties'](bpy.context.scene)
        result['scenes'][scene_name] = {o.name: helpers['object_state'](o) for o in bpy.context.scene.objects}
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                result['rigs'][obj.name] = rig_snapshot(obj)
    bpy.context.window.scene = saved_scene
    bpy.context.view_layer.update()
    assert set(original_names) <= set(bpy.data.objects.keys()), 'Original34 global identities must all remain present'
    result['globalObjects'] = {o.name: helpers['object_state'](o) for o in bpy.data.objects}
    result['original34Names'] = original_names
    # Scene membership is compared exactly before/after; global originals can
    # be unlinked and therefore are not inferred from any Scene object count.
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        result['meshes'][obj.name] = mesh_snapshot(obj)
        if obj.name in ['Finish body FULL', 'Finish body FOUR']:
            result['weights'][obj.name] = {'outside330': membership_hash(obj, changed_ids),
                                         'auxiliary': membership_hash(obj, auxiliary_only=True)}
        else:
            result['weights'][obj.name] = {'all': membership_hash(obj)}
    result['materials'] = {m.name: {'properties': helpers['properties'](m),
        'nodes': [{'name': n.name, 'type': n.bl_idname, 'properties': helpers['properties'](n),
            'inputs': [(s.name, helpers['value'](s.default_value)) for s in n.inputs if hasattr(s, 'default_value')]}
            for n in m.node_tree.nodes] if m.node_tree else None,
        'links': [(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name)
            for l in m.node_tree.links] if m.node_tree else None} for m in bpy.data.materials}
    result['images'] = {i.name: {'size': list(i.size), 'source': i.source, 'filepath': i.filepath,
        'packed': hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None} for i in bpy.data.images}
    return result


def raw_fields(obj):
    result = np.zeros((len(obj.data.vertices), len(names)), np.float32)
    for vertex in obj.data.vertices:
        for membership in vertex.groups:
            name = obj.vertex_groups[membership.group].name
            if name in names:
                result[vertex.index, names.index(name)] = membership.weight
    return result


diagnostics = {'status': 'AUTHOR49_STARTED_NOT_ACCEPTED', 'stages': [],
    'trial45RawFullSHA256': hashlib.sha256(trial45_raw_full.tobytes()).hexdigest(),
    'storageFullSHA256': hashlib.sha256(expected['FULL'].tobytes()).hexdigest(),
    'storageCorrectionRows': correction_rows.tolist(),
    'normalizedFullLBSFieldsByteExact': True,
    'rnaWeightSchema': None}


def field_diagnostic(stage, label, actual, reference):
    # Persist every differing scalar, without truncation, before any equality assert.
    cells = np.argwhere(actual != reference)
    record = {'stage': stage, 'label': label, 'actualMinimum': float(actual.min()),
        'actualMaximum': float(actual.max()), 'expectedMinimum': float(reference.min()),
        'expectedMaximum': float(reference.max()),
        'actualPositiveMinimum': float(actual[actual > 0].min()) if np.any(actual > 0) else None,
        'nonfiniteCells': np.argwhere(~np.isfinite(actual)).tolist(),
        'mismatchCount': len(cells), 'mismatches': [
            {'nativeID': int(row), 'column': int(col), 'bone': names[int(col)],
             'actual': float(actual[row, col]), 'expected': float(reference[row, col]),
             'actualFloat32Bits': int(actual[row, col].view(np.uint32)),
             'expectedFloat32Bits': int(reference[row, col].view(np.uint32))}
            for row, col in cells]}
    diagnostics['stages'].append(record)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + '\n')
    print('AUTHOR49_FIELD_DIAGNOSTIC', stage, label, 'mismatches', len(cells),
          'actualMinMax', record['actualMinimum'], record['actualMaximum'], flush=True)
    return not len(cells)


bpy.ops.wm.open_mainfile(filepath=str(source))
saved_active_scene = bpy.context.window.scene.name
before = snapshot()
rna_weight = bpy.types.VertexGroupElement.bl_rna.properties['weight']
rna_add_weight = bpy.types.VertexGroup.bl_rna.functions['add'].parameters['weight']
diagnostics['rnaWeightSchema'] = {name: {'hardMin': prop.hard_min, 'hardMax': prop.hard_max,
    'softMin': prop.soft_min, 'softMax': prop.soft_max, 'type': prop.type}
    for name, prop in [('VertexGroupElement.weight', rna_weight), ('VertexGroup.add.weight', rna_add_weight)]}
print('AUTHOR49_RNA_WEIGHT_RANGE', diagnostics['rnaWeightSchema'], flush=True)
assert set(before['rigs']) == {'Independent anatomical foundation rig', 'Finish rig'}
for name in before['rigs']:
    assert len(before['rigs'][name]['rest']) == 51
source_actual = {label: raw_fields(bpy.data.objects['Finish body ' + label]) for label in ['FULL', 'FOUR']}
source_field_pass = [field_diagnostic('source-read', label, source_actual[label], controls[label]) for label in ['FULL', 'FOUR']]
assert all(source_field_pass), 'Source field mismatch; both labels and all cells logged'
author_field_pass = []
for label in ['FULL', 'FOUR']:
    obj = bpy.data.objects['Finish body ' + label]
    assert obj.data.users == 1, 'Never edit a shared source mesh'
    actual_before = source_actual[label]
    # Replace only memberships whose exact frozen Float32 value changes.
    # Existing OTHER/nonbone values and group ordering receive no author call.
    memberships_changed = 0
    for vertex_id in changed_ids:
        columns = np.flatnonzero(expected[label][vertex_id] != actual_before[vertex_id])
        for column in columns:
            group = obj.vertex_groups[names[column]]
            value = float(expected[label][vertex_id, column])
            if value == 0:
                group.remove([int(vertex_id)])
            else:
                group.add([int(vertex_id)], value, 'REPLACE')
            memberships_changed += 1
    actual_after = raw_fields(obj)
    author_field_pass.append(field_diagnostic('after-write', label, actual_after, expected[label]))
    print('SHOULDER_NATIVE_FIELDS', label, 'frozen330 readback', 'memberships', memberships_changed, flush=True)
assert all(author_field_pass), 'Author field mismatch; both labels and all cells logged'
after = snapshot()
assert before == after, 'Non-field source/global/scenes/derivative snapshot must remain exact before save'
arrays = {key: fields[key] for key in fields.files}
arrays['bodyShoulderTrial45RawFullWeights'] = trial45_raw_full.copy()
arrays['bodyShoulderStorage48CorrectionNativeIDs'] = correction_rows.copy()
arrays['bodyBody06RawReferenceFullWeights'] = controls['FULL'].copy()
arrays['bodyBody06RawReferenceFourWeights'] = controls['FOUR'].copy()
arrays['bodyFullWeights'] = expected['FULL'].copy()
arrays['bodyFourWeights'] = expected['FOUR'].copy()
arrays['bodyShoulderHarmonicScope438NativeIDs'] = ids.copy()
arrays['bodyShoulderHarmonicChanged330NativeIDs'] = changed_ids.copy()
for side in ['L', 'R']:
    for name in ['maskNativeIDs', 'maskCanonicalIDs', 'boundaryNativeIDs', 'boundaryCanonicalIDs', 'shoulderAnchorNativeIDs', 'shoulderAnchorCanonicalIDs', 'armAnchorNativeIDs', 'armAnchorCanonicalIDs', 'unknownNativeIDs', 'unknownCanonicalIDs', 'HarmonicPartition']:
        arrays['bodyShoulderHarmonic' + side + name] = proposal[side + name].copy()
for key in fields.files:
    if key not in ['bodyFullWeights', 'bodyFourWeights']:
        assert np.array_equal(arrays[key], fields[key]), key
np.savez_compressed(new_fields, **arrays)
bpy.context.window.scene = bpy.data.scenes[saved_active_scene]
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True, relative_remap=False)
bpy.ops.wm.open_mainfile(filepath=str(native))
reopened = snapshot()
reopen_field_pass = [field_diagnostic('reopen', label, raw_fields(bpy.data.objects['Finish body ' + label]), expected[label]) for label in ['FULL', 'FOUR']]
assert all(reopen_field_pass), 'Reopened field mismatch; both labels and all cells logged'
assert before == reopened, 'Actual reopen must preserve all non-field data and saved active scene'
reopened_fields = np.load(new_fields)
for key, value in arrays.items():
    assert np.array_equal(reopened_fields[key], value), key
assert all(sha(root / path) == digest for path, digest in pins.items())
receipt = {'status': 'UNACCEPTED_BODY07_FROZEN_SHOULDER_FIELDS_NATIVE_SAVE_REOPEN_PASS_QA_PENDING',
    'inputPins': pins, 'recipeSHA256': sha(__file__), 'native': str(native.relative_to(root)), 'nativeSHA256': sha(native),
    'fields': str(new_fields.relative_to(root)), 'fieldsSHA256': sha(new_fields), 'parentTrialContractSHA256': sha(contract_path),
    'parentStorage48ContractSHA256': sha(storage_contract_path),
    'storageCorrectionRows': correction_rows.tolist(), 'normalizedFullLBSFieldsByteExact': True,
    'nativeDiagnostics': str(diagnostics_path.relative_to(root)),
    'blender': bpy.app.version_string, 'elapsedSeconds': time.monotonic()-started,
    'scopeRows': 438, 'effectiveChangedRows': 330, 'effectiveChangedNativeIDs': changed_ids.tolist(),
    'weightHandling': 'Exact parent-frozen storage FULL/Four Float32 memberships. Only four single-positive FULL values capped from 1.0000001192092896 to1 in frozen array48, normalized FULL LBS byte-exact to trial45. Raw trial45 FULL retained separate. No harmonic rerun/truncation/global normalization; OTHER/boundary/outside330 raw fields exact.',
    'body06NativeRawFullFourReferencesRetainedSeparate': True, 'body52RawSourceFullAndCanonicalFourControlsRetainedSeparate': True,
    'allHeadIncludingCapAndProtectedFieldsExact': True, 'everyMeshRestXYZTopologyUVRawDecodedNormalsMaterialSlotsExact': True,
    'allOriginal34GlobalObjectsAndMembershipsExact': True, 'allSceneMembershipsAndActiveSceneExact': True, 'allOtherDerivativeFieldsExact': True,
    'originalAndCopiedOwn51RestWorldSavedPoseExact': True, 'allMaterialsImagesExact': True,
    'authorSaveReopenNonFieldSnapshotExact': True, 'authorSaveReopenRawBodyFieldsExact': True, 'frozenSourcePinsStillExact': True,
    'nonFieldSnapshotSHA256': hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
    'limits': ['Author verification/save/reopen only; independent evaluated native/manual, whole contacts and held-out played shoulder QA pending.',
        'Frozen330 fields only; no geometry/bone/UV/normal/material/pose changes, GLB/export, render or player asset promotion.',
        'Ten-pose array target pairs cleared but novel/continuous-time crossings and anatomical appearance remain unmeasured; maximum predicted displacement138.34mm.',
        'Inherited body/boxer/hip contact and head shader-normal failures remain open. No face/body/garment/art/mobile acceptance.',
        'Helper snapshot excludes read-only runtime properties and implicit animation collections; no pose/action assignment performed.']}
diagnostics['status'] = 'AUTHOR49_SAVE_REOPEN_FIELDS_EXACT_UNACCEPTED'
diagnostics_path.write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + '\n')
receipt['nativeDiagnosticsSHA256'] = sha(diagnostics_path)
with receipt_path.open('x') as file:
    json.dump(receipt, file, indent=2, allow_nan=False)
    file.write('\n')
print('BODY07_NATIVE_FROZEN', sha(native), sha(new_fields), flush=True)
