"""Author one deep fixed-sole crouch/rise on a pinned complete native75.

Parent CPU2 lease only. No garment, topology, fields, rest or binding edits.
blender -b -t 2 --python-exit-code 1 --python author.py -- CONFIG FRESH_OUT
"""
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[4]
ACTION = 'UnacceptedSelectedDeepFixedSoleCrouchRise217'
EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}
# Artistic timing only: half-second neutral, three-second descent, two-second
# deep hold, three-second rise, half-second neutral. Geometry sets the depth.
STATIONS = ((1, 0.), (13, 0.), (85, 1.), (133, 1.), (205, 0.), (217, 0.))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed input', row)
    return path


def phase(frame):
    for first, last in zip(STATIONS, STATIONS[1:]):
        if frame <= last[0]:
            t = (frame-first[0])/(last[0]-first[0])
            t = t*t*(3-2*t)
            return first[1]*(1-t)+last[1]*t
    return 0.


def angle(a, b):
    return math.degrees(a.normalized().angle(b.normalized()))


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    config_path, out = (Path(p).resolve() for p in args)
    config = json.loads(config_path.read_text())
    assert config['accepted'] is False and config['ready'] is True
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-deep-crouch03')
    native, contract_path, receipt_path = [pin(config[k]) for k in ('native', 'baseContract', 'sourceReceipt')]
    contract, receipt = json.loads(contract_path.read_text()), json.loads(receipt_path.read_text())
    assert receipt['native'] == config['native'] and receipt['accepted'] is False
    assert set(receipt['objects']) == EXPECTED and receipt['rigAndContractExactNative75'] is True
    assert contract['nativeRest']['frame'] == 'X-left,-Y-forward,Z-up'
    helper_path = pin(config['geometryHelper'])
    visibility_path = pin(config['visibilityHelper'])
    helper = runpy.run_path(str(helper_path))
    geometry, rest_rows = helper['geometry'], helper['rest']
    bpy.ops.wm.open_mainfile(filepath=str(native))
    scene, rig = bpy.context.scene, bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.matrix_world.is_identity and rig.animation_data is None
    assert not rig.constraints and all(not b.constraints and b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    assert all(layer.material_override is None for layer in scene.view_layers)
    native_rows = [{'name': b.name, 'parent': b.parent.name if b.parent else None,
        'head': list(b.head_local), 'tail': list(b.tail_local), 'matrix': [list(r) for r in b.matrix_local],
        'useConnect': b.use_connect, 'useDeform': b.use_deform} for b in rig.data.bones]
    assert native_rows == contract['nativeRest']['bones'], 'Exact target native75 rest required'
    roles = contract['specification']['roles']
    group = lambda v: v if isinstance(v, list) else [v]
    one = lambda v: group(v)[0]
    pelvis = one(roles['pelvis'])
    assert rig.data.bones[pelvis].parent is None
    neck = group(roles['neck'])
    rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    heads = {b.name: b.head_local.copy() for b in rig.data.bones}
    meshes = [bpy.data.objects[n] for n in sorted(EXPECTED)]
    anatomy = bpy.data.objects['RiderBody__FullAnatomyReference']
    assert anatomy.hide_render and all(o.matrix_world.is_identity for o in meshes)
    fingerprints = {o.name: geometry(o) for o in meshes+[anatomy]}
    rest_before = rest_rows(rig)
    object_state = [(o.name, o.hide_render, [list(r) for r in o.matrix_world]) for o in scene.objects]
    up = Vector((0, 0, 1))
    across = heads[one(roles['thighLeft'])]-heads[one(roles['thighRight'])]
    across -= up*across.dot(up); across.normalize()
    forward = sum((heads[one(roles['toe'+s])]-heads[one(roles['foot'+s])]
                   for s in ('Left', 'Right')), Vector((0, 0, 0)))
    forward -= up*forward.dot(up); forward.normalize()
    assert forward.y < -.9 and across.x > .9
    limbs, supports, deep_knees, own_lengths = {}, {}, {}, {}
    for side, suffix, sign in [('left', 'Left', 1), ('right', 'Right', -1)]:
        for kind, upper_role, lower_role, end_role in [('leg', 'thigh', 'shin', 'foot'), ('arm', 'upperArm', 'forearm', 'wrist')]:
            uppers, lowers = group(roles[upper_role+suffix]), group(roles[lower_role+suffix])
            end = one(roles[end_role+suffix])
            a, b = (heads[lowers[0]]-heads[uppers[0]]).length, (heads[end]-heads[lowers[0]]).length
            limbs[kind+suffix] = (uppers, lowers, end, a, b)
        foot, toe = [one(roles[k+suffix]) for k in ('foot', 'toe')]
        boot = bpy.data.objects['ActualSelectedBoot.'+('L' if sign == 1 else 'R')]
        foot_forward = heads[toe]-heads[foot]
        foot_forward -= up*foot_forward.dot(up); foot_forward.normalize()
        lateral = foot_forward.cross(up)
        groups = {g.index: g.name for g in boot.vertex_groups}
        ids = [v.index for v in boot.data.vertices if v.groups
               and all(groups[g.group] in {foot, toe} for g in v.groups if g.weight > 0)]
        assert ids, ('No actual foot/toe-only boot support vertices', side)
        points = np.asarray([boot.data.vertices[i].co[:] for i in ids])
        ids = np.asarray(ids); low = points[:, 2] <= points[:, 2].min()+.003
        ids, points = ids[low], points[low]
        long, wide = points@np.asarray(foot_forward), points@np.asarray(lateral)
        front = long >= long.min()+.6*(long.max()-long.min())
        assert front.any(); front_ids = np.flatnonzero(front)
        chosen = [int(ids[np.argmin(long)]), int(ids[front_ids[np.argmin(wide[front])]]),
                  int(ids[front_ids[np.argmax(wide[front])]])]
        reference = [boot.data.vertices[i].co.copy() for i in chosen]
        assert len(set(chosen)) == 3 and (reference[1]-reference[0]).cross(reference[2]-reference[0]).length*.5 > 1e-5
        sole = contract['driver']['soleSocketNames'][side]
        assert rig.data.bones[sole].parent.name == foot
        weights = [[(groups[g.group], g.weight) for g in boot.data.vertices[i].groups if g.weight > 0] for i in chosen]
        assert all(abs(sum(w for _, w in row)-1) < 2e-5 for row in weights)
        supports[side] = {'boot': boot, 'ids': chosen, 'reference': reference, 'weights': weights,
            'foot': foot, 'toe': toe, 'sole': sole, 'forward': foot_forward,
            'restSole': rig.pose.bones[sole].matrix.copy()}
        leg = limbs['leg'+suffix]
        # Knee over the actual two forefoot support bearings, with lateral
        # position between the same-side hip and ankle. Its height follows
        # that side's shin length; no angle is supplied to the leg solver.
        bearing = (reference[1]+reference[2])*.5
        ankle, hip = heads[foot], heads[leg[0][0]]
        planar = forward*(bearing-ankle).dot(forward)+across*((hip-ankle).dot(across)*.5)
        vertical2 = leg[4]**2-planar.length_squared
        assert vertical2 > 0, ('Actual boot bearing beyond own shin reach', side, leg[4], planar.length)
        deep_knees[side] = ankle+planar+up*math.sqrt(vertical2)
        own_lengths[side] = {'femurM': leg[3], 'shinM': leg[4], 'forefootBearing': list(bearing),
                            'derivedKnee': list(deep_knees[side])}
    rest_hip_center = (heads[one(roles['thighLeft'])]+heads[one(roles['thighRight'])])*.5
    depth_fraction = config['authoring']['hipBelowKneeFemurFraction']
    assert 0 < depth_fraction < .5
    hip_height = min(p.z for p in deep_knees.values())-depth_fraction*min(v['femurM'] for v in own_lengths.values())
    back_candidates = []
    for side, suffix in [('left', 'Left'), ('right', 'Right')]:
        leg, knee = limbs['leg'+suffix], deep_knees[side]
        hip_offset = heads[leg[0][0]]-rest_hip_center
        dx = (heads[leg[0][0]]-knee).dot(across)
        dz = hip_height+hip_offset.z-knee.z
        reach2 = leg[3]**2-dx*dx-dz*dz
        assert reach2 > 0, ('Requested knee-level hip position exceeds own femur', side, dx, dz)
        back_candidates.append(knee.dot(forward)-math.sqrt(reach2)-hip_offset.dot(forward))
    deep_hip_center = across*rest_hip_center.dot(across)+forward*min(back_candidates)+up*hip_height
    support_center = sum((p for support in supports.values() for p in support['reference']), Vector((0, 0, 0)))/6
    torso = heads[neck[0]]-rest_hip_center
    radius = math.hypot(torso.dot(forward), torso.dot(up))
    required_forward = (support_center-deep_hip_center).dot(forward)
    assert abs(required_forward) < radius, 'Native torso cannot place neck landmark above finite support center'
    deep_pitch = math.asin(required_forward/radius)-math.atan2(torso.dot(forward), torso.dot(up))
    assert 0 < deep_pitch < math.pi/2, ('Invalid geometry-derived torso direction', deep_pitch)
    drop = rest_hip_center.z-deep_hip_center.z
    assert drop > .24, ('Deep target is not distinct from prior 12cm action', drop)
    targets = {'ownSideLegs': own_lengths, 'restHipCenter': list(rest_hip_center),
        'deepHipCenter': list(deep_hip_center), 'hipDropM': drop,
        'hipBelowKneeFemurFraction': depth_fraction, 'supportLandmarkCenter': list(support_center),
        'depthMeaning': 'Hip-below-knee fraction is an authored depth choice, not a derived anatomical limit',
        'derivedTorsoPitchDegrees': math.degrees(deep_pitch),
        'torsoProjectionMeaning': 'Neck-base landmark over finite sole bearing centroid; not tissue COM or comfort qualification'}
    maximum = {'segmentLengthM': 0., 'ankleTargetM': 0., 'wristTargetM': 0., 'soleFrameM': 0., 'soleFrameRadians': 0.,
               'directNativeSolePointM': 0., 'evaluatedSolePointM': 0.}
    peaks = {side: {'kneeFlexionDegrees': 0., 'hipSwingFromRestDegrees': 0., 'ankleSwingFromRestDegrees': 0.}
             for side in ('left', 'right')}
    for values in peaks.values():
        values.update(hipSagittalFlexionDegrees=0., ankleDorsiflexionFromVerticalDegrees=0.)
    spine_peaks = {name: 0. for name in group(roles['trunk'])+neck}
    spine_world_peak = 0.

    def world_rotation(name, quaternion):
        bone = rig.pose.bones[name]
        matrix = quaternion.to_matrix().to_4x4(); matrix.translation = bone.matrix.translation
        bone.matrix = matrix; bone.scale = (1, 1, 1); bpy.context.view_layer.update()

    def aim(names, end, direction):
        swing = (heads[end]-heads[names[0]]).normalized().rotation_difference(direction.normalized())
        for name in names:
            world_rotation(name, swing@rest[name].to_quaternion())

    def solve(limb, target, pole):
        uppers, lowers, end, a, b = limb
        start = rig.pose.bones[uppers[0]].matrix.translation.copy()
        ray = target-start; distance = ray.length
        assert abs(a-b)+1e-7 < distance < a+b-1e-7, ('Unreachable native endpoint; no stretch/fallback', end, distance, a, b)
        ray.normalize(); pole = pole-start; pole -= ray*pole.dot(ray)
        assert pole.length > 1e-7; pole.normalize()
        along = (a*a+distance*distance-b*b)/(2*distance)
        middle = start+ray*along+pole*math.sqrt(max(0., a*a-along*along))
        aim(uppers, lowers[0], middle-start); aim(lowers, end, target-middle)
        actual = [rig.pose.bones[n].matrix.translation.copy() for n in (uppers[0], lowers[0], end)]
        error = max(abs((actual[1]-actual[0]).length-a), abs((actual[2]-actual[1]).length-b))
        assert error < 1e-4 and (actual[2]-target).length < 1e-4
        return actual, error, (actual[2]-target).length

    suspend = runpy.run_path(str(visibility_path))['DenseViewportSuspend'](scene, meshes, rig)
    assert bpy.data.actions.get(ACTION) is None
    action = bpy.data.actions.new(ACTION); rig.animation_data_create(); rig.animation_data.action = action
    scene.render.fps = 24; scene.render.fps_base = 1; scene.frame_start = 1; scene.frame_end = 217
    observations, matrices, endpoint_basis = [], [], []
    bone_names = [b.name for b in rig.pose.bones]
    for frame in range(1, 218):
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            bone.rotation_mode = 'QUATERNION'; bone.location = (0, 0, 0)
            bone.rotation_quaternion = (1, 0, 0, 0); bone.scale = (1, 1, 1)
        amount = phase(frame)
        if amount:
            turn = Quaternion(across, deep_pitch*amount)
            hip_center = rest_hip_center.lerp(deep_hip_center, amount)
            root = turn.to_matrix().to_4x4()@rest[pelvis]
            root.translation = hip_center+turn@(heads[pelvis]-rest_hip_center)
            rig.pose.bones[pelvis].matrix = root
            bpy.context.view_layer.update()
            # The torso remains one native rigid chain; neck counter-rotates
            # gradually so gaze returns to its native world orientation.
            for name in neck:
                r = rest[name].to_quaternion()
                rig.pose.bones[name].rotation_quaternion = r.inverted()@Quaternion(across, -deep_pitch*amount/len(neck))@r
        bpy.context.view_layer.update()
        sample = {'frame': frame, 'crouch': amount, 'pelvis': list(rig.pose.bones[pelvis].matrix.translation),
                  'legs': {}, 'arms': {}, 'supports': {}}
        for side, suffix, sign in [('left', 'Left', 1), ('right', 'Right', -1)]:
            leg, arm, support = limbs['leg'+suffix], limbs['arm'+suffix], supports[side]
            foot, toe = support['foot'], support['toe']
            if amount:
                pole = heads[leg[1][0]].lerp(deep_knees[side], amount)
                actual, segment_error, ankle_error = solve(leg, heads[foot], pole)
                world_rotation(foot, rest[foot].to_quaternion()); world_rotation(toe, rest[toe].to_quaternion())
                start = rig.pose.bones[arm[0][0]].matrix.translation.copy(); length = arm[3]+arm[4]
                rest_wrist = rig.pose.bones[arm[2]].matrix.translation.copy()
                counterbalance = start+forward*(.70*length)-up*(.20*length)+across*(sign*.10*length)
                wrist = rest_wrist.lerp(counterbalance, amount)
                elbow_pole = start+forward*(.35*length)-up*(.45*length)+across*(sign*.25*length)
                arm_actual, arm_length_error, wrist_error = solve(arm, wrist, heads[arm[1][0]].lerp(elbow_pole, amount))
                lower_swing = (heads[arm[2]]-heads[arm[1][0]]).normalized().rotation_difference((arm_actual[2]-arm_actual[1]).normalized())
                world_rotation(arm[2], lower_swing@rest[arm[2]].to_quaternion())
            else:
                actual = [rig.pose.bones[n].matrix.translation.copy() for n in (leg[0][0], leg[1][0], foot)]
                segment_error = max(abs((actual[1]-actual[0]).length-leg[3]), abs((actual[2]-actual[1]).length-leg[4]))
                ankle_error = (actual[2]-heads[foot]).length
                arm_actual = [rig.pose.bones[n].matrix.translation.copy() for n in (arm[0][0], arm[1][0], arm[2])]
                arm_length_error = max(abs((arm_actual[1]-arm_actual[0]).length-arm[3]),
                                       abs((arm_actual[2]-arm_actual[1]).length-arm[4]))
                wrist_error = (arm_actual[2]-heads[arm[2]]).length
            maximum['segmentLengthM'] = max(maximum['segmentLengthM'], segment_error, arm_length_error)
            maximum['ankleTargetM'] = max(maximum['ankleTargetM'], ankle_error)
            maximum['wristTargetM'] = max(maximum['wristTargetM'], wrist_error)
            sample['arms'][side] = {'shoulder': list(arm_actual[0]), 'elbow': list(arm_actual[1]),
                'wrist': list(arm_actual[2]), 'segmentLengthResidualM': arm_length_error,
                'wristTargetResidualM': wrist_error}
            knee = 180-angle(actual[0]-actual[1], actual[2]-actual[1])
            root_q = rig.pose.bones[pelvis].matrix.to_quaternion()@rest[pelvis].to_quaternion().inverted()
            hip = angle(root_q@(heads[leg[1][0]]-heads[leg[0][0]]), actual[1]-actual[0])
            ankle = angle(heads[foot]-heads[leg[1][0]], actual[2]-actual[1])
            thigh, shin_up = actual[1]-actual[0], actual[1]-actual[2]
            hip_flex = math.degrees(math.atan2(thigh.dot(root_q@forward), -thigh.dot(root_q@up)))
            ankle_flex = math.degrees(math.atan2(shin_up.dot(support['forward']), shin_up.dot(up)))
            for key, value in [('kneeFlexionDegrees', knee), ('hipSwingFromRestDegrees', hip),
                               ('ankleSwingFromRestDegrees', ankle), ('hipSagittalFlexionDegrees', hip_flex),
                               ('ankleDorsiflexionFromVerticalDegrees', ankle_flex)]:
                peaks[side][key] = max(peaks[side][key], value)
            assert actual[1].dot(across)*sign > 0, ('Knee crossed body midline', frame, side)
            sole = rig.pose.bones[support['sole']].matrix
            sole_error = (sole.translation-support['restSole'].translation).length
            sole_angle = sole.to_quaternion().rotation_difference(support['restSole'].to_quaternion()).angle
            predicted = [sum(((rig.pose.bones[n].matrix@rest[n].inverted()@p)*w for n, w in row), Vector((0, 0, 0)))
                         for p, row in zip(support['reference'], support['weights'])]
            point_error = max((p-q).length for p, q in zip(predicted, support['reference']))
            assert max(sole_error, sole_angle, point_error) < 2e-5, ('Finite sole support moved', frame, side)
            for key, value in [('soleFrameM', sole_error), ('soleFrameRadians', sole_angle), ('directNativeSolePointM', point_error)]:
                maximum[key] = max(maximum[key], value)
            sample['legs'][side] = {'hip': list(actual[0]), 'knee': list(actual[1]), 'ankle': list(actual[2]),
                'segmentLengthResidualM': segment_error, 'ankleTargetResidualM': ankle_error,
                'kneeFlexionDegrees': knee, 'hipSwingFromRestDegrees': hip, 'ankleSwingFromRestDegrees': ankle,
                'hipSagittalFlexionDegrees': hip_flex, 'ankleDorsiflexionFromVerticalDegrees': ankle_flex}
            sample['supports'][side] = {'nativeVertexIds': support['ids'], 'directNativeSolePointResidualM': point_error,
                'soleFrameResidualM': sole_error, 'soleFrameResidualRadians': sole_angle}
        for name in spine_peaks:
            spine_peaks[name] = max(spine_peaks[name], math.degrees(rig.pose.bones[name].rotation_quaternion.angle))
        spine_world = angle(heads[neck[0]]-heads[pelvis],
                            rig.pose.bones[neck[0]].matrix.translation-rig.pose.bones[pelvis].matrix.translation)
        spine_world_peak = max(spine_world_peak, spine_world)
        sample['spineWorldSwingFromRestDegrees'] = spine_world
        bpy.context.view_layer.update()
        for bone in rig.pose.bones:
            assert all(math.isfinite(v) for row in bone.matrix_basis for v in row) and all(abs(v-1) < 1e-5 for v in bone.scale)
            for prop in ('location', 'rotation_quaternion', 'scale'):
                bone.keyframe_insert(data_path=prop, frame=frame, group=bone.name)
        world = np.asarray([rig.pose.bones[n].matrix for n in bone_names], dtype=np.float64)
        assert world.shape == (75, 4, 4) and np.isfinite(world).all()
        matrices.append(world)
        if frame in (1, 217):
            endpoint_basis.append([[list(row) for row in b.matrix_basis] for b in rig.pose.bones])
            assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
        if frame in {station[0] for station in STATIONS}:
            with suspend.visible_for_measurement(s['boot'] for s in supports.values()) as graph:
                for side, support in supports.items():
                    evaluated = support['boot'].evaluated_get(graph)
                    assert len(evaluated.data.vertices) == len(support['boot'].data.vertices)
                    points = [evaluated.data.vertices[i].co.copy() for i in support['ids']]
                    error = max((p-q).length for p, q in zip(points, support['reference']))
                    assert error < 2e-5, ('Evaluated actual finite sole points moved', frame, side, error)
                    maximum['evaluatedSolePointM'] = max(maximum['evaluatedSolePointM'], error)
                    sample['supports'][side]['evaluatedNativeSolePointResidualM'] = error
        observations.append(sample)
    assert len(action.slots) == 1 and endpoint_basis[0] == endpoint_basis[1]
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(action.slots[0])
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    visibility_report = suspend.restore()
    assert rest_before == rest_rows(rig) and fingerprints == {o.name: geometry(o) for o in meshes+[anatomy]}
    assert object_state == [(o.name, o.hide_render, [list(r) for r in o.matrix_world]) for o in scene.objects]
    scene.frame_set(1); out.mkdir(parents=True)
    candidate = out/'selected-deep-fixed-sole217.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate), compress=True)
    matrix_path = out/'native-world-matrices.npz'
    np.savez_compressed(matrix_path, boneNames=bone_names, frames=np.arange(1, 218), worldMatrices=np.asarray(matrices))
    report = {'accepted': False, 'candidate': {'path': str(candidate.relative_to(ROOT)), 'sha256': sha(candidate)},
        'sourceNative': config['native'], 'baseContract': config['baseContract'], 'sourceReceipt': config['sourceReceipt'],
        'recipeSHA256': sha(__file__), 'configSHA256': sha(config_path), 'action': ACTION,
        'actionSlot': action.slots[0].identifier, 'fps': 24, 'frameRange': [1, 217],
        'nativeMatrices': {'path': str(matrix_path.relative_to(ROOT)), 'sha256': sha(matrix_path), 'space': contract['nativeRest']['frame']},
        'sourceDerivedTargets': targets, 'peakJointAngles': peaks, 'peakSpineLocalSwingDegrees': spine_peaks,
        'peakSpineWorldSwingFromRestDegrees': spine_world_peak,
        'maximumResiduals': maximum, 'observations': observations, 'visibleMeshes': sorted(EXPECTED),
        'exact75TRSKeyedEveryFrame': True, 'neutralBasisReturnExact': True,
        'restAndOutfitFingerprintsUnchanged': fingerprints, 'viewportVisibility': visibility_report,
        'geometryHelperSHA256': sha(helper_path), 'visibilityHelperSHA256': sha(visibility_path),
        'limits': ['One authored geometry-derived deep crouch; no universal joint/anatomy comfort claim.',
            'Support landmark projection is not integrated tissue COM, muscle effort, balance simulation or contact acceptance.',
            'Per-frame support residuals use actual finite native boot vertices and source LBS; evaluated boot points are checked at six timing stations.',
            'Full dressed played motion, clipping/tissue deformation, actual Garage/GPU parity and devices remain parent gates.',
            'No geometry/material/skin/rest edit, export, external animation library, player promotion or device acceptance.']}
    (out/'motion.json').write_text(json.dumps(report, indent=2)+'\n')
    assert sha(native) == config['native']['sha256']
    print(json.dumps({'candidate': report['candidate'], 'action': ACTION, 'sourceDerivedTargets': targets,
                      'peakJointAngles': peaks, 'maximumResiduals': maximum}), flush=True)


if __name__ == '__main__':
    main()
