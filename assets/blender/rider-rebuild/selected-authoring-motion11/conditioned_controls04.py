"""Explicit limb FK/IK modes and deterministic native75 action playback.

Original native75 rest and skin fields never change. The qualified controls11
recipe remains the foundation; only its nondeforming mechanism names, gating,
and the destinations of its existing finger-curl drivers change.
"""
import bpy
from mathutils import Matrix
import controls as base

LIVE = 'M11_liveControls'
IK = 'M11_ikMode'
rest_rows, ctrl = base.rest_rows, base.ctrl


def property_driver(owner, property_name, rig, expression, variables):
    curve = owner.driver_add(property_name)
    driver = curve.driver
    driver.type = 'SCRIPTED'
    driver.expression = expression
    for name, path in variables:
        variable = driver.variables.new()
        variable.name = name
        variable.type = 'SINGLE_PROP'
        variable.targets[0].id = rig
        variable.targets[0].data_path = path
    return curve


def install(rig, contract):
    context = base.install(rig, contract)
    names = set(context['names'])
    original_rest = rest_rows(rig, names)
    renamed = {}
    for limb in context['limbs']:
        for field in ('mechanismUpper', 'mechanismLower'):
            old = limb[field]
            new = old.replace('MCH-', 'CTRL-FK-', 1)
            rig.data.bones[old].name = new
            assert new in rig.pose.bones and old not in rig.pose.bones
            renamed[old] = new
            limb[field] = new
            rig.data.bones[new].hide = False
            rig.data.bones[new].color.palette = 'THEME03'
    # Do not rely on Blender's rename propagation for constraint subtargets.
    for bone in rig.pose.bones:
        for constraint in bone.constraints:
            if constraint.target == rig and constraint.subtarget in renamed:
                constraint.subtarget = renamed[constraint.subtarget]
    context['fkControls'] = [limb[field] for limb in context['limbs']
                             for field in ('mechanismUpper', 'mechanismLower')]
    rig[LIVE] = 1.
    rig.id_properties_ui(LIVE).update(min=0., max=1.,
        description='1: author controls. 0: native75 playback. Named actions key this mode explicitly.')
    for limb in context['limbs']:
        target = rig.pose.bones[limb['targetControl']]
        target[IK] = 1.
        target.id_properties_ui(IK).update(min=0., max=1.,
            description='0: edit the visible CTRL-FK upper/lower bones. 1: use palm/sole and pole IK.')

    # Direct quaternion drivers on deform bones would override a generic clip
    # even with limb constraints disabled. Move the exact curl expression onto
    # a nondeforming helper and gate its LOCAL rotation constraint instead.
    digits = [name for side in ('left', 'right')
              for chain in contract['specification']['hands'][side]['digits'].values() for name in chain]
    assert len(digits) == len(set(digits)) == 30
    source_drivers = {}
    for name in digits:
        path = f'pose.bones["{name}"].rotation_quaternion'
        curves = [curve for curve in rig.animation_data.drivers if curve.data_path == path]
        assert sorted(curve.array_index for curve in curves) == [0, 1, 2, 3]
        rows = []
        for curve in curves:
            driver = curve.driver
            assert driver.type == 'SCRIPTED' and len(driver.variables) == 1
            variable = driver.variables[0]
            assert variable.type == 'SINGLE_PROP' and variable.targets[0].id == rig
            rows.append({'index': curve.array_index, 'expression': driver.expression,
                         'variable': variable.name, 'path': variable.targets[0].data_path})
        source_drivers[name] = rows
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    edit = rig.data.edit_bones
    for name in digits:
        original = edit[name]
        helper = edit.new('MCH-curl-'+name)
        helper.head = (0, 0, 0)
        helper.tail = (0, original.length, 0)
        helper.matrix = original.matrix.copy()
        helper.parent = original.parent
        helper.use_connect = False
        helper.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    assert rest_rows(rig, names) == original_rest, 'Curl helpers changed original75 rest'
    for name in digits:
        bone = rig.pose.bones[name]
        helper = rig.pose.bones['MCH-curl-'+name]
        helper.rotation_mode = 'QUATERNION'
        helper.matrix_basis = Matrix.Identity(4)
        helper.bone.hide = True
        for row in source_drivers[name]:
            assert bone.driver_remove('rotation_quaternion', row['index'])
            curve = helper.driver_add('rotation_quaternion', row['index'])
            driver = curve.driver
            driver.type = 'SCRIPTED'
            driver.expression = row['expression']
            variable = driver.variables.new()
            variable.name = row['variable']
            variable.type = 'SINGLE_PROP'
            variable.targets[0].id = rig
            variable.targets[0].data_path = row['path']
        bone.rotation_quaternion = (1, 0, 0, 0)
        constraint = bone.constraints.new('COPY_ROTATION')
        constraint.name = 'M11 gated curl'
        constraint.target = rig
        constraint.subtarget = helper.name
        constraint.owner_space = constraint.target_space = 'LOCAL'
        constraint.mix_mode = 'REPLACE'
    ik_targets = {limb['mechanismLower']: limb['targetControl'] for limb in context['limbs']}
    for bone in rig.pose.bones:
        for constraint in bone.constraints:
            variables = [('live', f'["{LIVE}"]')]
            expression = 'live'
            if constraint.type == 'IK':
                variables.append(('ik', f'pose.bones["{ik_targets[bone.name]}"]["{IK}"]'))
                expression = 'live*ik'
            property_driver(constraint, 'influence', rig, expression, variables)
    assert not any(curve.data_path.startswith(f'pose.bones["{name}"].rotation_quaternion')
                   for name in names for curve in rig.animation_data.drivers)
    assert all(not bone.use_deform for bone in rig.data.bones if bone.name not in names)
    context['liveProperty'] = LIVE
    context['ikProperty'] = IK
    context['curlHelpers'] = ['MCH-curl-'+name for name in digits]
    rig['M11_controls'] = ('Explicit FK/IK: visible CTRL-FK upper/lower bones, palm/sole IK and poles. '
        'Native.* playback actions disable all added constraints; Author.* actions enable controls and reset native channels. '
        'Finger curl is confined to gated helpers. No trusted frame handlers.')
    bpy.context.view_layer.update()
    return context
