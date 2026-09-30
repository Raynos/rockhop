"""Neutral MODEL anatomy evidence; native posing remains separately failed.

Reads fresh unposed anatomical source and retains interpolated native weights.
No rider source imports or finger flexion corrections.
"""
import hashlib,json,math
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy')
RUN=BASE/'neutral-anatomy';SOURCE=BASE/'fresh-anatomical-source.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
if (OUT/'report.json').exists():raise RuntimeError('Frozen neutral evidence exists')
before=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
base=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
assert all(b.rotation_quaternion.angle<1e-6 for b in arm.pose.bones),'Fresh source must be unposed'
group_names={g.index:g.name for g in base.vertex_groups};bone_names=list(arm.data.bones.keys())
bpy.context.view_layer.update();evaluated=base.evaluated_get(bpy.context.evaluated_depsgraph_get());native=evaluated.to_mesh()
new_objects=[];reports=[]
def loop(edges):
    adj={}
    for e in edges:
        for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
    assert adj and all(len(v)==2 for v in adj.values())
    first=next(iter(adj));ids=[first];prev=None;cur=first
    while True:
        nxt=next(v for v in adj[cur] if v!=prev)
        if nxt==first:break
        ids.append(nxt);prev,cur=cur,nxt
    assert len(ids)==len(adj)
    return ids
for side in ['L','R']:
    wrist=arm.data.bones[f'wrist.{side}'].head_local.copy()
    knuckles=[arm.data.bones[f'finger{i}-1.{side}'].head_local.copy() for i in range(2,6)]
    length=(sum(knuckles,Vector())/4-wrist).normalized()
    width=knuckles[0]-knuckles[-1];width=(width-length*width.dot(length)).normalized()
    normal=width.cross(length).normalized()
    if side=='R':normal.negate()
    frame=Matrix((width,normal,length))
    m=native.copy();bm=bmesh.new();bm.from_mesh(m)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=wrist-length*.017,plane_no=length,clear_inner=True)
    seed=min(bm.verts,key=lambda v:(v.co-(wrist+length*.07)).length_squared)
    selected={seed};pending=[seed]
    while pending:
        v=pending.pop()
        for e in v.link_edges:
            other=e.other_vert(v)
            if other not in selected:selected.add(other);pending.append(other)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in selected],context='VERTS')
    boundary=loop([e for e in bm.edges if e.is_boundary]);deform=bm.verts.layers.deform.active
    assert deform is not None,'Native hand weights must remain available'
    for v in bm.verts:
        local=frame@(v.co-wrist);v.co=(-local.x,-local.y,-local.z)
        if side=='R':v.co.x*=-1
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.verts.index_update()
    vertices=np.array([v.co for v in bm.verts]);faces=[[v.index for v in f.verts] for f in bm.faces]
    weights=np.zeros((len(vertices),len(bone_names)))
    bone_column={name:i for i,name in enumerate(bone_names)}
    for v in bm.verts:
        for gid,weight in v[deform].items():
            name=group_names[gid]
            if name in bone_column:weights[v.index,bone_column[name]]=weight
    topology={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdgesBeyondWrist':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'wristBoundaryVertices':len(boundary)}
    assert topology['boundaryEdges']==len(boundary) and topology['nonmanifoldEdgesBeyondWrist']==0
    np.savez(RUN/f'neutral-hand-{side}.npz',vertices=vertices,quadFaces=np.array([f for f in faces if len(f)==4]),triFaces=np.array([f for f in faces if len(f)==3]),wristLoop=np.array([v.index for v in boundary]),nativeBoneWeights=weights,nativeBoneNames=np.array(bone_names))
    bm.to_mesh(m);bm.free();m.update();obj=bpy.data.objects.new(f'NEW neutral anatomical hand {side}',m);bpy.context.scene.collection.objects.link(obj)
    for col,name in enumerate(bone_names):
        vg=obj.vertex_groups.new(name=name)
        for vi in np.flatnonzero(weights[:,col]>0):vg.add([int(vi)],float(weights[vi,col]),'REPLACE')
    for f in m.polygons:f.use_smooth=True
    # Smoothing is a non-destructive display modifier; original cage/weights retained.
    sub=obj.modifiers.new('Neutral anatomical display smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
    reports.append({'side':side,'topology':topology,'bounds':[vertices.min(0).tolist(),vertices.max(0).tolist()],'nativeWeightSums':[float(weights.sum(1).min()),float(weights.sum(1).max())],
                    'nativeFrame':{'wrist':list(wrist),'width':list(width),'normal':list(normal),'length':list(length)},'nativeBones':bone_names,'nativeNPZ':str(RUN/f'neutral-hand-{side}.npz')})
    new_objects.append(obj)
evaluated.to_mesh_clear()
for o in list(bpy.context.scene.objects):
    if o not in new_objects:bpy.data.objects.remove(o,do_unlink=True)
gray=bpy.data.materials.new('Neutral MODEL anatomy gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
for o in new_objects:o.data.materials.clear();o.data.materials.append(gray)
world=bpy.data.worlds.new('Same studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;bpy.context.scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,-.08))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Neutral hand camera');camera=bpy.data.objects.new(cd.name,cd);bpy.context.scene.collection.objects.link(camera);bpy.context.scene.camera=camera;cd.type='ORTHO';cd.ortho_scale=.29
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
views=[]
for obj,report in zip(new_objects,reports):
    for o in new_objects:o.hide_render=o!=obj
    for label,yaw in [('front',0),('profile',90 if report['side']=='L' else 270),('back',180)]:
        target=Vector((0,0,-.09));angle=math.radians(yaw);camera.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        path=RUN/f'neutral-{report["side"]}-{label}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);views.append({'side':report['side'],'view':label,'file':str(path),'sha256':sha(path)})
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());display=evaluated.to_mesh();display.calc_loop_triangles()
    vs=[v.co.copy() for v in display.vertices];tris=[list(t.vertices) for t in display.loop_triangles]
    bvh=BVHTree.FromPolygons(vs,tris,all_triangles=True)
    pairs=[(a,b) for a,b in bvh.overlap(bvh) if a<b and not(set(tris[a])&set(tris[b]))]
    report['neutralDisplayNonadjacentBVHOverlapPairs']=len(pairs)
    report['neutralDisplayFirstOverlapPairs']=pairs[:100]
    evaluated.to_mesh_clear()
for o in new_objects:o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'neutral-anatomical-hands.blend'))
assert before==sha(SOURCE)
(OUT/'report.json').write_text(json.dumps({'status':'NEUTRAL MODEL evidence; parent judgment pending; curl/contacts separately unaccepted','source':str(SOURCE),'sourceSHA256':before,'sourceSHA256After':sha(SOURCE),'recipeSHA256':sha(Path(__file__)),'hands':reports,'views':views,'threads':4,'limits':['One expected open wrist loop per template, not a body join.','Native source skin topology and weights retained; no curl or bake.','No final19bone adapter or actual bike contact.','BVH overlap diagnostic excludes shared-vertex triangle neighbors.']},indent=2)+'\n')
print('NEUTRAL_HAND_MODEL_EVIDENCE_FROZEN',flush=True)
