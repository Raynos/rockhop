"""Sample a declared SAME native candidate in memory; preserve source/rest/binds.

Run Blender background threads2 --python this-file -- --source ... --manifest ...
--battery ... --out NEW_DIR [--stride 12]. No saves, renders, or source mutation.
Manifest: sourceSHA256, rigName, pairs:[{region,full,four}]. Every pair requires
identical rest geometry/topology and explicit semantic51 weight coverage.
"""
import argparse, gzip, hashlib, json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
p = argparse.ArgumentParser(description=__doc__)
for key in ['source', 'manifest', 'battery', 'out']:
    p.add_argument('--' + key, required=True)
p.add_argument('--stride', type=int, default=12)
p.add_argument('--export-idle', help='Optional new FOUR GLB with same-candidate 2s idle; no native save')
p.add_argument('--indices', help='Explicit comma-separated sample identities; avoids whole-battery execution during first intake')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, manifest_path, battery_path, out = [Path(getattr(a, k)).resolve() for k in ['source', 'manifest', 'battery', 'out']]
assert not out.exists() and a.stride > 0
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
manifest, battery = json.loads(manifest_path.read_text()), json.loads(battery_path.read_text())
assert sha(source) == manifest['sourceSHA256']
assert battery['schema'] == 'rockhop-semantic-motion-v1'
pins = {str(x): sha(x) for x in [source, manifest_path, battery_path]}
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects[manifest['rigName']]
names = [b.name for b in rig.data.bones]
assert len(names) == 51 and len(set(names)) == 51
rest = {b.name: np.array(b.matrix_local) for b in rig.data.bones}
rig.animation_data_clear()
for b in rig.pose.bones:
    for c in b.constraints:
        c.mute = True
declared_names = {item[k] for item in manifest['pairs'] for k in ['full', 'four']}
for o in [bpy.data.objects[name] for name in declared_names]:
    if o.type == 'MESH':
        o.animation_data_clear()
        if o.data.shape_keys:
            o.data.shape_keys.animation_data_clear()
            for key in o.data.shape_keys.key_blocks:
                key.value = 0

def read(o):
    assert o.type == 'MESH' and not o.data.shape_keys, 'Declare basis-only mesh; shape-key candidates require explicit controller handling'
    mods = [m for m in o.modifiers if m.show_viewport]
    assert len(mods) == 1 and mods[0].type == 'ARMATURE' and mods[0].object == rig
    assert not mods[0].use_deform_preserve_volume, 'Linear skin comparison cannot silently approximate DQS'
    o.data.calc_loop_triangles()
    xyz = np.array([v.co[:] for v in o.data.vertices])
    faces = np.array([t.vertices[:] for t in o.data.loop_triangles])
    weights = np.zeros((len(xyz), 51))
    auxiliary = {}
    for v in o.data.vertices:
        for g in v.groups:
            name = o.vertex_groups[g.group].name
            if g.weight > 0:
                if name in names and rig.data.bones[name].use_deform:
                    weights[v.index, names.index(name)] = g.weight
                else:
                    auxiliary[name] = auxiliary.get(name, 0) + 1
    assert np.all(weights.sum(1) > 0)
    sums = weights.sum(1)
    raw_weights = weights.copy()
    tolerance = manifest.get('normalizedWeightTolerance')
    if tolerance is not None:
        assert float(np.max(np.abs(sums - 1))) <= tolerance, (o.name, 'Declared normalized native contract failed', float(sums.min()), float(sums.max()))
    weights /= sums[:, None]
    return {'object': o, 'xyz': xyz, 'faces': faces, 'weights': weights, 'rawWeights': raw_weights, 'weightSums': sums, 'auxiliaryMembershipCounts': auxiliary, 'objectWorld': np.array(o.matrix_world), 'cornerNormals': np.array([n.vector[:] for n in o.data.corner_normals]), 'cornerVertices': np.array([x.vertex_index for x in o.data.loops])}
parts = []
for item in manifest['pairs']:
    full, four = read(bpy.data.objects[item['full']]), read(bpy.data.objects[item['four']])
    assert np.array_equal(full['xyz'], four['xyz']) and np.array_equal(full['faces'], four['faces']), item['region']
    assert np.max((four['weights'] > 0).sum(1)) <= 4
    assert np.array_equal(full['objectWorld'], four['objectWorld'])
    parts.append((item, full, four))
assert any(item['region'] == 'body' for item, _, _ in parts)
assert any(item['region'] == 'head' for item, _, _ in parts), 'Head must be measured separately; no omitted target pass'

out.mkdir(parents=True)
rig.hide_viewport = False
for _, full, four in parts:
    for field in [full, four]:
        field['object'].hide_viewport = False
        field['object'].hide_set(False)
def save_json(name, data):
    path = out / name
    if name.endswith('.gz'):
        with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as f:
            f.write(json.dumps(data, separators=(',', ':'), allow_nan=False).encode())
    else:
        path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    return {'path': name, 'sha256': sha(path), 'bytes': path.stat().st_size}

def apply(command):
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'
        b.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    blend = command.get('armDirectionBlend', 0)
    for side, direction in (command.get('armDirections') or {}).items():
        for role in ['upperArm', 'forearm']:
            b = rig.pose.bones[f'{role}.{side}']
            current = b.matrix.to_quaternion()
            axis = current @ Vector((0, 1, 0))
            desired = axis.rotation_difference(Vector(direction).normalized()) @ current
            target = current.slerp(desired, blend)
            parent_rest = b.bone.parent.matrix_local if b.bone.parent else Matrix.Identity(4)
            local_rest = parent_rest.inverted() @ b.bone.matrix_local
            parent_pose = b.parent.matrix if b.parent else Matrix.Identity(4)
            local_target = parent_pose.to_quaternion().inverted() @ target
            b.rotation_quaternion = local_rest.to_quaternion().inverted() @ local_target
            bpy.context.view_layer.update()
    for r in command['rotations']:
        b = rig.pose.bones[r['bone']]
        rest_q = b.bone.matrix_local.to_quaternion()
        delta = rest_q.inverted() @ Quaternion(Vector(r['axisNative']), math.radians(r['degrees'])) @ rest_q
        b.rotation_quaternion = b.rotation_quaternion @ delta
    rig.pose.bones['pelvis'].location = rig.data.bones['pelvis'].matrix_local.to_3x3().inverted() @ Vector(command['rootTranslationNativeM'])
    bpy.context.view_layer.update()

def evaluated(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = e.to_mesh()
    mesh.calc_loop_triangles()
    rows = np.array([list(e.matrix_world @ v.co) for v in mesh.vertices])
    normals = np.array([list(e.matrix_world.to_3x3().inverted().transposed() @ n.vector) for n in mesh.corner_normals])
    lengths = np.linalg.norm(normals, axis=1)
    nonzero = lengths > 0
    normals[nonzero] /= lengths[nonzero, None]
    faces = np.array([t.vertices[:] for t in mesh.loop_triangles])
    e.to_mesh_clear()
    return rows, normals, faces

records, snapshot_pins = [], []
selected = set(range(0, len(battery['frames']), a.stride))
for case in battery['cases']:
    rows = battery['frames'][case['start']:case['end'] + 1]
    for phase in ['forward', 'hold', 'reverse']:
        indices = [r['index'] for r in rows if r['phase'] == phase]
        if indices:
            selected.update([indices[0], indices[len(indices) // 2], indices[-1]])
if a.indices:
    selected = {int(x) for x in a.indices.split(',')}
    assert selected and all(0 <= x < len(battery['frames']) for x in selected)
rest_report = {'jointOrder': names, 'rigWorldRows': np.array(rig.matrix_world).tolist(), 'restBoneRows': {n: m.tolist() for n, m in rest.items()}, 'parts': {}}
for item, full, four in parts:
    rest_report['parts'][item['region']] = {k: full[k].tolist() for k in ['xyz', 'faces', 'objectWorld', 'cornerNormals', 'cornerVertices']}
    rest_report['parts'][item['region']].update({'fullWeights': full['weights'].tolist(), 'fourWeights': four['weights'].tolist(), 'fullRawWeights': full['rawWeights'].tolist(), 'fourRawWeights': four['rawWeights'].tolist(), 'fullRawSumRange': [float(full['weightSums'].min()), float(full['weightSums'].max())], 'fourRawSumRange': [float(four['weightSums'].min()), float(four['weightSums'].max())], 'auxiliaryMembershipCounts': full['auxiliaryMembershipCounts']})
rest_pin = save_json('rest.json.gz', rest_report)
for index in sorted(selected):
    frame = battery['frames'][index]
    apply(frame['command'])
    skin = np.array([rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted() for n in names])
    row = {'index': index, 'case': frame['case'], 'phase': frame['phase'], 'timeS': frame['timeS'], 'skinNativeRows': skin.tolist(), 'boneWorldNativeRows': {n: np.array(rig.matrix_world @ rig.pose.bones[n].matrix).tolist() for n in names}, 'poseBasisBlender': {n: {'location': list(rig.pose.bones[n].location), 'quaternionWXYZ': list(rig.pose.bones[n].rotation_quaternion), 'scale': list(rig.pose.bones[n].scale)} for n in names}, 'parts': {}}
    compact = {'index': index, 'case': frame['case'], 'phase': frame['phase'], 'parts': {}}
    for item, full, four in parts:
        xyzs = []
        for kind, field in [('full', full), ('four', four)]:
            xyz, normal, faces = evaluated(field['object'])
            assert len(xyz) == len(field['xyz'])
            topology_exact = np.array_equal(faces, field['faces'])
            local_to_rig = np.linalg.inv(np.array(rig.matrix_world)) @ field['objectWorld']
            homogeneous = np.column_stack([field['xyz'], np.ones(len(field['xyz']))]) @ local_to_rig.T
            predicted = np.einsum('vj,jab,vb->va', field['weights'], skin, homogeneous) @ np.array(rig.matrix_world).T
            residual = np.linalg.norm(xyz - predicted[:, :3], axis=1)
            raw_prediction = np.einsum('vj,jab,vb->va', field['rawWeights'], skin, homogeneous) @ np.array(rig.matrix_world).T
            raw_residual = np.linalg.norm(xyz - raw_prediction[:, :3], axis=1)
            assert np.isfinite(xyz).all() and np.isfinite(normal).all()
            xyzs.append(xyz)
            row['parts'].setdefault(item['region'], {})[kind] = {'xyzWorld': xyz.tolist(), 'normalWorldCorners': normal.tolist(), 'faces': faces.tolist()}
            compact['parts'].setdefault(item['region'], {})[kind] = {'nativeNormalizedManualMaxM': float(residual.max()), 'nativeRawManualMaxM': float(raw_residual.max()), 'rawSumMin': float(field['weightSums'].min()), 'rawSumMax': float(field['weightSums'].max()), 'worstVertex': int(residual.argmax()), 'topologyExact': topology_exact, 'finiteNormals': True, 'zeroNormalCornerIDs': np.flatnonzero(np.linalg.norm(normal, axis=1) == 0).tolist()}
        loss = np.linalg.norm(xyzs[0] - xyzs[1], axis=1)
        compact['parts'][item['region']]['fullFourMaxM'] = float(loss.max())
    snapshot_pins.append(save_json(f'sample-{index:04d}.json.gz', row))
    records.append(compact)
    print('SAMPLED', index, frame['case'], flush=True)
idle_export = None
if a.export_idle:
    idle_path = Path(a.export_idle).resolve()
    assert not idle_path.exists()
    idle_case = next(case for case in battery['cases'] if case['name'] == 'idle')
    idle_rows = [row for row in battery['frames'][idle_case['start']:idle_case['end'] + 1] if row['phase'] == 'forward']
    assert abs((len(idle_rows) - 1) / battery['sampling']['hz'] - 2) < 1e-9
    scene = bpy.data.scenes.new('Unaccepted same51 UniMate input only')
    for obj in [rig.parent, rig] + [four['object'] for _, _, four in parts]:
        if obj and obj.name not in scene.objects:
            scene.collection.objects.link(obj)
    bpy.context.window.scene = scene
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 0, 60
    for i in range(61):
        position = i / 30 * battery['sampling']['hz']
        low = min(int(position), len(idle_rows) - 1)
        high = min(low + 1, len(idle_rows) - 1)
        t = position - low
        first, second = idle_rows[low]['command'], idle_rows[high]['command']
        command = {'rotations': [{**r, 'degrees': (1-t)*r['degrees']+t*second['rotations'][j]['degrees']} for j, r in enumerate(first['rotations'])],
                   'rootTranslationNativeM': [(1-t)*x+t*second['rootTranslationNativeM'][j] for j, x in enumerate(first['rootTranslationNativeM'])], 'armDirections': None}
        scene.frame_set(i)
        apply(command)
        for b in rig.pose.bones:
            for field in ['location', 'rotation_quaternion', 'scale']:
                b.keyframe_insert(data_path=field, frame=i, group=b.name)
    rig.animation_data.action.name = 'Unaccepted same51 semantic idle 2s'
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    for _, _, four in parts:
        four['object'].select_set(True)
    bpy.context.view_layer.objects.active = rig
    idle_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(idle_path), export_format='GLB', use_selection=True,
                              export_attributes=True, export_animations=True, export_animation_mode='ACTIVE_ACTIONS',
                              export_frame_range=True, export_force_sampling=True, export_frame_step=1,
                              export_cameras=False, export_lights=False, export_skins=True)
    idle_export = {'path': str(idle_path), 'sha256': sha(idle_path), 'bytes': idle_path.stat().st_size,
                   'batteryFrameIDs': [row['index'] for row in idle_rows], 'durationS': 2, 'exportFPS': 30, 'bakedSamples': 61, 'upsampling': 'Linear interpolation of generator12Hz idle commands into a separate transient UniMate-only input scene; primary diagnostic battery unchanged.',
                   'jointOrder': names, 'status': 'UNACCEPTED_SAME_CANDIDATE_FOUR_IDLE_INPUT_EXPORT',
                   'limits': ['Generated FK idle, no natural motion/GPU/actual engine/film acceptance. Exact exported animation parity remains a separate check.']}
assert pins == {path: sha(path) for path in pins}
assert all(np.array_equal(rest[n], np.array(rig.data.bones[n].matrix_local)) for n in names)
save_json('report.json', {'status': 'UNACCEPTED_NATIVE_SEMANTIC_BATTERY_SAMPLED', 'sourcePins': pins, 'recipeSHA256': sha(__file__), 'blender': bpy.app.version_string, 'rest': rest_pin, 'samples': snapshot_pins, 'records': records, 'idleExport': idle_export, 'originalRestBindsUnchanged': True, 'weightHandling': 'Raw membership fields and sums retained. Raw and explicitly normalized LBS are separate hypotheses compared to actual evaluated native output; neither silently replaces the native reference.', 'limits': ['In-memory basis-only FK diagnostics; source file was not saved.', 'Native normal corners are measured outputs, not GLB/GPU parity.', 'No contact, coverage, natural gait, bike-support, art or device pass follows from skin parity.', 'Only declared selected sample identities measured; intervening states remain unmeasured.']})
print('NATIVE_READY', len(records), flush=True)
