"""Pure source qualification for the complete actual rider; no bpy or exports."""
import hashlib
import json
import math
from pathlib import Path

EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
REQUIRED = {'restSurfaceClearanceQualified', 'selfIntersectionQualified',
            'sourceArtworkTransportQualified', 'bodyAndSourceRestValidated'}
FACE_SHA = 'c58e38f94db9c66d29763c679a3f205096b4ab8493eb52f543650b469f89d8cd'
FIELD_SHA = '4c2d53c61d0e0cc820ab64f09c66eb27f3eb2d471949743b2b11e10522ce1023'
STALE_DRIVER_KEYS = {'spineFlexTable', 'poseCalibration', 'adaptiveSpineFlex', 'maxSpineFlexRadians',
                     'palmForwardBike', 'palmNormalBike', 'sourceSHA256', 'calibrationSourceSHA256'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pinned(row):
    assert isinstance(row, dict) and isinstance(row.get('path'), str)
    assert isinstance(row.get('sha256'), str) and len(row['sha256']) == 64
    path = Path(row['path']).resolve()
    assert path.is_file() and sha(path) == row['sha256'], ('Missing/changed actual source pin', str(path))
    return path

def vector(value, count):
    assert isinstance(value, list) and len(value) == count and all(isinstance(x, (int, float)) and math.isfinite(x) for x in value)
    return value

def norm(value): return math.sqrt(sum(x*x for x in value))
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

def validate_frame(frame):
    assert isinstance(frame, list) and len(frame) == 4
    for row in frame: vector(row, 4)
    assert frame[3] == [0, 0, 0, 1], 'Affine sole frame required'
    axes = [[frame[i][j] for i in range(3)] for j in range(3)]
    assert all(abs(norm(axis)-1) < 1e-7 for axis in axes), 'Unit sole axes required; scaling is not a socket frame'
    assert all(abs(dot(axes[i], axes[j])) < 1e-7 for i in range(3) for j in range(i)), 'Orthogonal sole axes required'
    assert abs(dot(axes[0], cross(axes[1], axes[2]))-1) < 1e-7, 'Proper nonreflected sole frame required'
    return axes

def validate_sole_certificate(side, support, receipt, unit):
    assert support['object'] == 'ActualSelectedBoot.'+side
    assert receipt['native']['sha256'] == unit['native']['sha256']
    assert Path(receipt['native']['path']).resolve() == pinned(unit['native'])
    assert receipt['object'] == support['object']
    assert receipt['nativeFrame'] == support['nativeFrame'] and receipt['boneLengthM'] == support['boneLengthM']
    assert receipt['supportPatch'] == support['supportPatch'], 'Manifest patch must match measured actual sole patch'
    assert receipt['gates']['actualOuterSolePatchValidated'] is True and receipt['gates']['properFrameValidated'] is True
    axes = validate_frame(support['nativeFrame'])
    assert 0 < support['boneLengthM'] < .1
    patch = support['supportPatch']
    assert patch['domain'] == 'actual-outer-sole'
    rows, bary = patch['triangleRows'], patch['barycentrics']
    assert rows and len(rows) == len(bary) and all(isinstance(row, int) and row >= 0 for row in rows)
    for weights in bary:
        vector(weights, 3); assert min(weights) >= 0 and abs(sum(weights)-1) < 1e-8
    centre, outward, tangent = [vector(patch[k], 3) for k in ('pointNative', 'outwardNormalNative', 'forwardTangentNative')]
    assert abs(norm(outward)-1) < 1e-7 and abs(norm(tangent)-1) < 1e-7 and abs(dot(outward,tangent)) < 1e-7
    assert max(abs(centre[i]-support['nativeFrame'][i][3]) for i in range(3)) < 1e-8
    for local, wanted in [(support['outwardNormalInFrame'], outward), (support['forwardTangentInFrame'], tangent)]:
        vector(local, 3); assert abs(norm(local)-1) < 1e-7
        actual = [sum(axes[j][i]*local[j] for j in range(3)) for i in range(3)]
        assert max(abs(actual[i]-wanted[i]) for i in range(3)) < 1e-7, 'Sole frame disagrees with measured patch axes'

def validate_digit_controls(receipt, rig_sha, specification, motion_receipt):
    assert receipt['rigNativeSHA256'] == rig_sha, 'Digit controls must derive from this corrected rig'
    assert receipt['qualification']=='INDEPENDENT_SMALL_SKIN_CURL_SIGN_VERIFIED_MOVING_ART_PENDING'
    assert receipt.get('gates',{}).get('jointRangeValidated') is not True, 'Declared limits cannot claim final range qualification'
    assert motion_receipt['native']['sha256']==rig_sha
    assert motion_receipt['exactSourceGeometryIDsAndOutsideFields'] is True
    signs={(row['side'],row['digit']):row for row in motion_receipt['smallCurlSkinSigns']}
    motions={row['pose']:row for row in motion_receipt['movingFields']}
    assert set(receipt['digitFlex']) == {'left', 'right'}
    for side in ('left', 'right'):
        native_side='L' if side=='left' else 'R'
        names = {specification['jointNames'][identity] for chain in specification['hands'][side]['digits'].values() for identity in chain}
        assert len(names) == 15 and set(receipt['digitFlex'][side]) == names, 'All corrected finger controls required'
        motion=motions[native_side+'-whole-hand-curl']
        parity=motion['nativeFourVsLinearEvaluatorMaximumM']
        assert isinstance(parity,(int,float)) and math.isfinite(parity) and 0<=parity<3e-6
        rotations={row['joint']:row for row in motion['rotations']}
        assert len(motion['rotations'])==15 and set(rotations)==names
        for digit in specification['hands'][side]['digits']:
            displacement=signs[native_side,digit]['smallCurlMeanSkinDisplacementTowardPalmM']
            assert isinstance(displacement,(int,float)) and math.isfinite(displacement) and displacement>0
        for row in receipt['digitFlex'][side].values():
            axis = vector(row['axisLocal'], 3)
            assert abs(norm(axis)-1) < 1e-6 and 0 < row['maxRadians'] <= math.pi
        for name, row in rotations.items():
            assert row['axisLocal']==receipt['digitFlex'][side][name]['axisLocal'], 'Measured motion must use these exact new control axes'
            assert math.isfinite(row['radians']) and 0<row['radians']<=receipt['digitFlex'][side][name]['maxRadians']

def validate_body_operator(receipt, rig_native, actual_rows=None):
    """Bind a measured native/export operator; static triangulation is allowed."""
    assert receipt['native']['sha256'] == rig_native['sha256']
    assert Path(receipt['native']['path']).resolve() == Path(rig_native['path']).resolve()
    assert receipt['exactSourceGeometryIDsAndOutsideFields'] is True
    assert receipt['exportTriangleWindingAndOriginalPolygonLoopCornerLineageExact'] is True
    lineage = receipt['nativeTriangulationLineage']
    assert lineage['everyTriangleAndUVCornerHasOriginalPolygonLoopAncestry'] is True
    assert isinstance(lineage['triangles'], int) and lineage['triangles'] > 0
    assert isinstance(lineage['sourcePolygons'], int) and lineage['sourcePolygons'] > 0
    assert isinstance(lineage['sourceUVLayer'], str) and lineage['sourceUVLayer']
    rows = receipt['bodyModifierOperators']
    assert isinstance(rows, list) and 1 <= len(rows) <= 2
    assert [row['index'] for row in rows] == list(range(len(rows))), 'Ordered native modifier indices required'
    assert sum(row['type']=='ARMATURE' for row in rows) == 1
    assert sum(row['type']=='TRIANGULATE' for row in rows) <= 1
    assert all(row['type'] in {'ARMATURE','TRIANGULATE'} for row in rows), 'Unsupported prepared body deformation operator'
    assert len({row['name'] for row in rows}) == len(rows)
    for row in rows:
        assert isinstance(row['name'], str) and row['name']
        options = row['options']
        assert options['show_viewport'] is True and options['show_render'] is True
        if row['type']=='ARMATURE':
            assert options['use_deform_preserve_volume'] is False, 'GPU FOUR linear operator required'
            assert options['use_vertex_groups'] is True and options['use_bone_envelopes'] is False
            assert options['use_multi_modifier'] is False and options['vertex_group']==''
            assert options['invert_vertex_group'] is False
        else:
            assert options['quad_method'] in {'BEAUTY','FIXED','FIXED_ALTERNATE','SHORTEST_DIAGONAL','LONGEST_DIAGONAL'}
            assert options['ngon_method'] in {'BEAUTY','CLIP'}
            assert isinstance(options['min_vertices'], int) and options['min_vertices'] >= 4
            if 'keep_custom_normals' in options: assert isinstance(options['keep_custom_normals'], bool)
    if actual_rows is not None:
        assert actual_rows == rows, 'Prepared native modifier order/options differ from independent proof'
    return rows

def validate_manifest(manifest, root):
    assert set(manifest) >= {'rigMaster', 'units', 'baseContract', 'faceRecipe', 'fieldRecipe', 'soleSupport', 'correctedDigitControls', 'preparedBodyOperator'}
    paths = {key: pinned(manifest[key]) for key in ('rigMaster', 'baseContract', 'faceRecipe', 'fieldRecipe', 'correctedDigitControls', 'preparedBodyOperator')}
    operator_receipt = json.loads(paths['preparedBodyOperator'].read_text())
    validate_body_operator(operator_receipt, manifest['rigMaster'])
    pinned(operator_receipt['nativeTriangulationLineage']['arrays'])
    assert paths['faceRecipe'] == root/'assets/blender/rider-rebuild/construction02/build-selected-face01.py' and sha(paths['faceRecipe']) == FACE_SHA
    assert paths['fieldRecipe'] == root/'assets/blender/rider-rebuild/construction02/build-selected-rider01.py' and sha(paths['fieldRecipe']) == FIELD_SHA
    contract = json.loads(paths['baseContract'].read_text())
    assert not STALE_DRIVER_KEYS.intersection(contract['driver']), 'Old source-specific pose calibration cannot enter a changed-rig assembly'
    assert len(contract['specification']['jointNames']) == 75
    units = manifest['units']
    assert set(name for unit in units for name in unit['objects']) == EXPECTED-{'RiderBody'}
    assert sum(len(unit['objects']) for unit in units) == 6
    qualifications, by_object = [], {}
    for unit in units:
        native, qualification = pinned(unit['native']), pinned(unit['independentQualification'])
        receipt = json.loads(qualification.read_text())
        assert receipt['native']['sha256'] == unit['native']['sha256'] and Path(receipt['native']['path']).resolve() == native
        assert all(receipt['gates'].get(gate) is True for gate in REQUIRED)
        assert set(receipt['objects']) == set(unit['objects'])
        assert set(receipt['objectGeometryUVAndFieldsSHA256']) == set(unit['objects'])
        for name in unit['objects']: by_object[name] = unit
        qualifications.append(receipt)
    assert set(manifest['soleSupport']) == {'L','R'}
    sole_receipts = {}
    for side, support in manifest['soleSupport'].items():
        measurement = pinned(support['independentMeasurement'])
        receipt = json.loads(measurement.read_text())
        validate_sole_certificate(side, support, receipt, by_object['ActualSelectedBoot.'+side])
        sole_receipts[side] = receipt
    digit_receipt = json.loads(paths['correctedDigitControls'].read_text())
    motion_path=pinned(digit_receipt['smallCurlSignProof'])
    motion_receipt=json.loads(motion_path.read_text())
    assert motion_receipt['native']==operator_receipt['native'], 'Digit motion and body operator must share the exact native master'
    validate_digit_controls(digit_receipt, manifest['rigMaster']['sha256'], contract['specification'], motion_receipt)
    return {'paths': paths, 'baseContract': contract, 'qualifications': qualifications,
            'soleReceipts': sole_receipts, 'digitReceipt': digit_receipt, 'bodyOperatorReceipt': operator_receipt}

def recheck_manifest_pins(manifest):
    for key in ('rigMaster','baseContract','faceRecipe','fieldRecipe','correctedDigitControls','preparedBodyOperator'): pinned(manifest[key])
    operator_receipt = json.loads(pinned(manifest['preparedBodyOperator']).read_text())
    pinned(operator_receipt['nativeTriangulationLineage']['arrays'])
    digit_receipt=json.loads(pinned(manifest['correctedDigitControls']).read_text())
    pinned(digit_receipt['smallCurlSignProof'])
    for unit in manifest['units']:
        pinned(unit['native']); pinned(unit['independentQualification'])
    for support in manifest['soleSupport'].values(): pinned(support['independentMeasurement'])
