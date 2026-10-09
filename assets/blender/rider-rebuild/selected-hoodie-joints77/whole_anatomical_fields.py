"""Whole selected-garment paint using native anatomy and sewn sleeve meridians.

The lowered hood belongs to the collar, not whichever head/body triangle is
nearest. All trunk rows are painted anew before either sleeve inherits its seam.
No field diffusion, frozen donor boundary, bone alias, or top-four reduction.
"""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE/'author.py'))
ROOT, pin, checked = (A[k] for k in ('ROOT', 'pin', 'checked'))
INPUT = {'path': 'harness/out/rider-rebuild/selected-hoodie-joints77/receiver11/receiver.json',
         'sha256': '60dfafa60368969d6eded105ec4d2871bcf20b30ab8985147e4337f6e7de70c2'}
PRIOR = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/wearer_fields.py',
         'sha256': '0330daa6b90700ccdddd2e90df96737832b4edf20f976a47624a07633f476fb1'}
TRUNK = ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003')
SOURCE_ROLES = ('selected_original', 'armhole_seam')
SLEEVE_ROLES = ('shoulder_cap', 'axilla', 'sleeve_panel', 'elbow', 'cuff', 'cuff_rolled_lip')


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value*value*(3-2*value)


def inputs():
    previous = runpy.run_path(str(checked(PRIOR)))['verify'](checked(INPUT))
    rest = json.loads(checked(previous['source47Receipt']).read_text())['expectedRest']
    assert previous['recipe'] == pin(HERE/'author.py') and len(rest) == 75
    return previous, rest


def paint(a, rest):
    """Paint one continuous sleeve/trunk system, retaining the existing topology."""
    p, roles = a['positions'], a['vertexRoles']
    names = a['groupNames'].tolist(); bones = {bone[0]: bone for bone in rest}
    assert len(names) == 71 and all(name in bones for name in names)
    known = set(SOURCE_ROLES)|{role+'_'+side for role in SLEEVE_ROLES for side in ('L', 'R')}
    assert set(roles.tolist()) <= known
    torso = np.zeros((len(p), len(names)), np.float64)
    shoulder_amount = np.zeros(len(p), np.float64)
    spine_centers = np.asarray([(bones[name][2][2]+bones[name][3][2])*.5 for name in TRUNK])
    assert np.all(np.diff(spine_centers) > 0)
    collar_z = float(bones['DEF-spine.004'][2][2])
    lower_chest_z = float(bones['DEF-spine.002'][2][2])
    # Every retained panel gets the same native-height trunk field, including
    # both walls of the lowered hood. The top spine support stops at chest003.
    for vi, point in enumerate(p):
        z = float(point[2])
        if z <= spine_centers[0]:
            torso[vi, names.index(TRUNK[0])] = 1.
        elif z >= spine_centers[-1]:
            torso[vi, names.index(TRUNK[-1])] = 1.
        else:
            index = int(np.searchsorted(spine_centers, z)-1)
            t = float(smooth((z-spine_centers[index])/(spine_centers[index+1]-spine_centers[index])))
            torso[vi, names.index(TRUNK[index])] = 1-t
            torso[vi, names.index(TRUNK[index+1])] = t
        side = 'L' if point[0] >= 0 else 'R'; sign = 1. if side == 'L' else -1.
        name = 'DEF-shoulder.'+side; bone = bones[name]
        medial, lateral = sign*bone[2][0], sign*bone[3][0]
        shoulder_z = float((bone[2][2]+bone[3][2])*.5)
        assert 0 < medial < lateral and lower_chest_z < shoulder_z < collar_z
        # The true clavicle's lateral interval owns the shoulder. This is zero
        # across the central chest, with no opposite-side field propagation.
        lateral_paint = smooth((sign*point[0]-medial)/(lateral-medial))
        elevation_paint = smooth((z-lower_chest_z)/(shoulder_z-lower_chest_z))
        elevation_paint *= 1-smooth((z-shoulder_z)/(collar_z-shoulder_z))
        clavicle = float(lateral_paint*elevation_paint)
        torso[vi] *= 1-clavicle; torso[vi, names.index(name)] += clavicle
        shoulder_amount[vi] = clavicle
    source = np.isin(roles, SOURCE_ROLES)
    blend = a['authoredSkinBlend']; parents = a['authoredCapSeamParents']; fractions = a['authoredCapSeamFraction']
    assert np.isfinite(blend).all() and blend.min() >= 0 and blend.max() <= 1
    assert np.all(blend[source] == 0)
    fields = torso.copy()
    for vi in np.flatnonzero(~source):
        side = str(roles[vi])[-1]; sign = 1 if side == 'L' else -1
        assert p[vi, 0]*sign > 0
        limb = A['limb_fields'](p[vi], side, rest, names)
        if blend[vi] == 1:
            fields[vi] = limb
        else:
            ia, ib = parents[vi]; fraction = float(fractions[vi])
            assert ia >= 0 and ib >= 0 and source[ia] and source[ib] and 0 <= fraction <= 1
            assert p[ia, 0]*sign > 0 and p[ib, 0]*sign > 0
            seam = (1-fraction)*torso[ia]+fraction*torso[ib]
            # This existing coefficient comes from the explicitly authored
            # source seam's measured sleeve meridian, at least80mm, including
            # the compressed axilla. Its exact saved values remain untouched.
            fields[vi] = (1-blend[vi])*seam+blend[vi]*limb
    assert np.isfinite(fields).all() and fields.min() >= 0
    assert np.max(abs(fields.sum(1)-1)) < 1e-12
    # Each side can use the four torso controls and its own clavicle/four arm
    # controls only. These are meaningful authored supports, not pruned weights.
    for side, sign in (('L', 1), ('R', -1)):
        own = set(TRUNK)|{'DEF-'+part+'.'+side for part in ('shoulder', 'upper_arm', 'forearm')}
        own |= {'DEF-upper_arm.'+side+'.001', 'DEF-forearm.'+side+'.001'}
        forbidden = [i for i, name in enumerate(names) if name not in own]
        ids = np.flatnonzero(p[:, 0]*sign > 0)
        assert np.all(fields[np.ix_(ids, forbidden)] == 0)
    hood = source&(p[:, 2] >= collar_z)
    assert hood.any() and np.all(fields[hood, names.index('DEF-spine.003')] == 1)
    assert np.all((fields > 0).sum(1) <= 7)
    return fields, torso, shoulder_amount, hood, {
        'spineCenterHeightsM': spine_centers.tolist(), 'collarBaseHeightM': collar_z,
        'lowerChestHeightM': lower_chest_z,
        'sleeveBlendAuthority': 'Exact authoredSkinBlend/seam parents/fractions from immutable receiver08 topology; authored >=80mm measured meridian transition.',
        'maximumUsefulSupportsByConstruction': 7}


def verify(receipt_path):
    row = json.loads(Path(receipt_path).read_text()); binding = row['wholeAnatomicalFieldBinding']
    assert binding['recipe'] == pin(__file__) and binding['input'] == INPUT
    assert binding['status'] == 'WHOLE_GARMENT_ANATOMICAL_PAINT_UNACCEPTED'
    assert 'wearerFieldBinding' not in row and 'anatomicalFieldRepair' not in row and 'fieldRepair' not in row
    previous, rest = inputs()
    assert row['priorWearerFieldBinding'] == previous['wearerFieldBinding']
    assert binding['bodyGuide'] == previous['wearerFieldBinding']['bodyGuide']
    before = np.load(checked(previous['receiver'])); after = np.load(checked(row['receiver']))
    for key in before.files:
        if key not in ('namedFields', 'priorNamedFields'):
            assert np.array_equal(before[key], after[key]), key
    assert np.array_equal(after['priorNamedFields'], before['namedFields'])
    assert np.array_equal(after['wearer11PriorNamedFields'], before['priorNamedFields'])
    fields, torso, shoulder, hood, construction = paint(before, rest)
    assert after['namedFields'].dtype == np.float32
    for key, expected in (('namedFields', fields.astype(np.float32)), ('wholeAnatomicalTorsoFields', torso),
                          ('wholeAnatomicalClaviclePaint', shoulder), ('wholeAnatomicalHoodCollar', hood)):
        assert np.array_equal(after[key], expected), key
    assert np.max(abs(after['namedFields'].sum(1)-1)) < 3e-7
    diagnostic = json.loads(checked(binding['diagnostic']).read_text())
    assert diagnostic['construction'] == construction
    assert diagnostic['input'] == INPUT and diagnostic['recipe'] == pin(__file__)
    return row


def main(output):
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    previous, rest = inputs(); a = dict(np.load(checked(previous['receiver'])))
    fields, torso, shoulder, hood, construction = paint(a, rest)
    prior = a['namedFields'].copy(); previous_prior = a['priorNamedFields'].copy()
    a.update(namedFields=fields.astype(np.float32), priorNamedFields=prior, wearer11PriorNamedFields=previous_prior,
             wholeAnatomicalTorsoFields=torso, wholeAnatomicalClaviclePaint=shoulder, wholeAnatomicalHoodCollar=hood)
    output.mkdir(parents=True); np.savez(output/'receiver.npz', **a)
    count, frequency = np.unique((a['namedFields'] > 0).sum(1), return_counts=True)
    report = {'acceptedArt': False, 'input': INPUT, 'recipe': pin(__file__), 'construction': construction,
              'allReceiverVerticesRepainted': len(fields), 'hoodCollarOwnedVertices': int(hood.sum()),
              'geometryUVAncestryUnchanged': True, 'raw11BodySampleWitnessesRetainedAsHistory': True,
              'supportCountHistogram': {str(k): int(v) for k, v in zip(count, frequency)},
              'activeNamedControls': [name for name, maximum in zip(a['groupNames'].tolist(), fields.max(0)) if maximum > 0],
              'controlInventory': len(a['groupNames']), 'productionFourConditioned': False,
              'method': 'Whole trunk native spine/clavicle paint; lowered hood follows collar chest003; both sleeves inherit newly painted exact seam parents and measured authored meridian blend to own native limb controls. No nearest-body branch selection or frozen original fields.',
              'limits': 'Authored control-field construction only. Actual482/generic/heldout deformation, finite contact, native/GPU parity, genuine bake and played art remain unqualified.'}
    (output/'whole-anatomical-fields.json').write_text(json.dumps(report, indent=2)+'\n')
    row = dict(previous); row['receiver'] = pin(output/'receiver.npz')
    row['priorWearerFieldBinding'] = row.pop('wearerFieldBinding')
    row['wholeAnatomicalFieldBinding'] = {'status': 'WHOLE_GARMENT_ANATOMICAL_PAINT_UNACCEPTED',
        'input': INPUT, 'bodyGuide': previous['wearerFieldBinding']['bodyGuide'], 'recipe': pin(__file__),
        'diagnostic': pin(output/'whole-anatomical-fields.json')}
    row['priorWearerCorrespondenceAndSkin'] = previous['correspondenceAndSkin']
    row['correspondenceAndSkin'] = dict(previous['correspondenceAndSkin'], skinStatus=report['method'],
        healthyFieldsExactBeforeFloat32=False, sourceFarFieldAnchorsExact=False,
        wholeAnatomicallyPaintedVertices=len(fields), hoodCollarOwnedVertices=int(hood.sum()))
    for key in ('wholeWearerTransferredVertices', 'originalSelectedFieldRowsExactAfterTransfer'):
        row['correspondenceAndSkin'].pop(key, None)
    row['priorWearerLimitations'] = previous['limitations']
    row['limitations'] = ['Every derivative row is anatomically painted; original selected/raw11 fields remain ancestry only.',
        'The lowered hood is collar-owned; sleeve transitions follow actual sewn seam ancestry and measured meridians.',
        'No native/GPU parity, finite contact, genuine atlas/detail bake, production-four or played art pass.']
    (output/'receiver.json').write_text(json.dumps(row, indent=2)+'\n'); verify(output/'receiver.json')
    print(json.dumps(report), flush=True)


if __name__ == '__main__': main(sys.argv[1])
