"""Native Blender controls for the exact selected75; no mesh or rest replacement.

Only nondeforming controls/mechanisms are added. Native IK uses two full-length
mechanism bones; their rotations drive the existing split deform segments.
"""
import json
import math
import bpy
from mathutils import Matrix, Quaternion, Vector


def rest_rows(rig, names=None):
    return [{'name': b.name, 'parent': b.parent.name if b.parent else None,
             'head': list(b.head_local), 'tail': list(b.tail_local),
             'matrix': [list(r) for r in b.matrix_local],
             'useConnect': b.use_connect, 'useDeform': b.use_deform}
            for b in rig.data.bones if names is None or b.name in names]


def ctrl(name):
    return name.replace('DEF-', 'CTRL-', 1)


def install(rig, contract):
    expected = contract['nativeRest']['bones']; names = [b['name'] for b in expected]
    assert rest_rows(rig) == expected and len(names) == 75 and rig.matrix_world.is_identity
    assert all(not b.constraints for b in rig.pose.bones)
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'; bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    heads = {b.name: b.head_local.copy() for b in rig.data.bones}
    roles = contract['specification']['roles']; one = lambda value: value[0] if isinstance(value, list) else value
    fk = [*roles['trunk'], *roles['neck'], one(roles['head']), roles['shoulderLeft'], roles['shoulderRight']]
    assert len(fk) == len(set(fk))
    bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); edit = rig.data.edit_bones; controls = []; limbs = []; added = {}

    def add(name, matrix, length, parent=None):
        # EditBone.matrix carries direction/roll, not length. A fresh zero-length
        # bone cannot retain that direction: establish its tail BEFORE assigning
        # the desired matrix. Actual neutral-probe01 demonstrated the old failure.
        assert length > 0
        b = edit.new(name); b.head = (0, 0, 0); b.tail = (0, length, 0)
        b.matrix = matrix; b.use_deform = False
        b.parent = edit[parent] if parent else None; b.use_connect = False
        added[name] = (matrix.copy(), length); return b

    for name in fk:
        parent = edit[name].parent.name if edit[name].parent else None
        add(ctrl(name), rest[name], edit[name].length, ctrl(parent) if parent in fk else None)
        controls.append(ctrl(name))
    for suffix, role_side, side in [('L', 'Left', 'left'), ('R', 'Right', 'right')]:
        for kind, upper_role, lower_role, end_role, socket in [
                ('arm', 'upperArm', 'forearm', 'wrist', 'PalmSocket.'+suffix),
                ('leg', 'thigh', 'shin', 'foot', 'SoleSocket.'+suffix)]:
            uppers, lowers = roles[upper_role+role_side], roles[lower_role+role_side]
            end = one(roles[end_role+role_side]); upper, lower = uppers[0], lowers[0]
            start, middle, tip = heads[upper], heads[lower], heads[end]
            line = (tip-start).normalized(); bend = middle-start-line*(middle-start).dot(line)
            assert bend.length > 1e-5, ('Need a declared rest bend plane', kind, suffix)
            pole_location = middle+bend.normalized()*.45
            target_name = 'CTRL-'+('palm' if kind == 'arm' else 'sole')+'.'+suffix
            pole_name = 'CTRL-'+('elbow' if kind == 'arm' else 'knee')+'.'+suffix
            add(target_name, rest[socket], .10); pole_matrix = Matrix.Translation(pole_location)
            add(pole_name, pole_matrix, .10); controls += [target_name, pole_name]
            target = 'MCH-target-'+end; add(target, rest[end], .06, target_name)
            m_upper, m_lower = 'MCH-'+upper, 'MCH-'+lower
            parent = ctrl(roles['shoulder'+role_side]) if kind == 'arm' else ctrl(one(roles['pelvis']))
            add(m_upper, rest[upper], (middle-start).length, parent)
            add(m_lower, rest[lower], (tip-middle).length, m_upper); edit[m_lower].use_connect = True
            normal = (tip-start).cross(pole_location-start)
            pole_axis = normal.cross(middle-start).normalized()
            x = edit[m_upper].x_axis.normalized(); z = edit[m_upper].z_axis.normalized()
            # Blender IK_QJacobianSolver::ConstrainPoleVector constructs
            # up = rootX*cos(angle) + rootZ*sin(angle). A signed angle around
            # rootY reverses this convention because X cross Z = -Y.
            pole_angle = math.atan2(pole_axis.dot(z), pole_axis.dot(x))
            limbs.append({'kind': kind, 'side': suffix, 'uppers': uppers, 'lowers': lowers, 'end': end,
                          'socket': socket, 'targetControl': target_name, 'poleControl': pole_name,
                          'target': target, 'mechanismUpper': m_upper, 'mechanismLower': m_lower,
                          'poleAngle': pole_angle, 'lengths': [(middle-start).length, (tip-middle).length]})
    bpy.ops.object.mode_set(mode='OBJECT')
    assert rest_rows(rig, set(names)) == expected, 'Adding controls changed a source rest bone'
    added_rest_residual = 0.; added_rest_checks = []
    for name, (matrix, length) in added.items():
        b = rig.data.bones[name]
        error = max(abs(b.matrix_local[i][j]-matrix[i][j]) for i in range(4) for j in range(4))
        added_rest_residual = max(added_rest_residual, error)
        # Source foot/socket matrices already have ~3.4e-5 Gram residual.
        # EditBone reconstruction normalizes its direction/roll. Measure that
        # known source deviation in metres instead of an arbitrary matrix epsilon.
        delta = b.matrix_local @ matrix.inverted()
        linear = math.sqrt(sum((delta[i][j]-(i==j))**2 for i in range(3) for j in range(3)))
        bound = linear*2 + delta.translation.length
        gram = matrix.to_3x3().transposed() @ matrix.to_3x3()
        added_rest_checks.append({'name':name, 'maximumMatrixComponentResidual':error,
            'sourceGramFrobenius':math.sqrt(sum((gram[i][j]-(i==j))**2 for i in range(3) for j in range(3))),
            'sourceDeterminant':matrix.to_3x3().determinant(),
            'affineDisplacementBoundWithin2mM':bound, 'lengthResidualM':abs(b.length-length)})
    print(json.dumps({'addedRestBeforeConstraints':added_rest_checks}),flush=True)
    assert all(r['affineDisplacementBoundWithin2mM']<.0001 and r['lengthResidualM']<.0001 for r in added_rest_checks), ('Added control rest exceeds 0.1 mm physical bound',added_rest_checks)

    def copy(name, target, kind):
        c = rig.pose.bones[name].constraints.new(kind); c.name = 'M11 '+target
        c.target = rig; c.subtarget = target; c.target_space = c.owner_space = 'POSE'; return c

    for name in fk: copy(name, ctrl(name), 'COPY_TRANSFORMS')
    for limb in limbs:
        bone = rig.pose.bones[limb['mechanismLower']]; ik = bone.constraints.new('IK')
        ik.name = 'M11 native two-bone IK'; ik.target = rig; ik.subtarget = limb['target']
        ik.pole_target = rig; ik.pole_subtarget = limb['poleControl']; ik.pole_angle = limb['poleAngle']
        ik.chain_count = 2; ik.use_stretch = False; ik.iterations = 64
        for name in [limb['mechanismUpper'], limb['mechanismLower']]: rig.pose.bones[name].ik_stretch = 0.
        for name in limb['uppers']: copy(name, limb['mechanismUpper'], 'COPY_ROTATION')
        for name in limb['lowers']: copy(name, limb['mechanismLower'], 'COPY_ROTATION')
        copy(limb['end'], limb['target'], 'COPY_ROTATION')
    for suffix, side in [('L', 'left'), ('R', 'right')]:
        control = rig.pose.bones['CTRL-palm.'+suffix]
        hand = contract['specification']['hands'][side]
        for digit, digit_bones in hand['digits'].items():
            control[digit] = 0.; control.id_properties_ui(digit).update(min=0., max=1., description='Open to anatomically measured curl')
            for name in digit_bones:
                flex = contract['driver']['digitFlex'][side][name]; angle = flex['maxRadians']*flex['positiveSign']
                axis = Vector(flex['axisLocal']).normalized(); bone = rig.pose.bones[name]; bone.rotation_mode = 'QUATERNION'
                for i in range(4):
                    driver = bone.driver_add('rotation_quaternion', i).driver
                    v = driver.variables.new(); v.name = 'curl'; v.type = 'SINGLE_PROP'
                    v.targets[0].id = rig; v.targets[0].data_path = f'pose.bones["{control.name}"]["{digit}"]'
                    driver.expression = f'cos(curl*{angle/2:.12g})' if i == 0 else f'{axis[i-1]:.12g}*sin(curl*{angle/2:.12g})'
    for bone in rig.pose.bones: bone.rotation_mode = 'QUATERNION'
    for bone in rig.data.bones:
        bone.hide = bone.name not in controls
        if bone.name in controls: bone.color.palette = 'THEME04'
    rig.show_in_front = True; rig.data.display_type = 'STICK'
    rig['M11_controls'] = 'Native hips/spine/head FK; palm/sole IK and elbow/knee poles; five curl properties on each palm. No trusted Python handlers.'
    bpy.context.view_layer.update()
    residual = max((rig.pose.bones[n].matrix.translation-rest[n].translation).length for n in names)
    neutral_checks = []
    for name in names:
        actual = rig.pose.bones[name].matrix.copy(); operator = actual @ rest[name].inverted()
        linear = math.sqrt(sum((operator[i][j]-(i==j))**2 for i in range(3) for j in range(3)))
        neutral_checks.append({'name':name, 'nativePoseMatrix':[list(r) for r in actual],
            'skinOperator':[list(r) for r in operator],
            'affineDisplacementBoundWithin2mM':linear*2+operator.translation.length})
    neutral_bound = max(r['affineDisplacementBoundWithin2mM'] for r in neutral_checks)
    print(json.dumps({'neutral75BeforeActions':neutral_checks, 'neutralMaximumAffineBoundWithin2mM':neutral_bound}),flush=True)
    assert residual < .0001, ('Native controls failed source rest pose', residual, [{k:l[k] for k in ('kind','side','poleAngle')} for l in limbs])
    assert neutral_bound < .0001, ('Native controls changed neutral skin operator',
        sorted(neutral_checks,key=lambda r:r['affineDisplacementBoundWithin2mM'],reverse=True)[:5])
    return {'names': names, 'controls': controls, 'fk': fk, 'limbs': limbs, 'rest': rest, 'heads': heads,
            'roles': roles, 'sourceRestResidualM': residual, 'addedRestMaximumMatrixResidual': added_rest_residual,
            'addedRestBeforeConstraints':added_rest_checks,'neutral75BeforeActions':neutral_checks,
            'neutralMaximumAffineBoundWithin2mM':neutral_bound}


def set_world(rig, name, matrix):
    rig.pose.bones[name].matrix = matrix


def rotate_local(rig, context, name, axis, degrees):
    r = context['rest'][name].to_quaternion(); local_axis = r.inverted() @ Vector(axis)
    rig.pose.bones[ctrl(name)].rotation_quaternion = Quaternion(local_axis, math.radians(degrees))
