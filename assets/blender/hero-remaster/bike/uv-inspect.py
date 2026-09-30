import bpy,sys,json
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 a=o.data.uv_layers.active
 if a:
  uv=[tuple(x.uv) for x in a.data];print(o.name,len(uv),min(x[0] for x in uv),max(x[0] for x in uv),min(x[1] for x in uv),max(x[1] for x in uv))
