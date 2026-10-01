"""Fresh native evaluated young-adult male head; no custom face deformation.

Prior v4/v5 extracted Basis, bypassing active macro shape keys. This recipe
bakes the actual installed native morph mix before head extraction, retains
native UVs, and uses only one uniform IPD scale plus translation.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy,bmesh,addon_utils
import numpy as np
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen native result exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
start=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True)
addon=Path.home()/'Library/Application Support/Blender/5.1/extensions/user_default'
bpy.context.preferences.extensions.repos.new(name='Native head evaluated preset',module='native_head_mpfb',custom_directory=str(addon))
addon_utils.enable('bl_ext.native_head_mpfb.mpfb',default_set=True,persistent=False)
from bl_ext.native_head_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.native_head_mpfb.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict()
macro.update(gender=1,age=.50,muscle=.60,weight=.50,proportions=.50,height=.50,
    race={'asian':.25,'caucasian':.35,'african':.40})
target_stack=TargetService.calculate_target_stack_from_macro_info_dict(macro)
base_obj=addon/'mpfb/data/3dobjs/base.obj'
macro_file=addon/'mpfb/data/targets/macrodetails/macro.json'
eye_asset=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/high-poly/high-poly.mhclo')
sources={str(p):sha(p) for p in [base_obj,macro_file,eye_asset,eye_asset.with_suffix('.obj')]}
for item in target_stack:
    p=addon/'mpfb/data/targets'/(item[0]+'.target.gz')
    if not p.exists():raise RuntimeError('Native target missing: '+str(p))
    sources[str(p)]=sha(p)
body=HumanService.create_human(mask_helpers=True,detailed_helpers=True,
    extra_vertex_groups=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro)
active_keys=[dict(name=k.name,value=k.value) for k in body.data.shape_keys.key_blocks if k.name!='Basis' and abs(k.value)>1e-8]
body.name='NEW native young-adult male anatomical source'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'fresh-native-source.blend'))
# This operates on the NEW task-owned source instance, never on donor files.
TargetService.bake_targets(body)
assert body.data.shape_keys is None or len(body.data.shape_keys.key_blocks)==0
def indices(name):
    gi=body.vertex_groups[name].index
    return {v.index for v in body.data.vertices if any(g.group==gi and g.weight>.1 for g in v.groups)}
def center(name):return np.mean([body.data.vertices[i].co[:] for i in indices(name)],axis=0)
eye_centers=[center('joint-l-eye'),center('joint-r-eye')]
eye_mid=(eye_centers[0]+eye_centers[1])/2
native_ipd=float(np.linalg.norm(eye_centers[0]-eye_centers[1]))
scale=.156924/native_ipd
ty=.111-scale*eye_mid[2];tz=.169+scale*eye_mid[1]
neck_center=center('joint-neck')
cut_z=float(neck_center[2]-.035)
eye=HumanService.add_mhclo_asset(str(eye_asset),body,asset_type='Eyes',subdiv_levels=0,
    set_up_rigging=False,interpolate_weights=False,import_subrig=False,import_weights=False)
eye.name='NEW native CC0 eye surfaces fitted to baked male source'
if eye.data.shape_keys:TargetService.bake_targets(eye)
head=body.copy();head.data=body.data.copy();bpy.context.collection.objects.link(head)
head.name='UNACCEPTED native evaluated young-adult male head'
for modifier in list(head.modifiers):head.modifiers.remove(modifier)
body_ids=indices('body')
bm=bmesh.new();bm.from_mesh(head.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
remove=[face for face in bm.faces if not all(v.index in body_ids for v in face.verts)
    or min(v.co.z for v in face.verts)<cut_z]
bmesh.ops.delete(bm,geom=remove,context='FACES')
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(head.data);bm.free();head.data.update()
original_uv_layers={o.name:[u.name for u in o.data.uv_layers] for o in [head,eye]}
for o in [head,eye]:
    # Uniform source meters->Pixal-native adapter. No anisotropic scaling,
    # Gaussian displacement, source skin shrinkwrap or cosmetic texture edit.
    matrix=o.matrix_world.copy()
    for v in o.data.vertices:
        p=matrix@v.co;v.co=(scale*p.x,scale*p.y-tz,scale*p.z+ty)
    o.matrix_world.identity();o.data.update()
for o in list(bpy.context.scene.objects):
    if o not in [head,eye]:bpy.data.objects.remove(o,do_unlink=True)
for o,level in [(head,2),(eye,1)]:
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    modifier=o.modifiers.new('Native anatomical subdivision','SUBSURF');modifier.levels=level
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for poly in o.data.polygons:poly.use_smooth=True
mat=bpy.data.materials.new('Neutral gray native anatomical inspection');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
bsdf.inputs['Roughness'].default_value=.65
for o in [head,eye]:o.data.materials.clear();o.data.materials.append(mat);o.select_set(True)
bpy.context.view_layer.objects.active=head
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
head.data.calc_loop_triangles()
v=np.array([[x.co.x,x.co.z,-x.co.y] for x in head.data.vertices],dtype=np.float32)
f=np.array([t.vertices[:] for t in head.data.loop_triangles],dtype=np.int32)
np.savez(out/'head-skin.npz',vertices=v,faces=f)
report=dict(status='UNACCEPTED fresh native evaluated male alternative; parent gray judgment required',
    correctionOf='v4/v5 extracted raw Basis rather than active male/age macro mix. Manual fit failures remain2 and STOPPED.',
    macroPreset=macro,calculatedTargetStack=target_stack,actualAppliedShapeKeysBeforeBake=active_keys,
    nativeBake='TargetService.bake_targets on NEW owned instance before anatomy extraction',
    originalNativeEyeCentersMeters=[p.tolist() for p in eye_centers],originalNativeIPDMeters=native_ipd,
    adapter=dict(uniformScale=scale,verticalTranslation=ty,depthTranslation=tz,
        targetIPDNative=.156924,eyeYNative=.111,eyeZNative=.169),
    neckSourceCut=dict(jointNeckMeters=neck_center.tolist(),cutZSourceMeters=cut_z,method='temporary source-neck extraction; no accepted body join'),
    UVLayersBeforeSubdivision=original_uv_layers,UVLayersAfterSubdivision={o.name:[u.name for u in o.data.uv_layers] for o in [head,eye]},
    skinTopology=dict(vertices=len(v),triangles=len(f)),sources=sources,sourcesAfter={p:sha(p) for p in sources},
    freshSourceSHA256=sha(out/'fresh-native-source.blend'),scriptSHA256=sha(__file__),
    wallSeconds=time.monotonic()-start,
    customLandmarkDisplacements=0,denseSnaps=0,
    identityTarget='Approved buzz reference and retained NEW Pixal dense face/detail donor remain target; this native face is not claimed identical.',
    limits=['Neutral face geometry has no accepted likeness, skin texture or buzz material.',
        'Native UV layers retained; no UV layout quality or bake acceptance claimed.',
        'Neck base is temporary and unjoined; no body fit, neck movement, rig, or gameplay test.',
        'No historical donor, manual face warp, dense snap, GPU, AI sampling or texture bake.'])
assert sources==report['sourcesAfter']
(out/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
