"""Mask/export the saved complete selected native for private actual-game review.

Parent CPU2 only, after source checkpoint and moving shape judgment.
blender -b -t 2 --python-exit-code 1 --python export-private.py -- MANIFEST FRESH_OUT
Normal player models/catalogs are never written.
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[4]


def export_cutoff(obj, rig, helper):
    """Match Blender 5.2.1's fixed glTF cutoff on delivery copies only."""
    rows = helper['mesh_four'](obj, rig)
    groups = {g.name: g for g in obj.vertex_groups}
    changed, maximum_loss = 0, 0.
    for index, row in enumerate(rows):
        kept = [(name, weight) for name, weight in row if weight > .0001]
        if len(kept) == len(row): continue
        assert kept
        changed += 1
        maximum_loss = max(maximum_loss, sum(w for _, w in row if w <= .0001))
        total = sum(w for _, w in kept)
        for name, _ in row: groups[name].remove([index])
        for name, weight in kept: groups[name].add([index], weight/total, 'REPLACE')
    assert all(weight > .0001 for row in helper['mesh_four'](obj, rig) for _, weight in row)
    return {'object': obj.name, 'cutoff': .0001, 'changedRows': changed,
            'maximumRemovedMass': maximum_loss,
            'method': 'Mirror installed glTF fixed cutoff then normalize before native save/export'}


def four_readback(document, raw, meshes, helper):
    """Compare actual decoded material-primitive fields with saved native FOUR."""
    np = helper['np']
    json_size = struct.unpack_from('<I', raw, 12)[0]
    binary = memoryview(raw)[28+json_size:]
    types = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    def accessor(identity):
        row = document['accessors'][identity]; view = document['bufferViews'][row['bufferView']]
        assert not row.get('sparse') and view['buffer'] == 0
        width = {'SCALAR': 1, 'VEC4': 4}[row['type']]
        dtype = np.dtype(types[row['componentType']])
        values = np.ndarray((row['count'], width), dtype=dtype, buffer=binary,
            offset=view.get('byteOffset', 0)+row.get('byteOffset', 0),
            strides=(view.get('byteStride', width*dtype.itemsize), dtype.itemsize))
        if row.get('normalized'):
            assert dtype.kind == 'u'; return values.astype(float)/np.iinfo(dtype).max
        return values
    joints = [document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    by_name = {obj.name: obj for obj in meshes}
    results = []
    for node in document['nodes']:
        if 'mesh' not in node: continue
        obj = by_name[node['name']]
        native = helper['mesh_four'](obj, bpy.data.objects['RiderSkeleton'])
        seen, maximum, count = set(), 0., 0
        for primitive in document['meshes'][node['mesh']]['primitives']:
            attributes = primitive['attributes']
            assert 'WEIGHTS_1' not in attributes and 'JOINTS_1' not in attributes
            ids = accessor(attributes['_NATIVE_ID']).reshape(-1)
            palettes, weights = accessor(attributes['JOINTS_0']), accessor(attributes['WEIGHTS_0'])
            assert len(ids) == len(palettes) == len(weights)
            assert np.isfinite(weights).all() and np.min(weights) >= 0
            assert np.max(abs(weights.sum(1)-1)) < 2e-5
            for identity, palette, row in zip(ids, palettes, weights):
                index = int(identity); assert identity == index and 0 <= index < len(native)
                seen.add(index); count += 1
                actual = {}
                for joint, weight in zip(palette, row):
                    if weight > 0: actual[joints[int(joint)]] = actual.get(joints[int(joint)], 0.)+float(weight)
                wanted = dict(native[index])
                maximum = max(maximum, max(abs(actual.get(name, 0)-wanted.get(name, 0)) for name in actual.keys()|wanted.keys()))
        assert seen == {i for polygon in obj.data.polygons for i in polygon.vertices}
        assert maximum < 2e-5, ('Decoded source FOUR mismatch', obj.name, maximum)
        results.append({'object': obj.name, 'decodedPrimitiveRows': count,
                        'nativeSurfaceVertexIDs': len(seen), 'maximumNamedWeightResidual': maximum,
                        'maximumNativePositiveInfluences': max(map(len, native))})
    return {'decodedSourceFOURMatchesSavedNative': True, 'objects': results,
            'limits': 'Source transport fields only; native-vs-actual-GPU moving parity remains open.'}


def native_rest(rig):
    return [{'name': b.name, 'parent': b.parent.name if b.parent else None,
             'head': list(b.head_local), 'tail': list(b.tail_local),
             'matrix': [list(row) for row in b.matrix_local],
             'useConnect': b.use_connect, 'useDeform': b.use_deform} for b in rig.data.bones]


def scalar_rna(value):
    """Transport-relevant scalar RNA; datablock pointers are named separately."""
    result = {}
    for prop in value.bl_rna.properties:
        if prop.identifier == 'rna_type' or prop.is_readonly: continue
        if prop.type not in {'BOOLEAN', 'INT', 'FLOAT', 'ENUM', 'STRING'}: continue
        item = getattr(value, prop.identifier)
        result[prop.identifier] = sorted(item) if isinstance(item, set) else list(item) if getattr(prop, 'is_array', False) else item
    return result


def part_fingerprint(obj, helper, allow_positions=False):
    """Hash actual native data, independent of the correcting builder's receipt."""
    np = helper['np']; mesh = obj.data
    assert obj.type == 'MESH' and not mesh.shape_keys and obj.animation_data is None
    digest = hashlib.sha256()
    def array(label, collection, property_name, width, dtype):
        values = np.empty(len(collection)*width, dtype=dtype)
        collection.foreach_get(property_name, values)
        digest.update(label.encode()); digest.update(values.tobytes())
    if not allow_positions: array('positions', mesh.vertices, 'co', 3, np.float32)
    for label, collection, prop, width, dtype in [
        ('edgeVertices', mesh.edges, 'vertices', 2, np.int32),
        ('cornerVertices', mesh.loops, 'vertex_index', 1, np.int32),
        ('polygonStart', mesh.polygons, 'loop_start', 1, np.int32),
        ('polygonSizes', mesh.polygons, 'loop_total', 1, np.int32),
        ('polygonMaterial', mesh.polygons, 'material_index', 1, np.int32),
        ('polygonSmooth', mesh.polygons, 'use_smooth', 1, np.bool_)]:
        array(label, collection, prop, width, dtype)
    formats = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32),
               'BOOLEAN': ('value', 1, np.bool_), 'FLOAT_VECTOR': ('vector', 3, np.float32),
               'FLOAT2': ('vector', 2, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32),
               'BYTE_COLOR': ('color', 4, np.float32), 'INT8': ('value', 1, np.int32),
               'QUATERNION': ('value', 4, np.float32), 'FLOAT4X4': ('value', 16, np.float32),
               'INT32_2D': ('value', 2, np.int32),
               'INT16_2D': ('value', 2, np.int16)}
    for attr in mesh.attributes:
        if allow_positions and attr.name == 'position': continue
        assert attr.data_type in formats, ('Unsupported immutable attribute', obj.name, attr.name, attr.data_type)
        digest.update(json.dumps([attr.name, attr.domain, attr.data_type]).encode())
        field, width, dtype = formats[attr.data_type]
        array('attribute', attr.data, field, width, dtype)
    # Preserve exact UV layers and their active selection, including legacy UV RNA.
    for uv in mesh.uv_layers:
        digest.update(json.dumps([uv.name, uv.active_render, uv.active_clone]).encode())
        array('uv', uv.data, 'uv', 2, np.float32)
    if not allow_positions:
        array('evaluatedCornerNormals', mesh.corner_normals, 'vector', 3, np.float32)
    digest.update(json.dumps([g.name for g in obj.vertex_groups]).encode())
    for vertex in mesh.vertices:
        digest.update(struct.pack('<I', len(vertex.groups)))
        for group in vertex.groups: digest.update(struct.pack('<If', group.group, group.weight))
    materials = []
    for mat in mesh.materials:
        assert mat and mat.use_nodes
        nodes = []
        for node in mat.node_tree.nodes:
            row = {'name': node.name, 'type': node.bl_idname, 'settings': scalar_rna(node),
                   'inputs': [{'identifier': socket.identifier, 'type': socket.type,
                               'default': scalar_rna(socket).get('default_value')} for socket in node.inputs]}
            if node.type == 'TEX_IMAGE' and node.image:
                image = node.image; assert image.packed_file, ('Unpacked selected map', image.name)
                row['image'] = {'name': image.name, 'size': list(image.size),
                                'colorSpace': image.colorspace_settings.name,
                                'alphaMode': image.alpha_mode,
                                'sha256': hashlib.sha256(image.packed_file.data).hexdigest()}
            nodes.append(row)
        materials.append({'name': mat.name, 'settings': scalar_rna(mat), 'nodes': nodes,
            'links': [[link.from_node.name, link.from_socket.identifier,
                       link.to_node.name, link.to_socket.identifier] for link in mat.node_tree.links]})
    transforms = {'world': [list(row) for row in obj.matrix_world],
                  'parentInverse': [list(row) for row in obj.matrix_parent_inverse],
                  'parent': obj.parent.name if obj.parent else None,
                  'modifiers': [{'settings': scalar_rna(mod),
                                 'object': mod.object.name if hasattr(mod, 'object') and mod.object else None}
                                for mod in obj.modifiers],
                  'materials': materials, 'hideRender': obj.hide_render,
                  'customProperties': {key: obj[key] for key in obj.keys()
                                       if isinstance(obj[key], (str, int, float, bool))}}
    digest.update(json.dumps(transforms, sort_keys=True).encode())
    return {'sha256': digest.hexdigest(), 'vertices': len(mesh.vertices),
            'polygons': len(mesh.polygons), 'positionChangesAllowed': allow_positions}


def masked_state(helper, contract, allowed_position_objects):
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.animation_data is None and rig.matrix_world.is_identity
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert native_rest(rig) == contract['nativeRest']['bones'], 'Exact saved native75 rest changed'
    visible = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render]
    assert {obj.name for obj in visible} == helper['EXPECTED'] and len(visible) == 7
    reference = bpy.data.objects['RiderBody__FullAnatomyReference']
    body = bpy.data.objects['RiderBody']
    assert reference.hide_render and body['outfitFullBodyReference'] == reference.name
    for obj in visible:
        assert obj.matrix_world.is_identity
        arms = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
        assert len(arms) == 1 and arms[0].object == rig and not arms[0].use_deform_preserve_volume
        assert all(mod.type in {'ARMATURE', 'TRIANGULATE'} for mod in obj.modifiers)
        rows = helper['mesh_four'](obj, rig)
        assert all(weight > .0001 for row in rows for _, weight in row), ('Saved export cutoff unstable', obj.name)
    states = {obj.name: part_fingerprint(obj, helper, obj.name in allowed_position_objects)
              for obj in visible+[reference]}
    positions = {}
    for obj in visible:
        if obj.name not in allowed_position_objects: continue
        values = helper['np'].empty(len(obj.data.vertices)*3, dtype=helper['np'].float32)
        obj.data.vertices.foreach_get('co', values)
        assert helper['np'].isfinite(values).all()
        positions[obj.name] = hashlib.sha256(values.tobytes()).hexdigest()
    return rig, visible, states, positions


def intake_masked(manifest, manifest_path, out, helper):
    """Validate a shape-only derivative, without mask, prune or weight writes."""
    gloves = {'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
    allowed = manifest.get('allowedPositionObjects', sorted(gloves))
    assert isinstance(allowed, list) and all(isinstance(name, str) for name in allowed)
    assert len(allowed) == len(set(allowed)), 'Duplicate allowed position object'
    allowed = set(allowed)
    assert allowed in (gloves, gloves | {'RiderHoodie'}), 'Only bilateral gloves or gloves plus hoodie may change positions'
    pin = helper['pin']
    parent_path = pin(manifest['parentExportReceipt'])
    parent = json.loads(parent_path.read_text())
    corrected = json.loads(pin(manifest['correctedNativeReceipt']).read_text())
    assert parent['accepted'] is False and parent['rigAndContractExactNative75'] is True
    assert parent['decodedFourQualification']['decodedSourceFOURMatchesSavedNative'] is True
    assert parent['native'] == manifest['parentNative'] == corrected['sourceMaster']
    assert corrected['native'] == manifest['native'] and corrected['exact75RestUnchanged'] is True
    assert corrected.get('acceptedArt') is False and corrected['visibleMeshes'] == sorted(helper['EXPECTED'])
    assert Path(parent['native']['path']).parent == Path(manifest['baseContract']['path']).parent
    for key, filename in [('bodyMaskManifest', 'body-mask-manifest.json'),
                          ('bodyMaskReceipt', parent['bodyMaskReceipt'])]:
        assert pin(manifest[key]) == parent_path.parent/filename
    contract = json.loads(pin(manifest['baseContract']).read_text())
    assert contract['glbSHA256'] == parent['glb']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['parentNative'])))
    _, _, before, before_positions = masked_state(helper, contract, allowed)
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['native'])))
    rig, meshes, after, after_positions = masked_state(helper, contract, allowed)
    assert before == after, ('Shape-only masked export changed protected native data',
                             [name for name in before if before[name] != after[name]])
    assert all(before_positions[name] != after_positions[name] for name in before_positions), 'Expected allowed-object shape correction is absent'
    qualification = {'positionHashesBefore': before_positions, 'positionHashesAfter': after_positions,
                     'parentExportReceipt': manifest['parentExportReceipt'],
                     'parentNative': manifest['parentNative'], 'correctedNativeReceipt': manifest['correctedNativeReceipt'],
                     'protectedNativeFingerprints': after, 'bodyMaskAppliedAgain': False,
                     'weightPruningOrNormalizationPerformed': False,
                     'allowedPositionObjects': sorted(allowed),
                     'fullAnatomyReferenceAndOtherMeshesExact': True,
                     'otherVisibleMeshesExactCount': len(meshes)-len(allowed),
                     'allSevenTopologyUVPBRAndDeliveryFieldsExact': True,
                     'savedPointNativeIDsValidatedByFinalizer': True,
                     'exportCutoffStableWithoutMutation': True}
    if allowed == gloves:
        qualification.update({'glovePositionHashesBefore': before_positions, 'glovePositionHashesAfter': after_positions,
                              'fullAnatomyReferenceAndOtherFiveMeshesExact': True})
    conditioning = [{'object': obj.name, 'cutoff': .0001, 'changedRows': 0,
                     'maximumRemovedMass': 0., 'method': 'Assert existing saved delivery coefficients; no mutation'}
                    for obj in meshes]
    finalize(manifest, manifest_path, out, helper, rig, meshes, contract,
             json.loads(pin(manifest['bodyMaskManifest']).read_text()),
             json.loads(pin(manifest['bodyMaskReceipt']).read_text()),
             {'method': 'Existing masked body FOUR preserved exactly; no conditioning',
              'fullAnatomyReferenceChanged': False}, conditioning, qualification)


def finalize(manifest, manifest_path, out, helper, rig, meshes, contract, mask_manifest, mask_receipt, body_four, cutoff_conditioning, masked_qualification=None):
    """One strict transport finalizer for fresh masks and shape-only corrections."""
    pin, sha = helper['pin'], helper['sha']
    for obj in meshes:
        attribute = obj.data.attributes.get('_NATIVE_ID')
        if attribute is None:
            assert not manifest.get('alreadyMasked'), ('Missing saved native identity', obj.name)
            attribute = obj.data.attributes.new('_NATIVE_ID', 'INT', 'POINT')
        assert attribute.domain == 'POINT' and attribute.data_type == 'INT'
        if manifest.get('alreadyMasked'):
            values = helper['np'].empty(len(obj.data.vertices), dtype=helper['np'].int32)
            attribute.data.foreach_get('value', values)
            assert helper['np'].array_equal(values, helper['np'].arange(len(values))), ('Changed native identity', obj.name)
        else:
            attribute.data.foreach_set('value', list(range(len(obj.data.vertices))))
    contract['accepted'] = False
    contract['specification']['meshNames'] = {o.name: o.name for o in meshes}
    contract['driver']['nearSimilarityTolerance'] = 1e-4
    contract['driver']['socketOrientationCalibrationRequired'] = True
    contract['qualificationState'] = {'promotionAllowed': False,
        'movingArt': 'PARENT_PLAYED_REVIEW_PENDING', 'nativeGPUParity': 'UNQUALIFIED',
        'finiteGloveBarAndBootPegContacts': 'UNQUALIFIED', 'devicePerformance': 'UNQUALIFIED'}
    for key in ('glbSHA256', 'exportedObjectMeshes', 'sourceSHA256', 'metadataSHA256', 'genericAction'):
        contract.pop(key, None)
    out.mkdir(parents=True)
    if manifest.get('alreadyMasked'):
        (out/'body-mask-manifest.json').write_bytes(pin(manifest['bodyMaskManifest']).read_bytes())
        (out/'body-mask-receipt.json').write_bytes(pin(manifest['bodyMaskReceipt']).read_bytes())
    else:
        (out/'body-mask-manifest.json').write_text(json.dumps(mask_manifest, indent=2)+'\n')
        (out/'body-mask-receipt.json').write_text(json.dumps(mask_receipt, indent=2)+'\n')
    bpy.ops.object.select_all(action='DESELECT')
    rig.hide_set(False); rig.select_set(True)
    for obj in meshes: obj.hide_set(False); obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    native = out/'rider-private-masked.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    glb = out/'rider.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
        export_animations=False, export_def_bones=True, export_skins=True,
        export_influence_nb=4, export_all_influences=False, export_apply=True,
        export_yup=True, export_attributes=True)
    raw = glb.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20+size])
    assert len(document['skins']) == 1 and len(document['skins'][0]['joints']) == 75
    nodes = [node for node in document['nodes'] if 'mesh' in node]
    assert {node['name'] for node in nodes} == helper['EXPECTED'] and len(nodes) == 7
    assert all(node.get('skin') == 0 for node in nodes)
    for node in nodes:
        for primitive in document['meshes'][node['mesh']]['primitives']:
            assert {'POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0', '_NATIVE_ID'} <= set(primitive['attributes'])
            assert 'material' in primitive
    contract['glbSHA256'] = sha(glb)
    decoded_four = four_readback(document, raw, meshes, helper)
    contract['exportedObjectMeshes'] = [{'nodeName': node['name'], 'meshIndex': node['mesh'],
        'primitiveCount': len(document['meshes'][node['mesh']]['primitives'])} for node in nodes]
    (out/'rider-contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    for row in helper['pins'](manifest): pin(row)
    report = {'accepted': False, 'status': 'PRIVATE_SELECTED_MASKED_ENGINE_EXPORT_REVIEW_PENDING',
        'native': {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)},
        'glb': {'path': str(glb.relative_to(ROOT)), 'sha256': sha(glb)},
        'recipeSHA256': sha(__file__), 'manifestSHA256': sha(manifest_path),
        'bodyMaskReceipt': 'body-mask-receipt.json', 'renderBodyFourConditioning': body_four,
        'renderDeliveryExportCutoffConditioning': cutoff_conditioning,
        'decodedFourQualification': decoded_four,
        'alreadyMaskedReexport': masked_qualification,
        'objects': sorted(helper['EXPECTED']),
        'rigAndContractExactNative75': True, 'normalPlayerAssetsWritten': False,
        'limits': ['Structural export intake only. All R0-R5 remain open.',
                   'Actual Garage/game continuous motion, GPU parity and device performance require parent judgment.',
                   'Original4K maps embedded; this dense private preview does not meet a shipping performance gate.',
                   'No old combined04 calibration transferred across corrected finger rest frames.']}
    (out/'export.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'glb': report['glb']}), flush=True)



def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    manifest_path, out = (Path(value).resolve() for value in args)
    manifest = json.loads(manifest_path.read_text())
    assert manifest['accepted'] is False and manifest.get('ready') is True and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-complete-engine01')
    # Use the already reviewed small merge helpers for pinning and FOUR intake.
    helper_path = ROOT/manifest['mergeHelper']['path']
    import hashlib
    assert hashlib.sha256(helper_path.read_bytes()).hexdigest() == manifest['mergeHelper']['sha256']
    helper = runpy.run_path(str(helper_path))
    pin, sha = helper['pin'], helper['sha']
    for row in helper['pins'](manifest): pin(row)
    if manifest.get('alreadyMasked'):
        intake_masked(manifest, manifest_path, out, helper)
        return
    merged = json.loads(pin(manifest['mergeReceipt']).read_text())
    assert merged['native'] == manifest['native'] and merged['visibleMeshes'] == sorted(helper['EXPECTED'])
    assert merged['recipeSHA256'] == manifest['mergeHelper']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['native'])))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    visible = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    assert {o.name for o in visible} == helper['EXPECTED']
    contract = json.loads(pin(manifest['baseContract']).read_text())
    native_rest = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                    'head': list(b.head_local), 'tail': list(b.tail_local),
                    'matrix': [list(row) for row in b.matrix_local],
                    'useConnect': b.use_connect, 'useDeform': b.use_deform} for b in rig.data.bones]
    assert native_rest == contract['nativeRest']['bones'], 'Fresh native75 contract must match actual source rest'
    for obj in visible:
        helper['mesh_four'](obj, rig, require_four=obj != body)
        arms = [m for m in obj.modifiers if m.type == 'ARMATURE']
        assert len(arms) == 1 and arms[0].object == rig and not arms[0].use_deform_preserve_volume
        assert obj.matrix_world.is_identity
    full_body_fields = helper['mesh_four'](body, rig, require_four=False)
    mask = runpy.run_path(str(pin(manifest['maskHelper'])))
    render_body, mask_manifest, mask_receipt = mask['freeze_and_apply'](
        body, rig, ['hoodie', 'jeans', 'gloves', 'boots'], manifest['native'])
    body.name = 'RiderBody__FullAnatomyReference'
    render_body.name = 'RiderBody'
    render_body['outfitFullBodyReference'] = body.name
    mask_receipt.update(renderBody=render_body.name, fullBodyReference=body.name)
    body_four = helper['limit_four'](render_body, rig)
    assert helper['mesh_four'](body, rig, require_four=False) == full_body_fields
    meshes = [render_body]+[o for o in visible if o != body]
    assert {o.name for o in meshes} == helper['EXPECTED']
    cutoff_conditioning = [export_cutoff(obj, rig, helper) for obj in meshes]
    assert helper['mesh_four'](body, rig, require_four=False) == full_body_fields
    finalize(manifest, manifest_path, out, helper, rig, meshes, contract, mask_manifest, mask_receipt, body_four, cutoff_conditioning)


if __name__ == '__main__': main()
