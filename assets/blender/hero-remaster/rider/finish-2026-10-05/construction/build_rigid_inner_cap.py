"""One admitted body06 field-only cap/alias derivative of immutable body05.

Set320 derived rows to head1 in the two derivative head controls. Seven rows
effectively change. Keep every original/source/outside row and all geometry,
rest normals, rig, materials and images exact. No motion, render or export.
"""
import hashlib
import json
from pathlib import Path
import struct

import bpy
import numpy as np

owned = Path(__file__).resolve().parent
root = owned.parents[5]
source = owned / 'body05/natural-foundation.blend'
fields_path = owned / 'body05/authored-neck-fields.npz'
proposal_root = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body05/inner-cap-field-preflight02'
mask_path = proposal_root / 'proposal/exact-mask-and-reference.npz'
proposal_path = proposal_root / 'proposal/preflight.json'
contract_path = proposal_root / 'parent-readback.json'
out = owned / 'body06'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body06'
native = out / 'natural-foundation.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not out.exists(), 'Fresh version only; no overwrite'
assert not native.exists()
assert sha(source) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
assert sha(fields_path) == '36277520249bcd2a8058a76c2f4a7595d7c460d3196e9bc59b3aa3a31690cb2d'
assert sha(mask_path) == '37f4fc4e292fb1f693d98b2d4e768adc1a5e683753e3c332ecf49ee9aca31ed7'
assert sha(proposal_path) == 'c88f9165358a83669abe75ec7ba501a3b5daec864cd0ff7f238f42cf3c00cac3'
contract = json.loads(contract_path.read_text())
assert contract['status'] == 'PARENT_MASK_AND_REFERENCE_READBACK_PASS_ONE_NATIVE_FIELD_TRIAL_ADMITTED'
assert contract['maskRows'] == 320
fields, mask = np.load(fields_path), np.load(mask_path)
ids = mask['expanded320NativeIDs'].astype(int)
changed_ids = mask['actualChanged7NativeIDs'].astype(int)
assert len(ids) == 320 and np.array_equal(changed_ids, contract['actualChangedIDs'])
assert np.array_equal(changed_ids, [43732, 43827, 43828, 43829, 43837, 43842, 44240])
assert np.all(ids >= 43707)
assert not np.intersect1d(ids, fields['headOuterCutNativeIDs']).size
names = fields['boneNames'].tolist()
head_index = names.index('head')
expected = fields['headFullWeights'].copy()
expected[ids] = mask['proposedHeadOnlyRows']
assert np.array_equal(fields['headFullWeights'], fields['headFourWeights'])
assert np.array_equal(fields['headFullWeights'][ids], mask['originalRawFullRows'])
assert np.array_equal(fields['headFourWeights'][ids], mask['originalRawFourRows'])
assert np.all(expected[ids, head_index] == 1) and np.all((expected[ids] > 0).sum(axis=1) == 1)
assert np.array_equal(np.flatnonzero(np.any(expected != fields['headFullWeights'], axis=1)), changed_ids)
outside = np.setdiff1d(np.arange(len(expected)), ids)
pins = {str(p.relative_to(root)): sha(p) for p in [source, fields_path, mask_path, proposal_path, contract_path]}
helper_path = root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/verify_extended_protected_data.py'
helper_text = helper_path.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(helper_text[helper_text.index('def value('):helper_text.index('def snapshot(')], str(helper_path), 'exec'), helpers)
pins[str(helper_path.relative_to(root))] = sha(helper_path)


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
    result = {'scenes': {}, 'meshes': {}, 'weights': {}, 'rigs': {}}
    for scene_name in ['Scene', 'Finish natural wearer diagnostic']:
        bpy.context.window.scene = bpy.data.scenes[scene_name]
        bpy.context.view_layer.update()
        result['scenes'][scene_name] = {o.name: helpers['object_state'](o) for o in bpy.context.scene.objects}
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                result['rigs'][obj.name] = rig_snapshot(obj)
    assert len(result['scenes']['Scene']) == 34
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        result['meshes'][obj.name] = mesh_snapshot(obj)
        if obj.name in ['Finish head FULL', 'Finish head FOUR']:
            result['weights'][obj.name] = {'outside320': membership_hash(obj, ids),
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


bpy.ops.wm.open_mainfile(filepath=str(source))
before = snapshot()
assert set(before['rigs']) == {'Independent anatomical foundation rig', 'Finish rig'}
for name in before['rigs']:
    assert len(before['rigs'][name]['rest']) == 51
for label in ['FULL', 'FOUR']:
    obj = bpy.data.objects['Finish head ' + label]
    assert obj.data.users == 1, 'No shared source mesh may receive field authoring'
    actual_before = raw_fields(obj)
    assert np.array_equal(actual_before, fields['head' + label.title() + 'Weights'])
    assert set(np.flatnonzero(actual_before[ids].sum(axis=0))) <= {names.index('neck'), head_index}
    obj.vertex_groups['neck'].remove(ids.tolist())
    obj.vertex_groups['head'].add(ids.tolist(), 1.0, 'REPLACE')
    actual_after = raw_fields(obj)
    assert np.array_equal(actual_after, expected)
    assert np.array_equal(actual_after[outside], actual_before[outside])
    assert np.array_equal(actual_after[:43707], actual_before[:43707])
    print('CAP_NATIVE_FIELDS', label, 'mask320 effective7 exact', flush=True)
after = snapshot()
assert before == after, 'Every non-field source and derivative state must remain exact before save'
arrays = {key: fields[key] for key in fields.files}
arrays['headBody05RawReferenceFullWeights'] = fields['headFullWeights'].copy()
arrays['headBody05RawReferenceFourWeights'] = fields['headFourWeights'].copy()
arrays['headFullWeights'] = expected.copy()
arrays['headFourWeights'] = expected.copy()
arrays['headCapRigid320NativeIDs'] = ids.copy()
arrays['headCapEffective7NativeIDs'] = changed_ids.copy()
assert np.array_equal(arrays['headBody05RawReferenceFullWeights'], fields['headFullWeights'])
assert np.array_equal(arrays['headBody05RawReferenceFourWeights'], fields['headFourWeights'])
for key in fields.files:
    if key not in ['headFullWeights', 'headFourWeights']:
        assert np.array_equal(arrays[key], fields[key])
out.mkdir()
new_fields = out / 'authored-neck-fields.npz'
np.savez_compressed(new_fields, **arrays)
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True, relative_remap=False)
bpy.ops.wm.open_mainfile(filepath=str(native))
reopened = snapshot()
assert before == reopened, 'Actual author reopen must preserve all non-field data'
for label in ['FULL', 'FOUR']:
    assert np.array_equal(raw_fields(bpy.data.objects['Finish head ' + label]), expected)
assert all(sha(root / path) == digest for path, digest in pins.items())
evidence.mkdir(parents=True, exist_ok=True)
receipt = {'status': 'UNACCEPTED_BODY06_FIELD_ONLY_NATIVE_AUTHOR_REOPEN_PASS_INDEPENDENT_QA_PENDING',
    'inputPins': pins, 'recipeSHA256': sha(__file__), 'native': str(native.relative_to(root)),
    'nativeSHA256': sha(native), 'fields': str(new_fields.relative_to(root)), 'fieldsSHA256': sha(new_fields),
    'parentTrialContractSHA256': sha(contract_path), 'blender': bpy.app.version_string,
    'maskRows': len(ids), 'effectiveChangedIDs': changed_ids.tolist(), 'field': 'head1 on derived320 in BOTH FULL and FOUR',
    'sourceBody05RawReferenceFullFourRetainedSeparate': True,
    'allOriginal43707AndOutside320FieldsExact': True, 'everyMeshRestXYZTopologyUVRawDecodedNormalsMaterialSlotsExact': True,
    'allOriginal34ObjectsAndWeightsExact': True, 'allOtherDerivativeWeightsExact': True,
    'originalAndCopiedOwn51RestWorldSavedPoseExact': True, 'allMaterialsImagesExact': True,
    'authorSaveReopenNonFieldSnapshotExact': True, 'authorSaveReopenRawHeadFieldsExact': True,
    'frozenSourcePinsStillExact': True, 'nonFieldSnapshotSHA256': hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
    'limits': ['Author verification and actual reopen only; independent save/reopen, evaluated native/manual, propercontacts and custom-normal QA remain pending.',
        'One field-only trial; no geometry/bone/rest-normal rewrite, movie, GLB/export, engine/GPU or ordinary player asset.',
        'Inherited shoulder/hip/body/boxer failures remain. No art, body/face, contact, mobile or promotion acceptance.',
        'Original helper snapshot scope excludes read-only runtime properties and implicit animation collections; no code changes or source pose assignment occurred.']}
(evidence / 'authoring.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
print('BODY06_NATIVE_FROZEN', sha(native), sha(new_fields), flush=True)
