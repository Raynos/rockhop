"""Source-only exact75 clothed head turn/nod review; parent CPU2 lease only.

Requires a NEW pinned assembled native containing actual selected outfit +
the explicit reviewed conditioned body, and its assembly/readback receipts. No mesh/material/rest edit, no
export, no fallback action, and no garment/shoulder movement qualification.
blender -b -t 2 --python-exit-code 1 --python author-clothed-neck-motion.py -- CONFIG FRESH_OUT
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path(__file__).resolve().parents[4]
ACTION='UnacceptedClothedNeckTurnNod72'
ACTIVE=('DEF-spine.004','DEF-spine.005','DEF-spine.006')
YAW_SHARES=(.15,.25,.60)
NOD_SHARES=(.20,.30,.50)
STATIONS=((1,0.,0.),(13,24.,0.),(25,-24.,0.),(37,0.,0.),
          (49,0.,10.),(61,0.,-6.),(72,0.,0.))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pin(row):
    path=(ROOT/row['path']).resolve();assert sha(path)==row['sha256'],('Changed input',str(path));return path

def rest(rig):
    return [{'name':b.name,'parent':b.parent.name if b.parent else None,
      'head':list(b.head_local),'tail':list(b.tail_local),
      'matrix':[list(r) for r in b.matrix_local],'connect':b.use_connect,'deform':b.use_deform}
      for b in rig.data.bones]

def geometry(obj):
    h=hashlib.sha256();h.update(obj.name.encode())
    for v in obj.data.vertices:
        h.update(struct.pack('<3f',*v.co))
        for g in v.groups:h.update(struct.pack('<If',g.group,g.weight))
    for p in obj.data.polygons:
        h.update(struct.pack('<II',p.material_index,len(p.vertices)))
        h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    for layer in obj.data.uv_layers:
        h.update(layer.name.encode())
        for corner in layer.data:h.update(struct.pack('<2f',*corner.uv))
    for mat in obj.data.materials:
        if mat and mat.use_nodes:
            h.update(mat.name.encode())
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    assert node.image.packed_file,('Unpacked actual PBR',obj.name,node.image.name)
                    h.update(hashlib.sha256(node.image.packed_file.data).digest())
    return h.hexdigest()

def angles(frame):
    for a,b in zip(STATIONS,STATIONS[1:]):
        if frame<=b[0]:
            t=(frame-a[0])/(b[0]-a[0]);t=max(0.,min(1.,t));t=t*t*(3-2*t)
            return (a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t)
    return 0.,0.

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    config_path,out=(Path(p).resolve() for p in args);config=json.loads(config_path.read_text())
    assert config['accepted'] is False
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/head-neck-anatomical02') and not out.exists()
    master=pin(config['masterNative']);assembly_path=pin(config['assemblyReceipt']);readback_path=pin(config['bodyReadback'])
    assembly=json.loads(assembly_path.read_text());readback=json.loads(readback_path.read_text())
    reviewed_body=pin(config['reviewedBodyNative']);conditioning=json.loads(pin(config['bodyConditionReceipt']).read_text())
    assert conditioning['candidate']==config['reviewedBodyNative']
    assert conditioning['afterEndpointFieldJump']['all']['maxL1']==0.
    assert assembly['native']==config['masterNative']
    assert assembly['bodyCandidate']['native']==config['reviewedBodyNative']
    assert assembly['canonical75RestExact'] is True and assembly['bodyAnd75RigUnchangedByAssembly'] is True
    assert readback['candidate']==config['reviewedBodyNative'] and readback['all75RestRecordsExactlyUnchanged'] is True
    assert readback['repairedHandRowsExactlyUnchanged']==1446
    visible=config['visibleMeshes'];assert sorted(visible)==assembly['visibleMeshes'] and len(visible)==7
    assert 'RiderBody' in visible and all(any(n.startswith(p) for n in visible) for p in ('Boots__','Gloves__','Hoodie__','Jeans__'))
    bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
    rig=bpy.data.objects['RiderSkeleton'];body=bpy.data.objects['RiderBody']
    assert len(rig.data.bones)==75 and not rig.constraints and all(not b.constraints for b in rig.pose.bones)
    assert rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert set(visible)<={o.name for o in scene.objects}
    actual_visible=sorted(o.name for o in scene.objects if o.type=='MESH' and not o.hide_render)
    assert actual_visible==sorted(visible),('Wrong visible actual outfit',actual_visible)
    meshes=[bpy.data.objects[n] for n in visible];before_geometry={o.name:geometry(o) for o in meshes};before_rest=rest(rig)
    before_object_matrices={o.name:[list(r) for r in o.matrix_world] for o in meshes}
    # Shoulder/torso/arms remain static. This is deliberately restricted to the
    # actual neck chain, using measured native rest axes, never Euler guesses.
    names=[b.name for b in rig.data.bones];assert set(ACTIVE)<=set(names)
    assert bpy.data.actions.get(ACTION) is None,'Exact action name already exists; no fallback/suffix'
    for bone in rig.pose.bones:
        bone.rotation_mode='QUATERNION';bone.location=(0,0,0);bone.rotation_quaternion=(1,0,0,0);bone.scale=(1,1,1)
    bpy.context.view_layer.update()
    static_reference={n:rig.pose.bones[n].matrix.copy() for n in names if n not in ACTIVE}
    rest_frames={n:rig.data.bones[n].matrix_local.to_quaternion() for n in ACTIVE}
    action=bpy.data.actions.new(ACTION);rig.animation_data_create();rig.animation_data.action=action
    scene.render.fps=24;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=72
    observations=[];max_static_error=0.
    for frame in range(1,73):
        scene.frame_set(frame)
        for bone in rig.pose.bones:
            bone.location=(0,0,0);bone.rotation_quaternion=(1,0,0,0);bone.scale=(1,1,1)
        yaw,nod=angles(frame)
        for name,ys,ns in zip(ACTIVE,YAW_SHARES,NOD_SHARES):
            if yaw==0. and nod==0.:
                rig.pose.bones[name].rotation_quaternion=(1,0,0,0)
            else:
                q=Quaternion(Vector((0,0,1)),math.radians(yaw)*ys) @ Quaternion(Vector((1,0,0)),math.radians(nod)*ns)
                r=rest_frames[name];rig.pose.bones[name].rotation_quaternion=r.inverted() @ q @ r
        bpy.context.view_layer.update()
        for name,reference in static_reference.items():
            current=rig.pose.bones[name].matrix
            delta=max(abs(current[i][j]-reference[i][j]) for i in range(4) for j in range(4))
            max_static_error=max(max_static_error,delta);assert delta<=5e-7,('Non-neck bone moved',frame,name,delta)
        for name in names:
            bone=rig.pose.bones[name]
            for prop in ('location','rotation_quaternion','scale'):bone.keyframe_insert(data_path=prop,frame=frame,group=name)
        if frame in {s[0] for s in STATIONS}:
            observations.append({'frame':frame,'authoredTotalYawDegrees':yaw,'authoredTotalNodDegrees':nod,
                'headWorldMatrix':[list(r) for r in rig.pose.bones['DEF-spine.006'].matrix],
                'shoulderWorldMatrices':{n:[list(r) for r in rig.pose.bones[n].matrix] for n in ('DEF-shoulder.L','DEF-shoulder.R')}})
    assert action.slots and len(action.slots)==1,'Actual action slot required'
    # Every integer frame is explicitly authored. Linear channel interpolation
    # prevents an unobserved Bezier overshoot between those recorded frames.
    for layer in action.layers:
        for strip in layer.strips:
            bag=strip.channelbag(action.slots[0])
            if bag:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    samples={}
    for frame in (1,72):
        scene.frame_set(frame);bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
        samples[frame]={o.name:[v.co.copy() for v in o.evaluated_get(graph).data.vertices] for o in meshes}
    return_error=max((a-b).length for n in visible for a,b in zip(samples[1][n],samples[72][n]));assert return_error<=2e-6
    assert rest(rig)==before_rest and {o.name:geometry(o) for o in meshes}==before_geometry
    assert {o.name:[list(r) for r in o.matrix_world] for o in meshes}==before_object_matrices
    scene.frame_set(1);bpy.context.view_layer.update();assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    out.mkdir(parents=True);candidate=out/'clothed-neck-turn-nod72.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate),compress=True)
    result={'accepted':False,'status':'UNACCEPTED_CLOTHED_NECK_ACTION_SAVED_FOR_PLAYED_REVIEW',
      'candidate':{'path':str(candidate.relative_to(ROOT)),'sha256':sha(candidate)},
      'sourceMaster':config['masterNative'],'sourceAssemblyReceipt':config['assemblyReceipt'],'bodyReadback':config['bodyReadback'],
      'reviewedBodyNative':config['reviewedBodyNative'],'bodyConditionReceipt':config['bodyConditionReceipt'],
      'recipeSHA256':sha(__file__),'configSHA256':sha(config_path),'action':action.name,'actionSlot':action.slots[0].identifier,
      'fps':24,'frameRange':[1,72],'continuousFrames':72,'activeBones':list(ACTIVE),'resetAndTRSKeyedJointsEveryFrame':75,
      'stations':STATIONS,'yawShares':YAW_SHARES,'nodShares':NOD_SHARES,'all75RestRecordsUnchanged':True,
      'actualMeshPBRGeometryFieldsUnchanged':before_geometry,'visibleMeshes':visible,'nonNeckWorldMatrixMaxError':max_static_error,
      'neutralReturnEvaluatedVertexMaxErrorMetres':return_error,'observations':observations,
      'limits':['Parent judges actual continuous clothed clip; no art/motion gate passed.','Only head/neck stress sample; shoulder, grip, gait, jump, and bike motion not qualified.',
        'Actual working garments remain unaccepted; this action does not repair hoodie panels, glove grip, or jeans appearance.',
        'Rest-shape residual C7 bulge, right neck albedo patching, shading transition and hair texture seam remain open; endpoint conditioning itself has no moving acceptance.',
        'Body saved-normal residual remains governed by its independent readback; no normal waiver or player export.']}
    (out/'motion-report.json').write_text(json.dumps(result,indent=2)+'\n');assert sha(master)==config['masterNative']['sha256']
    print(json.dumps({'candidate':result['candidate'],'action':ACTION,'frames':72,'visibleMeshes':visible}))
if __name__=='__main__':main()
