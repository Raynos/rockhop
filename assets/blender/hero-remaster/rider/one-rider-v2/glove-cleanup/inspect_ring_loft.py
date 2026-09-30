"""Read-only CPU gray/PBR inspection and temporary sewn-wrist motion.

No texture bake, full character rig or gameplay contact claim.
"""
import hashlib, json, math, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/ring-loft-trial1'
OUT=REPO/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'inspection.json').exists():raise RuntimeError('Frozen inspection exists')
started=time.perf_counter(); build=json.loads((OUT/'report.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(RUN/'body-gloves.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bm=bmesh.new(); bm.from_mesh(body.data); uv=bm.loops.layers.uv.active
def protected(v):return abs(v.co.x)<.24 or v.co.z>=.92 or v.co.z<.70
rows=sorted(tuple(round(float(x),7) for x in v.co) for v in bm.verts if protected(v))
position_sha=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
rows=[]
for f in bm.faces:
    if all(protected(v) for v in f.verts):rows.append(sorted(tuple(round(float(x),7) for x in list(l.vert.co)+list(l[uv].uv)) for l in f.loops))
uv_sha=hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
assert position_sha==build['protectedSourcePositionSHA256'],'Protected positions changed after mesh export'
assert uv_sha==build['protectedSourceUVSHA256'],'Protected face-loop UV changed after mesh construction'
components=[]; unvisited=set(bm.verts)
while unvisited:
    seed=unvisited.pop(); pending=[seed]; count=1
    while pending:
        v=pending.pop()
        for e in v.link_edges:
            other=e.other_vert(v)
            if other in unvisited:unvisited.remove(other);pending.append(other);count+=1
    components.append(count)
bm.free()
mesh=body.data; mesh.calc_loop_triangles()
vs=np.array([v.co for v in mesh.vertices]); tris=np.array([t.vertices for t in mesh.loop_triangles])
new_tri=np.array([t.material_index==1 for t in mesh.loop_triangles])
bvh=BVHTree.FromPolygons([Vector(p) for p in vs],tris.tolist(),all_triangles=True)
broad=bvh.overlap(bvh)
def intersects(a,b):
    ea=np.array([a[1]-a[0],a[2]-a[1],a[0]-a[2]]); eb=np.array([b[1]-b[0],b[2]-b[1],b[0]-b[2]])
    na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1]);axes=[na,nb]
    axes.extend(np.cross(x,y) for x in ea for y in eb)
    axes.extend(np.cross(na,x) for x in ea);axes.extend(np.cross(nb,x) for x in eb)
    for axis in axes:
        n=np.linalg.norm(axis)
        if n<1e-14:continue
        axis=axis/n; pa=a@axis;pb=b@axis
        if pa.max()<pb.min()-1e-7 or pb.max()<pa.min()-1e-7:return False
    return True
overlaps=[]; examined=0
for a,b in broad:
    if a>=b or not (new_tri[a] or new_tri[b]) or set(tris[a])&set(tris[b]):continue
    examined+=1
    if intersects(vs[tris[a]],vs[tris[b]]):
        overlaps.append({'triangleA':a,'triangleB':b,'centres':[vs[tris[a]].mean(0).tolist(),vs[tris[b]].mean(0).tolist()]})
scene=bpy.context.scene
world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Matched glove diagnostic');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
gray=bpy.data.materials.new('Geometry diagnostic gray');gray.use_nodes=True;bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
original=list(mesh.materials)
views=[]
def aim(target,yaw,ortho):
    cd.ortho_scale=ortho;target=Vector(target);angle=math.radians(yaw)
    cam.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for mode in ['gray','pbr']:
    mesh.materials.clear()
    for m in ([gray,gray] if mode=='gray' else original):mesh.materials.append(m)
    for side in [1,-1]:
        centre=next(p['centre'] for p in build['patches'] if p['sign']==side)
        for label,yaw in [('front',0),('profile',90 if side==1 else 270),('back',180)]:
            aim((centre[0],centre[1]-.02,.850),yaw,.27)
            p=RUN/f'glove-{side}-{label}-{mode}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
            views.append({'side':side,'view':label,'yaw':yaw,'mode':mode,'file':str(p),'sha256':sha(p)})
# Temporary two-bone-per-arm diagnostic; not the final19-bone rig or IK.
mesh.materials.clear()
for m in original:mesh.materials.append(m)
armdata=bpy.data.armatures.new('Temporary sewn-wrist diagnostic only');arm=bpy.data.objects.new(armdata.name,armdata);scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
root=armdata.edit_bones.new('diagnosticRoot');root.head=(0,0,0);root.tail=(0,0,.2)
for sign in [1,-1]:
    c=Vector(next(p['centre'] for p in build['patches'] if p['sign']==sign))
    f=armdata.edit_bones.new(f'diagnosticForearm{sign}');f.head=(sign*.29,c.y,1.145);f.tail=c;f.parent=root
    h=armdata.edit_bones.new(f'diagnosticHand{sign}');h.head=c;h.tail=(c.x,c.y,.830);h.parent=f;h.use_connect=True
bpy.ops.object.mode_set(mode='OBJECT')
groups={name:body.vertex_groups.new(name=name) for name in armdata.bones.keys()}
for v in mesh.vertices:
    x,y,z=v.co; sign=1 if x>0 else -1
    if abs(x)>.25 and .70<z<1.19:
        forearm=max(0,min(1,(1.19-z)/.08));hand=max(0,min(1,(.930-z)/.060))
        hand=hand*hand*(3-2*hand)
        groups[f'diagnosticHand{sign}'].add([v.index],forearm*hand,'REPLACE')
        groups[f'diagnosticForearm{sign}'].add([v.index],forearm*(1-hand),'REPLACE')
        groups['diagnosticRoot'].add([v.index],1-forearm,'REPLACE')
    else:groups['diagnosticRoot'].add([v.index],1,'REPLACE')
mod=body.modifiers.new('Temporary seam deformation only','ARMATURE');mod.object=arm
scene.frame_start=0;scene.frame_end=35;scene.render.fps=12
motion=[]
for frame in range(36):
    phase=frame/35*2*math.pi
    for sign in [1,-1]:
        f=arm.pose.bones[f'diagnosticForearm{sign}'];h=arm.pose.bones[f'diagnosticHand{sign}']
        f.rotation_mode='XYZ';h.rotation_mode='XYZ'
        f.rotation_euler=(math.radians(18)*math.sin(phase),0,math.radians(12)*math.sin(phase))
        h.rotation_euler=(math.radians(30)*math.sin(phase),math.radians(40)*math.sin(phase*2),0)
        f.keyframe_insert(data_path='rotation_euler',frame=frame);h.keyframe_insert(data_path='rotation_euler',frame=frame)
    scene.frame_set(frame);bpy.context.view_layer.update()
    for side in [1,-1]:
        c=Vector(next(p['centre'] for p in build['patches'] if p['sign']==side))
        aim((c.x,c.y-.01,.925),45 if side==1 else 315,.48)
        p=RUN/f'motion-{side}-{frame:04d}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        motion.append({'frame':frame,'side':side,'seconds':frame/12,'file':str(p),'sha256':sha(p),'wristFlexDegrees':30*math.sin(phase),'wristTwistDegrees':40*math.sin(phase*2),'forearmFlexDegrees':18*math.sin(phase)})
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'temporary-wrist-diagnostic.blend'))
inspection={'status':'static/motion evidence only; no parent acceptance or gameplay contact','recipeSHA256':sha(Path(__file__)),'blender':bpy.app.version_string,'backend':'Cycles CPU','threads':4,'samples':24,'componentVertexCounts':components,'protectedSourcePositionSHA256AfterFinal':position_sha,'protectedSourceUVSHA256AfterFinal':uv_sha,'sourcePreservationVerifiedAfterFinal':True,'triangles':len(tris),'intersectionDiagnostic':{'method':'BVH broadphase plus triangle SAT, tolerance1e-7m; pairs sharing any vertex excluded','nonadjacentCandidatePairsExamined':examined,'trianglePairsIncludingTouching':len(overlaps),'firstPairs':overlaps[:200],'limits':'Tolerance includes touching; does not measure glove-bike fit or deformed self-intersections.'},'views':views,'motion':motion,'temporaryRig':'diagnostic root plus2bones perarm only; no final19bone bind/socket/IK','wallSeconds':time.perf_counter()-started}
(OUT/'inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
print('GLOVE_INSPECTION_DONE',len(overlaps),'triangle overlaps',flush=True)
