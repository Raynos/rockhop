"""Mask/export the saved complete selected native for private actual-game review.

Parent CPU2 only, after source checkpoint and moving shape judgment.
blender -b -t 2 --python-exit-code 1 --python export-private.py -- MANIFEST FRESH_OUT
Normal player models/catalogs are never written.
"""
import json
import runpy
import struct
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[4]


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


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    manifest_path, out = (Path(value).resolve() for value in args)
    manifest = json.loads(manifest_path.read_text())
    assert manifest['accepted'] is False and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-complete-engine01')
    # Use the already reviewed small merge helpers for pinning and FOUR intake.
    helper_path = ROOT/manifest['mergeHelper']['path']
    import hashlib
    assert hashlib.sha256(helper_path.read_bytes()).hexdigest() == manifest['mergeHelper']['sha256']
    helper = runpy.run_path(str(helper_path))
    pin, sha = helper['pin'], helper['sha']
    for row in helper['pins'](manifest): pin(row)
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['native'])))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    visible = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
    assert {o.name for o in visible} == helper['EXPECTED']
    contract = json.loads(pin(manifest['baseContract']).read_text())
    native_rest = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                    'head': list(b.head_local), 'tail': list(b.tail_local),
                    'matrix': [list(row) for row in b.matrix_local]} for b in rig.data.bones]
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
    for obj in meshes:
        attribute = obj.data.attributes.get('_NATIVE_ID')
        if attribute is None:
            attribute = obj.data.attributes.new('_NATIVE_ID', 'INT', 'POINT')
        assert attribute.domain == 'POINT' and attribute.data_type == 'INT'
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
        'decodedFourQualification': decoded_four,
        'objects': sorted(helper['EXPECTED']),
        'rigAndContractExactNative75': True, 'normalPlayerAssetsWritten': False,
        'limits': ['Structural export intake only. All R0-R5 remain open.',
                   'Actual Garage/game continuous motion, GPU parity and device performance require parent judgment.',
                   'Original4K maps embedded; this dense private preview does not meet a shipping performance gate.',
                   'No old combined04 calibration transferred across corrected finger rest frames.']}
    (out/'export.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'glb': report['glb']}), flush=True)


if __name__ == '__main__': main()
