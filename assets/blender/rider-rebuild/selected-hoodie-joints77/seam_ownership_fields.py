"""Correct arm ownership across the actual seam and retained attachment band.

Topology labels locate the sewn attachment; anatomy determines ownership.
Keep12 far trunk/down hood and the existing native limb fields. No diffusion,
geometry edits, donor anchors, split-bone aliasing, or production-four claim.
"""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE/'author.py'))
ROOT, pin, checked = (A[k] for k in ('ROOT', 'pin', 'checked'))
INPUT = {'path': 'harness/out/rider-rebuild/selected-hoodie-joints77/receiver12/receiver.json',
         'sha256': '115aeff06087f24ca0fac029846e8f492aed699273fdc2d08f7b8cc13ba85139'}
PRIOR = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/whole_anatomical_fields.py',
         'sha256': '22aab060a8bab553c15c0d7f0f22e088eebad2a270d443d54192c63c104e5ed1'}
GRAPH = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/field_repair.py',
         'sha256': 'ce027c64927dfb571bf8c1b1edb5502b619daf9749f78af8ae845a68b14f26e4'}
# Exact six Hermite construction parameters in frozen author.py/build_sleeve.
CAP_U = (.06, .15, .30, .50, .72, .88)


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value*value*(3-2*value)


def inputs():
    previous = runpy.run_path(str(checked(PRIOR)))['verify'](checked(INPUT))
    assert previous['recipe'] == pin(HERE/'author.py')
    rest = json.loads(checked(previous['source47Receipt']).read_text())['expectedRest']
    construction = json.loads(checked(previous['construction']).read_text())
    assert len(rest) == 75
    return previous, rest, construction


def paint(a, rest, construction):
    p, roles = a['positions'], a['vertexRoles']; names = a['groupNames'].tolist()
    assert len(names) == 71
    bones = {bone[0]: bone for bone in rest}; source = np.isin(roles, ('selected_original', 'armhole_seam'))
    G = runpy.run_path(str(checked(GRAPH))); _, _, neighbors = G['graph'](a)
    fields = a['namedFields'].astype(np.float64).copy()
    amount = np.zeros(len(p)); domain = np.zeros(len(p), bool)
    distance_witness = np.full((len(p), 2), -1., np.float64)
    cap_parameter = np.zeros(len(p)); cap_blend = np.zeros(len(p)); generated_rows = []
    construction_rows = {row['side']: row for row in construction if 'side' in row}
    policy = {}
    for si, (side, sign) in enumerate((('L', 1), ('R', -1))):
        source_side = source&(p[:, 0]*sign > 0)
        seam = np.flatnonzero(source_side&(roles == 'armhole_seam'))
        assert len(seam) == sum(construction_rows[side]['sourceBoundaryVertices'])
        graph = [[(j, d) for j, d in row if source_side[j]] if source_side[i] else []
                 for i, row in enumerate(neighbors)]
        distance = G['distances'](graph, seam)
        finite = np.isfinite(distance); distance_witness[finite, si] = distance[finite]
        clavicle = bones['DEF-shoulder.'+side]; proximal = bones['DEF-upper_arm.'+side]
        length = float(np.linalg.norm(np.asarray(clavicle[3])-clavicle[2]))
        medial = float(sign*clavicle[2][0]); lateral = float(sign*clavicle[3][0]); middle = (medial+lateral)*.5
        width = .5*float(np.linalg.norm(np.asarray(proximal[3])-proximal[2]))
        frame, _ = A['bone_frame'](rest, side); origin, axis, _, _ = frame(0)
        station = (p-origin)@axis
        shoulder_z = float(proximal[2][2]); collar_z = float(bones['DEF-spine.004'][2][2])
        assert 0 < medial < middle < lateral and shoulder_z < collar_z and length > 0 and width > 0
        # Same native joint-centered arm ownership as10, now applied to source
        # attachment points too. The actual clavicle span defines its retained
        # surface band; the medial half-clavicle and collar are smooth borders.
        anatomical = smooth((station+width)/(2*width))
        attachment = 1-smooth(distance/length)
        central = smooth((sign*p[:, 0]-medial)/(middle-medial))
        collar = 1-smooth((p[:, 2]-shoulder_z)/(collar_z-shoulder_z))
        alpha = anatomical*attachment*central*collar
        alpha[~source_side] = 0.
        assert np.isfinite(alpha).all() and alpha.min() >= 0 and alpha.max() <= 1
        geometric_band = source_side&finite&(distance < length)&(sign*p[:, 0] > medial)&(p[:, 2] < collar_z)
        assert np.all(alpha[~geometric_band] == 0)
        for vi in np.flatnonzero(alpha > 0):
            limb = A['limb_fields'](p[vi], side, rest, names)
            fields[vi] = (1-alpha[vi])*fields[vi]+alpha[vi]*limb
        amount += alpha; domain |= alpha > 0
        policy[side] = {'clavicleLengthM': length, 'medialAttachmentXAbsoluteM': medial,
                        'midClavicleXAbsoluteM': middle, 'shoulderJointHeightM': shoulder_z,
                        'collarBaseHeightM': collar_z, 'nativeShoulderHalfWidthM': width,
                        'sourceSeamVertices': len(seam), 'topologicalBandVertices': int(geometric_band.sum()),
                        'nonzeroSourceOwnershipVertices': int((alpha > 0).sum()),
                        'seamArmAmountPercentiles': np.percentile(alpha[seam], [0, 50, 100]).tolist()}
    # Source points can belong to the arm. Both walls inherit that corrected
    # seam exactly; a single authored cap parameter reaches the own arm at the
    # first ordinary station, removing the inherited angular torso islands.
    for side in ('L', 'R'):
        spec = construction_rows[side]; perimeter = spec['perimeterVertices']
        cap_count = spec['capTransitionRings']; stations = spec['stationsM']; layer_rows = cap_count+len(stations)
        assert perimeter == 48 and cap_count == len(CAP_U) and stations[0] == .145
        ids = np.flatnonzero(np.asarray([str(role).endswith('_'+side) for role in roles]))
        ids = ids[np.argsort(a['constructionVertexIds'][ids])]
        assert np.all(np.diff(a['constructionVertexIds'][ids]) == 1)
        assert len(ids) == (2*layer_rows+3)*perimeter
        rows = ids.reshape(2*layer_rows+3, perimeter)
        generated_rows.append(rows[:2*layer_rows].reshape(2, layer_rows, perimeter))
        for layer in range(2):
            wall = rows[layer*layer_rows:(layer+1)*layer_rows]
            parents = a['authoredCapSeamParents'][wall[0]]; fractions = a['authoredCapSeamFraction'][wall[0]]
            assert np.all(parents >= 0) and np.all(source[parents])
            assert fractions.min() >= 0 and fractions.max() <= 1
            assert np.array_equal(a['authoredCapSeamParents'][wall], np.broadcast_to(parents, (layer_rows, perimeter, 2)))
            assert np.array_equal(a['authoredCapSeamFraction'][wall], np.broadcast_to(fractions, (layer_rows, perimeter)))
            seam_fields = (1-fractions[:, None])*fields[parents[:, 0]]+fractions[:, None]*fields[parents[:, 1]]
            for ri, row in enumerate(wall):
                if ri < cap_count:
                    assert set(roles[row]) <= {'axilla_'+side, 'shoulder_cap_'+side}
                    u = CAP_U[ri]; blend = float(smooth(u))
                else:
                    assert not any(str(role).startswith(('axilla_', 'shoulder_cap_')) for role in roles[row])
                    u = blend = 1.
                for ci, vi in enumerate(row):
                    limb = A['limb_fields'](p[vi], side, rest, names)
                    fields[vi] = (1-blend)*seam_fields[ci]+blend*limb
                cap_parameter[row] = u; cap_blend[row] = blend
                domain[row] |= (a['authoredSkinBlend'][row] < 1)
        cap_parameter[rows[-3:]] = 1.; cap_blend[rows[-3:]] = 1.
    fields = fields.astype(np.float32)
    assert np.isfinite(fields).all() and fields.min() >= 0 and np.max(abs(fields.sum(1)-1)) < 3e-7
    assert np.array_equal(fields[~domain], a['namedFields'][~domain])
    assert np.array_equal(fields[a['wholeAnatomicalHoodCollar']], a['namedFields'][a['wholeAnatomicalHoodCollar']])
    distal = ~source&(a['authoredSkinBlend'] == 1)
    assert np.array_equal(fields[distal], a['namedFields'][distal])
    for side, sign in (('L', 1), ('R', -1)):
        allowed = {'DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003', 'DEF-shoulder.'+side}
        allowed |= {'DEF-'+part+'.'+side+suffix for part in ('upper_arm', 'forearm') for suffix in ('', '.001')}
        forbidden = [i for i, name in enumerate(names) if name not in allowed]
        assert np.all(fields[np.ix_(np.flatnonzero(p[:, 0]*sign > 0), forbidden)] == 0)
    witnesses = {'seamSourceArmAmount': amount, 'seamAttachmentDistanceM': distance_witness,
                 'seamOwnershipDomain': domain, 'seamCapParameter': cap_parameter,
                 'seamCapBlend': cap_blend, 'seamGeneratedRows': np.asarray(generated_rows, np.int32)}
    return fields, witnesses, policy


def verify(receipt_path):
    row = json.loads(Path(receipt_path).read_text()); binding = row['seamOwnershipBinding']
    assert binding['recipe'] == pin(__file__) and binding['input'] == INPUT
    assert binding['status'] == 'ANATOMICAL_SEAM_ATTACHMENT_OWNERSHIP_UNACCEPTED'
    assert 'wholeAnatomicalFieldBinding' not in row
    previous, rest, construction = inputs()
    assert row['priorWholeAnatomicalFieldBinding'] == previous['wholeAnatomicalFieldBinding']
    assert binding['bodyGuide'] == previous['wholeAnatomicalFieldBinding']['bodyGuide']
    before = np.load(checked(previous['receiver'])); after = np.load(checked(row['receiver']))
    for key in before.files:
        if key not in ('namedFields', 'priorNamedFields'): assert np.array_equal(before[key], after[key]), key
    assert np.array_equal(after['priorNamedFields'], before['namedFields'])
    assert np.array_equal(after['whole12PriorNamedFields'], before['priorNamedFields'])
    fields, witnesses, policy = paint(before, rest, construction)
    assert np.array_equal(after['namedFields'], fields)
    for key, value in witnesses.items(): assert np.array_equal(after[key], value), key
    diagnostic = json.loads(checked(binding['diagnostic']).read_text())
    assert diagnostic['anatomicalPolicy'] == policy and diagnostic['input'] == INPUT
    assert diagnostic['recipe'] == pin(__file__)
    return row


def main(output):
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    previous, rest, construction = inputs(); a = dict(np.load(checked(previous['receiver'])))
    fields, witnesses, policy = paint(a, rest, construction)
    prior = a['namedFields'].copy(); previous_prior = a['priorNamedFields'].copy()
    a.update(namedFields=fields, priorNamedFields=prior, whole12PriorNamedFields=previous_prior, **witnesses)
    output.mkdir(parents=True); np.savez(output/'receiver.npz', **a)
    count, frequency = np.unique((fields > 0).sum(1), return_counts=True)
    report = {'acceptedArt': False, 'recipe': pin(__file__), 'input': INPUT, 'graphHelper': GRAPH,
              'constructionAuthority': previous['construction'], 'anatomicalPolicy': policy,
              'sourceBandArmOwnedVertices': int((witnesses['seamSourceArmAmount'] > 0).sum()),
              'changedFieldVertices': int(np.any(fields != prior, axis=1).sum()),
              'geometryUVAncestryExact': True, 'fieldsOutsideActualDomain12Exact': True,
              'loweredHood12Exact': True, 'priorFullyLimbOwnedRows12Exact': True,
              'supportCountHistogram': {str(k): int(v) for k, v in zip(count, frequency)},
              'controlInventory': len(a['groupNames']), 'productionFourConditioned': False,
              'method': 'Native joint-centered source seam arm ownership in a clavicle-length retained surface band; actual medial attachment/collar taper; six explicit generated cap rows reach uniform own-arm ownership at first ordinary station. Existing12 far trunk/down hood and limb fields retained.',
              'limits': 'One anatomical attachment correction. No new geometry or field diffusion. Actual482/generic/heldout, finite contact, native/GPU parity, genuine bake and played art remain unqualified.'}
    (output/'seam-ownership-fields.json').write_text(json.dumps(report, indent=2)+'\n')
    row = dict(previous); row['receiver'] = pin(output/'receiver.npz')
    row['priorWholeAnatomicalFieldBinding'] = row.pop('wholeAnatomicalFieldBinding')
    row['seamOwnershipBinding'] = {'status': 'ANATOMICAL_SEAM_ATTACHMENT_OWNERSHIP_UNACCEPTED',
        'input': INPUT, 'bodyGuide': previous['wholeAnatomicalFieldBinding']['bodyGuide'], 'recipe': pin(__file__),
        'diagnostic': pin(output/'seam-ownership-fields.json')}
    row['priorWholeAnatomicalCorrespondenceAndSkin'] = previous['correspondenceAndSkin']
    row['correspondenceAndSkin'] = dict(previous['correspondenceAndSkin'], skinStatus=report['method'],
        healthyFieldsExactBeforeFloat32=False, sourceFarFieldAnchorsExact=False,
        attachmentBandOwnedVertices=report['sourceBandArmOwnedVertices'], farTrunk12FieldsExact=True)
    row['correspondenceAndSkin'].pop('wholeAnatomicallyPaintedVertices', None)
    row['priorWholeAnatomicalLimitations'] = previous['limitations']
    row['limitations'] = ['Seam topology ancestry does not imply torso ownership; native shoulder station now paints the attachment.',
        'Geometry/UV/selected ancestry,12far trunk/down hood and already limb-owned rows are exact.',
        'No native/GPU, finite contact, genuine bake, production-four or played art pass.']
    (output/'receiver.json').write_text(json.dumps(row, indent=2)+'\n'); verify(output/'receiver.json')
    print(json.dumps(report), flush=True)


if __name__ == '__main__': main(sys.argv[1])
