"""Parent CPU2 only: import pinned corrective06 deltas into engine05 native.

blender -b -t 2 --python-exit-code 1 --python import-native.py --
  --shape-key=JSON --shape-sha256=SHA --corrective-receipt=JSON
  --corrective-sha256=SHA --out=FRESH_IGNORED_DIRECTORY
No GLB export, fitting, weight edits, normal assets, or trust changes.
"""
import argparse
import hashlib
import inspect
import json
import math
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NAME = 'SelectedSeatedCorrective06'
PINS = {
    'native': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-private-masked.blend',
               '95a4f14e06fb52cc055df6d1446a035d8cd3d35180d565ad52f3a70b3b05664b'),
    'contract': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-contract.json',
                 '2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728'),
    'sourceGLB': ('harness/out/rider-rebuild/selected-complete-engine01/engine05/rider.glb',
                  '72b90e8790f8490743a75f8b70791aa21edfee6234cec609093e9b62e08d4bfd'),
}


def sha(file):
    digest = hashlib.sha256()
    with Path(file).open('rb') as handle:
        while block := handle.read(1024*1024): digest.update(block)
    return digest.hexdigest()


def values(collection, field, width, dtype=np.float32):
    result = np.empty(len(collection)*width, dtype=dtype)
    collection.foreach_get(field, result); return result.reshape(len(collection), width)


def install_driver(owner, data_path, expression, variables, rig):
    curve = owner.driver_add(data_path); driver = curve.driver; driver.type = 'SCRIPTED'
    driver.expression = expression
    for name, specification in variables.items():
        variable = driver.variables.new(); variable.name = name; target = variable.targets[0]; target.id = rig
        if specification[0] == 'WORLD_QUATERNION':
            variable.type = 'TRANSFORMS'; target = variable.targets[0]; target.id = rig
            target.bone_target = specification[1]; target.transform_space = 'WORLD_SPACE'
            target.rotation_mode = 'QUATERNION'; target.transform_type = 'ROT_'+specification[2].upper()
        else:
            variable.type = 'SINGLE_PROP'; target = variable.targets[0]; target.id = rig
            target.data_path = '['+json.dumps(specification[1])+']'
    return curve


def probe_driver_graph(rig, roles, activation, blocks, maths, curves):
    saved = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
    saved_world = rig.matrix_world.copy()
    probes = []; pelvis = rig.pose.bones[roles['pelvis']].matrix.to_quaternion()
    try:
        for t, rotated in [(0., False), (.25, False), (.5, False), (.75, False), (1., False), (1., True)]:
            rig.matrix_world = (Quaternion((.8, .2, -.3, .4)).normalized().to_matrix().to_4x4()
                                if rotated else saved_world)
            for index, side in enumerate(('L', 'R')):
                rest = Quaternion(maths['wxyz'](activation['restRelativeXYZW'][index]))
                target = Quaternion(maths['multiply'](maths['wxyz'](activation['keyXYZW'][index]), tuple(rest)))
                bone = rig.pose.bones[roles[side]]; location = bone.matrix.translation.copy()
                matrix = (pelvis @ rest.slerp(target, t)).to_matrix().to_4x4(); matrix.translation = location; bone.matrix = matrix
            bpy.context.view_layer.update()
            world = [tuple((rig.matrix_world @ rig.pose.bones[roles[key]].matrix).to_quaternion()) for key in ('pelvis', 'L', 'R')]
            expected = maths['expected_weight'](world, activation); actual = [float(block.value) for block in blocks]
            assert all(curve.driver.is_valid and curve.driver.is_simple_expression for curve in curves), 'Built-in driver graph invalid or requires Python execution'
            residual = max(abs(weight-expected) for weight in actual)
            assert residual < 2e-5, ('Driver parity needs parent probe', t, expected, actual, residual)
            probes.append({'t': t, 'commonRigRotation': rotated, 'expected': expected, 'actual': actual, 'maximumResidual': residual})
        assert probes[0]['expected'] < 1e-12 and abs(probes[-1]['expected']-1) < 2e-5
    finally:
        for bone in rig.pose.bones: bone.matrix_basis = saved[bone.name]
        rig.matrix_world = saved_world
        bpy.context.view_layer.update()
    return probes


def protected_fingerprinter():
    exporter = ROOT/'assets/blender/rider-rebuild/selected-complete-engine01/export-private.py'
    assert sha(exporter) == 'b0720a3f492e2b05b1256f4034411d775d6920f3e1cd7c69ccebb5b9b8944cb5'
    helpers = runpy.run_path(str(exporter))
    source = inspect.getsource(helpers['part_fingerprint'])
    anchor = "assert obj.type == 'MESH' and not mesh.shape_keys and obj.animation_data is None"
    assert source.count(anchor) == 1
    namespace = dict(helpers); exec(source.replace(anchor, "assert obj.type == 'MESH' and obj.animation_data is None"), namespace)
    return lambda obj: namespace['part_fingerprint'](obj, {'np': np}), helpers, exporter


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--shape-key', required=True)
    parser.add_argument('--shape-sha256', required=True); parser.add_argument('--corrective-receipt', required=True)
    parser.add_argument('--corrective-sha256', required=True); parser.add_argument('--out', required=True)
    parser.add_argument('--allow-failed-diagnostic', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    out = Path(args.out).resolve(); shape_path = Path(args.shape_key).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-native07')
    assert sha(shape_path) == args.shape_sha256
    corrective_path = Path(args.corrective_receipt).resolve(); assert sha(corrective_path) == args.corrective_sha256
    for filename, digest in PINS.values(): assert sha(ROOT/filename) == digest, ('Changed engine05 pin', filename)
    shape = json.loads(shape_path.read_text()); activation = shape['activation']
    corrective = json.loads(corrective_path.read_text())
    assert corrective['accepted'] is False
    assert corrective['status'] in {'UNACCEPTED_CORRECTIVE_CANDIDATE', 'FAILED_CORRECTIVE_GATES'}
    assert [check['t'] for check in corrective['checks']] == [0, .25, .5, .75, 1]
    assert all(check['pass'] for check in corrective['checks']) or args.allow_failed_diagnostic, 'Failed geometry needs explicit diagnostic intake'
    assert corrective['activation'] == activation and corrective['pins']['rider']['sha256'] == PINS['sourceGLB'][1]
    assert shape['accepted'] is False and shape['relative'] is True and shape['name'] == NAME
    assert shape['status'] == corrective['status'], 'Shape and geometry receipt classifications differ'
    assert shape['sourceSHA256'] == PINS['sourceGLB'][1] and set(shape['deltas']) == {'RiderJeans', 'RiderBody'}
    contract = json.loads((ROOT/PINS['contract'][0]).read_text())
    maths = runpy.run_path(str(HERE/'driver_math.py'))
    # Reuse the actual protected-data fingerprint. Relax only its no-shape-key
    # eligibility assertion; its positions/UV/material/Four/normal hashing is exact.
    fingerprint, helpers, exporter = protected_fingerprinter()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/PINS['native'][0]), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; assert rig.matrix_world.is_identity and len(rig.data.bones) == 75
    assert rig.animation_data is None and not rig.constraints and all(not bone.constraints and bone.matrix_basis.is_identity for bone in rig.pose.bones)
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    names = set(contract['specification']['meshNames'].values())
    visible = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and not obj.hide_render]
    assert {obj.name for obj in visible} == names and len(visible) == 7
    reference = bpy.data.objects['RiderBody__FullAnatomyReference']; assert reference.hide_render
    before = {obj.name: fingerprint(obj) for obj in visible+[reference]}
    role_name = lambda role: contract['specification']['jointNames'][
        (contract['specification']['roles'][role][0] if isinstance(contract['specification']['roles'][role], list) else contract['specification']['roles'][role])]
    roles = {'pelvis': role_name('pelvis'), 'L': role_name('thighLeft'), 'R': role_name('thighRight')}
    rest_relative = []
    for index, side in enumerate(('L', 'R')):
        relative = rig.data.bones[roles['pelvis']].matrix_local.to_quaternion().inverted() @ rig.data.bones[roles[side]].matrix_local.to_quaternion()
        residual = maths['angle'](tuple(relative), maths['wxyz'](activation['restRelativeXYZW'][index]))
        assert residual < 1e-5, ('Native/export relative-quaternion basis differs; parent probe required', side, residual)
        rest_relative.append(residual)
    mesh_reports = {}; blocks = []
    for name, rows in shape['deltas'].items():
        obj = bpy.data.objects[name]; mesh = obj.data; assert not mesh.shape_keys
        assert isinstance(rows, list) and (rows or name == 'RiderBody'), 'Jeans corrective is empty'
        attribute = mesh.attributes.get('_NATIVE_ID'); assert attribute and attribute.domain == 'POINT' and attribute.data_type == 'INT'
        native = values(attribute.data, 'value', 1, np.int32).reshape(-1)
        assert np.array_equal(native, np.arange(len(mesh.vertices))), ('Native current-inventory ancestry changed', name)
        base = values(mesh.vertices, 'co', 3); desired = base.astype(np.float64); seen = set()
        for row in rows:
            identity = row['nativeID']; assert type(identity) is int and 0 <= identity < len(base) and identity not in seen; seen.add(identity)
            delta = np.asarray(row['deltaBlender'], dtype=np.float64); assert delta.shape == (3,) and np.isfinite(delta).all()
            assert np.max(abs(delta[[0, 2, 1]]*np.array([1, 1, -1])-np.asarray(row['deltaGLTF']))) < 1e-12
            desired[identity] += delta
        basis = obj.shape_key_add(name='Basis', from_mix=False); block = obj.shape_key_add(name=NAME, from_mix=False)
        mesh.shape_keys.use_relative = True; block.relative_key = basis; block.value = 0.; block.slider_min = 0.; block.slider_max = 1.
        expected = desired.astype(np.float32); block.data.foreach_set('co', expected.ravel())
        assert np.array_equal(values(basis.data, 'co', 3), base) and np.array_equal(values(mesh.vertices, 'co', 3), base)
        assert np.array_equal(values(block.data, 'co', 3), expected)
        mesh_reports[name] = {'nativeVertices': len(base), 'explicitDeltaIDs': len(seen), 'basisExactlySource': True,
            'targetFloat32ExactlyExpected': True, 'maximumAssignmentQuantizationM': float(np.max(np.linalg.norm(expected.astype(float)-desired, axis=1)))}
        blocks.append(block)
    curves = []
    for property_name, expression, variables in maths['graph'](activation, roles):
        assert property_name not in rig; rig[property_name] = 0.
        curves.append(install_driver(rig, '['+json.dumps(property_name)+']', expression, variables, rig))
    for block in blocks:
        curves.append(install_driver(block, 'value', maths['SHAPE_EXPRESSION'], {'x': ('PROPERTY', maths['PREFIX']+'x')}, rig))
    probes = probe_driver_graph(rig, roles, activation, blocks, maths, curves)
    assert all(bone.matrix_basis.is_identity for bone in rig.pose.bones), 'Probe did not restore exact rest pose'
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    after = {obj.name: fingerprint(obj) for obj in visible+[reference]}; assert before == after
    assert all(abs(block.value) < 1e-12 for block in blocks)
    for block in blocks: block.value = 0.
    out.mkdir(parents=True); native_out = out/'selected-seated-native07.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native_out), compress=True)
    report = {'accepted': False, 'status': 'UNACCEPTED_NATIVE_CORRECTIVE_REOPEN_PROBE_PENDING',
        'sourcePins': {key: {'path': filename, 'sha256': digest} for key, (filename, digest) in PINS.items()},
        'shapeKey': {'path': str(shape_path), 'sha256': args.shape_sha256}, 'recipeSHA256': sha(__file__),
        'correctiveReceipt': {'path': str(corrective_path), 'sha256': args.corrective_sha256,
                              'status': corrective['status'], 'checks': corrective['checks'],
                              'failedDiagnosticAuthorized': args.allow_failed_diagnostic},
        'driverMathSHA256': sha(HERE/'driver_math.py'), 'fingerprintRecipeSHA256': sha(exporter),
        'native': {'path': str(native_out.relative_to(ROOT)), 'sha256': sha(native_out)},
        'exact75RestUnchanged': True, 'protectedNativeBefore': before, 'protectedNativeAfter': after,
        'meshes': mesh_reports, 'relativeRestBasisResidualRadians': rest_relative, 'driverProbes': probes,
        'driverMethod': 'Built-in WORLD quaternion variables -> inverse pelvis times thigh -> distance to key times rest -> bilateral Wendland',
        'scriptAutoExecutionRequired': False, 'defaultRestKeyValue': 0,
        'limits': ['Saved/reopened driver parity and default-zero evaluation remain parent probes.',
                   'No GLB export or driver runtime transport claim. No moving-art or contact acceptance.']}
    (out/'native-import.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'status': report['status']}), flush=True)


if __name__ == '__main__': main()
