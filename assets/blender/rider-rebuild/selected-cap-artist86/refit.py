"""Local17 REST-body cap attachments and paired lower-front repair.

Source only until parent review. No pose is consulted to choose an attachment.
Original full fields, selected UV/appearance ancestry, topology and .145/.168
sleeve endpoints survive. The dense47 source itself is never opened or written.
"""
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OLD = 'harness/out/rider-rebuild/selected-hoodie-joints77/'
OUT = ROOT/'harness/out/rider-rebuild/selected-cap-artist86'
PINS = {
    'receipt': (OLD+'receiver16/receiver.json', 'c201ad21d6c52cb50895d5f36183d6b260e66db10c08d091be4b7d2ecd4d856a'),
    'arrays': (OLD+'receiver16/receiver.npz', '0196f00498c94304a692442dd37ab62ae7b695dd4be5eb0b962e80e92cba0bf5'),
    'construction': (OLD+'receiver15/connected-cap.json', '193db2d2cea4de7ccb0372f6560109177b73a75d1904d7c3b70453c7f024508b'),
    'paint': (OLD+'receiver16/local-paint.json', '993e1eda80a7cae0cf8d1aab4a866aa50dc6a4a7fe583367bbfd2754e56c6cc4'),
    'body': (OLD+'body-guide01/actual-body-fields.json', '8fb18ac1722439375e3fa30a3b72b9696fb8d2459d4747892d3a454e6f2be6e3'),
    'bodyArrays': (OLD+'body-guide01/actual-body-fields.npz', 'cfb58ca2e8bd6d9e933b7a1a22a3405080dd219aacfb5acfe97a3a079dafc4f8'),
    'author': ('assets/blender/rider-rebuild/selected-hoodie-joints77/author.py', '9477ea7896d42a91f0c91c18aed760d2987aabb4b9bd8953ceccf95220361fb7'),
}
# The observed lower-front connected patch identifies garment scope only.
# Its posed body triangle IDs NEVER become binding candidates.
LOWER_SEEDS = (3959, 4012, 4057, 4160, 4162, 4258, 4259, 4260, 4353, 4440,
    4558, 4667, 4827, 4909, 4913, 4947, 5074, 5310, 5389, 5391, 5473,
    5628, 5679, 5731, 5766, 5795, 5925, 5927, 5929, 5969, 6070, 6071, 6155)
INNER_EASE, WALL = .003, .0023


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def checked(key):
    path, digest = PINS[key]
    assert pin(ROOT/path) == {'path': path, 'sha256': digest}, key
    return ROOT/path


def read(key):
    return json.loads(checked(key).read_text())


def inputs():
    for key in PINS: checked(key)
    receipt, body = read('receipt'), read('body')
    a, b = dict(np.load(checked('arrays'))), dict(np.load(checked('bodyArrays')))
    assert receipt['source47Receipt'] == body['sourceReceipt']
    assert set(a['groupNames']) == set(b['groupNames']) and len(a['groupNames']) == 71
    order = [b['groupNames'].tolist().index(n) for n in a['groupNames']]
    # Actual body/garment inventories have different column orders.
    b['inputFieldOrder'] = b['groupNames'].copy()
    b['normalizedNamedFields'] = b['normalizedNamedFields'][:, order]
    b['rawNamedFields'] = b['rawNamedFields'][:, order]
    b['groupNames'] = a['groupNames'].copy()
    assert len(body['rest']) == 75 and receipt['receiver'] == pin(checked('arrays'))
    return receipt, a, body, b, read('construction'), read('paint')


def connected_faces(faces, eligible, seeds):
    """Literal shared-edge component; no proximity links between body sheets."""
    owner, adjacent = {}, defaultdict(set)
    for fi in np.flatnonzero(eligible):
        for i, j in zip(faces[fi], np.roll(faces[fi], -1)):
            edge = tuple(sorted((int(i), int(j))))
            if edge in owner:
                adjacent[fi].add(owner[edge]); adjacent[owner[edge]].add(int(fi))
            else: owner[edge] = int(fi)
    reached, stack = set(), [int(seeds[0])]
    assert all(eligible[i] for i in seeds), 'Anatomical domain excludes an actual boundary seed'
    while stack:
        i = stack.pop()
        if i in reached: continue
        reached.add(i); stack.extend(adjacent[i]-reached)
    assert set(map(int, seeds)) <= reached, 'Boundary seeds lie on different body sheets'
    return np.asarray(sorted(reached), np.int32)


class BodyChart:
    def __init__(self, body, face_ids, Surface):
        self.body, self.face_ids = body, face_ids
        vertices = np.unique(body['triangles'][face_ids]); index = np.full(len(body['positions']), -1, np.int32)
        index[vertices] = np.arange(len(vertices))
        self.surface = Surface(body['positions'][vertices], index[body['triangles'][face_ids]])

    def nearest(self, point):
        local, bary, q, normal, gap = self.surface.nearest(point)
        face = int(self.face_ids[local]); ids = self.body['triangles'][face]
        fields = bary @ self.body['normalizedNamedFields'][ids]
        assert np.isfinite(fields).all() and fields.min() >= -1e-12 and abs(fields.sum()-1) < 1e-12
        return {'bodyTriangle': face, 'bodyVertexIds': ids.tolist(), 'barycentric': bary.tolist(),
                'bodyRestPoint': q.tolist(), 'bodyRestNormal': normal.tolist(), 'signedRestGapM': float(gap),
                'rawFull71Fields': fields.tolist()}, q, normal, fields


def shoulder_chart(side, b, body, construction, A):
    bones = {r[0]: r for r in body['rest']}; frame, _ = A['bone_frame'](body['rest'], side)
    origin, axis, _, _ = frame(0); sign = 1 if side == 'L' else -1
    centroid = b['positions'][b['triangles']].mean(1)
    medial = float(bones['DEF-shoulder.'+side][2][0])
    # Native clavicle medial plane + ordinary sleeve boundary delimit one
    # torso/shoulder/upper-arm sheet. Head-region and opposite arm are absent.
    eligible = np.all(b['regionIds'][b['triangles']] == 1, axis=1)
    eligible &= (centroid[:, 0]-medial)*sign > 0
    eligible &= (centroid-origin) @ axis <= .168
    seam = {int(v) for s in construction['strips'] if s['side'] == side for v in s['seamLoop']+s['capRows'][-1]}
    seeds = sorted({r['bodyTriangle'] for r in construction['bodyBoundarySamples'] if r['vertex'] in seam})
    faces = connected_faces(b['triangles'], eligible, seeds)
    return BodyChart(b, faces, A['Surface']), {'side': side, 'seedBodyTriangles': seeds,
        'bodyTriangleIds': faces.tolist(), 'medialPlaneX': medial, 'distalArmStationM': .168}


def periodic_partner(angle, angles, row, p):
    extended = np.r_[angles[-1]-2*np.pi, angles, angles[0]+2*np.pi]
    ids = np.r_[row[-1], row, row[0]]
    while angle < extended[0]: angle += 2*np.pi
    while angle > extended[-1]: angle -= 2*np.pi
    j = min(int(np.searchsorted(extended, angle, side='right')-1), len(extended)-2)
    t = float((angle-extended[j])/(extended[j+1]-extended[j]))
    return (1-t)*p[ids[j]]+t*p[ids[j+1]], [int(ids[j]), int(ids[j+1])], t


def cap_edit(a, b, body, construction, paint, A):
    p, fields = a['positions'].copy(), a['namedFields'].copy()
    retained = np.isin(a['vertexRoles'], ('selected_original', 'armhole_seam'))
    # Literal original47 full fields: no height paint, head remap or pelvis loss.
    fields[retained] = a['sourceOnlyNamedFields'][retained]
    witnesses, charts, fixed, restored = [], [], set(), set(np.flatnonzero(retained).tolist())
    for side in ('L', 'R'):
        chart, detail = shoulder_chart(side, b, body, construction, A); charts.append(detail)
        frame, _ = A['bone_frame'](body['rest'], side)
        origin, _, forward, outward = frame(0)
        strips = {s['wall'].split(':')[1]: s for s in construction['strips'] if s['side'] == side}
        angles, chains = {}, {}
        for wall, strip in strips.items():
            seam = a['referencePositions'][strip['seamLoop']]-origin
            angles[wall] = np.arctan2(seam@outward, seam@forward) % (2*np.pi)
            assert np.all(np.diff(angles[wall]) > 0), 'Actual seam order must remain monotone'
            chains[wall] = np.asarray([strip['seamLoop'], *strip['capRows']], np.int32)
            fixed.update(strip['capRows'][-1]); fixed.update(strip['ordinaryBoundary'])
        local = next(r for r in paint['paint'] if r['side'] == side)['retainedPaintVertexIds']
        seam_ids = {int(i) for chain in chains.values() for i in chain[0]}
        for vi in sorted(set(local)-seam_ids):
            witness, _, _, values = chart.nearest(a['positions'][vi])
            fields[vi] = values; restored.discard(vi)
            witnesses.append(dict(witness, vertex=vi, kind='retained_shoulder', restPositionFixed=True))
        for wall, chain in chains.items():
            other = 'inner' if wall == 'outer' else 'outer'; sign = 1 if wall == 'outer' else -1
            # Last cap row and ordinary sleeve remain exactly the healthy16 anchors.
            for ri, row in enumerate(chain[:-1]):
                for vi, angle in zip(row, angles[wall]):
                    partner, pair_ids, t = periodic_partner(float(angle), angles[other], chains[other][ri], a['positions'])
                    midpoint = (a['positions'][vi]+partner)/2
                    witness, q, normal, values = chart.nearest(midpoint)
                    signed = float((midpoint-q)@normal)
                    center = midpoint+normal*max(0., INNER_EASE+WALL/2-signed)
                    # The actual selected seam is the fixed shape boundary. All
                    # interior rows share one midsurface and explicit 2.3mm wall.
                    if ri > 0: p[vi] = center+sign*WALL/2*normal
                    fields[vi] = values; restored.discard(int(vi))
                    witnesses.append(dict(witness, vertex=int(vi), kind='cap', side=side, wall=wall, row=ri,
                        partnerVertices=pair_ids, partnerFraction=t, originalMidpoint=midpoint.tolist(),
                        pairedInnerRest=(center-WALL/2*normal).tolist(), pairedOuterRest=(center+WALL/2*normal).tolist(),
                        wallThicknessM=WALL, seamShapeFixed=ri == 0))
    assert np.array_equal(p[sorted(fixed)], a['positions'][sorted(fixed)])
    assert np.array_equal(fields[sorted(fixed)], a['namedFields'][sorted(fixed)])
    return p, fields, witnesses, charts, sorted(fixed), restored


def front_pair(point, body_surface, garment_surface, body, A):
    bones = {r[0]: r for r in body['rest']}
    spine = np.asarray([bones[n][2] for n in ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002')])
    origin = np.array([point[0], np.interp(point[2], spine[:, 2], spine[:, 1]), point[2]])
    direction = np.array([0., -1., 0.]); distance = float(origin[1]-point[1])
    hits = body_surface.ray(origin, direction)
    assert hits and hits[0][1] > 0, 'Lower-front ray must exit its actual torso sheet'
    body_hit = hits[0]
    hits = garment_surface.ray(origin, direction)
    # Native triangle winding identifies the two walls at the SAME x/z, not
    # two unrelated nearest vertices or opposite sides of an air gap.
    pairs = [(inner, outer) for inner in hits if inner[1] < 0 for outer in hits
             if outer[1] > 0 and outer[0] > inner[0]]
    assert pairs, ('No literal paired front wall', point.tolist())
    inner, outer = min(pairs, key=lambda pair: (min(abs(distance-pair[0][0]), abs(distance-pair[1][0])), pair[1][0]-pair[0][0]))
    own = 'inner' if abs(distance-inner[0]) < abs(distance-outer[0]) else 'outer'
    shift = max(0., body_hit[0]+INNER_EASE-inner[0])
    # Translate both sampled walls together; retain the selected local thickness.
    new_distance = distance+shift
    return origin+direction*new_distance, body_hit, inner, outer, own, shift, origin


def lower_front_edit(a, p, fields, b, body, A):
    f, _, poly = A['triangulate'](a); selected = a['faceRoles'][poly] == 'selected_retained'
    assert f[3959].tolist() == [3887, 3898, 3889] and selected[list(LOWER_SEEDS)].all()
    garment = A['Surface'](a['positions'], f[selected]); selected_ids = np.flatnonzero(selected)
    body_faces = np.flatnonzero(np.all(b['regionIds'][b['triangles']] == 1, axis=1))
    body_surface = A['Surface'](b['positions'], b['triangles'][body_faces])
    adjacent = defaultdict(set)
    for face in f[selected]:
        for i, j in zip(face, np.roll(face, -1)): adjacent[int(i)].add(int(j)); adjacent[int(j)].add(int(i))
    core = set(np.unique(f[list(LOWER_SEEDS)]).tolist()); paired = set()
    for vi in sorted(core):
        _, _, inner, outer, _, _, _ = front_pair(a['positions'][vi], body_surface, garment, body, A)
        for hit in (inner, outer): paired.update(f[selected_ids[hit[2]]].tolist())
    core |= paired
    # One literal surrounding edge ring is part of the sculpt; the next ring
    # stays fixed. No successive radius/taper attempts or full torso refit.
    active = core | {j for i in core for j in adjacent[i]}
    fixed = {j for i in active for j in adjacent[i]}-active
    witnesses = []
    for vi in sorted(active | fixed):
        target, hit, inner, outer, wall, shift, origin = front_pair(a['positions'][vi], body_surface, garment, body, A)
        if vi in fixed:
            assert shift == 0., ('Fixed surrounding ring is not healthy; revise explicit patch', vi, shift)
            continue
        distance, _, local_face, bary = hit; face = int(body_faces[local_face]); vertices = b['triangles'][face]
        values = bary@b['normalizedNamedFields'][vertices]
        if shift > 0:
            p[vi] = target; fields[vi] = values
        witnesses.append({'vertex': vi, 'kind': 'lower_front', 'wall': wall, 'bodyTriangle': face,
            'bodyVertexIds': vertices.tolist(), 'barycentric': bary.tolist(),
            'bodyRestPoint': (origin+np.array([0., -distance, 0.])).tolist(), 'rawFull71Fields': values.tolist(),
            'innerGarmentTriangle': int(selected_ids[inner[2]]), 'innerGarmentBarycentric': inner[3].tolist(),
            'outerGarmentTriangle': int(selected_ids[outer[2]]), 'outerGarmentBarycentric': outer[3].tolist(),
            'selectedWallThicknessM': outer[0]-inner[0], 'pairedWallShiftM': shift,
            'positionApplied': shift > 0})
    assert np.array_equal(p[sorted(fixed)], a['positions'][sorted(fixed)])
    return witnesses, {'seedGarmentTriangles': list(LOWER_SEEDS), 'coreVertexIds': sorted(core),
        'activeVertexIds': sorted(active), 'fixedHealthyRingVertexIds': sorted(fixed)}



def verify(receipt_path):
    """Saved17 attachment admission for the parent's existing native77 adapter.

    Recompute full fields and recorded local position equations from immutable
    actual16/body47 arrays. Never rerun a field solve or replace the saved model.
    """
    receipt_path = Path(receipt_path).resolve()
    row = json.loads(receipt_path.read_text()); binding = row['localRestBodyBinding']
    assert row['acceptedArt'] is False and binding['recipe'] == pin(__file__)
    assert binding['input'] == pin(checked('receipt')) and binding['bodyGuide'] == pin(checked('body'))
    report_path = ROOT/binding['attachments']['path']
    assert pin(report_path) == binding['attachments'] == row['construction']
    report = json.loads(report_path.read_text()); arrays_path = ROOT/row['receiver']['path']
    assert pin(arrays_path) == row['receiver'] == report['receiver']
    assert report['recipe'] == binding['recipe'] and report['input'] == binding['input']
    _, before, _, b, _, _ = inputs(); after = np.load(arrays_path)
    for key, value in before.items():
        if key not in ('positions', 'namedFields'): assert np.array_equal(after[key], value), key
    assert np.array_equal(after['before17Positions'], before['positions'])
    assert np.array_equal(after['before17NamedFields'], before['namedFields'])
    for key, name, listed in (('positions', 'attachment17PositionIds', 'changedPositionVertices'),
                              ('namedFields', 'attachment17FieldIds', 'changedFieldVertices')):
        changed = np.flatnonzero(np.any(after[key] != before[key], axis=1))
        assert np.array_equal(changed, after[name]) and changed.tolist() == report[listed]
    fixed, restored = after['fixed17SleeveVertexIds'], after['restored47VertexIds']
    for key in ('positions', 'namedFields'): assert np.array_equal(after[key][fixed], before[key][fixed])
    assert np.array_equal(after['namedFields'][restored], before['sourceOnlyNamedFields'][restored])
    for w in report['attachments']:
        ids = b['triangles'][w['bodyTriangle']]; bary = np.asarray(w['barycentric'])
        assert ids.tolist() == w['bodyVertexIds'] and bary.min() >= -1e-10 and abs(bary.sum()-1) < 1e-12
        values = bary@b['normalizedNamedFields'][ids]
        assert np.array_equal(values, np.asarray(w['rawFull71Fields']))
        assert np.max(abs(bary@b['positions'][ids]-w['bodyRestPoint'])) < 1e-12
        vi = w['vertex']
        if w['kind'] != 'lower_front' or w['positionApplied']:
            assert np.array_equal(after['namedFields'][vi], values.astype(np.float32))
        if w['kind'] == 'cap':
            expected = before['positions'][vi] if w['seamShapeFixed'] else np.asarray(w['pairedOuterRest' if w['wall'] == 'outer' else 'pairedInnerRest'])
            assert np.array_equal(after['positions'][vi], expected)
            assert abs(np.linalg.norm(np.asarray(w['pairedOuterRest'])-w['pairedInnerRest'])-WALL) < 1e-12
        elif w['kind'] == 'lower_front' and w['positionApplied']:
            assert np.max(abs(after['positions'][vi]-before['positions'][vi]-[0., -w['pairedWallShiftM'], 0.])) < 1e-12
    assert np.isfinite(after['positions']).all() and np.isfinite(after['namedFields']).all()
    assert after['namedFields'].min() >= 0 and np.max(abs(after['namedFields'].sum(1)-1)) < 3e-7
    assert pin(ROOT/row['editableOBJ']['path']) == row['editableOBJ']
    return row


def main(output):
    controller = int(os.environ['ROCKHOP_GENERATION_CONTROLLER_PID'])
    assert controller == os.getppid(); os.kill(controller, 0)
    assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
    assert sys.version_info[:2] == (3, 13) and np.__version__ == '2.3.4'
    output = Path(output).resolve(); assert output.is_relative_to(OUT) and not output.exists()
    receipt, a, body, b, construction, paint = inputs(); recipe = pin(__file__)
    A = runpy.run_path(str(checked('author')))
    p, fields, cap, charts, anchors, restored = cap_edit(a, b, body, construction, paint, A)
    lower, lower_patch = lower_front_edit(a, p, fields, b, body, A)
    edited_lower = {r['vertex'] for r in lower if r['positionApplied']}; restored -= edited_lower
    assert np.array_equal(fields[sorted(restored)], a['sourceOnlyNamedFields'][sorted(restored)])
    assert np.isfinite(p).all() and np.isfinite(fields).all() and fields.min() >= 0
    assert np.max(abs(fields.sum(1)-1)) < 3e-7
    changed_p = np.flatnonzero(np.any(p != a['positions'], axis=1)); changed_f = np.flatnonzero(np.any(fields != a['namedFields'], axis=1))
    result = dict(a); result.update(positions=p, namedFields=fields, before17Positions=a['positions'],
        before17NamedFields=a['namedFields'], attachment17PositionIds=changed_p, attachment17FieldIds=changed_f,
        restored47VertexIds=np.asarray(sorted(restored), np.int32), fixed17SleeveVertexIds=np.asarray(anchors, np.int32))
    assert all(np.array_equal(result[k], v) for k, v in a.items() if k not in ('positions', 'namedFields'))
    output.mkdir(parents=True); np.savez_compressed(output/'receiver.npz', **result)
    with (output/'selected-cap17.obj').open('w') as stream:
        stream.write('# UNACCEPTED selected17 rest-body attachment derivative\n')
        for point in p: stream.write('v %.10g %.10g %.10g\n'%tuple(point))
        for uv in a['cornerUV']: stream.write('vt %.10g %.10g\n'%tuple(uv))
        for start, count in zip(a['polygonStarts'], a['polygonCounts']):
            stream.write('f '+' '.join(f'{a["cornerVertexIds"][i]+1}/{i+1}' for i in range(start, start+count))+'\n')
    report = {'status': 'LOCAL17_REST_BODY_PAIRED_WALL_ATTACHMENT_UNACCEPTED', 'acceptedArt': False,
        'recipe': recipe, 'input': pin(checked('receipt')), 'receiver': pin(output/'receiver.npz'),
        'bodyGuide': pin(checked('body')), 'charts': charts, 'attachments': cap+lower, 'lowerFrontPatch': lower_patch,
        'fixedSleeveVertices': anchors, 'restored47Vertices': sorted(restored),
        'changedPositionVertices': changed_p.tolist(), 'changedFieldVertices': changed_f.tolist(),
        'topologyUVAndAppearanceArraysExactly16': True, 'fullNamedGroups': 71,
        'limits': 'Unaccepted local authoring. Six-pose/depth inspection, all482 native/export parity, genuine79 bake, moving PBR and seated game review remain required.'}
    (output/'attachments.json').write_text(json.dumps(report, indent=2)+'\n')
    derivative = {k: receipt[k] for k in ('sourceReceiver', 'source47Receipt', 'fullBody', 'original47Geometry', 'actualGuides', 'topology')}
    derivative.update(status=report['status'], acceptedArt=False, recipe=recipe, receiver=report['receiver'],
        editableOBJ=pin(output/'selected-cap17.obj'), construction=pin(output/'attachments.json'),
        localRestBodyBinding={'recipe': recipe, 'input': report['input'], 'bodyGuide': report['bodyGuide'], 'attachments': pin(output/'attachments.json')},
        correspondenceAndSkin={'fullNamedFieldCount': 71, 'healthyFieldsExactBeforeFloat32': False, 'restoredOriginal47Rows': len(restored), 'productionFourConditioned': False},
        detailBakePassed=False, posedContactPassed=False, nativeSaved=False, movingArtPassed=False,
        genuineBakeAtlasPresent=False, limitations=[report['limits']])
    (output/'receiver.json').write_text(json.dumps(derivative, indent=2)+'\n')
    for key in PINS: checked(key)
    assert pin(__file__) == recipe
    print(json.dumps({'receiver': pin(output/'receiver.json'), 'positionEdits': len(changed_p), 'fieldEdits': len(changed_f), 'acceptedArt': False}), flush=True)
    return output/'receiver.json'


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 1; main(args[0])
