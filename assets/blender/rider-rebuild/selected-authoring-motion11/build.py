"""Parent-guarded native construction: controls plus six real actions.

blender -b -t 2 --python-exit-code 1 --python build.py -- source.json FRESH_OUT
Reads only RiderSkeleton from the appearance master. Never writes that master.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Quaternion

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]; sys.path.insert(0,str(HERE))
from controls import install, rest_rows
from motion import FPS, SCORES, score
from pose import apply


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024): h.update(block)
    return h.hexdigest()


def load_rig(path):
    with bpy.data.libraries.load(str(path),link=False) as (_,data): data.objects=['RiderSkeleton']
    rig=data.objects[0]; bpy.context.scene.collection.objects.link(rig); return rig


def action_curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(action.slots[0])
            if bag:
                yield from bag.fcurves


def keyed_action(name,names,samples):
    action=bpy.data.actions.new(name); action.use_fake_user=True
    slot=action.slots.new('OBJECT','RiderSkeleton')
    bag=action.layers.new('Baked native deformation').strips.new(type='KEYFRAME').channelbags.new(slot)
    for j,bone in enumerate(names):
        for prop,width,offset in [('location',3,0),('rotation_quaternion',4,3),('scale',3,7)]:
            for axis in range(width):
                curve=bag.fcurves.new(f'pose.bones["{bone}"].{prop}',index=axis)
                curve.keyframe_points.add(len(samples))
                data=np.column_stack([np.arange(1,len(samples)+1),samples[:,j,offset+axis]])
                curve.keyframe_points.foreach_set('co',data.ravel())
                for key in curve.keyframe_points: key.interpolation='LINEAR'
                curve.update()
    return action


def operator_bound(a,b):
    delta=np.asarray(a)-np.asarray(b)
    return float(np.linalg.norm(delta[:3,:3],2)*2+np.linalg.norm(delta[:3,3]))


def main():
    args=sys.argv[sys.argv.index('--')+1:]; assert len(args)==2
    config_path,out=map(lambda p:Path(p).resolve(),args); config=json.loads(config_path.read_text())
    assert config['accepted'] is False and not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    for row in (config['native'],config['contract']): assert sha(ROOT/row['path'])==row['sha256'],row
    native=ROOT/config['native']['path']; contract=json.loads((ROOT/config['contract']['path']).read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True); rig=load_rig(native); assert not bpy.data.meshes
    context=install(rig,contract); names=context['names']; scene=bpy.context.scene; scene.render.fps=FPS
    scene.render.fps_base=1; rig.animation_data_create(); records=[]; arrays={'boneNames':np.asarray(names)}; controls=[]; baked=[]
    for clip_index,(name,spec) in enumerate(SCORES.items()):
        frames=round(spec['seconds']*FPS)+1; action=bpy.data.actions.new('Author.'+name); action.use_fake_user=True
        rig.animation_data.action=action; world_samples=[]; local_samples=[]; support=[]; previous={}; previous_control={}
        palette_error=0.; maximum_sole_error=0.
        for frame in range(1,frames+1):
            scene.frame_set(frame); contact=apply(rig,context,score(name,(frame-1)/FPS))
            for control_name in context['controls']:
                bone=rig.pose.bones[control_name]; q=bone.rotation_quaternion.copy()
                if control_name in previous_control and q.dot(previous_control[control_name])<0: q.negate(); bone.rotation_quaternion=q
                previous_control[control_name]=q.copy()
                for prop in ('location','rotation_quaternion','scale'): bone.keyframe_insert(prop,frame=frame,group=control_name)
                if control_name.startswith('CTRL-palm.'):
                    for digit in ('thumb','index','middle','ring','pinky'): bone.keyframe_insert(f'["{digit}"]',frame=frame,group=control_name)
            bpy.context.view_layer.update(); worlds={n:rig.pose.bones[n].matrix.copy() for n in names}; local=[]
            for n in names:
                b=rig.data.bones[n]; options={'parent_matrix':worlds[b.parent.name], 'parent_matrix_local':b.parent.matrix_local} if b.parent else {}
                basis=b.convert_local_to_pose(worlds[n],b.matrix_local,invert=True,**options)
                p,q,s=basis.decompose()
                if n in previous and q.dot(previous[n])<0: q.negate()
                previous[n]=q.copy(); local.append([*p,*q,*s])
            for n,carrier in [('DEF-pelvis.L','DEF-spine'),('DEF-pelvis.R','DEF-spine'),
                              ('DEF-thigh.L.001','DEF-thigh.L'),('DEF-thigh.R.001','DEF-thigh.R')]:
                palette_error=max(palette_error,operator_bound(worlds[n]@context['rest'][n].inverted(),worlds[carrier]@context['rest'][carrier].inverted()))
            assert palette_error<.0001,('Regional shared skin-operator contract changed',name,frame,palette_error)
            maximum_sole_error=max(maximum_sole_error,*(p['errorM'] for p in contact['feet'].values()))
            world_samples.append([np.asarray(worlds[n]) for n in names]); local_samples.append(local)
            support.append({'frame':frame,'time':(frame-1)/FPS,**contact})
        for curve in action_curves(action):
            for key in curve.keyframe_points:key.interpolation='LINEAR'
        assert len(action.slots)==1
        poses=np.asarray(world_samples,dtype=np.float64); local=np.asarray(local_samples,dtype=np.float64)
        assert np.isfinite(poses).all() and np.isfinite(local).all()
        baked_action=keyed_action(name,names,local); controls.append(action); baked.append(baked_action)
        arrays[f'pose{clip_index}']=poses; arrays[f'local{clip_index}']=local
        records.append({'name':name,'controlAction':action.name,'controlSlot':action.slots[0].identifier,
                        'bakedSlot':baked_action.slots[0].identifier,'fps':FPS,'frameRange':[1,frames],
                        'seconds':spec['seconds'],'loop':spec['loop'],'rootForwardM':spec.get('rootForwardM',0.),
                        'playback': 'ONCE_OR_ACCUMULATE_ROOT_OFFSET' if spec.get('rootForwardM') else ('LOOP' if spec['loop'] else 'ONCE'),
                        'soleTargetMaximumM':maximum_sole_error,'regionalOperatorBoundWithin2mM':palette_error,'support':support})
        print(json.dumps({'action':name,'frames':frames,'soleMaxM':maximum_sole_error,'paletteBoundM':palette_error}),flush=True)
    assert rest_rows(rig,set(names))==contract['nativeRest']['bones'] and not bpy.data.meshes
    out.mkdir(parents=True); control_native=out/'native75-authoring-controls.blend'
    rig.animation_data.action=controls[0]; rig.animation_data.action_slot=controls[0].slots[0]
    scene.frame_set(1); scene.frame_start=1; scene.frame_end=records[0]['frameRange'][1]
    bpy.ops.wm.save_as_mainfile(filepath=str(control_native),compress=True)
    np.savez_compressed(out/'native-action-matrices.npz',**arrays)
    # A fresh source75 performs the saved visual bake independently of IK.
    data=rig.data; bpy.data.objects.remove(rig,do_unlink=True)
    if data.users==0:bpy.data.armatures.remove(data)
    for action in controls:bpy.data.actions.remove(action)
    rig=load_rig(native); assert rest_rows(rig)==contract['nativeRest']['bones']; rig.animation_data_create()
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    for i,(record,action) in enumerate(zip(records,baked)):
        rig.animation_data.action=action; rig.animation_data.action_slot=action.slots[0]; worst=0.
        for frame in range(1,record['frameRange'][1]+1):
            scene.frame_set(frame); bpy.context.view_layer.update()
            for j,n in enumerate(names):worst=max(worst,operator_bound(rig.pose.bones[n].matrix,arrays[f'pose{i}'][frame-1,j]))
        assert worst<.0001,('Visual bake differs from native constraints',record['name'],worst)
        record['bakeMaximumAffineBoundWithin2mM']=worst
    rig.animation_data.action=baked[0]; rig.animation_data.action_slot=baked[0].slots[0];scene.frame_set(1)
    export_native=out/'native75-baked-actions.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(export_native),compress=True)
    rig.select_set(True); bpy.context.view_layer.objects.active=rig
    options={'filepath':str(out/'rig-actions.glb'),'export_format':'GLB','use_selection':True,'export_yup':True,
             'export_animations':True,'export_animation_mode':'ACTIONS','export_anim_single_armature':True,
             'export_frame_range':False,'export_frame_step':1,'export_force_sampling':True,
             'export_optimize_animation_size':False,'export_optimize_animation_keep_anim_armature':True,
             'export_anim_slide_to_zero':True,'export_sampling_interpolation_fallback':'LINEAR','export_merge_animation':'NONE',
             'export_rest_position_armature':True,'export_def_bones':True,'export_skins':True,'export_leaf_bone':False,
             'export_armature_object_remove':False,'export_hierarchy_flatten_bones':False,'export_hierarchy_flatten_objs':False,
             'export_bake_animation':False,'export_pointer_animation':False,'export_current_frame':False}
    bpy.ops.export_scene.gltf(**options)
    report={'accepted':False,'status':'NATIVE_CONTROL_ACTION_PACKAGE_UNACCEPTED','source':config,
            'sources':{p.name:sha(p) for p in HERE.glob('*.py')},'controlNative':{'path':str(control_native.relative_to(ROOT)),'sha256':sha(control_native)},
            'bakedNative':{'path':str(export_native.relative_to(ROOT)),'sha256':sha(export_native)},
            'rigGLB':{'path':str((out/'rig-actions.glb').relative_to(ROOT)),'sha256':sha(out/'rig-actions.glb')},
            'controls':context['controls'],'sourceRestResidualM':context['sourceRestResidualM'],
            'addedRestMaximumMatrixResidual':context['addedRestMaximumMatrixResidual'],
            'addedRestBeforeConstraints':context['addedRestBeforeConstraints'],
            'neutral75BeforeActions':context['neutral75BeforeActions'],
            'neutralMaximumAffineBoundWithin2mM':context['neutralMaximumAffineBoundWithin2mM'],'actions':records,
            'limits':['Rig-only construction package, never a substitute for selected dressed playback.',
                      'Foot target stationarity is not finite boot/ground or clothing collision acceptance.',
                      'Native IK control envelope preserves regional palette; arbitrary independent split twists are not covered.',
                      'Bike contact actions, clothed motion, GPU parity and device/art acceptance remain open.']}
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');assert sha(native)==config['native']['sha256']
    print(json.dumps({'controlNative':report['controlNative'],'bakedNative':report['bakedNative'],'actions':[r['name'] for r in records]}),flush=True)


if __name__=='__main__':main()
