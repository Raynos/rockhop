import bpy,sys,json
from mathutils import Matrix,Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1]);arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
b=arm.data.bones['head'];origin=b.head_local;up=(b.tail_local-b.head_local).normalized();right=Vector((0,1,0));front=right.cross(up).normalized()
def local(p):
 d=p-origin;return [d.dot(front),d.dot(right),d.dot(up)]
report={'origin':list(origin),'up':list(up),'front':list(front),'objects':[]}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 ids=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name=='head')>.95]
 ps=[local(o.matrix_world@o.data.vertices[i].co) for i in ids]
 report['objects'].append({'name':o.name,'vertices':len(o.data.vertices),'tris':sum(len(f.vertices)-2 for f in o.data.polygons),'headverts':len(ids),'headbounds':[[min(p[k] for p in ps),max(p[k] for p in ps)]for k in range(3)]if ps else None,'mat':[m.name for m in o.data.materials]})
print('HEADINFO'+json.dumps(report))
