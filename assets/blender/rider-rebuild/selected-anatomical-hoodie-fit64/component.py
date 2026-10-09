"""One ordered anatomical C2 hoodie rest fit; parent guarded Blender only.

Exact original selected topology, source indices, UV/PBR and named fields are
preserved. Only rest positions and transported source corner normals change.
Raw native saves before postconstruction fingerprint/strain qualification.
"""
import gc
import hashlib
import importlib.util
import json
import runpy
import struct
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
c47 = runpy.run_path(str(HERE.parent/'selected-sleeve-component47/component.py'))
ROOT, checked, pin, write = (c47[k] for k in ('ROOT', 'checked', 'pin', 'write'))
OUT = ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit64'
SOURCE47 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/input01.json',
            'sha256': '7426ed1631f88fd4f6dc6c951ce10fb09d257c739add94f553243a8a3e2e6599'}
WRAPPER47 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/sleeve47.py',
             'sha256': 'a90e56476dffc95b1089a6d2af6df75e75fd3bfe10df173a9135d55014ea3b84'}
PENDING = 'UNACCEPTED_ANATOMICAL64_SAVED_REOPEN_PENDING'
QUALIFIED = 'UNACCEPTED_ANATOMICAL64_REOPENED_DISTAL_AND_MOTION_PENDING'
LOCAL = {'targets64': 'targets.py', 'sections64': 'sections.py', 'qualification64': 'qualify.py', 'geometry64': 'geometry.py', 'meridian64': 'meridian.py', 'intervals64': 'intervals.py'}
REFERENCE = {
    'rejected60Failure': {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit60/component01/construction-failure.json', 'sha256': 'a54762e60054f5f366c44bd0abc054ecd5a45bbe4db608816a3879e20277c680'},
    'rejected60Input': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit60/input01.json', 'sha256': '8c81efd750378a8348511cd870eae0993b11865e7cffbfba85432fedac6edf47'},
    'recordedRightTorsoCPU60': {'path': 'docs/evidence/rider-rebuild/selected-anatomical-hoodie-fit60/right-torso-exterior-preflight.json', 'sha256': '7e06b51fe9468706b4664aaa9850552631f7d64f536f08ccc05c14b0c97e8d02'},
    'rejected58Failure': {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit58/component01/construction-failure.json', 'sha256': 'b568285fa00d044de61367f7e572530705f19c5cfcd612e27c0b22617b767f35'},
    'rejected58Input': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit58/input01.json', 'sha256': 'b900c840f3803d2e63eeaf6cd52da35f5d4fb4b071bf34a4fd532b7ec0f9e577'},
    'rayDiagnosis60': {'path': 'docs/evidence/rider-rebuild/selected-anatomical-hoodie-fit60/ray58-diagnosis.json', 'sha256': 'b4cb7845fc86c27415e631ec356a13c79c33f11ef1a030cc02d76fb88862dd97'},
    'allBranchesCPU60': {'path': 'docs/evidence/rider-rebuild/selected-anatomical-hoodie-fit60/all-branches-preflight.json', 'sha256': '0f67ec5349b6e9f36558f0c2ccd0ea5dc9d9a9f1eab0a0e77c0dbd5b3b497758'},
    'rejected55Failure': {'path': 'harness/out/rider-rebuild/selected-anatomical-hoodie-fit55/component01/construction-failure.json', 'sha256': '7f42838fd2da3c911c54f373c0418fd1deb10e00467143c4c95da60c24878f74'},
    'rejected55Input': {'path': 'assets/blender/rider-rebuild/selected-anatomical-hoodie-fit55/input01.json', 'sha256': '7d9249f1dc0d1c2d068efd27562a85642848730b5c2b9fc6dd55009ef229cea8'},
    'endpointDiagnosis58': {'path': 'docs/evidence/rider-rebuild/selected-anatomical-hoodie-fit58/endpoint55-diagnosis.json', 'sha256': '284c233eaf438334ebaca96c53fd03a2ca43dc358d4db848c559419d4da66421'},
    'original47Arrays': {'path': 'harness/out/rider-rebuild/selected-proximal-fit-review54/original01/actual-hoodie-geometry.npz', 'sha256': '370a8bc8569113e422b66d05a8677f6d206628eb362cf731fb6903ac641e06fd'},
    'broad50Arrays': {'path': 'harness/out/rider-rebuild/selected-proximal-fit-review54/registered01/actual-hoodie-geometry.npz', 'sha256': 'f158094abeffce39b20038f10b2526c4fdd5890fe91612cb43eaf6ff8227fdf3'},
    'tangent54': {'path': 'assets/blender/rider-rebuild/selected-proximal-fit-review54/tangent.py', 'sha256': '08b96261f8ae752e48ae06696822247a45f8d5a92bccbe34420c011f54b28a43'},
    'sourcePair49': {'path': 'docs/evidence/rider-rebuild/selected-sleeve-support49/source-pair01.json', 'sha256': 'c1b7999f62f8f7172bba59bc9aa0027067d102835c3b865fc5bd3f6276e076da'}}
STAGE = {'name': 'EXACT_SOURCE_INTAKE'}


def read(row): return json.loads(checked(row).read_text())


def module(row, name):
    spec = importlib.util.spec_from_file_location(name, checked(row))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def freeze(output):
    output = Path(output).resolve(); assert output.is_relative_to(HERE) and not output.exists()
    frozen = read(SOURCE47)
    for row in frozen['pins'].values(): checked(row)
    config = {**frozen, 'sourceInput47': SOURCE47,
        'operation': 'ONE_ORDERED_ANATOMICAL_C2_SELECTED_HOODIE_FIT',
        'retired45mmRepairGateClaimed': False, 'pins': {**frozen['pins'],
            'component64': pin(__file__), 'cage64': pin(HERE/'cage.py'),
            'wrapper47': WRAPPER47, **{k: pin(HERE/v) for k, v in LOCAL.items()}, **REFERENCE}}
    write(output, config); print(json.dumps({'input': pin(output), 'nativeRunExecuted': False}))


def source_gate(config):
    assert config['sourceInput47'] == SOURCE47 and config['acceptedArt'] is False
    assert config['retired45mmRepairGateClaimed'] is False
    original = read(SOURCE47)
    assert config['field'] == original['field']
    assert all(config['pins'][k] == v for k, v in original['pins'].items())
    assert config['pins']['component64'] == pin(__file__)
    assert config['pins']['cage64'] == pin(HERE/'cage.py')
    assert config['pins']['wrapper47'] == WRAPPER47
    assert all(config['pins'][k] == pin(HERE/v) for k, v in LOCAL.items())
    assert all(config['pins'][k] == v for k, v in REFERENCE.items())
    for row in config['pins'].values(): checked(row)
    receipt = read(config['pins']['gloveReceipt']); c47['intake_gate'](receipt)
    return receipt


def transformed_source():
    wrapper = runpy.run_path(str(checked(WRAPPER47)))
    source = wrapper['transformed_source']()
    marker = '    surgery = B.Surgery(hoodie, source)\n'
    assert source.count(marker) == 1
    source = source[:source.index(marker)]+'    build({**globals(), **locals()})\n'
    old = "ROOT/'harness/out/rider-rebuild/selected-sleeve-component47'"
    assert source.count(old) == 1
    return wrapper, source.replace(old, "ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit64'")


def invariant(obj, faces, author, np):
    mesh = obj.data
    weights = hashlib.sha256()
    for vertex in mesh.vertices:
        weights.update(struct.pack('<I', len(vertex.groups)))
        for group in vertex.groups: weights.update(struct.pack('<If', group.group, group.weight))
    uv = {}
    for layer in mesh.uv_layers:
        values = np.empty((len(mesh.loops), 2), np.float32); layer.data.foreach_get('uv', values.ravel())
        uv[layer.name] = hashlib.sha256(values.tobytes()).hexdigest()
    attrs = {}
    for a in mesh.attributes:
        if not a.name.startswith('_'): continue
        assert a.data_type in {'INT', 'FLOAT', 'FLOAT_VECTOR'}, ('Unclassified source identity field', a.name, a.data_type)
        width = 3 if a.data_type == 'FLOAT_VECTOR' else 1
        values = np.empty((len(a.data), width), np.int32 if a.data_type == 'INT' else np.float32)
        a.data.foreach_get('vector' if width == 3 else 'value', values.ravel())
        attrs[a.name] = {'domain': a.domain, 'type': a.data_type,
                        'sha256': hashlib.sha256(values.tobytes()).hexdigest()}
    material = np.empty(len(mesh.polygons), np.int32); mesh.polygons.foreach_get('material_index', material)
    smooth = np.empty(len(mesh.polygons), bool); mesh.polygons.foreach_get('use_smooth', smooth)
    return {'vertices': len(mesh.vertices), 'triangles': len(faces),
        'topology': hashlib.sha256(faces.tobytes()).hexdigest(), 'weights': weights.hexdigest(),
        'uv': uv, 'identityAttributes': attrs,
        'materialIndices': hashlib.sha256(material.tobytes()).hexdigest(),
        'smoothFlags': hashlib.sha256(smooth.tobytes()).hexdigest(),
        'metadata': c47['canonical'](c47['metadata'](obj, author['packed_maps']))}


def corner_normals(obj, np):
    values = np.empty((len(obj.data.corner_normals), 3), np.float32)
    obj.data.corner_normals.foreach_get('vector', values.ravel())
    return values


def build(context):
    c = context; np = c['np']; bpy = c['bpy']; config = c['config']
    source_gate(config); cage = module(config['pins']['cage64'], 'anatomical64_cage')
    target_helper = module(config['pins']['targets64'], 'anatomical64_targets')
    hoodie = c['hoodie']; mesh = hoodie.data
    original = c['B'].A['points'](hoodie)[1]; faces = c['B'].A['faces'](hoodie)
    frozen = np.load(checked(config['pins']['original47Arrays']))
    broad = np.load(checked(config['pins']['broad50Arrays']))
    assert np.array_equal(original, frozen['points']) and np.array_equal(faces, frozen['faces'])
    assert np.array_equal(faces, broad['faces']) and len(original) == len(c['source'])
    author = runpy.run_path(str(checked(c['prior']['restHelper'])))
    before = invariant(hoodie, faces, author, np); normals = corner_normals(hoodie, np)
    loop_vertices = np.empty(len(mesh.loops), np.int32); mesh.loops.foreach_get('vertex_index', loop_vertices)
    target = config['field']['clothClearanceM']+config['field']['contactSolveMarginM']
    STAGE['name'] = 'ACTUAL_SOURCE_MERIDIANS_AND_BODY_TARGETS'
    c['failureContext'] = STAGE
    c['progress']('AUTHOR actual selected cavity meridians and anatomical paired section targets64')
    control_points, targets, target_report = target_helper.make(c, original, broad['points'].astype(float),
        faces, c['actual_nearest'](c['bp'], c['bf']), target)
    STAGE['name'] = 'FIXED_ANATOMICAL_C2_CAGE'
    moved, differential, maps, report = cage.fixed_targets(original, control_points, targets,
        config['field']['fieldCellM'], config['field']['maximumDerivativeBound'], c['progress'])
    out = c['out']; out.mkdir(parents=True)
    arrays = {'controlSource': control_points, 'controlTargets': targets, 'mapCount': np.array(len(maps), np.int32)}
    for i, field in enumerate(maps):
        for name in ('origin', 'shape', 'values'): arrays[str(i)+'_'+name] = getattr(field, name)
        arrays[str(i)+'_spacing'] = np.array(field.spacing)
    np.savez_compressed(out/'anatomical-cage.npz', **arrays)
    write(out/'material-targets.json', target_report)
    retained = np.ones(len(faces), bool); removed = {}
    for side in ('L', 'R'):
        xyz, _, _, _, _, scalar, _ = c['B'].source_sleeve_frame(c['source'], c['controls'], side)
        owned = c['ownership']['hands'][side]; data = np.load(checked(owned['arrays']))
        own_side = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
        terminal = np.all(own_side[faces], axis=1) & (scalar[faces].max(1) > owned['upperSourceAxialM'])
        inward = np.isin(np.arange(len(faces)), data['innerSourceFaceIds'])
        inward &= (scalar[faces].min(1) > owned['lowerSourceAxialM']) & (scalar[faces].max(1) < owned['upperSourceAxialM'])
        retained &= ~(terminal | inward)
        removed[side] = {'terminalCutFaces': int(terminal.sum()), 'replacedInwardFaces': int(inward.sum())}
    np.savez_compressed(out/'qualification-inputs.npz', retainedOriginalFaceIds=np.flatnonzero(retained))
    transformed = np.empty_like(normals)
    for start in range(0, len(normals), 16384):
        end = start+16384; inverse = np.linalg.inv(differential[loop_vertices[start:end]])
        vector = np.einsum('nji,nj->ni', inverse, normals[start:end].astype(float))
        length = np.linalg.norm(vector, axis=1)
        transformed[start:end] = np.divide(vector, length[:, None], out=np.zeros_like(vector), where=length[:, None] > 0)
    mesh.vertices.foreach_set('co', moved.astype(np.float32).ravel()); mesh.update()
    mesh.normals_split_custom_set(transformed.tolist()); mesh.update()
    assert c47['canonical'](author['rest'](c['rig'])) == c47['canonical'](c['rest_before'])
    del transformed, normals, arrays, maps, inverse, vector, differential
    STAGE['name'] = 'RAW_NATIVE_SAVE'
    gc.collect(); c['progress']('SAVE selected anatomical64 before full contact/strain qualification')
    native = c47['save_native'](out, 'UNACCEPTED-selected-anatomical-hoodie-fit64.blend', bpy)
    report.update(constructionContactSamplesPassed=False, contactTargetM=target,
        healthyRetainedBoundaryPassed=False, finalActualFullWearerMinimumM=None,
        sourceBoundaryMinimumM=None, sameSpatialMapCarriesBothSourceSheets=True,
        contactQualificationStage='PENDING_SEPARATE_REOPEN', retired45mmRepairGateClaimed=False)
    result = {'acceptedArt': False, 'status': PENDING, 'sourceRecipe': pin(__file__),
        'registrationRecipe': config['pins']['cage64'], 'input': pin(c['config_path']),
        'sourceInput47': SOURCE47, 'sourceIntake47': config['pins']['gloveReceipt'],
        'correctsRejected55': config['pins']['rejected55Failure'],
        'sourceComponentReceipt41': config['pins']['componentReceipt41'],
        'originalSourceGLB': c['prior']['originalHoodie'], 'native': native,
        'sourceVertexCount': len(original), 'sourceTriangleCount': len(faces),
        'scope': sorted(c47['OBJECTS']), 'anatomicalRegistration': report,
        'registrationMaps': pin(out/'anatomical-cage.npz'), 'materialTargets': pin(out/'material-targets.json'),
        'qualificationInputs': pin(out/'qualification-inputs.npz'),
        'scheduledDistalRemovalExcludedFromConstraints': removed,
        'protectedValidationPassed': False, 'sourceInvariantExact': False,
        'topologyAndSourceVertexOrderUnchanged': False, 'exact75RestUnchanged': False,
        'fullReferenceUnchanged': False, 'geometryGatesPassed': False, 'movingReviewPassed': False,
        'nativeStorage': {'compressed': False, 'reopenVerified': False},
        'limits': ['One anatomically ordered C2 construction from original47;50 is an explicitly unaccepted healthy-region reference.',
            'No triangle, wearer mask, inward sheet, UV, PBR or native skin field is replaced.',
            'Saved topology/source fidelity is separate from full contact, triangle relations, and moving appearance.']}
    write(out/'component-raw.json', result)
    assert invariant(hoodie, faces, author, np) == before
    witness = {'protectedGeometry': c['before'], 'rest': c['rest_before'], 'sourceInvariant': before,
        'rebuiltHoodieGeometry': c['geometry'](hoodie),
        'rebuiltCornerNormals': hashlib.sha256(corner_normals(hoodie, np).tobytes()).hexdigest()}
    write(out/'expected-witness.json', witness)
    result['expectedWitness'] = pin(out/'expected-witness.json')
    result['expectedRebuiltHoodieGeometry'] = witness['rebuiltHoodieGeometry']
    write(out/'component-pending.json', result)
    print(json.dumps({'native': native, 'status': PENDING, 'actualContactStillPending': True}), flush=True)


def construct():
    wrapper, source = transformed_source()
    namespace = {'__name__': 'anatomical64_selected_intake', '__file__': str(checked(wrapper['ORIGINAL'])),
        'helper47': wrapper['helper47'], 'ORIGINAL': wrapper['ORIGINAL'], 'WRAPPER': __file__,
        'gc': gc, 'build': build}
    exec(compile(source, namespace['__file__'], 'exec'), namespace)
    try: namespace['main']()
    except Exception as error:
        args = sys.argv[sys.argv.index('--')+1:]
        output = Path(args[1]).resolve()
        if output.is_relative_to(OUT):
            output.mkdir(parents=True, exist_ok=True)
            write(output/'construction-failure.json', {'acceptedArt': False,
                'status': 'UNACCEPTED_ANATOMICAL64_CONSTRUCTION_FAILED',
                'stage': STAGE['name'], 'targetContext': STAGE.get('target'), 'sourceRecipe': pin(__file__),
                'exceptionType': type(error).__name__, 'message': str(error),
                'traceback': traceback.format_exc(), 'rawNativeExists': any(output.glob('*.blend'))})
        raise


def qualify(path, bpy):
    import numpy as np
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    report = json.loads(path.read_text()); assert report['status'] == PENDING
    config = read(report['input']); source_gate(config)
    assert report['sourceRecipe'] == pin(__file__) and report['registrationRecipe'] == config['pins']['cage64']
    expected = read(report['expectedWitness']); prior = read(config['pins']['priorInputs'])
    author, geometry = c47['helpers'](prior)
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False) == {'FINISHED'}
    rig = c47['scoped'](bpy); hoodie = bpy.data.objects['RiderHoodie']
    assert hoodie.matrix_world.is_identity and not hoodie.data.shape_keys
    assert c47['canonical'](author['rest'](rig)) == expected['rest']
    assert set(expected['protectedGeometry']) == c47['PROTECTED']
    for name, value in expected['protectedGeometry'].items(): assert geometry(bpy.data.objects[name]) == value
    assert geometry(hoodie) == expected['rebuiltHoodieGeometry'] == report['expectedRebuiltHoodieGeometry']
    assert hashlib.sha256(corner_normals(hoodie, np).tobytes()).hexdigest() == expected['rebuiltCornerNormals']
    hoodie.data.calc_loop_triangles()
    faces = np.empty((len(hoodie.data.loop_triangles), 3), np.int32)
    hoodie.data.loop_triangles.foreach_get('vertices', faces.ravel())
    assert invariant(hoodie, faces, author, np) == expected['sourceInvariant']
    assert len(hoodie.data.vertices) == report['sourceVertexCount'] and len(faces) == report['sourceTriangleCount']
    checked(report['registrationMaps'])
    qualifier = module(config['pins']['qualification64'], 'anatomical64_qualification')
    qualifier.measure(report, config, hoodie, bpy.data.objects['RiderBody__FullAnatomyReference'], faces, path.parent)
    report.update(status=QUALIFIED, protectedValidationPassed=True, sourceInvariantExact=True,
        topologyAndSourceVertexOrderUnchanged=True, exact75RestUnchanged=True, fullReferenceUnchanged=True,
        protectedGeometryUnchanged=expected['protectedGeometry'],
        protectedValidationStage='SEPARATE_REOPENED_COMPONENT_NATIVE', pendingReceipt=pin(path))
    report['nativeStorage']['reopenVerified'] = True
    write(path.parent/'component-qualified.json', report)


def qualify_receipt(path):
    """Authoritative CPU admission; preservation alone never admits failed fit."""
    path = Path(path).resolve(); assert path.is_relative_to(OUT)
    report = json.loads(path.read_text()); assert report['status'] == QUALIFIED
    config = read(report['input']); source_gate(config)
    assert report['sourceRecipe'] == pin(__file__) and report['registrationRecipe'] == config['pins']['cage64']
    for name in ('native', 'registrationMaps', 'materialTargets', 'qualificationInputs',
                 'expectedWitness', 'pendingReceipt', 'actualTangentAndPair'): checked(report[name])
    pending = read(report['pendingReceipt']); assert pending['status'] == PENDING
    assert pending['native'] == report['native'] and pending['input'] == report['input']
    for name in ('protectedValidationPassed', 'sourceInvariantExact', 'topologyAndSourceVertexOrderUnchanged',
                 'exact75RestUnchanged', 'fullReferenceUnchanged'): assert report[name] is True
    assert report['nativeStorage']['reopenVerified'] is True
    expected = read(report['expectedWitness'])
    assert report['sourceVertexCount'] == expected['sourceInvariant']['vertices'] == 716971
    assert report['sourceTriangleCount'] == expected['sourceInvariant']['triangles'] == 921722
    assert report['expectedRebuiltHoodieGeometry'] == expected['rebuiltHoodieGeometry']
    assert report['protectedGeometryUnchanged'] == expected['protectedGeometry']
    r = report['anatomicalRegistration']; target = config['field']['clothClearanceM']+config['field']['contactSolveMarginM']
    assert r['endpointCorrespondencePassed'] and r['sameSpatialMapCarriesBothSourceSheets']
    assert r['maximumEndpointResidualM'] <= r['nativeCoordinatePrecisionM']
    assert r['continuousMapInjectivityProven'] and r['steps']
    lower = 1.
    for row in r['steps']:
        cert = row['certificate']; bound = cert['globalDisplacementLipschitzUpperBound']
        assert cert['basis'] == 'C2 tensor cubic B-spline'
        assert cert['compactC2ZeroExtensionProven']
        assert 0 <= bound <= config['field']['maximumDerivativeBound'] and bound < 1
        assert cert['positiveJacobianProvenForContinuousField'] and cert['globalMinimumSingularValueLowerBound'] == 1-bound
        lower *= 1-bound
    assert r['globalComposedMinimumSingularValueLowerBound'] == lower and lower > 0
    assert r['constructionContactSamplesPassed'] and r['healthyRetainedBoundaryPassed']
    assert r['contactQualificationStage'] == 'INDEPENDENT_SAVED_NATIVE_REOPEN'
    assert r['contactTargetM'] == target and r['deficientRetainedConstraintCount'] == 0
    assert r['newZeroAreaFromNondegenerateSource'] == 0
    for key in ('finalActualFullWearerMinimumM', 'sourceBoundaryMinimumM'):
        assert r[key] >= target-config['field']['numericalContactToleranceM']
    return report


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze':
        assert len(args) == 2; freeze(args[1])
    elif args[0] == 'qualify':
        assert len(args) == 2
        import bpy
        qualify(args[1], bpy)
    else:
        assert len(args) == 2
        construct()
