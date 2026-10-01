"""Reopen cage04 and measure actual Blender precision rather than claim parity."""
import bpy, hashlib, json
import numpy as np
from pathlib import Path
run=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/cage04')
bpy.ops.wm.open_mainfile(filepath=str(run/'fit04.blend'))
objects=list(bpy.data.objects);assert len(objects)==1 and objects[0].type=='MESH'
o=objects[0];field=np.load(run/'fit04.npz')
P=np.array([(v.co.x,v.co.z,-v.co.y) for v in o.data.vertices])
Q=np.array([list(p.vertices) for p in o.data.polygons])
uv=np.array([list(loop.uv) for loop in o.data.uv_layers.active.data])
weights=np.zeros_like(field['weights'])
for vertex in o.data.vertices:
    for group in vertex.groups:weights[vertex.index,group.group]=group.weight
assert np.array_equal(Q,field['quads']) and len(o.vertex_groups)==19
errors={'positionMaxErrorM':float(abs(P-field['positions']).max()),
        'weightMaxError':float(abs(weights-field['weights']).max()),
        'uvMaxError':float(abs(uv-field['uvLoops']).max())}
assert errors['positionMaxErrorM']<1e-6 and errors['weightMaxError']<1e-6 and errors['uvMaxError']<1e-6
out=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cage04')
report=json.loads((out/'master-report.json').read_text());report.pop('nativeWeightsUVTopologyExact',None)
report.update(nativeFieldsExactBeforeBlenderStorage=True,masterReopened=True,
              masterQuadsExact=True,masterVertexGroupCount=19,blenderFloatStorageErrors=errors)
assert hashlib.sha256((run/'fit04.blend').read_bytes()).hexdigest()==report['sha256']
(out/'master-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(errors))
