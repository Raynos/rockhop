"""Export the two existing native actions from a rig-only editable scene.

Parent serialized CPU2 only. No dense mesh import/export, fitting or new motion.
blender -b -t 2 --python-exit-code 1 --python author.py -- INPUT FRESH_OUT
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


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], ('Changed input',row); return path


def rest(rig):
    return [{'name':b.name,'parent':b.parent.name if b.parent else None,
             'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local],
             'useConnect':b.use_connect,'useDeform':b.use_deform} for b in rig.data.bones]


def action_fingerprint(action, slot, rig, frames):
    rows = []; found = set()
    expected = {(f'pose.bones["{bone.name}"].{prop}',index)
                for bone in rig.data.bones for prop,width in [('location',3),('rotation_quaternion',4),('scale',3)]
                for index in range(width)}
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(slot)
            if bag is None: continue
            for curve in bag.fcurves:
                identity = (curve.data_path, curve.array_index)
                assert identity in expected and identity not in found and not curve.modifiers
                found.add(identity)
                keys = [[float(key.co.x),float(key.co.y),key.interpolation] for key in curve.keyframe_points]
                assert [key[0] for key in keys] == frames and all(key[2]=='LINEAR' for key in keys)
                rows.append([*identity,keys])
    assert found == expected, 'All exact75 TRS components must be present on the original slot'
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args)==2
    config_path,out = (Path(value).resolve() for value in args)
    config = json.loads(config_path.read_text()); assert config['accepted'] is False and config['ready'] is True
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-garage-actions01')
    for key in ('native','sourceGLB','contract','calibration'): pin(config[key])
    for row in config['exporterSources']: pin(row)
    assert sha(HERE/'append_actions.py') == config['appendHelperSHA256']
    contract = json.loads(pin(config['contract']).read_text())
    receipts = [json.loads(pin(row['motionReceipt']).read_text()) for row in config['actions']]
    for row,receipt in zip(config['actions'],receipts):
        assert receipt['accepted'] is False and receipt['sourceNative']==config['native']
        assert receipt['baseContract']==config['contract'] and receipt['candidate']==row['native']
        assert receipt['exact75TRSKeyedEveryFrame'] and receipt['neutralBasisReturnExact']
        assert receipt['action']==row['name'] and receipt['actionSlot']==row['slot']
        assert receipt['fps']==24 and receipt['frameRange']==row['frameRange']
        pin(row['native'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(pin(config['native'])),link=False) as (_,loaded): loaded.objects=['RiderSkeleton']
    rig = loaded.objects[0]; bpy.context.scene.collection.objects.link(rig)
    assert rig.name=='RiderSkeleton' and rig.type=='ARMATURE' and rig.matrix_world.is_identity
    assert rest(rig)==contract['nativeRest']['bones'] and len(rig.data.bones)==75
    assert rig.animation_data is None and all(not bone.constraints for bone in rig.pose.bones)
    loaded_actions = []; records = []
    for row in config['actions']:
        with bpy.data.libraries.load(str(pin(row['native'])),link=False) as (_,loaded):
            loaded.objects=['RiderSkeleton']; loaded.actions=[row['name']]
        candidate,action = loaded.objects[0],loaded.actions[0]
        assert rest(candidate)==rest(rig) and candidate.matrix_world.is_identity
        assert candidate.animation_data.action==action and len(action.slots)==1
        slot = action.slots[0]; assert slot.identifier==row['slot'] and slot.target_id_type=='OBJECT'
        assert candidate.animation_data.action_slot==slot
        frames = list(range(row['frameRange'][0],row['frameRange'][1]+1))
        fingerprint = action_fingerprint(action,slot,rig,frames)
        action.use_fake_user=True; loaded_actions.append(action)
        data = candidate.data; bpy.data.objects.remove(candidate,do_unlink=True)
        if data.users==0: bpy.data.armatures.remove(data)
        records.append({'name':action.name,'slot':slot.identifier,'frameRange':row['frameRange'],
                        'frames':len(frames),'fps':24,'seconds':(len(frames)-1)/24,
                        'sourceCurveSHA256':fingerprint})
    assert set(bpy.data.actions)==set(loaded_actions)
    assert not bpy.data.meshes and list(bpy.context.scene.objects)==[rig]
    rig.animation_data_create()
    for bone in rig.pose.bones: bone.rotation_mode='QUATERNION'
    scene=bpy.context.scene; scene.render.fps=24; scene.render.fps_base=1
    scene.frame_start=1; scene.frame_end=max(row['frameRange'][1] for row in config['actions'])
    expected = {'boneNames':np.asarray([bone.name for bone in rig.data.bones])}
    axis=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
    for index,(row,action) in enumerate(zip(config['actions'],loaded_actions)):
        rig.animation_data.action=action; rig.animation_data.action_slot=action.slots[0]
        matrices=[]
        for frame in range(row['frameRange'][0],row['frameRange'][1]+1):
            scene.frame_set(frame); bpy.context.view_layer.update()
            matrices.append([np.asarray(axis@rig.matrix_world@bone.matrix) for bone in rig.pose.bones])
        expected[f'pose{index}']=np.asarray(matrices,dtype=np.float64)
        assert action_fingerprint(action,action.slots[0],rig,list(range(*[row['frameRange'][0],row['frameRange'][1]+1])))==records[index]['sourceCurveSHA256']
    rig.animation_data.action=loaded_actions[0]; rig.animation_data.action_slot=loaded_actions[0].slots[0]
    scene.frame_set(1); bpy.context.view_layer.update()
    assert all(bone.matrix_basis.is_identity for bone in rig.pose.bones)
    assert rest(rig)==contract['nativeRest']['bones']
    out.mkdir(parents=True); native=out/'native75-two-original-actions.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    np.savez_compressed(out/'native-action-matrices.npz',**expected)
    rig.select_set(True); bpy.context.view_layer.objects.active=rig
    options={'filepath':str(out/'rig-actions.glb'),'export_format':'GLB','use_selection':True,
             'export_yup':True,'export_animations':True,'export_animation_mode':'ACTIONS',
             'export_anim_single_armature':True,'export_frame_range':False,'export_frame_step':1,
             'export_force_sampling':True,'export_optimize_animation_size':False,
             'export_optimize_animation_keep_anim_armature':True,'export_anim_slide_to_zero':True,
             'export_sampling_interpolation_fallback':'LINEAR','export_merge_animation':'NONE',
             'export_rest_position_armature':True,'export_def_bones':True,'export_skins':True,
             'export_leaf_bone':False,'export_armature_object_remove':False,
             'export_hierarchy_flatten_bones':False,'export_hierarchy_flatten_objs':False,
             'export_bake_animation':False,'export_pointer_animation':False,'export_current_frame':False}
    available=bpy.ops.export_scene.gltf.get_rna_type().properties
    assert set(options)<=set(available.keys()), 'Installed glTF operator schema changed'
    bpy.ops.export_scene.gltf(**options)
    report={'accepted':False,'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},
            'recipeSHA256':sha(__file__),'inputSHA256':sha(config_path),'actions':records,
            'exportOptions':options,'rigOnlyNoMeshes':True,'exact75Rest':True,
            'limits':['Original action transport only; no moving art, actual GPU, contacts or device qualification.']}
    (out/'rig-export.json').write_text(json.dumps(report,indent=2)+'\n')
    helper=runpy.run_path(str(HERE/'append_actions.py'))
    helper['append'](config,config_path,out,report)
    for key in ('native','sourceGLB','contract','calibration'): pin(config[key])
    print(json.dumps({'out':str(out),'actions':records}),flush=True)


if __name__=='__main__': main()
