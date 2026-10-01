import bpy,json,numpy as np,hashlib
from pathlib import Path
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend')
bpy.ops.wm.open_mainfile(filepath=str(source));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'body' in o.vertex_groups)
basis=np.array([v.co[:] for v in body.data.vertices]);keys=body.data.shape_keys
active=[];mix=basis.copy()
for key in keys.key_blocks:
    if key.name=='Basis' or abs(key.value)<1e-8:continue
    arr=np.array([v.co[:] for v in key.data]);mix+=(arr-basis)*key.value
    active.append(dict(name=key.name,value=key.value))
head=basis[:,2]>1.38;delta=np.linalg.norm(mix-basis,axis=1)
report=dict(status='Read-only macro capability and basis-vs-shape-key audit; no new mesh constructed',source=str(source),sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),activeShapeKeys=active,headVerticesCompared=int(head.sum()),headMaxNativeMeters=float(delta[head].max()),headMedianNativeMeters=float(np.median(delta[head])),headBasisBounds=[basis[head].min(0).tolist(),basis[head].max(0).tolist()],headMacroMixBounds=[mix[head].min(0).tolist(),mix[head].max(0).tolist()])
print(json.dumps(report));Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/mpfb-native-capability.json').write_text(json.dumps(report,indent=2)+'\n')
