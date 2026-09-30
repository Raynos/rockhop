"""Fresh anatomical MPFB hands, fixed native finger curl, sewn H21-4 wrists.

Source rider bytes/legs/clothes untouched; CPU only, no bake or voxel union.
"""
import hashlib,json,math,time
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector,Matrix,Quaternion
REPO=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/mpfb-trial2'
OUT=REPO/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.perf_counter(); source_sha=sha(SOURCE)
if (RUN/'body-gloves.blend').exists():raise RuntimeError('Frozen derivative exists')
bpy.ops.wm.open_mainfile(filepath=str(RUN/'fresh-anatomical-source.blend'))
base=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
native=[]
for side in ['L','R']:
    bones=arm.data.bones
    wrist=bones[f'wrist.{side}'].head_local.copy()
    knuckles=[bones[f'finger{i}-1.{side}'].head_local.copy() for i in range(2,6)]
    longitudinal=(sum(knuckles,Vector())/4-wrist).normalized()
    lateral=knuckles[0]-knuckles[-1]; lateral=(lateral-longitudinal*lateral.dot(longitudinal)).normalized()
    normal=lateral.cross(longitudinal).normalized()
    rotations={}
    for finger in range(1,6):
        angles=[22,38,20] if finger==1 else [35,62,35]
        for joint,angle in enumerate(angles,1):
            name=f'finger{finger}-{joint}.{side}';b=bones[name];pb=arm.pose.bones[name]
            axis=b.matrix_local.to_3x3().inverted()@lateral
            pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(axis.normalized(),math.radians(angle))
            rotations[name]={'degrees':angle,'localAxis':list(axis.normalized())}
    native.append({'side':side,'wrist':wrist,'longitudinal':longitudinal,'lateral':lateral,'normal':normal,'rotations':rotations})
bpy.context.view_layer.update()
evaluated=base.evaluated_get(bpy.context.evaluated_depsgraph_get()); posed=evaluated.to_mesh()
posed_vertices=[evaluated.matrix_world@v.co for v in posed.vertices]
posed_faces=[list(f.vertices) for f in posed.polygons]
hands=[]
def loop_from_edges(edges):
    adj={}
    for e in edges:
        for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
    assert adj and all(len(x)==2 for x in adj.values()),'Not one regular closed boundary'
    seed=min(adj,key=lambda v:(v.co.x,v.co.y,v.co.z));loop=[seed];prev=None;cur=seed
    while True:
        nxt=next(v for v in adj[cur] if v!=prev)
        if nxt==seed:break
        loop.append(nxt);prev,cur=cur,nxt;assert len(loop)<=len(adj)
    assert len(loop)==len(adj),'Multiple hand wrist boundaries'
    return loop
for info in native:
    m=bpy.data.meshes.new('Fresh posed native hand extraction');m.from_pydata(posed_vertices,[],posed_faces);m.update()
    bm=bmesh.new();bm.from_mesh(m)
    origin=info['wrist'];longitudinal=info['longitudinal']
    plane=origin-longitudinal*.017
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=plane,plane_no=longitudinal,clear_inner=True)
    seed=min(bm.verts,key=lambda v:(v.co-(origin+longitudinal*.07)).length_squared)
    connected={seed};pending=[seed]
    while pending:
        v=pending.pop()
        for e in v.link_edges:
            other=e.other_vert(v)
            if other not in connected:connected.add(other);pending.append(other)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in connected],context='VERTS')
    loop=loop_from_edges([e for e in bm.edges if e.is_boundary])
    # Canonical hand frame: width toward thumb, length distal, palm forward.
    frame=Matrix((info['lateral'],info['normal'],info['longitudinal']))
    for v in bm.verts:
        local=frame@(v.co-origin)
        v.co=(-local.x,-local.y,-local.z)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
    obj=bpy.data.objects.new('Fresh anatomical hand, native curl collapsed',m);bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    sub=obj.modifiers.new('Local anatomical hand subdivision','SUBSURF');sub.levels=1
    bpy.ops.object.modifier_apply(modifier=sub.name)
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for v in bm.verts:v.co+=v.normal*.0009
    bm.verts.index_update()
    loop=loop_from_edges([e for e in bm.edges if e.is_boundary])
    vv=np.array([v.co for v in bm.verts]);ff=[[v.index for v in f.verts] for f in bm.faces]
    native_side=info['side']
    np.savez(RUN/f'new-anatomical-hand-{native_side}.npz',vertices=vv,quadFaces=np.array([f for f in ff if len(f)==4]),triFaces=np.array([f for f in ff if len(f)==3]),wristLoop=np.array([v.index for v in loop]))
    hands.append({'side':native_side,'vertices':vv,'faces':ff,'wristLoop':[v.index for v in loop],
                  'nativeFrame':{k:list(info[k]) for k in ['wrist','longitudinal','lateral','normal']},'rotations':info['rotations']})
    bm.free()
evaluated.to_mesh_clear()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE));bpy.context.view_layer.update()
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');material=list(body.data.materials)[0]
points=np.array([body.matrix_world@v.co for v in body.data.vertices]);lo,hi=points.min(0),points.max(0)
scale=1.8/(hi[2]-lo[2]);trans=np.array([-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]])*scale
for v,p in zip(body.data.vertices,points):v.co=p*scale+trans
body.parent=None;body.matrix_world=Matrix.Identity(4)
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
uv=bm.loops.layers.uv.active
def protected(v):return abs(v.co.x)<.24 or v.co.z>=.92 or v.co.z<.70
def fingerprints(b):
    rows=sorted(tuple(round(float(x),7) for x in v.co) for v in b.verts if protected(v))
    positions=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
    layer=b.loops.layers.uv.active;rows=[]
    for f in b.faces:
        if all(protected(v) for v in f.verts):rows.append(sorted(tuple(round(float(x),7) for x in list(l.vert.co)+list(l[layer].uv)) for l in f.loops))
    return positions,hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
position_sha,uv_sha=fingerprints(bm)
seams=[];CUT=.900
for sign in [1,-1]:
    selected=[v for v in bm.verts if sign*v.co.x>.26 and .70<v.co.z<.95]
    eligible=set(selected);faces=[f for f in bm.faces if all(v in eligible for v in f.verts)]
    bmesh.ops.bisect_plane(bm,geom=list(set(selected)|set(faces)|set(e for f in faces for e in f.edges)),dist=1e-7,plane_co=(0,0,CUT),plane_no=(0,0,1))
    candidates={v for v in bm.verts if .70<v.co.z<CUT-1e-7}
    seed=min((v for v in candidates if sign*v.co.x>.30),key=lambda v:(v.co-Vector((sign*.35,-.02,.83))).length_squared)
    distal={seed};pending=[seed]
    while pending:
        v=pending.pop()
        for e in v.link_edges:
            other=e.other_vert(v)
            if other in candidates and other not in distal:distal.add(other);pending.append(other)
    assert all(sign*v.co.x>.25 for v in distal)
    bmesh.ops.delete(bm,geom=list(distal),context='VERTS')
    loop=loop_from_edges([e for e in bm.edges if e.is_boundary and all(sign*v.co.x>.285 and abs(v.co.z-CUT)<1e-5 for v in e.verts)])
    centre=sum((v.co for v in loop),Vector())/len(loop)
    seams.append((sign,loop,centre))
assert fingerprints(bm)==(position_sha,uv_sha),'Protected source body/UV changed'
bm.verts.index_update();vertices=[list(v.co) for v in bm.verts];faces=[[v.index for v in f.verts] for f in bm.faces]
uvs=[[list(l[uv].uv) for l in f.loops] for f in bm.faces];materials=[f.material_index for f in bm.faces]
patches=[]
for (sign,loop,centre),hand in zip(seams,hands):
    cx,cy,_=centre;hv=hand['vertices'].copy()
    if sign<0:hv[:,0]*=-1
    # Retain native anatomical proportions. Wrist sits18mm below sewn cut.
    hv+=np.array([cx,cy,.864])
    offset=len(vertices);vertices.extend(hv.tolist());newfaces=[[offset+i for i in f] for f in hand['faces']]
    faces.extend(newfaces);uvs.extend([[[vertices[i][0]+.5,vertices[i][2]] for i in f] for f in newfaces]);materials.extend([1]*len(newfaces))
    old=sorted([v.index for v in loop],key=lambda i:math.atan2(vertices[i][1]-cy,vertices[i][0]-cx))
    new=sorted([offset+i for i in hand['wristLoop']],key=lambda i:math.atan2(vertices[i][1]-cy,vertices[i][0]-cx))
    a=[math.atan2(vertices[i][1]-cy,vertices[i][0]-cx) for i in old];b=[math.atan2(vertices[i][1]-cy,vertices[i][0]-cx) for i in new]
    i=j=0;count=0
    while i<len(old) or j<len(new):
        an=a[(i+1)%len(old)]+(2*math.pi if i+1>=len(old) else 0) if i<len(old) else float('inf')
        bn=b[(j+1)%len(new)]+(2*math.pi if j+1>=len(new) else 0) if j<len(new) else float('inf')
        if an<bn:f=[old[i%len(old)],old[(i+1)%len(old)],new[j%len(new)]];i+=1
        else:f=[old[i%len(old)],new[(j+1)%len(new)],new[j%len(new)]];j+=1
        faces.append(f);uvs.append([[vertices[k][0]+.5,vertices[k][2]] for k in f]);materials.append(1);count+=1
    patches.append({'sign':sign,'centre':list(centre),'nativeSide':hand['side'],'nativeFrame':hand['nativeFrame'],'fixedNativeFingerRotations':hand['rotations'],'nativeHandFaces':len(hand['faces']),'sourceWristLoopVertices':len(old),'anatomicalWristLoopVertices':len(new),'seamFaces':count,'gripVolumeDiameterMeters':.022,'gripVolumeCentre':[cx,cy-.031,.770],'gripVolumeAxis':'canonical X lateral; visual fitting hypothesis, not bike contact pass'})
bm.free()
mesh=bpy.data.meshes.new('Fresh anatomical glove patches sewn into H21-4');mesh.from_pydata(vertices,[],faces);mesh.update();body.data=mesh
layer=mesh.uv_layers.new(name='PreservedSourceAndUnbakedGloveUV')
for f,p,mat in zip(mesh.polygons,uvs,materials):
    f.material_index=mat;f.use_smooth=True
    for li,value in zip(f.loop_indices,p):layer.data[li].uv=value
mesh.materials.append(material)
glove=bpy.data.materials.new('Unbaked anatomical glove provisional PBR');glove.use_nodes=True
bs=glove.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.057,.062,1);bs.inputs['Roughness'].default_value=.64;mesh.materials.append(glove)
check=bmesh.new();check.from_mesh(mesh);bmesh.ops.recalc_face_normals(check,faces=list(check.faces));check.to_mesh(mesh)
topology={'vertices':len(check.verts),'faces':len(check.faces),'boundaryEdges':sum(e.is_boundary for e in check.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in check.edges)}
print('ANATOMICAL_SEWN_TOPOLOGY',json.dumps(topology),flush=True)
assert topology['boundaryEdges']==0 and topology['nonmanifoldEdges']==0,'Anatomical sewing failed manifold gate'
assert fingerprints(check)==(position_sha,uv_sha),'Protected source body/UV changed after final sewing'
check.free();body.name='H21-4_new_anatomical_glove_trial2'
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'body-gloves.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'body-gloves.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
report={'status':'UNACCEPTED second glove appearance correction, parent gray judgment required','source':str(SOURCE),'sourceSHA256':source_sha,'sourceSHA256After':sha(SOURCE),'freshMPFBSourceSHA256':sha(RUN/'fresh-anatomical-source.blend'),'recipeSHA256':sha(Path(__file__)),'displayHeight':1.8,'sourceDisplayTransform':{'scale':float(scale),'translation':trans.tolist()},'protectedSourcePositionSHA256':position_sha,'protectedSourceUVSHA256':uv_sha,'protectedSourcePositionsVerifiedAfterFinal':True,'protectedSourceUVsVerifiedAfterFinal':True,'patches':patches,'topology':topology,'nativeFingerChainsCollapsedIntoGeometry':True,'files':{str(p):sha(p) for p in RUN.glob('*') if p.is_file()},'wallSeconds':time.perf_counter()-start,'limits':['Anatomical source freshly instantiated from CC0 installed base; no historical donor.','No texture bake; glove UV/shader provisional.','Native finger rig only authoring aid; final19bone rider adapter not present.','22mm grip cage is visual fitting target; visible gameplay contact unverified.']}
assert source_sha==sha(SOURCE)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('FRESH_ANATOMICAL_GLOVE_DERIVATIVE_FROZEN',flush=True)
