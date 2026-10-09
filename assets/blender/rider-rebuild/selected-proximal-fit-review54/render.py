"""Parent-guarded, matched actual47/50 rest turntable and tangent diagnosis.

No native save, source edit, model substitute, pose gate or art acceptance.
CLI: render.py -- original|registered cloth|wearer FRESH_OUT ORIGINAL_RECEIPT|-
"""
import hashlib
import json
import math
import runpy
import subprocess
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
OUT = ROOT/'harness/out/rider-rebuild/selected-proximal-fit-review54'
NATIVES = {
    'original': {'path': 'harness/out/rider-rebuild/selected-sleeve-component47/intake01/UNACCEPTED-selected-sleeve-intake47.blend',
                 'sha256': 'ff2ba521943db9b8586e75ed674fc8122d7612df5cf5d609ffb9ef48c9016bc7'},
    'registered': {'path': 'harness/out/rider-rebuild/selected-proximal-hoodie-fit50/component01/UNACCEPTED-selected-proximal-hoodie-fit50.blend',
                   'sha256': 'ef5f8e9be05fee40f5c162c3d5ced791c96a1e1fef39a3c08abfa81b0e025b89'}}
QUALIFIED50 = {'path': 'harness/out/rider-rebuild/selected-proximal-hoodie-fit50/component01/component-qualified.json',
               'sha256': 'cc39eb66657d46517dedeab8fcf04783bb79d0456c89992e0069f4d5b4a68636'}
SOURCE_PAIR = {'path': 'docs/evidence/rider-rebuild/selected-sleeve-support49/source-pair01.json',
               'sha256': 'c1b7999f62f8f7172bba59bc9aa0027067d102835c3b865fc5bd3f6276e076da'}
RENDER_HELPER = {'path': 'assets/blender/rider-rebuild/selected-dressed-motion01/render.py',
                 'sha256': 'a0ab4b6b68b31c875a5bf576561ef40f48e5d87f13d1a4f4c4ca8da4c6117984'}
FRAME_COUNT, FPS, RESOLUTION = 48, 12, 512
FOCUS, SCALE = (0., 0., 1.25), 1.28


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1048576): h.update(chunk)
    return h.hexdigest()


def pin(path): return {'path': str(Path(path).resolve().relative_to(ROOT)), 'sha256': sha(path)}


def checked(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], row['path']; return path


def geometry(obj):
    assert obj.matrix_world.is_identity
    points = np.empty((len(obj.data.vertices), 3), np.float32); obj.data.vertices.foreach_get('co', points.ravel())
    obj.data.calc_loop_triangles(); faces = np.empty((len(obj.data.loop_triangles), 3), np.int32)
    obj.data.loop_triangles.foreach_get('vertices', faces.ravel())
    return points, faces


def diagnose(original, current, faces, body, out):
    helper = runpy.run_path(str(HERE/'tangent.py'))
    report, stretch, area = helper['measure'](original.astype(float), current.astype(float), faces)
    pair = json.loads(checked(SOURCE_PAIR).read_text()); first = pair['sourceFaceId']
    hit = pair['rays']['awayArmAxis']['firstHits'][0]; second = hit['sourceFaceId']
    bary = np.asarray(hit['sourceBarycentric'])
    spans = []
    for points in (original, current):
        inside = points[faces[first]].astype(float).mean(0)
        outside = bary@points[faces[second]].astype(float)
        spans.append({'innerSourceCentroid': inside.tolist(), 'pairedSourceWallPoint': outside.tolist(),
                      'fixedSourceCorrespondenceSeparationM': float(np.linalg.norm(outside-inside))})
    bp, bf = geometry(body); origin = (bp.min(0)+bp.max(0)).astype(float)*.5
    tree = BVHTree.FromPolygons([Vector(p-origin) for p in bp], bf.tolist(), all_triangles=True)
    ids = sorted(set([first, second]+report['mostCompressedFaceIds']+report['mostStretchedFaceIds']))
    witnesses = []
    for face in ids:
        point = current[faces[face]].astype(float).mean(0)
        q, n, body_face, distance = tree.find_nearest(Vector(point-origin))
        sign = 1 if np.dot(point-origin-np.asarray(q), np.asarray(n)) >= 0 else -1
        witnesses.append({'sourceFaceId': face, 'nativeVertexIds': faces[face].tolist(),
            'centroid': point.tolist(), 'tangentPrincipalStretches': stretch[face].tolist(),
            'areaRatio': float(area[face]), 'nearestFullReferenceTriangleId': int(body_face),
            'signedNearestFullReferenceCentroidGapM': sign*float(distance)})
    report.update(sourcePair=SOURCE_PAIR, pairFaceIds=[first, second],
        sourcePairBeforeAfter=spans, sourcePairSeparationRatio=spans[1]['fixedSourceCorrespondenceSeparationM']/spans[0]['fixedSourceCorrespondenceSeparationM'],
        boundedActualFaceWitnesses=witnesses,
        localContactLimit='Only listed saved triangle centroids measured; global contact remains failed in qualified50.')
    path = out/'tangent-and-pair.json'; path.write_text(json.dumps(report, indent=2)+'\n')
    return pin(path)


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 4
    variant, mode, output, original_receipt = args; assert variant in NATIVES and mode in ('cloth', 'wearer')
    out = Path(output).resolve(); assert out.is_relative_to(OUT) and not out.exists()
    qualified = json.loads(checked(QUALIFIED50).read_text())
    assert qualified['native'] == NATIVES['registered'] and qualified['protectedValidationPassed']
    assert qualified['broadRegistration']['constructionContactSamplesPassed'] is False
    original_report = None
    if variant == 'registered':
        original_path = Path(original_receipt).resolve(); assert original_path.is_relative_to(OUT)
        original_report = json.loads(original_path.read_text())
        assert original_report['native'] == NATIVES['original'] and original_report['mode'] == mode
        assert original_report['cameraSequence'] == {'frames': FRAME_COUNT, 'fps': FPS, 'focus': list(FOCUS), 'orthoScale': SCALE}
    else: assert original_receipt == '-'
    native = checked(NATIVES[variant]); bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
    scene = bpy.context.scene; rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert rig.animation_data is None or rig.animation_data.action is None
    hoodie = bpy.data.objects['RiderHoodie']; body = bpy.data.objects['RiderBody__FullAnatomyReference']
    visible = {'RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}
    if mode == 'wearer': visible.add(body.name)
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.hide_render = obj.name not in visible
            if obj.name in visible: obj.hide_viewport = False; obj.hide_set(False)
    if mode == 'wearer':
        material = bpy.data.materials.new('DIAGNOSTIC actual full anatomy neutral'); material.use_nodes = True
        bsdf = material.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Base Color'].default_value = (.32, .38, .42, 1)
        bsdf.inputs['Roughness'].default_value = .8
        for i in range(len(body.material_slots)): body.data.materials[i] = material
    assert all(layer.material_override is None for layer in scene.view_layers)
    points, faces = geometry(hoodie); out.mkdir(parents=True)
    np.savez_compressed(out/'actual-hoodie-geometry.npz', points=points, faces=faces)
    metrics = None
    if original_report:
        original = np.load(checked(original_report['actualGeometry']))
        assert np.array_equal(faces, original['faces']) and points.shape == original['points'].shape
        metrics = diagnose(original['points'], points, faces, body, out)
    aim = runpy.run_path(str(checked(RENDER_HELPER)))['aim']
    scene.render.engine = 'BLENDER_EEVEE'; scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.eevee.taa_render_samples = 16; scene.eevee.use_raytracing = False
    scene.render.resolution_x = scene.render.resolution_y = RESOLUTION; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    scene.render.use_compositing = False; scene.render.use_sequencer = False; scene.render.film_transparent = False
    scene.render.fps = FPS; scene.render.fps_base = 1; scene.view_settings.view_transform = 'AgX'
    scene.render.use_stamp = True; scene.render.use_stamp_note = True; scene.render.stamp_font_size = 12
    scene.render.stamp_note_text = ('DIAGNOSTIC | ORIGINAL47' if variant == 'original' else 'DIAGNOSTIC | FIT50 CONTACT FAIL')+' | STATIC REST TURNTABLE'
    for name in ('date', 'time', 'render_time', 'frame', 'frame_range', 'memory', 'hostname', 'camera', 'lens', 'scene', 'marker', 'filename', 'sequencer_strip'):
        attribute = 'use_stamp_'+name
        if hasattr(scene.render, attribute): setattr(scene.render, attribute, False)
    world = bpy.data.worlds.new('Matched diagnostic54 world'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55; scene.world = world
    for obj in scene.objects:
        if obj.type == 'LIGHT': obj.hide_render = True
    for name, location, power, size in [('Key', (2,-3,4), 650, 3), ('Fill', (-3,-2,2), 450, 3), ('Rim', (0,3,3), 700, 2)]:
        light = bpy.data.lights.new('Matched54 '+name, 'AREA'); light.energy = power; light.shape = 'DISK'; light.size = size
        obj = bpy.data.objects.new(light.name, light); scene.collection.objects.link(obj); obj.location = location; aim(obj, FOCUS)
    camera = bpy.data.objects.new('Matched54 camera', bpy.data.cameras.new('Matched54 camera'))
    scene.collection.objects.link(camera); scene.camera = camera; camera.data.type = 'ORTHO'; camera.data.ortho_scale = SCALE
    frames = out/'frames'; frames.mkdir(); start = time.monotonic(); records = []
    for index in range(FRAME_COUNT):
        angle = 2*math.pi*index/FRAME_COUNT
        camera.location = (3.2*math.sin(angle), -3.2*math.cos(angle), 1.37); aim(camera, FOCUS)
        scene.frame_set(index+1); bpy.context.view_layer.update()
        scene.render.filepath = str(frames/f'{index:04d}.png'); bpy.ops.render.render(write_still=True)
        records.append({'frame': index, 'cameraMatrix': [list(row) for row in camera.matrix_world]})
        if (index+1)%8 == 0: print('DIAGNOSTIC54', variant, index+1, FRAME_COUNT, time.monotonic()-start, flush=True)
    movie = out/(variant+'.mp4')
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(frames/'%04d.png'),
        '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', '-an', str(movie)], check=True)
    streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(movie)]))['streams']
    assert len(streams) == 1 and streams[0]['codec_type'] == 'video' and int(streams[0]['nb_read_frames']) == FRAME_COUNT
    assert streams[0]['avg_frame_rate'] == str(FPS)+'/1' and sha(native) == NATIVES[variant]['sha256']
    report = {'acceptedArt': False, 'diagnosticOnly': True, 'variant': variant, 'mode': mode,
        'native': NATIVES[variant], 'qualification50': QUALIFIED50, 'recipe': pin(__file__), 'tangentHelper': pin(HERE/'tangent.py'),
        'movie': pin(movie), 'actualGeometry': pin(out/'actual-hoodie-geometry.npz'), 'tangentMetrics': metrics,
        'cameraSequence': {'frames': FRAME_COUNT, 'fps': FPS, 'focus': list(FOCUS), 'orthoScale': SCALE},
        'cameraRecords': records, 'visibleMeshes': sorted(visible), 'audioStreams': 0,
        'elapsedRenderSeconds': time.monotonic()-start, 'renderSamples': 16, 'rayTracing': False,
        'limits': ['Selected hoodie and gloves only; this is not a completed rider or pose/motion acceptance.',
                   'Actual full reference is neutral opaque only in wearer mode; selected garment PBR is unchanged.',
                   'Static rest-camera rotation diagnoses shoulder/axilla shape; game/generic moving gates remain open.']}
    if original_report: assert records == original_report['cameraRecords']
    (out/'render.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'movie': report['movie'], 'diagnosticOnly': True}), flush=True)


if __name__ == '__main__': main()
