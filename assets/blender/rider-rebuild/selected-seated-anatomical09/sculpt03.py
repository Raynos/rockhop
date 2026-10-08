"""Parent CPU2 only: one editable shared pelvic cage, then fresh inverse skin.

The current author04 key is a rejected construction witness, not a final pose.
No general vertex solve, old corrective, body mask, topology edit or export.
"""
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import author as base

bpy, np, Matrix, Vector = base.bpy, base.np, base.Matrix, base.Vector
KEY = 'A09_SeatedVolume'


def protected_signature():
    # Permit the explicitly added Key datablock. Keep the original complete
    # rest geometry, normals, UV, group fields, materials and transforms hash.
    _, helpers = base.protected_signature()
    source = inspect.getsource(helpers['part_fingerprint'])
    clause = "assert obj.type == 'MESH' and not mesh.shape_keys and obj.animation_data is None"
    assert source.count(clause) == 1
    source = source.replace(clause, "assert obj.type == 'MESH' and obj.animation_data is None")
    namespace = dict(helpers); exec(source, namespace)
    return lambda obj: namespace['part_fingerprint'](obj, {'np': np}), helpers


def linear_shape_action(obj):
    action = obj.data.shape_keys.animation_data.action; found = 0
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation = 'LINEAR'; found += 1
    assert found == 3, ('Expected exactly three scalar diagnostic shape keys', obj.name, found)


def smoothstep(t):
    t = max(0., min(1., t)); return t*t*(3-2*t)


def kernel(point, center, radius):
    r = sum(((point[k]-center[k])/radius[k])**2 for k in range(3))**.5
    return 1-r*r*r*(10-15*r+6*r*r) if r < 1 else 0.


def saddle_height(x, z, triangles):
    """Finite actual top only. A missing guide footprint is a source failure."""
    hits = []
    for t in triangles:
        if not t['upward']: continue
        a, b, c = [Vector(p) for p in t['pointsBike']]
        denominator = (b.z-c.z)*(a.x-c.x)+(c.x-b.x)*(a.z-c.z)
        if abs(denominator) < 1e-12: continue
        u = ((b.z-c.z)*(x-c.x)+(c.x-b.x)*(z-c.z))/denominator
        v = ((c.z-a.z)*(x-c.x)+(a.x-c.x)*(z-c.z))/denominator
        if min(u, v, 1-u-v) >= -1e-8:
            hits.append((u*a.y+v*b.y+(1-u-v)*c.y, t['sourceTriangleOrdinal']))
    assert hits, ('Artist bearing guide misses actual finite saddle', x, z)
    return max(hits)


def main():
    out = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    assert not out.exists() and out.is_relative_to(base.ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    config = json.loads((HERE/'sculpt03.input.json').read_text())
    for pin in config['pins'].values(): assert base.sha(base.ROOT/pin['path']) == pin['sha256'], pin['path']
    read = lambda name: json.loads((base.ROOT/config['pins'][name]['path']).read_text())
    native_receipt, contract, selection, context, patches = [read(n) for n in ['nativeReceipt', 'contract', 'selection', 'bikeContext', 'patches']]
    assert native_receipt['supportCorrection']['rankPruning'] is False
    assert native_receipt['native']['sha256'] == config['pins']['native']['sha256']
    pose_pin = native_receipt['diagnosticPoses'][config['bike']]
    assert base.sha(base.ROOT/pose_pin['path']) == pose_pin['sha256']
    pose = json.loads((base.ROOT/pose_pin['path']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(base.ROOT/config['pins']['native']['path']), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; objects = [bpy.data.objects[n] for n in ['RiderJeans', 'RiderBody']]
    assert len(rig.data.bones) == 75 and rig.matrix_world.is_identity
    fingerprint, helpers = protected_signature()
    protected = [bpy.data.objects[n] for n in contract['specification']['meshNames'].values()]
    protected.append(bpy.data.objects['RiderBody__FullAnatomyReference'])
    signatures = {o.name: fingerprint(o) for o in protected}
    fields = {o.name: base.named_weights(o, rig) for o in protected}
    basis = {o.name: base.xyz(o.data.vertices) for o in objects}
    assert all(not o.data.shape_keys and o.matrix_world.is_identity for o in objects)
    for obj in objects:
        assert [a.value for a in obj.data.attributes['_NATIVE_ID'].data] == list(range(len(obj.data.vertices)))
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    base.reset_pose(rig); base.set_target_pose(rig, base.pose_targets(pose, rig))
    posed = {o.name: base.evaluated_positions(o) for o in objects}
    to_bike, to_native = Matrix(context['nativeToBike']), Matrix(context['bikeToNative'])
    bike = next(b for b in context['bikes'] if b['name'] == config['bike'])
    groups = selection['jeans']['groups']
    center = lambda ids: sum((to_bike @ Vector(posed['RiderJeans'][i]) for i in ids), Vector())/len(ids)

    # Artist-authored broad handles. The guide patches have positive finite
    # area; their centroids position cage handles, never project mesh vertices.
    guides, handles = {}, []
    for side in ['left', 'right']:
        points, witnesses = [], []
        for x in config['bearingGuide']['bikeX']:
            for z in config['bearingGuide']['bikeZ'][side]:
                y, row = saddle_height(x, z, bike['saddle'])
                points.append(Vector((x, y+config['bearingGuide']['offsetM'], z))); witnesses.append(row)
        core = [v['id'] for v in patches['patches'][side]['core']['nativeVertices']]
        origin = center(core); target = sum(points, Vector())/len(points)
        delta = target-origin
        assert delta.length <= config['maximumBearingHandleMoveM'], ('Author a different pelvis pose before a large volume pull', side, delta.length)
        handles.append({'name': 'bearing_'+side, 'center': origin, 'delta': delta,
                        'radius': config['bearingGuide']['radiusM'], 'sourceNativeIDs': core})
        guides[side] = {'pointsBike': [list(p) for p in points], 'sourceTriangleOrdinals': witnesses,
            'projectedAreaM2': (max(config['bearingGuide']['bikeX'])-min(config['bearingGuide']['bikeX']))*
                              abs(config['bearingGuide']['bikeZ'][side][1]-config['bearingGuide']['bikeZ'][side][0]),
            'meaning': 'Authored finite underside guide, not measured rider contact or support acceptance.'}
    for edit in config['grabs']:
        handles.append({'name': edit['name'], 'center': center(groups[edit['group']]),
            'delta': Vector(edit['deltaBikeM']), 'radius': edit['radiusM'], 'sourceNativeIDs': groups[edit['group']]})

    # Both layers use one world-space volume, including complete incident waist
    # faces. No independently selected nearest cloth corner moves a body face.
    waist = set(selection['body']['crossingWitnessNativeIDs']); body = objects[1]
    incident = [p for p in body.data.polygons if waist.intersection(p.vertices)]
    whole = sorted({i for p in incident for i in p.vertices})
    bounds_points = [to_bike @ Vector(posed['RiderJeans'][i]) for i in selection['jeans']['domain']]
    bounds_points += [to_bike @ Vector(posed['RiderBody'][i]) for i in whole]
    lower = Vector(tuple(min(p[k] for p in bounds_points)-config['paddingM'][k] for k in range(3)))
    upper = Vector(tuple(max(p[k] for p in bounds_points)+config['paddingM'][k] for k in range(3)))
    span, middle = upper-lower, (upper+lower)/2
    collection = bpy.data.collections.new('A09_EDITABLE_POSED_VOLUME'); bpy.context.scene.collection.children.link(collection)
    data = bpy.data.lattices.new('A09_PelvicVolumeCage'); data.points_u = data.points_v = data.points_w = config['cageResolution']
    data.interpolation_type_u = data.interpolation_type_v = data.interpolation_type_w = 'KEY_BSPLINE'
    cage = bpy.data.objects.new(data.name, data); collection.objects.link(cage)
    cage.matrix_world = to_native @ Matrix.Translation(middle) @ Matrix.Diagonal((*span, 1.))
    cage.show_in_front = True; cage.hide_render = True
    original_controls, control_targets = [], []
    for point in data.points:
        original = point.co_deform.copy(); position = middle+Vector(tuple(original[k]*span[k] for k in range(3)))
        delta = sum((h['delta']*kernel(position, h['center'], h['radius']) for h in handles), Vector())
        # Fixed outer cage controls keep the volume boundary continuous.
        if any(abs(original[k]) > .499 for k in range(3)): delta = Vector()
        point.co_deform = original+Vector(tuple(delta[k]/span[k] for k in range(3)))
        original_controls.append(list(original)); control_targets.append(list(point.co_deform))
    for h in handles:
        empty = bpy.data.objects.new('A09_'+h['name']+'_TARGET', None); collection.objects.link(empty)
        empty.empty_display_type = 'ARROWS'; empty.empty_display_size = .025
        empty.location = to_native @ (h['center']+h['delta']); empty.hide_render = True
    guide_vertices = [to_native @ Vector(p) for g in guides.values() for p in g['pointsBike']]
    guide_mesh = bpy.data.meshes.new('A09_actual_saddle_guide_points'); guide_mesh.from_pydata(guide_vertices, [], [])
    guide = bpy.data.objects.new(guide_mesh.name, guide_mesh); collection.objects.link(guide); guide.hide_render = True

    working, target = {}, {}
    for obj in objects:
        copy = obj.copy(); copy.data = obj.data.copy(); copy.animation_data_clear(); copy.name = obj.name+'__A09_PosedSculpt'
        collection.objects.link(copy); copy.modifiers.clear(); copy.hide_render = True
        copy.data.vertices.foreach_set('co', posed[obj.name].ravel()); copy.data.update()
        group = copy.vertex_groups.new(name='A09_shared_spatial_cage_falloff')
        for i, p in enumerate(posed[obj.name]):
            q = to_bike @ Vector(p); uvw = [(q[k]-lower[k])/span[k] for k in range(3)]
            factor = 1.
            for t in uvw: factor *= smoothstep(min(t, 1-t)/config['boundaryFalloffFraction'])
            if factor: group.add([i], factor, 'REPLACE')
        modifier = copy.modifiers.new('A09 shared posed pelvic volume', 'LATTICE'); modifier.object = cage; modifier.vertex_group = group.name
        working[obj.name] = copy
    bpy.context.view_layer.update()
    for obj in objects: target[obj.name] = base.evaluated_positions(working[obj.name])

    # Fresh affine inverses from THIS frozen named field and THIS actual pose.
    inverse_rest = {b.name: b.matrix_local.inverted() for b in rig.data.bones}
    operators = {b.name: np.asarray(b.matrix @ inverse_rest[b.name], dtype=np.float64) for b in rig.pose.bones}
    deltas, residuals, moved = {}, {}, {}
    for obj in objects:
        name = obj.name; rest_delta = np.zeros_like(basis[name]); source_residual = 0.; condition_max = 0.
        for i, row in enumerate(fields[name]):
            weights_sum = sum(row.values()); matrix = sum(operators[n]*w for n, w in row.items())/weights_sum
            expected = (matrix @ np.append(basis[name][i], 1.))[:3]
            source_residual = max(source_residual, float(np.linalg.norm(expected-posed[name][i])))
            change = target[name][i]-posed[name][i]
            if np.linalg.norm(change) < .000001: continue
            condition = float(np.linalg.cond(matrix[:3, :3])); condition_max = max(condition_max, condition)
            assert condition < 50, ('Ill-conditioned inverse: do not sculpt through collapsed skin', name, i, condition)
            rest_delta[i] = np.linalg.solve(matrix[:3, :3], change)
        assert source_residual < .000002, ('Fresh affine skin differs from actual native evaluation', name, source_residual)
        ids = np.flatnonzero(np.linalg.norm(rest_delta, axis=1) > 1e-9).tolist(); assert ids
        if name == 'RiderJeans': assert min(float(basis[name][i][2]) for i in ids) > .40, 'Sculpt reached wardrobe lower-hem ownership'
        protected_arms = {b.name for side in ['Left', 'Right'] for b in [rig.pose.bones[contract['specification']['roles']['shoulder'+side]], *rig.pose.bones[contract['specification']['roles']['shoulder'+side]].children_recursive]}
        if name == 'RiderBody': assert all(not(set(fields[name][i]) & protected_arms) for i in ids), 'Pelvic cage reached an arm/hand'
        obj.shape_key_add(name='Basis', from_mix=False); key = obj.shape_key_add(name=KEY, from_mix=False)
        key.data.foreach_set('co', (basis[name]+rest_delta).ravel()); key.value = 1.
        bpy.context.view_layer.update()
        error = float(np.max(np.linalg.norm(base.evaluated_positions(obj)-target[name], axis=1)))
        assert error < .000003, ('Fresh inverse failed saved target', name, error)
        deltas[name] = [{'nativeID': i, 'deltaBlender': rest_delta[i].tolist(),
                        'deltaGLTF': [float(rest_delta[i][0]), float(rest_delta[i][2]), -float(rest_delta[i][1])]} for i in ids]
        moved[name] = len(ids); residuals[name] = {'sourceAffineM': source_residual, 'posedTargetM': error, 'maximumInverseCondition': condition_max}

    # Preserve all original fields and Basis, save explicit rest/key/return work.
    for obj in objects:
        for frame, value in [(1, 0.), (31, 1.), (61, 0.)]:
            obj.data.shape_keys.key_blocks[KEY].value = value
            obj.data.shape_keys.key_blocks[KEY].keyframe_insert('value', frame=frame)
        linear_shape_action(obj)
    assert fields == {o.name: base.named_weights(o, rig) for o in protected}
    assert signatures == {o.name: fingerprint(o) for o in protected}
    assert helpers['native_rest'](rig) == contract['nativeRest']['bones']
    samples, arrays = {}, {}
    rig.animation_data_create()
    for bike_name in ['rookie', 'pro']:
        original_action = bpy.data.actions['A09_'+bike_name+'_REJECTED_POSE_WEIGHT_DIAGNOSTIC']
        action = original_action.copy(); action.name = 'A09_'+bike_name+'_UNACCEPTED_POSED_VOLUME'; action.use_fake_user = True
        rig.animation_data.action = action; samples[bike_name] = {}
        for frame in [1, 16, 31, 46, 61]:
            bpy.context.scene.frame_set(frame); samples[bike_name][frame] = {}
            for obj in objects:
                evaluated = base.evaluated_positions(obj); arrays[f'{bike_name}_{frame}_{obj.name}'] = evaluated
                if frame in (1, 61): assert float(np.max(np.linalg.norm(evaluated-basis[obj.name], axis=1))) < .000002
                samples[bike_name][frame][obj.name] = {'minimumNativeXYZ': evaluated.min(axis=0).tolist(), 'maximumNativeXYZ': evaluated.max(axis=0).tolist()}
    rig.animation_data.action = bpy.data.actions['A09_rookie_UNACCEPTED_POSED_VOLUME']; bpy.context.scene.frame_set(1)
    collection.hide_render = True; collection.hide_viewport = True
    rig['A09_sculpt'] = 'UNACCEPTED posed volume. Author04 diagnostic key is not final posture; finite contacts/crossings/moving appearance remain open.'
    out.mkdir(parents=True); blend = out/'selected-anatomical09-posed-volume.blend'
    for obj in objects:
        obj.data.calc_loop_triangles(); arrays[obj.name+'_triangles'] = np.asarray([list(t.vertices) for t in obj.data.loop_triangles], dtype=np.int32)
    np.savez_compressed(out/'posed-surface-samples.npz', **arrays)
    (out/'shape-key.json').write_text(json.dumps({'accepted': False, 'name': KEY, 'relative': True,
        'sourceNative': config['pins']['native'], 'sourceWeights': config['pins']['nativeReceipt'], 'posePin': pose_pin,
        'deltas': deltas, 'activation': 'LINEAR native scalar keys at frames1/31/61 with values0/1/0. Runtime pose-driven activation is not yet qualified.'})+'\n')
    object_names = [o.name for o in objects]
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False)
    reopened = {}
    for name in object_names:
        saved = bpy.data.objects[name]
        assert np.array_equal(base.xyz(saved.data.vertices), basis[name])
        assert base.named_weights(saved, bpy.data.objects['RiderSkeleton']) == fields[name]
        bpy.context.scene.frame_set(31); error = float(np.max(np.linalg.norm(base.evaluated_positions(saved)-arrays['rookie_31_'+name], axis=1)))
        assert error < 1e-8; reopened[name] = error
    report = {'accepted': False, 'status': 'UNACCEPTED_POSED_VOLUME_CONTACT_AND_MOVING_REVIEW_PENDING',
        'sourcePins': config['pins'], 'recipeSHA256': base.sha(__file__), 'inputSHA256': base.sha(HERE/'sculpt03.input.json'),
        'posePin': pose_pin, 'poseQualification': 'REJECTED_AUTHOR04_CONSTRUCTION_WITNESS', 'shapeKey': KEY,
        'shapeAnimation': {'interpolation': 'LINEAR', 'frames': [1, 31, 61], 'values': [0, 1, 0],
            'scope': 'Scalar shape interpolation is linear; original native skeletal action midpoint curves are not claimed identical to an endpoint-only glTF diagnostic.'},
        'native': {'path': str(blend.relative_to(base.ROOT)), 'sha256': base.sha(blend)}, 'movedVertices': moved,
        'basisWeightsRestUVMapsExact': True, 'bodyWholeIncidentVertices': whole,
        'cage': {'boundsBike': [list(lower), list(upper)], 'resolution': config['cageResolution'],
                 'originalControls': original_controls, 'targetControls': control_targets,
                 'handles': [{**h, 'center': list(h['center']), 'delta': list(h['delta'])} for h in handles]},
        'finiteBearingGuides': guides, 'inverseChecks': residuals, 'samples': samples, 'reopenedResidualM': reopened,
        'limits': ['Finite guide area is not measured garment support. Actual complete triangle/contact and played review remain required.',
                   'No old06 deltas, topology refinement, hidden faces, normal-player asset or runtime activation change.',
                   'Current author04 pose remains rejected. Native control/posture authoring and motion11 envelope review remain required.']}
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['status', 'native', 'movedVertices', 'inverseChecks', 'reopenedResidualM']}), flush=True)


if __name__ == '__main__': main()
