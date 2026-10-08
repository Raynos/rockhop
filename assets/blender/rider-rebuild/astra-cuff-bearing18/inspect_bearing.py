"""Read-only replay of native07's first failed cuff bearing.

Normal Python writes the exact/quantized triangle-ray evidence. The parent's
single CPU2 Blender invocation may add --bvh to exercise the original BVHTree
API as well. No scene, mesh, fitting, export or acceptance state is changed.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1048576):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], row['path']
    return path


def finite_hits(origin, direction, points, faces, face_ids=None):
    """All actual positive triangle hits within the original 0.3 m limit.

    The calculation uses the supplied precision without a barycentric slack,
    normal-angle exclusion, enlarged surface, substitute profile or fake hit.
    """
    triangle = points[faces]
    e1, e2 = triangle[:, 1] - triangle[:, 0], triangle[:, 2] - triangle[:, 0]
    p = np.cross(direction, e2)
    determinant = np.sum(e1 * p, axis=1)
    nonparallel = determinant != 0
    inverse = 1 / np.where(nonparallel, determinant, 1)
    s = origin - triangle[:, 0]
    u = np.sum(s * p, axis=1) * inverse
    q = np.cross(s, e1)
    v = np.sum(direction * q, axis=1) * inverse
    distance = np.sum(e2 * q, axis=1) * inverse
    valid = nonparallel & (u >= 0) & (v >= 0) & (u + v <= 1)
    valid &= (distance > 0) & (distance < .3)
    selected = np.flatnonzero(valid)
    selected = selected[np.argsort(distance[selected])]
    if face_ids is None:
        face_ids = np.arange(len(faces))
    return [{'triangleId': int(face_ids[i]), 'vertexIds': faces[i].tolist(),
             'distanceM': float(distance[i]),
             'barycentric': [float(1-u[i]-v[i]), float(u[i]), float(v[i])]}
            for i in selected]


def bvh_hit(points, faces, origin, direction):
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([Vector(p) for p in points], faces.tolist(),
                               all_triangles=True)
    hit = tree.ray_cast(Vector(origin), Vector(direction), .3)
    return None if hit[0] is None else {
        'distanceM': float(hit[3]), 'triangleIdInSelection': int(hit[2]),
        'position': list(hit[0]), 'normal': list(hit[1])}


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) in (1, 2) and (len(args) == 1 or args[1] == '--bvh')
    out = Path(args[0]).resolve()
    allowed = [ROOT/'docs/evidence/rider-rebuild/astra-cuff-bearing18',
               ROOT/'harness/out/rider-rebuild/astra-cuff-bearing18']
    assert any(out.is_relative_to(p) for p in allowed) and not out.exists()
    config = json.loads((HERE/'input.json').read_text())
    constructor = pin(config['failedConstructor'])
    current = json.loads(pin(config['failedInput']).read_text())
    base = json.loads(pin(current['baseInput']).read_text())
    prior = json.loads(pin(base['priorInputs']).read_text())
    inspection = json.loads(pin(prior['currentInspection']).read_text())
    assert inspection['master'] == prior['master']
    helper = runpy.run_path(str(pin(base['volumeHelper'])))
    guide = np.load(pin(prior['guideArrays']['L']))
    placement = json.loads(pin(prior['placement']).read_text())
    donor = np.load(pin(prior['originalGloveDense']))
    source, faces = donor['vertices'], donor['faces']
    wearer_pin = next(row for row in inspection['hands']['L']['localSurfaces']
                      if row['role'] == 'wearer')
    assert wearer_pin['object'] == 'RiderBody__FullAnatomyReference'
    wearer = np.load(pin(wearer_pin))
    scale, x, z = helper['cuff_frame'](guide, placement['hands']['L'])
    axial, sx, sz = helper['source_cuff'](
        source, guide, placement['sourceRest']['wrist'], scale, x, z)
    wrist = guide['wristWorld']
    axis = np.asarray(guide['forearmAxisWorld'], dtype=float)
    axis /= np.linalg.norm(axis)
    points = wrist + axial[:, None]*axis + sx[:, None]*x + sz[:, None]*z
    face = np.array([46711, 48112, 46712])
    bary = np.array([.05, .9, .05])
    point = np.sum(points[face]*bary[:, None], axis=0)
    station = float(np.sum((point-wrist)*axis))
    origin = wrist+station*axis
    vector = point-origin
    radius = float(np.linalg.norm(vector))
    direction = vector/radius
    normal = np.cross(points[face[1]]-points[face[0]], points[face[2]]-points[face[0]])
    normal /= np.linalg.norm(normal)
    # Every face that can meet this radial plane is below the floor surgery.
    actual_axial = np.sum((points-wrist)*axis, axis=1)
    at_plane = (actual_axial[faces].min(axis=1) <= station)
    at_plane &= actual_axial[faces].max(axis=1) >= station
    assert np.all(source[faces[at_plane], 1] < base['settings']['gloveFloorCutY'])
    cuff_ids = np.flatnonzero(np.all(
        source[faces, 1] <= base['settings']['gloveFloorCutY']+1e-8, axis=1))
    cuff = faces[cuff_ids]
    bp, bf = wearer['worldXYZ'], wearer['faces']
    d = bp-wrist
    ba = np.sum(d*axis, axis=1)
    br = np.linalg.norm(d-ba[:, None]*axis, axis=1)
    # The same local ownership predicate as construct07.body_tree.
    own = (bp[:, 0] > 0) & (ba > -.035) & (ba < .23) & (br < .12)
    body_ids = np.flatnonzero(np.any(own[bf], axis=1))
    body = bf[body_ids]
    result = {
        'acceptedArt': False, 'geometryGatesPassed': False,
        'method': 'One saved bearing; finite actual triangle rays; no model solve.',
        'recipeSHA256': sha(Path(__file__)), 'inputSHA256': sha(HERE/'input.json'),
        'failedConstructor': {'path': str(constructor.relative_to(ROOT)),
                              'sha256': sha(constructor)},
        'sourceMaster': prior['master'], 'originalGloveDense': prior['originalGloveDense'],
        'wearerSnapshot': {k: wearer_pin[k] for k in ('path', 'sha256', 'object')},
        'witness': {'sourceVertexIds': face.tolist(), 'barycentric': bary.tolist(),
                    'sourceXYZ': source[face].tolist(), 'worldXYZ': points[face].tolist(),
                    'sourceY': float(source[face, 1]@bary), 'stationM': station,
                    'origin': origin.tolist(), 'direction': direction.tolist(),
                    'knownPointRadiusM': radius, 'normalDotRay': float(normal@direction)},
        'floorCutCannotAffectStation': True,
        'actualSourceFacesAtStation': int(at_plane.sum()),
        'cuffFaces': len(cuff), 'bodyFaces': len(body), 'triangleRays': {},
        'limitations': ['Finite bearing evidence is not containment or moving-art acceptance.',
                       'The body snapshot is a pinned crop from the identical engine05 master.',
                       'Only --bvh exercises Blender; NumPy-only output cannot claim its API result.'],
    }
    for name, po, origin_value, direction_value in (
            ('worldFloat64', points, origin, direction),
            ('worldFloat32', points.astype('f4'), origin.astype('f4'), direction.astype('f4')),
            ('quantizedWorldGeometryFloat64Math', points.astype('f4').astype(float), origin, direction),
            ('wristRelativeFloat32', (points-wrist).astype('f4'),
             (origin-wrist).astype('f4'), direction.astype('f4'))):
        result['triangleRays'][name] = finite_hits(
            origin_value, direction_value, po, cuff, cuff_ids)
    result['wearerRaysFloat64'] = finite_hits(origin, direction, bp, body, body_ids)
    result['wearerRaysFloat32'] = finite_hits(
        origin.astype('f4'), direction.astype('f4'), bp.astype('f4'), body, body_ids)
    assert len(result['triangleRays']['worldFloat64']) == 2
    assert not result['triangleRays']['worldFloat32']
    assert len(result['triangleRays']['wristRelativeFloat32']) == 2
    assert result['wearerRaysFloat64'] and result['wearerRaysFloat32']
    if len(args) == 2:
        result['blenderBVH'] = {
            'worldCuff': bvh_hit(points, cuff, origin, direction),
            'worldWearer': bvh_hit(bp, body, origin, direction),
            'wristRelativeCuff': bvh_hit(points-wrist, cuff, origin-wrist, direction),
            'wristRelativeWearer': bvh_hit(bp-wrist, body, origin-wrist, direction),
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': str(out.relative_to(ROOT)), 'sha256': sha(out),
                      'blenderBVH': result.get('blenderBVH'),
                      'cuffHitCounts': {k: len(v) for k, v in result['triangleRays'].items()}}))


if __name__ == '__main__':
    main()
