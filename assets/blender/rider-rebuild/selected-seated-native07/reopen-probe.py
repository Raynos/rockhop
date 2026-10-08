"""Parent CPU2 only. Reopen with scripts disabled; optional static morph export.

blender -b -t 2 --python-exit-code 1 --python reopen-probe.py --
  --receipt=NATIVE_IMPORT_JSON --out=FRESH_IGNORED_DIRECTORY [--export-probe]
No namespace registration, embedded Text execution, or trust preference changes.
"""
import argparse
import json
import mmap
import runpy
import struct
import sys
from pathlib import Path
import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--receipt', required=True)
    parser.add_argument('--out', required=True); parser.add_argument('--export-probe', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:]); out = Path(args.out).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-native07')
    source = runpy.run_path(str(HERE/'import-native.py')); sha, values = source['sha'], source['values']
    receipt = json.loads(Path(args.receipt).read_text())
    assert receipt['accepted'] is False and sha(HERE/'import-native.py') == receipt['recipeSHA256']
    assert sha(HERE/'driver_math.py') == receipt['driverMathSHA256']
    native = ROOT/receipt['native']['path']; assert sha(native) == receipt['native']['sha256']
    shape_path = Path(receipt['shapeKey']['path']); assert sha(shape_path) == receipt['shapeKey']['sha256']
    corrective = receipt['correctiveReceipt']; assert sha(corrective['path']) == corrective['sha256']
    shape = json.loads(shape_path.read_text()); activation = shape['activation']
    contract_path, contract_sha = source['PINS']['contract']; assert sha(ROOT/contract_path) == contract_sha
    contract = json.loads((ROOT/contract_path).read_text()); maths = runpy.run_path(str(HERE/'driver_math.py'))
    bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; fingerprint, helpers, _ = source['protected_fingerprinter']()
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones'] and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    meshes = [bpy.data.objects[name] for name in contract['specification']['meshNames'].values()]
    reference = bpy.data.objects['RiderBody__FullAnatomyReference']
    assert {obj.name: fingerprint(obj) for obj in meshes+[reference]} == receipt['protectedNativeBefore']
    blocks = [bpy.data.objects[name].data.shape_keys.key_blocks[source['NAME']] for name in ('RiderJeans', 'RiderBody')]
    default_values = [float(block.value) for block in blocks]
    assert default_values == [0., 0.], ('Saved rest key is not exactly zero', default_values)
    curves = list(rig.animation_data.drivers)
    for name in ('RiderJeans', 'RiderBody'): curves += list(bpy.data.objects[name].data.shape_keys.animation_data.drivers)
    assert len(curves) == 13 and all(curve.driver.is_simple_expression for curve in curves)
    role = lambda name: contract['specification']['jointNames'][
        (contract['specification']['roles'][name][0] if isinstance(contract['specification']['roles'][name], list) else contract['specification']['roles'][name])]
    roles = {'pelvis': role('pelvis'), 'L': role('thighLeft'), 'R': role('thighRight')}
    probes = source['probe_driver_graph'](rig, roles, activation, blocks, maths, curves)
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {obj.name: fingerprint(obj) for obj in meshes+[reference]} == receipt['protectedNativeBefore']
    report = {'accepted': False, 'status': 'UNACCEPTED_NATIVE_REOPEN_PROBE', 'useScripts': False,
        'nativeImportReceipt': {'path': str(Path(args.receipt).resolve()), 'sha256': sha(args.receipt)},
        'correctiveReceipt': corrective,
        'defaultStoredWeights': default_values, 'builtInDriverCount': len(curves), 'driverProbes': probes,
        'exact75RestAndProtectedNativeFields': True, 'exportProbe': None,
        'limits': ['No moving-art, finite contact, or native/GPU acceptance.',
                   'Static morph export probe does not establish unchanged baseline GLB topology/UV/PBR/BIN parity or live driver transport.']}
    out.mkdir(parents=True)
    if args.export_probe:
        # Driver formulas are native-only. Static glTF transports targets and
        # default weights; engine activation must be implemented explicitly.
        for curve in curves: curve.mute = True
        for block in blocks: block.value = 0.
        bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
        for obj in meshes: obj.select_set(True)
        bpy.context.view_layer.objects.active = rig
        glb = out/'native-static-morph-probe.glb'
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
            export_animations=False, export_def_bones=True, export_skins=True, export_influence_nb=4,
            export_all_influences=False, export_apply=False, export_yup=True, export_attributes=True,
            export_morph=True, export_morph_normal=True, export_morph_tangent=False)
        with glb.open('rb') as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            length = struct.unpack_from('<I', raw, 12)[0]; document = json.loads(raw[20:20+length]); offset = 28+length
            assert len(document['skins']) == 1 and len(document['skins'][0]['joints']) == 75
            def accessor(index):
                a = document['accessors'][index]; v = document['bufferViews'][a['bufferView']]
                assert not a.get('sparse') and v['buffer'] == 0
                dtype = np.dtype({5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']])
                width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
                return np.ndarray((a['count'], width), dtype=dtype, buffer=raw,
                    offset=offset+v.get('byteOffset', 0)+a.get('byteOffset', 0),
                    strides=(v.get('byteStride', width*dtype.itemsize), dtype.itemsize))
            audited = []
            for node in document['nodes']:
                if node.get('name') not in shape['deltas'] or 'mesh' not in node: continue
                name = node['name']; mesh = document['meshes'][node['mesh']]
                assert mesh.get('weights') == [0.] and mesh['extras']['targetNames'] == [source['NAME']]
                obj = bpy.data.objects[name]; base = values(obj.data.vertices, 'co', 3)
                deltas = np.zeros_like(base)
                key = obj.data.shape_keys.key_blocks[source['NAME']]
                deltas[:] = values(key.data, 'co', 3)-base
                maximum = 0.; decoded = 0
                for primitive in mesh['primitives']:
                    attrs = primitive['attributes']; assert {'POSITION', 'JOINTS_0', 'WEIGHTS_0', '_NATIVE_ID'} <= set(attrs)
                    assert 'WEIGHTS_1' not in attrs and 'JOINTS_1' not in attrs and len(primitive['targets']) == 1
                    ids = accessor(attrs['_NATIVE_ID']).reshape(-1).astype(np.int64)
                    assert np.min(ids) >= 0 and np.max(ids) < len(base)
                    expected = deltas[ids][:, [0, 2, 1]]*np.array([1, 1, -1])
                    actual = accessor(primitive['targets'][0]['POSITION'])
                    maximum = max(maximum, float(np.max(abs(actual-expected)))); decoded += len(ids)
                assert maximum < 1e-7, ('Exported native-ID morph mismatch', name, maximum)
                audited.append({'name': name, 'decodedRows': decoded, 'maximumMorphResidualM': maximum})
            assert {row['name'] for row in audited} == {'RiderJeans', 'RiderBody'}
            report['exportProbe'] = {'path': str(glb.relative_to(ROOT)), 'sha256': sha(glb),
                'exportApply': False, 'defaultWeight': 0, 'actualNativeIDMorphReadback': audited,
                'runtimeDriverFormulaExported': False, 'fullBaselineTransportQualified': False}
            del actual
        # The probe changed only this process's in-memory driver mute state;
        # the source .blend is never resaved or replaced.
    (out/'reopen-probe.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'out': str(out), 'status': report['status'], 'exportProbe': bool(report['exportProbe'])}), flush=True)


if __name__ == '__main__': main()
