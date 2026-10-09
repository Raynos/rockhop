"""Pinned, bounded source/target fan evidence for actual native02 vertex 2485."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'harness/out/rider-rebuild/selected-production-allocation46'
CANDIDATE = BASE/'candidate01/constructor.json'
CANDIDATE_SHA = '624affb3b59053d6bdee32fb3283c6b2ce23ff3d849c3fe0dd9669ec9319f3c8'
NATIVE = BASE/'native02/UNACCEPTED-constructor46-before-transfer.blend'
NATIVE_SHA = '85621ef92bc802c0163fbccf9a43bd647a70b62e100257a94b1c68684a475ff2'
PRODUCTION = BASE/'native02/production.json'
PRODUCTION_SHA = '25c00819770ec7c315c3fb3c20fb3fe3072decb4c30d04e95958b88f317bc4fe'
ENGINE = ROOT/'assets/blender/rider-rebuild/selected-rider-production25/author.py'
ENGINE_SHA = 'bc9e03aa6d99eba0d4b5037ceff49424c34ddcde99f0f2aae0f84a5090cbc483'
TARGET_ID = 2485
ORIGINAL_ID = 56390
INHERITED_SOURCE_FACE = 113358
INHERITED_TARGET_FACE = 5011
REJECTED_DOT = -0.9968504702542031


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576): digest.update(block)
    return digest.hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def pin(path, expected):
    assert sha(path) == expected, ('Pinned input changed', str(path))
    return {'path': str(path.relative_to(ROOT)), 'sha256': expected}


def arrays(row):
    pin(ROOT/row['path'], row['sha256'])
    raw = (ROOT/row['path']).read_bytes()
    return {name: np.frombuffer(raw, dtype=item['dtype'],
             count=item.get('count', int(np.prod(item.get('shape', [])))), offset=item['byteOffset'])
            for name, item in row['layout'].items()}


def face_fan(p, f, vertex_id, original_ids=None):
    ids = np.flatnonzero((f == vertex_id).any(axis=1)); result = []
    weighted = np.zeros(3)
    for face_id in ids:
        face = f[face_id]; triangle = p[face]
        cross = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
        length = np.linalg.norm(cross); assert length > 0
        normal = cross/length
        corner = int(np.flatnonzero(face == vertex_id)[0])
        a = triangle[(corner+1) % 3]-triangle[corner]
        b = triangle[(corner+2) % 3]-triangle[corner]
        angle = float(np.arctan2(np.linalg.norm(np.cross(a, b)), a@b))
        weighted += angle*normal
        result.append({'faceId': int(face_id), 'vertexIds': face.tolist(),
                       'originalVertexIds': (face if original_ids is None else original_ids[face]).tolist(),
                       'positions': triangle.tolist(), 'geometricNormal': normal.tolist(),
                       'areaM2': float(length/2), 'cornerAngleRadians': angle})
    weighted /= np.linalg.norm(weighted)
    return {'incidentFaces': result, 'angleWeightedNormal': weighted.tolist()}


def cpu_report():
    constructor_pin = pin(CANDIDATE, CANDIDATE_SHA)
    production_pin = pin(PRODUCTION, PRODUCTION_SHA)
    receipt = json.loads(CANDIDATE.read_text())
    s = arrays(receipt['sourceArrayPackage']); c = arrays(receipt['candidate'])
    sp = s['positions'].reshape(-1, 3).astype(float); sf = s['triangles'].reshape(-1, 3)
    tp = c['positions'].reshape(-1, 3).astype(float); tf = c['triangles'].reshape(-1, 3)
    original = c['originalVertexIds']; assert int(original[TARGET_ID]) == ORIGINAL_ID
    assert np.array_equal(tp[TARGET_ID], sp[ORIGINAL_ID])
    source = face_fan(sp, sf, ORIGINAL_ID); target = face_fan(tp, tf, TARGET_ID, original)
    source_normal = s['vertexNormals'].reshape(-1, 3)[ORIGINAL_ID].astype(float)
    target_normal = np.array(target['angleWeightedNormal'])
    for data in [source, target]:
        for row in data['incidentFaces']:
            row['dotDonorVertexNormal'] = float(np.array(row['geometricNormal'])@source_normal)
    inherited_source = next(row for row in source['incidentFaces'] if row['faceId'] == INHERITED_SOURCE_FACE)
    inherited_target = next(row for row in target['incidentFaces'] if row['faceId'] == INHERITED_TARGET_FACE)
    inherited_exact = inherited_source['originalVertexIds'] == inherited_target['originalVertexIds'] and inherited_source['positions'] == inherited_target['positions']
    assert inherited_exact
    material_exact = int(s['faceMaterialIds'][INHERITED_SOURCE_FACE]) == int(c['faceMaterialIds'][INHERITED_TARGET_FACE])
    assert material_exact
    return {'status': 'CPU_FAN_EVIDENCE_NATIVE_BEARING_UNPROVEN', 'acceptedArt': False,
            'constructor': constructor_pin, 'production': production_pin,
            'sourceArrays': {'path': receipt['sourceArrayPackage']['path'], 'sha256': receipt['sourceArrayPackage']['sha256']},
            'targetVertexId': TARGET_ID, 'originalVertexId': ORIGINAL_ID, 'position': tp[TARGET_ID].tolist(),
            'sourceVertexNormal': source_normal.tolist(), 'sourceFan': source, 'targetFan': target,
            'inheritedSourceFaceId': INHERITED_SOURCE_FACE, 'inheritedTargetFaceId': INHERITED_TARGET_FACE,
            'inheritedFaceExact': inherited_exact, 'inheritedFaceMaterialExact': material_exact,
            'inheritedFaceOriginalVertexIds': inherited_source['originalVertexIds'],
            'inheritedFaceAreaM2': inherited_source['areaM2'],
            'cpuPredictedRejectedDot': float(np.array(inherited_source['geometricNormal'])@target_normal),
            'nativeRejectedDot': REJECTED_DOT, 'consistentVertexNormalDotCPU': float(source_normal@target_normal),
            'limits': 'CPU fan evidence identifies an exactly inherited reversed micro-face, not the native BVH bearing. Native57 must confirm the nearest face/point and Blender vertex normal before changing correspondence. Donor geometry/PBR/fields remain untouched.'}


if __name__ == '__main__':
    out = ROOT/'docs/evidence/rider-rebuild/selected-boot-fold57'
    out.mkdir(parents=True, exist_ok=True)
    report = cpu_report()
    (out/'cpu-fan.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['sourceFan', 'targetFan']}, indent=2))
