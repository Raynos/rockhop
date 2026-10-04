"""Read frozen native controls and candidate arrays; never save/render/evaluate."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
out=Path(__file__).resolve().parent;root=out.parents[4]
prep=json.loads((out.parent/'neck61/preparation.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'
paths={'baseline':asset/'selected-hoodie26/native-four-with-full-control.blend','failed':asset/'neck-interface27/bounded-neck-join.blend','candidate':asset/'neck-interface27/bounded-neck-join-triangulated.blend'}
arrays={};reports={}
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def serial(v):
 if v is None or isinstance(v,(str,int,float,bool)):return v
 if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name,v.library.filepath if v.library else None]
 if isinstance(v,set):return sorted(v)
 if hasattr(v,'to_dict'):return {k:serial(x) for k,x in v.to_dict().items()}
 return [serial(x) for x in v]
def props(x):
 d={}
 for p in x.bl_rna.properties:
  if p.identifier=='rna_type' or p.is_readonly or p.type=='COLLECTION':continue
  v=getattr(x,p.identifier)
  d[p.identifier]=([v.bl_rna.identifier] if v is not None and p.type=='POINTER' and not isinstance(v,bpy.types.ID) else serial(v))
 return d
def custom(x):
 try:return {k:serial(v) for k,v in x.items()}
 except TypeError:return {}
def flat(collection,key,width,dtype):
 a=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(key,a);return a.reshape(-1,width)
def attrs(mesh):
 result={}
 for a in mesh.attributes:
  fields={}
  if len(a.data):
   for prop in a.data[0].bl_rna.properties:
    if prop.identifier=='rna_type':continue
    assert prop.type in ['FLOAT','INT','BOOLEAN','STRING'],(a.name,prop.identifier,prop.type)
    if prop.type=='STRING':v=np.array([getattr(x,prop.identifier) for x in a.data])
    else:v=flat(a.data,prop.identifier,max(1,prop.array_length),np.float32 if prop.type=='FLOAT' else np.bool_ if prop.type=='BOOLEAN' else np.int32)
    fields[prop.identifier]=v
  result[a.name]={'kind':a.data_type,'domain':a.domain,'fields':fields}
 return result
def state(o):
 d={'type':o.type,'world':serial(o.matrix_world),'basis':serial(o.matrix_basis),'local':serial(o.matrix_local),'parentInverse':serial(o.matrix_parent_inverse),'parent':serial(o.parent),'parentType':o.parent_type,'parentBone':o.parent_bone,'properties':custom(o),'modifiers':[{'kind':m.type,'properties':props(m),'custom':custom(m)} for m in o.modifiers],'constraints':[props(c) for c in o.constraints]}
 if o.type=='MESH':
  m=o.data;a=attrs(m);d['mesh']={'positions':digest(flat(m.vertices,'co',3,np.float32)),'polygons':digest(flat(m.polygons,'loop_total',1,np.int32)),'loops':digest(flat(m.loops,'vertex_index',1,np.int32)),'edges':digest(flat(m.edges,'vertices',2,np.int32)),'materials':[serial(x) for x in m.materials],'smooth':digest(flat(m.polygons,'use_smooth',1,np.bool_)),'materialIndices':digest(flat(m.polygons,'material_index',1,np.int32)),'weights':digest(np.array([[v.index,g.group,g.weight] for v in m.vertices for g in v.groups],dtype=np.float64)),'groups':[g.name for g in o.vertex_groups],'attributes':{n:{'kind':x['kind'],'domain':x['domain'],'fields':{k:digest(v) for k,v in x['fields'].items()}} for n,x in a.items()},'hasCustomNormals':m.has_custom_normals,'cornerNormals':digest(flat(m.corner_normals,'vector',3,np.float32)),'shapeKeys':None if not m.shape_keys else {k.name:digest(flat(k.data,'co',3,np.float32)) for k in m.shape_keys.key_blocks}}
 if o.type=='ARMATURE':
  d['armature']={'dataProperties':props(o.data),'bones':{b.name:{'rest':serial(b.matrix_local),'properties':props(b),'custom':custom(b)} for b in o.data.bones},'pose':{b.name:{'matrix':serial(b.matrix),'basis':serial(b.matrix_basis),'properties':props(b),'custom':custom(b),'constraints':[props(c) for c in b.constraints]} for b in o.pose.bones}}
 return d
def materials():
 r={}
 for m in bpy.data.materials:
  x={'properties':props(m),'custom':custom(m),'nodes':{},'links':[]}
  if m.node_tree:
   for n in m.node_tree.nodes:
    x['nodes'][n.name]={'type':n.bl_idname,'properties':props(n),'inputs':{s.identifier:serial(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'outputs':{s.identifier:serial(s.default_value) for s in n.outputs if hasattr(s,'default_value')}}
   x['links']=sorted([[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links])
  r[m.name]=x
 return r
for label,path in paths.items():
 bpy.ops.wm.open_mainfile(filepath=str(path))
 reports[label]={'objects':{o.name:state(o) for o in bpy.data.objects},'images':{im.name:{'packed':sha_data if False else hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'size':list(im.size),'colour':im.colorspace_settings.name,'filepath':im.filepath} for im in bpy.data.images},'materials':materials()}
 names=list(bpy.data.objects['Independent anatomical foundation rig'].data.bones.keys())
 for part,name in [('body','Canonical body with hidden head interface'),('head','Protected textured head above hidden neck interface')]:
  labels=['source'] if label=='baseline' else ['full','four']
  for field in labels:
   obj=bpy.data.objects[name if label=='baseline' else 'Bounded neck27 '+('triangulated ' if label=='candidate' else '')+part+' '+field+', unaccepted'];m=obj.data;m.calc_loop_triangles();key=label+'_'+part+'_'+field
   d={'positions':flat(m.vertices,'co',3,np.float32),'loopVertices':flat(m.loops,'vertex_index',1,np.int32).ravel(),'polygonStarts':flat(m.polygons,'loop_start',1,np.int32).ravel(),'polygonCounts':flat(m.polygons,'loop_total',1,np.int32).ravel(),'triangleVertices':np.array([t.vertices[:] for t in m.loop_triangles],dtype=np.int32),'trianglePolygons':np.array([t.polygon_index for t in m.loop_triangles],dtype=np.int32),'triangleLoops':np.array([t.loops[:] for t in m.loop_triangles],dtype=np.int32),'edges':flat(m.edges,'vertices',2,np.int32),'smooth':flat(m.polygons,'use_smooth',1,np.bool_).ravel(),'materialIndices':flat(m.polygons,'material_index',1,np.int32).ravel(),'weights':np.zeros((len(m.vertices),len(names)),dtype=np.float32)}
   for v in m.vertices:
    for g in v.groups:d['weights'][v.index,names.index(obj.vertex_groups[g.group].name)]=g.weight
   metadata={}
   for an,a in attrs(m).items():
    metadata[an]={'kind':a['kind'],'domain':a['domain'],'fields':{}}
    for fn,value in a['fields'].items():
     ref=key+'_attribute_'+an+'_'+fn;arrays[ref]=value;metadata[an]['fields'][fn]=ref
   reports[label].setdefault('domains',{})[part+'_'+field]={'attributes':metadata,'world':serial(obj.matrix_world),'materialNames':[x.name if x else None for x in m.materials]}
   arrays.update({key+'_'+k:v for k,v in d.items()})
 reports[label]['bones']=names
 print('READ_ONLY_NATIVE',label,len(reports[label]['objects']),flush=True)
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
np.savez_compressed(out/'native-read.npz',**arrays)
report={'status':'UNACCEPTED_INDEPENDENT_READ_ONLY_NATIVE_SNAPSHOT','blenderVersion':bpy.app.version_string,'recipeSHA256':sha(__file__),'nativeReadNPZ_SHA256':sha(out/'native-read.npz'),'preparationSHA256':sha(out.parent/'neck61/preparation.json'),'snapshots':reports,'limits':['Stored rest and object/material/configuration fields only; no dependency-graph pose evaluation, render, export, native save or source edit.','Configurable RNA excludes read-only runtime and generic collections beyond explicit object/mesh/bone/material inventories. Animation curves/NLA and external linked-file contents are not certified.','Scope/topology independently assessed next; no contact, dynamic, appearance, device or promotion pass.']}
(out/'native-read.json').write_text(json.dumps(report,indent=2)+'\n')
print('READ_ONLY_SNAPSHOTS_SAVED',len(arrays),flush=True)
