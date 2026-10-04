"""ONE matched baseline/candidate proof of frozen failed neck27, CPU only.

Exact archived sample IDs, no controller/interpolation/field retry. Actual47
is explicitly the same native reconstruction measured in99, not an exact
game-field certificate. Source UV/PBR and evaluated native normals retained.
"""
import hashlib
import json
import math
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

root = Path(__file__).resolve().parents[6]
owned = Path(__file__).resolve().parent
ev = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = ev / 'neck-interface99/played'
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'render.json').exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze = json.loads((ev / 'neck-interface98/triangulation.json').read_text())
native = root / freeze['native']
assert sha(native) == freeze['nativeSHA256']
field_path = native.parent / 'triangulated-neck-fields.npz'
assert sha(field_path) == freeze['fieldsSHA256']
f = np.load(field_path)
pose_path = ev / 'neck-interface99/pose-witnesses.npz'
motion_path = ev / 'neck-interface99/motion.json'
motion = json.loads(motion_path.read_text())
assert sha(pose_path) == motion['archiveSHA256']
pose = np.load(pose_path)
names = f['boneNames'].tolist()
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
n = np.load(qa / 'body52/native-fields.npz')
identity_path = ev / 'neck-interface99/actual47-identity.json'
pins = {str(p.relative_to(root)): sha(p) for p in [native, field_path, pose_path, motion_path, identity_path,
    qa / 'body52/native-fields.npz', qa / 'neck62/FINDING.md']}
sample_rows = []
for domain, ids in [('native', list(range(0, 529, 4))), ('actual47', list(range(4, 704, 4)) + [703])]:
    for source_id in ids:
        i = int(np.flatnonzero((pose['domains'] == domain) & (pose['sourceIndices'] == source_id))[0])
        record = motion['frames'][i]
        sample_rows.append({'domain': domain, 'sourceIndex': source_id, 'archiveRow': i,
            'sourceTimeS': record['sourceTimeS'], 'nativeFourLocalContact': record['variants']['four']['localNativeCollision']})
assert len(sample_rows) == 309
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
source_scene = bpy.context.scene
rig = bpy.data.objects['Independent anatomical foundation rig']
rest_bones = np.array([np.array(rig.data.bones[name].matrix_local) for name in names])
sources = {'oldBody': bpy.data.objects['Canonical body with hidden head interface'],
    'oldHead': bpy.data.objects['Protected textured head above hidden neck interface'],
    'newBody': bpy.data.objects['Bounded neck27 triangulated body four, unaccepted'],
    'newHead': bpy.data.objects['Bounded neck27 triangulated head four, unaccepted'],
    'cheek': bpy.data.objects['Protected coherent cheek patch'], 'boxers': bpy.data.objects['Opaque boxer fitting garment']}
source_matrices = {key: np.array(obj.matrix_world) for key, obj in sources.items()}
pose_before = {pb.name: {'location': pb.location[:], 'quaternion': pb.rotation_quaternion[:],
    'euler': pb.rotation_euler[:], 'axis': pb.rotation_axis_angle[:], 'scale': pb.scale[:], 'mode': pb.rotation_mode} for pb in rig.pose.bones}
hide_before = {obj.name: obj.hide_get() for obj in [rig] + list(sources.values())}
for obj in [rig] + list(sources.values()): obj.hide_set(False)
bpy.context.view_layer.update()
parent_order = sorted(names, key=lambda name: len(rig.data.bones[name].parent_recursive))
lookup = {name: i for i, name in enumerate(names)}
def set_pose(S):
    desired = S @ rest_bones
    for name in parent_order:
        bone = rig.data.bones[name]; parent = bone.parent
        kw = {} if parent is None else {'parent_matrix': Matrix(desired[lookup[parent.name]].tolist()), 'parent_matrix_local': parent.matrix_local}
        rig.pose.bones[name].matrix_basis = bone.convert_local_to_pose(Matrix(desired[lookup[name]].tolist()), bone.matrix_local, invert=True, **kw)

rest = {}; sparse = {}
for key, obj in sources.items():
    xyz = np.array([v.co[:] for v in obj.data.vertices])
    rest[key] = np.column_stack([xyz, np.ones(len(xyz))])
    w = np.zeros((len(xyz), 51), dtype=float)
    for v in obj.data.vertices:
        for g in v.groups:
            name = obj.vertex_groups[g.group].name
            if name in names: w[v.index, names.index(name)] = g.weight
    w /= w.sum(axis=1)[:, None]
    sparse[key] = [(np.flatnonzero(w[:, j] > 0), w[w[:, j] > 0, j]) for j in range(51)]
def points(key, S):
    p = np.zeros_like(rest[key])
    for j, (ids, weight) in enumerate(sparse[key]):
        if len(ids): p[ids] += (rest[key][ids] @ S[j].T) * weight[:, None]
    return (p @ source_matrices[key].T)[:, :3]

# Fixed bounds derive from every displayed field, both inputs and three views.
maximum_horizontal = 0.; minimum_z = math.inf; maximum_z = -math.inf
for row in sample_rows:
    S = pose['rigLocalSkinMatrices'][row['archiveRow']]
    pelvis = (pose['rigWorldRows'] @ S[0] @ rest_bones[0])[:3, 3]
    for key in ['oldBody', 'oldHead', 'newBody', 'newHead']:
        p = points(key, S) - pelvis
        maximum_horizontal = max(maximum_horizontal, float(np.abs(p[:, :2]).max()))
        minimum_z = min(minimum_z, float(p[:, 2].min())); maximum_z = max(maximum_z, float(p[:, 2].max()))
cell_width = 2 * maximum_horizontal + .24
height = maximum_z - minimum_z
row_pitch = height + .24
lower = -minimum_z + .12
upper = lower + row_pitch
display_height = 2 * height + .48
ortho = max(3 * cell_width + .10, display_height * 1.5)
scene = bpy.data.scenes.new('Frozen failed neck99 proof CPU only')
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 4
scene.cycles.use_denoising = True; scene.cycles.max_bounces = 3
scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
scene.render.resolution_x = 1920; scene.render.resolution_y = 1280; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('Neck99 neutral world'); world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.075, .075, .075, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .65; scene.world = world
target = Vector((.65, 0, display_height / 2))
data = bpy.data.cameras.new('Matched frozen neck99 orthographic'); data.type = 'ORTHO'; data.ortho_scale = ortho
camera = bpy.data.objects.new(data.name, data); scene.collection.objects.link(camera)
camera.location = (10, 0, display_height / 2); camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler(); scene.camera = camera
panels = []
for row, label in enumerate(['baseline', 'candidate']):
    for col, yaw in enumerate([0, 90, 180]):
        theta = math.radians(yaw)
        R = np.array([[math.cos(theta), -math.sin(theta), 0], [math.sin(theta), math.cos(theta), 0], [0, 0, 1.]])
        offset = np.array([.65, (col - 1) * cell_width, upper if row == 0 else lower])
        collection = bpy.data.collections.new(f'{label} view{col} matched light receivers'); scene.collection.children.link(collection)
        copies = {}
        for role in ['Body', 'Head', 'cheek', 'boxers']:
            key = ('old' if label == 'baseline' else 'new') + role if role in ['Body', 'Head'] else role
            obj = bpy.data.objects.new(f'{label} view{col} posed {role}', bpy.data.meshes.new('empty posed copy'))
            collection.objects.link(obj); copies[key] = obj
        # Receiver links give each panel the identical local three-light rig.
        for name, position, energy in [('Key', (4, -4, 6), 1100), ('Fill', (-3, 4, 5), 1000), ('Top', (0, 0, 7), 800)]:
            light = bpy.data.lights.new(f'{label}{col} {name}', 'AREA'); light.energy = energy; light.size = 5
            lamp = bpy.data.objects.new(light.name, light); scene.collection.objects.link(lamp)
            lamp.location = offset + position
            lamp.rotation_euler = (Vector(offset + np.array([0, 0, .6])) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
            lamp.light_linking.receiver_collection = collection
            lamp.light_linking.blocker_collection = collection
        panels.append({'label': label, 'row': row, 'column': col, 'yaw': yaw, 'rotation': R, 'offset': offset, 'copies': copies})
source_signature = {key: {'positions': hashlib.sha256(rest[key].tobytes()).hexdigest(),
    'UV': {u.name: hashlib.sha256(np.array([x.uv[:] for x in u.data], dtype=np.float32).tobytes()).hexdigest() for u in obj.data.uv_layers},
    'materials': [m.name if m else None for m in obj.data.materials]} for key, obj in sources.items()}
frames_dir = out / 'frames'; frames_dir.mkdir(exist_ok=True)
frames = []; maximum_parity = 0.; started = time.monotonic()
for number, row in enumerate(sample_rows):
    bpy.context.window.scene = source_scene
    S = pose['rigLocalSkinMatrices'][row['archiveRow']]
    set_pose(S); bpy.context.view_layer.update()
    pelvis = (pose['rigWorldRows'] @ S[0] @ rest_bones[0])[:3, 3]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_meshes = {}; parity = {}
    for key, original in sources.items():
        evaluated = original.evaluated_get(depsgraph); m = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        xyz = np.array([evaluated.matrix_world @ v.co for v in m.vertices])
        gap = float(np.linalg.norm(xyz - points(key, S), axis=1).max()); parity[key] = gap
        assert gap < 4e-6, (row['domain'], row['sourceIndex'], key, gap)
        maximum_parity = max(maximum_parity, gap)
        evaluated_meshes[key] = m.copy(); evaluated.to_mesh_clear()
    frame = {'number': number, **row, 'nativeEvaluationVsAuditedFieldParityM': parity, 'views': []}
    bpy.context.window.scene = scene
    for panel in panels:
        transform = np.eye(4); transform[:3, :3] = panel['rotation']; transform[:3, 3] = panel['offset'] - panel['rotation'] @ pelvis
        focus_points = []
        for key, obj in panel['copies'].items():
            old_mesh = obj.data; obj.data = evaluated_meshes[key].copy()
            obj.data.transform(Matrix((transform @ source_matrices[key]).tolist())); obj.data.update()
            if old_mesh.users == 0: bpy.data.meshes.remove(old_mesh)
            if key.endswith('Head'): focus_points.append(np.array([v.co[:] for v in obj.data.vertices]))
            elif key.endswith('Body'):
                mask = (rest[key][:, 2] >= 1.25) & (np.abs(rest[key][:, 1]) <= .30)
                focus_points.append(np.array([obj.data.vertices[int(i)].co[:] for i in np.flatnonzero(mask)]))
        # Crop references only; every actor mesh is rendered intact, opaque.
        context = np.vstack(focus_points); center = context.mean(axis=0)
        projected = world_to_camera_view(scene, camera, Vector(center))
        cx, cy = projected.x * 1920, (1 - projected.y) * 1280
        width, crop_height = 420, 390
        left, top = int(round(cx - width / 2)), int(round(cy - crop_height / 2))
        left = max(panel['column'] * 640, min((panel['column'] + 1) * 640 - width, left))
        top = max(panel['row'] * 640, min((panel['row'] + 1) * 640 - crop_height, top))
        frame['views'].append({'label': panel['label'], 'row': panel['row'], 'column': panel['column'], 'yaw': panel['yaw'],
            'displayFromSourceRows': transform.tolist(), 'neckContextCropXYWH': [left, top, width, crop_height]})
    bpy.context.view_layer.update()
    scene.render.filepath = str(frames_dir / f'{number:04d}.png'); bpy.ops.render.render(write_still=True)
    frame['PNG_SHA256'] = sha(scene.render.filepath); frames.append(frame)
    for m in evaluated_meshes.values():
        if m.users == 0: bpy.data.meshes.remove(m)
    (out / 'progress.json').write_text(json.dumps({'completed': len(frames), 'target': len(sample_rows), 'lastSource': [row['domain'], row['sourceIndex']], 'elapsedS': time.monotonic() - started}, indent=2) + '\n')
    if number % 8 == 0: print('NECK_PROOF_FRAME', number, row['domain'], row['sourceIndex'], round(time.monotonic() - started, 1), flush=True)
    assert time.monotonic() - started < 7200, 'Bounded own CPU proof cap'
bpy.context.window.scene = source_scene
for name, state in pose_before.items():
    pb = rig.pose.bones[name]; pb.rotation_mode = state['mode']; pb.location = state['location']; pb.rotation_quaternion = state['quaternion']
    pb.rotation_euler = state['euler']; pb.rotation_axis_angle = state['axis']; pb.scale = state['scale']
for name, hidden in hide_before.items(): bpy.data.objects[name].hide_set(hidden)
bpy.context.view_layer.update()
assert pins == {p: sha(root / p) for p in pins}
after_signature = {key: {'positions': hashlib.sha256(np.column_stack([np.array([v.co[:] for v in obj.data.vertices]), np.ones(len(obj.data.vertices))]).tobytes()).hexdigest(),
    'UV': {u.name: hashlib.sha256(np.array([x.uv[:] for x in u.data], dtype=np.float32).tobytes()).hexdigest() for u in obj.data.uv_layers},
    'materials': [m.name if m else None for m in obj.data.materials]} for key, obj in sources.items()}
assert source_signature == after_signature
report = {'status': 'UNACCEPTED_ONE_FROZEN_FAILED_NECK_PROOF_RENDERED', 'pins': pins, 'recipeSHA256': sha(__file__),
    'frames': frames, 'sampledSources': len(sample_rows), 'elapsedS': time.monotonic() - started,
    'maximumNativeRenderVsAuditedFieldParityM': maximum_parity, 'sourceGeometryUVMaterialsAndFilePinsExact': True,
    'settings': {'resolution': [1920, 1280], 'engine': 'CYCLES', 'device': 'CPU', 'samples': 4, 'threads': 2,
        'orthographicWidthM': ortho, 'cameraWorldRows': np.array(camera.matrix_world).tolist(),
        'rows': ['Original baseline FOUR', 'Frozen failed neck27 FOUR'], 'views': ['front', 'left side', 'rear'],
        'sameLocalThreeLightsPerLinkedPanel': True, 'normalPolicy': 'Actual native evaluated Armature mesh/corner normals; rigid presentation transforms only; original UV/PBR/smooth fields retained. No normal camouflage.'},
    'limits': ['Only sampled existing streams: native every4th48Hz identity and actual47every4th120Hz identity plus703; no interpolation/controller/new pose trace.',
        'Actual47 native reconstruction retains the measured up-to3.36micrometre body identity bound failure. This proof cannot waive it.',
        'Known auxiliary native-group omission remains in frozen98; restoration follows this checkpoint, never alters current inputs.',
        'Local intersections/area compression remain failed evidence. No visible/art acceptance inferred from counts or technical playback.',
        'No source save, weights/geometry/rig retune, clothing cover, new worker/model/GPU job, publication or promotion. All M0-M5 open.']}
(out / 'render.json').write_text(json.dumps(report, indent=2) + '\n')
print('NECK_ONE_PROOF_RENDER_READY', len(frames), report['elapsedS'], flush=True)
