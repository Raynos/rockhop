"""Parent CPU2 only: validate and reuse saved reference05; no sculpt or resave.

Hidden cage matrix_world/local caches were initially identity while its stored
matrix_basis was already exactly the subsequently evaluated authored matrix.
Refresh before comparison, retaining exact equality for every authored field.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REFERENCE = 'RiderBody__FullAnatomyReference'


def sha(filename):
    digest = hashlib.sha256()
    with Path(filename).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def authored_transform(row):
    # matrix_local is an evaluated cache; matrix_basis and all stored channels
    # remain included and exact. Visibility is restored independently.
    return {k: v for k, v in row.items() if k not in {'matrix_local', 'collections'}}


def validate_recorded_cage(record):
    first = record['firstTransforms']; assert first['parent'] is None
    assert first['constraints'] == [] and first['animation'] is None
    expected = record['observations'][2]['state']
    assert first['matrix_basis'] == expected['matrix']
    original_nonmatrix = {k: v for k, v in record['firstState'].items() if k != 'matrix'}
    assert original_nonmatrix == {k: v for k, v in expected.items() if k != 'matrix'}
    for row in record['observations'][2:]:
        assert row['state'] == expected
        assert row['transforms']['matrix_local'] == expected['matrix']
        assert authored_transform(row['transforms']) == authored_transform(first)
    return expected


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    out = Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    config_path = HERE/'recover-reference06.input.json'; config = json.loads(config_path.read_text())
    assert config['accepted'] is False
    for pin in config['pins'].values(): assert sha(ROOT/pin['path']) == pin['sha256'], pin['path']
    read = lambda name: json.loads((ROOT/config['pins'][name]['path']).read_text())
    checks, observation, membership, contract = [read(n) for n in ['constructionChecks', 'cageObservations', 'membershipReceipt', 'contract']]
    expected_cage = validate_recorded_cage(observation)
    assert checks['recoveryNative'] == config['pins']['recoveryNative']
    assert checks['surfaces'] == config['pins']['surfaceSamples']
    assert membership['arrays'] == config['pins']['membershipArrays']
    assert membership['sourceNative'] == config['pins']['sourceNative'] == observation['sourceNative']
    for key in ['restReturnByteExact', 'allNamedFieldsExact', 'allProtectedSignaturesExact', 'visibleKeysExact', 'originalActionsExact', 'native75RestExact']:
        assert checks['checks'][key] is True, ('Unexpected predecessor failure', key)
    assert checks['checks']['cageExact'] is False and checks['checks']['cageExactAfterSave'] is False
    assert checks['checks']['ownFullAffineMaximumM'] < .000002
    assert checks['checks']['freshInverseTargetMaximumM'] < .000003
    assert checks['checks']['maximumInverseCondition'] < 50
    helper_path = ROOT/config['pins']['referenceHelper']['path']
    spec = importlib.util.spec_from_file_location('reference05_helpers', helper_path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    bpy, np, base = helper.bpy, helper.np, helper.base
    fingerprint, native_helpers = helper.sculpt.protected_signature()
    expected_surfaces = np.load(ROOT/config['pins']['surfaceSamples']['path'], allow_pickle=False)
    expected_membership = np.load(ROOT/config['pins']['membershipArrays']['path'], allow_pickle=False)
    out.mkdir(parents=True); observations = []

    def evaluated_cage(stage):
        cage = bpy.data.objects['A09_PelvicVolumeCage']
        raw = helper.cage_state(cage); stored = helper.cage_transform_state(cage)
        assert authored_transform(stored) == authored_transform(observation['firstTransforms'])
        assert stored['matrix_basis'] == expected_cage['matrix']
        visibility = [(c, c.hide_viewport) for c in cage.users_collection]
        for c, _ in visibility: c.hide_viewport = False
        bpy.context.view_layer.update()
        evaluated = helper.cage_state(cage); refreshed = helper.cage_transform_state(cage)
        for c, previous in visibility: c.hide_viewport = previous
        bpy.context.view_layer.update()
        restored = helper.cage_state(cage); restored_transform = helper.cage_transform_state(cage)
        row = {'stage': stage, 'raw': raw, 'stored': stored, 'evaluated': evaluated, 'restored': restored,
            'rawCacheDifference': helper.exact_difference(raw, evaluated),
            'expectedDifference': helper.exact_difference(expected_cage, evaluated)}
        observations.append(row)
        (out/'exact-cage-reopen.json').write_text(json.dumps({'accepted': False, 'observations': observations}, indent=2)+'\n')
        assert evaluated == expected_cage == restored
        assert refreshed['matrix_local'] == expected_cage['matrix']
        assert restored_transform['matrix_local'] == expected_cage['matrix']
        assert authored_transform(refreshed) == authored_transform(stored) == authored_transform(restored_transform)
        assert stored['collections'] == restored_transform['collections']
        return cage

    # Read original source once for independent protected-state expectations;
    # do not repeat the cage construction, inverse solve, or huge native save.
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/config['pins']['sourceNative']['path']), use_scripts=False)
    bpy.context.scene.frame_set(1); evaluated_cage('original-sculpt03-after-refresh')
    names = list(contract['specification']['meshNames'].values()); protected_names = names+[REFERENCE]
    rig = bpy.data.objects['RiderSkeleton']
    before = {name: fingerprint(bpy.data.objects[name]) for name in protected_names}
    fields = {name: base.named_weights(bpy.data.objects[name], rig) for name in protected_names}
    keys = {name: helper.keys_state(bpy.data.objects[name]) for name in names}
    actions = {a.name: helper.action_state(a) for a in bpy.data.actions}
    assert native_helpers['native_rest'](rig) == contract['nativeRest']['bones']
    original_arrays, original_ids = helper.membership_arrays(bpy.data.objects[REFERENCE], base.xyz(bpy.data.objects[REFERENCE].data.vertices))
    assert set(original_arrays) == set(expected_membership.files)
    for name, array in original_arrays.items(): assert np.array_equal(array, expected_membership[name]), ('Original membership changed', name)
    assert original_ids == membership['identityAttributes']

    bpy.ops.wm.open_mainfile(filepath=str(ROOT/config['pins']['recoveryNative']['path']), use_scripts=False)
    bpy.context.scene.frame_set(1); evaluated_cage('recovery05-after-refresh')
    rig = bpy.data.objects['RiderSkeleton']
    assert before == {name: fingerprint(bpy.data.objects[name]) for name in protected_names}
    assert fields == {name: base.named_weights(bpy.data.objects[name], rig) for name in protected_names}
    assert keys == {name: helper.keys_state(bpy.data.objects[name]) for name in names}
    assert actions == {name: helper.action_state(bpy.data.actions[name]) for name in actions}
    assert native_helpers['native_rest'](rig) == contract['nativeRest']['bones']
    recovered_arrays, recovered_ids = helper.membership_arrays(bpy.data.objects[REFERENCE], base.xyz(bpy.data.objects[REFERENCE].data.vertices))
    assert original_ids == recovered_ids
    for name, array in recovered_arrays.items(): assert np.array_equal(array, original_arrays[name]), ('Recovery membership changed', name)
    reference = bpy.data.objects[REFERENCE]; assert reference.hide_render
    saved_key = reference.data.shape_keys.key_blocks[helper.KEY]
    shape = read('shapeDeltas'); assert shape['object'] == REFERENCE and shape['name'] == helper.KEY
    delta = np.zeros_like(original_arrays[REFERENCE+'_basis'])
    for row in shape['deltas']: delta[row['sourceVertex']] = row['deltaBlender']
    assert np.array_equal(base.xyz(saved_key.data), original_arrays[REFERENCE+'_basis']+delta), 'Saved key differs from recorded fresh inverse'
    hidden = reference.hide_get(); reference.hide_set(False)
    samples = []; objects = [REFERENCE, 'RiderBody', 'RiderJeans']; actual_rest = {}
    for name in objects:
        obj = bpy.data.objects[name]; obj.data.calc_loop_triangles()
        triangles = np.asarray([list(t.vertices) for t in obj.data.loop_triangles], dtype=np.int32)
        assert np.array_equal(triangles, expected_surfaces[name+'_triangles']), ('Full topology mismatch', name)
    for bike in ['rookie', 'pro']:
        rig.animation_data.action = bpy.data.actions['A09_'+bike+'_UNACCEPTED_POSED_VOLUME']
        for frame in [1, 16, 31, 46, 61]:
            bpy.context.scene.frame_set(frame)
            for name in objects:
                actual = base.evaluated_positions(bpy.data.objects[name]); label = f'{bike}_{frame}_{name}'
                assert np.array_equal(actual, expected_surfaces[label]), ('Reopened full surface differs', label)
                if frame == 1: actual_rest[bike+'/'+name] = actual
                if frame == 61: assert np.array_equal(actual, actual_rest[bike+'/'+name]), ('Reopened rest/return differs', bike, name)
                samples.append({'bike': bike, 'frame': frame, 'object': name, 'vertices': len(actual), 'sha256': helper.digest(actual), 'byteExact': True})
    rig.animation_data.action = bpy.data.actions['A09_rookie_UNACCEPTED_POSED_VOLUME']; bpy.context.scene.frame_set(1)
    reference.hide_set(hidden); evaluated_cage('recovery05-after-all-pose-samples')
    assert before == {name: fingerprint(bpy.data.objects[name]) for name in protected_names}
    assert fields == {name: base.named_weights(bpy.data.objects[name], rig) for name in protected_names}
    assert keys == {name: helper.keys_state(bpy.data.objects[name]) for name in names}
    assert actions == {name: helper.action_state(bpy.data.actions[name]) for name in actions}
    assert native_helpers['native_rest'](rig) == contract['nativeRest']['bones']
    report = {'accepted': False, 'status': 'UNACCEPTED_FULL_REFERENCE_COMPANION_EXACT_REOPEN_PASS_CONTACT_PENDING',
        'sourcePins': config['pins'], 'recipeSHA256': sha(__file__), 'inputSHA256': sha(config_path),
        'native': config['pins']['recoveryNative'], 'nativeBytesReusedWithoutSave': True,
        'cause': 'Initially hidden cage world/local caches were stale identity; stored matrix_basis and every authored channel/control already equaled exact refreshed state.',
        'exactEvaluatedCageAndStoredBasis': True, 'noToleranceWaiver': True,
        'allOriginalProtectedFieldsVisibleKeysAndActionsExact': True, 'allOriginalBasisTopologyMapsWeightsAnd75RestExact': True,
        'ownFreshInverseKeyReopenedExact': True, 'nativeRestReturnByteExact': True,
        'fullSurfaceReopenSamples': samples, 'membership': config['pins']['membershipReceipt'],
        'sourceMembershipArrays': config['pins']['membershipArrays'], 'completePosedSurfaces': config['pins']['surfaceSamples'],
        'limits': ['Mechanical recovery validation only; no full-wearer collision, garment clearance, support or art acceptance.',
            'Old author04 construction pose remains rejected; measured new bike controls supersede it before more posed sculpting.',
            'No new native sculpt, mask, player export, animation or map changes. Reference04/05 failures remain retained.']}
    for pin in config['pins'].values(): assert sha(ROOT/pin['path']) == pin['sha256'], pin['path']
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'native': report['native'], 'byteExactReopenSamples': len(samples)}), flush=True)


if __name__ == '__main__': main()
