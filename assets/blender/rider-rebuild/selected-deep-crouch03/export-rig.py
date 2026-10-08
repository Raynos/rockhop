"""Export the one pinned deep217 action; no dense mesh import or target export.

Parent CPU2 lease only: blender -b -t 2 --python-exit-code 1 --python
export-rig.py -- EXPORT_CONFIG FRESH_OUT
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ACTION = 'UnacceptedSelectedDeepFixedSoleCrouchRise217'
HISTORICAL = {'path': 'assets/blender/rider-rebuild/selected-garage-actions01/author.py',
              'sha256': '98198da80f1d5b83c5dcf8929c65346c709d0ba3a85960702f1e4072e3d6cfd2'}
SOURCE_AUTHOR = {'path': 'assets/blender/rider-rebuild/selected-deep-crouch03/author.py',
                 'sha256': '96f0bfc45415ecd94cdb8430359a0f1d94f607a0369b33b36ea6de702d696e38'}
SOURCE_CONFIG = {'path': 'assets/blender/rider-rebuild/selected-deep-crouch03/engine05-input01.json',
                 'sha256': '80acead6a9bcb4c25d5ad650b59e52fbc97e3bda90ea727e8cceddc6628e324d'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): digest.update(block)
    return digest.hexdigest()


def pin(row):
    assert set(row) == {'path', 'sha256'} and isinstance(row['path'], str) and row['path']
    assert isinstance(row['sha256'], str) and len(row['sha256']) == 64
    path = ROOT/row['path']; assert sha(path) == row['sha256'], ('Changed input', row)
    return path


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    config_path, out = (Path(p).resolve() for p in args)
    config = json.loads(config_path.read_text())
    assert config['accepted'] is False and config['ready'] is True
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-deep-crouch03')
    assert config['sourceAuthor'] == SOURCE_AUTHOR and config['sourceConfig'] == SOURCE_CONFIG
    pin(SOURCE_AUTHOR)
    source = json.loads(pin(SOURCE_CONFIG).read_text())
    assert source['accepted'] is False and source['ready'] is True
    native, contract_path = pin(source['native']), pin(source['baseContract'])
    contract = json.loads(contract_path.read_text())
    receipt = json.loads(pin(config['motionReceipt']).read_text())
    assert receipt['accepted'] is False and receipt['sourceNative'] == source['native']
    assert receipt['baseContract'] == source['baseContract'] and receipt['candidate'] == config['candidate']
    assert receipt['recipeSHA256'] == SOURCE_AUTHOR['sha256'] and receipt['configSHA256'] == SOURCE_CONFIG['sha256']
    assert receipt['action'] == ACTION and receipt['fps'] == 24 and receipt['frameRange'] == [1, 217]
    assert receipt['exact75TRSKeyedEveryFrame'] and receipt['neutralBasisReturnExact']
    assert receipt['nativeMatrices'] == {**config['nativeMatrices'], 'space': contract['nativeRest']['frame']}
    candidate_path = pin(config['candidate'])
    recorded = np.load(pin(config['nativeMatrices']))
    assert np.array_equal(recorded['frames'], np.arange(1, 218))
    assert recorded['worldMatrices'].shape == (217, 75, 4, 4) and np.isfinite(recorded['worldMatrices']).all()
    for row in config['exporterSources']: pin(row)
    historical = runpy.run_path(str(pin(HISTORICAL)))
    rest, fingerprint = historical['rest'], historical['action_fingerprint']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(native), link=False) as (_, loaded): loaded.objects = ['RiderSkeleton']
    rig = loaded.objects[0]; bpy.context.scene.collection.objects.link(rig)
    assert rig.name == 'RiderSkeleton' and rig.matrix_world.is_identity and rig.animation_data is None
    assert len(rig.data.bones) == 75 and rest(rig) == contract['nativeRest']['bones']
    assert not rig.constraints and all(not b.constraints for b in rig.pose.bones)
    with bpy.data.libraries.load(str(candidate_path), link=False) as (_, loaded):
        loaded.objects = ['RiderSkeleton']; loaded.actions = [ACTION]
    candidate, action = loaded.objects[0], loaded.actions[0]
    assert candidate.matrix_world.is_identity and rest(candidate) == rest(rig)
    assert candidate.animation_data.action == action and len(action.slots) == 1
    slot = action.slots[0]
    assert slot.identifier == receipt['actionSlot'] and candidate.animation_data.action_slot == slot
    assert slot.target_id_type == 'OBJECT'
    curve_sha = fingerprint(action, slot, rig, list(range(1, 218)))
    action.use_fake_user = True
    data = candidate.data; bpy.data.objects.remove(candidate, do_unlink=True)
    if data.users == 0: bpy.data.armatures.remove(data)
    assert set(bpy.data.actions) == {action} and not bpy.data.meshes and list(bpy.context.scene.objects) == [rig]
    rig.animation_data_create(); rig.animation_data.action = action; rig.animation_data.action_slot = slot
    for bone in rig.pose.bones: bone.rotation_mode = 'QUATERNION'
    scene = bpy.context.scene; scene.render.fps = 24; scene.render.fps_base = 1
    scene.frame_start = 1; scene.frame_end = 217
    names = [b.name for b in rig.pose.bones]
    assert recorded['boneNames'].tolist() == names
    axis = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    matrices, residual = [], 0.
    for frame in range(1, 218):
        scene.frame_set(frame); bpy.context.view_layer.update()
        native_world = np.asarray([b.matrix for b in rig.pose.bones], dtype=np.float64)
        residual = max(residual, float(np.max(abs(native_world-recorded['worldMatrices'][frame-1]))))
        matrices.append([np.asarray(axis@rig.matrix_world@b.matrix) for b in rig.pose.bones])
    assert residual < 2e-6, ('Saved action differs from authored native matrices', residual)
    assert fingerprint(action, slot, rig, list(range(1, 218))) == curve_sha
    scene.frame_set(1); bpy.context.view_layer.update()
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones) and rest(rig) == contract['nativeRest']['bones']
    out.mkdir(parents=True); editable = out/'native75-deep217-rig.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(editable), compress=True)
    np.savez_compressed(out/'native-action-matrices.npz', boneNames=names, pose0=np.asarray(matrices, dtype=np.float64))
    rig.select_set(True); bpy.context.view_layer.objects.active = rig
    options = {'filepath': str(out/'rig-actions.glb'), 'export_format': 'GLB', 'use_selection': True,
        'export_yup': True, 'export_animations': True, 'export_animation_mode': 'ACTIONS',
        'export_anim_single_armature': True, 'export_frame_range': False, 'export_frame_step': 1,
        'export_force_sampling': True, 'export_optimize_animation_size': False,
        'export_optimize_animation_keep_anim_armature': True, 'export_anim_slide_to_zero': True,
        'export_sampling_interpolation_fallback': 'LINEAR', 'export_merge_animation': 'NONE',
        'export_rest_position_armature': True, 'export_def_bones': True, 'export_skins': True,
        'export_leaf_bone': False, 'export_armature_object_remove': False,
        'export_hierarchy_flatten_bones': False, 'export_hierarchy_flatten_objs': False,
        'export_bake_animation': False, 'export_pointer_animation': False, 'export_current_frame': False}
    assert set(options) <= set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    bpy.ops.export_scene.gltf(**options)
    provenance = {k: config[k] for k in ('sourceAuthor', 'sourceConfig', 'motionReceipt', 'candidate', 'nativeMatrices')}
    report = {'accepted': False, 'native': {'path': str(editable.relative_to(ROOT)), 'sha256': sha(editable)},
        'recipeSHA256': sha(__file__), 'inputSHA256': sha(config_path), 'historicalExporter': HISTORICAL,
        'motionProvenance': provenance, 'sourceNative': source['native'], 'sourceContract': source['baseContract'],
        'rigOnlyNoMeshes': True, 'exact75Rest': True, 'maximumSavedNativeMatrixResidual': residual,
        'actions': [{'name': ACTION, 'slot': slot.identifier, 'frameRange': [1, 217], 'frames': 217,
                     'fps': 24, 'seconds': 9., 'sourceCurveSHA256': curve_sha}], 'exportOptions': options,
        'limits': ['One new deep217 action; full dressed played motion, Garage/GPU contacts and devices remain unaccepted.']}
    (out/'rig-export.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'out': str(out), 'action': ACTION, 'maximumSavedNativeMatrixResidual': residual}), flush=True)


if __name__ == '__main__':
    if not __debug__: raise RuntimeError('Do not disable validation with Python -O')
    main()
