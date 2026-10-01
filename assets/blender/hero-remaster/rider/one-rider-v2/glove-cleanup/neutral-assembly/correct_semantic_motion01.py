"""One semantic diagnostic weight correction; immutable anatomy/native weights."""
import hashlib,json,math,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/neutral-assembly'
PARENT=ROOT/'docs/evidence/hero-remaster'/BASE
OUT=PARENT/'motion-correction01';OUT.mkdir(exist_ok=True)
SOURCE_RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
RUN=SOURCE_RUN/'motion-correction01';RUN.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'report.json').exists():raise RuntimeError('Frozen correction exists')
start=time.perf_counter();clean=SOURCE_RUN/'body-neutral-hands.blend';failed=SOURCE_RUN/'temporary-wrist-diagnostic.blend'
sources={str(p):sha(p) for p in [clean,failed]}
build=json.loads((PARENT/'report.json').read_text());proof=json.loads((PARENT/'native-weight-proof.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(failed));old=next(o for o in bpy.context.scene.objects if o.type=='MESH');oldarm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
bone_names=list(oldarm.data.bones.keys());columns={name:i for i,name in enumerate(bone_names)}
weights=np.zeros((len(old.data.vertices),len(bone_names)));group_names={g.index:g.name for g in old.vertex_groups}
for v in old.data.vertices:
    for g in v.groups:
        name=group_names[g.group]
        if name in columns:weights[v.index,columns[name]]=g.weight
bone_defs=[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'connect':b.use_connect} for b in oldarm.data.bones]
bpy.ops.wm.open_mainfile(filepath=str(clean));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=body.data
rest=np.array([v.co[:] for v in mesh.vertices]);original_materials=[p.material_index for p in mesh.polygons]
native_names={g.index:g.name for g in body.vertex_groups};source_limit=build['sourceVertexPrefixCount'];semantics=[]
for hand in proof['hands']:
    side=hand['side'];sign=1 if side=='L' else -1;first=hand['firstNativeVertexIndex'];last=first+hand['nativeVertices']
    native=list(range(first,last));transition=list(range(last,last+22))
    wrist=[v.index for v in mesh.vertices[:source_limit] if any(native_names[g.group]=='wrist.'+side and g.weight>.999 for g in v.groups)]
    assert len(wrist)==(62 if sign==1 else 65)
    hand_col=columns[f'diagnosticHand{sign}'];arm_col=columns[f'diagnosticForearm{sign}']
    weights[native]=0;weights[native,hand_col]=1
    weights[wrist]=0;weights[wrist,arm_col]=1
    weights[transition]=0;weights[transition,hand_col]=.5;weights[transition,arm_col]=.5
    edges=[list(e.vertices) for e in mesh.edges if all(first<=i<last for i in e.vertices)]
    semantics.append({'side':side,'sign':sign,'native':native,'transition':transition,'sourceWrist':wrist,'edges':edges})
assert np.allclose(weights.sum(1),1,atol=1e-6,rtol=0)
armdata=bpy.data.armatures.new('Corrected semantic seam diagnostic only');arm=bpy.data.objects.new(armdata.name,armdata);bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for definition in bone_defs:
    bone=armdata.edit_bones.new(definition['name']);bone.head=definition['head'];bone.tail=definition['tail']
    if definition['parent']:bone.parent=armdata.edit_bones[definition['parent']]
    bone.use_connect=definition['connect']
bpy.ops.object.mode_set(mode='OBJECT')
for name,col in columns.items():
    group=body.vertex_groups.new(name=name)
    for vi in np.flatnonzero(weights[:,col]>0):group.add([int(vi)],float(weights[vi,col]),'REPLACE')
mod=body.modifiers.new('Semantic seam diagnostic only','ARMATURE');mod.object=arm
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.frame_start=0;scene.frame_end=35;scene.render.fps=12
gray=bpy.data.materials.new('Corrected semantic geometry gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
scene.view_layers[0].material_override=gray
world=bpy.data.worlds.new('Matched gray studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Matched semantic motion');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
def aim(target,yaw,ortho):
    cd.ortho_scale=ortho;target=Vector(target);angle=math.radians(yaw);cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
motion=[];closeups=[];edge_checks=[]
for frame in range(36):
    phase=frame/35*2*math.pi
    for sign in [1,-1]:
        forearm=arm.pose.bones[f'diagnosticForearm{sign}'];hand=arm.pose.bones[f'diagnosticHand{sign}'];forearm.rotation_mode='XYZ';hand.rotation_mode='XYZ'
        forearm.rotation_euler=(math.radians(18)*math.sin(phase),0,math.radians(12)*math.sin(phase));hand.rotation_euler=(math.radians(30)*math.sin(phase),math.radians(40)*math.sin(phase*2),0)
        forearm.keyframe_insert(data_path='rotation_euler',frame=frame);hand.keyframe_insert(data_path='rotation_euler',frame=frame)
    scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());deformed=ev.to_mesh();posed=np.array([v.co[:] for v in deformed.vertices])
    for semantic in semantics:
        side=semantic['side'];sign=semantic['sign'];edges=np.array(semantic['edges']);before=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);after=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1);valid=before>.001
        absolute=float(abs(after-before).max());ratio=float((after[valid]/before[valid]).max());assert absolute<1e-6 and ratio<1.001,'Native finger edge stretch: stop correction'
        edge_checks.append({'frame':frame,'side':side,'nativeEdgeCount':len(edges),'maximumAbsoluteEdgeLengthErrorM':absolute,'maximumEdgeRatioForRestOver1mm':ratio})
        centre=next(p['centre'] for p in build['patches'] if p['sign']==sign);aim((centre[0],centre[1]-.01,.810),45 if sign==1 else 315,.62)
        path=RUN/f'motion-{sign}-{frame:04d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);motion.append({'frame':frame,'side':sign,'file':str(path),'sha256':sha(path),'wristFlexDegrees':30*math.sin(phase),'wristTwistDegrees':40*math.sin(phase*2)})
        if frame in [4,9,10,13,26,31]:
            target=posed[semantic['sourceWrist']].mean(0);aim(target,45 if sign==1 else 315,.26)
            path=RUN/f'wrist-{sign}-{frame:04d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);closeups.append({'frame':frame,'side':sign,'file':str(path),'sha256':sha(path)})
    ev.to_mesh_clear()
assert original_materials==[p.material_index for p in mesh.polygons]
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'semantic-wrist-diagnostic.blend'))
assert sources=={p:sha(Path(p)) for p in sources}
report={'status':'One diagnostic correction; parent moving appearance judgment pending; no bake','correctedFailure':'Material-slot clearing erased semantic mask, leaving125distalfinger vertices on root. This copy uses immutable hand ranges/actual source wrist and transition sets; no spatial/material hand fallback.','sourceFilesSHA256Before':sources,'sourceFilesSHA256After':{p:sha(Path(p)) for p in sources},'semantics':[{'side':s['side'],'nativeVertexCount':len(s['native']),'nativeVertexRange':[min(s['native']),max(s['native'])],'sourceWristVertices':s['sourceWrist'],'transitionVertices':s['transition'],'allNativeHandDiagnosticWeight':1,'rootOrOppositeHandNativeVertices':0} for s in semantics],'nativeGroupsUntouched':True,'originalMaterialIndicesPreserved':True,'grayRendering':'scene material_override only; never clear indexedslots','weightsTotalRange':[float(weights.sum(1).min()),float(weights.sum(1).max())],'edgeChecks':edge_checks,'motion':motion,'closeups':closeups,'threads':4,'backend':'Cycles CPU','masterSHA256':sha(RUN/'semantic-wrist-diagnostic.blend'),'recipeSHA256':sha(Path(__file__)),'wallSeconds':time.perf_counter()-start,'limits':['Nativehand edgechecks establish rigidshape preservation only, not deformedcollision/hand-bike contacts.','Temporary5bone localdiagnostic, no final19bone adapter/physics/Garage/lean/landing.','No bake, new headintegration or normalplayerasset promotion.']}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('SEMANTIC_WRIST_CORRECTION_EVIDENCE_FROZEN',flush=True)
