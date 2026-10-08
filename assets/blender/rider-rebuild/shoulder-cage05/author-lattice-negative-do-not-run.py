"""Save an editable real selected-PBR cage garment in the dressed master.

SOURCE ONLY: parent checkpoint and global serial CPU2 lease before Blender.
No bake, body edit, projection, retopology, field transfer or player export.
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[4]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()

def pin(row):
    path=ROOT/row['path']
    assert path.is_file() and sha(path)==row['sha256'],('Changed source',row)
    return path

def geometry_uv_signature(mesh):
    h=hashlib.sha256()
    for name,items,field,dtype,width in [
        ('positions',mesh.vertices,'co',np.float32,3),
        ('corners',mesh.loops,'vertex_index',np.int32,1),
        ('polygonSizes',mesh.polygons,'loop_total',np.int32,1)]:
        a=np.empty(len(items)*width,dtype=dtype);items.foreach_get(field,a)
        h.update(name.encode());h.update(a.tobytes())
    for layer in mesh.uv_layers:
        a=np.empty(len(mesh.loops)*2,dtype=np.float32);layer.data.foreach_get('uv',a)
        h.update(layer.name.encode());h.update(a.tobytes())
    return h.hexdigest()

def packed_maps(obj):
    result={}
    for material in obj.data.materials:
        assert material and material.use_nodes
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                image=node.image
                assert image.packed_file,('Actual selected map not packed',image.name)
                result[image.name]={'sha256':hashlib.sha256(image.packed_file.data).hexdigest(),
                                    'pixels':list(image.size)}
    return result

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    controls_path,out=(Path(a).resolve() for a in args)
    controls=json.loads(controls_path.read_text())
    assert controls['accepted'] is False
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/shoulder-cage05') and not out.exists()
    for value in controls.values():
        if isinstance(value,dict) and 'path' in value and 'sha256' in value:pin(value)
    helper=runpy.run_path(str(pin(controls['signatureHelper'])))
    bpy.ops.wm.open_mainfile(filepath=str(pin(controls['incomingNative'])))
    body=bpy.data.objects[controls['body']];rig=bpy.data.objects[controls['rig']]
    assert len(rig.data.bones)==75
    assert helper['signature'](body,rig)==controls['bodyRigSignature']
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    old=bpy.data.objects[controls['visibleOldHoodie']]
    assert old.type=='MESH' and not old.hide_render
    visible_before=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    assert len(visible_before)==7
    other_visible={o.name:(o.data.as_pointer(),o.matrix_world.copy(),
        [(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers])
        for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o!=old}
    source=pin(controls['originalDensePBR'])
    with source.open('rb') as f:
        _,_,_,size,_=struct.unpack('<5I',f.read(20));doc=json.loads(f.read(size))
    assert len(doc['nodes'])==len(doc['meshes'])==1
    assert not any(k in doc['nodes'][0] for k in ('matrix','rotation','translation','scale','skin'))
    accessor=doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(source))
    imported=set(bpy.data.objects)-before
    meshes=[o for o in imported if o.type=='MESH'];assert len(meshes)==1
    garment=meshes[0]
    assert len(garment.data.vertices)==controls['sourceVertices']
    assert len(garment.data.polygons)==controls['sourcePolygons']
    assert garment.matrix_world.is_identity and garment.parent is None
    xyz=np.empty(len(garment.data.vertices)*3,dtype=np.float32)
    garment.data.vertices.foreach_get('co',xyz);xyz=xyz.reshape((-1,3))
    axis=np.array(controls['gltfToBlenderRows'])
    expected=np.array([axis@np.array([x,y,z]) for x in (accessor['min'][0],accessor['max'][0])
        for y in (accessor['min'][1],accessor['max'][1]) for z in (accessor['min'][2],accessor['max'][2])])
    imported_bounds=[xyz.min(0).tolist(),xyz.max(0).tolist()]
    assert np.max(abs(np.array(imported_bounds)-np.array([expected.min(0),expected.max(0)])))<1e-5
    source_signature=geometry_uv_signature(garment.data)
    maps=packed_maps(garment)
    assert set(controls['originalPBRHashes'])=={v['sha256'] for v in maps.values()}
    assert all(v['pixels']==[4096,4096] for v in maps.values())
    collection=bpy.data.collections.new('Hoodie cage05 | editable original selected PBR | UNACCEPTED')
    bpy.context.scene.collection.children.link(collection)
    for obj in imported:
        collection.objects.link(obj)
        for previous in list(obj.users_collection):
            if previous!=collection:previous.objects.unlink(obj)
    garment.name='Hoodie__ActualSelectedPBR_Cage05'
    affine=controls['sourceDisplayAffine'];garment.matrix_world=Matrix.Diagonal(Vector((*affine['scale'],1)))
    garment.matrix_world.translation=Vector(affine['translation'])
    garment['originalSelectedGLBSHA256']=controls['originalDensePBR']['sha256']
    garment['originalVertexIdentity']='Mesh vertex index, unchanged original GLB import'
    garment['acceptedArt']=False;garment['privateAuthoringContext']=True
    garment['contextStatus']='EDITABLE_CAGE_REST_FIT_PENDING_PARENT_JUDGMENT_UNRIGGED'
    lattice_controls=controls['lattice'];counts=lattice_controls['counts']
    data=bpy.data.lattices.new('Selected shoulder armhole sculpt | named anatomical controls')
    data.points_u,data.points_v,data.points_w=counts
    data.interpolation_type_u=data.interpolation_type_v=data.interpolation_type_w=lattice_controls['interpolation']
    data.use_outside=False
    cage=bpy.data.objects.new('Hoodie_Cage05_EditableAnatomicalControls',data)
    collection.objects.link(cage)
    actual=np.array([p.co[:] for p in data.points]);lo=actual.min(0);hi=actual.max(0)
    world_lo=np.array(lattice_controls['worldMin']);world_hi=np.array(lattice_controls['worldMax'])
    scale=(world_hi-world_lo)/(hi-lo);translation=world_lo-lo*scale
    cage.matrix_world=Matrix.Diagonal(Vector((*scale,1)))
    cage.matrix_world.translation=Vector(translation)
    inverse=cage.matrix_world.inverted()
    assert len(data.points)==len(lattice_controls['points'])
    for point,row in zip(data.points,lattice_controls['points']):
        assert (cage.matrix_world@point.co-Vector(row['sourceWorld'])).length<1e-5,('Lattice point order',row['index'])
        point.co_deform=inverse@Vector(row['deformedWorld'])
    for name,ids in lattice_controls['namedControlPointGroups'].items():
        group=cage.vertex_groups.new(name=name)
        if ids:group.add(ids,1,'REPLACE')
    cage.show_in_front=True;cage.hide_render=True;cage.display_type='WIRE'
    cage['acceptedArt']=False;cage['controlSourceSHA256']=sha(controls_path)
    cage['editInstructions']='Edit lattice points; named vertex groups select anatomical neighborhoods. Marker empties document anchors and do not drive deformation.'
    modifier=garment.modifiers.new('Editable selected shoulder and armhole cage05','LATTICE')
    modifier.object=cage;modifier.strength=1;modifier.show_in_editmode=True
    for name,row in controls['landmarks'].items():
        marker=bpy.data.objects.new('Cage05_anchor_'+name,None);collection.objects.link(marker)
        marker.location=row['target'];marker.empty_display_type='SPHERE';marker.empty_display_size=.008
        marker.hide_render=True;marker.hide_set(True)
        marker['sourceWorld']=row['source'];marker['targetWorld']=row['target']
        marker['role']='Documented source/target pose anchor; edit actual lattice points to sculpt'
    old.hide_render=True;old.hide_set(True)
    old['contextStatus']='FAILED_CORRECTED04_SHOULDER_RETAINED_TOGGLEABLE_REFERENCE'
    garment.hide_render=False;garment.hide_set(False)
    assert geometry_uv_signature(garment.data)==source_signature
    assert packed_maps(garment)==maps
    assert helper['signature'](body,rig)==controls['bodyRigSignature']
    for name,(pointer,matrix,modifiers) in other_visible.items():
        obj=bpy.data.objects[name]
        assert obj.data.as_pointer()==pointer and obj.matrix_world==matrix
        assert [(m.name,m.type,m.show_viewport,m.show_render) for m in obj.modifiers]==modifiers
        assert not obj.hide_render
    visible=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render)
    assert len(visible)==7 and body.name in visible and garment.name in visible
    assert not any(m.type=='ARMATURE' for m in garment.modifiers)
    out.mkdir(parents=True)
    native=out/'selected-cage-outfit.blend'
    notes=bpy.data.texts.new('CAGE05_ACTUAL_SELECTED_PBR_UNACCEPTED')
    notes.write(json.dumps({'controls':controls,'visibleMeshes':visible},indent=2))
    bpy.context.view_layer.objects.active=garment
    for obj in bpy.context.selected_objects:obj.select_set(False)
    garment.select_set(True)
    # Save the actual editable geometry and original PBR before any views or
    # field transfer. Lattice evaluation remains editable and is not applied.
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    receipt={'accepted':False,'stage':'SAVED_EDITABLE_ACTUAL_SELECTED_PBR_CAGE_PENDING_REST_REVIEW',
        'controls':{'path':str(controls_path.relative_to(ROOT)),'sha256':sha(controls_path)},
        'author':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(__file__)},
        'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},
        'incomingNative':controls['incomingNative'],'originalDensePBR':controls['originalDensePBR'],
        'bodyAnd75RigSignature':controls['bodyRigSignature'],'originalBaseGeometryAndUVSignature':source_signature,
        'originalImportedBounds':imported_bounds,'sourceVertices':len(garment.data.vertices),
        'sourcePolygons':len(garment.data.polygons),'packedOriginalPBR':maps,
        'latticeCounts':counts,'editableLatticePoints':len(data.points),'visibleMeshes':visible,
        'garmentRigged':False,'limits':controls['limits']}
    (out/'author.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
