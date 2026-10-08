"""Parent-only tiny native driver test; no rider inputs, file saves or exports.

blender -b -t 2 --disable-autoexec --python-exit-code 1 --python probe-builtins.py
Exercises the same-rig property DAG and shape-key consumers on three bones.
"""
import json
import math
import runpy
import sys
from pathlib import Path
import bpy
from mathutils import Quaternion

HERE = Path(__file__).resolve().parent


def main():
    assert '--disable-autoexec' in sys.argv, 'Probe requires explicit disabled autoexec'
    source = runpy.run_path(str(HERE/'import-native.py'))
    maths = runpy.run_path(str(HERE/'driver_math.py'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    armature = bpy.data.armatures.new('NativeDriverProbe')
    rig = bpy.data.objects.new('NativeDriverProbe', armature)
    bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
    rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for name, x in [('P', 0.), ('L', .2), ('R', -.2)]:
        bone = armature.edit_bones.new(name); bone.head = (x, 0., 0.); bone.tail = (x, 1., 0.)
        if name != 'P': bone.parent = armature.edit_bones['P']
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.pose.bones['P'].rotation_mode = 'QUATERNION'
    rig.pose.bones['P'].rotation_quaternion = Quaternion((.8, .2, -.1, .3)).normalized()
    bpy.context.view_layer.update()
    roles = {'pelvis': 'P', 'L': 'L', 'R': 'R'}
    key = [Quaternion((1, 0, 0), .6), Quaternion((0, 0, 1), .9)]
    activation = {'restRelativeXYZW': [[0., 0., 0., 1.]]*2,
        'keyXYZW': [[q.x, q.y, q.z, q.w] for q in key], 'radiusRadians': math.hypot(.6, .9)}
    # Negative control only parses; never attach unsupported Python to the scene.
    parser_owner = bpy.data.objects.new('ParserOnly', None); parser_owner['result'] = 0.
    parser_curve = source['install_driver'](parser_owner, '["result"]',
        'max(0,1-x)**4*(4*x+1)', {'x': ('PROPERTY', 'unused')}, rig)
    assert not parser_curve.driver.is_simple_expression, 'Negative parser control changed'
    bpy.data.objects.remove(parser_owner)
    blocks = []
    for index in range(2):
        mesh = bpy.data.meshes.new('Consumer'+str(index)); mesh.from_pydata([(0, 0, 0)], [], [])
        obj = bpy.data.objects.new(mesh.name, mesh); bpy.context.collection.objects.link(obj)
        obj.shape_key_add(name='Basis'); blocks.append(obj.shape_key_add(name=source['NAME']))
    curves = []
    for name, expression, variables in maths['graph'](activation, roles):
        rig[name] = 0.
        curves.append(source['install_driver'](rig, '['+json.dumps(name)+']', expression, variables, rig))
    for block in blocks:
        curves.append(source['install_driver'](block, 'value', maths['SHAPE_EXPRESSION'],
            {'x': ('PROPERTY', maths['PREFIX']+'x')}, rig))
    source['check_driver_graph'](curves, require_valid=False)
    probes = source['probe_driver_graph'](rig, roles, activation, blocks, maths, curves)
    print(json.dumps({'accepted': False, 'status': 'SYNTHETIC_NATIVE_DRIVER_PROBE_ONLY',
        'blenderVersion': bpy.app.version_string, 'driverCount': len(curves),
        'unsupportedPowerRejected': True, 'useScripts': False, 'driverProbes': probes,
        'limits': ['No actual rider import, protected-field check, save/reopen or art acceptance.']}), flush=True)


if __name__ == '__main__': main()
