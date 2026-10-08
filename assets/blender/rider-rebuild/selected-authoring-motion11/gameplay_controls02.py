"""Reconstruct editable native controls from the actual held-input gameplay film.

Parent CPU2 only: blender -b -t 2 --python-exit-code 1 --python THIS --
CONVERTED_RECEIPT.json FRESH_OUT. Never writes the selected appearance master.
"""
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from build import sha, load_rig, action_curves, keyed_action, operator_bound
from controls import install, ctrl, rest_rows

LIMIT = .0001
PAIRS = [('DEF-pelvis.L', 'DEF-spine'), ('DEF-pelvis.R', 'DEF-spine'),
         ('DEF-thigh.L.001', 'DEF-thigh.L'), ('DEF-thigh.R.001', 'DEF-thigh.R')]


def pin(path):
    return {'path': str(path.resolve().relative_to(ROOT)), 'sha256': sha(path)}


def pinned(row):
    path = (ROOT/row['path']).resolve()
    assert path.is_relative_to(ROOT) and sha(path) == row['sha256'], row
    return path


def rows(matrix):
    return [list(row) for row in matrix]


def reconstruct(rig, context, wanted):
    """Use the actual runtime prepose; do not ask legacy IK to find it anew.

    Its official solver ignores tolerance and stops at angle norm1e-3 after10
    iterations. Starting at the exact analytic gameplay solution removes that
    convergence error without changing the solver or the .1mm acceptance gate.
    Hidden mechanism prepose keys remain behind live palm/sole/pole IK controls.
    """
    limbs = context['limbs']
    iks = [next(c for c in rig.pose.bones[l['mechanismLower']].constraints if c.type == 'IK') for l in limbs]
    for constraint in iks:
        constraint.mute = True
    for name in context['controls']:
        rig.pose.bones[name].matrix_basis = Matrix.Identity(4)
    for name in context['fk']:
        rig.pose.bones[ctrl(name)].matrix = wanted[name]
        bpy.context.view_layer.update()
    seeds = []
    for limb in limbs:
        # Added EditBone frames are orthonormalized by Blender. Use their ACTUAL
        # rest relation instead of assuming CTRL-sole rest equals source socket.
        control_rest = rig.data.bones[limb['targetControl']].matrix_local
        target_rest = rig.data.bones[limb['target']].matrix_local
        desired_end = wanted[limb['end']]
        rig.pose.bones[limb['targetControl']].matrix = desired_end @ target_rest.inverted() @ control_rest
        upper = wanted[limb['uppers'][0]]
        lower = wanted[limb['lowers'][0]]
        start, middle, end = upper.translation, lower.translation, desired_end.translation
        a, b = limb['lengths']
        assert max(abs((middle-start).length-a), abs((end-middle).length-b)) < LIMIT, ('Captured limb changes length', limb['kind'], limb['side'])
        assert abs(a-b)+1e-7 < (end-start).length < a+b, ('Captured limb unreachable', limb['kind'], limb['side'])
        # This is the exact up direction read by Blender ConstrainPoleVector:
        # upper.x*cos(poleAngle)+upper.z*sin(poleAngle). The captured analytic
        # solution therefore enters the solver with zero pole-frame rotation.
        angle = limb['poleAngle']
        up = upper.to_3x3().col[0]*math.cos(angle)+upper.to_3x3().col[2]*math.sin(angle)
        ray = (end-start).normalized()
        assert (up-ray*up.dot(ray)).length > 1e-5
        rig.pose.bones[limb['poleControl']].matrix = Matrix.Translation(start+up.normalized()*.45)
        for mechanism, desired in [(limb['mechanismUpper'], upper), (limb['mechanismLower'], lower)]:
            rig.pose.bones[mechanism].matrix = desired
            bpy.context.view_layer.update()
        seeds.append({'limb': limb['kind']+limb['side'], 'desiredUpper': rows(upper), 'desiredLower': rows(lower),
                      'desiredEnd': rows(desired_end), 'actualControlTarget': rows(rig.pose.bones[limb['target']].matrix),
                      'outerReachMarginM': a+b-(end-start).length, 'poleAngle': angle})
    for side in ('L', 'R'):
        for digit in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            rig.pose.bones['CTRL-palm.'+side][digit] = 1.
    for constraint in iks:
        constraint.mute = False
    bpy.context.view_layer.update()
    all_bones = []
    for name in context['names']:
        actual = rig.pose.bones[name].matrix.copy()
        all_bones.append({'name': name, 'affineBoundWithin2mM': operator_bound(actual, wanted[name]),
                          'positionResidualM': (actual.translation-wanted[name].translation).length})
    contacts = []
    for limb in limbs:
        actual = rig.pose.bones[limb['socket']].matrix.copy()
        desired = wanted[limb['socket']]
        contacts.append({'socket': limb['socket'], 'actual': rows(actual), 'captured': rows(desired),
                         'affineBoundWithin2mM': operator_bound(actual, desired),
                         'positionResidualM': (actual.translation-desired.translation).length})
    maximum = max(row['affineBoundWithin2mM'] for row in all_bones)
    witness = {'maximumCapturedPoseAffineBoundWithin2mM': maximum, 'bones': all_bones, 'contacts': contacts, 'mechanismSeeds': seeds}
    context['failureWitness'] = witness
    assert maximum < LIMIT, ('Native live controls differ from actual gameplay', sorted(all_bones, key=lambda r: r['affineBoundWithin2mM'], reverse=True)[:5])
    assert max(r['affineBoundWithin2mM'] for r in contacts) < LIMIT, contacts
    return witness


def key_controls(rig, context, frame, previous):
    names = context['controls'] + [l[k] for l in context['limbs'] for k in ('mechanismUpper', 'mechanismLower')]
    for name in names:
        bone = rig.pose.bones[name]
        if name in previous and bone.rotation_quaternion.dot(previous[name]) < 0:
            bone.rotation_quaternion.negate()
        previous[name] = bone.rotation_quaternion.copy()
        for prop in ('location', 'rotation_quaternion', 'scale'):
            bone.keyframe_insert(prop, frame=frame, group=name)
        if name.startswith('CTRL-palm.'):
            for digit in ('thumb', 'index', 'middle', 'ring', 'pinky'):
                bone.keyframe_insert(f'["{digit}"]', frame=frame, group=name)


def main():
    receipt_path, out = map(lambda p: Path(p).resolve(), sys.argv[sys.argv.index('--')+1:])
    measured = json.loads(receipt_path.read_text())
    assert measured['status'] == 'MEASURED_GAMEPLAY_NATIVE_POSES_UNACCEPTED' and measured['accepted'] is False
    pinned(measured['input']); pinned(measured['recipe'])
    document = json.loads(pinned(measured['nativePoseJSON']).read_text())
    assert document['source'] == measured['source'] and document['boneNames'] == measured['boneNames']
    config = measured['source']; native = pinned(config['selectedNative'])
    for row in config['recipes'].values():
        pinned(row)
    assert pinned(config['recipes']['gameplayControls']) == Path(__file__).resolve()
    contract = json.loads(pinned(config['selectedContract']).read_text())
    for p in config['reports'].values():
        pinned(p)
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rig = load_rig(native); context = install(rig, contract); names = context['names']
    assert names == document['boneNames'] and document['nativeRest'] == contract['nativeRest']
    scene = bpy.context.scene; scene.render.fps = 24; scene.render.fps_base = 1
    out.mkdir(parents=True); rig.animation_data_create()
    arrays = {'boneNames': np.asarray(names)}; records = []; authored = []; baked = []
    for index, record in enumerate(document['actions']):
        assert record['fps'] == 24 and record['frameRange'] == [1, 241] and record['shapeActivation'] == 0
        action = bpy.data.actions.new('Author.'+record['name']); action.use_fake_user = True
        rig.animation_data.action = action; previous = {}; previous_local = {}; poses = []; locals_ = []; witnesses = []
        try:
            for frame, sample in enumerate(record['nativeWorldMatrices'], 1):
                scene.frame_set(frame)
                wanted = {name: Matrix(value) for name, value in zip(names, sample)}
                witness = reconstruct(rig, context, wanted)
                key_controls(rig, context, frame, previous); bpy.context.view_layer.update()
                worlds = {n: rig.pose.bones[n].matrix.copy() for n in names}; local = []
                regional = max(operator_bound(worlds[a]@context['rest'][a].inverted(), worlds[b]@context['rest'][b].inverted()) for a, b in PAIRS)
                assert regional < LIMIT, ('Regional support semantics changed', frame, regional)
                for n in names:
                    bone = rig.data.bones[n]
                    options = {'parent_matrix': worlds[bone.parent.name], 'parent_matrix_local': bone.parent.matrix_local} if bone.parent else {}
                    basis = bone.convert_local_to_pose(worlds[n], bone.matrix_local, invert=True, **options)
                    p, q, s = basis.decompose()
                    if n in previous_local and q.dot(previous_local[n]) < 0:
                        q.negate()
                    previous_local[n] = q.copy(); local.append([*p, *q, *s])
                poses.append([np.asarray(worlds[n]) for n in names]); locals_.append(local)
                witnesses.append({'frame': frame, 'sourceTick': record['sourceTicks'][frame-1],
                    'capturedPoseBoundM': witness['maximumCapturedPoseAffineBoundWithin2mM'], 'regionalOperatorBoundM': regional})
                if frame == 1:
                    initial = out/(record['bike']+'-first-physical-controls.blend')
                    bpy.ops.wm.save_as_mainfile(filepath=str(initial), compress=True)
                    (out/(record['bike']+'-first-physical-pose.json')).write_text(json.dumps({'accepted': False,
                        'status': 'FIRST_MEASURED_PHYSICAL_CONTROLS_UNACCEPTED', 'sourceReceipt': pin(receipt_path),
                        'native': pin(initial), 'physics': record['physicsWitnesses'][0], 'witness': witness,
                        'nativeBoneWorldMatrices': {n: rows(worlds[n]) for n in names}}, indent=2)+'\n')
        except Exception as error:
            (out/'failed-action.json').write_text(json.dumps({'accepted': False, 'action': record['name'], 'frame': frame,
                'sourceTick': record['sourceTicks'][frame-1], 'error': repr(error), 'poseWitness': context.get('failureWitness'),
                'completedActions': [r['name'] for r in records]}, indent=2)+'\n')
            raise
        for curve in action_curves(action):
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        arrays[f'pose{index}'] = np.asarray(poses); arrays[f'local{index}'] = np.asarray(locals_)
        baked.append(keyed_action(record['name'], names, arrays[f'local{index}']).name); authored.append(action.name)
        result = {k: v for k, v in record.items() if k != 'nativeWorldMatrices'}
        result.update(controlAction=action.name, nativeWitnesses=witnesses)
        scene.frame_set(1); scene.frame_start = 1; scene.frame_end = 241
        control_file = out/(record['bike']+'-editable-gameplay-controls.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(control_file), compress=True); result['controlNative'] = pin(control_file)
        records.append(result)
        np.savez_compressed(out/'gameplay-action-matrices.npz', **arrays)
        (out/'partial-receipt.json').write_text(json.dumps({'accepted': False, 'status': 'MEASURED_GAMEPLAY_CONTROLS_BAKE_PENDING',
            'sourceReceipt': pin(receipt_path), 'actions': records}, indent=2)+'\n')
        # Read the saved control file, including hidden MCH prepose keys and
        # live IK. Construction-time evaluated matrices alone cannot prove the
        # editable action works after reload. This stays inside the same job.
        bpy.ops.wm.open_mainfile(filepath=str(control_file), use_scripts=False)
        rig = bpy.data.objects['RiderSkeleton']; scene = bpy.context.scene
        assert rest_rows(rig, set(names)) == contract['nativeRest']['bones']
        worst = 0.
        for frame in range(1, 242):
            scene.frame_set(frame); bpy.context.view_layer.update()
            worst = max(worst, *(operator_bound(rig.pose.bones[n].matrix, arrays[f'pose{index}'][frame-1, j]) for j, n in enumerate(names)))
        result['savedControlReplayMaximumAffineBoundWithin2mM'] = worst
        (out/(record['bike']+'-control-readback.json')).write_text(json.dumps({'accepted': False,
            'native': result['controlNative'], 'frames': 241, 'maximumAffineBoundWithin2mM': worst}, indent=2)+'\n')
        assert worst < LIMIT, ('Reopened live control action differs', record['name'], worst)
    assert rest_rows(rig, set(names)) == contract['nativeRest']['bones']
    data = rig.data; bpy.data.objects.remove(rig, do_unlink=True)
    if data.users == 0:
        bpy.data.armatures.remove(data)
    for name in authored:
        bpy.data.actions.remove(bpy.data.actions[name])
    rig = load_rig(native); assert rest_rows(rig) == contract['nativeRest']['bones']; rig.animation_data_create()
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    for index, (record, name) in enumerate(zip(records, baked)):
        action = bpy.data.actions[name]
        rig.animation_data.action = action; rig.animation_data.action_slot = action.slots[0]; worst = 0.
        for frame in range(1, 242):
            scene.frame_set(frame); bpy.context.view_layer.update()
            worst = max(worst, *(operator_bound(rig.pose.bones[n].matrix, arrays[f'pose{index}'][frame-1, j]) for j, n in enumerate(names)))
        assert worst < LIMIT, ('Fresh native bake differs', record['name'], worst)
        record['bakeMaximumAffineBoundWithin2mM'] = worst
    scene.frame_set(1); baked_file = out/'gameplay75-baked-actions.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(baked_file), compress=True)
    result = {'accepted': False, 'status': 'NATIVE_MEASURED_GAMEPLAY_ACTIONS_UNACCEPTED', 'sourceReceipt': pin(receipt_path),
        'recipe': pin(Path(__file__)), 'controlsRecipe': pin(HERE/'controls.py'), 'commonBuildRecipe': pin(HERE/'build.py'),
        'nativeRestExactlyPreserved': True, 'shapeActivation': 0, 'bakedNative': pin(baked_file),
        'nativeMatrices': pin(out/'gameplay-action-matrices.npz'), 'actions': records,
        'limits': ['Actual simulation replay and live control reconstruction; no new gameplay driver or time-clip substitution.',
                   'Captured keys are24Hz; native between-key physics states were not captured or inferred.',
                   'Complete selected dressed/full-reference contact and moving appearance remain independent unaccepted gates.']}
    (out/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'actions': [r['name'] for r in records]}), flush=True)


if __name__ == '__main__':
    main()
