"""Fresh reopen of a declared field-only candidate; no save, render or export.

Compare every body05 object and mesh attribute before assigning the ten exact
saved51 pose payloads. True triangle geometry is computed from vertex crosses;
RNA polygon normals are never interpreted as geometric face normals.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix

p = argparse.ArgumentParser(description=__doc__)
for name in ('base', 'candidate', 'candidate-sha', 'mask', 'intake', 'out'):
    p.add_argument('--' + name, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
base, candidate, mask_path, intake, out = [Path(getattr(a, name)).resolve()
                                        for name in ('base', 'candidate', 'mask', 'intake', 'out')]
assert not out.exists()
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
assert sha(base) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
assert sha(candidate) == a.candidate_sha
assert sha(mask_path) == '37f4fc4e292fb1f693d98b2d4e768adc1a5e683753e3c332ecf49ee9aca31ed7'
mask = np.load(mask_path)
changed_ids = mask['actualChanged7NativeIDs']
scope_ids = mask['expanded320NativeIDs']
alias_ids, representative_ids = mask['additionalInnerNativeAliases'], mask['aliasRepresentativeNativeIDs']
report_path = intake / 'report.json'
old_report = json.loads(report_path.read_text())
rest_path = intake / old_report['rest']['path']
assert sha(rest_path) == old_report['rest']['sha256']
old_rest = json.loads(gzip.decompress(rest_path.read_bytes()))
names = old_rest['jointOrder']
assert len(names) == 51
pins = {str(x): sha(x) for x in (base, candidate, mask_path, report_path, rest_path)}
helper_path = Path('assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/verify_extended_protected_data.py').resolve()
text = helper_path.read_text()
h = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(text[text.index('def value('):text.index('before=snapshot(original)')], str(helper_path), 'exec'), h)
digest = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def weights(obj):
    raw = np.zeros((len(obj.data.vertices), 51), np.float32)
    auxiliary = []
    for v in obj.data.vertices:
        extra = []
        for item in v.groups:
            name = obj.vertex_groups[item.group].name
            if name in names:
                raw[v.index, names.index(name)] = item.weight
            else:
                extra.append((name, item.weight))
        auxiliary.append(sorted(extra))
    return raw, digest(auxiliary)

def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result = {'scene': bpy.context.scene.name, 'scenes': {}}
    for scene in bpy.data.scenes:
        bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        objects = {}
        # Original34 inventory includes unlinked preserved objects. Compare all
        # global objects in each matching scene context; linkage is separate.
        for obj in bpy.data.objects:
            row = {'object': h['object_state'](obj), 'properties': h['custom_properties'](obj)}
            if obj.type == 'MESH':
                raw, auxiliary = weights(obj)
                row.update(mesh=h['mesh_extra'](obj.data), xyz=h['array_digest'](obj.data.vertices, 'co', 3),
                           polygons=[list(poly.vertices) for poly in obj.data.polygons],
                           groups=[g.name for g in obj.vertex_groups], auxiliary=auxiliary,
                           materials=[m.name if m else None for m in obj.data.materials])
                if obj.name in ('Finish head FULL', 'Finish head FOUR'):
                    expected = np.array(old_rest['parts']['head'][('full' if obj.name.endswith('FULL') else 'four') + 'RawWeights'], np.float32)
                    if path == candidate:
                        expected[scope_ids] = mask['proposedHeadOnlyRows']
                    assert np.array_equal(raw, expected), ('actual semantic fields', obj.name)
                    row['deformWeights'] = 'explicit admitted head field checked separately'
                else:
                    row['deformWeights'] = hashlib.sha256(raw.tobytes()).hexdigest()
            if obj.type == 'ARMATURE':
                row['rigData'] = h['properties'](obj.data)
                row['bones'] = [{ 'name': b.name, 'parent': b.parent.name if b.parent else None,
                                  'rest': h['value'](b.matrix_local), 'head': list(b.head_local),
                                  'tail': list(b.tail_local), 'deform': b.use_deform } for b in obj.data.bones]
                row['poses'] = {b.name: {'matrix': h['value'](b.matrix), 'basis': h['value'](b.matrix_basis),
                                       'properties': h['properties'](b), 'custom': h['custom_properties'](b),
                                       'constraints': [h['properties'](c) for c in b.constraints]} for b in obj.pose.bones}
            objects[obj.name] = digest(row)
        result['scenes'][scene.name] = {'linkedObjectNames': sorted(o.name for o in scene.objects),
                                      'globalObjectSnapshots': objects}
    result['materials'] = {m.name: digest({'properties': h['properties'](m),
        'nodes': [{'name': n.name, 'type': n.bl_idname, 'properties': h['properties'](n),
                   'inputs': [(s.name, h['value'](s.default_value)) for s in n.inputs if hasattr(s, 'default_value')]} for n in m.node_tree.nodes] if m.node_tree else None,
        'links': [(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name) for l in m.node_tree.links] if m.node_tree else None}) for m in bpy.data.materials}
    result['images'] = {i.name: {'size': list(i.size), 'source': i.source, 'filepath': i.filepath,
                                'packed': hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None} for i in bpy.data.images}
    return result

before, after = snapshot(base), snapshot(candidate)
assert before == after, ('Field-only native scope differs', before, after)
bpy.context.window.scene = bpy.data.scenes[after['scene']]
rig = bpy.data.objects['Finish rig']
assert [b.name for b in rig.data.bones] == names
rig.animation_data_clear()
for b in rig.pose.bones:
    for constraint in b.constraints:
        constraint.mute = True
rig.hide_viewport = False
objects = {region: {kind: bpy.data.objects['Finish ' + region + ' ' + kind.upper()]
                     for kind in ('full', 'four')} for region in ('head', 'body')}
rest_world = {}
for region in objects:
    part = old_rest['parts'][region]
    world = np.array(part['objectWorld'])
    rest_world[region] = (np.c_[part['xyz'], np.ones(len(part['xyz']))] @ world.T)[:, :3]
    for obj in objects[region].values():
        obj.animation_data_clear()
        obj.hide_viewport = False
        obj.hide_set(False)
        assert not obj.data.shape_keys
        active = [m for m in obj.modifiers if m.show_viewport]
        assert len(active) == 1 and active[0].type == 'ARMATURE' and active[0].object == rig and not active[0].use_deform_preserve_volume
out.mkdir(parents=True)

def save(name, payload):
    path = out / name
    with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as stream:
        stream.write(json.dumps(payload, separators=(',', ':'), allow_nan=False).encode())
    return {'path': name, 'sha256': sha(path), 'bytes': path.stat().st_size}

def crossing_stats(xyz, faces, ids, transported):
    q = xyz[faces[ids]]
    cross = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    ref = transported[ids]
    ref_lengths = np.linalg.norm(ref, axis=1)
    dot = np.einsum('ij,ij->i', cross, ref) / (lengths * ref_lengths)
    old = rest_world['head'][faces[ids]]
    old_area = np.linalg.norm(np.cross(old[:, 1] - old[:, 0], old[:, 2] - old[:, 0]), axis=1)
    return {'minimumArea2M2': float(lengths.min()), 'minimumAreaRatioToRest': float((lengths / old_area).min()),
            'maximumAreaRatioToRest': float((lengths / old_area).max()), 'minimumDotToTransportedHeadReference': float(dot.min()),
            'opposedTriangleIDs': ids[dot < 0].tolist(), 'zeroAreaTriangleIDs': ids[lengths == 0].tolist()}

records, samples = [], []
rig_world = np.array(rig.matrix_world)
head_index = names.index('head')
for pin in old_report['samples']:
    path = intake / pin['path']
    assert sha(path) == pin['sha256']
    pins[str(path)] = pin['sha256']
    old = json.loads(gzip.decompress(path.read_bytes()))
    assert list(old['poseBasisBlender']) == names
    for name in names:
        bone = rig.pose.bones[name]
        pose = old['poseBasisBlender'][name]
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)
        bone.location, bone.rotation_quaternion, bone.scale = pose['location'], pose['quaternionWXYZ'], pose['scale']
    bpy.context.view_layer.update()
    actual_pose = {name: {'location': list(rig.pose.bones[name].location), 'quaternionWXYZ': list(rig.pose.bones[name].rotation_quaternion),
                          'scale': list(rig.pose.bones[name].scale)} for name in names}
    assert actual_pose == old['poseBasisBlender'], 'Exact saved pose payload changed'
    skin = np.array([rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted() for name in names])
    assert np.array_equal(skin, np.array(old['skinNativeRows'])), 'Exact skin matrices changed'
    native = {'index': old['index'], 'case': old['case'], 'phase': old['phase'], 'poseBasisBlender': actual_pose,
              'skinNativeRows': skin.tolist(), 'parts': {}}
    record = {'index': old['index'], 'case': old['case'], 'phase': old['phase'], 'posePayloadExact': True,
              'skinMatricesExact': True, 'parts': {}}
    for region, fields in objects.items():
        reference = old_rest['parts'][region]
        faces = np.array(reference['faces'], int)
        world = np.array(reference['objectWorld'])
        to_rig = np.linalg.inv(rig_world) @ world
        to_local = np.linalg.inv(to_rig)
        corner_ids = np.array(reference['cornerVertices'], int)
        rest_normals = np.array(reference['cornerNormals'])
        for kind, obj in fields.items():
            e = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = e.to_mesh()
            mesh.calc_loop_triangles()
            xyz = np.array([list(e.matrix_world @ v.co) for v in mesh.vertices])
            actual_faces = np.array([list(t.vertices) for t in mesh.loop_triangles], int)
            normals = np.array([list(e.matrix_world.to_3x3().inverted().transposed() @ n.vector) for n in mesh.corner_normals])
            normals /= np.linalg.norm(normals, axis=1)[:, None]
            e.to_mesh_clear()
            assert np.isfinite(xyz).all() and np.isfinite(normals).all()
            topology = bool(np.array_equal(actual_faces, faces))
            assert topology, ('Evaluated triangle change', region, kind, old['index'])
            raw, _ = weights(obj)
            normalized = raw.astype(float) / raw.sum(axis=1, dtype=np.float64)[:, None]
            homogeneous = np.c_[reference['xyz'], np.ones(len(reference['xyz']))] @ to_rig.T
            manual_xyz = (np.einsum('vj,jab,vb->va', normalized, skin, homogeneous) @ rig_world.T)[:, :3]
            position_error = np.linalg.norm(xyz - manual_xyz, axis=1)
            linear = np.einsum('ab,vj,jbc,cd->vad', to_local, normalized, skin, to_rig)[:, :3, :3]
            predicted = np.einsum('vab,vb->va', linear[corner_ids], rest_normals) @ np.linalg.inv(world[:3, :3])
            predicted /= np.linalg.norm(predicted, axis=1)[:, None]
            error = np.linalg.norm(predicted - normals, axis=1)
            worst = int(error.argmax())
            row = {'evaluatedTrianglesExact': topology, 'maximumCPUFormulaNativeCornerNormalError': float(error[worst]),
                   'maximumNormalizedManualNativePositionErrorM': float(position_error.max()),
                   'worstPositionVertex': int(position_error.argmax()),
                   'worstCorner': worst, 'worstVertex': int(corner_ids[worst]),
                   'predictedWorldNormal': predicted[worst].tolist(), 'actualWorldNormal': normals[worst].tolist()}
            if region == 'head':
                row['priorWitnessCorners'] = {str(c): {'vertex': int(corner_ids[c]), 'normalError': float(error[c]),
                    'predictedWorldNormal': predicted[c].tolist(), 'actualWorldNormal': normals[c].tolist()}
                    for c in (183498, 206973)}
                gaps = np.linalg.norm(xyz[alias_ids] - xyz[representative_ids], axis=1)
                row['all17ActualAliasGapsM'] = gaps.tolist()
                row['maximumActualAliasGapM'] = float(gaps.max())
                q = rest_world['head'][faces]
                cross = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0])
                head_world = rig_world @ skin[head_index] @ np.linalg.inv(rig_world)
                transported = cross @ np.linalg.inv(head_world[:3, :3])
                row['cap301'] = crossing_stats(xyz, faces, mask['capTriangleIDs'], transported)
                row['lining459'] = crossing_stats(xyz, faces, mask['adjacentLiningTriangleIDs'], transported)
            else:
                assert np.array_equal(xyz, np.array(old['parts'][region][kind]['xyzWorld'])), 'Body actual evaluation changed'
                assert np.array_equal(normals, np.array(old['parts'][region][kind]['normalWorldCorners'])), 'Body actual moving normals changed'
                row['actualBodyXYZAndNormalExactToBody05'] = True
            native['parts'].setdefault(region, {})[kind] = {'xyzWorld': xyz.tolist(), 'faces': actual_faces.tolist(), 'normalWorldCorners': normals.tolist()}
            record['parts'].setdefault(region, {})[kind] = row
        full_xyz = np.array(native['parts'][region]['full']['xyzWorld'])
        four_xyz = np.array(native['parts'][region]['four']['xyzWorld'])
        record['parts'][region]['maximumNativeFullFourPositionDifferenceM'] = float(np.linalg.norm(full_xyz - four_xyz, axis=1).max())
    samples.append(save('sample-%04d.json.gz' % old['index'], native))
    records.append(record)
    print('BODY06_NATIVE_SAMPLE', old['index'], flush=True)
assert pins == {path: sha(path) for path in pins}
receipt = {'status': 'UNACCEPTED_FRESH_REOPEN_FIELD_SCOPE_AND_TEN_POSE_NATIVE_DIAGNOSTIC', 'sourcePins': pins,
           'recipeSHA256': sha(__file__), 'helperSHA256': sha(helper_path), 'blender': bpy.app.version_string,
           'allBody05ScenesObjectsMeshesAttributesMaterialsImagesSavedRigPosesExactExceptAdmittedFields': True,
           'exactScopeSnapshotSHA256': digest(before), 'scopeSnapshots': before,
           'admittedChanged7NativeIDs': changed_ids.tolist(), 'scope320NativeIDsCount': len(scope_ids),
           'samples': samples, 'records': records,
           'limits': ['No save/render/export/GPU or player asset mutation.', 'Triangle geometry uses cross products, never custom RNA polygon normals.',
                      'Finite ten poses only; contacts run separately against these exact compressed evaluated meshes.',
                      'CPU linear skin normal formula remains measured without tolerance relaxation or corner exclusions.',
                      'Original F0 source/protected corner ancestry preservation is a separate pinned reader; this reader compares all body05 native data.']}
(out / 'report.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
print('BODY06_NATIVE_READY', len(records), flush=True)
