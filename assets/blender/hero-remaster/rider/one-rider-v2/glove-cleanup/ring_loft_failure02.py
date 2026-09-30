"""Explicit sewn glove branches; one bounded CPU-only isolated trial.

Each finger and thumb starts at a genuine palm hole's shared vertex IDs.
No voxel union, intersecting closed primitives, bake or source remesh.
"""
import hashlib, json, math, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

REPO=Path('/Users/raynos/projects/games/rockhop')
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
BASE='one-rider-v2/glove-cleanup/ring-loft-trial1'
OUT=REPO/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
CUT=.900
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(SOURCE); started=time.perf_counter()
OUT.mkdir(parents=True,exist_ok=True); RUN.mkdir(parents=True,exist_ok=True)
if (OUT/'report.json').exists(): raise RuntimeError('Frozen ring-loft trial exists')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE)); bpy.context.view_layer.update()
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
points=np.array([body.matrix_world@v.co for v in body.data.vertices]); lo,hi=points.min(0),points.max(0)
scale=1.8/(hi[2]-lo[2]); trans=np.array([-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]])*scale
for v,p in zip(body.data.vertices,points):v.co=p*scale+trans
body.parent=None; body.matrix_world=Matrix.Identity(4)
bm=bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
uv=bm.loops.layers.uv.active
def protected(v): return abs(v.co.x)<.28 or v.co.z>=.92
def vertex_fingerprint(b):
    rows=sorted(tuple(round(float(x),7) for x in v.co) for v in b.verts if protected(v))
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
def uv_fingerprint(b):
    rows=[]
    for f in b.faces:
        if all(protected(v) for v in f.verts):
            rows.append(sorted(tuple(round(float(x),7) for x in list(l.vert.co)+list(l[uv].uv)) for l in f.loops))
    return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()
positions_before=vertex_fingerprint(bm); uvs_before=uv_fingerprint(bm)
def loop_from_edges(edges):
    adjacency={}
    for e in edges:
        for v in e.verts:adjacency.setdefault(v,[]).append(e.other_vert(v))
    assert adjacency and all(len(a)==2 for a in adjacency.values()),'Not one regular closed boundary'
    first=min(adjacency,key=lambda v:(v.co.x,v.co.y,v.co.z)); loop=[first]; prev=None; cur=first
    while True:
        nxt=next(v for v in adjacency[cur] if v!=prev)
        if nxt==first:break
        loop.append(nxt); prev,cur=cur,nxt
        assert len(loop)<=len(adjacency)
    assert len(loop)==len(adjacency),'More than one boundary'
    return loop
source_seams=[]
for sign in [1,-1]:
    selected=[v for v in bm.verts if sign*v.co.x>.285 and v.co.z<.95]
    eligible=set(selected); faces=[f for f in bm.faces if all(v in eligible for v in f.verts)]
    geom=list(set(selected)|set(faces)|set(e for f in faces for e in f.edges))
    bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-7,plane_co=(0,0,CUT),plane_no=(0,0,1))
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if sign*v.co.x>.285 and v.co.z<CUT-1e-7],context='VERTS')
    loop=loop_from_edges([e for e in bm.edges if e.is_boundary and all(sign*v.co.x>.285 and abs(v.co.z-CUT)<1e-5 for v in e.verts)])
    centre=sum((v.co for v in loop),Vector())/len(loop)
    source_seams.append((sign,loop,centre))
assert positions_before==vertex_fingerprint(bm),'Protected source position changed'
assert uvs_before==uv_fingerprint(bm),'Protected source face UV changed'
bm.verts.index_update(); bm.faces.index_update()
all_vertices=[list(v.co) for v in bm.verts]
all_faces=[[v.index for v in f.verts] for f in bm.faces]
all_uv=[[list(l[uv].uv) for l in f.loops] for f in bm.faces]
all_material=[f.material_index for f in bm.faces]
source_count=len(all_vertices)
records=[]
for sign,old_loop,centre in source_seams:
    cx,cy,_=centre
    verts=[]; faces=[]
    def vertex(p):verts.append(tuple(float(x) for x in p)); return len(verts)-1
    def face(ids):
        assert len(set(ids))==len(ids),'Repeated index in authored face'
        faces.append(tuple(ids))
    xs=[-.045,-.040,-.0315,-.023,-.019,-.0105,-.002,.002,.0105,.019,.023,.0315,.040,.045]
    ys=[-.027,-.014,0,.014,.027]
    nx,ny=len(xs),len(ys)
    grid={}
    for i,x in enumerate(xs):
        for j,y in enumerate(ys): grid[i,j]=vertex((cx+sign*x,cy+y,.836))
    slots=[(1,3),(4,6),(7,9),(10,12)]
    for i in range(nx-1):
        for j in range(ny-1):
            hole=any(a<=i<b and 1<=j<3 for a,b in slots)
            if not hole: face([grid[i,j],grid[i+1,j],grid[i+1,j+1],grid[i,j+1]])
    # Distal ring follows rectangular grid perimeter with shared grid vertices.
    border=[(i,0) for i in range(nx)]+[(nx-1,j) for j in range(1,ny)]+[(i,ny-1) for i in range(nx-2,-1,-1)]+[(0,j) for j in range(ny-2,0,-1)]
    rings=[[grid[k] for k in border]]
    zrows=[.836,.850,.860,.8725,.885,.894]
    for z in zrows[1:]:
        shape=1.0 if z<.86 else 1-(z-.86)*2.4
        ring=[vertex((cx+sign*xs[i]*shape,cy+ys[j]*(1+.7*(z-.836)/(.885-.836)),z)) for i,j in border]
        rings.append(ring)
    # Thumb outlet on anatomical inner palm side, four side-wall cells.
    thumb_side={(len(border)-3,2),(len(border)-2,2),(len(border)-3,3),(len(border)-2,3)}
    # These four cells occupy y[-.014,+.014], z[.860,.885].
    for r in range(len(rings)-1):
        for k in range(len(border)):
            if (k,r) in thumb_side:continue
            face([rings[r][k],rings[r][(k+1)%len(border)],rings[r+1][(k+1)%len(border)],rings[r+1][k]])
    # Recover thumb hole from mesh edge incidence; wrist outlet is separate.
    def boundaries(faces):
        edges={}
        for f in faces:
            for a,b in zip(f,f[1:]+f[:1]):edges[tuple(sorted((a,b)))]=edges.get(tuple(sorted((a,b))),0)+1
        return [e for e,n in edges.items() if n==1]
    def indexed_loop(edges):
        adj={}
        for a,b in edges:adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
        assert adj and all(len(v)==2 for v in adj.values())
        first=min(adj); ids=[first]; cur=first; prev=None
        while True:
            nxt=next(v for v in adj[cur] if v!=prev)
            if nxt==first:break
            ids.append(nxt); prev,cur=cur,nxt
        assert len(ids)==len(adj)
        return ids
    thumbedges=[e for e in boundaries(faces) if all(abs(verts[v][0]-(cx-sign*.043))<.008 and .859<verts[v][2]<.886 for v in e)]
    thumbroot=indexed_loop(thumbedges)
    assert len(thumbroot)==8,'Thumb must have one eight-edge outlet'
    def loft(root,path,radii):
        root_c=sum((Vector(verts[i]) for i in root),Vector())/len(root)
        a=(Vector(verts[root[0]])-root_c).normalized()
        tangent=(Vector(path[1])-root_c).normalized(); a=(a-tangent*a.dot(tangent)).normalized()
        b=tangent.cross(a).normalized()
        # Derive phase angles from actual shared outlet positions.
        angles=[math.atan2((Vector(verts[i])-root_c).dot(b),(Vector(verts[i])-root_c).dot(a)) for i in root]
        previous=root
        for n,point in enumerate(path[1:],1):
            tangent=(Vector(path[min(n+1,len(path)-1)])-Vector(path[n-1])).normalized()
            axis=(a-tangent*a.dot(tangent)).normalized(); other=tangent.cross(axis).normalized()
            ring=[vertex(Vector(point)+radii[n]*(math.cos(t)*axis+math.sin(t)*other)) for t in angles]
            for j in range(len(root)):face([previous[j],previous[(j+1)%len(root)],ring[(j+1)%len(root)],ring[j]])
            previous=ring
        tip=vertex(Vector(path[-1])+tangent*radii[-1]*.65)
        for j in range(len(root)):face([previous[j],previous[(j+1)%len(root)],tip])
    fingers=[]
    for n,(a,b) in enumerate(slots):
        mid=(a+b)//2
        root=[grid[a,1],grid[mid,1],grid[b,1],grid[b,2],grid[b,3],grid[mid,3],grid[a,3],grid[a,2]]
        x=cx+sign*(xs[a]+xs[b])/2
        shift=[.004,-.004,-.002,.009][n]
        path=[(x,cy,.836),(x,cy-.004,.824),(x,cy-.012,.810+shift),(x,cy-.027,.797+shift),
              (x,cy-.043,.790+shift),(x,cy-.058,.800+shift),(x,cy-.065,.816+shift),(x,cy-.061,.829+shift)]
        loft(root,path,[.010,.0095,.0092,.0088,.0084,.0079,.0075,.007])
        fingers.append({'rootVertexIDs':root,'centreline':path})
    tc=sum((Vector(verts[i]) for i in thumbroot),Vector())/len(thumbroot)
    tpath=[tuple(tc),(cx-sign*.054,cy-.009,.873),(cx-sign*.059,cy-.028,.863),
           (cx-sign*.052,cy-.048,.853),(cx-sign*.035,cy-.060,.853),(cx-sign*.021,cy-.061,.855)]
    loft(thumbroot,tpath,[.015,.013,.012,.011,.010,.0085])
    # Remove unused interior grid vertices inside open outlets.
    used=sorted(set(i for f in faces for i in f)); remap={v:i for i,v in enumerate(used)}
    vertices=[verts[i] for i in used]; faces2=[[remap[i] for i in f] for f in faces]
    assert len(set(tuple(sorted(f)) for f in faces2))==len(faces2),'Duplicate authored face'
    np.savez(RUN/f'authored-{sign}-before-subdivision.npz',vertices=np.array(vertices),faces=np.array([f for f in faces2 if len(f)==4]),triangleCaps=np.array([f for f in faces2 if len(f)==3]))
    mesh=bpy.data.meshes.new(f'Explicit_glove_{sign}'); mesh.from_pydata(vertices,[],faces2); mesh.update()
    patch=bpy.data.objects.new(mesh.name,mesh); bpy.context.scene.collection.objects.link(patch)
    bpy.context.view_layer.objects.active=patch; patch.select_set(True)
    mod=patch.modifiers.new('Local authored branch smoothing only','SUBSURF'); mod.levels=1; mod.render_levels=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    pb=bmesh.new(); pb.from_mesh(patch.data); pb.verts.index_update()
    newloop=loop_from_edges([e for e in pb.edges if e.is_boundary])
    offset=len(all_vertices); all_vertices.extend(list(v.co) for v in pb.verts)
    addedfaces=[[offset+v.index for v in f.verts] for f in pb.faces]
    all_faces.extend(addedfaces); all_uv.extend([[[all_vertices[i][0]+.5,all_vertices[i][2]] for i in f] for f in addedfaces]); all_material.extend([1]*len(addedfaces))
    # Shared-index zipper stitches the true source and authored boundaries.
    old=sorted([v.index for v in old_loop],key=lambda i:math.atan2(all_vertices[i][1]-cy,all_vertices[i][0]-cx))
    new=sorted([offset+v.index for v in newloop],key=lambda i:math.atan2(all_vertices[i][1]-cy,all_vertices[i][0]-cx))
    old_angles=[math.atan2(all_vertices[i][1]-cy,all_vertices[i][0]-cx) for i in old]
    new_angles=[math.atan2(all_vertices[i][1]-cy,all_vertices[i][0]-cx) for i in new]
    i=j=0; seamfaces=[]
    while i<len(old) or j<len(new):
        an=old_angles[(i+1)%len(old)]+(2*math.pi if i+1>=len(old) else 0) if i<len(old) else float('inf')
        bn=new_angles[(j+1)%len(new)]+(2*math.pi if j+1>=len(new) else 0) if j<len(new) else float('inf')
        if an<bn:f=[old[i%len(old)],old[(i+1)%len(old)],new[j%len(new)]]; i+=1
        else:f=[old[i%len(old)],new[(j+1)%len(new)],new[j%len(new)]]; j+=1
        all_faces.append(f); all_uv.append([[all_vertices[k][0]+.5,all_vertices[k][2]] for k in f]); all_material.append(1); seamfaces.append(f)
    records.append({'sign':sign,'centre':list(centre),'oldSourceWristLoopVertices':len(old),'newAuthoredWristLoopVertices':len(new),'seamFaces':len(seamfaces),'fingerBranches':4,'thumbBranches':1,'authoredFaces':len(pb.faces),'sourceWristIndices':old,'newWristIndices':new,'fingerOutletSharedIndexProof':fingers,'thumbOutletSharedIndexProof':thumbroot})
    pb.free(); bpy.data.objects.remove(patch,do_unlink=True)
bm.free()
mesh=bpy.data.meshes.new('Body with sewn explicit glove topology'); mesh.from_pydata(all_vertices,[],all_faces); mesh.update()
body.data=mesh
uvlayer=mesh.uv_layers.new(name='PreservedSourceAndProvisionalGloveUV')
for polygon,coords,mat in zip(mesh.polygons,all_uv,all_material):
    polygon.material_index=mat
    for li,p in zip(polygon.loop_indices,coords):uvlayer.data[li].uv=p
    polygon.use_smooth=True
# Original source material datablock remains unchanged and reusable.
source_material=bpy.data.materials.get('Material')
assert source_material is not None
mesh.materials.append(source_material)
glove=bpy.data.materials.new('Glove trial provisional PBR; no bake'); glove.use_nodes=True
bs=glove.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.055,.057,.062,1); bs.inputs['Roughness'].default_value=.64; bs.inputs['Metallic'].default_value=0
mesh.materials.append(glove)
check=bmesh.new(); check.from_mesh(mesh)
bmesh.ops.recalc_face_normals(check,faces=list(check.faces)); check.to_mesh(mesh)
topology={'vertices':len(check.verts),'faces':len(check.faces),'boundaryEdges':sum(e.is_boundary for e in check.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in check.edges)}
print('SEWN_TOPOLOGY',json.dumps(topology),flush=True)
if topology['boundaryEdges'] or topology['nonmanifoldEdges']:
    bad=[{'a':list(e.verts[0].co),'b':list(e.verts[1].co),'incidentFaces':len(e.link_faces)} for e in check.edges if not e.is_manifold]
    (OUT/'seam-topology-failure.json').write_text(json.dumps({'status':'failed, not accepted','topology':topology,'badEdges':bad},indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'failed-sewn-body.blend'))
assert topology['boundaryEdges']==0 and topology['nonmanifoldEdges']==0,'Sewn branches must be manifold'
check.free(); body.name='H21-4_explicit_gloves_trial1'
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'body-gloves.blend'))
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'body-gloves.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
report={'status':'UNACCEPTED explicit-branch glove trial1; parent gray judgment required','source':str(SOURCE),'sourceSHA256':source_sha,'sourceSHA256After':sha(SOURCE),'recipeSHA256':sha(Path(__file__)),'displayHeight':1.8,'sourceDisplayTransform':{'scale':float(scale),'translation':trans.tolist()},'cutHeightMeters':CUT,'protectedSourcePositionSHA256':positions_before,'protectedSourceUVSHA256':uvs_before,'protectedSourcePositionsVerifiedAfterCut':True,'protectedSourceUVsVerifiedAfterCut':True,'protectedRegion':'absX<.28 OR z>=.92, all cuffs/hood/feet/knees retained; same source face-loop UV values','sourceVertexCountAfterDistalCuts':source_count,'patches':records,'topology':topology,'files':{str(p):sha(p) for p in RUN.glob('*') if p.is_file()},'wallSeconds':time.perf_counter()-started,'limits':['Source PBR retained; new glove UV/shader are provisional, no bake.','Ring-loft source grid and final seam topology explicit; no closed primitive union.','No gameplay rig/contact or anatomy acceptance.','Intersection diagnostic and temporary seam motion still required.']}
assert report['sourceSHA256']==report['sourceSHA256After']
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('EXPLICIT_GLOVE_TRIAL1_BUILT',json.dumps(topology),flush=True)
