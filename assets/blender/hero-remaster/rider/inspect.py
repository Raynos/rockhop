import bpy,json,sys
from mathutils import Matrix,Vector
from pathlib import Path
p=Path(__file__).parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'work/baseline.glb'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.animation_data.action=None
for t in arm.animation_data.nla_tracks:t.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
print('RIG',arm.name, list(arm.matrix_world))
for b in arm.data.bones:print('BONE',b.name,list(b.head_local),list(b.tail_local))
for o in bpy.data.objects:
 if o.type=='MESH':
  vs=[o.matrix_world@v.co for v in o.data.vertices]
  print('MESH',o.name,len(vs),[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)])
