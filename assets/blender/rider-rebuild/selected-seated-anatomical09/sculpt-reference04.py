"""Parent CPU2 only: hidden full-wearer companion to the actual sculpt03 cage.

The complete reference uses its OWN full named field, never render-body FOUR
deltas. Visible keys, every Basis/topology/map/weight and the original mask are
protected. This saves surfaces for later contact work, not contact acceptance.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sculpt03 as sculpt

base = sculpt.base
bpy, np, Matrix, Vector = base.bpy, base.np, base.Matrix, base.Vector
KEY = sculpt.KEY
REFERENCE = 'RiderBody__FullAnatomyReference'


def digest(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def falloff(point, lower, upper, fraction):
    factor = 1.
    for k in range(3):
        t = (point[k]-lower[k])/(upper[k]-lower[k])
        factor *= sculpt.smoothstep(min(t, 1-t)/fraction)
    return factor


def action_state(action):
    if action is None: return None
    curves = []
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        assert not curve.modifiers, ('Unexpected action modifier', action.name)
                        curves.append({'slot': slot.identifier, 'path': curve.data_path, 'index': curve.array_index,
                            'extrapolation': curve.extrapolation,
                            'points': [[list(p.co), list(p.handle_left), list(p.handle_right),
                                p.handle_left_type, p.handle_right_type, p.interpolation, p.easing]
                                for p in curve.keyframe_points]})
    return {'name': action.name, 'curves': curves}


def keys_state(obj):
    keys = obj.data.shape_keys
    if keys is None: return None
    assert not keys.animation_data or not keys.animation_data.drivers
    return {'relative': keys.use_relative, 'blocks': [{'name': k.name, 'relative': k.relative_key.name,
        'value': k.value, 'mute': k.mute, 'slider': [k.slider_min, k.slider_max], 'group': k.vertex_group,
        'coordinatesSHA256': digest(base.xyz(k.data))} for k in keys.key_blocks],
        'action': action_state(keys.animation_data.action if keys.animation_data else None)}


def cage_state(cage):
    return {'matrix': [list(r) for r in cage.matrix_world],
        'resolution': [cage.data.points_u, cage.data.points_v, cage.data.points_w],
        'interpolation': [cage.data.interpolation_type_u, cage.data.interpolation_type_v, cage.data.interpolation_type_w],
        'controls': [list(p.co_deform) for p in cage.data.points]}


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    out = Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(base.ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    config_path = HERE/'sculpt-reference04.input.json'; config = json.loads(config_path.read_text())
    assert config['accepted'] is False
    for pin in config['pins'].values(): assert base.sha(base.ROOT/pin['path']) == pin['sha256'], pin['path']
    read = lambda key: json.loads((base.ROOT/config['pins'][key]['path']).read_text())
    receipt, contract, original_config, context = [read(k) for k in ['nativeReceipt', 'contract', 'sculptInput', 'bikeContext']]
    assert receipt['native'] == config['pins']['native'] and receipt['basisWeightsRestUVMapsExact']
    assert receipt['shapeKey'] == KEY and receipt['recipeSHA256'] == config['pins']['sculptRecipe']['sha256']
    assert receipt['inputSHA256'] == config['pins']['sculptInput']['sha256']
    assert original_config['pins']['bikeContext'] == config['pins']['bikeContext']
    assert receipt['poseQualification'] == 'REJECTED_AUTHOR04_CONSTRUCTION_WITNESS'
    bpy.ops.wm.open_mainfile(filepath=str(base.ROOT/config['pins']['native']['path']), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; reference = bpy.data.objects[REFERENCE]
    visible = [bpy.data.objects[n] for n in contract['specification']['meshNames'].values()]
    protected = visible+[reference]; fingerprint, helpers = sculpt.protected_signature()
    protected_names = [o.name for o in protected]
    assert reference.hide_render and not reference.data.shape_keys and reference.matrix_world.is_identity
    assert bpy.data.objects['RiderBody']['outfitFullBodyReference'] == REFERENCE
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    bpy.context.scene.frame_set(1)
    before = {o.name: fingerprint(o) for o in protected}
    fields = {o.name: base.named_weights(o, rig) for o in protected}
    visible_keys = {o.name: keys_state(o) for o in visible}
    saved_actions = {a.name: action_state(a) for a in bpy.data.actions}
    basis = base.xyz(reference.data.vertices)
    own_fields = fields[REFERENCE]; assert len(own_fields) == len(basis)
    assert len(own_fields) == len(fields['RiderBody']), 'Existing mask must retain all source vertex ordinals'
    assert all(row and set(row) <= set(rig.pose.bones.keys()) and all(w > 0 for w in row.values()) for row in own_fields)
    arms = [m for m in reference.modifiers if m.type == 'ARMATURE']
    assert len(arms) == 1 and arms[0].object == rig and not arms[0].use_deform_preserve_volume
    assert all(m.type in {'ARMATURE', 'TRIANGULATE'} for m in reference.modifiers)
    cage = bpy.data.objects['A09_PelvicVolumeCage']; saved_cage = cage_state(cage)
    assert saved_cage['controls'] == receipt['cage']['targetControls']
    assert saved_cage['resolution'] == [original_config['cageResolution']]*3
    assert saved_cage['interpolation'] == ['KEY_BSPLINE']*3
    lower, upper = [Vector(v) for v in receipt['cage']['boundsBike']]
    to_bike = Matrix(context['nativeToBike'])
    hidden = reference.hide_get(); reference.hide_set(False)
    rig.animation_data.action = bpy.data.actions['A09_rookie_UNACCEPTED_POSED_VOLUME']
    bpy.context.scene.frame_set(31); bpy.context.view_layer.update()
    posed = base.evaluated_positions(reference)
    collection = bpy.data.collections.new('A09_FULL_REFERENCE_COMPANION'); bpy.context.scene.collection.children.link(collection)
    working = reference.copy(); working.data = reference.data.copy(); working.animation_data_clear()
    working.name = REFERENCE+'__A09_PosedSculpt'; working.modifiers.clear(); working.hide_render = True
    collection.objects.link(working); working.hide_set(False); working.data.vertices.foreach_set('co', posed.ravel()); working.data.update()
    group = working.vertex_groups.new(name='A09_shared_spatial_cage_falloff')
    for i, p in enumerate(posed):
        factor = falloff(to_bike @ Vector(p), lower, upper, original_config['boundaryFalloffFraction'])
        if factor: group.add([i], factor, 'REPLACE')
    modifier = working.modifiers.new('A09 same saved full-wearer volume', 'LATTICE')
    modifier.object = cage; modifier.vertex_group = group.name
    cage_collections = [(c, c.hide_viewport) for c in cage.users_collection]
    for c, _ in cage_collections: c.hide_viewport = False
    bpy.context.view_layer.update(); target = base.evaluated_positions(working)

    # Normalize THIS complete reference's actual full weights exactly as native
    # LBS does. Verify against native evaluation before any inverse is trusted.
    operators = {b.name: np.asarray(b.matrix @ rig.data.bones[b.name].matrix_local.inverted(), dtype=np.float64)
                 for b in rig.pose.bones}
    rest_delta = np.zeros_like(basis); source_residual = 0.; condition_max = 0.
    for i, row in enumerate(own_fields):
        matrix = sum(operators[n]*w for n, w in row.items())/sum(row.values())
        expected = (matrix @ np.append(basis[i], 1.))[:3]
        source_residual = max(source_residual, float(np.linalg.norm(expected-posed[i])))
        change = target[i]-posed[i]
        if np.linalg.norm(change) < .000001: continue
        condition = float(np.linalg.cond(matrix[:3, :3])); condition_max = max(condition_max, condition)
        assert condition < 50, ('Full reference inverse is ill-conditioned', i, condition)
        rest_delta[i] = np.linalg.solve(matrix[:3, :3], change)
    assert source_residual < .000002, ('Own full-weight affine pose differs from actual native reference', source_residual)
    moved = np.flatnonzero(np.linalg.norm(rest_delta, axis=1) > 1e-9).tolist(); assert moved
    protected_arms = {b.name for side in ['Left', 'Right'] for b in [rig.pose.bones[contract['specification']['roles']['shoulder'+side]],
        *rig.pose.bones[contract['specification']['roles']['shoulder'+side]].children_recursive]}
    assert all(not(set(own_fields[i]) & protected_arms) for i in moved), 'Pelvic companion reached arms/hands'
    assert min(float(basis[i][2]) for i in moved) > .40, 'Pelvic companion reached lower hem ownership'
    reference.shape_key_add(name='Basis', from_mix=False); key = reference.shape_key_add(name=KEY, from_mix=False)
    key.data.foreach_set('co', (basis+rest_delta).ravel()); key.value = 1.; bpy.context.view_layer.update()
    target_residual = float(np.max(np.linalg.norm(base.evaluated_positions(reference)-target, axis=1)))
    assert target_residual < .000003, ('Own-field inverse failed full reference target', target_residual)
    for frame, value in [(1, 0.), (31, 1.), (61, 0.)]:
        key.value = value; key.keyframe_insert('value', frame=frame)
    reference.data.shape_keys.animation_data.action.name = 'A09_FULL_REFERENCE_VOLUME_DIAGNOSTIC'
    sculpt.linear_shape_action(reference)

    # Full native topology and arrays include every vertex, including masked
    # render-body orphans. Reference ordinals are stable source indices; no new
    # mesh identity attribute, mask, deletion, or geometric collision claim.
    arrays, samples = {REFERENCE+'_basis': basis.copy()}, {}
    identity_attributes = {}
    for name in ['_NATIVE_ID', '_SOURCE_VERTEX_ID', '_REGION_ID']:
        attribute = reference.data.attributes.get(name)
        if attribute is None:
            identity_attributes[name] = {'present': False, 'invented': False}
            continue
        assert attribute.domain == 'POINT' and attribute.data_type in {'INT', 'FLOAT'}, ('Unexpected original identity attribute', name)
        values = np.empty(len(basis), dtype=np.int32 if attribute.data_type == 'INT' else np.float32)
        attribute.data.foreach_get('value', values)
        label = REFERENCE+'_'+name; arrays[label] = values
        identity_attributes[name] = {'present': True, 'invented': False, 'domain': attribute.domain,
            'dataType': attribute.data_type, 'array': label, 'sha256': digest(values)}
    surfaces = [reference, bpy.data.objects['RiderBody'], bpy.data.objects['RiderJeans']]
    surface_names = [o.name for o in surfaces]
    for obj in surfaces:
        obj.data.calc_loop_triangles()
        arrays[obj.name+'_triangles'] = np.asarray([list(t.vertices) for t in obj.data.loop_triangles], dtype=np.int32)
    for bike in ['rookie', 'pro']:
        rig.animation_data.action = bpy.data.actions['A09_'+bike+'_UNACCEPTED_POSED_VOLUME']; samples[bike] = {}
        for frame in [1, 16, 31, 46, 61]:
            bpy.context.scene.frame_set(frame); samples[bike][frame] = {}
            for obj in surfaces:
                actual = base.evaluated_positions(obj); label = f'{bike}_{frame}_{obj.name}'; arrays[label] = actual
                samples[bike][frame][obj.name] = {'vertices': len(actual), 'positionSHA256': digest(actual)}
                if frame == 61: assert np.array_equal(actual, arrays[f'{bike}_1_{obj.name}']), ('Rest/return not byte-exact', bike, obj.name)
    rig.animation_data.action = bpy.data.actions['A09_rookie_UNACCEPTED_POSED_VOLUME']; bpy.context.scene.frame_set(1)
    reference.hide_set(hidden); collection.hide_render = True; collection.hide_viewport = True
    for c, previous in cage_collections: c.hide_viewport = previous
    assert fields == {o.name: base.named_weights(o, rig) for o in protected}
    assert before == {o.name: fingerprint(o) for o in protected}
    assert visible_keys == {o.name: keys_state(o) for o in visible}
    assert saved_cage == cage_state(cage)
    assert saved_actions == {name: action_state(bpy.data.actions[name]) for name in saved_actions}
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    out.mkdir(parents=True); blend = out/'selected-anatomical09-full-reference-volume.blend'
    np.savez_compressed(out/'full-wearer-surface-samples.npz', **arrays)
    (out/'reference-shape-key.json').write_text(json.dumps({'accepted': False, 'name': KEY, 'object': REFERENCE,
        'indexMeaning': 'Unchanged full-reference source vertex ordinal; no new _NATIVE_ID attribute added',
        'sourceNative': config['pins']['native'], 'ownNamedWeightsSHA256': hashlib.sha256(json.dumps(own_fields, sort_keys=True).encode()).hexdigest(),
        'deltas': [{'sourceVertex': i, 'deltaBlender': rest_delta[i].tolist()} for i in moved]})+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False)
    bpy.data.objects[REFERENCE].hide_set(False)
    reopened = {}
    for name in surface_names:
        obj = bpy.data.objects[name]
        for frame in [1, 31, 61]:
            bpy.context.scene.frame_set(frame); actual = base.evaluated_positions(obj)
            assert np.array_equal(actual, arrays[f'rookie_{frame}_{name}']), ('Reopened actual surface differs', name, frame)
        reopened[name] = 'Byte-exact rest/key/return'
    bpy.context.scene.frame_set(1)
    bpy.data.objects[REFERENCE].hide_set(hidden)
    reopened_protected = [bpy.data.objects[name] for name in protected_names]
    assert before == {o.name: fingerprint(o) for o in reopened_protected}
    assert fields == {o.name: base.named_weights(o, bpy.data.objects['RiderSkeleton']) for o in reopened_protected}
    assert visible_keys == {name: keys_state(bpy.data.objects[name]) for name in visible_keys}
    assert np.array_equal(base.xyz(bpy.data.objects[REFERENCE].data.vertices), basis)
    report = {'accepted': False, 'status': 'UNACCEPTED_FULL_REFERENCE_COMPANION_CONTACT_PENDING',
        'sourcePins': config['pins'], 'recipeSHA256': base.sha(__file__), 'inputSHA256': base.sha(config_path),
        'native': {'path': str(blend.relative_to(base.ROOT)), 'sha256': base.sha(blend)}, 'shapeKey': KEY,
        'referenceObject': REFERENCE, 'fullReferenceVertices': len(basis), 'movedReferenceVertices': len(moved),
        'ownSavedFullField': {'maximumInfluences': max(map(len, own_fields)),
            'rowsDifferentFromRenderBody': sum(a != b for a, b in zip(own_fields, fields['RiderBody'])),
            'copiedRenderFourDeltas': False},
        'inverseChecks': {'sourceAffineM': source_residual, 'posedTargetM': target_residual, 'maximumInverseCondition': condition_max},
        'originalVisibleKeysAndActionsExact': True, 'allBasisTopologyUVMapsWeightsAnd75RestExact': True,
        'savedCageControlsAndMatrixExact': True, 'noNewMask': True,
        'shapeAnimation': {'interpolation': 'LINEAR', 'frames': [1, 31, 61], 'values': [0, 1, 0]},
        'restReturnByteExact': True, 'reopenedSurfaces': reopened, 'samples': samples,
        'surfaceScope': {'objects': [REFERENCE, 'RiderBody', 'RiderJeans'], 'allNativeVerticesAndTriangles': True,
            'renderBodyUnusedVerticesIncluded': True, 'referenceExported': False,
            'originalReferenceBasisArray': REFERENCE+'_basis', 'originalIdentityAttributes': identity_attributes},
        'limits': ['Complete wearer and Jeans arrays are inspection inputs only; no collision, enclosure, support or art pass.',
            'Same rejected author04 key and existing authored skeletal action midpoint curves; no new posture or runtime activation.',
            'No player export. Visible Body/Jeans geometry and existing keys remain unchanged.']}
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    for pin in config['pins'].values(): assert base.sha(base.ROOT/pin['path']) == pin['sha256']
    print(json.dumps({k: report[k] for k in ['status', 'native', 'movedReferenceVertices', 'ownSavedFullField', 'inverseChecks', 'reopenedSurfaces']}), flush=True)


if __name__ == '__main__': main()
