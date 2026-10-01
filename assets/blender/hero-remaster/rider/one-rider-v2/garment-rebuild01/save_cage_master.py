"""Save editable unbound cage04 construction master with exact native fields."""
import bpy, json, hashlib
from pathlib import Path
import numpy as np
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
run=root/'cage04';f=np.load(run/'fit04.npz');original=np.load(root/'fit01.npz')
for key in ['weights','quads','uvLoops']:assert np.array_equal(f[key],original[key])
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh=bpy.data.meshes.new('Source_cross_section_clean_garment04')
mesh.from_pydata([(p[0],-p[2],p[1]) for p in f['positions']],[],f['quads'].tolist());mesh.update()
obj=bpy.data.objects.new('Clean_source_cage04_UNACCEPTED',mesh);bpy.context.collection.objects.link(obj)
layer=mesh.uv_layers.new(name='Native_garment_bake_UV')
for loop,uv in zip(layer.data,f['uvLoops']):loop.uv=uv
names=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
for name in names:obj.vertex_groups.new(name=name)
for i,weights in enumerate(f['weights']):
    for j,w in enumerate(weights):
        if w>0:obj.vertex_groups[j].add([i],float(w),'REPLACE')
for polygon in mesh.polygons:polygon.use_smooth=True
master=run/'fit04.blend';assert not master.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(master),compress=True)
out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cage04')
(out/'master-report.json').write_text(json.dumps({'master':str(master),'sha256':hashlib.sha256(master.read_bytes()).hexdigest(),
 'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'nativeFieldsExactBeforeBlenderStorage':True,
 'armatureCount':0,'status':'Editable unbound construction master, not a complete rigged character'},indent=2)+'\n')
