"""Prepared v3 exact-saved51 capture; ROOT FROZEN MANIFEST required before use.

Background Blender/CPU2 only. No save/export/render; native-sample serializers
are reused without invoking their semantic motion generator. The original F0
reader runs in this process before candidate controllers are muted in memory.
"""
import argparse
import ast
import gzip
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', required=True)
p.add_argument('--out', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
manifest_path, out = Path(a.manifest).resolve(), Path(a.out).resolve()
assert not out.exists()
manifest = json.loads(manifest_path.read_text())
assert manifest['schema'] == 'rockhop-exact-saved51-native-intake-v1'
assert manifest['rootFrozen'] is True, 'Prepared manifest is not root admission'
assert 'normalizedWeightTolerance' not in manifest and 'normalizedRequiredObjects' not in manifest, 'Inherited raw fields are not globally normalized'
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
def pinned(item):
    path = Path(item['path']).resolve()
    assert sha(path) == item['sha256'], str(path)
    return path

source = pinned(manifest['candidate'])
parent_native = pinned(manifest['parentNative'])
fields_path = pinned(manifest['fields'])
original = pinned(manifest['f0Original'])
contract_path = pinned(manifest['f0Contract'])
scope_receipt = pinned(manifest['candidateScopeReceipt'])
helper = pinned(manifest['f0SnapshotHelper'])
serializer = pinned(manifest['nativeSerializer'])
preservation_reader = pinned(manifest['preservationReader'])
prior_report_path = pinned(manifest['poseAuthorityReport'])
prior_dir = prior_report_path.parent
prior = json.loads(prior_report_path.read_text())
prior_rest_path = pinned({'path': str(prior_dir / prior['rest']['path']),
                          'sha256': prior['rest']['sha256']})
prior_rest = json.loads(gzip.decompress(prior_rest_path.read_bytes()))
selected = [0, 70, 99, 128, 151, 157, 186, 244, 302, 422]
assert manifest['indices'] == selected
sample_pins = {int(pin['path'].split('-')[1].split('.')[0]): pin for pin in prior['samples']}
assert set(selected) <= set(sample_pins)
sample_paths = {index: pinned({'path': str(prior_dir / sample_pins[index]['path']),
                              'sha256': sample_pins[index]['sha256']}) for index in selected}
# Candidate comes first because the existing export checker consumes that pin.
pins = {str(source): sha(source)}
for path in [manifest_path, parent_native, fields_path, original, contract_path, scope_receipt,
             helper, serializer, preservation_reader, prior_report_path,
             prior_rest_path, *sample_paths.values()]:
    pins[str(path)] = sha(path)
out.mkdir(parents=True)

# Reuse the corrected reader, including original34, own51, UV/PBR, raw packed
# protected corners, decoded normals and complete source-corner coverage.
saved_argv = sys.argv[:]
sys.argv = [str(preservation_reader), '--', '--source', str(original),
            '--candidate', str(source), '--contract', str(contract_path),
            '--fields', str(fields_path), '--out', str(out / 'f0-preservation.json')]
try:
    runpy.run_path(str(preservation_reader), run_name='__main__')
finally:
    sys.argv = saved_argv
f0 = json.loads((out / 'f0-preservation.json').read_text())
for key in ['originalObjectsExact', 'original51RigRestWorldScaleExact',
            'copied51RigRestWorldScaleExact', 'originalSavedPoseBasisExact',
            'originalMaterialsExact', 'originalPackedImagesExact']:
    assert f0[key], key
assert f0['readerHelperSHA256'] == sha(helper)
for head in f0['heads'].values():
    for key in ['protectedXYZExact', 'everySourceProtectedCornerOccursExactlyOnce',
                'rawProtectedPackedNormalCornersExact', 'nativeXYZMatchesAuthoredFields']:
        assert head[key], key
    assert head['changedProtectedNormalCorners'] == 0
    assert all(uv['protectedExact'] for uv in head['protectedUVLayers'])

def copied_saved_pose():
    return {bone.name: {'location': list(bone.location),
        'quaternionWXYZ': list(bone.rotation_quaternion), 'scale': list(bone.scale),
        'rotationMode': bone.rotation_mode, 'matrixBasisRows': np.array(bone.matrix_basis).tolist()}
        for bone in bpy.data.objects[manifest['rigName']].pose.bones}

bpy.ops.wm.open_mainfile(filepath=str(parent_native))
bpy.context.window.scene = bpy.data.scenes[manifest['sceneName']]
bpy.context.view_layer.update()
parent_saved_pose = copied_saved_pose()
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.window.scene = bpy.data.scenes[manifest['sceneName']]
bpy.context.view_layer.update()
rig = bpy.data.objects[manifest['rigName']]
names = [bone.name for bone in rig.data.bones]
assert names == prior_rest['jointOrder'] and len(names) == 51
rest = {bone.name: np.array(bone.matrix_local) for bone in rig.data.bones}
rig_world = np.array(rig.matrix_world)
assert rig_world.tolist() == prior_rest['rigWorldRows']
assert {name: rows.tolist() for name, rows in rest.items()} == prior_rest['restBoneRows']
saved_candidate_pose = copied_saved_pose()
assert saved_candidate_pose == parent_saved_pose, 'Copied own51 saved pose changed'
rig.animation_data_clear()
for bone in rig.pose.bones:
    for constraint in bone.constraints:
        constraint.mute = True
rig.hide_viewport = False
rig.hide_set(False)

# Compile only the three existing function definitions. Their module-level
# argparse/open/apply/export code never runs, so no pose is regenerated.
tree = ast.parse(serializer.read_text(), filename=str(serializer))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {'read', 'evaluated', 'save_json'}]
assert {node.name for node in functions} == {'read', 'evaluated', 'save_json'}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(serializer), 'exec'), globals())

def normal_provenance(mesh):
    mesh.calc_loop_triangles()
    attr = mesh.attributes.get('custom_normal')
    packed = None
    if attr:
        assert attr.domain == 'CORNER' and attr.data_type == 'INT16_2D'
        raw = np.empty(len(attr.data) * 2, np.int32)
        attr.data.foreach_get('value', raw)
        packed = raw.reshape(-1, 2).tolist()
    sharp = mesh.attributes.get('sharp_edge')
    return {'customNormalAttribute': None if attr is None else
            {'domain': attr.domain, 'dataType': attr.data_type, 'packed': packed},
            'decodedCornerNormals': [list(row.vector) for row in mesh.corner_normals],
            'triangleLoopTriples': [list(t.loops) for t in mesh.loop_triangles],
            'trianglePolygonIDs': [t.polygon_index for t in mesh.loop_triangles],
            'cornerEdgeIDs': [loop.edge_index for loop in mesh.loops],
            'edges': [list(edge.vertices) for edge in mesh.edges],
            'sharpEdges': [bool(sharp.data[edge.index].value) if sharp else False for edge in mesh.edges],
            'polygons': [{'vertexIDs': list(poly.vertices), 'cornerIDs': list(poly.loop_indices),
                          'smooth': poly.use_smooth} for poly in mesh.polygons],
            'interpretation': 'Fan connectivity inputs, not a global automatic/custom normal solution.'}

parts = []
assert [item['region'] for item in manifest['pairs']] == ['body', 'head', 'boxer', 'cheek']
for item in manifest['pairs']:
    pair = []
    for label in ['full', 'four']:
        obj = bpy.data.objects[item[label]]
        assert obj.name in bpy.context.scene.objects
        obj.animation_data_clear()
        obj.hide_viewport = False
        obj.hide_set(False)
        pair.append(read(obj))
    full, four = pair
    for key in ['xyz', 'faces', 'objectWorld', 'cornerVertices', 'cornerNormals']:
        assert np.array_equal(full[key], four[key]), (item['region'], key)
    assert np.max((four['weights'] > 0).sum(axis=1)) <= 4
    parts.append((item, full, four))

rest_report = {'jointOrder': names, 'rigWorldRows': rig_world.tolist(),
    'restBoneRows': {name: value.tolist() for name, value in rest.items()},
    'jointHierarchy': [{'name': bone.name, 'parent': bone.parent.name if bone.parent else None,
                        'deform': bone.use_deform} for bone in rig.data.bones],
    'candidateSavedPoseBeforeControllerMute': saved_candidate_pose, 'parts': {}}
fields = np.load(fields_path)
for item, full, four in parts:
    region = item['region']
    row = {key: full[key].tolist() for key in
           ['xyz', 'faces', 'objectWorld', 'cornerNormals', 'cornerVertices']}
    row.update(fullWeights=full['weights'].tolist(), fourWeights=four['weights'].tolist(),
               fullRawWeights=full['rawWeights'].tolist(), fourRawWeights=four['rawWeights'].tolist(),
               fullRawSumRange=[float(full['weightSums'].min()), float(full['weightSums'].max())],
               fourRawSumRange=[float(four['weightSums'].min()), float(four['weightSums'].max())],
               auxiliaryMembershipCounts={kind: field['auxiliaryMembershipCounts']
                                          for kind, field in [('full', full), ('four', four)]},
               normalProvenance={kind: normal_provenance(field['object'].data)
                                 for kind, field in [('full', full), ('four', four)]})
    row['rawAllMemberships'] = {kind: {'groupNames': [group.name for group in field['object'].vertex_groups],
        'vertices': [[(group.group, group.weight) for group in vertex.groups]
                     for vertex in field['object'].data.vertices]}
        for kind, field in [('full', full), ('four', four)]}
    # Preserve the actual authored ancestry arrays rather than infer coordinates.
    row['authoredFieldArrays'] = {key: fields[key].tolist() for key in fields.files
        if key.startswith(region) and any(term in key for term in
            ['Source', 'Ancestry', 'AttributeEdge', 'UnusedNative', 'SeamPhysical'])}
    row['usedNativeVertexIDs'] = np.unique(full['faces']).tolist()
    rest_report['parts'][region] = row
rest_pin = save_json('rest.json.gz', rest_report)
records, samples = [], []
for index in selected:
    old = json.loads(gzip.decompress(sample_paths[index].read_bytes()))
    assert old['index'] == index and list(old['poseBasisBlender']) == names
    for name in names:
        bone, basis = rig.pose.bones[name], old['poseBasisBlender'][name]
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)
        bone.location, bone.rotation_quaternion, bone.scale = basis['location'], basis['quaternionWXYZ'], basis['scale']
    bpy.context.view_layer.update()
    actual_basis = {name: {'location': list(rig.pose.bones[name].location),
        'quaternionWXYZ': list(rig.pose.bones[name].rotation_quaternion),
        'scale': list(rig.pose.bones[name].scale)} for name in names}
    assert actual_basis == old['poseBasisBlender']
    skin = np.array([rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted() for name in names])
    worlds = {name: np.array(rig.matrix_world @ rig.pose.bones[name].matrix).tolist() for name in names}
    assert np.array_equal(skin, np.array(old['skinNativeRows']))
    assert worlds == old['boneWorldNativeRows']
    row = {key: old[key] for key in ['index', 'case', 'phase', 'timeS']}
    row.update(poseBasisBlender=actual_basis, skinNativeRows=skin.tolist(),
               boneWorldNativeRows=worlds, parts={})
    record = {'index': index, 'posePayloadExact': True, 'skinAndBoneWorldExact': True, 'parts': {}}
    for item, full, four in parts:
        region = item['region']
        for kind, field in [('full', full), ('four', four)]:
            xyz, normals, faces = evaluated(field['object'])
            assert len(xyz) == len(field['xyz']) and np.isfinite(xyz).all() and np.isfinite(normals).all()
            topology = bool(np.array_equal(faces, field['faces']))
            if region in ['head', 'body']:
                assert topology, ('Changed frozen head/body triangulation', index, region, kind)
            evaluated_obj = field['object'].evaluated_get(bpy.context.evaluated_depsgraph_get())
            evaluated_mesh = evaluated_obj.to_mesh()
            evaluated_mesh.calc_loop_triangles()
            corner_vertices = np.array([loop.vertex_index for loop in evaluated_mesh.loops])
            triangle_loops = [list(triangle.loops) for triangle in evaluated_mesh.loop_triangles]
            polygon_ids = [triangle.polygon_index for triangle in evaluated_mesh.loop_triangles]
            evaluated_obj.to_mesh_clear()
            assert np.array_equal(corner_vertices, field['cornerVertices'])
            assert len(normals) == len(corner_vertices)
            assert np.array_equal(corner_vertices[np.array(triangle_loops)], faces)
            triangle_corner_exact = triangle_loops == rest_report['parts'][region]['normalProvenance'][kind]['triangleLoopTriples']
            if region in ['head', 'body']:
                assert triangle_corner_exact, ('Changed frozen head/body triangle corners', index, region, kind)
            row['parts'].setdefault(region, {})[kind] = {'xyzWorld': xyz.tolist(),
                'normalWorldCorners': normals.tolist(), 'faces': faces.tolist(),
                'cornerVertices': corner_vertices.tolist(), 'triangleLoopTriples': triangle_loops,
                'trianglePolygonIDs': polygon_ids}
            rig_inverse = np.linalg.inv(rig_world)
            rest_homogeneous = np.c_[field['xyz'], np.ones(len(field['xyz']))]
            for label, values in [('rigWorld', rig_world), ('rigInverse', rig_inverse),
                                  ('objectWorld', field['objectWorld']), ('restHomogeneous', rest_homogeneous),
                                  ('skinNativeRows', skin)]:
                assert np.isfinite(values).all(), (index, region, kind, label)
            to_rig = np.einsum('ab,bc->ac', rig_inverse, field['objectWorld'], optimize=False)
            assert np.isfinite(to_rig).all(), (index, region, kind, 'toRig')
            homogeneous = np.einsum('va,ba->vb', rest_homogeneous, to_rig, optimize=False)
            assert np.isfinite(homogeneous).all(), (index, region, kind, 'rigHomogeneous')
            residuals = {}
            for hypothesis, weights in [('normalized', field['weights']), ('raw', field['rawWeights'])]:
                assert np.isfinite(weights).all(), (index, region, kind, hypothesis, 'weights')
                predicted_rig = np.einsum('vj,jab,vb->va', weights, skin, homogeneous, optimize=False)
                assert np.isfinite(predicted_rig).all(), (index, region, kind, hypothesis, 'weightedLBS')
                predicted_world = np.einsum('va,ba->vb', predicted_rig, rig_world, optimize=False)
                assert np.isfinite(predicted_world).all(), (index, region, kind, hypothesis, 'worldLBS')
                predicted = predicted_world[:, :3]
                residuals[hypothesis + 'ManualNativeMaxM'] = float(np.linalg.norm(predicted - xyz, axis=1).max())
            record['parts'].setdefault(region, {})[kind] = {'topologyExact': topology,
                'triangleCornerTriplesExact': triangle_corner_exact, 'cornerVertexIdentityExact': True,
                'topologyStatus': 'EXACT_AT_SAVED_POSE' if topology and triangle_corner_exact else 'FAILED_EVALUATED_TRIANGULATION_STABILITY_ACTUAL_TRIPLES_RETAINED',
                'rawSumMinimum': float(field['weightSums'].min()), 'rawSumMaximum': float(field['weightSums'].max()),
                'maximumRawSumResidual': float(np.max(np.abs(field['weightSums'] - 1))),
                **residuals, 'zeroNormalCornerIDs': np.flatnonzero(np.linalg.norm(normals, axis=1) == 0).tolist()}
        delta = np.array(row['parts'][region]['full']['xyzWorld']) - np.array(row['parts'][region]['four']['xyzWorld'])
        record['parts'][region]['maximumFullFourPositionDifferenceM'] = float(np.linalg.norm(delta, axis=1).max())
    samples.append(save_json('sample-%04d.json.gz' % index, row))
    records.append(record)
    print('EXACT_SAVED51_SAMPLE', index, flush=True)
assert pins == {path: sha(path) for path in pins}
assert all(np.array_equal(rest[name], np.array(rig.data.bones[name].matrix_local)) for name in names)
assert np.array_equal(rig_world, np.array(rig.matrix_world))
save_json('report.json', {'status': 'UNACCEPTED_EXACT_SAVED51_NATIVE_CAPTURE',
    'sourcePins': pins, 'recipeSHA256': sha(__file__), 'blender': bpy.app.version_string,
    'rest': rest_pin, 'samples': samples, 'records': records,
    'f0Preservation': {'path': 'f0-preservation.json', 'sha256': sha(out / 'f0-preservation.json')},
    'candidateScopeReceipt': {'path': str(scope_receipt), 'sha256': sha(scope_receipt)},
    'limits': ['Ten exact saved native poses; no regenerated motion or native save/export/render.',
        'Boxer inherited n-gon retessellation is recorded as failed stability with actual triangles/corner triples retained; no dropped partner, waiver or promotion.',
        'Frozen head/body triangles and triangle-corner triples must remain exact; all region corner->point identities remain exact.',
        'Pinned candidate scope receipt remains separately reviewed authority; this capture does not invent an admitted mask.',
        'All raw FULL and authored FOUR fields retained; no normalization rewrite.',
        'Inherited raw FOUR outside the admitted author field is not claimed globally normalized; normalized and raw manual hypotheses are separately measured. Shipping-normalized FOUR remains open.',
        'Fan/packed inputs are provenance, not a general Blender moving-normal solution.',
        'No shader/GPU, played-art, contact, support, LOD, device or promotion pass.']})
print('EXACT_SAVED51_NATIVE_READY', len(samples), flush=True)
