"""Original-selected native apply and independent reopen. Never exports assets."""
import hashlib
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = runpy.run_path(str(HERE/'worker.py'))
ROOT, OUT, pin, checked, read, write = (W[k] for k in ('ROOT', 'OUT', 'pin', 'checked', 'read', 'write'))
H = runpy.run_path(str(HERE.parent/'selected-anatomical-hoodie-fit65/component.py'))
C = H['c47']


def geometry_arrays(obj, np):
    assert obj.matrix_world.is_identity
    points = np.empty((len(obj.data.vertices), 3), np.float32); obj.data.vertices.foreach_get('co', points.ravel())
    obj.data.calc_loop_triangles(); faces = np.empty((len(obj.data.loop_triangles), 3), np.int32)
    obj.data.loop_triangles.foreach_get('vertices', faces.ravel())
    return points, faces


def witness(rig, hoodie, config, bpy, np):
    prior = read(config['pins']['priorInputs']); author, geometry = C['helpers'](prior)
    _, faces = geometry_arrays(hoodie, np)
    return {'rest': C['canonical'](author['rest'](rig)),
        'sourceInvariant': H['invariant'](hoodie, faces, author, np),
        'hoodieGeometry': geometry(hoodie),
        'protectedGeometry': {name: geometry(bpy.data.objects[name]) for name in sorted(C['PROTECTED'])},
        'cornerNormals': hashlib.sha256(H['corner_normals'](hoodie, np).tobytes()).hexdigest()}


def open_original(job, bpy, np):
    config = read(job['input65']); H['source_gate'](config)
    assert job['native47'] == config['pins']['gloveNative']
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(job['native47'])), use_scripts=False) == {'FINISHED'}
    rig = C['scoped'](bpy); hoodie = bpy.data.objects['RiderHoodie']; body = bpy.data.objects['RiderBody__FullAnatomyReference']
    assert len(rig.data.bones) == 75 and not hoodie.data.shape_keys
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    return rig, hoodie, body, config, witness(rig, hoodie, config, bpy, np)


def apply(input_path, solve_path, output):
    import bpy
    import numpy as np
    job = W['load_job'](input_path); out = Path(output).resolve()
    assert out.is_relative_to(OUT) and not out.exists(); out.mkdir(parents=True)
    solve_path = Path(solve_path).resolve(); solved = json.loads(solve_path.read_text())
    assert solved['input'] == pin(input_path) and solved['acceptedArt'] is False
    prepared = read(solved['prepared']); assert prepared['input'] == pin(input_path)
    rig, hoodie, body, config, before = open_original(job, bpy, np)
    assert before == prepared['sourceWitness']
    original, faces = geometry_arrays(hoodie, np)
    moved = np.load(checked(solved['positions']), mmap_mode='r')
    assert moved.shape == original.shape and np.isfinite(moved).all()
    mesh = hoodie.data; loops = np.empty((len(mesh.loop_triangles), 3), np.int32)
    mesh.loop_triangles.foreach_get('loops', loops.ravel())
    assert len(np.unique(loops)) == len(mesh.loops)
    normals = H['corner_normals'](hoodie, np)
    transformed, unsupported = runpy.run_path(str(HERE/'dense.py'))['tangent_normals'](
        original.astype(float), moved, faces, normals[loops].astype(float))
    normals[loops] = transformed.astype(np.float32)
    mesh.vertices.foreach_set('co', moved.astype(np.float32).ravel()); mesh.update()
    mesh.normals_split_custom_set(normals.tolist()); mesh.update()
    # Save the actual candidate even if construction contact failed. The status
    # and authoritative admission below fail closed; no private/game export.
    native = C['save_native'](out, 'UNACCEPTED-selected-anatomical-hoodie-fit73.blend', bpy)
    expected = witness(rig, hoodie, config, bpy, np)
    for key in ('rest', 'sourceInvariant', 'protectedGeometry'): assert expected[key] == before[key]
    write(out/'expected-witness.json', expected)
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_DENSE73_SAVED_CONTACT_REOPEN_PENDING',
        'input': pin(input_path), 'solve': pin(solve_path), 'native': native,
        'expectedWitness': pin(out/'expected-witness.json'), 'qualificationInputs': job['retained72'],
        'sourceVertexCount': len(original), 'sourceTriangleCount': len(faces),
        'linearizedObjectiveConverged': solved['linearizedObjectiveConverged'],
        'sourceRestProtectedInvariantPassed': True, 'normalTransport': 'ACTUAL_PER_TRIANGLE_INVERSE_TRANSPOSE',
        'normalTransportUnsupportedSourceOrDestinationFaces': unsupported,
        'anatomicalRegistration': {'contactTargetM': config['field']['clothClearanceM']+config['field']['contactSolveMarginM'],
            'constructionContactSamplesPassed': False, 'continuousMapInjectivityClaimed': False},
        'nativeStorage': {'reopenVerified': False}, 'geometryGatesPassed': False, 'movingReviewPassed': False}
    write(out/'component-pending.json', report)
    print(json.dumps({'native': native, 'pending': pin(out/'component-pending.json')}), flush=True)


def qualify(pending_path):
    import bpy
    import numpy as np
    path = Path(pending_path).resolve(); report = json.loads(path.read_text())
    assert path.is_relative_to(OUT) and report['status'] == 'UNACCEPTED_DENSE73_SAVED_CONTACT_REOPEN_PENDING'
    job = W['load_job'](checked(report['input'])); config = read(job['input65'])
    H['source_gate'](config); expected = read(report['expectedWitness'])
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(report['native'])), use_scripts=False) == {'FINISHED'}
    rig = C['scoped'](bpy); hoodie = bpy.data.objects['RiderHoodie']
    assert witness(rig, hoodie, config, bpy, np) == expected
    _, faces = geometry_arrays(hoodie, np)
    # Same exact existing full retained-domain contact and tangent qualifier65.
    runpy.run_path(str(checked(config['pins']['qualification65'])))['measure'](
        report, config, hoodie, bpy.data.objects['RiderBody__FullAnatomyReference'], faces, path.parent)
    passed = report['anatomicalRegistration']['constructionContactSamplesPassed']
    status = 'UNACCEPTED_DENSE73_REOPENED_CONTACT_FAILED' if not passed else (
        'UNACCEPTED_DENSE73_REOPENED_CONTACT_PASSED_OBJECTIVE_UNCONVERGED' if not report['linearizedObjectiveConverged'] else
        'UNACCEPTED_DENSE73_REOPENED_CONTACT_PASSED_MOTION_PENDING')
    report.update(status=status,
        pendingReceipt=pin(path), sourceInvariantExact=True, topologyAndSourceVertexOrderUnchanged=True,
        exact75RestUnchanged=True, fullReferenceUnchanged=True, protectedValidationPassed=True)
    report['nativeStorage']['reopenVerified'] = True
    write(path.parent/'component-reopened.json', report)
    print(json.dumps({'reopened': pin(path.parent/'component-reopened.json'), 'status': report['status']}), flush=True)


def admit(path):
    report = json.loads(Path(path).read_text())
    assert report['status'] == 'UNACCEPTED_DENSE73_REOPENED_CONTACT_PASSED_MOTION_PENDING'
    job = W['load_job'](checked(report['input']))
    for key in ('native', 'solve', 'pendingReceipt', 'actualTangentAndPair', 'expectedWitness', 'qualificationInputs'): checked(report[key])
    assert report['nativeStorage']['reopenVerified'] and report['protectedValidationPassed']
    assert report['linearizedObjectiveConverged'] and read(report['solve'])['linearizedObjectiveConverged']
    r = report['anatomicalRegistration']
    assert r['constructionContactSamplesPassed'] and r['deficientRetainedConstraintCount'] == 0
    assert r['healthyRetainedBoundaryPassed'] and r['newZeroAreaFromNondegenerateSource'] == 0
    assert all(report[k] for k in ('sourceInvariantExact', 'topologyAndSourceVertexOrderUnchanged', 'exact75RestUnchanged', 'fullReferenceUnchanged'))
    assert report['acceptedArt'] is False and report['geometryGatesPassed'] is False
    return report


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'apply': apply(*args[1:])
    elif args[0] == 'qualify': qualify(*args[1:])
    elif args[0] == 'admit': admit(*args[1:])
    else: raise AssertionError(args)
