import bpy,json
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
p=Path(__file__).resolve().parent/'rig-source-decoded.glb'
bpy.ops.import_scene.gltf(filepath=str(p))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE')
r={'source':str(p),'rigMatrix':list(list(row) for row in a.matrix_world),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':list(list(row) for row in b.matrix_local)} for b in a.data.bones},'sockets':{o.name:list(list(row) for row in o.matrix_local) for o in bpy.data.objects if o.type=='EMPTY'},'actions':[ac.name for ac in bpy.data.actions]}
(Path(__file__).resolve().parent/'rig-numbers.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='bones'}))
for b in a.data.bones:print(b.name,list(b.head_local),list(b.tail_local))
