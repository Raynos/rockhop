"""Bounded actual3667 fan diagnosis and exact source-fan retention certificate.

CPU only. Emits construction constraints and diagnoses the existing candidate;
does not invoke a simplifier, modify a mesh, or qualify production geometry.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
FAN57 = ROOT/'assets/blender/rider-rebuild/selected-boot-fold57/fan.py'
spec = importlib.util.spec_from_file_location('fan59_frozen57', FAN57)
fan = importlib.util.module_from_spec(spec); spec.loader.exec_module(fan)
fan.pin(FAN57, '141a51716ffe65defaca86210789ecde72cc526e5faa516f10609b6c89dfeb82')
PRODUCTION = fan.BASE/'native03/production.json'
PRODUCTION_SHA = '0d5de5443e4688433f5166657921a29a602bbbe7a2a139b760b0e27c8d38b837'
TARGET_ID = 3667
ORIGINAL_ID = 80837
FAILED_DOT = -0.9220517171222511


def oriented_key(triangle):
    triangle = tuple(int(v) for v in triangle)
    return min(triangle, triangle[1:]+triangle[:1], triangle[2:]+triangle[:2])


def edges(faces):
    return sorted({tuple(sorted((int(a), int(b)))) for face in faces for a, b in zip(face, np.roll(face, -1))})


def metrics(data, donor_normal):
    rows = data['incidentFaces']
    normals = np.array([row['geometricNormal'] for row in rows])
    angles = np.array([row['cornerAngleRadians'] for row in rows])
    weighted = angles@normals
    return {'minimumPairwiseFaceNormalDot': float((normals@normals.T).min()),
            'angleWeightedNormalCoherence': float(np.linalg.norm(weighted)/angles.sum()),
            'dotDonorVertexNormal': float(np.array(data['angleWeightedNormal'])@donor_normal)}


def retention(certificate, candidate):
    """Exact requirements, including the whole center fan, not just count/locks."""
    original = candidate['originalVertexIds']; p = candidate['positions'].reshape(-1, 3)
    f = candidate['triangles'].reshape(-1, 3); w = candidate['namedWeights'].reshape(len(p), -1)
    assert len(original) == len(p) and len(np.unique(original)) == len(original)
    assert np.all(f >= 0) and np.all(f < len(p))
    inverse = {int(v): i for i, v in enumerate(original)}
    missing = []; moved = []; altered_fields = []
    for row in certificate['lockedVertices']:
        v = row['originalVertexId']
        if v not in inverse: missing.append(v); continue
        if not np.array_equal(p[inverse[v]], row['position']): moved.append(v)
        if not np.array_equal(w[inverse[v]], row['namedWeights']): altered_fields.append(v)
    actual_original_faces = original[f]
    center_faces = actual_original_faces[(actual_original_faces == certificate['centerOriginalVertexId']).any(axis=1)]
    actual = [oriented_key(t) for t in center_faces]
    required = {oriented_key(t) for t in certificate['requiredOrientedTrianglesOriginal']}
    actual_set = set(actual); actual_edges = set(edges(actual_original_faces))
    result = {'missingOriginalVertices': missing, 'movedOriginalVertices': moved,
              'changedNamedFields': altered_fields,
              'missingEdgesOriginal': [e for e in certificate['requiredEdgesOriginal'] if tuple(e) not in actual_edges],
              'missingCenterTrianglesOriginal': [list(t) for t in sorted(required-actual_set)],
              'unexpectedCenterTrianglesOriginal': [list(t) for t in sorted(actual_set-required)],
              'duplicateCenterTriangles': len(actual)-len(actual_set)}
    result['passed'] = not any(result.values())
    return result


def diagnose():
    constructor_pin = fan.pin(fan.CANDIDATE, fan.CANDIDATE_SHA)
    production_pin = fan.pin(PRODUCTION, PRODUCTION_SHA)
    native = json.loads(PRODUCTION.read_text())
    assert native['failure'] == "AssertionError(('Wrong-facing source correspondence', 'ActualSelectedBoot.L', 3667, -0.9220517171222511))"
    receipt = json.loads(fan.CANDIDATE.read_text())
    source = fan.arrays(receipt['sourceArrayPackage']); candidate = fan.arrays(receipt['candidate'])
    sp = source['positions'].reshape(-1, 3).astype(float); sf = source['triangles'].reshape(-1, 3)
    tp = candidate['positions'].reshape(-1, 3).astype(float); tf = candidate['triangles'].reshape(-1, 3)
    original = candidate['originalVertexIds']; assert int(original[TARGET_ID]) == ORIGINAL_ID
    assert np.array_equal(tp[TARGET_ID], sp[ORIGINAL_ID])
    source_fan = fan.face_fan(sp, sf, ORIGINAL_ID)
    target_fan = fan.face_fan(tp, tf, TARGET_ID, original)
    ids = np.flatnonzero((sf == ORIGINAL_ID).any(axis=1)); required_faces = sf[ids]
    vertices = np.unique(required_faces)
    weights = source['namedWeights'].reshape(len(sp), -1)
    normal = source['vertexNormals'].reshape(-1, 3)[ORIGINAL_ID].astype(float)
    certificate = {'status': 'PROPOSED_EXACT_SOURCE_FAN_CONSTRUCTION_CONSTRAINT_UNACCEPTED',
        'sourceArrays': {'path': receipt['sourceArrayPackage']['path'], 'sha256': receipt['sourceArrayPackage']['sha256']},
        'centerOriginalVertexId': ORIGINAL_ID, 'sourceFaceIds': ids.tolist(),
        'lockedOriginalVertexIds': vertices.tolist(),
        'lockedVertices': [{'originalVertexId': int(v), 'position': sp[v].tolist(),
                            'namedWeights': weights[v].tolist()} for v in vertices],
        'requiredEdgesOriginal': [list(edge) for edge in edges(required_faces)],
        'requiredOrientedTrianglesOriginal': required_faces.tolist(),
        'requireExactCenterIncidentFan': True, 'minimumVertexNormalDot': .25,
        'constructionUse': 'Union these original vertex locks and edge constraints with every existing constructor37 protection before one separately authorized index-only construction. Require this exact oriented incident fan after compaction; locks alone are not proof. Do not splice an overlapping patch into candidate01.',
        'limits': 'One measured donor fold only. Source topology/positions/fields/PBR remain unchanged. Full source/target normal, surface, skin, contact, budget and motion gates remain required; this is not a global fold census or a construction run.'}
    current = retention(certificate, candidate)
    source_metrics = metrics(source_fan, normal); target_metrics = metrics(target_fan, normal)
    assert len(ids) == 7 and len(vertices) == 8
    assert not current['passed'] and len(current['missingOriginalVertices']) == 6
    assert len(current['missingCenterTrianglesOriginal']) == 7
    report = {'status': 'ACTUAL_NATIVE03_FAN_RETENTION_FAILURE_UNACCEPTED', 'acceptedArt': False,
        'production': production_pin, 'constructor': constructor_pin,
        'sourceArrays': certificate['sourceArrays'], 'nativeReceipt': native['native'],
        'targetVertexId': TARGET_ID, 'originalVertexId': ORIGINAL_ID,
        'donorVertexNormal': normal.tolist(), 'nativeRejectedDot': FAILED_DOT,
        'sourceFan': source_fan, 'targetFan': target_fan,
        'sourceMetrics': source_metrics, 'targetMetrics': target_metrics,
        'centerNamedFieldsSource': weights[ORIGINAL_ID].tolist(),
        'centerNamedFieldsTarget': candidate['namedWeights'].reshape(len(tp), -1)[TARGET_ID].tolist(),
        'currentCandidateRetention': current,
        'finding': 'The source already contains a sharply folded seven-face fan. Candidate46 retained only two of its eight vertices and none of its seven triangles; new fan geometry reverses the consistent vertex normal. This is actual source-fan loss, not the prior arbitrary nearest-face comparison.',
        'correction': 'Preserve the exact eight-vertex, fourteen-edge, seven-triangle donor fan as a topology constraint. Keep the source fold, original fields/PBR and 0.25 gate. No shading-normal override, deletion, bearing substitution or simplification parameter sweep.',
        'limits': 'CPU angle weighting reproduces the native rejection within 2.6e-5; Blender float arithmetic differs slightly. No new native run or candidate. The certificate is a bounded supported construction requirement, not proof that all other source folds or scene gates pass.'}
    return report, certificate, source, candidate


if __name__ == '__main__':
    report, certificate, _, _ = diagnose()
    out = ROOT/'docs/evidence/rider-rebuild/selected-boot-fan59'
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [('finding.json', report), ('source-fan-constraint.json', certificate)]:
        (out/name).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['sourceFan', 'targetFan']}, indent=2))
