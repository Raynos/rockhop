"""Bounded NumPy-only solid classification of the actual49 deepest sample.

No Blender/model construction. Exact full-reference and canonical body meshes
independently supply winding and three transverse ray witnesses.
"""
import json
import runpy
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'diagnose.py'))
checked, pin = h['checked'], h['pin']
CONFIG = json.loads(checked(h['INPUT']).read_text())
ACTUAL = CONFIG['pins']['referenceSamples']
DIAGNOSTIC_PATH = h['ROOT']/'harness/out/rider-rebuild/selected-sleeve-support49/diagnostic01/diagnostic.json'


def solid_witness(points, faces, query, nearest_face):
    triangles = points[faces]
    vectors = triangles-query
    lengths = np.linalg.norm(vectors, axis=2)
    numerator = np.einsum('ij,ij->i', vectors[:, 0], np.cross(vectors[:, 1], vectors[:, 2]))
    denominator = np.prod(lengths, axis=1)
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        denominator += np.einsum('ij,ij->i', vectors[:, i], vectors[:, j])*lengths[:, k]
    winding = np.sum(2*np.arctan2(numerator, denominator))/(4*np.pi)
    e1, e2 = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
    normals = np.cross(e1, e2)
    offset = query-triangles[:, 0]
    rays = []
    for raw in ([1., .371, .193], [-.537, 1., .271], [.191, -.313, 1.]):
        direction = np.asarray(raw); direction /= np.linalg.norm(direction)
        cross = np.cross(direction, e2)
        det = np.einsum('ij,ij->i', e1, cross)
        valid = abs(det) > 1e-14
        inverse = 1/np.where(valid, det, 1.)
        u = np.einsum('ij,ij->i', offset, cross)*inverse
        q = np.cross(offset, e1)
        v = (q@direction)*inverse
        distance = np.einsum('ij,ij->i', e2, q)*inverse
        hit = valid & (u >= 0) & (v >= 0) & (u+v <= 1) & (distance > 0)
        ids = np.flatnonzero(hit); ids = ids[np.argsort(distance[ids])]
        rays.append({'direction': raw, 'positiveHitCount': len(ids),
            'firstHits': [{'triangleId': int(i), 'distanceM': float(distance[i]),
                'barycentric': [float(1-u[i]-v[i]), float(u[i]), float(v[i])],
                'normalDotRay': float(normals[i]@direction/np.linalg.norm(normals[i]))}
                for i in ids[:4]]})
    # Exhaustive Euclidean distance independently checks the BVH witness.
    # Minimum over all three clamped edges plus face interiors is exact.
    closest = np.full(len(faces), np.inf)
    for i, j in ((0, 1), (1, 2), (2, 0)):
        edge = triangles[:, j]-triangles[:, i]
        square = np.einsum('ij,ij->i', edge, edge)
        t = np.einsum('ij,ij->i', query-triangles[:, i], edge)/np.where(square > 0, square, 1)
        candidate = triangles[:, i]+np.clip(t, 0, 1)[:, None]*edge
        closest = np.minimum(closest, np.sum((query-candidate)**2, axis=1))
    nn = np.sum(normals*normals, axis=1)
    signed = np.einsum('ij,ij->i', offset, normals)/np.where(nn > 0, nn, 1)
    projection = query-signed[:, None]*normals
    inside = nn > 0
    for i, j in ((0, 1), (1, 2), (2, 0)):
        side = np.cross(triangles[:, j]-triangles[:, i], projection-triangles[:, i])
        inside &= np.einsum('ij,ij->i', side, normals) >= 0
    closest[inside] = np.minimum(closest[inside], signed[inside]**2*nn[inside])
    minimum_face = int(np.argmin(closest))
    normal = normals[nearest_face]/np.linalg.norm(normals[nearest_face])
    return {'solidAngleWinding': float(winding), 'rays': rays,
        'nearestFaceIdFromActualDiagnostic': nearest_face,
        'nearestFaceCoordinates': triangles[nearest_face].tolist(), 'nearestFaceNormal': normal.tolist(),
        'signedNearestFacePlaneDistanceM': float((query-triangles[nearest_face, 0])@normal),
        'exhaustiveNearestTriangleId': minimum_face,
        'exhaustiveUnsignedDistanceM': float(np.sqrt(closest[minimum_face]))}


def main():
    assert len(sys.argv) == 2, 'check_solid.py OUTPUT_JSON'
    output = Path(sys.argv[1]).resolve()
    assert not output.exists() and output.is_relative_to(h['ROOT'])
    actual_diagnostic = json.loads(DIAGNOSTIC_PATH.read_text())
    assert actual_diagnostic['sourceInput'] == h['INPUT']
    assert actual_diagnostic['fullReference'] == ACTUAL
    assert actual_diagnostic['canonicalBody'] == h['CANONICAL']
    witness = actual_diagnostic['globalMinimum']; query = np.asarray(witness['worldPoint'])
    nearest = witness['nearestFullReference']
    assert nearest['canonicalCoordinatesExact'] and len(nearest['canonicalNative02TriangleIds']) == 1
    actual = np.load(checked(ACTUAL)); canonical = np.load(checked(h['CANONICAL']))
    key = 'RiderBody__FullAnatomyReference'
    result = {'status': 'ACTUAL_UPPER_ARM_WITNESS_INSIDE_BOTH_BODY_SOLIDS', 'acceptedArt': False,
        'queryWorldPoint': query.tolist(), 'originalHoodieFace': witness['originalNativeFaceId'],
        'diagnostic': pin(DIAGNOSTIC_PATH), 'recipe': pin(__file__),
        'actualReference': ACTUAL, 'canonicalBody': h['CANONICAL'], 'meshes': {}}
    for label, points, faces, face in (
        ('actualFullReference', actual[key+'_basis'], actual[key+'_triangles'], nearest['fullReferenceTriangleId']),
        ('canonicalNative02', canonical['vertices'], canonical['faces'], nearest['canonicalNative02TriangleIds'][0])):
        row = solid_witness(points.astype(float), faces, query, face)
        assert abs(row['solidAngleWinding']-1) < 1e-10
        assert all(r['positiveHitCount'] == 1 and r['firstHits'][0]['normalDotRay'] > 0 for r in row['rays'])
        assert abs(row['exhaustiveUnsignedDistanceM']+witness['signedFullReferenceGapM']) < 1e-7
        result['meshes'][label] = row
    result['limits'] = ['One actual witness, not a full garment qualification.',
        'Winding, separated transverse rays and exhaustive distance agree; no support/geometry/target changes.',
        'Distal inner-band exclusion does not prove this proximal donor face is an exterior garment surface.']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': pin(output), 'status': result['status']}))


if __name__ == '__main__': main()
