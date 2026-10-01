"""One relaxed neutral anatomical hand assembly; no curl, bake or source remesh."""
import hashlib,json,math,time
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector,Matrix
REPO=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/neutral-assembly'
OUT=REPO/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True)
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
CAGES=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.perf_counter();source_sha=sha(SOURCE)
if (RUN/'body-neutral-hands.blend').exists():raise RuntimeError('Frozen neutral assembly exists')
hands=[]
for side in ['L','R']:
    path=CAGES/f'neutral-complete-{side}.npz';data=np.load(path)
    indices=data['polygonIndices'];offsets=data['polygonOffsets']
    faces=[indices[a:b].tolist() for a,b in zip(offsets[:-1],offsets[1:])]
    assert len(faces)==1656 and len(data['wristLoop'])==22
    hands.append({'side':side,'vertices':data['vertices'].copy(),'faces':faces,'wristLoop':data['wristLoop'].tolist(),'weights':data['nativeBoneWeights'].copy(),'boneNames':data['nativeBoneNames'].tolist(),'source':str(path),'sha256':sha(path)})
def loop_from_edges(edges):
    adj={}
    for e in edges:
        for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
    assert adj and all(len(x)==2 for x in adj.values())
    seed=min(adj,key=lambda v:(v.co.x,v.co.y,v.co.z));loop=[seed];prev=None;cur=seed
    while True:
        nxt=next(v for v in adj[cur] if v!=prev)
        if nxt==seed:break
        loop.append(nxt);prev,cur=cur,nxt;assert len(loop)<=len(adj)
    assert len(loop)==len(adj)
    return loop
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
def fingerprints(b,source_limit=None):
    rows=sorted(tuple(round(float(x),7) for x in v.co) for v in b.verts if protected(v) and (source_limit is None or v.index<source_limit))
    positions=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
    layer=b.loops.layers.uv.active;rows=[]
    for f in b.faces:
        if all(protected(v) and (source_limit is None or v.index<source_limit) for v in f.verts):rows.append(sorted(tuple(round(float(x),7) for x in list(l.vert.co)+list(l[layer].uv)) for l in f.loops))
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
source_vertex_count=len(vertices);patches=[];native_assignments=[]
for (sign,loop,centre),hand in zip(seams,hands):
    cx,cy,_=centre
    # Estimate clothed distal forearm axis from a narrow source slice; rigid
    # alignment changes the whole hand frame, never native finger articulation.
    section=bm.copy();height=.945
    bmesh.ops.bisect_plane(section,geom=list(section.verts)+list(section.edges)+list(section.faces),dist=1e-7,plane_co=(0,0,height),plane_no=(0,0,1))
    section_edges={e for e in section.edges if all(abs(v.co.z-height)<1e-5 for v in e.verts)}
    loops=[]
    while section_edges:
        seed_edge=section_edges.pop();connected={seed_edge};pending=[seed_edge]
        while pending:
            edge=pending.pop()
            for vertex in edge.verts:
                for adjacent in vertex.link_edges:
                    if adjacent in section_edges:section_edges.remove(adjacent);connected.add(adjacent);pending.append(adjacent)
        ring=loop_from_edges(connected);mean=sum((v.co for v in ring),Vector())/len(ring)
        if sign*mean.x>.25:loops.append((mean,ring))
    assert loops,'No isolated forearm cross section'
    proximalCentre,proximalLoop=min(loops,key=lambda item:(item[0]-centre).length_squared)
    proximalLoopCount=len(proximalLoop);proximalCentre=proximalCentre.copy();section.free()
    axis=(centre-proximalCentre).normalized()
    angle=Vector((0,0,-1)).angle(axis)
    assert angle<math.radians(40),'Unexpected forearm frame: stop before sewing'
    rotation=Vector((0,0,-1)).rotation_difference(axis).to_matrix()
    hv=np.array([rotation@Vector(p) for p in hand['vertices']])
    ring=hv[hand['wristLoop']];ring_centre=ring.mean(0)
    translation=np.array([cx-ring_centre[0],cy-ring_centre[1],CUT-.006-ring[:,2].max()])
    hv+=translation
    offset=len(vertices);vertices.extend(hv.tolist())
    newfaces=[[offset+i for i in f] for f in hand['faces']]
    faces.extend(newfaces);uvs.extend([[[vertices[i][0]+.5,vertices[i][2]] for i in f] for f in newfaces]);materials.extend([1]*len(newfaces))
    old=sorted([v.index for v in loop],key=lambda i:math.atan2(vertices[i][1]-cy,vertices[i][0]-cx))
    new=sorted([offset+i for i in hand['wristLoop']],key=lambda i:math.atan2(vertices[i][1]-cy,vertices[i][0]-cx))
    a=[math.atan2(vertices[i][1]-cy,vertices[i][0]-cx) for i in old]
    # A22vertex shared-index transition band gradually blends the source cuff
    # cross-section into the untouched native22edge wrist opening.
    mid=[]
    for idx in new:
        p=np.array(vertices[idx]);theta=math.atan2(p[1]-cy,p[0]-cx)
        bracket=next((k for k in range(len(old)) if a[k]<=theta<(a[(k+1)%len(old)]+(2*math.pi if k+1==len(old) else 0))),None)
        if bracket is None:bracket=len(old)-1;theta+=2*math.pi
        k=bracket;low=a[k];high=a[(k+1)%len(old)]+(2*math.pi if k+1==len(old) else 0)
        t=(theta-low)/(high-low);q=(1-t)*np.array(vertices[old[k]])+t*np.array(vertices[old[(k+1)%len(old)]])
        mid.append(len(vertices));vertices.append(((p+q)*.5).tolist())
    def add_face(f):
        faces.append(f);uvs.append([[vertices[i][0]+.5,vertices[i][2]] for i in f]);materials.append(1)
    for j in range(len(new)):add_face([new[j],new[(j+1)%len(new)],mid[(j+1)%len(mid)],mid[j]])
    b=[math.atan2(vertices[i][1]-cy,vertices[i][0]-cx) for i in mid]
    i=j=0;count=22
    while i<len(old) or j<len(mid):
        an=a[(i+1)%len(old)]+(2*math.pi if i+1>=len(old) else 0) if i<len(old) else float('inf')
        bn=b[(j+1)%len(mid)]+(2*math.pi if j+1>=len(mid) else 0) if j<len(mid) else float('inf')
        if an<bn:f=[old[i%len(old)],old[(i+1)%len(old)],mid[j%len(mid)]];i+=1
        else:f=[old[i%len(old)],mid[(j+1)%len(mid)],mid[j%len(mid)]];j+=1
        add_face(f);count+=1
    native_assignments.append({'side':hand['side'],'offset':offset,'weights':hand['weights'],'boneNames':hand['boneNames'],'wristVertices':old+mid})
    patches.append({'sign':sign,'nativeSide':hand['side'],'centre':list(centre),'neutralCageSource':hand['source'],'neutralCageSHA256':hand['sha256'],'nativeHandFaces':1656,'nativeHandVertices':1668,'anatomicalWristLoopVertices':22,'sourceWristLoopVertices':len(old),'sharedTransitionRingVertices':22,'seamFaces':count,'forearmAxis':list(axis),'forearmProximalCentroid':list(proximalCentre),'proximalPlaneLoopVertices':proximalLoopCount,'rigidAlignmentDegrees':math.degrees(angle),'rigidAlignmentMatrix':[list(row) for row in rotation],'translation':translation.tolist(),'bounds':[hv.min(0).tolist(),hv.max(0).tolist()],'nativeWeightSums':[float(hand['weights'].sum(1).min()),float(hand['weights'].sum(1).max())]})
bm.free()
mesh=bpy.data.meshes.new('Neutral anatomical hands sewn into NEW H21-4 body');mesh.from_pydata(vertices,[],faces);mesh.update();body.data=mesh
layer=mesh.uv_layers.new(name='PreservedSourceAndUnbakedNeutralGloveUV')
for f,p,mat in zip(mesh.polygons,uvs,materials):
    f.material_index=mat;f.use_smooth=True
    for li,value in zip(f.loop_indices,p):layer.data[li].uv=value
mesh.materials.append(material)
glove=bpy.data.materials.new('Neutral anatomical glove unbaked provisional');glove.use_nodes=True
bs=glove.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.057,.062,1);bs.inputs['Roughness'].default_value=.64;mesh.materials.append(glove)
for assignment in native_assignments:
    for col,name in enumerate(assignment['boneNames']):
        g=body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
        for vi in np.flatnonzero(assignment['weights'][:,col]>0):g.add([assignment['offset']+int(vi)],float(assignment['weights'][vi,col]),'REPLACE')
    g=body.vertex_groups.get('wrist.'+assignment['side']);g.add(assignment['wristVertices'],1,'REPLACE')
check=bmesh.new();check.from_mesh(mesh);check.verts.index_update();bmesh.ops.recalc_face_normals(check,faces=list(check.faces));check.to_mesh(mesh)
topology={'vertices':len(check.verts),'faces':len(check.faces),'boundaryEdges':sum(e.is_boundary for e in check.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in check.edges)}
print('NEUTRAL_SEWN_TOPOLOGY',json.dumps(topology),flush=True)
assert topology['boundaryEdges']==0 and topology['nonmanifoldEdges']==0
assert fingerprints(check,source_vertex_count)==(position_sha,uv_sha),'Protected original source positions/UV changed after sewing'
check.free();body.name='NEW_H21-4_neutral_anatomical_hands'
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'body-neutral-hands.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'body-neutral-hands.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
report={'status':'One neutral-hand body assembly; parent appearance/deformation judgment pending; no curl/bake','source':str(SOURCE),'sourceSHA256':source_sha,'sourceSHA256After':sha(SOURCE),'recipeSHA256':sha(Path(__file__)),'displayHeight':1.8,'sourceDisplayTransform':{'scale':float(scale),'translation':trans.tolist()},'sourceVertexPrefixCount':source_vertex_count,'protectedSourcePositionSHA256':position_sha,'protectedSourceUVSHA256':uv_sha,'protectedSourcePositionsVerifiedAfterFinal':True,'protectedSourceUVsVerifiedAfterFinal':True,'patches':patches,'topology':topology,'nativeFingerChainsCollapsedIntoGeometry':False,'nativeWeightsRetained':True,'files':{str(p):sha(p) for p in RUN.glob('*') if p.is_file()},'wallSeconds':time.perf_counter()-start,'limits':['Historical head/hair rejected; new head integration pending.','Source outside distal hand component and loopUV protected; globally recalculated normals not hashpreserved.','Neutral pose only; no finger curl/grip solve.','Native anatomical weights retained but no runtime rig/socket/physics adapter.','Unbaked provisional glove shader/UV; no game-ready character.']}
assert source_sha==sha(SOURCE)
for hand in hands:assert hand['sha256']==sha(Path(hand['source']))
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('NEUTRAL_ASSEMBLY_FROZEN',flush=True)
