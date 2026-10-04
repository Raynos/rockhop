"""Extend frozen body/head preservation to attributes, normals and rig state."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['original','candidate','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);original,candidate,out=[Path(getattr(a,k)).resolve() for k in ['original','candidate','out']];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [original,candidate]};assert pins[str(candidate)]=='86b85d476b13f709ba832e11dfcd14a17f071f5af69f3ebbbaf7dd1dbe6f58f9'
names=['Canonical anatomical body, baked adult hm08','Canonical body with hidden head interface','Full native diagnostic body','Protected textured head above hidden neck interface','Protected coherent cheek patch','Protected mustard hood on own rig'];rigName='Independent anatomical foundation rig'
def value(x):
    if x is None or isinstance(x,(str,bool,int,float)):return x
    if isinstance(x,set):return sorted(x)
    if isinstance(x,bpy.types.ID):return {'idType':x.bl_rna.identifier,'name':x.name,'library':x.library.filepath if x.library else None}
    if hasattr(x,'to_list'):return [value(v) for v in x.to_list()]
    if hasattr(x,'to_dict'):return {k:value(v) for k,v in x.to_dict().items()}
    try:return [value(v) for v in x]
    except TypeError:raise TypeError('Unsupported RNA value '+str(type(x)))
def custom_properties(x):
    try:return {'supported':True,'values':{k:value(v) for k,v in x.items()}}
    except TypeError:return {'supported':False,'values':{}}
def properties(x):
    result={}
    for p in x.bl_rna.properties:
        if p.identifier=='rna_type' or p.is_readonly or p.type=='COLLECTION':continue
        if p.type=='POINTER':
            obj=getattr(x,p.identifier);result[p.identifier]=None if obj is None else value(obj) if isinstance(obj,bpy.types.ID) else {'rnaType':obj.bl_rna.identifier}
        else:result[p.identifier]=value(getattr(x,p.identifier))
    return result
def array_digest(collection,field,width=1,dtype=np.float32):
    values=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(field,values);return {'count':len(collection),'width':width,'dtype':str(values.dtype),'sha256':hashlib.sha256(values.tobytes()).hexdigest()}
def mesh_extra(mesh):
    attrs={}
    for attr in mesh.attributes:
        fields={}
        if attr.data:
            for p in attr.data[0].bl_rna.properties:
                if p.identifier=='rna_type':continue
                assert p.type in ['FLOAT','INT','BOOLEAN','STRING'],(attr.name,p.identifier,p.type)
                if p.type=='STRING':fields[p.identifier]=hashlib.sha256(json.dumps([getattr(x,p.identifier) for x in attr.data]).encode()).hexdigest()
                else:fields[p.identifier]=array_digest(attr.data,p.identifier,max(1,p.array_length),np.float32 if p.type=='FLOAT' else np.int32 if p.type=='INT' else np.bool_)
        attrs[attr.name]={'type':attr.data_type,'domain':attr.domain,'elements':len(attr.data),'fields':fields}
    shape=None
    if mesh.shape_keys:
        shape={'properties':properties(mesh.shape_keys),'blocks':{key.name:{'properties':properties(key),'relativeKey':key.relative_key.name if key.relative_key else None,'coordinates':array_digest(key.data,'co',3)} for key in mesh.shape_keys.key_blocks}}
    return {'attributes':attrs,'hasCustomNormals':mesh.has_custom_normals,'cornerNormals':array_digest(mesh.corner_normals,'vector',3),'vertexNormals':array_digest(mesh.vertices,'normal',3),'polygonNormals':array_digest(mesh.polygons,'normal',3),'shapeKeys':shape}
def object_state(obj):return {'world':value(obj.matrix_world),'basis':value(obj.matrix_basis),'local':value(obj.matrix_local),'parentInverse':value(obj.matrix_parent_inverse),'parent':obj.parent.name if obj.parent else None,'parentType':obj.parent_type,'parentBone':obj.parent_bone,'modifiers':[{'type':m.type,'properties':properties(m),'customProperties':custom_properties(m)} for m in obj.modifiers],'constraints':[{'type':c.type,'properties':properties(c)} for c in obj.constraints]}
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));objects={}
    for name in names:
        obj=bpy.data.objects[name];objects[name]={'object':object_state(obj),'mesh':mesh_extra(obj.data)}
    rig=bpy.data.objects[rigName];bones={b.name:{'matrix':value(b.matrix),'basis':value(b.matrix_basis),'poseProperties':properties(b),'constraints':[{'type':c.type,'properties':properties(c)} for c in b.constraints],'customProperties':custom_properties(b)} for b in rig.pose.bones}
    return {'protectedMeshes':objects,'rigObject':object_state(rig),'rigDataProperties':properties(rig.data),'poseBones':bones}
before=snapshot(original);after=snapshot(candidate);assert before==after,'Extended protected data mismatch';assert len(before['poseBones'])==51;result={'status':'UNACCEPTED extended protected native data equality audit','pins':pins,'recipeSHA256':sha(__file__),'protectedMeshes':len(names),'bones':51,'extendedScopeExact':True,'snapshots':before,'scope':['Six protected body/head/cheek/hood meshes: every exposed generic attribute field (including raw head custom_normal and sharp flags), actual corner/vertex/polygon normals, shape-key blocks/properties.','All configurable modifier/constraint RNA, ID custom properties, object parent/basis/local/world matrices; independent rig object/data and51pose matrices/configurable properties/constraints.','Existing original-data audit separately covers29original geometries/UV/material graphs/images/51rest+pose.'],'limits':['RNA snapshots exclude read-only runtime properties, collection-valued configuration beyond explicitly enumerated modifiers/constraints/key blocks/pose bones, animation F-curves/NLA and external linked-file contents. Exact equality is only the stated scope.','No source save/body-head-51bind mutation, capture/rig/motion/promotion or wearer/art/M0-M5/mobile acceptance.']};assert pins=={x:sha(x) for x in pins};out.write_text(json.dumps(result,indent=2)+'\n');print('EXTENDED_PROTECTED_DATA_EXACT','meshes',len(names),'bones',51,flush=True)
