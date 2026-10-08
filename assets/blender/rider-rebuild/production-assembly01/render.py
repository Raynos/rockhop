"""Read-only pinned-native studio diagnostics; stills or actual action films.

blender -b -t 2 --python-exit-code 1 --python render.py -- SPEC FRESH_OUT
Never saves the native or exports a model. Parent judges played art.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
VIEWS = {'front': (0, -4, 1.0), 'profile': (4, 0, 1.0)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def studio(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('ProductionDiagnosticWorld')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55
    scene.world = world
    for obj in list(scene.objects):
        if obj.type == 'LIGHT': obj.hide_render = True
    for name, location, power, size in [('Key', (2, -3, 4), 650, 3),
                                       ('Fill', (-3, -2, 2), 450, 3),
                                       ('Rim', (0, 3, 3), 700, 2)]:
        light = bpy.data.lights.new('ProductionDiagnostic'+name, 'AREA')
        light.energy = power
        light.shape = 'DISK'
        light.size = size
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = location
        aim(obj, (0, 0, 1))
    camera = bpy.data.objects.new('ProductionDiagnosticCamera',
                                  bpy.data.cameras.new('ProductionDiagnosticCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 2.12
    return camera


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    specpath, out = map(lambda p: Path(p).resolve(), args)
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-assembly01')
    spec = json.loads(specpath.read_text())
    native = (ROOT/spec['native']['path']).resolve()
    assert sha(native) == spec['native']['sha256']
    assert spec['mode'] in ('stills', 'played')
    bpy.ops.wm.open_mainfile(filepath=str(native))
    scene = bpy.context.scene
    names = set(spec['objects'])
    body_name = spec.get('bodyObject', 'RiderBody')
    names.add(body_name)
    assert names <= set(scene.objects.keys()) and scene.objects[body_name].type == 'MESH'
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj.name not in names
            if obj.name in names:
                obj.hide_viewport = False
                obj.hide_set(False)
    assert not scene.objects[body_name].hide_render
    camera = studio(scene)
    focus = spec.get('focus', [0, -.025, .90])
    views = spec.get('views', VIEWS)
    camera.data.ortho_scale = spec.get('orthoScale', 2.12)
    assert len(focus) == 3 and all(len(p) == 3 for p in views.values())
    assert .1 <= camera.data.ortho_scale <= 3
    out.mkdir(parents=True)
    rig_name = spec.get('rigObject', 'RiderSkeleton')
    rig = scene.objects.get(rig_name)
    if spec['mode'] == 'stills':
        if rig is not None:
            assert rig.type == 'ARMATURE'
            rig.animation_data_clear()
            for bone in rig.pose.bones: bone.matrix_basis = Matrix.Identity(4)
            bpy.context.view_layer.update()
        frames = [0]
    else:
        assert rig is not None and rig.type == 'ARMATURE'
        action = bpy.data.actions.get(spec['actionName'])
        assert action is not None, 'Pinned native must already contain the intended review action'
        rig.animation_data_create()
        rig.animation_data.action = action
        if action.slots:
            # Explicit action slot avoids binding a Blender5 multi-slot action
            # to a different animated object. Caller names it when ambiguous.
            identifier = spec.get('actionSlot')
            if identifier is None:
                assert len(action.slots) == 1, 'Name actionSlot for a multi-slot action'
                slot = action.slots[0]
            else:
                slot = next(s for s in action.slots if s.identifier == identifier)
            rig.animation_data.action_slot = slot
        first, last = spec['frameRange']
        assert isinstance(first, int) and isinstance(last, int) and first < last
        frames = list(range(first, last+1))
        scene.render.fps = spec.get('fps', 24)
        scene.render.fps_base = 1
    outputs = []
    for view, position in views.items():
        camera.location = position
        aim(camera, focus)
        if spec['mode'] == 'stills':
            path = out/(view+'.png')
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            outputs.append({'path': str(path), 'sha256': sha(path), 'view': view})
        else:
            directory = out/view
            directory.mkdir()
            for index, frame in enumerate(frames):
                scene.frame_set(frame)
                scene.render.filepath = str(directory/f'{index:04d}.png')
                bpy.ops.render.render(write_still=True)
            video = out/(view+'.mp4')
            subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                            '-framerate', str(scene.render.fps), '-i', str(directory/'%04d.png'),
                            '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p',
                            '-an', str(video)], check=True)
            outputs.append({'path': str(video), 'sha256': sha(video), 'view': view,
                            'frames': len(frames), 'continuousFrames': True, 'audio': False})
    assert sha(native) == spec['native']['sha256'], 'Diagnostic renderer changed native source'
    result = {'accepted': False, 'recipeSHA256': sha(__file__), 'specSHA256': sha(specpath),
              'sourceNative': spec['native'], 'nativeSourceUnchanged': True,
              'selectedMeshes': sorted(names), 'completeBodyVisible': body_name,
              'mode': spec['mode'], 'outputs': outputs,
              'framing': {'focus': focus, 'views': views,
                          'orthoScale': camera.data.ortho_scale},
              'studio': {'resolution': [640, 640], 'engine': 'Cycles', 'device': 'CPU',
                         'threads': 2, 'samples': 12, 'viewTransform': 'AgX'},
              'limits': ['Studio diagnostics only; parent judges moving art.',
                         'Stills cannot accept motion. Actual Garage/game and device review pending.',
                         'No native save, geometry/material rebuild or player export.']}
    (out/'render.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__': main()
