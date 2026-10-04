"""Recover selected donor silhouette directly, with explicit wearer openings.

Simplify the immutable high donor while retaining original UV/PBR. Avoid the
failed projected QuadriFlow and stock-pattern relief controls. Plane cuts and
bounded neck surface clipping preserve actual retained donor geometry; rest
topology/intersections and played likeness remain qualification, not assumed.
"""
import argparse, collections, hashlib, json, math, sys, time
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,recipe,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'donor-surface.blend').exists(),'Keep frozen source controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,recipe]}
assert pins[str(source)]=='6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93'
bpy.ops.wm.open_mainfile(filepath=str(source))
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
old=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged']
g=high.copy();g.data=high.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor surface with wearer cuts, unaccepted'
g.hide_set(False);g.hide_render=False
for o in bpy.data.objects:o.select_set(False)
g.select_set(True);bpy.context.view_layer.objects.active=g
if g.data.has_custom_normals:g.data.normals_split_custom_set([(0,0,0)]*len(g.data.loops))
bm=bmesh.new();bm.from_mesh(g.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
remaining=set(bm.verts);components=[]
while remaining:
    v=remaining.pop();found={v};stack=[v]
    while stack:
        p=stack.pop()
        for e in p.link_edges:
            q=e.other_vert(p)
            if q in remaining:remaining.remove(q);found.add(q);stack.append(q)
    components.append(found)
main=max(components,key=len);removed=[{'vertices':len(c),'faces':len({f for v in c for f in v.link_faces})} for c in components if c is not main]
for c in components:
    if c is not main:bmesh.ops.delete(bm,geom=list(c),context='VERTS')
clean={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'otherNonManifoldEdges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
assert clean=={'vertices':460752,'faces':921568,'boundaryEdges':0,'otherNonManifoldEdges':0},clean
bm.to_mesh(g.data);bm.free();g.data.update();print('ACTUAL_DONOR_CLEAN',clean,flush=True)
modifier=g.modifiers.new('Original donor UV-aware direct surface simplification','DECIMATE');modifier.decimate_type='COLLAPSE';modifier.ratio=.018;modifier.use_collapse_triangulate=True;modifier.delimit={'UV','MATERIAL','SEAM'}
bpy.ops.object.modifier_apply(modifier=modifier.name)
display=np.array([v.co[:] for v in g.data.vertices]);g.data.calc_loop_triangles();simplified_triangles=len(g.data.loop_triangles)
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')];exec(compile(definition,str(recipe),'exec'))
native=np.array([register(p)[0] for p in display])
for v,p in zip(g.data.vertices,native):v.co=p
g.parent=body.parent;g.matrix_parent_inverse=body.matrix_parent_inverse.copy();g.matrix_basis=body.matrix_basis.copy();g.data.update()
attr=g.data.attributes.new('actual_donor_display_xyz',type='FLOAT_VECTOR',domain='POINT');attr.data.foreach_set('vector',display.astype(np.float32).ravel())
bm=bmesh.new();bm.from_mesh(g.data);originalFace=bm.faces.layers.int.new('simplified_donor_polygon')
for i,f in enumerate(bm.faces):f[originalFace]=i
def topology():
    boundary={e for e in bm.edges if e.is_boundary};loops=[]
    while boundary:
        first=boundary.pop();found={first};stack=[first]
        while stack:
            e=stack.pop()
            for v in e.verts:
                for other in v.link_edges:
                    if other in boundary:boundary.remove(other);found.add(other);stack.append(other)
        verts={v for e in found for v in e.verts};p=np.array([v.co[:] for v in verts])
        loops.append({'edges':len(found),'vertices':len(verts),'allDegree2':all(sum(e in found for e in v.link_edges)==2 for v in verts),'nativeXYZBoundsM':[p.min(0).tolist(),p.max(0).tolist()],'nativeCentroidM':p.mean(0).tolist()})
    return {'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryLoops':loops,'otherNonManifoldEdges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
beforeCuts=topology();cuts=[]
def plane_cut(label,point,normal):
    count=len(bm.faces);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=Vector(point),plane_no=Vector(normal),clear_outer=True,clear_inner=False)
    cuts.append({'name':label,'nativePlanePointM':list(point),'nativePlaneNormal':list(normal),'facesBefore':count,'facesAfter':len(bm.faces)})
central=native[np.abs(native[:,1])<.20];hem=float(central[:,2].min()+.008)
plane_cut('Hem: retain donor band above its lowest8mm',[0,0,hem],[0,0,-1])
for side in ['R','L']:
    b=rig.data.bones['forearm.'+side];axis=np.array(b.tail_local)-np.array(b.head_local);axis/=np.linalg.norm(axis)
    point=np.array(b.tail_local)-axis*.005;plane_cut('Cuff '+side+': actual wrist minus5mm',point,axis)
afterWearerCuts=topology()
# A small convex neck cavity removes the donor's generated neck-floor closure.
# Split the surface along each halfspace before deleting interior pieces, so
# retained actual hood vertices/UVs are not snapped or resculpted.
center=np.array([.015,0]);radii=np.array([.078,.085]);zlo=1.485;zhi=1.67;segments=20
polygon=np.array([center+radii*[math.cos(2*math.pi*i/segments),math.sin(2*math.pi*i/segments)] for i in range(segments)])
planes=[]
for i,p in enumerate(polygon):
    q=polygon[(i+1)%segments];edge=q-p;n=np.array([edge[1],-edge[0],0]);n/=np.linalg.norm(n);planes.append((np.r_[p,0],n))
planes.extend([(np.array([0,0,zlo]),np.array([0,0,-1])),(np.array([0,0,zhi]),np.array([0,0,1]))])
for point,normal in planes:
    selected=[f for f in bm.faces if any(zlo-.04<=v.co.z<=zhi+.04 and abs(v.co.x-center[0])<.16 and abs(v.co.y)<.16 for v in f.verts)]
    edges={e for f in selected for e in f.edges};verts={v for f in selected for v in f.verts}
    bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+selected,dist=1e-8,plane_co=Vector(point),plane_no=Vector(normal),clear_outer=False,clear_inner=False)
interior=[]
for f in bm.faces:
    p=np.array(f.calc_center_median())
    if all(np.dot(p-q,n)<1e-8 for q,n in planes):interior.append(f)
neckRemoved=len(interior);bmesh.ops.delete(bm,geom=interior,context='FACES')
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));finalTopology=topology();bm.to_mesh(g.data);bm.free();g.data.update();g.data.calc_loop_triangles()
p=np.array([v.co[:] for v in g.data.vertices]);tris=[tuple(t.vertices) for t in g.data.loop_triangles]
body.data.calc_loop_triangles();bodyXYZ=np.array([v.co[:] for v in body.data.vertices]);bodyTri=[tuple(t.vertices) for t in body.data.loop_triangles]
gt=BVHTree.FromPolygons([Vector(v) for v in p],tris,all_triangles=True);bt=BVHTree.FromPolygons([Vector(v) for v in bodyXYZ],bodyTri,all_triangles=True)
selfPairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(tris[i])&set(tris[j])];bodyPairs=gt.overlap(bt)
def witnesses(pairs,other,otherTri):
    return [{'garmentTriangle':i,'otherTriangle':j,'garmentVertexIDs':list(tris[i]),'otherVertexIDs':list(otherTri[j]),'garmentNativeXYZ':p[list(tris[i])].tolist(),'otherNativeXYZ':other[list(otherTri[j])].tolist()} for i,j in pairs[:64]]
old.hide_render=True;old.hide_set(True);g['accepted']=False;g['constructionStage']='Actual selected donor simplified surface, original UV/PBR, explicit wearer cuts; unrigged/unaccepted'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'donor-surface.blend'),compress=True)
np.savez_compressed(out/'donor-construction.npz',simplifiedDonorDisplayXYZ=display,simplifiedRegisteredXYZ=native,finalNativeXYZ=p,triangles=np.array(tris),selfTrianglePairs=np.array(selfPairs,dtype=np.int32),bodyTrianglePairs=np.array(bodyPairs,dtype=np.int32))
report={'status':'UNACCEPTED actual selected donor surface recovery, rest wearing/art still require qualification','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'donor-surface.blend'),'constructionArchiveSHA256':sha(out/'donor-construction.npz'),
        'sourceDonorSHA256':'800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba','sourceCleanup':clean,'removedComponents':removed,'simplification':{'method':'Collapse decimation in original donor frame, UV/material/seam delimiters, triangle output','ratio':.018,'vertices':len(display),'triangles':simplified_triangles},
        'beforeCuts':beforeCuts,'wearerPlaneCuts':cuts,'afterHemCuffCuts':afterWearerCuts,'neckCavity':{'centerXYM':center.tolist(),'ellipseRadiiXYM':radii.tolist(),'zRangeM':[zlo,zhi],'segments':segments,'removedSurfacePieces':neckRemoved,'method':'Explicit surface halfspace partition then interior face deletion; no Boolean modifier or body vertex snaps'},'finalTopology':finalTopology,'triangles':len(tris),
        'restGarmentBodyTrianglePairs':len(bodyPairs),'restNonAdjacentSelfTrianglePairs':len(selfPairs),'bodyWitnesses':witnesses(bodyPairs,bodyXYZ,bodyTri),'selfWitnesses':witnesses(selfPairs,p,tris),
        'material':'Original selected donor material graph and packed4096base/ORM, original source UVs carried through simplification/cuts; no new bake or recolor',
        'limits':['This recovers actual donor geometry instead of stock-pattern relief. Simplification/registration/cuts alter source, not exact high-poly reproduction.','All contacts/topology defects remain explicit failed prerequisites; no rig or moving/collision/art/mobile acceptance.','All original body/head/source13/source14/51bind preserved; root alone judges played likeness. AllM0-M5 open, no normal-player/Library promotion.']}
assert pins=={x:sha(x) for x in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item())+'\n');print('ACTUAL_DONOR_SURFACE_READY',len(p),len(tris),'body',len(bodyPairs),'self',len(selfPairs),'loops',len(finalTopology['boundaryLoops']),flush=True)
