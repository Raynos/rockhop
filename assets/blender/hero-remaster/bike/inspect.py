import bpy,json,sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
out={}
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  bb=[o.matrix_world@Vector(v) for v in o.bound_box]
  out[o.name]={'tris':sum(len(p.vertices)-2 for p in o.data.polygons),'location':list(o.location),'matrix':[list(r) for r in o.matrix_world],'min':[min(p[i] for p in bb) for i in range(3)],'max':[max(p[i] for p in bb) for i in range(3)],'mats':[m.name for m in o.data.materials]}
print('INSPECT '+json.dumps(out))
