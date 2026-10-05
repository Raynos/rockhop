"""Analytic native own51 support driver; anatomical controls, no rest edits.

+X forward, +Z up, -Y left; metres. Surface support remains a measured
output, not an implication of the ankle target. Call only on a diagnostic
in-memory rig with its existing immutable inverse binds.
"""
import math
from mathutils import Matrix, Quaternion, Vector

CLIPS = {'idle': 2.0, 'crouch': 2.5, 'jump-land': 2.3}


def prepare(rig):
    assert len(rig.data.bones) == 51
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        for constraint in bone.constraints:
            constraint.mute = True
    rest = {bone.name: bone.matrix_local.copy() for bone in rig.data.bones}
    return {'rest': rest, 'ankles': {s: rest['foot.' + s].translation.copy() for s in ['L', 'R']},
            'lengths': {s: ((rest['shin.'+s].translation-rest['thigh.'+s].translation).length,
                           (rest['foot.'+s].translation-rest['shin.'+s].translation).length) for s in ['L', 'R']}}


def update():
    import bpy
    bpy.context.view_layer.update()


def set_orientation(bone, orientation):
    matrix = orientation.to_matrix().to_4x4()
    matrix.translation = bone.matrix.translation
    bone.matrix = matrix
    update()


def direct(bone, direction):
    axis = bone.matrix.to_quaternion() @ Vector((0, 1, 0))
    rotation = axis.rotation_difference(Vector(direction).normalized()) @ bone.matrix.to_quaternion()
    set_orientation(bone, rotation)


def two_bone(rig, upper_name, lower_name, end_name, target, pole):
    """Solve a connected chain, explicitly report unreachable input targets."""
    upper, lower, end = [rig.pose.bones[name] for name in [upper_name, lower_name, end_name]]
    hip = upper.matrix.translation.copy()
    a = (lower.matrix.translation-hip).length
    b = (end.matrix.translation-lower.matrix.translation).length
    delta = Vector(target)-hip
    requested = delta.length
    assert requested > 1e-9 and a > 0 and b > 0
    distance = min(max(requested, abs(a-b)+1e-7), a+b-1e-7)
    direction = delta.normalized()
    bend = Vector(pole)-direction*Vector(pole).dot(direction)
    assert bend.length > 1e-8, 'Pole cannot be parallel to the limb target'
    bend.normalize()
    along = (a*a-b*b+distance*distance)/(2*distance)
    height = math.sqrt(max(0, a*a-along*along))
    knee = hip+direction*along+bend*height
    admitted_target = hip+direction*distance
    direct(upper, knee-hip)
    direct(lower, admitted_target-lower.matrix.translation)
    residual = (end.matrix.translation-Vector(target)).length
    return {'requestedDistanceM': requested, 'chainLengthM': a+b,
            'targetClampedM': abs(distance-requested), 'endResidualM': residual}


def smooth(value):
    value = min(max(value, 0.0), 1.0)
    return value*value*(3-2*value)


def controls(clip, time_s):
    assert clip in CLIPS and 0 <= time_s <= CLIPS[clip]+1e-9
    cycle = time_s / CLIPS[clip]
    offset = Vector((0, 0, 0))
    tilt = 0.0
    phase = 'double-support'
    ankle_lift = 0.0
    arm_reach = 0.0
    if clip == 'idle':
        breath = math.sin(2*math.pi*cycle)
        offset.z = -.002*(1-math.cos(2*math.pi*cycle))
        tilt = .6*breath
    elif clip == 'crouch':
        amount = math.sin(math.pi*cycle)**2
        offset.x = -.11*amount
        offset.z = -.23*amount
        tilt = 18*amount
        arm_reach = amount
    else:
        # Smooth preload -> parabolic flight -> grounded damped recovery.
        if time_s <= .45:
            amount = math.sin(math.pi*time_s/.45)**2
            offset.x = -.055*amount
            offset.z = -.12*amount
            tilt = 9*amount
        elif time_s < 1.15:
            flight = (time_s-.45)/.70
            height = 4*.28*flight*(1-flight)
            tuck = .045*math.sin(math.pi*flight)**2
            offset.z = height-tuck
            ankle_lift = height
            phase = 'airborne'
            arm_reach = .65*math.sin(math.pi*flight)
        else:
            recovery = (time_s-1.15)/(CLIPS[clip]-1.15)
            amount = math.sin(math.pi*min(recovery*1.8,1))**2*math.exp(-2*recovery)
            offset.x = -.065*amount
            offset.z = -.17*amount
            tilt = 12*amount
            arm_reach = .4*amount
    return {'rootOffsetNativeM': offset, 'torsoTiltDegrees': tilt,
            'supportPhase': phase, 'ankleLiftM': ankle_lift, 'armReach': arm_reach}


def apply(rig, contract, clip, time_s):
    import bpy
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)
    update()
    control = controls(clip, time_s)
    root = rig.pose.bones['pelvis']
    root.location = rig.data.bones['pelvis'].matrix_local.to_3x3().inverted() @ control['rootOffsetNativeM']
    update()
    for name, fraction in [('spine', .55), ('chest', .45)]:
        bone = rig.pose.bones[name]
        axis = bone.bone.matrix_local.to_quaternion()
        delta = axis.inverted() @ Quaternion(Vector((0, 1, 0)), math.radians(control['torsoTiltDegrees']*fraction)) @ axis
        bone.rotation_quaternion = delta
        update()
    residuals = {}
    targets = {}
    for side in ['L', 'R']:
        target = contract['ankles'][side] + Vector((0, 0, control['ankleLiftM']))
        residuals['leg.'+side] = two_bone(rig, 'thigh.'+side, 'shin.'+side, 'foot.'+side, target, (1, 0, 0))
        set_orientation(rig.pose.bones['foot.'+side], contract['rest']['foot.'+side].to_quaternion())
        targets[side] = list(target)
        sign = -1 if side == 'L' else 1
        shoulder = rig.pose.bones['upperArm.'+side].matrix.translation
        pelvis = rig.pose.bones['pelvis'].matrix.translation
        reach = control['armReach']
        hand = Vector((pelvis.x+.045+.29*reach, shoulder.y+sign*.07, pelvis.z+.075+.22*reach))
        residuals['arm.'+side] = two_bone(rig, 'upperArm.'+side, 'forearm.'+side, 'hand.'+side, hand, (1, sign*.2, 0))
    assert all(contract['rest'][name] == rig.data.bones[name].matrix_local for name in contract['rest'])
    return {'clip': clip, 'timeS': time_s, 'supportPhase': control['supportPhase'],
            'rootOffsetNativeM': list(control['rootOffsetNativeM']),
            'ankleTargetsNativeM': targets, 'limbResiduals': residuals,
            'limits': ['Ankle/limb targets only; actual evaluated sole support is measured separately.']}
