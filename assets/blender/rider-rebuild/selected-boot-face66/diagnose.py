"""CPU classification of every actual63 face failure; no candidate or native job."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
ADMISSION63 = ROOT/'assets/blender/rider-rebuild/selected-boot-native63/admission.py'
ADMISSION63_SHA = '46a5f5479aaf55c459944a9e4e60fda4347a7b77005e7b3b8b40d393d4b5eccd'
assert hashlib.sha256(ADMISSION63.read_bytes()).hexdigest() == ADMISSION63_SHA
spec = importlib.util.spec_from_file_location('face66_admission63', ADMISSION63)
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
PRODUCTION = ROOT/'harness/out/rider-rebuild/selected-boot-native63/native01/production.json'
PRODUCTION_SHA = 'ba31a23f3489296c97ca02d3e34808cc10e8f869cc1f035d347b148efdba7644'
SAMPLES_SHA = 'a392ee80c46ba2f0caa927b430ef5bb74fe4349eed53c78845dbcd88b7f39eda'
EVIDENCE = ROOT/'docs/evidence/rider-rebuild/selected-boot-face66'


def normals(points, faces):
    cross = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    length = np.linalg.norm(cross, axis=1)
    assert np.isfinite(cross).all() and np.all(length > 0)
    return cross/length[:, None], length/2


def closest(point, triangle):
    """Scale-independent plane projection plus exact three-edge candidates."""
    origin, b, c = triangle
    u, v = b-origin, c-origin; scale = max(np.max(np.abs(u)), np.max(np.abs(v)))
    assert scale > 0
    u, v, q = u/scale, v/scale, (point-origin)/scale
    cross = np.cross(u, v); denominator = cross@cross
    assert denominator > 0
    beta = np.cross(q, v)@cross/denominator
    gamma = np.cross(u, q)@cross/denominator
    coeff = np.array([1-beta-gamma, beta, gamma])
    candidates = []
    if np.all(coeff >= 0): candidates.append(coeff@triangle)
    for i in range(3):
        begin, end = triangle[i], triangle[(i+1) % 3]; edge = end-begin
        assert edge@edge > 0
        candidates.append(begin+np.clip((point-begin)@edge/(edge@edge), 0, 1)*edge)
    distance = np.linalg.norm(np.asarray(candidates)-point, axis=1); index = np.argmin(distance)
    return {'distanceM': float(distance[index]), 'closestPoint': candidates[index].tolist(),
            'planeBarycentric': coeff.tolist(), 'planeProjectionInside': bool(np.all(coeff >= 0))}


def fan_closure(source_faces, count, center_ids):
    centers = np.unique(center_ids).astype(np.uint32)
    assert len(centers) > 0 and np.all(centers < count)
    mask = np.zeros(count, bool); mask[centers] = True
    ids = np.flatnonzero(mask[source_faces].any(axis=1)).astype(np.uint32); faces = source_faces[ids]
    edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    return {'centerOriginalVertexIds': centers, 'lockedOriginalVertexIds': np.unique(faces).astype(np.uint32),
            'requiredSourceFaceIds': ids, 'requiredEdgesOriginal': edges.astype(np.uint32).ravel()}


def verify_report(report, source, candidate, sample_values):
    """Require exhaustive stored-bearing evidence and the complete constraint set."""
    sp = source['positions'].reshape(-1, 3).astype(float); sf = source['triangles'].reshape(-1, 3)
    tp = candidate['positions'].reshape(-1, 3).astype(float); tf = candidate['triangles'].reshape(-1, 3)
    faces = candidate['originalVertexIds'][tf]; sn, _ = normals(sp, sf); tn, _ = normals(tp, tf)
    expected_ids = np.flatnonzero(sample_values['normalDot'] < .25).tolist()
    assert [r['targetFaceId'] for r in report['failures']] == expected_ids, 'Failure census incomplete or reordered'
    source_keys = {a.oriented_key(face): i for i, face in enumerate(sf)}
    required_centers = set(); new_ids = []
    for row in report['failures']:
        i = row['targetFaceId']; bearing = int(sample_values['sourceFaceId'][i])
        assert row['nativeBearingSourceFaceId'] == bearing, 'Actual native bearing changed'
        assert row['originalVertexIds'] == faces[i].tolist()
        assert row['targetPositions'] == tp[tf[i]].tolist()
        assert row['nativeNormalDot'] == float(sample_values['normalDot'][i])
        assert np.float32(row['reproducedNormalDotFloat64']) == np.float32(tn[i]@sn[bearing]) == sample_values['normalDot'][i]
        exact = source_keys.get(a.oriented_key(faces[i]))
        assert row['exactSourceFaceId'] == exact, 'False inherited-face claim'
        if exact is None:
            assert row['classification'] == 'NEW_FACE_NATIVE_NORMAL_FAILURE'
            required_centers.update(faces[i].tolist()); required_centers.update(sf[bearing].tolist()); new_ids.append(i)
        else:
            assert row['classification'] == 'EXACT_INHERITED_ORIENTED_SOURCE_FACE'
            assert row['exactAncestor']['ownSourceNormalDot'] == float(tn[i]@sn[exact])
    proposal = report['proposedConstructionConstraint']
    assert proposal['newTargetFaceIds'] == new_ids
    assert proposal['requestedOriginalFanCenters'] == sorted(required_centers), 'Not all target and bearing fans retained'
    assert report['summary']['failuresClassified'] == len(expected_ids)
    assert report['summary']['newFaces'] == len(new_ids)


def diagnose():
    a.pin(PRODUCTION, PRODUCTION_SHA); a.pin(a.RECEIPT, a.RECEIPT_SHA)
    production = json.loads(PRODUCTION.read_text()); receipt = json.loads(a.RECEIPT.read_text())
    samples = production['sourceSurfaceSamples']['target-face-centroids']; sample_path = ROOT/samples['arrays']['path']
    assert samples['arrays']['sha256'] == SAMPLES_SHA; a.pin(sample_path, SAMPLES_SHA)
    assert production['constructor'] == a.pin(a.RECEIPT, a.RECEIPT_SHA)
    s = a.array_package(receipt['sourceArrayPackage']); c = a.array_package(receipt['candidate'])
    returned = a.array_package(receipt['returnedOriginalIndices'])
    prior = a.array_package(receipt['finalFanProtection'])
    a.verify_arrays(s, c, returned, prior, receipt)
    sp = s['positions'].reshape(-1, 3).astype(float); sf = s['triangles'].reshape(-1, 3)
    tp = c['positions'].reshape(-1, 3).astype(float); tf = c['triangles'].reshape(-1, 3)
    original_faces = c['originalVertexIds'][tf]
    sn, sa = normals(sp, sf); tn, ta = normals(tp, tf)
    donor_vertex_normals = s['vertexNormals'].reshape(-1, 3).astype(float)
    with np.load(sample_path) as values: z = {key: values[key] for key in values.files}
    assert set(z) == {'distanceM', 'normalDot', 'sourceFaceId'}
    assert len(z['normalDot']) == len(tf) == samples['samples']
    assert np.isfinite(z['distanceM']).all() and np.isfinite(z['normalDot']).all()
    assert np.all(z['sourceFaceId'] >= 0) and np.all(z['sourceFaceId'] < len(sf))
    reproduced = np.array([tn[i]@sn[j] for i, j in enumerate(z['sourceFaceId'])], np.float32)
    assert np.array_equal(reproduced, z['normalDot']), 'Recorded native face normal arithmetic not exactly reproduced'
    failed = np.flatnonzero(z['normalDot'] < .25)
    assert len(failed) == samples['normalBelowPoint25Count'] == 95
    assert np.count_nonzero(z['distanceM'] > .001) == samples['over1mmCount'] == 0
    source_lookup = {a.oriented_key(face): i for i, face in enumerate(sf)}
    assert len(source_lookup) == len(sf), 'Duplicate source oriented face requires explicit classification'
    target_lookup = {a.oriented_key(face): i for i, face in enumerate(original_faces)}
    assert len(target_lookup) == len(tf)
    rows = []; new_faces = []
    for target_id in failed:
        target_id = int(target_id); bearing_id = int(z['sourceFaceId'][target_id]); face = original_faces[target_id]
        source_id = source_lookup.get(a.oriented_key(face)); reversed_id = source_lookup.get(a.oriented_key(face[::-1]))
        centroid = tp[tf[target_id]].mean(axis=0); native_query = centroid.astype(np.float32).astype(float)
        inherited = source_id is not None
        row = {'targetFaceId': target_id, 'originalVertexIds': face.tolist(), 'targetPositions': tp[tf[target_id]].tolist(),
               'classification': 'EXACT_INHERITED_ORIENTED_SOURCE_FACE' if inherited else 'NEW_FACE_NATIVE_NORMAL_FAILURE',
               'exactSourceFaceId': source_id, 'reversedSourceFaceId': reversed_id,
               'targetGeometricNormal': tn[target_id].tolist(), 'targetAreaM2': float(ta[target_id]),
               'nativeQueryCentroidFloat64': centroid.tolist(), 'nativeQueryPointFloat32': native_query.tolist(),
               'queryRoundingDisplacementM': float(np.linalg.norm(centroid-native_query)),
               'nativeBearingSourceFaceId': bearing_id, 'nativeBearingOriginalVertexIds': sf[bearing_id].tolist(),
               'nativeBearingPositions': sp[sf[bearing_id]].tolist(), 'nativeBearingNormal': sn[bearing_id].tolist(),
               'nativeBearingAreaM2': float(sa[bearing_id]),
               'nativeBearingRetainedTargetFaceId': target_lookup.get(a.oriented_key(sf[bearing_id])),
               'nativeNormalDot': float(z['normalDot'][target_id]), 'reproducedNormalDotFloat64': float(tn[target_id]@sn[bearing_id]),
               'nativeDistanceM': float(z['distanceM'][target_id]),
               'cpuDistanceToRecordedBearingAtNativeQuery': closest(native_query, sp[sf[bearing_id]]),
               'targetFaceDotOriginalCornerVertexNormals': (donor_vertex_normals[face]@tn[target_id]).tolist(),
               'bearingFaceDotOwnCornerVertexNormals': (donor_vertex_normals[sf[bearing_id]]@sn[bearing_id]).tolist()}
        if inherited:
            assert np.array_equal(sp[sf[source_id]], tp[tf[target_id]])
            source_centroid = sp[sf[source_id]].mean(axis=0)
            assert np.array_equal(centroid, source_centroid)
            row['exactAncestor'] = {'sourcePositionsAndOrderExact': True, 'sourceCentroidExact': True,
                'ownSourceNormalDot': float(tn[target_id]@sn[source_id]),
                'ownSourceCentroidDistanceM': float(np.linalg.norm(source_centroid-centroid)),
                'ownSourceAtNativeRoundedQuery': closest(native_query, sp[sf[source_id]]),
                'sharedVerticesWithActualBearing': sorted(set(sf[source_id].tolist()) & set(sf[bearing_id].tolist())),
                'sourceMaterialExact': bool(s['faceMaterialIds'][source_id] == c['faceMaterialIds'][target_id])}
        else:
            assert reversed_id is None, 'Actual reversal of an existing face needs separate classification'
            new_faces.append(target_id)
        rows.append(row)
    new_faces = np.array(new_faces, dtype=np.int32)
    target_centers = np.unique(original_faces[new_faces]); bearing_centers = np.unique(sf[z['sourceFaceId'][new_faces]])
    requested = np.union1d(target_centers, bearing_centers)
    merged = fan_closure(sf, len(sp), np.union1d(prior['centerOriginalVertexIds'], requested))
    for key in ['centerOriginalVertexIds', 'lockedOriginalVertexIds', 'requiredSourceFaceIds']:
        assert np.isin(prior[key], merged[key]).all()
    # Complete center fans forbid every current failing new triangle; exact inherited faces stay.
    merged_keys = {a.oriented_key(face) for face in sf[merged['requiredSourceFaceIds']]}
    assert all(a.oriented_key(original_faces[i]) not in merged_keys for i in new_faces)
    summary = {'samplesExamined': len(tf), 'recordedDotValuesReproducedExactly': True, 'failuresClassified': len(rows),
               'exactInheritedOrientedSourceFaces': sum(r['exactSourceFaceId'] is not None for r in rows),
               'newFaces': len(new_faces), 'reversedExistingSourceFaces': sum(r['reversedSourceFaceId'] is not None for r in rows),
               'failedDistanceMaximumM': float(z['distanceM'][failed].max()),
               'newTargetFaceCornerCenters': len(target_centers), 'newBearingSourceFaceCornerCenters': len(bearing_centers),
               'unionRequestedCenters': len(requested), 'additionalCenters': len(np.setdiff1d(requested, prior['centerOriginalVertexIds'])),
               'proposedTotalCenters': len(merged['centerOriginalVertexIds']), 'proposedLockedVertices': len(merged['lockedOriginalVertexIds']),
               'proposedExactSourceFaces': len(merged['requiredSourceFaceIds']), 'proposedRequiredEdges': len(merged['requiredEdgesOriginal'])//2,
               'newFaceBearingHasCornerNormalBelowPoint25': sum(min(r['bearingFaceDotOwnCornerVertexNormals']) < .25 for r in rows if r['exactSourceFaceId'] is None),
               'newFaceHasOriginalCornerNormalBelowPoint25': sum(min(r['targetFaceDotOriginalCornerVertexNormals']) < .25 for r in rows if r['exactSourceFaceId'] is None)}
    report = {'status': 'COMPLETE_ACTUAL63_FACE_FAILURE_DIAGNOSIS_UNACCEPTED', 'acceptedArt': False,
        'recipeSHA256': a.sha(__file__), 'production': a.pin(PRODUCTION, PRODUCTION_SHA),
        'constructor': a.pin(a.RECEIPT, a.RECEIPT_SHA), 'sampleArrays': samples['arrays'],
        'sourceArrays': {key: receipt['sourceArrayPackage'][key] for key in ['path', 'sha256']},
        'candidateArrays': {key: receipt['candidate'][key] for key in ['path', 'sha256']},
        'nativeReceipt': production['native'], 'summary': summary, 'failures': rows,
        'proposedConstructionConstraint': {'policy': 'Retain every source fan centered at the original corners of all 94 failing NEW target faces and all their recorded source-bearing faces, union all prior 62 protected fans. Add all failures together, retaining exact oriented source fans/edges/positions/fields. Recompute both full vertex and proper face correspondence metrics on each new original-source reduction; no threshold/flag/error change or isolated-face patch.',
            'newTargetFaceIds': new_faces.tolist(), 'requestedOriginalFanCenters': requested.tolist(),
            'addedOriginalFanCenters': np.setdiff1d(requested, prior['centerOriginalVertexIds']).tolist()},
        'inheritedFinding': 'Target 15560 is exactly source 278671, but native BVH selected adjacent source 278672. Own geometry/centroid is exact and own normal dot is 1. Native float32 query/nearest-point arithmetic produces a nonzero distance on this extremely thin face; stored receipt proves bearing ID, but no nearest-point/native own-face distance was saved. A conditional bearing correction needs bounded native proof, and applies only to exact oriented face ancestry.',
        'newFaceFinding': 'All 94 remaining failures are genuinely new target triangles, not inherited face ties or reversed copies. Their native face-to-bearing dot values reproduce exactly. They omit exact original corner fans, and must remain rejected. Individual wrong-sheet or coarse-chord cause cannot be decided by normal dot alone; preserving both new-face corner fans and bearing-face fans retains the authored surface without guessing replacement bearings.',
        'limits': 'CPU diagnosis and proposed constraints only. No corrected bearing, new simplifier/native job, gate waiver, bake, art or allocation acceptance. The 1mm surface and .25 orientation limits stay unchanged; edge/reverse face stages have not run.'}
    verify_report(report, s, c, z)
    return report, merged


def main():
    report, merged = diagnose(); EVIDENCE.mkdir(parents=True, exist_ok=True)
    raw = bytearray(); layout = {}
    for key, values in merged.items():
        data = values.astype('<u4').tobytes(); layout[key] = {'dtype': '<u4', 'count': values.size, 'byteOffset': len(raw), 'byteLength': len(data)}; raw.extend(data)
    binary = EVIDENCE/'proposed-fan-constraints.bin'; binary.write_bytes(raw)
    report['proposedConstructionConstraint']['arrays'] = dict(a.pin(binary, a.sha(binary)), layout=layout)
    (EVIDENCE/'finding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__': main()
