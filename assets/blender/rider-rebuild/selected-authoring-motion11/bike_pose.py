"""Author a bike pose on the installed M11 controls, without changing a mesh.

The caller supplies pelvis position/tilt and all four pole positions explicitly.
Contact matrices come from bike_context.mjs; every control remains independently
editable afterward. This is an authoring operation, not a contact/shape solver.
"""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector
from controls import ctrl


def apply_bike_pose(rig, context, document, bike_name, *, pelvis_bike,
                    pelvis_pitch_degrees, chest_pitch_degrees, head_nod_degrees,
                    knee_poles_bike, elbow_poles_bike, grip=0.75):
    bike = next(b for b in document['bikes'] if b['name'] == bike_name)
    transform = Matrix(document['bikeToNative'])
    for name in context['controls']:
        rig.pose.bones[name].matrix_basis = Matrix.Identity(4)
    pelvis = context['roles']['pelvis']
    rotation = Quaternion((1, 0, 0), math.radians(pelvis_pitch_degrees))
    matrix = (rotation @ context['rest'][pelvis].to_quaternion()).to_matrix().to_4x4()
    matrix.translation = transform @ Vector(pelvis_bike)
    rig.pose.bones[ctrl(pelvis)].matrix = matrix
    for name in context['roles']['trunk'][1:]:
        basis = context['rest'][name].to_quaternion()
        pitch = Quaternion((1, 0, 0), math.radians(chest_pitch_degrees / 3))
        rig.pose.bones[ctrl(name)].rotation_quaternion = basis.inverted() @ pitch @ basis
    for name, share in zip([*context['roles']['neck'], context['roles']['head']], (.2, .25, .55)):
        basis = context['rest'][name].to_quaternion()
        pitch = Quaternion((1, 0, 0), math.radians(head_nod_degrees * share))
        rig.pose.bones[ctrl(name)].rotation_quaternion = basis.inverted() @ pitch @ basis
    for name, values in bike['nativeControlMatrices'].items():
        rig.pose.bones[name].matrix = Matrix(values)
    for side in ('L', 'R'):
        for kind, positions in [('knee', knee_poles_bike), ('elbow', elbow_poles_bike)]:
            rig.pose.bones['CTRL-' + kind + '.' + side].matrix = Matrix.Translation(transform @ Vector(positions[side]))
        for digit in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            rig.pose.bones['CTRL-palm.' + side][digit] = grip
    bpy.context.view_layer.update()
    checks = []
    for limb in context['limbs']:
        end = rig.pose.bones[limb['end']].matrix.translation
        target = rig.pose.bones[limb['target']].matrix.translation
        start = rig.pose.bones[limb['uppers'][0]].matrix.translation
        middle = rig.pose.bones[limb['lowers'][0]].matrix.translation
        row = {'limb': limb['kind'] + limb['side'], 'targetM': (end - target).length,
               'lengthM': max(abs((middle - start).length - limb['lengths'][0]),
                              abs((end - middle).length - limb['lengths'][1]))}
        checks.append(row)
    # Report all four before rejecting an unreachable authored pose.
    assert all(max(r['targetM'], r['lengthM']) < .0001 for r in checks), checks
    return {'accepted': False, 'bike': bike_name, 'checks': checks,
            'controls': {name: {'location': list(rig.pose.bones[name].location),
                               'rotationWXYZ': list(rig.pose.bones[name].rotation_quaternion),
                               'scale': list(rig.pose.bones[name].scale)} for name in context['controls']}}


def add_saddle_context(document, bike_name):
    """Optional exact bike saddle guide, kept outside the rider rig and its export."""
    bike = next(b for b in document['bikes'] if b['name'] == bike_name)
    mesh = bpy.data.meshes.new('M11 reference saddle ' + bike_name)
    vertices = [p for triangle in bike['saddle'] for p in triangle['pointsNative']]
    mesh.from_pydata(vertices, [], [(i, i + 1, i + 2) for i in range(0, len(vertices), 3)])
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj['sourceBikeSHA256'] = bike['bike']['sha256']
    obj['purpose'] = 'Exact saddle reference only. Exclude from rider export.'
    obj.display_type = 'WIRE'; obj.hide_render = True
    return obj
