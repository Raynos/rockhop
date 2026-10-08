"""Parent-guarded, rig-only editable bike actions from actual weight02 anatomy.

blender -b -t 2 --python-exit-code 1 --python bike_build.py -- INPUT.json FRESH_OUT
The saved package is appendable authoring data. Full dressed support/appearance
must be evaluated separately; joint reach and patch centroids cannot accept it.
"""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE))
from build import sha,load_rig,action_curves,keyed_action,operator_bound
from controls import install,rest_rows
from bike_action import FPS,SECONDS,KEYS,PAIRS,score,solve_seat


def saddle_height(x,z,triangles):
    hits=[]
    for row in triangles:
        if not row['upward']:continue
        a,b,c=map(Vector,row['pointsBike']);d=(b.z-c.z)*(a.x-c.x)+(c.x-b.x)*(a.z-c.z)
        if abs(d)<1e-12:continue
        u=((b.z-c.z)*(x-c.x)+(c.x-b.x)*(z-c.z))/d;v=((c.z-a.z)*(x-c.x)+(a.x-c.x)*(z-c.z))/d
        if min(u,v,1-u-v)>=-1e-8:hits.append((u*a.y+v*b.y+(1-u-v)*c.y,row['sourceTriangleOrdinal']))
    assert hits,('Fixed guide misses finite saddle',x,z)
    return max(hits)


def core_source(jeans,patches,names):
    assert jeans.matrix_world.is_identity and not jeans.data.shape_keys
    ids={v.value:i for i,v in enumerate(jeans.data.attributes['_NATIVE_ID'].data)}
    groups={g.index:g.name for g in jeans.vertex_groups};points={};triangles={}
    for side in ('left','right'):
        patch=patches['patches'][side]['core'];triangles[side]=[r['nativeVertexIDs'] for r in patch['triangles']]
        for row in patch['nativeVertices']:
            vertex=jeans.data.vertices[ids[row['id']]];assert (vertex.co-Vector(row['sourceXYZ'])).length<1e-7
            weights={groups[g.group]:g.weight for g in vertex.groups if g.weight>0 and groups[g.group] in names}
            assert weights and abs(sum(weights.values())-1)<1e-6
            assert set(weights)<={'DEF-spine','DEF-thigh.L','DEF-thigh.R'}, 'Torso must not affect the chosen finite support cores'
            points[row['id']]=(vertex.co.copy(),weights)
    bpy.data.objects.remove(jeans,do_unlink=True)
    return {'points':points,'triangles':triangles}


def key_controls(rig,context,frame,previous):
    for name in context['controls']:
        bone=rig.pose.bones[name];q=bone.rotation_quaternion.copy()
        if name in previous and q.dot(previous[name])<0:q.negate();bone.rotation_quaternion=q
        previous[name]=q.copy()
        for prop in ('location','rotation_quaternion','scale'):bone.keyframe_insert(prop,frame=frame,group=name)
        if name.startswith('CTRL-palm.'):
            for digit in ('thumb','index','middle','ring','pinky'):bone.keyframe_insert(f'["{digit}"]',frame=frame,group=name)


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    source,out=map(lambda p:Path(p).resolve(),args);config=json.loads(source.read_text())
    assert config['accepted'] is False and not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    for p in config['pins'].values():assert sha(ROOT/p['path'])==p['sha256'],p
    read=lambda name:json.loads((ROOT/config['pins'][name]['path']).read_text())
    contract,document,patches=map(read,['contract','bikeContext','patches']);native=ROOT/config['pins']['native']['path']
    receipt=read('weightReceipt');assert receipt['native']==config['pins']['native'] and receipt['supportCorrection']['rankPruning'] is False
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(native),link=False) as (_,data):data.objects=['RiderSkeleton','RiderJeans']
    rig,jeans=data.objects;scene=bpy.context.scene;scene.collection.objects.link(rig);context=install(rig,contract)
    context['parents']={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
    names=context['names'];support=core_source(jeans,patches,names);scene.render.fps=FPS;scene.render.fps_base=1
    out.mkdir(parents=True);rig.animation_data_create();arrays={'boneNames':np.asarray(names)};records=[];author=[];baked=[]
    support_path=out/'finite-core-source.json'
    support_path.write_text(json.dumps({'accepted':False,'source':config,'points':{str(i):{'basisNative':list(p),'actualNamedWeights':w} for i,(p,w) in support['points'].items()},
        'triangles':support['triangles'],'shapeActivation':0,'reason':'Author a new pose against actual weight02 Basis. No author04 volume activation or fitted pelvis is imported.'},indent=2)+'\n')
    for index,bike in enumerate(document['bikes']):
        guide={};guides={}
        for side in ('left','right'):
            guide[side]=[]
            for x in (-.40,-.36,-.32):
                for z in ((-.03,-.05) if side=='left' else (.03,.05)):
                    y,row=saddle_height(x,z,bike['saddle']);guide[side].append({'pointBike':[x,y+.001,z],'sourceTriangleOrdinal':row})
            guides[side]=list(sum((Vector(r['pointBike']) for r in guide[side]),Vector())/len(guide[side]))
        support['guideCentersBike']=guides
        name='RiderBikeSeatedLean'+bike['name'].title();action=bpy.data.actions.new('Author.'+name);action.use_fake_user=True
        rig.animation_data.action=action;world_samples=[];local_samples=[];witnesses=[];previous={};previous_control={};root=None;regional=0.
        try:
            for frame in range(1,round(SECONDS*FPS)+2):
                scene.frame_set(frame);params=score((frame-1)/FPS)
                root,witness=solve_seat(rig,context,bike,document,support,params,root)
                key_controls(rig,context,frame,previous_control);bpy.context.view_layer.update()
                worlds={n:rig.pose.bones[n].matrix.copy() for n in names};local=[]
                for n in names:
                    b=rig.data.bones[n];options={'parent_matrix':worlds[b.parent.name],'parent_matrix_local':b.parent.matrix_local} if b.parent else {}
                    matrix=b.convert_local_to_pose(worlds[n],b.matrix_local,invert=True,**options);p,q,s=matrix.decompose()
                    if n in previous and q.dot(previous[n])<0:q.negate()
                    previous[n]=q.copy();local.append([*p,*q,*s])
                for n,carrier in PAIRS:regional=max(regional,operator_bound(worlds[n]@context['rest'][n].inverted(),worlds[carrier]@context['rest'][carrier].inverted()))
                assert regional<.0001,('Regional skin palette changed',frame,regional)
                world_samples.append([np.asarray(worlds[n]) for n in names]);local_samples.append(local)
                witnesses.append({'frame':frame,'timeSeconds':(frame-1)/FPS,**witness})
                if frame==1:
                    initial_file=out/(bike['name']+'-first-seated-controls.blend')
                    bpy.ops.wm.save_as_mainfile(filepath=str(initial_file),compress=True)
                    (out/(bike['name']+'-first-seated-pose.json')).write_text(json.dumps({'accepted':False,
                        'status':'FIRST_NATIVE_SEATED_POSE_FINITE_CONTACT_AND_ART_PENDING','source':config,'bike':bike['bike'],
                        'native':{'path':str(initial_file.relative_to(ROOT)),'sha256':sha(initial_file)},'witness':witness,
                        'nativeBoneWorldMatrices':{n:[list(r) for r in worlds[n]] for n in names},
                        'controlBasis':{n:[list(r) for r in rig.pose.bones[n].matrix_basis] for n in context['controls']}},indent=2)+'\n')
        except Exception as error:
            (out/'failed-action.json').write_text(json.dumps({'accepted':False,'action':name,'frame':frame,'score':params,'error':repr(error),'completed':[r['name'] for r in records],'lastWitness':witnesses[-1] if witnesses else None},indent=2)+'\n')
            raise
        for curve in action_curves(action):
            for key in curve.keyframe_points:key.interpolation='LINEAR'
        arrays[f'pose{index}']=np.asarray(world_samples);arrays[f'local{index}']=np.asarray(local_samples)
        baked_action=keyed_action(name,names,arrays[f'local{index}']);author.append(action);baked.append(baked_action)
        record={'name':name,'bike':bike['bike'],'controlAction':action.name,'fps':FPS,'seconds':SECONDS,'frameRange':[1,241],
            'loop':False,'playback':'ONCE','shapeActivation':0,'surfaceWitnessFrames':[1,61,181,241],
            'guides':guide,'keyScore':KEYS,'regionalOperatorBoundWithin2mM':regional,'support':witnesses,
            'finiteContactAccepted':False,'finiteContactMeaning':'Centroid calibration only; whole anatomical reference and dressed finite support are separate required measurements.'}
        records.append(record);scene.frame_set(1);scene.frame_start=1;scene.frame_end=241
        file=out/(bike['name']+'-editable-controls.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
        record['controlNative']={'path':str(file.relative_to(ROOT)),'sha256':sha(file)}
        np.savez_compressed(out/'bike-action-matrices.npz',**arrays)
        (out/'construction.json').write_text(json.dumps({'accepted':False,'status':'BIKE_CONTROLS_CONSTRUCTED_CONTACT_AND_ART_PENDING','source':config,'actions':records},indent=2)+'\n')
    assert rest_rows(rig,set(names))==contract['nativeRest']['bones']
    data=rig.data;bpy.data.objects.remove(rig,do_unlink=True)
    if data.users==0:bpy.data.armatures.remove(data)
    for action in author:bpy.data.actions.remove(action)
    rig=load_rig(native);assert rest_rows(rig)==contract['nativeRest']['bones'];rig.animation_data_create()
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    for index,(record,action) in enumerate(zip(records,baked)):
        rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];worst=0.
        for frame in range(1,242):
            scene.frame_set(frame);bpy.context.view_layer.update()
            for j,n in enumerate(names):worst=max(worst,operator_bound(rig.pose.bones[n].matrix,arrays[f'pose{index}'][frame-1,j]))
        assert worst<.0001,('Native bake differs',record['name'],worst);record['bakeMaximumAffineBoundWithin2mM']=worst
    scene.frame_set(1);export=out/'bike75-baked-actions.blend';bpy.ops.wm.save_as_mainfile(filepath=str(export),compress=True)
    for p in config['pins'].values():assert sha(ROOT/p['path'])==p['sha256'],p
    result={'accepted':False,'status':'NATIVE_BIKE_ACTIONS_UNACCEPTED','source':config,
        'sources':{p.name:sha(p) for p in [Path(__file__),HERE/'bike_action.py',HERE/'controls.py',HERE/'build.py']},
        'nativeRestExactlyPreserved':True,'bakedNative':{'path':str(export.relative_to(ROOT)),'sha256':sha(export)},
        'nativeMatrices':{'path':str((out/'bike-action-matrices.npz').relative_to(ROOT)),'sha256':sha(out/'bike-action-matrices.npz')},
        'finiteCoreSource':{'path':str(support_path.relative_to(ROOT)),'sha256':sha(support_path)},'actions':records,
        'limits':['No author04 pose or corrective is imported. No rig object/mesh/rest transform changes.',
                  'Complete full-reference and dressed finite support/collision checks and moving review remain mandatory.',
                  'This editable source must be appended to the selected master; rig-only output cannot be an appearance delivery.']}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'actions':[r['name'] for r in records]}),flush=True)


if __name__=='__main__':main()
