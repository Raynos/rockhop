"""Audit frozen original native data and unchanged material-test geometry."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['original','candidate','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);original,candidate,out=[Path(getattr(a,k)).resolve() for k in ['original','candidate','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [original,candidate]}
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));meshes={};materials={};images={}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        m=o.data;h=hashlib.sha256()
        for collection,key,width,dtype in [(m.vertices,'co',3,np.float32),(m.loops,'vertex_index',1,np.int32),(m.polygons,'loop_start',1,np.int32),(m.polygons,'loop_total',1,np.int32),(m.polygons,'material_index',1,np.int32),(m.polygons,'use_smooth',1,np.bool_)]:
            v=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(key,v);h.update(v.tobytes())
        for u in m.uv_layers:
            v=np.empty(len(u.data)*2,dtype=np.float32);u.data.foreach_get('uv',v);h.update(u.name.encode());h.update(v.tobytes())
        h.update(json.dumps([(v.index,[(o.vertex_groups[g.group].name,float(g.weight)) for g in v.groups]) for v in m.vertices if v.groups],separators=(',',':')).encode())
        h.update(json.dumps({'world':list(map(list,o.matrix_world)),'materials':[x.name for x in m.materials]},sort_keys=True).encode())
        meshes[o.name]=h.hexdigest()
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        nodes=[]
        for n in m.node_tree.nodes:
            inputs={}
            for s in n.inputs:
                if hasattr(s,'default_value'):
                    v=s.default_value;inputs[s.name]=list(v) if hasattr(v,'__len__') and not isinstance(v,str) else v
            nodes.append([n.name,n.type,inputs,n.image.name if n.type=='TEX_IMAGE' and n.image else None])
        materials[m.name]=hashlib.sha256(json.dumps([nodes,[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]],sort_keys=True).encode()).hexdigest()
    for im in bpy.data.images:
        data=im.packed_file.data if im.packed_file else Path(bpy.path.abspath(im.filepath)).read_bytes() if im.filepath and Path(bpy.path.abspath(im.filepath)).is_file() else b''
        images[im.name]=[hashlib.sha256(data).hexdigest(),list(im.size),im.colorspace_settings.name]
    r=bpy.data.objects['Independent anatomical foundation rig']
    bones=[[b.name,list(map(list,b.matrix_local)),list(map(list,r.pose.bones[b.name].matrix_basis)),b.use_deform] for b in r.data.bones]
    return {'meshes':meshes,'materials':materials,'images':images,'bones':bones}
before=snapshot(original);after=snapshot(candidate)
for kind in ['meshes','materials','images']:
    assert all(after[kind].get(name)==value for name,value in before[kind].items()),kind
assert before['bones']==after['bones']
old=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged'].data
new=bpy.data.objects['Selected donor direct-UV transfer on unchanged source13, unaccepted'].data
assert [v.co[:] for v in old.vertices]==[v.co[:] for v in new.vertices]
assert [p.vertices[:] for p in old.polygons]==[p.vertices[:] for p in new.polygons]
assert [[u.uv[:] for u in layer.data] for layer in old.uv_layers]==[[u.uv[:] for u in layer.data] for layer in new.uv_layers]
report={'status':'UNACCEPTED transfer source-preservation preflight, no art/wearing acceptance','pins':pins,'recipeSHA256':sha(__file__),'originalCounts':{k:len(v) for k,v in before.items()},'originalNativeDataExact':True,'candidateCoordinatesPolygonsUVExactToFrozenSource13':True,'snapshots':before,'limits':['Original object render/hide state changes to display derivative; native geometry, groups, UVs, materials, images and51bind/pose unchanged.','No played shape/material acceptance or moving/collision/iOS qualification.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('TRANSFER_SOURCE_EXACT',report['originalCounts'],flush=True)
