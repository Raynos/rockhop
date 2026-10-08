"""Pinned dressed native75: moderate fixed-foot crouch/rise/arm-raise/return.

Parent CPU2 only. Separate action/artifact; existing145 reach source untouched.
blender -b -t 2 --python-exit-code 1 --python author.py -- CONFIG FRESH_OUT
CONFIG: accepted:false, native/baseContract/sourceReceipt exact path+sha256.
"""
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion, Vector

ROOT=Path(__file__).resolve().parents[4]
ACTION='UnacceptedSelectedCrouchRiseArmsUp193'
EXPECTED={'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}
STATIONS=((1,0.,0.),(13,0.,0.),(49,1.,0.),(61,1.,0.),(97,0.,0.),(109,0.,0.),(145,0.,1.),(157,0.,1.),(193,0.,0.))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()


def pin(row):
    path=ROOT/row['path'];assert sha(path)==row['sha256'],('Changed input',row);return path


def phase(frame):
    for a,b in zip(STATIONS,STATIONS[1:]):
        if frame<=b[0]:
            t=(frame-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t
    return 0.,0.


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    config_path,out=(Path(p).resolve() for p in args);config=json.loads(config_path.read_text())
    assert config['accepted'] is False and not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-generic-envelope02')
    native,contract_path,receipt_path=[pin(config[k]) for k in ('native','baseContract','sourceReceipt')]
    contract=json.loads(contract_path.read_text());receipt=json.loads(receipt_path.read_text())
    assert receipt['native']==config['native'] and receipt['accepted'] is False and set(receipt['objects'])==EXPECTED
    assert receipt['rigAndContractExactNative75'] is True and contract['nativeRest']['frame']=='X-left,-Y-forward,Z-up'
    helper_path=ROOT/'assets/blender/rider-rebuild/head-neck-anatomical02/author-clothed-neck-motion.py'
    assert sha(helper_path)=='86cd010c88ad10cf3d5c925a133cdaafab760ac72a30a1e487d782a562fc71b2'
    helper=runpy.run_path(str(helper_path));geometry,rest_rows=helper['geometry'],helper['rest']
    bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;rig=bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones)==75 and rig.matrix_world.is_identity and rig.animation_data is None
    assert all(not b.constraints and b.matrix_basis.is_identity for b in rig.pose.bones) and not rig.constraints
    assert {o.name for o in scene.objects if o.type=='MESH' and not o.hide_render}==EXPECTED
    assert all(layer.material_override is None for layer in scene.view_layers)
    rows=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),
           'matrix':[list(r) for r in b.matrix_local],'useConnect':b.use_connect,'useDeform':b.use_deform} for b in rig.data.bones]
    assert rows==contract['nativeRest']['bones'],'Exact corrected native75 required'
    roles=contract['specification']['roles'];one=lambda value:value[0] if isinstance(value,list) else value
    group=lambda value:value if isinstance(value,list) else [value]
    pelvis=one(roles['pelvis']);assert rig.data.bones[pelvis].parent is None
    trunk=[n for n in group(roles['trunk']) if n!=pelvis];neck=group(roles['neck']);head=one(roles['head'])
    assert trunk and neck and all(n in rig.data.bones for v in roles.values() for n in group(v))
    rest={b.name:b.matrix_local.copy() for b in rig.data.bones};heads={b.name:b.head_local.copy() for b in rig.data.bones}
    meshes=[bpy.data.objects[n] for n in sorted(EXPECTED)];full=bpy.data.objects['RiderBody__FullAnatomyReference'];assert full.hide_render
    fingerprints={o.name:geometry(o) for o in meshes+[full]};before_rest=rest_rows(rig)
    object_state=[(o.name,o.hide_render,[list(r) for r in o.matrix_world]) for o in scene.objects]
    up=Vector((0,0,1));across=(heads[one(roles['thighLeft'])]-heads[one(roles['thighRight'])]);across-=up*across.dot(up);across.normalize()
    forward=sum((heads[one(roles['toe'+s])]-heads[one(roles['foot'+s])] for s in ('Left','Right')),Vector((0,0,0)))
    forward-=up*forward.dot(up);forward.normalize();assert forward.y<-.9 and across.x>.9
    limbs={};supports={};maximum={'jointLengthM':0.,'ankleTargetM':0.,'soleFrameM':0.,'soleFrameRadians':0.,'supportPointM':0.}
    for side,suffix,sign in [('left','Left',1),('right','Right',-1)]:
        for kind,upper_role,lower_role,end_role in [('arm','upperArm','forearm','wrist'),('leg','thigh','shin','foot')]:
            upper,lower,end=[one(roles[r+suffix]) for r in (upper_role,lower_role,end_role)]
            limbs[kind+suffix]=(group(roles[upper_role+suffix]),group(roles[lower_role+suffix]),end,
                (heads[lower]-heads[upper]).length,(heads[end]-heads[lower]).length)
        foot,toe=[one(roles[r+suffix]) for r in ('foot','toe')];boot=bpy.data.objects['ActualSelectedBoot.'+('L' if sign==1 else 'R')]
        foot_forward=heads[toe]-heads[foot];foot_forward-=up*foot_forward.dot(up);foot_forward.normalize();lateral=foot_forward.cross(up)
        groups={g.index:g.name for g in boot.vertex_groups};ids=[v.index for v in boot.data.vertices if v.groups and all(groups[g.group] in {foot,toe} for g in v.groups if g.weight>0)]
        assert ids,'Actual boot needs rigid foot/toe sole vertices';points=np.asarray([boot.data.vertices[i].co[:] for i in ids])
        ids=np.asarray(ids);low=points[:,2]<=points[:,2].min()+.003;ids=ids[low];points=points[low];assert len(ids)>=3
        long=points@np.asarray(foot_forward);wide=points@np.asarray(lateral);front=long>=long.min()+.6*(long.max()-long.min())
        assert front.any();front_ids=np.flatnonzero(front);chosen=[int(ids[np.argmin(long)]),int(ids[front_ids[np.argmin(wide[front])]]),int(ids[front_ids[np.argmax(wide[front])]])]
        p=[boot.data.vertices[i].co.copy() for i in chosen];assert len(set(chosen))==3 and (p[1]-p[0]).cross(p[2]-p[0]).length*.5>1e-5
        sole=contract['driver']['soleSocketNames'][side];assert rig.data.bones[sole].parent.name==foot
        supports[side]={'boot':boot,'ids':chosen,'reference':p,'sole':sole,'foot':foot,'toe':toe,'restSole':rig.pose.bones[sole].matrix.copy()}

    def world_rotation(name,q):
        bone=rig.pose.bones[name];m=q.to_matrix().to_4x4();m.translation=bone.matrix.translation;bone.matrix=m;bone.scale=(1,1,1);bpy.context.view_layer.update()

    def aim(names,end,direction):
        swing=(heads[end]-heads[names[0]]).normalized().rotation_difference(direction.normalized())
        for name in names:world_rotation(name,swing@rest[name].to_quaternion())

    def solve(limb,target,pole):
        uppers,lowers,end,a,b=limb;start=rig.pose.bones[uppers[0]].matrix.translation.copy();ray=target-start;distance=ray.length
        assert abs(a-b)+1e-7<distance<a+b-1e-7,('Unreachable native target',end,distance,a,b)
        ray.normalize();pole=pole-start;pole-=ray*pole.dot(ray);assert pole.length>1e-7;pole.normalize()
        along=(a*a+distance*distance-b*b)/(2*distance);middle=start+ray*along+pole*math.sqrt(max(0,a*a-along*along))
        aim(uppers,lowers[0],middle-start);aim(lowers,end,target-middle)
        actual=[rig.pose.bones[n].matrix.translation.copy() for n in (uppers[0],lowers[0],end)]
        error=max(abs((actual[1]-actual[0]).length-a),abs((actual[2]-actual[1]).length-b));maximum['jointLengthM']=max(maximum['jointLengthM'],error);assert error<1e-4
        return (actual[2]-target).length

    visibility_path=Path(__file__).with_name('authoring-visibility.py')
    suspend=runpy.run_path(str(visibility_path))['DenseViewportSuspend'](scene,meshes,rig)
    assert bpy.data.actions.get(ACTION) is None;action=bpy.data.actions.new(ACTION);rig.animation_data_create();rig.animation_data.action=action
    scene.render.fps=24;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=193;observations=[];endpoint_basis=[]
    for frame in range(1,194):
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            bone.rotation_mode='QUATERNION';bone.location=(0,0,0);bone.rotation_quaternion=(1,0,0,0);bone.scale=(1,1,1)
        crouch,raise_arms=phase(frame)
        if crouch:
            # Root location is bone-local: explicitly convert the intended
            # native-world rearward/down displacement through its true rest.
            rig.pose.bones[pelvis].location=rest[pelvis].to_3x3().inverted()@(forward*(-.04*crouch)+up*(-.12*crouch))
            for name,degrees in [(pelvis,3.)]+[(n,9./len(trunk)) for n in trunk]+[(n,-8./len(neck)) for n in neck]:
                r=rest[name].to_quaternion();rig.pose.bones[name].rotation_quaternion=r.inverted()@Quaternion(across,math.radians(degrees*crouch))@r
        bpy.context.view_layer.update()
        for side,suffix,sign in [('left','Left',1),('right','Right',-1)]:
            support=supports[side];foot,toe=support['foot'],support['toe'];leg=limbs['leg'+suffix];arm=limbs['arm'+suffix]
            if crouch:
                length=leg[3]+leg[4];pole=heads[leg[1][0]].lerp(heads[foot]+forward*(.25*length)+up*(.375*length),crouch)
                error=solve(leg,heads[foot],pole);maximum['ankleTargetM']=max(maximum['ankleTargetM'],error);assert error<1e-4
                world_rotation(foot,rest[foot].to_quaternion());world_rotation(toe,rest[toe].to_quaternion())
                wrist=arm[2];start=rig.pose.bones[arm[0][0]].matrix.translation.copy();length=arm[3]+arm[4]
                target=heads[wrist].lerp(start+across*(sign*.11*length)+forward*(.64*length)-up*(.13*length),crouch)
                pole=heads[arm[1][0]].lerp(start+across*(sign*.34*length)+forward*(.26*length)-up*(.26*length),crouch);assert solve(arm,target,pole)<1e-4
                world_rotation(wrist,rest[wrist].to_quaternion())
            if raise_arms:
                shoulder=one(roles['shoulder'+suffix]);r=rest[shoulder].to_quaternion()
                rig.pose.bones[shoulder].rotation_quaternion=r.inverted()@Quaternion(forward,sign*math.radians(8)*raise_arms)@r;bpy.context.view_layer.update()
                upper_direction=(heads[arm[1][0]]-heads[arm[0][0]]).normalized();lower_direction=(heads[arm[2]]-heads[arm[1][0]]).normalized()
                desired_upper=across*(sign*math.sin(math.radians(125)))+up*(-math.cos(math.radians(125)))
                desired_lower=desired_upper*math.cos(math.radians(20))+forward*math.sin(math.radians(20))
                u=Quaternion((1,0,0,0)).slerp(upper_direction.rotation_difference(desired_upper),raise_arms)@upper_direction
                v=Quaternion((1,0,0,0)).slerp(lower_direction.rotation_difference(desired_lower),raise_arms)@lower_direction
                start=rig.pose.bones[arm[0][0]].matrix.translation.copy();pole=start+u*arm[3];target=pole+v*arm[4]
                assert solve(arm,target,pole)<1e-4;world_rotation(arm[2],lower_direction.rotation_difference(v)@rest[arm[2]].to_quaternion())
            sole_delta=(rig.pose.bones[support['sole']].matrix.translation-support['restSole'].translation).length
            maximum['soleFrameM']=max(maximum['soleFrameM'],sole_delta);assert sole_delta<2e-5
            sole_angle=rig.pose.bones[support['sole']].matrix.to_quaternion().rotation_difference(support['restSole'].to_quaternion()).angle
            maximum['soleFrameRadians']=max(maximum['soleFrameRadians'],sole_angle);assert sole_angle<2e-5
            knee_x=rig.pose.bones[leg[1][0]].matrix.translation.dot(across);assert knee_x*sign>0,'Knee crossed to the other side'
        bpy.context.view_layer.update()
        for bone in rig.pose.bones:
            assert all(math.isfinite(x) for row in bone.matrix_basis for x in row)
            for prop in ('location','rotation_quaternion','scale'):bone.keyframe_insert(data_path=prop,frame=frame,group=bone.name)
        if frame in (1,193):endpoint_basis.append([[list(row) for row in b.matrix_basis] for b in rig.pose.bones]);assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
        if frame in {r[0] for r in STATIONS}:
            sample={'frame':frame,'crouch':crouch,'armsUp':raise_arms,'pelvis':list(rig.pose.bones[pelvis].matrix.translation),'support':{}}
            with suspend.visible_for_measurement(support['boot'] for support in supports.values()) as graph:
                for side,support in supports.items():
                    evaluated=support['boot'].evaluated_get(graph);assert len(evaluated.data.vertices)==len(support['boot'].data.vertices)
                    actual=[evaluated.data.vertices[i].co.copy() for i in support['ids']];error=max((p-q).length for p,q in zip(actual,support['reference']))
                    maximum['supportPointM']=max(maximum['supportPointM'],error);assert error<2e-5,('Actual finite sole support moved',frame,side,error)
                    sample['support'][side]={'nativeVertexIDs':support['ids'],'actualPoints':[list(p) for p in actual],'maximumMovementM':error}
            observations.append(sample)
    assert len(action.slots)==1 and endpoint_basis[0]==endpoint_basis[1]
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(action.slots[0])
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    visibility_report=suspend.restore()
    assert before_rest==rest_rows(rig) and fingerprints=={o.name:geometry(o) for o in meshes+[full]}
    assert object_state==[(o.name,o.hide_render,[list(r) for r in o.matrix_world]) for o in scene.objects]
    scene.frame_set(1);out.mkdir(parents=True);candidate=out/'selected-generic-envelope193.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate),compress=True)
    report={'accepted':False,'candidate':{'path':str(candidate.relative_to(ROOT)),'sha256':sha(candidate)},'sourceNative':config['native'],'baseContract':config['baseContract'],'sourceReceipt':config['sourceReceipt'],
        'recipeSHA256':sha(__file__),'visibilityHelperSHA256':sha(visibility_path),'viewportVisibility':visibility_report,'configSHA256':sha(config_path),'action':ACTION,'actionSlot':action.slots[0].identifier,'fps':24,'frameRange':[1,193],
        'visibleMeshes':sorted(EXPECTED),'exact75TRSKeyedEveryFrame':True,'neutralBasisReturnExact':True,'restAndOutfitFingerprintsUnchanged':fingerprints,
        'maximumResiduals':maximum,'observations':observations,'limits':['Unaccepted separate native generic envelope; existing145 reach source/artifact unchanged.',
            'Moderate12cm crouch and125deg-from-down arm elevation only; no universal anatomy envelope, bike pose or moving acceptance.',
            'Three finite source sole vertices measured at stations; no claim that every boot surface point is a contact or that tissue COM is integrated.',
            'No geometry/material/field edit, export, clipping fix, player promotion or device acceptance.']}
    (out/'motion.json').write_text(json.dumps(report,indent=2)+'\n');assert sha(native)==config['native']['sha256'];print(json.dumps({'candidate':report['candidate'],'action':ACTION,'maximumResiduals':maximum}),flush=True)


if __name__=='__main__':main()
