"""Parent CPU2 only. One selected native weight intervention, before sculpting.

blender -b -t 2 --python-exit-code 1 --python author.py -- FRESH_OUT
No old corrective import, shape edit, render, GLB export, or player asset write.
"""
import inspect
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from prepare import GLB, connected, graph, sha
from weight_brush import smooth_rows

C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def xyz(collection):
    result = np.empty((len(collection), 3), np.float32)
    collection.foreach_get('co', result.ravel()); return result


def named_weights(obj, rig):
    groups = {g.index: g.name for g in obj.vertex_groups if g.name in rig.data.bones}
    return [{groups[g.group]: float(g.weight) for g in v.groups if g.group in groups and g.weight > 0}
            for v in obj.data.vertices]


def assign_weights(obj, rows, selected, rig):
    indices = sorted(selected)
    for group in obj.vertex_groups:
        if group.name in rig.data.bones: group.remove(indices)
    for i in indices:
        for name, value in rows[i].items(): obj.vertex_groups[name].add([i], value, 'REPLACE')


def protected_signature():
    """Keep the existing full mesh/PBR/bind fingerprint, omit only vertex groups.

    Weight edits and nondeforming selection groups are declared separately.
    No protected positions, topology, UV, normal, material, image, or rest check
    is relaxed. The helper source pin prevents a broad accidental replacement.
    """
    path = ROOT/'assets/blender/rider-rebuild/selected-complete-engine01/export-private.py'
    assert sha(path) == 'b0720a3f492e2b05b1256f4034411d775d6920f3e1cd7c69ccebb5b9b8944cb5'
    helpers = runpy.run_path(str(path)); source = inspect.getsource(helpers['part_fingerprint'])
    start = source.index('    digest.update(json.dumps([g.name for g in obj.vertex_groups])')
    end = source.index('    materials = []', start)
    namespace = dict(helpers); exec(source[:start]+source[end:], namespace)
    return lambda obj: namespace['part_fingerprint'](obj, {'np': np}), helpers


def local_matrix(row):
    q = row['rotationXYZW']; matrix = Quaternion((q[3], q[0], q[1], q[2])).to_matrix().to_4x4()
    for column, value in enumerate(row['scale']):
        for r in range(3): matrix[r][column] *= value
    matrix.translation = Vector(row['translation']); return matrix


def pose_targets(receipt, rig):
    rows = {r['id']: r for r in receipt['boneLocalTRS']}
    assert set(rows) == set(rig.pose.bones.keys())
    worlds = {}
    def world(name):
        if name not in worlds:
            parent = rig.data.bones[name].parent
            worlds[name] = (world(parent.name) if parent else Matrix.Identity(4)) @ local_matrix(rows[name])
        return worlds[name]
    return {bone.name: C.inverted() @ world(bone.name) for bone in rig.data.bones}


def set_target_pose(rig, targets):
    # Parents before children, explicit depsgraph update: same saved native rig,
    # no edit-bone/rest alteration and no hidden persistent transform driver.
    ordered = sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))
    for bone in ordered:
        bone.matrix = targets[bone.name]; bpy.context.view_layer.update()
    residual = max(abs(b.matrix[r][c]-targets[b.name][r][c])
                   for b in rig.pose.bones for r in range(4) for c in range(4))
    assert residual < 2e-5, ('Native pose conversion', residual)
    return residual


def reset_pose(rig):
    rig.animation_data_clear()
    for bone in rig.pose.bones: bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def evaluated_positions(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = evaluated.to_mesh()
    try:
        assert len(mesh.vertices) == len(obj.data.vertices)
        return xyz(mesh.vertices)
    finally: evaluated.to_mesh_clear()


def witness(obj, selection, source, edges):
    posed = evaluated_positions(obj); lengths = []
    for a, b in edges:
        rest = float(np.linalg.norm(source[a]-source[b])); actual = float(np.linalg.norm(posed[a]-posed[b]))
        if rest > 1e-9: lengths.append(actual/rest)
    return {'edges': [{'ids': pair, 'restM': float(np.linalg.norm(source[pair[0]]-source[pair[1]])),
                      'posedM': float(np.linalg.norm(posed[pair[0]]-posed[pair[1]])),
                      'pointsBlender': posed[pair].tolist()} for pair in selection['witnessEdges']],
            'wholeTransitionEdgeRatio': {'edgeCount': len(lengths), 'minimum': min(lengths),
                 'median': float(np.median(lengths)), 'p95': float(np.percentile(lengths, 95)), 'maximum': max(lengths)}}


def add_selection(obj, name, ids, values=None):
    group = obj.vertex_groups.new(name='A09_'+name)
    if values is None: group.add(sorted(ids), 1., 'REPLACE')
    else:
        for i in sorted(ids): group.add([i], values[i], 'REPLACE')


def save_action(rig, targets, bike):
    reset_pose(rig); set_target_pose(rig, targets)
    channels = {bone.name: (bone.location.copy(), bone.rotation_quaternion.copy(), bone.scale.copy())
                for bone in rig.pose.bones}
    reset_pose(rig); rig.animation_data_create()
    action = bpy.data.actions.new('A09_'+bike+'_REJECTED_POSE_WEIGHT_DIAGNOSTIC')
    action.use_fake_user = True; rig.animation_data.action = action
    for frame, keyed in [(1, False), (31, True), (61, False)]:
        for bone in rig.pose.bones:
            if keyed: bone.location, bone.rotation_quaternion, bone.scale = channels[bone.name]
            else:
                bone.location = (0, 0, 0); bone.rotation_quaternion = (1, 0, 0, 0); bone.scale = (1, 1, 1)
            for prop in ('location', 'rotation_quaternion', 'scale'): bone.keyframe_insert(prop, frame=frame, group=bone.name)
    return action


def contact_guides(receipt, bike_to_blender, bike):
    collection = bpy.data.collections.new('A09_'+bike+'_SOURCE_CONTACT_TARGETS')
    bpy.context.scene.collection.children.link(collection); collection.hide_render = True
    collection.hide_viewport = bike != 'rookie'
    frames = receipt['frames']; rows = [(p['side']+'_palm', p['position'], p['rotationXYZW']) for p in frames['palms']]
    rows += [(side+'_sole', p, frames['soleRotationXYZW'][side]) for side, p in frames['soles'].items()]
    for name, p, q in rows:
        obj = bpy.data.objects.new('A09_'+bike+'_'+name+'_TARGET', None); collection.objects.link(obj)
        obj.empty_display_type = 'ARROWS'; obj.empty_display_size = .04; obj.show_in_front = True
        obj.matrix_world = bike_to_blender @ local_matrix({'translation': p, 'rotationXYZW': q, 'scale': [1, 1, 1]})


def main():
    arguments = sys.argv[sys.argv.index('--')+1:]; assert len(arguments) == 1
    out = Path(arguments[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09')
    manifest = json.loads((HERE/'selection.json').read_text()); pins = manifest['sourcePins']
    for row in pins.values(): assert sha(ROOT/row['path']) == row['sha256'], row['path']
    contract = json.loads((ROOT/pins['contract']['path']).read_text())
    diagnostic_path = ROOT/'harness/out/rider-rebuild/selected-seated-author05/diagnostic01.json'
    assert sha(diagnostic_path) == '34368447e4dadb04470ffe85a937715acf94093d56da004234bc1ea83e5587cd'
    diagnostic = json.loads(diagnostic_path.read_text())
    receipts = {}; receipt_pins = {}
    for row in diagnostic['bikes']:
        path = ROOT/row['receipt']['path']; assert sha(path) == row['receipt']['sha256']
        receipts[row['name']] = json.loads(path.read_text()); receipt_pins[row['name']] = row['receipt']
    assert set(receipts) == {'rookie', 'pro'}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/pins['native']['path']), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; jeans = bpy.data.objects['RiderJeans']; body = bpy.data.objects['RiderBody']
    assert rig.matrix_world.is_identity and not rig.animation_data and len(rig.data.bones) == 75
    assert all(not b.constraints and b.matrix_basis.is_identity for b in rig.pose.bones)
    for bone in rig.pose.bones: bone.rotation_mode = 'QUATERNION'
    fingerprint, helper = protected_signature(); assert helper['native_rest'](rig) == contract['nativeRest']['bones']
    objects = [bpy.data.objects[name] for name in contract['specification']['meshNames'].values()]
    objects.append(bpy.data.objects['RiderBody__FullAnatomyReference'])
    original_signatures = {o.name: fingerprint(o) for o in objects}
    original_weights = {o.name: named_weights(o, rig) for o in objects}
    source = xyz(jeans.data.vertices); selection = manifest['jeans']
    native_ids = jeans.data.attributes['_NATIVE_ID']
    assert [a.value for a in native_ids.data] == list(range(len(source)))
    adjacency = graph([list(e.vertices) for e in jeans.data.edges])
    influence = dict(selection['influence']); selected = set(influence)
    domain = set(selection['domain']); assert connected(adjacency, domain) == [len(domain)]
    edges = [tuple(e.vertices) for e in jeans.data.edges if set(e.vertices) & selected]
    targets = {bike: pose_targets(receipt, rig) for bike, receipt in receipts.items()}
    rotation = contract['driver']['assetToBikeQuaternionXYZW']
    placement = Quaternion((rotation[3], *rotation[:3])).to_matrix().to_4x4()
    to_bike = placement @ C
    before = {}
    for bike, target in targets.items():
        reset_pose(rig); pose_residual = set_target_pose(rig, target)
        before[bike] = witness(jeans, selection, source, edges)
        actual = evaluated_positions(jeans); expected = next(r for r in diagnostic['bikes'] if r['name'] == bike)
        readback = max((to_bike @ Vector(actual[v['nativeID']])-Vector(v['posedBike'])).length
                       for side in expected['sides'].values() for v in side['vertices'])
        assert readback < .00002, ('Saved-pose source readback differs from author05', bike, readback)
        before[bike].update(savedPoseMatrixResidual=pose_residual, author05MaximumCoreResidualM=readback)
    reset_pose(rig)
    full, final, removed = smooth_rows(original_weights[jeans.name], adjacency, influence,
        **selection['smooth'], cutoff=selection['finalCutoff'])
    assign_weights(jeans, final, selected, rig)
    actual_weights = named_weights(jeans, rig)
    assert all(actual_weights[i] == original_weights[jeans.name][i] for i in range(len(source)) if i not in selected)
    assert all(len(row) <= 4 and abs(sum(row.values())-1) < 2e-6 and min(row.values()) > .0001 for row in actual_weights)
    after = {}
    for bike, target in targets.items():
        reset_pose(rig); set_target_pose(rig, target); after[bike] = witness(jeans, selection, source, edges)
    reset_pose(rig)
    rest_error = float(np.max(np.linalg.norm(evaluated_positions(jeans)-source, axis=1)))
    assert rest_error < 2e-6, ('Weight edit changed evaluated rest', rest_error)
    for name, ids in selection['groups'].items():
        add_selection(jeans, name, ids, influence if name == 'transition' else None)
    bad = set(manifest['body']['crossingWitnessNativeIDs'])
    incident = [p for p in body.data.polygons if bad.intersection(p.vertices)]
    whole = {i for p in incident for i in p.vertices}
    context = set(manifest['body']['transitionContext']) | whole
    add_selection(body, 'whole_incident_waist_faces', whole); add_selection(body, 'coupled_body_transition', context)
    assert set(manifest['body']['incidentFaceVertices']) <= whole
    assert helper['native_rest'](rig) == contract['nativeRest']['bones']
    assert original_signatures == {o.name: fingerprint(o) for o in objects}
    assert all(named_weights(o, rig) == original_weights[o.name] for o in objects if o != jeans)
    for bike, receipt in receipts.items(): contact_guides(receipt, to_bike.inverted(), bike)
    actions = {bike: save_action(rig, target, bike) for bike, target in targets.items()}
    rig['A09_classification'] = 'UNACCEPTED_WEIGHT_ONLY; author04 key is rejected; seated volume sculpt remains required'
    rig['A09_contact_controls'] = 'Existing native75 pose bones; named source palm/sole target empties. No IK or contact acceptance added.'
    saved_samples = {}
    for bike, action in actions.items():
        rig.animation_data.action = action; saved_samples[bike] = {}
        for frame in [1, 16, 31, 46, 61]:
            bpy.context.scene.frame_set(frame); saved_samples[bike][frame] = witness(jeans, selection, source, edges)
        assert max(abs(a['posedM']-b['posedM']) for a, b in zip(saved_samples[bike][1]['edges'], saved_samples[bike][61]['edges'])) < 1e-8
        assert max(abs(a['posedM']-b['posedM']) for a, b in zip(saved_samples[bike][31]['edges'], after[bike]['edges'])) < 2e-6
    rig.animation_data.action = actions['rookie']; bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = 61
    out.mkdir(parents=True); blend = out/'selected-anatomical09-weight-only.blend'
    report = {'accepted': False, 'status': 'UNACCEPTED_NATIVE_WEIGHT_INTERVENTION_SCULPT_PENDING',
        'sourcePins': pins, 'selectionSHA256': sha(HERE/'selection.json'), 'recipeSHA256': sha(__file__),
        'weightBrushSHA256': sha(HERE/'weight_brush.py'), 'diagnosticPoses': receipt_pins,
        'before': before, 'after': after, 'evaluatedRestMaximumResidualM': rest_error,
        'outsideWeightsExact': True, 'protectedSignatures': original_signatures, 'native75RestExact': True,
        'editedJeansVertices': len(selected), 'maximumFourRemovedMass': max(removed.values()),
        'bodyIncidentPolygonIDs': [p.index for p in incident], 'bodyWholeIncidentVertices': sorted(whole),
        'savedActionSamples': saved_samples,
        'witnessWeights': [{'id': i, 'before': original_weights[jeans.name][i], 'fullAuthored': full[i],
                           'savedFour': actual_weights[i], 'removedMass': removed[i]}
                          for i in sorted({i for pair in selection['witnessEdges'] for i in pair})],
        'limits': manifest['limitations']+['Contact guides are source target frames, not an IK solution.',
            'No mesh positions/topology/body weights were edited. Coupled body sculpt is explicitly pending.']}
    (out/'authored-weight-rows.json').write_text(json.dumps([{'nativeID': i, 'before': original_weights[jeans.name][i],
        'fullAuthored': full[i], 'finalFour': actual_weights[i], 'removedMass': removed[i]} for i in sorted(selected)])+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; jeans = bpy.data.objects['RiderJeans']
    assert helper['native_rest'](rig) == contract['nativeRest']['bones']
    assert named_weights(jeans, rig) == actual_weights
    assert original_signatures == {name: fingerprint(bpy.data.objects[name]) for name in original_signatures}
    reopen = {}
    for bike in actions:
        rig.animation_data.action = bpy.data.actions['A09_'+bike+'_REJECTED_POSE_WEIGHT_DIAGNOSTIC']
        for frame in [1, 31, 61]:
            bpy.context.scene.frame_set(frame); current = witness(jeans, selection, source, edges)
            error = max(abs(a['posedM']-b['posedM']) for a, b in zip(current['edges'], saved_samples[bike][frame]['edges']))
            assert error < 1e-8; reopen[f'{bike}:{frame}'] = error
    for row in pins.values(): assert sha(ROOT/row['path']) == row['sha256']
    report['reopenedWitnessResidualM'] = reopen
    report['native'] = {'path': str(blend.relative_to(ROOT)), 'sha256': sha(blend)}
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'native': report['native'],
                      'before': before, 'after': after, 'reopenedWitnessResidualM': reopen}), flush=True)


if __name__ == '__main__': main()
