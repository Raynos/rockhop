"""Read-only ownership of the 858 low faces in each rejected inner component.

Parent original CPU guard only. Source normals and vertical triangle hits;
no mesh edit, native execution, clearance adjustment, or wearable qualification.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'harness/out/rider-rebuild/selected-boot-wearer80'
SELECTION = ('harness/out/rider-rebuild/selected-boot-wearer80/selection01/selection.json',
             '8484fb23b19d3edcda3a1b3b995c735e219b2ecaf4431eeaaa2503bd02b309bc')
BODY = ('docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz',
        'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2')


def checked(row):
    path = ROOT/row[0]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row[1], row[0]
    return path


def pool(points, faces, queries, handedness):
    tri = points[faces]
    low, high = queries[:, :2].min(0), queries[:, :2].max(0)
    ids = np.flatnonzero(np.all(tri[:, :, :2].max(1) >= low, axis=1) &
                         np.all(tri[:, :, :2].min(1) <= high, axis=1))
    t = tri[ids]
    n = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0])*handedness
    n /= np.linalg.norm(n, axis=1)[:, None]
    return t, ids, n


def vertical_hits(package, q):
    tri, face_ids, normals = package
    use = np.all(tri[:, :, :2].max(1) >= q[:2]-1e-12, axis=1) & np.all(tri[:, :, :2].min(1) <= q[:2]+1e-12, axis=1)
    tri, face_ids, normals = tri[use], face_ids[use], normals[use]
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    e, f, d = b-a, c-a, q[:2]-a[:, :2]
    det = e[:, 0]*f[:, 1]-e[:, 1]*f[:, 0]
    good = np.abs(det) > 1e-18
    u = np.divide(d[:, 0]*f[:, 1]-d[:, 1]*f[:, 0], det, out=np.full(len(tri), np.inf), where=good)
    v = np.divide(e[:, 0]*d[:, 1]-e[:, 1]*d[:, 0], det, out=np.full(len(tri), np.inf), where=good)
    ids = np.flatnonzero(good & (u >= -1e-9) & (v >= -1e-9) & (u+v <= 1+1e-9))
    z = a[ids, 2]+u[ids]*e[ids, 2]+v[ids]*f[ids, 2]
    return sorted([{'triangleId': int(face_ids[i]), 'zM': float(h), 'normalLocal': normals[i].tolist()}
                   for i, h in zip(ids, z)], key=lambda row: row['zM'])


def span(values):
    return [float(min(values)), float(max(values))] if values else None


def main():
    assert len(sys.argv) == 2
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(BASE) and not out.exists()
    out.mkdir(parents=True)
    selection = json.loads(checked(SELECTION).read_text())
    source = json.loads(checked(selection['pins']['source']).read_text())
    inspection = json.loads(checked(selection['pins']['inspection']).read_text())
    failure = json.loads(checked(selection['pins']['failure']).read_text())
    actual47 = failure['actual47Below24cmMatchesNative02']
    assert actual47 == {'vertices': 2638, 'positionsExact': True, 'namedFieldsExact': True}
    body = dict(np.load(checked(BODY)))
    package = source['arrays']
    raw = checked((package['path'], package['sha256'])).read_bytes()
    arrays = {k: np.frombuffer(raw, dtype=v['dtype'], count=v['byteLength']//np.dtype(v['dtype']).itemsize,
                             offset=v['byteOffset']).reshape(v['shape']) for k, v in package['layout'].items()}
    report = {'status': 'LOW_INNER_COMPONENT_FACE_OWNERSHIP_UNACCEPTED', 'acceptedArt': False,
              'selectionPin': SELECTION, 'bodyPin': BODY, 'sourcePins': selection['pins'],
              'actual47Correspondence': actual47, 'recipeSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'sides': {}}
    for side in ('L', 'R'):
        prior, frame = selection['sides'][side], inspection['sides'][side]
        selected = np.load(checked((prior['selectedIds']['path'], prior['selectedIds']['sha256'])))
        origin, basis = np.array(frame['origin']), np.array(frame['basisColumns']).T
        p = (arrays[side+'Positions'].astype(float)-origin)@basis
        faces = arrays[side+'Triangles']
        handedness = float(np.linalg.det(basis))
        assert abs(abs(handedness)-1.) < 1e-12
        bad = selected[p[faces[selected], 2].min(1) <= -.001]
        assert len(bad) == prior['failedPredicates']['belowMinus1mm']['sourceTriangles'] == 858
        selected_mask = np.zeros(len(faces), bool)
        selected_mask[selected] = True
        centers = p[faces[bad]].mean(1)
        boot_pool = pool(p, faces, centers, handedness)
        own = np.all(body['vertices'][body['faces'], 0]*np.sign(origin[0]) > 0, axis=1)
        domain = own & np.all(body['vertices'][body['faces'], 2] < .24, axis=1)
        body_ids = np.flatnonzero(domain)
        body_pool = pool((body['vertices'].astype(float)-origin)@basis, body['faces'][body_ids], centers, handedness)
        body_pool = (body_pool[0], body_ids[body_pool[1]], body_pool[2])
        rows = []
        for i, q in zip(bad, centers):
            boot_hits, body_hits = vertical_hits(boot_pool, q), vertical_hits(body_pool, q)
            for hit in boot_hits:
                hit['insideSelectedComponent'] = bool(selected_mask[hit['triangleId']])
            own_hit = next(h for h in boot_hits if h['triangleId'] == i)
            assert abs(own_hit['zM']-q[2]) < 1e-9
            bottom = boot_hits[0]
            lower_outer = [h for h in boot_hits if not h['insideSelectedComponent'] and h['zM'] < q[2]-1e-7]
            qualifies = (own_hit['normalLocal'][2] > 0 and not bottom['insideSelectedComponent'] and
                         bottom['normalLocal'][2] < 0 and bool(lower_outer))
            rows.append({'sourceTriangleId': int(i), 'localCentroidM': q.tolist(),
                'ownNormalLocal': own_hit['normalLocal'], 'orderedSourceHits': boot_hits,
                'actualWearerHits': body_hits, 'innerFloorOwnershipSupported': qualifies,
                'outerBottomToFloorM': float(q[2]-bottom['zM']),
                'floorToActualPlantarM': float(body_hits[0]['zM']-q[2]) if body_hits else None})
        side_path = out/(side+'-low-faces.json')
        side_path.write_text(json.dumps(rows, indent=2)+'\n')
        report['sides'][side] = {
            'sourceFaces': len(rows), 'cutLoopAreaM2': prior['cutRings'][0]['areaM2'],
            'lowFaceBoundsLocalM': [p[faces[bad]].reshape(-1, 3).min(0).tolist(), p[faces[bad]].reshape(-1, 3).max(0).tolist()],
            'unsupportedOwnership': [r['sourceTriangleId'] for r in rows if not r['innerFloorOwnershipSupported']],
            'upNormalZRange': span([r['ownNormalLocal'][2] for r in rows]),
            'outerBottomToFloorM': span([r['outerBottomToFloorM'] for r in rows]),
            'floorToActualPlantarM': span([r['floorToActualPlantarM'] for r in rows if r['floorToActualPlantarM'] is not None]),
            'outsideActualFootProjection': [r['sourceTriangleId'] for r in rows if not r['actualWearerHits']],
            'faceEvidence': {'path': str(side_path.relative_to(ROOT)), 'sha256': hashlib.sha256(side_path.read_bytes()).hexdigest()}}
    report['limits'] = ('Every one of the 858 disputed source face centroids per side, with actual oriented normals '
        'and vertical triangle hit order. Own-side wearer triangles below24cm diagnose plantar relation; their exact '
        'actual47 correspondence was independently recorded in construction01. This is internal-face ownership '
        'evidence, not all-surface clearance, derivative topology, motion, art, or production acceptance.')
    (out/'ownership.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'output': str(out)}))


if __name__ == '__main__':
    main()
