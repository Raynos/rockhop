"""Actual continuous selected dressed action, read-only native/PBR, silent film.

Parent serialized CPU2 only. One explicit view per run; no sparse frame montage.
blender -b -t 2 --python-exit-code 1 --python render.py -- MOTION_JSON FRESH_OUT VIEW
VIEW: full, left, right, hands. Parent plays each requested film to natural end.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
VIEWS = {'full': ((-4, -5, 1.1), (0, -.025, .92), 2.16),
         'left': ((-4, 0, 1.0), (0, -.025, .92), 2.16),
         'right': ((4, 0, 1.0), (0, -.025, .92), 2.16),
         'hands': ((-3, -4, 1.65), (0, -.38, 1.37), .85)}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024): h.update(block)
    return h.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 3
    receipt_path, out = (Path(p).resolve() for p in args[:2]); view = args[2]
    assert view in VIEWS and not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-dressed-motion01')
    receipt_sha = sha(receipt_path); receipt = json.loads(receipt_path.read_text())
    assert receipt['accepted'] is False and receipt['frameRange'] == [1, 145] and receipt['fps'] == 24
    native = ROOT/receipt['candidate']['path']; assert sha(native) == receipt['candidate']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(native)); scene = bpy.context.scene
    rig = bpy.data.objects['RiderSkeleton']; assert len(rig.data.bones) == 75
    action = bpy.data.actions[receipt['action']]; assert rig.animation_data.action == action
    rig.animation_data.action_slot = next(s for s in action.slots if s.identifier == receipt['actionSlot'])
    visible = sorted(o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render)
    assert visible == receipt['visibleMeshes'] and len(visible) == 7
    assert all(layer.material_override is None for layer in scene.view_layers)
    scene.render.engine = 'BLENDER_EEVEE'; scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.resolution_x = 640; scene.render.resolution_y = 640; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    scene.render.film_transparent = False; scene.render.use_compositing = False; scene.render.use_sequencer = False
    scene.render.fps = 24; scene.render.fps_base = 1; scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Selected dressed actual PBR world'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55; scene.world = world
    for obj in scene.objects:
        if obj.type == 'LIGHT': obj.hide_render = True
    for name, location, power, size in [('Key', (2,-3,4), 650, 3), ('Fill', (-3,-2,2), 450, 3), ('Rim', (0,3,3), 700, 2)]:
        light = bpy.data.lights.new('Selected dressed '+name, 'AREA'); light.energy = power; light.shape = 'DISK'; light.size = size
        obj = bpy.data.objects.new(light.name, light); scene.collection.objects.link(obj); obj.location = location; aim(obj, (0,0,1))
    camera = bpy.data.objects.new('Selected dressed fixed camera', bpy.data.cameras.new('Selected dressed fixed camera'))
    scene.collection.objects.link(camera); scene.camera = camera; camera.data.type = 'ORTHO'
    position, focus, scale = VIEWS[view]; camera.location = position; camera.data.ortho_scale = scale; aim(camera, focus)
    out.mkdir(parents=True); frames = out/'frames'; frames.mkdir(); start = time.monotonic()
    for index, frame in enumerate(range(1, 146)):
        scene.frame_set(frame); bpy.context.view_layer.update()
        scene.render.filepath = str(frames/f'{index:04d}.png'); bpy.ops.render.render(write_still=True)
        if (index+1)%12 == 0: print('DRESSED_MOVIE_PROGRESS', index+1, 145, round(time.monotonic()-start, 3), flush=True)
    movie = out/(view+'.mp4')
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', '24', '-i', str(frames/'%04d.png'),
                    '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', '-an', str(movie)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(movie)]))
    video = [s for s in probe['streams'] if s['codec_type'] == 'video']; assert len(video) == 1
    assert not [s for s in probe['streams'] if s['codec_type'] == 'audio']
    assert int(video[0]['nb_read_frames']) == 145 and video[0]['avg_frame_rate'] == '24/1'
    assert sha(native) == receipt['candidate']['sha256'] and sha(receipt_path) == receipt_sha
    report = {'accepted': False, 'movie': {'path': str(movie.relative_to(ROOT)), 'sha256': sha(movie), 'frames': 145, 'fps': 24, 'audioStreams': 0},
              'native': receipt['candidate'], 'motionReceipt': {'path': str(receipt_path), 'sha256': receipt_sha},
              'recipeSHA256': sha(__file__), 'engine': 'BLENDER_EEVEE', 'threads': 2, 'continuousFrames': True,
              'visibleMeshes': visible, 'view': view, 'cameraPosition': position, 'focus': focus, 'orthoScale': scale,
              'elapsedSeconds': time.monotonic()-start, 'limits': ['Parent alone judges played art; all R0-R5 open.',
                  'Generic reach/curl only; actual Garage/ride remains required for bike contacts and crouch/extremes.',
                  'Hands view crops other garments; full view and both profiles are independent required reviews.',
                  'No native save, source geometry/PBR mutation, export, browser or audio.']}
    (out/'render.json').write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report['movie']), flush=True)


if __name__ == '__main__': main()
