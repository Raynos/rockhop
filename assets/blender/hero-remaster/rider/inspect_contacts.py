import bpy
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'candidate-v3.glb'))
for o in bpy.data.objects:
 if o.type=='MESH':
  print(o.name,'MAT',list(o.matrix_world),'BOUNDS',[(min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)) for i in range(3)])
  if 'Authored' in o.name:
   names={g.index:g.name for g in o.vertex_groups}
   rows=sorted([(sum(g.weight for g in v.groups if names[g.group].startswith(('hand','foot'))),v.index,tuple(v.co),[(names[g.group],g.weight) for g in v.groups]) for v in o.data.vertices])
   print('CONTACTBAD',rows[:10])
