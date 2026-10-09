"""One local shoulder/cap weight paint on immutable saved15 geometry.

No native save, geometry edit, global field solve or production-four pruning.
Run once only after parent source review/checkpoint, under the original guard.
"""
from collections import defaultdict
import hashlib
import heapq
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DATA = 'harness/out/rider-rebuild/selected-hoodie-joints77/'
PINS = {
    'receipt': (DATA+'receiver15/receiver.json', 'd92c1060f855c5daf3dc199404250b63af3bd577253dfb0fb8162bf8b41b1a0a'),
    'arrays': (DATA+'receiver15/receiver.npz', 'de556ac10b40fd625b922e072d49709dd40ccc99dc28c0df9274cbdb149b5305'),
    'construction': (DATA+'receiver15/connected-cap.json', '193db2d2cea4de7ccb0372f6560109177b73a75d1904d7c3b70453c7f024508b'),
    'body': (DATA+'body-guide01/actual-body-fields.json', '8fb18ac1722439375e3fa30a3b72b9696fb8d2459d4747892d3a454e6f2be6e3'),
    'bodyArrays': (DATA+'body-guide01/actual-body-fields.npz', 'cfb58ca2e8bd6d9e933b7a1a22a3405080dd219aacfb5acfe97a3a079dafc4f8'),
    'actualContact': (DATA+'contact15/posed-contact.json', '18f918f355f095ffa2119886f0f88d44166431eabb419fbecfa6284135087330'),
}


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def checked(key):
    path, digest = PINS[key]; assert pin(ROOT/path) == {'path': path, 'sha256': digest}, key
    return ROOT/path


def distances(adjacent, positions, allowed, seeds):
    distance = {int(v): 0. for v in seeds}; queue = [(0., int(v)) for v in seeds]; heapq.heapify(queue)
    while queue:
        d, i = heapq.heappop(queue)
        if d != distance[i]: continue
        for j in adjacent[i] & allowed:
            proposed = d+float(np.linalg.norm(positions[j]-positions[i]))
            if proposed < distance.get(j, np.inf):
                distance[j] = proposed; heapq.heappush(queue, (proposed, j))
    assert set(distance) == allowed
    return distance


def selected_target(raw, names, own):
    """Literal selected own-arm/clavicle mass, with an anatomical torso residual.

    Keep source lower-spine proportions. Neck/head source mass becomes collar
    spine.003 ownership on this lateral shoulder patch, not head ownership.
    The exact own controls are not renormalized against a pruned source family.
    """
    source = raw.astype(float); source /= source.sum()
    target = np.zeros(len(names)); target[own] = source[own]
    spine = [names.index(n) for n in ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003')]
    remainder = source[spine].copy()
    remainder[-1] += sum(source[names.index(n)] for n in ('DEF-spine.004', 'DEF-spine.005', 'DEF-spine.006'))
    assert remainder.sum() > 0 and target.sum() <= 1
    target[spine] = (1-target.sum())*remainder/remainder.sum()
    return target


def paint(a, construction, body, body_arrays):
    names = a['groupNames'].tolist(); assert len(names) == 71
    p = a['positions']; old = a['namedFields']; result = old.astype(float).copy()
    raw = a['sourceOnlyNamedFields'].astype(float); raw /= raw.sum(1)[:, None]
    adjacent = defaultdict(set); retained = set()
    for start, count, role in zip(a['polygonStarts'], a['polygonCounts'], a['faceRoles']):
        if role != 'selected_retained': continue
        ids = a['cornerVertexIds'][start:start+count].tolist(); retained.update(ids)
        for i, j in zip(ids, ids[1:]+ids[:1]): adjacent[i].add(j); adjacent[j].add(i)
    witnesses = {row['vertex']: row for row in construction['bodyBoundarySamples'] if row['kind'] == 'torso'}
    body_order = [body['groupNames'].index(n) for n in names]
    trunk = raw[:, [names.index(n) for n in ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003')]].sum(1)
    head = raw[:, [names.index(n) for n in ('DEF-spine.004', 'DEF-spine.005', 'DEF-spine.006')]].sum(1)
    bones = {row[0]: row for row in body['rest']}
    medial_axis = np.asarray(bones['DEF-shoulder.L'][2])-bones['DEF-shoulder.R'][2]
    medial_axis /= np.linalg.norm(medial_axis)
    touched = set(); fixed = set(); details = []; all_seams = []; seam_targets = []; allowed_changes = set()
    for side in ('L', 'R'):
        own = [names.index(n) for n in ('DEF-shoulder.'+side, 'DEF-upper_arm.'+side, 'DEF-upper_arm.'+side+'.001')]
        strips = [row for row in construction['strips'] if row['side'] == side]
        roots = {int(v) for strip in strips for v in strip['seamLoop']}
        own_mass = raw[:, own].sum(1)
        # The central collar between the two actual clavicle roots stays fixed.
        # Outside it, source anatomical families define the paint boundary, not
        # a height, brush radius, positive-weight epsilon or a field optimizer.
        medial_origin = np.asarray(bones['DEF-shoulder.'+side][2])
        outward = medial_axis*(1 if side == 'L' else -1)
        lateral = (p-medial_origin) @ outward
        assert all(lateral[i] > 0 for i in roots)
        family = {i for i in retained if lateral[i] > 0 and own_mass[i] > max(trunk[i], head[i], 1-own_mass[i]-trunk[i]-head[i])}
        eligible = family | roots; region = set(); stack = sorted(roots)
        while stack:
            i = stack.pop()
            if i in region: continue
            region.add(i); stack.extend((adjacent[i] & eligible)-region)
        outside = {j for i in region for j in adjacent[i] if j not in region}
        assert outside and not region & (touched | fixed) and not outside & touched
        touched.update(region); fixed.update(outside); allowed = region | outside
        ds = distances(adjacent, p, allowed, roots); db = distances(adjacent, p, allowed, outside)
        targets = {i: selected_target(a['sourceOnlyNamedFields'][i], names, own) for i in region}
        # Existing actual47 ray witnesses already identify the lower seam's
        # own body sheet. Restore its full measured field, including spine.001;
        # do not retain15's redistribution into inherited12 spine proportions.
        for i in roots & witnesses.keys():
            sample = witnesses[i]
            actual = np.asarray(sample['barycentric']) @ body_arrays['normalizedNamedFields'][body_arrays['triangles'][sample['bodyTriangle']]]
            assert np.array_equal(actual, np.asarray(sample['rawNamedFields']))
            target = actual[body_order]
            targets[i] = target/target.sum()
        for i in sorted(region):
            amount = db[i]/(db[i]+ds[i])
            result[i] = (1-amount)*old[i]+amount*targets[i]
        for i in sorted(roots):
            assert np.array_equal(result[i], targets[i])
            all_seams.append(i); seam_targets.append(targets[i])
        meridians = []
        for strip in strips:
            chain = np.asarray([strip['seamLoop'], *strip['capRows']], np.int32)
            assert np.all(a['faceWallKey'][np.char.startswith(a['faceRoles'], 'connected_cap_'+side)] != 'retained')
            lengths = np.linalg.norm(np.diff(p[chain], axis=0), axis=2)
            station = np.concatenate((np.zeros((1, chain.shape[1])), np.cumsum(lengths, axis=0)))
            assert np.all(station[-1] > 0)
            fraction = station/station[-1]
            start, end = result[chain[0]].copy(), old[chain[-1]].astype(float)
            for row in range(1, len(chain)-1):
                alpha = fraction[row, :, None]
                result[chain[row]] = (1-alpha)*start+alpha*end
            assert np.array_equal(result[chain[-1]], old[chain[-1]])
            allowed_changes.update(chain[:-1].ravel().tolist())
            meridians.append({'wall': strip['wall'], 'rows': chain.tolist(), 'materialFractions': fraction.tolist(),
                              'terminalBoundaryExactly15': True, 'ordinaryBoundary': strip['ordinaryBoundary']})
        allowed_changes.update(region)
        details.append({'side': side, 'retainedPaintVertexIds': sorted(region), 'fixedExternalVertexIds': sorted(outside),
                        'medialCollarPlane': {'origin': medial_origin.tolist(), 'outwardNormal': outward.tolist()},
                        'seamVertexIds': sorted(roots), 'bodyWitnessSeamVertexIds': sorted(roots & witnesses.keys()),
                        'sourceFamilySeamExceptions': sorted(roots-family), 'meridians': meridians})
    ids = np.asarray(sorted(allowed_changes), np.int32)
    result[ids] /= result[ids].sum(1)[:, None]
    result = result.astype(old.dtype)
    changed = np.flatnonzero(np.any(result != old, axis=1)).astype(np.int32)
    assert set(changed).issubset(allowed_changes)
    assert np.array_equal(result[sorted(fixed)], old[sorted(fixed)])
    assert np.isfinite(result).all() and result.min() >= 0 and np.max(abs(result.sum(1)-1)) < 3e-7
    return result, changed, details, np.asarray(all_seams, np.int32), np.asarray(seam_targets)


def main(output):
    controller = int(os.environ['ROCKHOP_GENERATION_CONTROLLER_PID']); assert controller == os.getppid(); os.kill(controller, 0)
    assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
    assert sys.version_info[:2] == (3, 13) and np.__version__ == '2.3.4'
    output = Path(output).resolve(); assert output.is_relative_to(ROOT/DATA) and not output.exists()
    self_pin = pin(__file__)
    for key in PINS: checked(key)
    read = lambda key: json.loads(checked(key).read_text())
    receipt, construction, body = read('receipt'), read('construction'), read('body')
    a = dict(np.load(checked('arrays')))
    fields, changed, details, seams, targets = paint(a, construction, body, np.load(checked('bodyArrays')))
    result = dict(a); result.update(namedFields=fields, prior15NamedFields=a['namedFields'],
        localPaintVertexIds=changed, localPaintOldFields=a['namedFields'][changed], localPaintNewFields=fields[changed],
        localPaintSeamVertexIds=seams, localPaintSeamTargetFields=targets)
    assert all(np.array_equal(value, result[key]) for key, value in a.items() if key != 'namedFields')
    output.mkdir(parents=True); np.savez_compressed(output/'receiver.npz', **result)
    report = {'status': 'LOCAL_PAIRED_WALL_SHOULDER_PAINT16_UNACCEPTED', 'acceptedArt': False, 'recipe': self_pin,
        'sourcePins': {key: {'path': value[0], 'sha256': value[1]} for key, value in PINS.items()},
        'input': pin(checked('receipt')), 'priorActualContact': pin(checked('actualContact')), 'bodyGuide': pin(checked('body')),
        'receiver': pin(output/'receiver.npz'), 'changedVertices': len(changed), 'changedVertexIds': changed.tolist(),
        'paint': details, 'allOtherInputArraysExactlyPreserved': True, 'fullNamedGroups': 71,
        'releasedInheritedFailure': '15 fixed upper seam to spine.003 by a collar-height cutoff and replaced actual axilla spine proportions with12 proportions.',
        'boundaryMethod': 'Connected retained source-own-family domain and its first external row; true edge-distance taper. All existing shared cap meridians use cumulative physical length to the unchanged terminal ring. No field solve.',
        'limits': 'Only rest geometry/UV/ancestry/wall spacing is preserved exactly. Posed spacing, six-pose contact, all482 motion, native/GPU parity and art await measurement. Retained hood/head and lower-front torso crossings remain separate open defects.'}
    (output/'local-paint.json').write_text(json.dumps(report, indent=2)+'\n')
    derivative = dict(receipt)
    derivative['priorConnectedCapBinding'] = derivative.pop('connectedCapBinding')
    derivative.update(status=report['status'], recipe=self_pin, receiver=report['receiver'],
        geometryConstruction=receipt['construction'], construction=pin(output/'local-paint.json'),
        localShoulderPaintBinding={'recipe': self_pin, 'input': pin(checked('receipt')), 'paint': pin(output/'local-paint.json'),
                                  'bodyGuide': pin(checked('body'))},
        correspondenceAndSkin={'kind': 'Local paired-wall shoulder/cap full71 paint', 'rawSourceFieldsPreserved': True,
                               'prior15FieldUnknownAndBoundaryArraysAreHistoricalOnly': True, 'productionFourPassed': False})
    (output/'receiver.json').write_text(json.dumps(derivative, indent=2)+'\n')
    for key in PINS: checked(key)
    assert pin(__file__) == self_pin
    print(json.dumps({'receiver': pin(output/'receiver.json'), 'changedVertices': len(changed), 'acceptedArt': False}), flush=True)
    return output/'receiver.json'


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    assert len(args) == 1; main(args[0])
