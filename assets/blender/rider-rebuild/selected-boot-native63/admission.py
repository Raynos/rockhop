"""Exact actual62 admission; verifies immutable arrays and both fan-closure rounds."""
import hashlib
import json
from pathlib import Path
import re

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
INPUT_BASE = ROOT/'harness/out/rider-rebuild/selected-boot-closure62'
OUTPUT_BASE = ROOT/'harness/out/rider-rebuild/selected-boot-native63'
RECEIPT = INPUT_BASE/'candidate01/constructor.json'
RECEIPT_SHA = 'e264a3df52483c996b0f298b6174a5730766ea2ef07465bf36293fddf199fc52'
CONSTRUCTOR62 = ROOT/'assets/blender/rider-rebuild/selected-boot-closure62/construct.mjs'
CONSTRUCTOR62_SHA = '56ac49d3d2001f65ea39bb6d151768e8b9626c8c192bf1ed90fa03ffaefa42cc'
CLOSURE62 = CONSTRUCTOR62.with_name('closure.mjs')
CLOSURE62_SHA = '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'
CONSTRUCTOR59 = ROOT/'assets/blender/rider-rebuild/selected-boot-fan59/construct.mjs'
CONSTRUCTOR59_SHA = 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'
CONSTRUCTOR37 = ROOT/'assets/blender/rider-rebuild/selected-production-constructor37/construct.mjs'
CONSTRUCTOR37_SHA = '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'
FAN_CENSUS = ROOT/'docs/evidence/rider-rebuild/selected-boot-fan59/fan-census.json'
FAN_CENSUS_SHA = '46b48498db71d774e9eb1e98793e0eec0f8d58b2b8e8b8a070edddafb12ec6ce'
SEED_PROTECTION_SHA = '4d1235558a67ac3a4d7c3f6e51d66bf99fa65291ec57fb4bde8c542716c61129'
FINAL_PROTECTION_SHA = '77e83c0a4595a787a4c7c0f230a6754b43049d9f94b8830be52ac8e39423cb30'
FINAL_CANDIDATE_SHA = '871388caea9ef810f3896e436f7a1035d186ab3882da83312fcaa1df5281ea73'
CENSUS35 = ROOT/'harness/out/rider-rebuild/selected-production-census35/bootL01/census.json'
CENSUS35_SHA = '0e1d5780eeea975fae6c534fc7b348894490c33cc3911d0e090cdb4c723507af'
POLICY46 = ROOT/'harness/out/rider-rebuild/selected-production-allocation46/candidate01/constructor.json'
POLICY46_SHA = '624affb3b59053d6bdee32fb3283c6b2ce23ff3d849c3fe0dd9669ec9319f3c8'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576): h.update(block)
    return h.hexdigest()


def pin(path, expected):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT) and re.fullmatch('[a-f0-9]{64}', expected), 'Invalid reviewed pin'
    assert sha(path) == expected, ('Pinned input changed', str(path))
    return {'path': str(path.relative_to(ROOT)), 'sha256': expected}


def array_package(row):
    path = ROOT/row['path']; pin(path, row['sha256']); raw = path.read_bytes()
    result = {}; offset = 0
    for name, item in row['layout'].items():
        dtype = np.dtype(item['dtype'])
        assert dtype in [np.dtype('<f4'), np.dtype('<i4'), np.dtype('<u4')]
        count = item.get('count', int(np.prod(item.get('shape', []))))
        assert isinstance(count, int) and count >= 0
        assert item['byteOffset'] == offset and item['byteLength'] == count*dtype.itemsize
        assert offset+item['byteLength'] <= len(raw)
        result[name] = np.frombuffer(raw, dtype=dtype, count=count, offset=offset)
        offset += item['byteLength']
    assert offset == len(raw), 'Unreported array bytes'
    return result


def oriented_key(face):
    face = tuple(int(v) for v in face)
    return min(face, face[1:]+face[:1], face[2:]+face[:2])


def verify_arrays(source, candidate, returned, protection, receipt):
    sp = source['positions'].reshape(-1, 3); sf = source['triangles'].reshape(-1, 3)
    p = candidate['positions'].reshape(-1, 3); f = candidate['triangles'].reshape(-1, 3)
    original = candidate['originalVertexIds']; k = len(receipt['groupNames'])
    assert len(p) == receipt['targetVertices'] and len(f) == receipt['targetTriangles']
    assert len(original) == len(p) and len(np.unique(original)) == len(original)
    assert np.all(original >= 0) and np.all(original < len(sp)), 'Original ordinal escaped source'
    assert np.all(f >= 0) and np.all(f < len(p))
    assert np.array_equal(p, sp[original]), 'Original positions changed'
    assert np.array_equal(candidate['namedWeights'].reshape(len(p), k), source['namedWeights'].reshape(len(sp), k)[original]), 'Original named fields changed'
    original_faces = original[f]
    assert np.array_equal(returned['triangles'], original_faces.ravel()), 'Returned index ancestry differs from candidate'
    cross = np.cross(p[f[:, 1]].astype(float)-p[f[:, 0]], p[f[:, 2]].astype(float)-p[f[:, 0]])
    assert np.isfinite(cross).all() and np.all(np.linalg.norm(cross, axis=1) > 0), 'Degenerate candidate face'
    assert len(candidate['faceMaterialIds']) == len(f)
    centers = protection['centerOriginalVertexIds']; required_face_ids = protection['requiredSourceFaceIds']
    assert np.all(centers < len(sp)) and np.array_equal(centers, np.unique(centers))
    assert np.all(np.isfinite(p)) and np.all(np.isfinite(candidate['namedWeights']))
    assert np.all(required_face_ids < len(sf))
    source_center_mask = np.zeros(len(sp), bool); source_center_mask[centers] = True
    actual_required_faces = np.flatnonzero(source_center_mask[sf].any(axis=1))
    assert np.array_equal(actual_required_faces, required_face_ids), 'Incomplete source center-fan certificate'
    required_vertices = np.unique(sf[required_face_ids])
    assert np.array_equal(required_vertices, protection['lockedOriginalVertexIds'])
    assert np.isin(required_vertices, original).all(), 'Protected original vertex absent'
    assert np.isin(required_vertices, candidate['lockedOriginalVertexIds']).all(), 'Protected vertex lock omitted'
    mask = source_center_mask[original_faces].any(axis=1)
    actual = [oriented_key(row) for row in original_faces[mask]]
    expected = {oriented_key(row): int(i) for i, row in zip(required_face_ids, sf[required_face_ids])}
    assert len(expected) == len(required_face_ids)
    assert len(actual) == len(set(actual)), 'Duplicate protected center face'
    assert set(actual) == set(expected), 'Exact oriented source fan changed'
    for target_face, key in zip(np.flatnonzero(mask), actual):
        assert candidate['faceMaterialIds'][target_face] == source['faceMaterialIds'][expected[key]], 'Protected source material changed'
    all_edges = set()
    for row in original_faces:
        for a, b in zip(row, np.roll(row, -1)): all_edges.add(tuple(sorted((int(a), int(b)))))
    required_edges = {tuple(map(int, row)) for row in protection['requiredEdgesOriginal'].reshape(-1, 2)}
    source_edges = {tuple(sorted((int(a), int(b)))) for row in sf[required_face_ids]
                    for a, b in zip(row, np.roll(row, -1))}
    assert required_edges == source_edges, 'Incomplete source fan-edge certificate'
    assert len(required_edges)*2 == len(protection['requiredEdgesOriginal'])
    declared_edges = {tuple(map(int, row)) for row in candidate['requiredEdgesOriginal'].reshape(-1, 2)}
    assert required_edges <= declared_edges <= all_edges, 'Required protected edge omitted'
    return {'exactOriginalPositionsAndNamedFields': True, 'exactReturnedOriginalIndices': True,
            'protectedCenters': len(centers), 'protectedVertices': len(required_vertices),
            'exactOrientedSourceFaces': len(expected), 'protectedEdges': len(required_edges),
            'protectedFaceMaterialsExact': True, 'passed': True}


def frozen_inputs():
    for path, digest in [(CONSTRUCTOR62, CONSTRUCTOR62_SHA), (CLOSURE62, CLOSURE62_SHA),
                         (CONSTRUCTOR59, CONSTRUCTOR59_SHA), (CONSTRUCTOR37, CONSTRUCTOR37_SHA),
                         (FAN_CENSUS, FAN_CENSUS_SHA), (CENSUS35, CENSUS35_SHA), (POLICY46, POLICY46_SHA)]:
        pin(path, digest)
    return tuple(json.loads(path.read_text()) for path in [CENSUS35, FAN_CENSUS, POLICY46])


def receipt_metadata(receipt, census, seed, policy_receipt):
    assert receipt['status'] == 'UNACCEPTED_SCENE_BUDGET_PENDING' and receipt['acceptedArt'] is False
    assert receipt['candidateAttempts'] == 2 and receipt['recipeSHA256'] == CONSTRUCTOR62_SHA
    assert receipt['closureRecipeSHA256'] == CLOSURE62_SHA
    assert receipt['constructorAncestry'] == pin(CONSTRUCTOR37, CONSTRUCTOR37_SHA)
    assert receipt['fanConstructorAncestry'] == pin(CONSTRUCTOR59, CONSTRUCTOR59_SHA)
    assert receipt['initialFanCensus'] == pin(FAN_CENSUS, FAN_CENSUS_SHA)
    assert receipt['census'] == pin(CENSUS35, CENSUS35_SHA)
    assert receipt['censusSourcePins'] == census['sourcePins']
    assert receipt['sourceArrayPackage'] == census['sourceArrayPackage']
    assert receipt['groupNames'] == census['sourceArrayPackage']['groupNames']
    assert receipt['policy'] == policy_receipt['policy']
    assert receipt['originalTopology'] == policy_receipt['topology']
    assert receipt['attributes'] == policy_receipt['attributes']
    assert receipt['attributeWeights'] == policy_receipt['attributeWeights']
    assert 'topology' not in receipt, 'Constructor62 schema must retain originalTopology'
    assert receipt['simplificationTargetIsSoft'] is True and receipt['simplificationTargetTriangles'] == 8000
    assert receipt['simplificationTargetReached'] == (receipt['targetTriangles'] <= 8000)
    assert receipt['sceneBudgetPassed'] is False and receipt['allocationPassed'] is False
    assert receipt['geometricQualification'] == 'CPU_VERTEX_NORMAL_PASSED_NATIVE_GEOMETRY_PENDING'
    for key in ['bakeCompleted', 'movingReviewPassed', 'devicePassed']: assert receipt[key] is False
    for key in ['sourceInputBytesUnchanged', 'exactOriginalPositionsAndNamedFields']: assert receipt[key] is True
    for key in ['sourceVertices', 'sourceTriangles']: assert receipt[key] == census[key]
    fixed = receipt['fixedPoint']; rows = fixed['iterations']
    assert fixed['complete'] is True and fixed['minimumNormalDot'] == 0.25
    assert len(rows) == receipt['candidateAttempts']
    assert rows[0]['protection']['sha256'] == seed['protection']['sha256'] == SEED_PROTECTION_SHA
    assert rows[-1]['protection']['sha256'] == FINAL_PROTECTION_SHA
    assert rows[-1]['candidate']['sha256'] == FINAL_CANDIDATE_SHA
    assert receipt['finalFanProtection'] == rows[-1]['protection']
    for key in ['candidate', 'returnedOriginalIndices', 'fanProtection', 'fanRetention',
                'targetTriangles', 'targetVertices', 'approximateCombinedErrorM', 'vertexNormalCensus']:
        assert receipt[key] == rows[-1][key], ('Final iteration differs', key)
    for i, row in enumerate(rows):
        final = i == len(rows)-1
        assert row['iteration'] == i+1
        assert np.isfinite(row['approximateCombinedErrorM']) and row['approximateCombinedErrorM'] >= 0
        assert row['status'] == ('CPU_NORMAL_FIXED_POINT_UNACCEPTED' if final else 'REQUIRES_MORE_SOURCE_FAN_CONSTRAINTS')
        retained = row['fanRetention']; normal = row['vertexNormalCensus']
        assert retained['passed'] is True
        assert retained['requiredSourceFaces'] == retained['actualProtectedIncidentFaces'] == row['fanProtection']['exactRequiredSourceFaces']
        assert retained['missingCount'] == retained['unexpectedCount'] == retained['duplicateFaces'] == 0
        assert retained['firstMissingOrientedTriangles'] == retained['firstUnexpectedOrientedTriangles'] == []
        assert normal['threshold'] == 0.25 and normal['undefinedNormals'] == 0
        assert normal['verticesExamined'] == row['targetVertices'] and normal['trianglesExamined'] == row['targetTriangles']
        assert np.isfinite(normal['minimumNormalDot'])
        assert normal['failingVertices'] == len(normal['failures'])
        assert normal['passed'] is final and (normal['minimumNormalDot'] >= 0.25) is final
        if final:
            assert normal['failures'] == []
        else:
            assert normal['failures'] and row['addedOriginalFanCenters']
            assert sorted({failure['originalVertexId'] for failure in normal['failures']}) == row['addedOriginalFanCenters']
            for failure in normal['failures']:
                assert np.isfinite(failure['normalDot']) and failure['normalDot'] < 0.25
                assert 0 <= failure['targetVertexId'] < row['targetVertices']
                assert 0 <= failure['originalVertexId'] < receipt['sourceVertices']


def verify_round(source, row, group_names, previous=None):
    packages = {}
    expected_layouts = {
        'candidate': ['positions', 'triangles', 'originalVertexIds', 'namedWeights',
                      'faceMaterialIds', 'requiredEdgesOriginal', 'lockedOriginalVertexIds'],
        'returnedOriginalIndices': ['triangles'],
        'protection': ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds', 'requiredEdgesOriginal']}
    for name, layout in expected_layouts.items():
        assert (ROOT/row[name]['path']).resolve().parent == RECEIPT.parent, 'Package outside exact actual62 directory'
        assert list(row[name]['layout']) == layout
        packages[name] = array_package(row[name])
    protection = packages['protection']; candidate = packages['candidate']
    checked = verify_arrays(source, candidate, packages['returnedOriginalIndices'], protection,
                            dict(row, groupNames=group_names))
    declared = row['fanProtection']
    for key, value in [('protectedCenters', checked['protectedCenters']), ('originalFanVertices', checked['protectedVertices']),
                       ('exactRequiredSourceFaces', checked['exactOrientedSourceFaces']), ('originalFanEdges', checked['protectedEdges']),
                       ('totalLockedVertices', len(candidate['lockedOriginalVertexIds'])),
                       ('totalRequiredEdges', len(candidate['requiredEdgesOriginal'])//2)]:
        assert declared[key] == value, ('Protected counts changed', key)
    # This exact source has no pre-existing boundary/material/coincident locks.
    assert np.array_equal(protection['lockedOriginalVertexIds'], candidate['lockedOriginalVertexIds'])
    assert np.array_equal(protection['requiredEdgesOriginal'], candidate['requiredEdgesOriginal'])
    prior_locked = np.array([], dtype=np.uint32) if previous is None else previous['lockedOriginalVertexIds']
    assert declared['addedLocks'] == len(np.setdiff1d(protection['lockedOriginalVertexIds'], prior_locked))
    for failure in row['vertexNormalCensus']['failures']:
        assert candidate['originalVertexIds'][failure['targetVertexId']] == failure['originalVertexId']
    if previous is not None:
        for key in ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds']:
            assert np.isin(previous[key], protection[key]).all(), ('Non-monotone protection', key)
        old_edges = set(map(tuple, previous['requiredEdgesOriginal'].reshape(-1, 2)))
        assert old_edges <= set(map(tuple, protection['requiredEdgesOriginal'].reshape(-1, 2)))
    return checked, protection


def verify_growth(previous, protection, prior_row):
    expected_centers = np.union1d(previous['centerOriginalVertexIds'], prior_row['addedOriginalFanCenters'])
    assert np.array_equal(expected_centers, protection['centerOriginalVertexIds']), 'Closure did not add every and only failing fan'
    assert prior_row['nextProtectedCenters'] == len(expected_centers)


def admit(receipt_path, reviewed_sha, out):
    receipt_path = Path(receipt_path).resolve(); out = Path(out).resolve()
    assert receipt_path == RECEIPT and reviewed_sha == RECEIPT_SHA, 'Exact reviewed actual62 receipt required'
    assert out.is_relative_to(OUTPUT_BASE) and out != OUTPUT_BASE and not out.exists(), 'Fresh native63 output required'
    reviewed_pin = pin(receipt_path, reviewed_sha)
    census, seed, policy_receipt = frozen_inputs()
    receipt = json.loads(receipt_path.read_text()); receipt_metadata(receipt, census, seed, policy_receipt)
    source = array_package(receipt['sourceArrayPackage'])
    seed_arrays = array_package(seed['protection'])
    previous = None; checked = []
    for i, row in enumerate(receipt['fixedPoint']['iterations']):
        verified, protection = verify_round(source, row, receipt['groupNames'], previous)
        if previous is None:
            for key in seed_arrays: assert np.array_equal(seed_arrays[key], protection[key])
        else:
            verify_growth(previous, protection, receipt['fixedPoint']['iterations'][i-1])
        previous = protection
        checked.append(dict(verified, iteration=row['iteration'], candidateSHA256=row['candidate']['sha256']))
    return {'status': 'EXACT_ACTUAL62_ADMITTED_NATIVE_QUALIFICATION_PENDING', 'acceptedArt': False,
        'admissionRecipeSHA256': sha(__file__), 'constructor': reviewed_pin,
        'constructorRecipe': pin(CONSTRUCTOR62, CONSTRUCTOR62_SHA), 'closureRecipe': pin(CLOSURE62, CLOSURE62_SHA),
        'iterationVerification': checked, 'finalCandidateSHA256': FINAL_CANDIDATE_SHA,
        'finalFanProtectionSHA256': FINAL_PROTECTION_SHA, 'sceneBudgetPassed': False,
        'limits': 'Admission only. Frozen native geometry/orientation/skin gates, contact, selected atlas bake and motion remain required.'}
