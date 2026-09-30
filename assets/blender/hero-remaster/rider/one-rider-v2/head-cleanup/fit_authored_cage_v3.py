"""Source-guided authored cage feasibility. CPU only, bounds disclosed.

Initial front skin chart and folded-ear guide placement use the NEW reduced
Pixal bust. Subsequent dense fitting is strictly <=.004 native units. These
are separate operations, never described as untouched source triangles.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--layout',required=True);ap.add_argument('--guide',required=True)
ap.add_argument('--dense',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out)
out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen fit exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p:sha(p) for p in [a.layout,a.guide,a.dense]};start=time.monotonic()
def summary(values):
    return dict(count=len(values),maximum=max(values,default=0),
                percentiles=np.percentile(values,[50,95,99]).tolist() if values else [])
def canonical(native):
    out=native[:,[0,2,1]].copy();out[:,1]*=-1;return out
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.guide)
guide_objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
if len(guide_objects)!=1:raise RuntimeError('Expected one measured source bust mesh')
obj=guide_objects[0];obj.data.transform(Matrix.Rotation(math.pi,4,'Z')@obj.matrix_world)
obj.matrix_world=Matrix.Identity(4);bpy.context.view_layer.update()
guide_bvh=BVHTree.FromObject(obj,bpy.context.evaluated_depsgraph_get())
p=np.load(a.layout);native=p['vertices'].astype(np.float64)
f=p['faces'];regions=p['guide_region'];feature=p['landmark']
co=canonical(native);placements=[];ear_placements=[];rejected=0
for i,(point,region) in enumerate(zip(co,regions)):
    original=Vector(point)
    if region==1:
        # Verified facial chart excludes curly scalp; extend upper forehead
        # from lower bare forehead samples rather than intersecting curls.
        x=float(point[0]);y=float(point[2])
        sample_y=min(y,.165 if abs(x)>.12 else .185)
        sample_x=max(-.16,min(.16,x)) if sample_y>.12 else x
        origin=Vector((sample_x,-.5,sample_y))
        hit,normal,idx,distance=guide_bvh.ray_cast(origin,Vector((0,1,0)),1)
        if hit is None:rejected+=1;continue
        proposed=Vector((x,hit.y,y))
        delta=(proposed-original).length
        if delta>.12:rejected+=1;continue
        co[i]=proposed;placements.append(float(delta))
    elif region==2:
        hit,normal,idx,distance=guide_bvh.find_nearest(original,.025)
        if hit is None:rejected+=1;continue
        # Source-fold guide remains a bounded initial placement; never claim
        # preservation of all undercuts merely from closest-point projection.
        proposed=original.lerp(hit,.8)
        co[i]=proposed;ear_placements.append(float((proposed-original).length))
mesh=bpy.data.meshes.new('Explicit authored cage with semantic feature loops')
mesh.from_pydata(co.tolist(),[],f.tolist());mesh.update()
clean=bpy.data.objects.new('UNACCEPTED authored head feasibility',mesh)
bpy.context.collection.objects.link(clean)
# Selective linear subdivision leaves all skull/neck/ear authored topology.
bm=bmesh.new();bm.from_mesh(mesh)
def verified_skin(point):
    x,y,z=point
    return abs(x)<.17 and -.145<z<.185 and -y>.10 and (z>-.025 or abs(x)<.10)
skin_edges=[e for e in bm.edges if all(verified_skin(v.co) for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=skin_edges,cuts=1,use_grid_fill=True)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh);bm.free();mesh.update()
for o in guide_objects:bpy.data.objects.remove(o,do_unlink=True)
# Actual retained dense source. Surface is a fitting reference, not assumed
# manifold geometry. Its topology failures stay recorded separately.
p=np.load(a.dense);dv=canonical(p['vertices']);df=p['faces']
target=bpy.data.meshes.new('Retained dense reference ONLY')
target.vertices.add(len(dv));target.vertices.foreach_set('co',dv.ravel())
target.loops.add(df.size);target.loops.foreach_set('vertex_index',df.ravel())
target.polygons.add(len(df));target.polygons.foreach_set('loop_start',np.arange(len(df),dtype=np.int32)*3)
target.polygons.foreach_set('loop_total',np.full(len(df),3,dtype=np.int32));target.update()
source=bpy.data.objects.new('Dense reference ONLY',target);bpy.context.collection.objects.link(source)
bpy.context.view_layer.update();bvh=BVHTree.FromObject(source,bpy.context.evaluated_depsgraph_get())
fits=[];fit_rejected=0;normal_rejected=0;post_error=[]
fit_coords_before=[];fit_coords_after=[]
for vertex in mesh.vertices:
    if not verified_skin(vertex.co):continue
    hit,normal,idx,distance=bvh.find_nearest(vertex.co,.004)
    if hit is None:fit_rejected+=1;continue
    # Reject inconsistent normals rather than chase folded/internal dust.
    if normal.dot(vertex.normal)<.25:normal_rejected+=1;continue
    initial=vertex.co.copy();vertex.co=hit
    fits.append(float((vertex.co-initial).length))
    fit_coords_before.append(list(initial));fit_coords_after.append(list(vertex.co))
    nearest,normal,idx,distance=bvh.find_nearest(vertex.co,.004)
    post_error.append(float(distance) if nearest is not None else float('nan'))
if max(fits,default=0)>.0040001:raise RuntimeError('Dense fitting bound exceeded')
bpy.data.objects.remove(source,do_unlink=True);bpy.data.meshes.remove(target)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh);bm.free();mesh.update()
for poly in mesh.polygons:poly.use_smooth=True
mat=bpy.data.materials.new('Neutral gray before any bake');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
bsdf.inputs['Roughness'].default_value=.65;mesh.materials.append(mat)
bpy.context.view_layer.objects.active=clean;clean.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
vertices=np.array([x.co[:] for x in mesh.vertices]);tri=np.array([x.vertices[:] for x in mesh.polygons],dtype=np.int32)
native=vertices[:,[0,2,1]].copy();native[:,2]*=-1
np.savez(out/'head.npz',vertices=native.astype(np.float32),faces=tri)
np.savez(out/'fit-samples.npz',before=np.array(fit_coords_before),after=np.array(fit_coords_after))
e,c=np.unique(np.sort(np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]])),axis=1),axis=0,return_counts=True)
area=np.linalg.norm(np.cross(native[tri[:,1]]-native[tri[:,0]],native[tri[:,2]]-native[tri[:,0]]),axis=1)
report=dict(status='UNACCEPTED authored cage feasibility; gray parent review required',
    sources=before,sourcesAfter={p:sha(p) for p in before},scriptSHA256=sha(__file__),
    blender=bpy.app.version_string,vertices=len(vertices),faces=len(tri),
    topology=dict(boundaryEdges=int(np.sum(c==1)),nonmanifoldEdges=int(np.sum(c>2)),
                  nearZeroAreaFaces=int(np.sum(area<1e-12))),
    initialSourceGuide=dict(frontSkin=summary(placements),frontSkinMaximumAllowed=.12,
        earFoldGuide=summary(ear_placements),earMaximumAllowed=.025,earGuideBlend=.8,
        rejectedVertices=rejected,method='frontal semantic chart and closest folded-ear source guides',
        disclosure='Initial authored cage placement; not the later <=.004-native dense fit'),
    subdivision=dict(cuts=1,selectedFacialEdges=len(skin_edges)),
    boundedDenseFit=dict(displacements=summary(fits),maximumAllowed=.004,
        missingWithinBound=fit_rejected,inconsistentNormalRejected=normal_rejected,
        finalAcceptedSampleDistance=summary(post_error)),
    wallSeconds=time.monotonic()-start,
    limits=['Folded ears are authored/source-guided; closest points alone cannot prove undercut fidelity.',
        'Post-fit error applies only accepted samples; rejects and authored skull/neck are excluded.',
        'Initial source-guided displacement is separately bounded and can exceed.004 native units.',
        'Dense source topology is not repaired or claimed clean.',
        'No new textures, detail/PBR bake, neck/body join, rig or gameplay pass.'])
assert before==report['sourcesAfter']
(out/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
