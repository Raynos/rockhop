"""Fresh anatomical MPFB/CC0 head cage, smooth anchors, bounded dense fit.

Source is newly instantiated for this rider session, never production donor.
Native eye assets are instantiated against that same source before extraction.
No whole-head shrinkwrap, chart replacement, texture bake, or body neck join.
"""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
import bpy,bmesh,addon_utils
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source',required=True);ap.add_argument('--dense',required=True)
ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen anatomical fit exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default'
base_obj=addon/'mpfb/data/3dobjs/base.obj'
eye_asset=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/high-poly/high-poly.mhclo')
eye_obj=eye_asset.with_suffix('.obj')
before={str(p):sha(p) for p in [Path(a.source),Path(a.dense),base_obj,eye_asset,eye_obj]}
start=time.monotonic();bpy.ops.wm.open_mainfile(filepath=a.source)
bpy.context.preferences.extensions.repos.new(name='Fresh anatomical head source',
    module='fresh_head_mpfb',custom_directory=str(addon))
addon_utils.enable('bl_ext.fresh_head_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.fresh_head_mpfb.mpfb.services.humanservice import HumanService
body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'body' in o.vertex_groups)
eyes=HumanService.add_mhclo_asset(str(eye_asset),body,asset_type='Eyes',subdiv_levels=0,
    set_up_rigging=False,interpolate_weights=False,import_subrig=False,import_weights=False)
eyes.name='NEW native CC0 anatomical eyeballs'
def group_indices(o,name,threshold=.1):
    gi=o.vertex_groups[name].index
    return {v.index for v in o.data.vertices if any(g.group==gi and g.weight>threshold for g in v.groups)}
def center_group(name):
    indices=group_indices(body,name)
    return np.mean([body.data.vertices[i].co[:] for i in indices],axis=0)
eye_center=(center_group('joint-l-eye')+center_group('joint-r-eye'))/2
# Explicit anatomical adapter. At the proposed .42m/native display scale,
# unmoved template IPD is about64.6mm; target eyes shift smoothly to68.0mm.
sx,sy,sz=2.5,2.035,2.0
ty=.111-sy*eye_center[2];tz=-.08
def native_transform(p):return np.array([sx*p[0],sy*p[2]+ty,-sz*p[1]+tz])
body_ids=group_indices(body,'body')
selected=[poly for poly in body.data.polygons if all(i in body_ids for i in poly.vertices)
    and min(body.data.vertices[i].co.z for i in poly.vertices)>1.385]
used=sorted({i for poly in selected for i in poly.vertices});lookup={v:i for i,v in enumerate(used)}
head_vertices=np.array([native_transform(body.data.vertices[i].co) for i in used])
polygons=[tuple(lookup[i] for i in poly.vertices) for poly in selected]
source_group_sets={name:group_indices(body,name) for name in ['ears','lips','scalp']}
source_group_masks={name:np.array([i in indices for i in used])
    for name,indices in source_group_sets.items()}
eye_native=[native_transform(center_group(name)) for name in ['joint-l-eye','joint-r-eye']]
# Landmarks are measured from the fresh anatomical source, not guessed chart
# samples. RBF displacements are continuous; protected folds move together.
lip_ids=group_indices(body,'lips');lip_positions=np.array([body.data.vertices[i].co[:] for i in lip_ids])
front_lips=lip_positions[lip_positions[:,1]<np.percentile(lip_positions[:,1],35)]
lip_anchor=native_transform(np.mean(front_lips,axis=0))
body_positions=np.array([body.data.vertices[i].co[:] for i in body_ids])
nose_region=body_positions[(np.abs(body_positions[:,0])<.025)&
    (body_positions[:,2]>1.49)&(body_positions[:,2]<1.555)]
nose_anchor=native_transform(nose_region[np.argmin(nose_region[:,1])])
anchors=np.array(eye_native+[lip_anchor,nose_anchor])
targets=anchors.copy();targets[0,:2]=[.081,.111];targets[1,:2]=[-.081,.111]
targets[2,1]=-.032;targets[3,1]=.035
shift=targets-anchors
def smooth_anchor(p):
    dist=np.linalg.norm(p[None,:]-anchors,axis=1)
    w=np.exp(-(dist/.060)**2)
    return (w[:,None]*shift).sum(axis=0)/(1+w.sum())
anchor_displacements=np.array([smooth_anchor(p) for p in head_vertices])
head_vertices+=anchor_displacements
eye_points=[]
eyes_transform=eyes.matrix_world.copy()
for v in eyes.data.vertices:
    initial=native_transform(eyes_transform@v.co)
    eye_points.append(initial)
eye_points=np.array(eye_points)
eye_component_translations=[]
for side,anchor in zip([1,-1],eye_native):
    mask=eye_points[:,0]*side>0
    center=(eye_points[mask].min(axis=0)+eye_points[mask].max(axis=0))/2
    translation=anchor-center
    eye_points[mask]+=translation
    eye_component_translations.append(dict(side=side,actualNativeAssetCenter=center.tolist(),
        anatomicalNativeAnchor=anchor.tolist(),translation=translation.tolist()))
eye_points=np.array([p+smooth_anchor(p) for p in eye_points])
eye_faces=[tuple(p.vertices) for p in eyes.data.polygons]
for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
def canonical(p):return np.array([p[0],-p[2],p[1]])
mesh=bpy.data.meshes.new('NEW CC0 anatomical head protected eye lip ear topology')
mesh.from_pydata([canonical(p) for p in head_vertices],[],polygons);mesh.update()
head=bpy.data.objects.new('UNACCEPTED fresh anatomical head fit',mesh)
bpy.context.collection.objects.link(head)
protect=source_group_masks['ears']|source_group_masks['lips']|source_group_masks['scalp']
# Protected eyelid/eyeball vicinity uses anatomical source centers.
for center in eye_native:
    protect|=np.linalg.norm(head_vertices-center,axis=1)<.070
group=head.vertex_groups.new(name='Protected eyelids lips ears scalp')
group.add(np.flatnonzero(protect).tolist(),1,'REPLACE')
fitgroup=head.vertex_groups.new(name='Verified cheek nose forehead skin only')
native_y=head_vertices[:,1];native_z=head_vertices[:,2]
allowed=(~protect)&(native_z>.10)&(native_y>-.05)&(native_y<.185)&(np.abs(head_vertices[:,0])<.16)
fitgroup.add(np.flatnonzero(allowed).tolist(),1,'REPLACE')
# Real anatomical quad topology subdivides smoothly; explicit neck boundary
# remains source-derived. No planar face-chart interpolation or arbitrary cap.
bpy.context.view_layer.objects.active=head;head.select_set(True)
sub=head.modifiers.new('Anatomical cage subdivision','SUBSURF');sub.levels=2
bpy.ops.object.modifier_apply(modifier=sub.name)
bpy.context.view_layer.update()
protected_group=head.vertex_groups['Protected eyelids lips ears scalp'].index
fit_group=head.vertex_groups['Verified cheek nose forehead skin only'].index
p=np.load(a.dense);dv=p['vertices'][:,[0,2,1]].copy();dv[:,1]*=-1;df=p['faces']
target=bpy.data.meshes.new('Dense Pixal fitting reference ONLY')
target.vertices.add(len(dv));target.vertices.foreach_set('co',dv.ravel())
target.loops.add(df.size);target.loops.foreach_set('vertex_index',df.ravel())
target.polygons.add(len(df));target.polygons.foreach_set('loop_start',np.arange(len(df),dtype=np.int32)*3)
target.polygons.foreach_set('loop_total',np.full(len(df),3,dtype=np.int32));target.update()
reference=bpy.data.objects.new('Retained dense fitting reference ONLY',target)
bpy.context.collection.objects.link(reference);bpy.context.view_layer.update()
bvh=BVHTree.FromObject(reference,bpy.context.evaluated_depsgraph_get())
fits=[];rejected=0;normals_rejected=0;protected_count=0;fit_samples=[]
for vertex in head.data.vertices:
    weights={g.group:g.weight for g in vertex.groups}
    if weights.get(protected_group,0)>.05:protected_count+=1;continue
    blend=weights.get(fit_group,0)
    if blend<.01:continue
    hit,normal,idx,distance=bvh.find_nearest(vertex.co,.004)
    if hit is None:rejected+=1;continue
    if normal.dot(vertex.normal)<.5:normals_rejected+=1;continue
    initial=vertex.co.copy();vertex.co=initial.lerp(hit,blend)
    moved=(vertex.co-initial).length
    if moved>.0040001:raise RuntimeError('Dense fitting bound exceeded')
    fits.append(moved);fit_samples.append((list(initial),list(vertex.co)))
bpy.data.objects.remove(reference,do_unlink=True);bpy.data.meshes.remove(target)
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(head.data);bm.free();head.data.update()
eye_mesh=bpy.data.meshes.new('Fresh native CC0 anatomical eyes')
eye_mesh.from_pydata([canonical(p) for p in eye_points],[],eye_faces);eye_mesh.update()
eye_obj_new=bpy.data.objects.new('NEW native CC0 eyeballs with same anchor adapter',eye_mesh)
bpy.context.collection.objects.link(eye_obj_new)
eye_sub=eye_obj_new.modifiers.new('Native anatomical eye subdivision','SUBSURF');eye_sub.levels=1
bpy.context.view_layer.objects.active=eye_obj_new;eye_obj_new.select_set(True)
bpy.ops.object.modifier_apply(modifier=eye_sub.name)
mat=bpy.data.materials.new('Neutral gray anatomical inspection');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
bsdf.inputs['Roughness'].default_value=.65
for o in [head,eye_obj_new]:
    o.data.materials.clear();o.data.materials.append(mat)
    for poly in o.data.polygons:poly.use_smooth=True
    o.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
head.data.calc_loop_triangles()
verts=np.array([x.co[:] for x in head.data.vertices]);tri=np.array([x.vertices[:] for x in head.data.loop_triangles],dtype=np.int32)
nv=verts[:,[0,2,1]].copy();nv[:,2]*=-1
np.savez(out/'head-skin.npz',vertices=nv.astype(np.float32),faces=tri)
np.savez(out/'fit-samples.npz',samples=np.array(fit_samples))
e,c=np.unique(np.sort(np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]])),axis=1),axis=0,return_counts=True)
def stats(values):return dict(count=len(values),maximum=max(values,default=0),
    percentiles=np.percentile(values,[50,95,99]).tolist() if len(values) else [])
report=dict(status='UNACCEPTED fresh anatomical CC0 retopology alternative; gray review',
    sources=before,sourcesAfter={p:sha(p) for p in before},scriptSHA256=sha(__file__),
    adapter=dict(xScale=sx,verticalScale=sy,depthScale=sz,verticalTranslation=ty,depthTranslation=tz),
    initialSmoothAnchors=dict(sourceNative=anchors.tolist(),targetNative=targets.tolist(),
        requestedShifts=shift.tolist(),actualDisplacements=stats(np.linalg.norm(anchor_displacements,axis=1)),
        sigmaNative=.060,method='normalized Gaussian RBF displacement, denominator1+sum(weights)'),
    anatomicalTopology=dict(skinVertices=len(nv),skinTriangles=len(tri),skinBoundaryEdges=int(np.sum(c==1)),
        skinNonmanifoldEdges=int(np.sum(c>2)),protectedSubdividedVertices=protected_count,
        nativeEyeVertices=len(eye_obj_new.data.vertices),nativeEyePolygons=len(eye_obj_new.data.polygons)),
    denseFit=dict(displacements=stats(fits),maximumAllowed=.004,missingWithinBound=rejected,
        normalRejected=normals_rejected,method='smooth group-weighted bounded fit of verified bare skin only'),
    eyeIPDNative=float(np.linalg.norm(targets[0]-targets[1])),
    nativeEyePlacement=dict(method='component translation onto measured NEW anatomical eye anchors',
        components=eye_component_translations,sourceGeometryRetained=True),
    suggestedWorldScale=.42,suggestedWorldIPDMeters=float(np.linalg.norm(targets[0]-targets[1]))*.42,
    wallSeconds=time.monotonic()-start,
    limits=['Anatomical template is fresh CC0 source, not historical production.',
        'Anchor targets are proposed approximations; protected face/ears are not identical to Pixal.',
        'Dense fit measures accepted skin only, not whole-head target conformity.',
        'Untextured anatomical source has no approved buzz material yet.',
        'No UV/detail/PBR bake, joined body neck, rig or gameplay acceptance.'])
assert before==report['sourcesAfter']
(out/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
