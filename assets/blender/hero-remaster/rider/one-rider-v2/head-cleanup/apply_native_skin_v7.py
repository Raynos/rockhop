"""One direct installed native-UV skin fallback; no geometry or UV edits."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input',required=True);ap.add_argument('--skin',required=True);ap.add_argument('--material',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'head.glb').exists():raise RuntimeError('Frozen native skin result exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
eye_tex=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/materials/brown_eye.png')
inputs={str(p):sha(p) for p in [Path(a.input),Path(a.skin),Path(a.material),eye_tex]}
bpy.ops.wm.open_mainfile(filepath=a.input)
meshes=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:len(o.data.vertices));eye,head=meshes
def geometry_sha(o):
    o.data.calc_loop_triangles()
    v=np.array([p.co[:] for p in o.data.vertices],dtype=np.float32)
    f=np.array([t.vertices[:] for t in o.data.loop_triangles],dtype=np.int32)
    uv=np.array([u.uv[:] for u in o.data.uv_layers.active.data],dtype=np.float32)
    return dict(vertices=hashlib.sha256(v.tobytes()).hexdigest(),triangles=hashlib.sha256(f.tobytes()).hexdigest(),UV=hashlib.sha256(uv.tobytes()).hexdigest())
before={o.name:geometry_sha(o) for o in meshes}
def assign(o,name,path,roughness,alpha=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    image=bpy.data.images.load(str(path),check_existing=False)
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
    mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    if alpha:
        mat.node_tree.links.new(node.outputs['Alpha'],bsdf.inputs['Alpha']);mat.surface_render_method='DITHERED'
    bsdf.inputs['Roughness'].default_value=roughness;bsdf.inputs['Metallic'].default_value=0
    o.data.materials.clear();o.data.materials.append(mat)
assign(head,'UNACCEPTED direct native CC0 young male skin fallback',Path(a.skin),.58)
assign(eye,'NEW native CC0 brown iris/sclera',eye_tex,.24,True)
for obj in bpy.context.scene.objects:obj.select_set(obj in meshes)
bpy.context.view_layer.objects.active=head
bpy.ops.wm.save_as_mainfile(filepath=str(out/'head.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'head.glb'),export_format='GLB',use_selection=True,export_yup=True)
after={o.name:geometry_sha(o) for o in meshes};assert before==after
report=dict(status='UNACCEPTED explicit native skin fallback alternative; parent actual appearance review',
    geometryBefore=before,geometryAfter=after,geometryAndUVUnchanged=True,
    sources={p:dict(before=s,after=sha(p),unchanged=s==sha(p)) for p,s in inputs.items()},
    scriptSHA256=sha(__file__),skinDiffuse=str(a.skin),skinRoughness=.58,skinMetallic=0,
    eyeDiffuse=str(eye_tex),eyeRoughness=.24,eyeMetallic=0,
    mapping='Direct matching native UVMap; no nearest color projection, no texture coordinate warps.',
    scalp='Native diffuse includes painted short stubble on same continuous native scalp; no separate shell or added dark mask.',
    identity='Approved Pixal/buzz reference remains target; this is an explicitly chosen native skin fallback, not claimed donor detail or exact likeness.',
    limits=['Installed native skin provides diffuse only; roughness/metallic are authored constants, no full PBR map-set or normal/displacement bake.',
        'No native texture edits; source diffuse/UV/source geometry untouched.',
        'Native head/skin identity remains approximate versus approved reference.',
        'Temporary neck base remains jagged/unjoined; no body fit, rig, animation or game-ready claim.'])
assert all(x['unchanged'] for x in report['sources'].values())
(out/'material-application.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
