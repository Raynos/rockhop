"""Immutable raw GLB inspection in Blender Cycles CPU, not an asset editor."""
import argparse
import datetime
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def geometry_pin(obj):
    positions = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get('co', positions)
    loops = np.empty(len(obj.data.loops), dtype=np.int32)
    obj.data.loops.foreach_get('vertex_index', loops)
    counts = np.asarray([len(p.vertices) for p in obj.data.polygons], dtype=np.int32)
    return {
        'name': obj.name, 'vertices': len(obj.data.vertices),
        'polygons': len(obj.data.polygons), 'loopCount': len(loops),
        'positionsSHA256': hashlib.sha256(positions.tobytes()).hexdigest(),
        'loopsSHA256': hashlib.sha256(loops.tobytes()).hexdigest(),
        'polygonCountsSHA256': hashlib.sha256(counts.tobytes()).hexdigest(),
        'matrixWorldBeforeViewer': [list(row) for row in obj.matrix_world],
        'modifiers': [m.type for m in obj.modifiers],
    }


def point_camera(camera, position, target):
    camera.location = Vector(position)
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()


args = argparse.ArgumentParser()
args.add_argument('--mode', choices=['probe', 'render'], required=True)
args.add_argument('--source', type=Path, required=True)
args.add_argument('--source-sha', required=True)
args.add_argument('--source-kind', choices=['native', 'finite-subset'], required=True)
args.add_argument('--out', type=Path, required=True)
args.add_argument('--orientation', type=Path)
args.add_argument('--seconds', type=float, default=1650)
a = args.parse_args(sys.argv[sys.argv.index('--') + 1:])
assert a.source.name == 'native-display.glb', 'No silent fallback to an older mesh'
assert a.source.is_file() and sha(a.source) == a.source_sha
a.out.mkdir(parents=True, exist_ok=False)
start = time.monotonic()
deadline = start + a.seconds
report = {
    'status': 'IN_PROGRESS_UNACCEPTED_RAW_STRUCTURAL_INSPECTION',
    'mode': a.mode, 'source': str(a.source), 'sourceSHA256': a.source_sha,
    'sourceKind': a.source_kind, 'finiteSubset': a.source_kind == 'finite-subset',
    'sourceQualification': 'Literal finite-face isolation of an invalid native generation; diagnostic surface only, not a native-output/art/rig pass' if a.source_kind == 'finite-subset' else 'Unaccepted raw generator output',
    'scriptSHA256': sha(__file__), 'device': 'CPU', 'threads': 2,
    'sourceEdits': False, 'assetExport': False,
    'rigMotion': 'UNMEASURED: camera orbit around the unrigged raw source only',
    'appearanceDecision': 'Parent judgment required; no pass assigned by builder',
    'views': [], 'frames': [],
}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source))
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == 'MESH']
assert meshes
assert not any(o.type == 'ARMATURE' for o in scene.objects), 'Expected an unrigged source'
report['blenderVersion'] = bpy.app.version_string
report['geometryBefore'] = [geometry_pin(o) for o in meshes]
source_world = [o.matrix_world.copy() for o in meshes]
view_matrix = np.eye(4)
if a.mode == 'render':
    assert a.orientation is not None
    cfg = json.loads(a.orientation.read_text())
    assert cfg['sourceSHA256'] == a.source_sha
    probe_report = Path(cfg['probeReport'])
    assert sha(probe_report) == cfg['probeReportSHA256']
    probe = json.loads(probe_report.read_text())
    assert probe['sourceSHA256'] == a.source_sha and probe['status'] == 'COMPLETE_UNACCEPTED_RAW_STRUCTURAL_INSPECTION'
    assert cfg['basisExplanation'] and cfg['frontEvidenceView'] in [v['label'] for v in probe['views']]
    view_matrix = np.asarray(cfg['viewerRotation4x4'], dtype=np.float64)
    assert view_matrix.shape == (4, 4)
    assert np.max(np.abs(view_matrix[3] - [0, 0, 0, 1])) < 1e-12
    assert np.max(np.abs(view_matrix[:3, 3])) < 1e-12, 'No scale/translation correction'
    rotation = view_matrix[:3, :3]
    assert np.max(np.abs(rotation.T @ rotation - np.eye(3))) < 1e-10
    assert abs(np.linalg.det(rotation) - 1) < 1e-10
    report['orientation'] = cfg
    report['orientationSHA256'] = sha(a.orientation)
    root = bpy.data.objects.new('Viewer rotation only, never exported', None)
    scene.collection.objects.link(root)
    imported_roots = [o for o in scene.objects if o != root and o.parent is None]
    for obj in imported_roots:
        obj.parent = root
        obj.matrix_parent_inverse = Matrix.Identity(4)
    root.matrix_world = Matrix(view_matrix.tolist())
    bpy.context.view_layer.update()
report['viewerRotation4x4'] = view_matrix.tolist()
world_points = np.concatenate([
    np.asarray([list(o.matrix_world @ v.co) for v in o.data.vertices], dtype=np.float64)
    for o in meshes
])
lower, upper = world_points.min(axis=0), world_points.max(axis=0)
center, extent = (lower + upper) / 2, upper - lower
report['blenderViewerAxes'] = {'up': '+Z', 'frontCamera': '-Y', 'sideCamera': '+X'}
report['worldBoundsM'] = {'min': lower.tolist(), 'max': upper.tolist(), 'extent': extent.tolist()}
report['importedObjectMatricesAfterViewer'] = {o.name: [list(row) for row in o.matrix_world] for o in meshes}
world = bpy.data.worlds.new('Fixed neutral studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.16, .16, .16, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65
scene.world = world
scale = float(np.linalg.norm(extent))
for name, direction, power in [('Key', (2, -3, 3), 650), ('Fill', (-3, -1, 2), 400), ('Rear', (1, 3, 2), 600)]:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power * (scale / 2) ** 2
    light.shape = 'DISK'
    light.size = scale * 1.3
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = Vector(center) + Vector(direction) * scale
    obj.rotation_euler = (Vector(center) - obj.location).to_track_quat('-Z', 'Y').to_euler()
gray = bpy.data.materials.new('Neutral gray geometric inspection')
gray.use_nodes = True
shader = gray.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.42, .42, .42, 1)
shader.inputs['Roughness'].default_value = .7
scene.view_layers[0].material_override = gray
camera_data = bpy.data.cameras.new('Orthographic matched full body')
camera = bpy.data.objects.new(camera_data.name, camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.clip_start = .001
camera_data.clip_end = max(100, scale * 20)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = False
scene.cycles.max_bounces = 2
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 1
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.render.film_transparent = False
report['renderSettings'] = {'engine': 'CYCLES', 'device': 'CPU', 'threads': 2, 'denoising': False, 'maxBounces': 2, 'materialOverride': 'gray .42 roughness .7', 'filmResolution': [960, 960], 'filmSamples': 8, 'filmFrames': 72, 'filmFPS': 12, 'stillResolution': [1200, 1200], 'stillSamples': 16, 'colorTransform': 'AgX'}


def render(label, position, target, ortho, pixels, samples, movie=False):
    assert time.monotonic() < deadline - 20, 'Bounded CPU batch deadline reached'
    camera_data.ortho_scale = ortho
    point_camera(camera, position, target)
    scene.render.resolution_x = scene.render.resolution_y = pixels
    scene.cycles.samples = samples
    scene.cycles.seed = 0
    destination = a.out / (('frames/' if movie else '') + label + '.png')
    destination.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(destination)
    before = time.monotonic()
    bpy.ops.render.render(write_still=True)
    item = {'label': label, 'path': str(destination), 'sha256': sha(destination), 'cameraPosition': list(position), 'cameraTarget': list(target), 'orthoScale': ortho, 'pixels': pixels, 'samples': samples, 'seconds': time.monotonic() - before}
    report['frames' if movie else 'views'].append(item)
    write(a.out / 'report.json', report)


try:
    if a.mode == 'probe':
        distance = scale * 3
        for label, axis in [('positive-X', (1, 0, 0)), ('negative-X', (-1, 0, 0)), ('positive-Y', (0, 1, 0)), ('negative-Y', (0, -1, 0)), ('positive-Z', (0, 0, 1)), ('negative-Z', (0, 0, -1))]:
            render(label, center + np.asarray(axis) * distance, center, scale * 1.1, 640, 8)
    else:
        full_scale = float(max(np.hypot(extent[0], extent[1]), extent[2]) * 1.12)
        distance = scale * 3
        for label, angle in [('front', 0), ('front-left', 45), ('left', 90), ('rear-left', 135), ('rear', 180), ('rear-right', 225), ('right', 270), ('front-right', 315)]:
            yaw = math.radians(angle)
            direction = np.asarray([math.sin(yaw), -math.cos(yaw), 0.0])
            render(label, center + direction * distance, center, full_scale, 1200, 16)
        # Whole upper body remains visible; do not selectively hide the chest or sleeve roots.
        crop_target = center.copy()
        crop_target[2] = lower[2] + .72 * extent[2]
        crop_scale = float(max(extent[0] * .74, extent[2] * .65))
        for label, angle in [('upper-front', 0), ('upper-rear', 180), ('upper-three-quarter', 45)]:
            yaw = math.radians(angle)
            direction = np.asarray([math.sin(yaw), -math.cos(yaw), 0.0])
            render(label, crop_target + direction * distance, crop_target, crop_scale, 1200, 16)
        for frame in range(72):
            yaw = 2 * math.pi * frame / 72
            direction = np.asarray([math.sin(yaw), -math.cos(yaw), 0.0])
            render(f'{frame:04d}', center + direction * distance, center, full_scale, 960, 8, movie=True)
    report['status'] = 'COMPLETE_UNACCEPTED_RAW_STRUCTURAL_INSPECTION'
except BaseException as error:
    report['status'] = 'INCOMPLETE_UNACCEPTED_RAW_STRUCTURAL_INSPECTION'
    report['failure'] = {'type': type(error).__name__, 'message': str(error)}
    raise
finally:
    after = [geometry_pin(o) for o in meshes]
    for before, current in zip(report['geometryBefore'], after):
        for key in ['vertices', 'polygons', 'loopCount', 'positionsSHA256', 'loopsSHA256', 'polygonCountsSHA256']:
            assert before[key] == current[key], 'Viewer modified mesh data'
    for obj, original_world in zip(meshes, source_world):
        expected = view_matrix @ np.asarray(original_world)
        assert np.max(np.abs(expected - np.asarray(obj.matrix_world))) < 1e-5
    report['geometryAfter'] = after
    report['sourceSHA256After'] = sha(a.source)
    assert report['sourceSHA256After'] == a.source_sha
    report['elapsedSeconds'] = time.monotonic() - start
    report['finishedUTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write(a.out / 'report.json', report)
