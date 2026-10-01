"""Apply CPU transfer maps and NEW CC0 native brown eyes; geometry immutable."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True);ap.add_argument('--maps',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.maps)
if (out/'head.glb').exists():raise RuntimeError('Frozen textured export exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
eye_tex=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/materials/brown_eye.png')
inputs={p:sha(p) for p in [Path(a.input),eye_tex]+list(out.glob('skin-*.png'))}
bpy.ops.wm.open_mainfile(filepath=a.input)
meshes=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices))
eye,head=meshes
def geometry_sha(o):
    o.data.calc_loop_triangles()
    v=np.array([p.co[:] for p in o.data.vertices],dtype=np.float32)
    f=np.array([t.vertices[:] for t in o.data.loop_triangles],dtype=np.int32)
    uv=np.array([u.uv[:] for u in o.data.uv_layers.active.data],dtype=np.float32)
    return dict(vertices=hashlib.sha256(v.tobytes()).hexdigest(),triangles=hashlib.sha256(f.tobytes()).hexdigest(),UV=hashlib.sha256(uv.tobytes()).hexdigest())
before={o.name:geometry_sha(o) for o in meshes}
def material(name):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    return mat,mat.node_tree.nodes.get('Principled BSDF')
mat,bsdf=material('UNACCEPTED CPU Pixal attribute transfer + compact native stubble')
for name,socket in [('skin-basecolor','Base Color'),('skin-roughness','Roughness'),('skin-metallic','Metallic')]:
    image=bpy.data.images.load(str(out/(name+'.png')),check_existing=False)
    if name!='skin-basecolor':image.colorspace_settings.name='Non-Color'
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
    mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs[socket])
head.data.materials.clear();head.data.materials.append(mat)
em,ebsdf=material('NEW native CC0 brown iris/sclera PBR')
image=bpy.data.images.load(str(eye_tex),check_existing=False)
node=em.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
em.node_tree.links.new(node.outputs['Color'],ebsdf.inputs['Base Color'])
em.node_tree.links.new(node.outputs['Alpha'],ebsdf.inputs['Alpha'])
ebsdf.inputs['Roughness'].default_value=.24;ebsdf.inputs['Metallic'].default_value=0
em.surface_render_method='DITHERED'
eye.data.materials.clear();eye.data.materials.append(em)
for obj in bpy.context.scene.objects:obj.select_set(obj in meshes)
bpy.context.view_layer.objects.active=head
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
after={o.name:geometry_sha(o) for o in meshes}
assert before==after
report=dict(status='UNACCEPTED textured feasibility; parent actual appearance review',
    geometryBefore=before,geometryAfter=after,geometryAndUVUnchanged=True,
    inputs={str(p):dict(before=s,after=sha(p),unchanged=s==sha(p)) for p,s in inputs.items()},
    scriptSHA256=sha(__file__),eyePBR=dict(source=str(eye_tex),roughness=.24,metallic=0,alpha='native texture'),
    limits=['Native geometry/UVs unchanged; no shape/detail displacement.',
        'CPU texture transfer is partial and approximate; likeness/final appearance remain unaccepted.',
        'No joined neck/body, rig, moving contacts, or game-ready claim.'])
assert all(v['unchanged'] for v in report['inputs'].values())
(out/'material-application.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
