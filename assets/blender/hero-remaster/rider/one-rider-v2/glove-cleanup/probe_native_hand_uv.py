"""Read-only probe of native unposed hand UV layouts."""
import bpy,json
from pathlib import Path
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/neutral-anatomical-hands.blend')
bpy.ops.wm.open_mainfile(filepath=str(source))
for obj in bpy.context.scene.objects:
    if obj.type=='MESH':
        print('NATIVE_HAND_UV',obj.name,len(obj.data.vertices),len(obj.data.polygons),[(layer.name,len(layer.data)) for layer in obj.data.uv_layers],flush=True)
        if obj.data.uv_layers.active:
            uv=obj.data.uv_layers.active
            values=[tuple(v.uv) for v in uv.data]
            print('UV_BOUNDS',[[min(v[i] for v in values),max(v[i] for v in values)] for i in range(2)],'DISTINCT',len(set(values)),flush=True)
