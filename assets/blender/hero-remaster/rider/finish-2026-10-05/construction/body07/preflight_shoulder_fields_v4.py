"""One fixed, array-only shoulder partition; never opens/saves Blender.

Candidate raw fields freeze even on predicted failures. No iteration, mask
expansion, alias merge, geometry change, bone edit, or implicit normalization.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
ASSET = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction'
EVIDENCE = ROOT / 'docs/evidence/hero-remaster/finish-2026-10-05'
PINS = {
    ASSET / 'body06/natural-foundation.blend': '66c45ab5a76fe592b0b284a5a96dc3e6ba1f74b2854e5dae849aaff03f43bb77',
    ASSET / 'body06/authored-neck-fields.npz': 'ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a',
    EVIDENCE / 'construction/foundation-source.npz': 'b6eaa2ccee77a9e6f6395daa1fc473da3f6099f26f79895f288e1300b3fba3ae',
}
# This control is conditioned FOUR, never raw source FULL.
PINS.update({
    ROOT / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body52/native-fields.npz': 'deb04faa6a5ca85ca9617cb963d84d5e62074aee281507c5a755fcbe8387d91c',
    ROOT / 'harness/out/rider-finish/body05-intake01/report.json': '4937d207ee8da9f58cf2778b0e4635e094a66e3065440a94bc9229ba95c4494f',
    EVIDENCE / 'runtime/body05-native-contacts01.json': 'eb6cb26a431370a1236599df8ad8158283a913e228ac492b52578832bc5ed66c',
    ROOT / 'harness/rider-finish/geometry-check.mjs': 'ce5e7afc9cbb8edc58a56ef9cdd1ec4c075550d53e4427dc5ebbd9b8b581103b',
    EVIDENCE / 'construction/parent-scope-decision.json': '2de7e9efe4d08c459d814dfebafeea77520a39a30607460d218a1ec6d9bb23fa',
})
EXPECTED_MASK_HASH = {
    'L': ('d0c1a264d58ef526578ff134d693e926e272b28ba6aa6ed3a35eab349912599b', 'c43c8ccff6ea07078597923660a7541291ce6ca05524be43dcd20d320ccaf9c7'),
    'R': ('4729a4564fc6fa5ac2ca3fed193c1790c11270f2c5fda3d7d7bbc7736c49b815', '6a931781a175761d573d974e2ae5c871b09692e01a493a77e071ada151f6aa39'),
}
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def array_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def finite(*values):
    assert all(np.isfinite(value).all() for value in values), 'Nonfinite array product/solve input or output'
def dense_product(left, right):
    finite(left, right)
    result = np.einsum('ij,jk->ik', left, right, optimize=False)
    finite(result)
    return result
def normalized(a):
    a = a.astype(np.float64)
    finite(a)
    sums = a.sum(axis=1)
    assert np.all(sums > 0)
    return a / sums[:, None]
def residual(a):
    r = a.astype(np.float64).sum(axis=1) - 1
    return {'minimum': float(r.min()), 'maximum': float(r.max()), 'maxAbsolute': float(abs(r).max())}
def safe_json(value):
    if isinstance(value, dict):
        return {k: safe_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [safe_json(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value
def freeze_json(path, value):
    with path.open('x') as f:
        json.dump(safe_json(value), f, indent=2, allow_nan=False)
        f.write('\n')

def main(out):
    start = time.monotonic()
    assert not out.exists(), 'Fresh output required'
    for path, expected in PINS.items():
        assert SHA(path) == expected, str(path)
    fields = np.load(ASSET / 'body06/authored-neck-fields.npz')
    foundation = np.load(EVIDENCE / 'construction/foundation-source.npz')
    source = np.load(ROOT / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body52/native-fields.npz')
    intake = ROOT / 'harness/out/rider-finish/body05-intake01'
    manifest = json.loads((intake / 'report.json').read_text())
    rest_path = intake / manifest['rest']['path']
    assert SHA(rest_path) == manifest['rest']['sha256']
    rest = json.loads(gzip.decompress(rest_path.read_bytes()))
    part = rest['parts']['body']
    names = fields['boneNames'].tolist()
    assert names == rest['jointOrder'] == foundation['boneNames'].tolist() == source['boneNames'].tolist()
    assert len(names) == 51
    xyz = fields['bodyRestXYZ']
    faces = fields['bodyTriangles'].astype(np.int32)
    ancestry = fields['bodyAttributeEdgeSources']
    controls = {'full': fields['bodyFullWeights'], 'four': fields['bodyFourWeights']}
    assert len(xyz) == 9183 and len(faces) == 18260
    assert np.array_equal(xyz, np.array(part['xyz'], np.float32))
    assert np.array_equal(faces, np.array(part['faces']))
    for kind in controls:
        assert np.array_equal(controls[kind], np.array(part[kind + 'RawWeights'], np.float32))
    # Source rest matrices stay a separate pinned control. Use actual own51 cache
    # matrices below, never infer new bones or poses from the patch anatomy.
    rig_world = np.array(rest['rigWorldRows'])
    rig_rest = source['rigRest']
    cached_rest = np.array([rest['restBoneRows'][name] for name in names])
    assert cached_rest.shape == (51, 4, 4)
    assert np.array_equal(rig_rest, cached_rest)
    assert np.array_equal(rig_rest, foundation['boneRest'])
    assert np.array_equal(rig_world, source['rigWorld'])
    finite(rig_rest, cached_rest, rig_world)
    edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    neighbors = [set() for _ in xyz]
    for a, b in edges:
        neighbors[a].add(int(b)); neighbors[b].add(int(a))
    proposal = {kind: value.copy() for kind, value in controls.items()}
    masks, descriptions, partitions, arrays = [], {}, {}, {}
    outcome_failures = []
    for side, sign in [('L', -1), ('R', 1)]:
        primary = np.array([names.index('chest'), names.index('shoulder.' + side), names.index('upperArm.' + side)])
        other = np.setdiff1d(np.arange(51), primary)
        H = rig_rest[primary[2], :3, 3].astype(float)
        E = rig_rest[names.index('forearm.' + side), :3, 3].astype(float)
        S = rig_rest[primary[1], :3, 3].astype(float)
        length = np.linalg.norm(E - H); axis = (E - H) / length
        finite(xyz, H, E, S, axis)
        q = np.einsum('ij,j->i', xyz.astype(float) - H, axis, optimize=False) / length
        finite(q)
        lateral = sign * xyz[:, 1].astype(float)
        clavicle = abs(H[1]) - abs(S[1])
        original = (np.arange(len(xyz)) < 9037) & (ancestry[:, 0] == ancestry[:, 1]) & (ancestry[:, 0] >= 0)
        mask = np.flatnonzero(original & (np.linalg.norm(xyz - H, axis=1) <= .13) & (q >= -.45) & (q <= .40)
                              & (lateral >= abs(S[1]) + .2 * clavicle)
                              & (controls['four'][:, primary[1]] + controls['four'][:, primary[2]] >= .02)
                              & (xyz[:, 2] < np.float32(1.54))).astype(np.int32)
        canonical = ancestry[mask, 0].astype(np.int32)
        assert len(mask) == len(np.unique(canonical)) == 219
        assert (array_sha(mask), array_sha(canonical)) == EXPECTED_MASK_HASH[side]
        membership = set(mask.tolist())
        boundary = np.array([v for v in mask if neighbors[v] - membership], np.int32)
        interior = np.setdiff1d(mask, boundary).astype(np.int32)
        shoulder = interior[(lateral[interior] > abs(S[1]) + .5 * clavicle) & (lateral[interior] <= abs(H[1]))
                            & (xyz[interior, 2] > max(H[2], S[2])) & (q[interior] < 0)]
        arm = interior[q[interior] >= .25]
        unknown = np.setdiff1d(interior, np.r_[shoulder, arm]).astype(np.int32)
        assert (len(boundary), len(interior), len(shoulder), len(arm), len(unknown)) == (54, 165, 20, 23, 122)
        assert not np.intersect1d(shoulder, arm).size
        # Dirichlet guards use the current production FOUR primary ratios.
        # One shared three-way anatomical partition is used for FULL and FOUR.
        local = {int(v): i for i, v in enumerate(mask)}
        partition = np.zeros((219, 3), float)
        mass = controls['four'][boundary][:, primary].astype(float).sum(axis=1)
        assert np.all(mass > 0)
        partition[[local[int(v)] for v in boundary]] = controls['four'][boundary][:, primary] / mass[:, None]
        partition[[local[int(v)] for v in shoulder], 1] = 1
        partition[[local[int(v)] for v in arm], 2] = 1
        unknown_index = {int(v): i for i, v in enumerate(unknown)}
        matrix, rhs = np.zeros((122, 122)), np.zeros((122, 3))
        for v, row in unknown_index.items():
            assert neighbors[v] <= membership
            for n in sorted(neighbors[v]):
                distance = np.linalg.norm(xyz[v].astype(float) - xyz[n].astype(float))
                assert distance > 0, 'Zero-length rest edge; no silent epsilon substitution'
                conductance = 1 / distance
                matrix[row, row] += conductance
                if n in unknown_index:
                    matrix[row, unknown_index[n]] -= conductance
                else:
                    rhs[row] += conductance * partition[local[n]]
        finite(matrix, rhs)
        solution = np.linalg.solve(matrix, rhs)
        solution_finite = bool(np.isfinite(solution).all())
        solution_valid = solution_finite and solution.min() >= 0 and np.max(abs(solution.sum(axis=1) - 1)) < 1e-12
        if not solution_valid:
            outcome_failures.append({'side': side, 'kind': 'HARMONIC_PARTITION', 'finite': solution_finite, 'reason': 'First fixed solution violates nonnegative finite unit partition; no clipping/resmoothing'})
        # No clipping or post-solve repartition: preserve the first solved field.
        partition[[local[int(v)] for v in unknown]] = solution
        interior_partition = partition[[local[int(v)] for v in interior]]
        side_info = {'primaryBones': [names[i] for i in primary], 'jointShoulder': S.tolist(), 'jointUpperArm': H.tolist(),
                     'jointElbow': E.tolist(), 'counts': {'mask': 219, 'boundary': 54, 'shoulderAnchor': 20, 'armAnchor': 23, 'unknown': 122},
                     'linearResidualMax': float(abs(dense_product(matrix, solution) - rhs).max()) if solution_finite else None,
                     'partitionSumResidualMax': float(abs(partition.sum(axis=1) - 1).max()), 'partitionMinimum': float(partition.min())}
        for label, ids in [('mask', mask), ('boundary', boundary), ('shoulderAnchor', shoulder), ('armAnchor', arm), ('unknown', unknown)]:
            arrays[side + label + 'NativeIDs'] = ids
            arrays[side + label + 'CanonicalIDs'] = ancestry[ids, 0].astype(np.int32)
            side_info[label] = {'nativeIDs': ids.tolist(), 'canonicalIDs': ancestry[ids, 0].astype(int).tolist(),
                                'nativeInt32SHA256': array_sha(ids), 'canonicalInt32SHA256': array_sha(arrays[side + label + 'CanonicalIDs'])}
        for kind, raw in controls.items():
            old_mass = raw[interior][:, primary].astype(float).sum(axis=1)
            new_mass = old_mass if kind == 'full' else 1 - raw[interior][:, other].astype(float).sum(axis=1)
            if not np.all(new_mass > 0):
                outcome_failures.append({'side': side, 'field': kind, 'kind': 'NONPOSITIVE_PRIMARY_MASS', 'nativeIDs': interior[new_mass <= 0].tolist()})
            proposal[kind][np.ix_(interior, primary)] = (interior_partition * new_mass[:, None]).astype(np.float32)
            other_changed = mask[np.any(proposal[kind][mask][:, other] != raw[mask][:, other], axis=1)]
            boundary_changed = boundary[np.any(proposal[kind][boundary] != raw[boundary], axis=1)]
            if len(other_changed) or len(boundary_changed):
                outcome_failures.append({'side': side, 'field': kind, 'kind': 'SIDE_RAW_PRESERVATION', 'otherChangedNativeIDs': other_changed.tolist(), 'boundaryChangedNativeIDs': boundary_changed.tolist()})
            side_info[kind] = {'sourcePrimaryMassDeltaMin': float((new_mass-old_mass).min()),
                               'sourcePrimaryMassDeltaMax': float((new_mass-old_mass).max()),
                               'sourcePrimaryMassDeltaMaxAbsolute': float(abs(new_mass-old_mass).max()),
                               'boundaryRawSumResidual': residual(raw[boundary]), 'candidateInteriorRawSumResidual': residual(proposal[kind][interior]),
                               'otherBoneRawChanges': len(other_changed), 'boundaryRawChanges': len(boundary_changed)}
        arrays[side + 'HarmonicPartition'] = partition
        masks.append(mask); descriptions[side] = side_info; partitions[side] = (set(boundary), set(shoulder), set(arm))
    mask = np.sort(np.concatenate(masks)).astype(np.int32)
    assert len(np.unique(mask)) == 438
    assert np.array_equal(xyz[mask], source['originalFullXYZ'][ancestry[mask, 0].astype(int)])
    outside = np.setdiff1d(np.arange(len(xyz)), mask)
    for kind, raw in controls.items():
        outside_changed = outside[np.any(proposal[kind][outside] != raw[outside], axis=1)]
        valid = bool(np.isfinite(proposal[kind]).all() and np.all(proposal[kind] >= 0) and np.all(proposal[kind].astype(float).sum(axis=1) > 0))
        if len(outside_changed) or not valid:
            outcome_failures.append({'field': kind, 'kind': 'GLOBAL_RAW_FIELD', 'outsideChangedNativeIDs': outside_changed.tolist(), 'finiteNonnegativePositiveMass': valid})
    # Slot outcomes are measured only after candidate freeze below; never assert
    # a production admission bar before preserving the first solved candidate.
    # Freeze fields/masks before any motion prediction, including failed seams.
    out.mkdir(parents=True)
    arrays.update(productionFullWeights=proposal['full'], productionFourWeights=proposal['four'],
                  body06NativeRawFullReference=controls['full'], body06NativeRawFourReference=controls['four'],
                  body52OriginalRawFullReference=source['originalFullWeights'], body52OriginalXYZReference=source['originalFullXYZ'], mask438NativeIDs=mask,
                  mask438CanonicalIDs=ancestry[mask, 0].astype(np.int32), bodyRestXYZReference=xyz, bodyTrianglesReference=faces,
                  boneNames=np.array(names), own51RigRestReference=rig_rest, own51RigWorldReference=rig_world)
    np.savez_compressed(out / 'frozen-shoulder-fields.npz', **arrays)
    slots = np.count_nonzero(proposal['four'], axis=1)
    invalid_slots = np.flatnonzero(slots > 4)
    if len(invalid_slots):
        outcome_failures.append({'kind': 'FOUR_SLOT_LIMIT', 'maximumSlots': int(slots.max()), 'nativeIDs': invalid_slots.tolist(), 'slotCounts': slots[invalid_slots].tolist()})
    fields_valid = all(np.isfinite(v).all() and np.all(v >= 0) and np.all(v.astype(float).sum(axis=1) > 0) for v in proposal.values())
    # Exact position groups across the WHOLE derivative, including guard/outside
    # rows; no global merge or seam repair. Existing differences are permitted
    # only when their pairwise raw field difference remains exactly unchanged.
    groups = {}
    for v, point in enumerate(xyz):
        groups.setdefault(tuple(float(x) for x in point), []).append(v)
    alias_records, conflicts = [], []
    for ids in groups.values():
        if len(ids) < 2 or not np.intersect1d(ids, mask).size:
            continue
        row = {'nativeIDs': ids, 'canonicalAncestry': ancestry[ids].tolist(), 'membership': [], 'fields': {}}
        for v in ids:
            classification = 'outside438'
            for side, (boundary, shoulder, arm) in partitions.items():
                if v in set(descriptions[side]['mask']['nativeIDs']):
                    classification = side + ':' + ('boundary' if v in boundary else 'shoulderAnchor' if v in shoulder else 'armAnchor' if v in arm else 'unknown')
            row['membership'].append(classification)
        for kind in controls:
            current_delta = controls[kind][ids].astype(float) - controls[kind][ids[0]].astype(float)
            new_delta = proposal[kind][ids].astype(float) - proposal[kind][ids[0]].astype(float)
            consistent = np.array_equal(current_delta, new_delta)
            row['fields'][kind] = {'originalRawRows': controls[kind][ids].tolist(), 'candidateRawRows': proposal[kind][ids].tolist(),
                                   'originalDifferenceSHA256': array_sha(current_delta), 'candidateDifferenceSHA256': array_sha(new_delta),
                                   'differenceUnchanged': bool(consistent), 'originalIdentical': bool(not np.any(current_delta)),
                                   'candidateIdentical': bool(not np.any(new_delta))}
            if not consistent:
                conflicts.append({'nativeIDs': ids, 'field': kind, 'reason': 'Exact coincident-point raw field difference changed; scope review required'})
        alias_records.append(row)
    contacts = json.loads((EVIDENCE / 'runtime/body05-native-contacts01.json').read_text())
    contact_by_index = {r['index']: r for r in contacts['records']}
    witnesses = []
    for r in contacts['records']:
        if r['index'] in [128, 157, 186]:
            for kind in ['full', 'four']:
                for w in r['fields'][kind]['body/body']['properWitnesses']:
                    ids = np.r_[w['nativeVertexIDsA'], w['nativeVertexIDsB']]
                    if not np.isin(ids, mask).all():
                        outcome_failures.append({'kind': 'TARGET_WITNESS_SCOPE', 'index': r['index'], 'field': kind, 'outsideNativeIDs': ids[~np.isin(ids, mask)].tolist()})
                    witnesses.append({'index': r['index'], 'field': kind, 'triangleA': w['triangleA'], 'triangleB': w['triangleB'],
                                      'nativeIDs': ids.tolist(), 'canonicalIDs': ancestry[ids, 0].astype(int).tolist()})
    normal_witness_included = bool(4572 in mask and ancestry[4572, 0] == 8051)
    if not normal_witness_included:
        outcome_failures.append({'kind': 'NORMAL_WITNESS_SCOPE', 'nativeID': 4572})
    affected_faces = np.flatnonzero(np.isin(faces, mask).any(axis=1))
    rest_tri = xyz.astype(float)[faces[affected_faces]]
    rest_area = np.linalg.norm(np.cross(rest_tri[:, 1]-rest_tri[:, 0], rest_tri[:, 2]-rest_tri[:, 0]), axis=1)
    if not np.all(rest_area > 0):
        outcome_failures.append({'kind': 'REST_ZERO_AREAS', 'triangleIDs': affected_faces[rest_area <= 0].tolist()})
    inverse_rig_world = np.linalg.inv(rig_world)
    finite(inverse_rig_world)
    local_to_rig = dense_product(inverse_rig_world, np.array(part['objectWorld']))
    homogeneous = dense_product(np.c_[xyz.astype(float), np.ones(len(xyz))], local_to_rig.T)
    records, prediction_arrays, actual_pins = [], {}, {str(rest_path.relative_to(ROOT)): SHA(rest_path)}
    # Target crossing predicates use the existing independent strict classifier,
    # not a new broad-phase/surface exclusion. Missing novel pairs stay unmeasured.
    classifier = "import{properTriangleCrossing as p}from'./harness/rider-finish/geometry-check.mjs';let s='';for await(const c of process.stdin)s+=c;console.log(JSON.stringify(JSON.parse(s).map(x=>p(x[0],x[1]))));"
    if fields_valid:
        for pin in manifest['samples']:
            path = intake / pin['path']; assert SHA(path) == pin['sha256']
            actual_pins[str(path.relative_to(ROOT))] = pin['sha256']
            sample = json.loads(gzip.decompress(path.read_bytes()))
            skin = np.array(sample['skinNativeRows'])
            assert skin.shape == (51, 4, 4) and np.isfinite(skin).all()
            result = {'index': sample['index'], 'case': sample['case'], 'phase': sample['phase'], 'fields': {}}
            for kind in controls:
                current_rig = np.einsum('vj,jab,vb->va', normalized(controls[kind]), skin, homogeneous, optimize=False)
                predicted_rig = np.einsum('vj,jab,vb->va', normalized(proposal[kind]), skin, homogeneous, optimize=False)
                finite(current_rig, predicted_rig)
                current = dense_product(current_rig, rig_world.T)
                predicted = dense_product(predicted_rig, rig_world.T)
                current, predicted = current[:, :3], predicted[:, :3]
                native = np.array(sample['parts']['body'][kind]['xyzWorld'])
                error = np.linalg.norm(current-native, axis=1).max()
                outside_motion_changed = outside[np.any(current[outside] != predicted[outside], axis=1)]
                if error >= 2e-6 or len(outside_motion_changed):
                    outcome_failures.append({'kind': 'PREDICTION_PARITY_OR_OUTSIDE', 'index': sample['index'], 'field': kind, 'controlManualNativeMaxM': float(error), 'outsideChangedNativeIDs': outside_motion_changed.tolist()})
                finite(current, predicted)
                tri = predicted[faces[affected_faces]]
                area = np.linalg.norm(np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]), axis=1)
                relevant = [w for w in witnesses if w['index'] == sample['index'] and w['field'] == kind]
                tests = [[current[faces[w['triangleA']]].tolist(), current[faces[w['triangleB']]].tolist()] for w in relevant]
                tests += [[predicted[faces[w['triangleA']]].tolist(), predicted[faces[w['triangleB']]].tolist()] for w in relevant]
                checked = []
                if tests:
                    proc = subprocess.run(['node', '--input-type=module', '-e', classifier], cwd=ROOT,
                                          input=json.dumps(tests), text=True, capture_output=True, timeout=15, check=True)
                    checked = json.loads(proc.stdout)
                result['fields'][kind] = {'currentNormalizedManualNativeMaxM': float(error), 'outside438PredictedChanges': len(outside_motion_changed),
                                         'maximumDisplacementM': float(np.linalg.norm(predicted-current, axis=1).max()),
                                         'affectedFaces': len(affected_faces), 'minimumArea2M2': float(area.min()),
                                         'minimumAreaRatioToRest': float((area/rest_area).min()), 'zeroAreaFaces': affected_faces[area < 1e-14].tolist(),
                                         'currentWholeBodyProperCrossings': contact_by_index[sample['index']]['fields'][kind]['body/body']['properCrossings'],
                                         'knownShoulderWitnessPairs': [{'triangleA': w['triangleA'], 'triangleB': w['triangleB'],
                                                                      'currentCrosses': checked[i], 'candidateCrosses': checked[i+len(relevant)]}
                                                                     for i, w in enumerate(relevant)]}
                prediction_arrays[f'sample{sample["index"]:04d}_{kind}_candidateXYZ'] = predicted
                prediction_arrays[f'sample{sample["index"]:04d}_{kind}_controlXYZ'] = current
            records.append(result)
            print('PREDICTED_SAMPLE', sample['index'], 'elapsedS', round(time.monotonic()-start, 3), flush=True)
            del sample
    if fields_valid:
        assert len(records) == 10
    else:
        outcome_failures.append({'kind': 'PREDICTIONS_SKIPPED_INVALID_FIRST_FIELDS', 'measuredSamples': 0})
    np.savez_compressed(out / 'saved-pose-predictions.npz', **prediction_arrays)
    for path, expected in PINS.items():
        assert SHA(path) == expected
    report = {'status': 'STOP_BEFORE_NATIVE_FIELD_OR_SCOPE_FINDING' if conflicts or outcome_failures else 'UNACCEPTED_ARRAY_ONLY_FIXED_SHOULDER_FIELDS',
              'outcomeFailures': outcome_failures, 'fourSlotMaximum': int(slots.max()), 'fourSlotFailureNativeIDs': invalid_slots.tolist(),
              'firstCandidateFrozenBeforeOutcomeAdmission': True, 'predictionStatus': 'MEASURED10' if fields_valid else 'UNMEASURED_INVALID_FIRST_FIELDS',
              'recipeSHA256': SHA(__file__), 'arrayMath': 'Matrix products explicitly einsum optimize=False; multi-input own51 LBS einsum optimize=False. Finite input/output checks around harmonic solve/products. CPU thread caps supplied by COMMAND.', 'elapsedSeconds': time.monotonic()-start,
              'sourcePins': {str(p.relative_to(ROOT)): h for p, h in PINS.items()}, 'nativeCachePins': actual_pins,
              'scope': descriptions, 'targetWitnesses': witnesses, 'currentNormalWitness': {'nativeID': 4572, 'canonicalID': 8051, 'included': normal_witness_included},
              'aliasGroups': alias_records, 'aliasConflicts': conflicts, 'outside438RawChanges': {k: int(np.count_nonzero(np.any(v[outside] != controls[k][outside], axis=1))) for k, v in proposal.items()},
              'outside438SourceRawSumResidual': {k: residual(v[outside]) for k, v in controls.items()},
              'changedNativeIDs': {k: np.flatnonzero(np.any(v != controls[k], axis=1)).tolist() for k, v in proposal.items()},
              'geometryXYZSHA256': array_sha(xyz), 'geometryTriangleInt32SHA256': array_sha(faces),
              'records': records, 'frozenFieldsSHA256': SHA(out / 'frozen-shoulder-fields.npz'),
              'predictionsSHA256': SHA(out / 'saved-pose-predictions.npz'),
              'weightHandling': 'Raw OTHER influences and boundary/outside rows exact. Interior FULL preserves original three-primary raw mass; interior FOUR primary mass is 1 minus original OTHER sum. Float32 storage residual disclosed. Only prediction copies normalized to match measured native LBS; no global raw normalization.',
              'limits': ['First fixed harmonic solution frozen; no native master, export, render, or art pass.',
                         'Target witness tables truncate at16; targeted crossing disappearance does not certify absence of new or other crossings.',
                         'Affected triangle areas measured at10 saved poses; neither rigid-reference normal dot nor positive area proves no folds.',
                         'No new head/neck/boxer fields, positions, UVs, normals, materials, source originals, or rest51 edits.',
                         'Current samples used to formulate proposal are not held-out; later native QA and played mirrored/reverse/grounded clips required.']}
    freeze_json(out / 'preflight.json', report)
    print('FROZEN', report['status'], report['frozenFieldsSHA256'], 'elapsedS', round(time.monotonic()-start, 3), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    main(parser.parse_args().out)
