"""Export the EXACT failed trial2 cut for diagnosis; no correction or bake."""
import argparse, ast, hashlib, json, sys
from pathlib import Path
import bpy
import numpy as np
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--scaffold',required=True);ap.add_argument('--recipe',required=True)
ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out)
out.mkdir(parents=True,exist_ok=True)
if (out/'cut.glb').exists():raise RuntimeError('Frozen diagnostic exists')
# Load only the exact pure clipping function from the frozen failed recipe.
tree=ast.parse(Path(a.recipe).read_text())
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef)
           and node.name=='clip']
exec(compile(ast.Module(body=functions,type_ignores=[]),a.recipe,'exec'),globals())
p=np.load(a.scaffold);v=p['vertices'].astype(np.float64);f=p['faces']
theta=np.arctan2(v[:,0],v[:,2]+.025);cosine=np.cos(theta)
height=np.where(cosine>=0,.13+.06*cosine,.13+.275*cosine)
v,f=clip(v,f,v[:,1]-height)
v,f=clip(v,f,-.31-v[:,1])
np.savez(out/'cut.npz',vertices=v.astype(np.float32),faces=f.astype(np.int32))
bpy.ops.wm.read_factory_settings(use_empty=True)
canonical=v[:,[0,2,1]].copy();canonical[:,1]*=-1
mesh=bpy.data.meshes.new('FAILED trial2 actual cut contours')
mesh.from_pydata(canonical.tolist(),[],f.tolist());mesh.update()
obj=bpy.data.objects.new('UNACCEPTED diagnostic only',mesh)
bpy.context.collection.objects.link(obj)
for polygon in mesh.polygons:polygon.use_smooth=True
mat=bpy.data.materials.new('Gray diagnostic');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
bsdf.inputs['Roughness'].default_value=.65;mesh.materials.append(mat)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'cut.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'cut.glb'),export_format='GLB',use_selection=True,export_yup=True)
report=dict(status='FAILED trial2 actual cut diagnostic, no correction',
            vertices=len(v),faces=len(f),source=a.scaffold,failedRecipe=a.recipe,
            sourceSHA256=hashlib.sha256(Path(a.scaffold).read_bytes()).hexdigest(),
            failedRecipeSHA256=hashlib.sha256(Path(a.recipe).read_bytes()).hexdigest(),
            diagnosticSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            limits=['No cap/dense fit because scalp-contour gate failed.',
                    'A diagnostic export is not a third corrective attempt.'])
(out/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
