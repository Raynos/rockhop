"""Isolated common CPU Blender comparison, derived from Rockhop render_raw.py.

Source GLBs remain unchanged. Align imported roots, then uniformly display
normalize using evaluated visible geometry. Preserve native PBR or show gray.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

BASE_RENDERER = '/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/search-v1/render_raw.py'
BASE_SHA256 = '38da920203ac1f1b7e9cfb085eb6783702e5c4487c710a6022768fdd5658ddae'
Z_ROTATIONS = {'baseline': -90, 'pixal': 180, 'trellis': 0, 'hunyuan21': 0, 'hunyuan': 0}
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--engine', required=True, choices=Z_ROTATIONS)
ap.add_argument('--gray', action='store_true')
ap.add_argument('--x-rotation',type=float,default=0)
ap.add_argument('--yaws', default='0,45,90,135,180,270')
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source = Path(a.input).resolve(); out = Path(a.out).resolve()
yaws = [float(v) for v in a.yaws.split(',')]
if not yaws or any(not math.isfinite(v) for v in yaws): raise ValueError('Invalid yaws')
out.mkdir(parents=True, exist_ok=True)
if (out / 'manifest.json').exists(): raise RuntimeError('Frozen render exists; select a new output directory')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha = sha(source); started = time.perf_counter()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
scene = bpy.context.scene
for o in list(scene.objects):
    if o.type in {'LIGHT', 'CAMERA'}: bpy.data.objects.remove(o, do_unlink=True)
# Disable animation playback so the baseline shows imported rest/bind geometry.
# The comparison does not transfer a new pose, rig, or motion onto neural models.
armatures = []
for o in scene.objects:
    if o.type == 'ARMATURE':
        armatures.append(o.name)
        if o.animation_data:
            o.animation_data.action = None
            for track in o.animation_data.nla_tracks: track.mute = True
        for bone in o.pose.bones: bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
meshes = [o for o in scene.objects if o.type == 'MESH' and o.visible_get()]
excluded = [{'name': o.name, 'vertices': len(o.data.vertices)} for o in scene.objects if o.type == 'MESH' and not o.visible_get()]
if not meshes: raise RuntimeError('No visible meshes')
roots = [o for o in scene.objects if o.parent is None]
alignment = bpy.data.objects.new('Recorded display front alignment', None)
scene.collection.objects.link(alignment)
for o in roots:
    matrix = o.matrix_world.copy(); o.parent = alignment; o.matrix_world = matrix
alignment.rotation_euler.z = math.radians(Z_ROTATIONS[a.engine])
alignment.rotation_euler.x = math.radians(a.x_rotation)
bpy.context.view_layer.update()
def evaluated_points():
    points = []; triangles = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        evaluated = o.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
        points.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
        mesh.calc_loop_triangles(); triangles += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    return points, triangles
points, triangles = evaluated_points()
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
height = hi.z - lo.z
if height <= 0: raise RuntimeError('Invalid display height')
centre = (lo + hi) / 2; scale = 1.8 / height
normalizer = bpy.data.objects.new('Recorded uniform display normalization', None)
scene.collection.objects.link(normalizer)
alignment.parent = normalizer
normalizer.scale = (scale,) * 3
normalizer.location = (-centre.x * scale, -centre.y * scale, -lo.z * scale)
bpy.context.view_layer.update()
material_changes = []
if a.gray:
    gray = bpy.data.materials.new('Geometry diagnostic neutral gray'); gray.diffuse_color = (.42, .42, .42, 1)
    gray.use_nodes = True; bsdf = gray.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (.42, .42, .42, 1)
    bsdf.inputs['Roughness'].default_value = .65; bsdf.inputs['Metallic'].default_value = 0
    for o in meshes:
        material_changes.append({'mesh': o.name, 'replacedMaterials': [m.name if m else None for m in o.data.materials]})
        o.data.materials.clear(); o.data.materials.append(gray)
world = bpy.data.worlds.new('Common gray studio'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.16, .16, .16, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65; scene.world = world
target = Vector((0, 0, .9)); light_rows = []
for name, position, power, size in [('Key', (3, -4, 4), 600, 4), ('Fill', (-3, -2, 2.5), 350, 4), ('Rim', (1, 3, 3), 450, 3)]:
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.shape = 'DISK'; d.size = size
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = position
    o.rotation_euler = (target - o.location).to_track_quat('-Z', 'Y').to_euler()
    light_rows.append({'name': name, 'position': position, 'powerWatts': power, 'size': size})
camera_data = bpy.data.cameras.new('Matched yaw orthographic')
camera = bpy.data.objects.new('Matched yaw orthographic', camera_data)
scene.collection.objects.link(camera); scene.camera = camera
camera_data.type = 'ORTHO'; camera_data.ortho_scale = 2.15
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 12; scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'; scene.render.threads = 6
scene.render.resolution_x = 512; scene.render.resolution_y = 768; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
views = []
for i, yaw in enumerate(yaws):
    angle = math.radians(yaw)
    camera.location = target + Vector((4 * math.sin(angle), -4 * math.cos(angle), 0))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    path = out / f'{i:04d}.png'; scene.render.filepath = str(path)
    frame_start = time.perf_counter(); bpy.ops.render.render(write_still=True)
    views.append({'frame': i, 'yaw': yaw, 'file': path.name, 'sha256': sha(path), 'wallSeconds': round(time.perf_counter() - frame_start, 3), 'cameraMatrix': [list(row) for row in camera.matrix_world]})
assert sha(source) == source_sha, 'Source GLB changed during render'
manifest = {
    'status': 'ISOLATED STATIC COMPARISON; no gameplay or art acceptance', 'engine': a.engine,
    'input': str(source), 'inputSHA256': source_sha, 'inputSHA256After': sha(source),
    'rendererSHA256': sha(__file__), 'derivedFrom': {'path': BASE_RENDERER, 'sha256AtDerivation': BASE_SHA256},
    'blender': bpy.app.version_string, 'wallSeconds': round(time.perf_counter() - started, 3),
    'triangles': triangles, 'visibleMeshes': [o.name for o in meshes], 'excludedInvisibleMeshes': excluded,
    'alignment': {'commonFront': 'Blender -Y', 'zRotationDegrees': Z_ROTATIONS[a.engine], 'xRotationDegrees':a.x_rotation, 'rootObjects': [o.name for o in roots], 'matrix': [list(row) for row in alignment.matrix_local]},
    'animationPolicy': 'imported rest/bind pose; actions disabled, NLA muted, bone matrix_basis identity', 'armatures': armatures,
    'boundsAfterAlignmentBeforeNormalization': [list(lo), list(hi)], 'boundsMethod': 'evaluated visible meshes only',
    'uniformScale': scale, 'normalizationTranslation': list(normalizer.location), 'displayHeight': 1.8, 'orthoScale': 2.15,
    'lights': light_rows, 'world': {'rgb': [.16] * 3, 'strength': .65}, 'resolution': [512, 768],
    'samples': 12, 'backend': 'Cycles CPU', 'viewTransform': 'AgX', 'materialMode': 'neutral-gray' if a.gray else 'native-PBR', 'materialChanges': material_changes, 'views': views,
    'limits': ['Source GLB bytes are unchanged; normalization and alignment affect display only.', 'Native PBR mode makes no material edits; gray diagnostic temporarily replaces visible materials.', 'Baseline production bind/rest pose differs from reference A-pose; anatomy and pose are not equivalent.', 'Engine orientation defaults must be visually checked for each new export.', 'Static views do not verify rig quality, animation, gameplay or acceptance.', 'Elapsed time can include concurrent host work; this is not a performance benchmark.']
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
