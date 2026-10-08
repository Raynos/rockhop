"""Topology-aware construction intake; reuse the strict selected native75 exporter.

Parent CPU2 only: blender -b -t 2 --python-exit-code 1 --python export.py -- INPUT FRESH_OUT
No remask, runtime change, normal-player write or inherited topology fingerprint waiver.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[4]
EDITED = {'RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}


def attributes(mesh, np):
    formats = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32),
               'BOOLEAN': ('value', 1, np.bool_), 'FLOAT_VECTOR': ('vector', 3, np.float32),
               'FLOAT2': ('vector', 2, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32),
               'BYTE_COLOR': ('color', 4, np.float32), 'INT8': ('value', 1, np.int32),
               'QUATERNION': ('value', 4, np.float32), 'FLOAT4X4': ('value', 16, np.float32),
               'INT32_2D': ('value', 2, np.int32), 'INT16_2D': ('value', 2, np.int16)}
    excluded = {'position', '_NATIVE_ID', '.corner_vert', '.corner_edge', '.edge_verts'} | {layer.name for layer in mesh.uv_layers}
    result = {}
    for attr in mesh.attributes:
        if attr.name in excluded or attr.name.startswith('.select_'): continue
        assert attr.domain in {'POINT', 'EDGE', 'FACE', 'CORNER'} and attr.data_type in formats
        field, width, dtype = formats[attr.data_type]
        values = np.empty(len(attr.data)*width, dtype=dtype); attr.data.foreach_get(field, values)
        result[attr.name] = {'domain': attr.domain, 'type': attr.data_type, 'values': values.reshape(-1, width)}
    return result


def material_state(obj, exporter):
    """Exact selected graph, packed image bytes and settings, independent of mesh topology."""
    scalar = exporter['scalar_rna']
    result = []
    for material in obj.data.materials:
        assert material and material.use_nodes
        nodes = []
        for node in material.node_tree.nodes:
            row = {'name': node.name, 'type': node.bl_idname, 'settings': scalar(node),
                   'inputs': [[socket.identifier, socket.type, scalar(socket).get('default_value')]
                              for socket in node.inputs]}
            if node.type == 'TEX_IMAGE' and node.image:
                image = node.image
                assert image.packed_file, ('Unpacked selected image', image.name)
                row['image'] = [image.name, list(image.size), image.colorspace_settings.name,
                                image.alpha_mode, hashlib.sha256(image.packed_file.data).hexdigest()]
            nodes.append(row)
        result.append({'name': material.name, 'settings': scalar(material), 'nodes': nodes,
                       'links': [[link.from_node.name, link.from_socket.identifier,
                                  link.to_node.name, link.to_socket.identifier]
                                 for link in material.node_tree.links]})
    return result


def snapshot(obj, helper, exporter):
    np = helper['np']; mesh = obj.data
    mesh.calc_loop_triangles()
    positions = np.empty(len(mesh.vertices)*3, dtype=np.float32)
    mesh.vertices.foreach_get('co', positions)
    triangles = np.array([list(face.vertices) for face in mesh.loop_triangles], dtype=np.int32)
    corners = np.array([list(face.loops) for face in mesh.loop_triangles], dtype=np.int32)
    edges = np.empty(len(mesh.edges)*2, dtype=np.int32); mesh.edges.foreach_get('vertices', edges)
    normals = np.empty(len(mesh.loops)*3, dtype=np.float32); mesh.corner_normals.foreach_get('vector', normals)
    polygons = [mesh.polygons[face.polygon_index] for face in mesh.loop_triangles]
    uv = {}
    for layer in mesh.uv_layers:
        values = np.empty(len(mesh.loops)*2, dtype=np.float32)
        layer.data.foreach_get('uv', values)
        uv[layer.name] = values.reshape(-1, 2).copy()
    return {'positions': positions.reshape(-1, 3), 'triangles': triangles, 'corners': corners,
            'material': np.array([face.material_index for face in polygons]),
            'smooth': np.array([face.use_smooth for face in polygons]), 'uv': uv,
            'cornerNormals': normals.reshape(-1, 3), 'attributes': attributes(mesh, np),
            'edges': edges.reshape(-1, 2), 'trianglePolygons': np.array([face.polygon_index for face in mesh.loop_triangles]),
            'uvSelection': [(layer.name, layer.active_render, layer.active_clone) for layer in mesh.uv_layers],
            'fields': helper['mesh_four'](obj, bpy.data.objects['RiderSkeleton'], require_four=False),
            'materials': material_state(obj, exporter)}


def validate_ancestry(obj, before, row, helper, exporter):
    """Check declared local reconstruction against actual source arrays and native fields."""
    np = helper['np']; after = snapshot(obj, helper, exporter)
    data = np.load(helper['pin'](row['ancestry']), allow_pickle=False)
    ids = data['vertexSourceIds']; parents = data['vertexParentSourceIds']; blend = data['vertexParentCoefficients']
    face_ids = data['faceSourceIds']; corner_ids = data['cornerSourceIds']
    vertex_roles = data['authoredVertexRoles']; face_roles = data['authoredFaceRoles']
    count = len(before['positions']); total = len(after['positions'])
    assert ids.shape == vertex_roles.shape == (total,) and parents.shape == blend.shape == (total, 3)
    assert np.array_equal(ids[:count], np.arange(count)) and np.all(ids[count:] == -1), 'Preserved source vertex prefix required'
    assert np.isin(vertex_roles[:count], [0, 1]).all() and np.isin(vertex_roles[count:], [2, 3]).all()
    assert face_ids.shape == face_roles.shape == (len(after['triangles']),)
    assert corner_ids.shape == after['corners'].shape
    assert np.isin(face_roles, [0, 1, 2]).all() and np.isfinite(after['positions']).all()
    affected_vertices = data['affectedSourceVertices']; affected_faces = data['affectedSourceFaces']; affected_corners = data['affectedSourceCorners']
    for values, maximum in [(affected_vertices, count), (affected_faces, len(before['triangles'])),
                            (affected_corners, next(iter(before['uv'].values())).shape[0])]:
        assert np.issubdtype(values.dtype, np.integer) and np.all((values >= 0) & (values < maximum))
        assert len(np.unique(values)) == len(values)
    unchanged = np.flatnonzero(vertex_roles == 0)
    assert np.array_equal(after['positions'][unchanged], before['positions'][ids[unchanged]])
    assert np.isin(np.flatnonzero(vertex_roles[:count] == 1), affected_vertices).all()
    maximum_field_residual = 0.
    for index, actual in enumerate(after['fields']):
        if vertex_roles[index] == 0:
            assert dict(actual) == dict(before['fields'][int(ids[index])]), ('Retained native fields changed', obj.name, index)
            continue
        valid = blend[index] > 0
        assert np.isfinite(blend[index]).all() and np.all(blend[index] >= 0) and valid.any()
        assert abs(float(blend[index].sum())-1) < 2e-5
        source_ids = parents[index][valid]
        assert np.issubdtype(source_ids.dtype, np.integer) and np.isin(source_ids, affected_vertices).all()
        expected = {}
        for source, coefficient in zip(source_ids, blend[index][valid]):
            for name, weight in before['fields'][int(source)]:
                expected[name] = expected.get(name, 0.) + float(coefficient)*weight
        expected = dict(sorted(expected.items(), key=lambda item: (-item[1], item[0]))[:4])
        mass = sum(expected.values()); expected = {name: weight/mass for name, weight in expected.items()}
        actual = dict(actual)
        residual = max(abs(actual.get(name, 0)-expected.get(name, 0)) for name in actual.keys() | expected.keys())
        maximum_field_residual = max(maximum_field_residual, residual)
    # Same named-weight transport tolerance used by the unchanged decoded FOUR finalizer.
    assert maximum_field_residual < 2e-5, ('Authored field ancestry mismatch', obj.name, maximum_field_residual)
    retained = face_roles == 0; clipped = face_roles == 1; lining = face_roles == 2
    assert np.all((face_ids[retained | clipped] >= 0) & (face_ids[retained | clipped] < len(before['triangles'])))
    assert np.all(face_ids[lining] == -1) and np.isin(face_ids[clipped], affected_faces).all()
    retained_source = face_ids[retained]
    assert len(np.unique(retained_source)) == len(retained_source)
    removed = np.setdiff1d(np.arange(len(before['triangles'])), face_ids[face_ids >= 0])
    assert np.isin(removed, affected_faces).all(), 'Undeclared source surface deletion'
    assert np.array_equal(ids[after['triangles'][retained]], before['triangles'][retained_source])
    assert np.array_equal(corner_ids[retained], before['corners'][retained_source])
    assert np.array_equal(after['material'][retained], before['material'][retained_source])
    assert np.array_equal(after['smooth'][retained], before['smooth'][retained_source])
    assert np.array_equal(after['material'][retained | clipped], before['material'][face_ids[retained | clipped]])
    assert after['uvSelection'] == before['uvSelection'] and after['materials'] == before['materials']
    retained_corners = corner_ids[retained].reshape(-1)
    immutable = ~np.isin(retained_corners, affected_corners)
    actual_corners = after['corners'][retained].reshape(-1)
    assert row.get('localRecompute'), 'Declare local normal/attribute reconstruction scope'
    assert np.array_equal(after['cornerNormals'][actual_corners[immutable]], before['cornerNormals'][retained_corners[immutable]]), 'Undeclared retained normal change'
    protected_points = np.setdiff1d(np.arange(count), affected_vertices)
    edge_ids = ids[after['edges']]
    source_edge_rows = {tuple(sorted(edge)): index for index, edge in enumerate(before['edges'])}
    actual_edge_rows = {tuple(sorted(edge_ids[index])): index for index in np.flatnonzero(np.all(edge_ids >= 0, axis=1))}
    protected_edge_indices = np.flatnonzero(~np.isin(before['edges'], affected_vertices).any(axis=1))
    protected_edges = [tuple(sorted(before['edges'][index])) for index in protected_edge_indices]
    assert all(key in actual_edge_rows for key in protected_edges), 'Undeclared retained edge deletion'
    for name, original in before['attributes'].items():
        actual = after['attributes'][name]
        assert actual['domain'] == original['domain'] and actual['type'] == original['type']
        domain = original['domain']; a, b = actual['values'], original['values']
        if domain == 'POINT': a, b = a[protected_points], b[protected_points]
        elif domain == 'CORNER': a, b = a[actual_corners[immutable]], b[retained_corners[immutable]]
        elif domain == 'FACE':
            outside = ~np.isin(retained_source, affected_faces)
            a = a[after['trianglePolygons'][retained][outside]]
            b = b[before['trianglePolygons'][retained_source[outside]]]
        else:
            a = a[[actual_edge_rows[key] for key in protected_edges]]
            b = b[[source_edge_rows[key] for key in protected_edges]]
        assert np.array_equal(a, b), ('Undeclared retained attribute change', obj.name, name)
    for name, values in after['uv'].items():
        assert np.isfinite(values).all()
        assert np.array_equal(values[actual_corners[immutable]], before['uv'][name][retained_corners[immutable]])
    maximum_clipped_uv_residual = 0.
    for face_index in np.flatnonzero(clipped):
        source_index = int(face_ids[face_index]); source_vertices = before['triangles'][source_index]
        source_corners = before['corners'][source_index]
        for corner, vertex in enumerate(after['triangles'][face_index]):
            if ids[vertex] >= 0:
                parent_ids, coefficients = np.array([ids[vertex]]), np.array([1.], dtype=np.float32)
            else:
                valid = blend[vertex] > 0; parent_ids, coefficients = parents[vertex][valid], blend[vertex][valid]
            assert np.isin(parent_ids, source_vertices).all(), ('Clipped triangle does not contain claimed parents', obj.name, face_index)
            source_slots = np.array([int(np.flatnonzero(source_vertices == identity)[0]) for identity in parent_ids])
            claimed_corner = int(corner_ids[face_index, corner])
            if claimed_corner >= 0:
                assert len(parent_ids) == 1 and claimed_corner == source_corners[source_slots[0]]
            actual_corner = after['corners'][face_index, corner]
            for name, values in after['uv'].items():
                source_uv = before['uv'][name][source_corners[source_slots]].astype(float)
                expected = coefficients.astype(float) @ source_uv; actual = values[actual_corner]
                residual = abs(actual.astype(float)-expected)
                # Bound only coefficient/final UV float32 rounding plus double arithmetic.
                bound = .5*(abs(np.spacing(coefficients)).astype(float) @ abs(source_uv))
                bound += .5*abs(np.spacing(actual)).astype(float) + 8*np.finfo(float).eps*np.maximum(1., abs(source_uv).sum(0))
                assert np.all(residual <= bound), ('Clipped source UV ancestry mismatch', obj.name, face_index, name, residual, bound)
                maximum_clipped_uv_residual = max(maximum_clipped_uv_residual, float(residual.max()))
    return {'ancestry': row['ancestry'], 'sourceVertices': count, 'authoredVertices': total,
            'retainedTriangles': int(retained.sum()), 'clippedTriangles': int(clipped.sum()),
            'newLiningTriangles': int(lining.sum()), 'removedSourceTriangles': len(removed),
            'maximumNamedFieldAncestryResidual': maximum_field_residual,
            'maximumClippedCornerUVResidual': maximum_clipped_uv_residual,
            'retainedOutsideLocalScopeNormalsAndAttributesExact': True, 'localRecompute': row['localRecompute'],
            'newLiningUVs': 'Explicit local authored UVs; distinct from clipped-source interpolation',
            'selectedMaterialGraphsAndPackedImagesExact': True, 'undeclaredCheckedArrayChanges': False,
            'limits': 'Declared local geometry/UV/fields may change; source lineage is not geometric or moving-art acceptance.'}


def scene_state(helper, exporter, contract):
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.animation_data is None and rig.matrix_world.is_identity
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert exporter['native_rest'](rig) == contract['nativeRest']['bones']
    visible = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render]
    assert len(visible) == 7 and {obj.name for obj in visible} == helper['EXPECTED']
    reference = bpy.data.objects['RiderBody__FullAnatomyReference']
    assert reference.hide_render and bpy.data.objects['RiderBody']['outfitFullBodyReference'] == reference.name
    for obj in visible:
        assert obj.matrix_world.is_identity and not obj.data.shape_keys and obj.animation_data is None
        arms = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
        assert len(arms) == 1 and arms[0].object == rig and not arms[0].use_deform_preserve_volume
        assert all(mod.type in {'ARMATURE', 'TRIANGULATE'} for mod in obj.modifiers)
    protected = {obj.name: exporter['part_fingerprint'](obj, helper)
                 for obj in visible+[reference] if obj.name not in EDITED}
    return rig, visible, protected


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    manifest_path, out = (Path(value).resolve() for value in args)
    manifest = json.loads(manifest_path.read_text())
    assert manifest['accepted'] is False and manifest['ready'] is True and manifest['alreadyMasked'] is True
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-construction-engine12') and not out.exists()
    def recipe(row):
        path = ROOT/row['path']; assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']; return runpy.run_path(str(path))
    helper = recipe(manifest['mergeHelper']); exporter = recipe(manifest['exportHelper'])
    pin = helper['pin']
    for row in helper['pins'](manifest): pin(row)
    parent = json.loads(pin(manifest['parentExportReceipt']).read_text())
    construction = json.loads(pin(manifest['constructionReceipt']).read_text())
    calibration = json.loads(pin(manifest['baseCalibration']).read_text())
    contract = json.loads(pin(manifest['baseContract']).read_text())
    assert parent['native'] == manifest['parentNative'] == construction['sourceMaster']
    assert parent['rigAndContractExactNative75'] and parent['decodedFourQualification']['decodedSourceFOURMatchesSavedNative']
    assert parent['glb']['sha256'] == contract['glbSHA256']
    assert calibration['sourceSHA256'] == parent['glb']['sha256']
    assert construction['native'] == manifest['native'] and construction['exact75RestUnchanged'] is True
    assert construction['acceptedArt'] is False and construction['visibleMeshes'] == sorted(helper['EXPECTED'])
    assert set(construction['objects']) == EDITED
    parent_dir = pin(manifest['parentExportReceipt']).parent
    assert pin(manifest['baseContract']).parent == parent_dir
    assert pin(manifest['bodyMaskManifest']) == parent_dir/'body-mask-manifest.json'
    assert pin(manifest['bodyMaskReceipt']) == parent_dir/parent['bodyMaskReceipt']
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['parentNative'])))
    _, _, before = scene_state(helper, exporter, contract)
    source = {name: snapshot(bpy.data.objects[name], helper, exporter) for name in EDITED}
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['native'])))
    rig, meshes, after = scene_state(helper, exporter, contract)
    assert before == after, ('Protected other four meshes/full anatomy changed', [name for name in before if before[name] != after[name]])
    ancestry = {name: validate_ancestry(bpy.data.objects[name], source[name], construction['objects'][name], helper, exporter) for name in sorted(EDITED)}
    conditioning = []
    for obj in meshes:
        if obj.name in EDITED:
            obj.data = obj.data.copy()  # Fresh delivery mesh only; authored input native remains immutable.
            rows = helper['mesh_four'](obj, rig, require_four=False)
            four = helper['limit_four'](obj, rig) if any(len(row) > 4 for row in rows) else {
                'method': 'Authored native FOUR retained without writes', 'changedRows': 0}
            cutoff = exporter['export_cutoff'](obj, rig, helper)
            old = obj.data.attributes.get('_NATIVE_ID')
            if old: obj.data.attributes.remove(old)
            attribute = obj.data.attributes.new('_NATIVE_ID', 'INT', 'POINT')
            attribute.data.foreach_set('value', list(range(len(obj.data.vertices))))
            conditioning.append({'object': obj.name, 'four': four, 'cutoff': cutoff, 'deliveryIDsRegenerated': True})
        else:
            helper['mesh_four'](obj, rig)
            conditioning.append({'object': obj.name, 'changedRows': 0, 'method': 'Exact existing protected delivery fields'})
    qualification = {'method': 'Explicit local topology construction ancestry; independent exact protected parity',
                     'constructorReceipt': manifest['constructionReceipt'], 'objects': ancestry,
                     'protectedNativeFingerprints': after, 'otherVisibleMeshesExactCount': 4,
                     'fullAnatomyReferenceExact': True, 'bodyMaskAppliedAgain': False,
                     'allSevenTopologyUVPBRAndDeliveryFieldsExact': False,
                     'editedTopologyUVAndNewFieldsExplicitlyAuthored': True}
    exporter['finalize'](manifest, manifest_path, out, helper, rig, meshes, contract,
                         json.loads(pin(manifest['bodyMaskManifest']).read_text()),
                         json.loads(pin(manifest['bodyMaskReceipt']).read_text()),
                         {'method': 'Existing masked body and full reference exact; no conditioning'}, conditioning, qualification)
    # The action transporter consumes the actual exported GLB identity, not a donor hash.
    path = out/'rider-contract.json'; saved = json.loads(path.read_text())
    saved['sourceSHA256'] = saved['glbSHA256']
    path.write_text(json.dumps(saved, indent=2)+'\n')
    old_driver = json.dumps(calibration['driver'], sort_keys=True)
    calibration['sourceSHA256'] = saved['glbSHA256']
    calibration['calibration']['constructionIntake'] = {
        'previousCalibration': manifest['baseCalibration'], 'constructorReceipt': manifest['constructionReceipt'],
        'protectedBootsFullAnatomyAndNative75RestExact': True, 'editedObjects': sorted(EDITED),
        'allPreviousDriverNumericsExact': True, 'gloveBarSurfaceQualification': 'UNQUALIFIED',
        'sourceSHA256Meaning': 'Actual new exported GLB; original sole/source ancestry remains separately pinned.'}
    assert json.dumps(calibration['driver'], sort_keys=True) == old_driver
    calibration_path = out/'rider-calibration.json'
    calibration_path.write_text(json.dumps(calibration, indent=2)+'\n')
    path = out/'export.json'; receipt = json.loads(path.read_text())
    receipt['constructionIntakeRecipeSHA256'] = helper['sha'](__file__)
    receipt['actualContract'] = {'path': str((out/'rider-contract.json').relative_to(ROOT)), 'sha256': helper['sha'](out/'rider-contract.json')}
    receipt['actualCalibration'] = {'path': str(calibration_path.relative_to(ROOT)), 'sha256': helper['sha'](calibration_path)}
    receipt['contractSourceSHA256Meaning'] = 'Alias of actual exported GLB SHA; original selected source ancestry remains separately pinned.'
    path.write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__': main()
