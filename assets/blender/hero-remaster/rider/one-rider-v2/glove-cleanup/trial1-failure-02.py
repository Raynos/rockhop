"""Bounded authored gripping-glove patch; CPU only, untouched donor retained.

Local voxel union shapes only the NEW authored glove. Distal source patches
are removed beneath intact cuffs; actual boundary loops are sewn by faces.
No texture bake, historical donor or whole-body remesh is involved.
"""
import hashlib, json, math, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

REPO=Path('/Users/raynos/projects/games/rockhop')
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/trial1'
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/trial1')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(SOURCE); started=time.perf_counter()
OUT.mkdir(parents=True,exist_ok=True); RUN.mkdir(parents=True,exist_ok=True)
if (OUT/'report.json').exists(): raise RuntimeError('Frozen trial already exists')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE)); bpy.context.view_layer.update()
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
coords=np.array([body.matrix_world@v.co for v in body.data.vertices]); lo=coords.min(0); hi=coords.max(0)
scale=1.8/(hi[2]-lo[2]); trans=np.array([-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]])*scale
for v,p in zip(body.data.vertices,coords): v.co=p*scale+trans
body.parent=None; body.matrix_world=Matrix.Identity(4)
bm=bmesh.new(); bm.from_mesh(body.data)
# Position welding removes UV seam duplicates only; source UV loops remain.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
uv=bm.loops.layers.uv.active
def fingerprint(verts):
    rows=sorted(tuple(round(float(x),7) for x in v.co) for v in verts)
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
protected_before=fingerprint([v for v in bm.verts if abs(v.co.x)<.28 or v.co.z>=.92])
def boundary_loop(edges):
    adjacency={}
    for e in edges:
        for v in e.verts: adjacency.setdefault(v,[]).append(e.other_vert(v))
    assert adjacency and all(len(n)==2 for n in adjacency.values()),'Boundary is not one closed loop'
    first=min(adjacency,key=lambda v:(v.co.x,v.co.y,v.co.z)); result=[first]; prev=None; current=first
    while True:
        nxt=next(v for v in adjacency[current] if v!=prev)
        if nxt==first: break
        result.append(nxt); prev,current=current,nxt
        assert len(result)<=len(adjacency),'Repeated boundary vertex'
    assert len(result)==len(adjacency),'Multiple boundary loops'
    return result
seams=[]
CUT=.900
for sign in [1,-1]:
    verts=[v for v in bm.verts if sign*v.co.x>.285 and v.co.z<.95]
    eligible=set(verts); faces=[f for f in bm.faces if all(v in eligible for v in f.verts)]
    edges=set(e for f in faces for e in f.edges)
    geom=list(set(verts)|edges|set(faces))
    bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-7,plane_co=(0,0,CUT),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
    remove=[v for v in bm.verts if sign*v.co.x>.285 and v.co.z<CUT-1e-7]
    bmesh.ops.delete(bm,geom=remove,context='VERTS')
    edges=[e for e in bm.edges if e.is_boundary and all(sign*v.co.x>.285 and abs(v.co.z-CUT)<1e-5 for v in e.verts)]
    loop=boundary_loop(edges)
    centre=sum((v.co for v in loop),Vector())/len(loop)
    seams.append({'sign':sign,'loop':loop,'centre':centre,'sourceBoundaryVertices':len(loop)})

def sphere(name,centre,radii):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=centre)
    o=bpy.context.object; o.name=name; o.scale=radii
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o
def tube(name,points,radii,rings=12):
    verts=[]; faces=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize(); a=tangent.cross(Vector((1,0,0)))
        if a.length<.01: a=tangent.cross(Vector((0,1,0)))
        a.normalize(); b=tangent.cross(a).normalized()
        for j in range(rings):
            theta=j*2*math.pi/rings
            verts.append(Vector(p)+radii[i]*(math.cos(theta)*a+math.sin(theta)*b))
    for i in range(len(points)-1):
        for j in range(rings): faces.append((i*rings+j,i*rings+(j+1)%rings,(i+1)*rings+(j+1)%rings,(i+1)*rings+j))
    faces.extend([tuple(range(rings-1,-1,-1)),tuple((len(points)-1)*rings+j for j in range(rings))])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(o); return o
patch_records=[]
for seam in seams:
    sign=seam['sign']; cx,cy,_=seam['centre']; parts=[]
    # Palm/back thickness surrounds a negative-Y grip; no grip cylinder is part of asset.
    parts.append(sphere('Authored palm',(cx,cy,.861),(.043,.031,.043)))
    parts.append(sphere('Authored wrist',(cx,cy,.892),(.039,.043,.027)))
    parts.append(sphere('Thumb mound',(cx-sign*.032,cy-.005,.856),(.023,.026,.029)))
    lengths=[.058,.068,.065,.052]
    for i,(dx,length) in enumerate(zip([-.027,-.009,.010,.028],lengths)):
        x=cx+sign*dx; z=.842
        points=[(x,cy+.002,z+.011),(x,cy-.007,z-.007),(x,cy-.021,z-length*.66),
                (x,cy-.047,z-length*.80),(x,cy-.064,z-length*.59),(x,cy-.067,z-length*.30)]
        parts.append(tube(f'Finger{i+1}',points,[.0105,.010,.0095,.009,.0082,.0075],16))
        parts.append(sphere(f'Knuckle{i+1}',points[0],(.011,.012,.012)))
        parts.append(sphere(f'Finger tip{i+1}',points[-1],(.0075,.0075,.0075)))
    thumbpts=[(cx-sign*.032,cy,.870),(cx-sign*.053,cy-.015,.852),(cx-sign*.055,cy-.038,.835),(cx-sign*.040,cy-.053,.827),(cx-sign*.020,cy-.057,.827)]
    parts.append(tube('Opposing thumb',thumbpts,[.017,.015,.014,.012,.010],16))
    parts.append(sphere('Thumb tip',thumbpts[-1],(.010,.010,.010)))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); patch=bpy.context.object
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    mod=patch.modifiers.new('Local authored-glove union only','REMESH'); mod.mode='VOXEL'; mod.voxel_size=.0018; mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    high_path=RUN/f'authored-glove-{sign}-high.blend'
    # Save local union in the full master later; numeric pre-reduction proof here.
    high_faces=len(patch.data.polygons)
    dec=patch.modifiers.new('Local glove-only triangle reduction','DECIMATE'); dec.ratio=min(1,5000/max(1,high_faces*2))
    bpy.ops.object.modifier_apply(modifier=dec.name)
    pb=bmesh.new(); pb.from_mesh(patch.data)
    bmesh.ops.bisect_plane(pb,geom=list(pb.verts)+list(pb.edges)+list(pb.faces),dist=1e-7,plane_co=(0,0,.880),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
    # Bisecting a locally decimated mesh can leave coincident sliver faces.
    # Clean only this new authored patch, never source-body triangles.
    bmesh.ops.remove_doubles(pb,verts=list(pb.verts),dist=1e-7)
    bmesh.ops.dissolve_degenerate(pb,edges=list(pb.edges),dist=1e-7)
    ploop=boundary_loop([e for e in pb.edges if e.is_boundary])
    # Copy local authored patch into the body BMesh, preserving source face UVs.
    vmap={v:bm.verts.new(v.co) for v in pb.verts}
    for f in pb.faces:
        new=bm.faces.new([vmap[v] for v in f.verts]); new.material_index=1; new.smooth=True
    new_loop=[vmap[v] for v in ploop]
    # Both loops ordered by geometric angle. Zipper sews actual shared vertices
    # when counts differ; no surface overlap or separate floating wrist shell.
    def angular(loop): return sorted(loop,key=lambda v:math.atan2(v.co.y-cy,v.co.x-cx))
    old=angular(seam['loop']); new=angular(new_loop)
    # Normalize phases to zero, then triangulate monotone angular progress.
    a=[math.atan2(v.co.y-cy,v.co.x-cx) for v in old]; b=[math.atan2(v.co.y-cy,v.co.x-cx) for v in new]
    i=j=0; bridge_faces=0
    while i<len(old) or j<len(new):
        oi=i%len(old); nj=j%len(new)
        an=a[(i+1)%len(old)]+(2*math.pi if i+1>=len(old) else 0) if i<len(old) else float('inf')
        bn=b[(j+1)%len(new)]+(2*math.pi if j+1>=len(new) else 0) if j<len(new) else float('inf')
        if an<bn: vs=[old[oi],old[(i+1)%len(old)],new[nj]]; i+=1
        else: vs=[old[oi],new[(j+1)%len(new)],new[nj]]; j+=1
        f=bm.faces.new(vs); f.material_index=1; f.smooth=True; bridge_faces+=1
    patch_records.append({'sign':sign,'centre':list(seam['centre']),'sourceWristLoopVertices':len(old),'authoredWristLoopVertices':len(new),'sewnBridgeFaces':bridge_faces,'localUnionFacesBeforeReduction':high_faces,'authoredFacesAfterReductionAndCut':len(pb.faces),'fingerCount':4,'thumbCount':1,'cutHeight':CUT,'authoredJoinHeight':.880})
    pb.free(); bpy.data.objects.remove(patch,do_unlink=True)
assert protected_before==fingerprint([v for v in bm.verts if abs(v.co.x)<.28 or v.co.z>=.92]),'Protected source geometry changed'
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
# Planar UVs only on the new glove; provisional dark glove shader, no bake.
for f in bm.faces:
    if f.material_index==1:
        for l in f.loops:l[uv].uv=((l.vert.co.x+.5),l.vert.co.z)
bm.to_mesh(body.data); bm.free(); body.data.update()
glove=bpy.data.materials.new('Provisional glove PBR; no baked source detail'); glove.use_nodes=True
bs=glove.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.055,.057,.062,1); bs.inputs['Roughness'].default_value=.64; bs.inputs['Metallic'].default_value=0
body.data.materials.append(glove)
body.name='H21-4_glove_trial1_connected'
diag=bmesh.new(); diag.from_mesh(body.data)
topology={'vertices':len(diag.verts),'faces':len(diag.faces),'boundaryEdges':sum(e.is_boundary for e in diag.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in diag.edges)}
diag.free()
assert topology['boundaryEdges']==0 and topology['nonmanifoldEdges']==0,'Glove sewing must be manifold'
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'body-gloves-trial1.blend'))
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'body-gloves-trial1.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
report={'status':'UNACCEPTED glove trial1; parent gray review required before bake/rig','source':str(SOURCE),'sourceSHA256':source_sha,'sourceSHA256After':sha(SOURCE),'recipeSHA256':sha(Path(__file__)),'displayHeight':1.8,'displayTransform':{'scale':float(scale),'translation':trans.tolist()},'cutHeight':CUT,'protectedSourceFingerprintBefore':protected_before,'protectedSourceFingerprintAfter':protected_before,'protectedDefinition':'all source position vertices with absX<.28 OR z>=.92; cuffs/hood/knees/feet untouched','patches':patch_records,'topology':topology,'files':{str(p):sha(p) for p in RUN.glob('body-gloves-trial1.*')},'wallSeconds':time.perf_counter()-started,'limits':['Provisional UV/shader only; source detail not baked.','No rig or gameplay acceptance; appearance/deformation require parent review.','Local authored palm/finger union uses voxel remesh, source body never globally remeshed.']}
assert report['sourceSHA256']==report['sourceSHA256After']
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('GLOVE_TRIAL1_BUILT',json.dumps(topology),flush=True)
