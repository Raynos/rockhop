"""Save an editable real selected-PBR source-pose garment in the dressed master.

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

def geometry_uv_signature(mesh, positions=True):
    h=hashlib.sha256()
    for name,items,field,dtype,width in [
        ('positions',mesh.vertices,'co',np.float32,3),
        ('corners',mesh.loops,'vertex_index',np.int32,1),
        ('polygonSizes',mesh.polygons,'loop_total',np.int32,1)]:
        if name=='positions' and not positions:continue
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
    garment['contextStatus']='ORIGINAL_SELECTED_SOURCE_WITH_TEMPORARY_AUTHORING_POSE_NOT_FINAL_BIND'
    # Conventional garment-only authoring armature. The wearer75 is never
    # reposed/reweighted. Original selected surface remains editable underneath.
    rig_data=bpy.data.armatures.new('Selected garment source-pose authoring bones ONLY')
    author_rig=bpy.data.objects.new('Hoodie_SourcePoseAuthoringAid7_NOT_FINAL_RIG',rig_data)
    collection.objects.link(author_rig)
    for selected in bpy.context.selected_objects:selected.select_set(False)
    bpy.context.view_layer.objects.active=author_rig;author_rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def frame(head,tail):
        head=Vector(head);direction=Vector(tail)-head
        result=direction.to_track_quat('Y','Z').to_matrix().to_4x4()
        result.translation=head
        return result
    for row in controls['authoringBones']:
        bone=rig_data.edit_bones.new(row['name'])
        bone.matrix=frame(row['sourceHead'],row['sourceTail'])
        bone.length=(Vector(row['sourceTail'])-Vector(row['sourceHead'])).length
        if row['parent']:bone.parent=rig_data.edit_bones[row['parent']]
        bone.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in rig_data.bones:bone.inherit_scale='NONE'
    world=xyz.astype(float)*np.array(affine['scale'])+np.array(affine['translation'])
    weight_controls=controls['sourcePoseWeightControls']
    bone_rows={row['name']:row for row in controls['authoringBones']}
    group_names=[row['name'] for row in controls['authoringBones']]
    weights=np.zeros((len(world),len(group_names)),dtype=np.float32)
    def smooth(a,b,value):
        t=np.clip((value-a)/(b-a),0,1);return t*t*(3-2*t)
    centered=world[:,0]-affine['translation'][0]
    for side,sign in [('L',1),('R',-1)]:
        mask=centered*sign>=0;indices=np.flatnonzero(mask);points=world[mask]
        distances=[]
        for role in ('ShoulderBridge','UpperArm','Forearm'):
            row=bone_rows['AUTHOR_'+role+'.'+side]
            a=np.array(row['sourceHead']);d=np.array(row['sourceTail'])-a
            t=np.clip((points-a)@d/(d@d),0,1)
            distances.append(np.linalg.norm(points-(a+t[:,None]*d),axis=1))
        radius=np.minimum.reduce(distances)
        x=abs(centered[mask])
        lateral=smooth(*weight_controls['lateralTransition'],x)
        radial=1-smooth(*weight_controls['radialTransition'],radius)
        sleeve=lateral*radial
        cap_x=abs(bone_rows['AUTHOR_UpperArm.'+side]['sourceHead'][0]-affine['translation'][0])
        elbow_x=abs(bone_rows['AUTHOR_Forearm.'+side]['sourceHead'][0]-affine['translation'][0])
        cap_width=weight_controls['capCrossfadeHalfWidth'];elbow_width=weight_controls['elbowCrossfadeHalfWidth']
        upper=smooth(cap_x-cap_width,cap_x+cap_width,x)
        fore=smooth(elbow_x-elbow_width,elbow_x+elbow_width,x)
        weights[indices,group_names.index('AUTHOR_Chest')]=1-sleeve
        for role,values in [('ShoulderBridge',sleeve*(1-upper)),
                            ('UpperArm',sleeve*upper*(1-fore)),('Forearm',sleeve*upper*fore)]:
            weights[indices,group_names.index('AUTHOR_'+role+'.'+side)]=values
    assert np.max(abs(weights.sum(1)-1))<1e-6 and np.min(weights)>=0
    # Quantize this temporary author's weights into4096 units for bounded
    # bulk group writes. Repair each row's largest column to exact unit sum.
    # This never quantizes wearer75 or any future final garment binding.
    units=np.rint(weights*4096).astype(np.int32)
    residual=4096-units.sum(1)
    units[np.arange(len(units)),np.argmax(units,axis=1)]+=residual
    assert np.all(units.sum(1)==4096) and np.min(units)>=0
    weights=units.astype(np.float32)/4096
    garment.vertex_groups.clear()
    for column,name in enumerate(group_names):
        group=garment.vertex_groups.new(name=name)
        values=units[:,column];order=np.argsort(values,kind='stable')
        sorted_values=values[order]
        starts=np.r_[0,np.flatnonzero(np.diff(sorted_values))+1,len(order)]
        for a,b in zip(starts[:-1],starts[1:]):
            value=int(sorted_values[a])
            if value:group.add(order[a:b].tolist(),value/4096,'REPLACE')
    modifier=garment.modifiers.new('ONE selected source-pose garment authoring transport','ARMATURE')
    modifier.object=author_rig;modifier.use_deform_preserve_volume=True
    target_matrices={}
    for row in controls['authoringBones']:
        source_length=(Vector(row['sourceTail'])-Vector(row['sourceHead'])).length
        target_length=(Vector(row['targetTail'])-Vector(row['targetHead'])).length
        target=frame(row['targetHead'],row['targetTail'])@Matrix.Diagonal((1,target_length/source_length,1,1))
        author_rig.pose.bones[row['name']].matrix=target
        target_matrices[row['name']]=target
        bpy.context.view_layer.update()
    for name,target in target_matrices.items():
        actual=author_rig.pose.bones[name].matrix
        assert max(abs(actual[r][c]-target[r][c]) for r in range(4) for c in range(4))<1e-5,('Source-pose matrix',name)
    depsgraph=bpy.context.evaluated_depsgraph_get()
    evaluated=garment.evaluated_get(depsgraph)
    mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=depsgraph)
    assert len(mesh.vertices)==controls['sourceVertices'] and len(mesh.polygons)==controls['sourcePolygons']
    assert geometry_uv_signature(mesh,positions=False)==geometry_uv_signature(garment.data,positions=False)
    derivative=garment.copy();derivative.data=mesh;collection.objects.link(derivative)
    garment.name='Hoodie__OriginalSelectedPBR_EditableSourcePoseAid05'
    derivative.name='Hoodie__ActualSelectedPBR_Cage05'
    derivative.modifiers.clear();derivative.vertex_groups.clear()
    derivative['contextStatus']='ONE_REAL_SELECTED_SOURCE_POSE_TRANSPORT_REST_FIT_UNACCEPTED_UNRIGGED'
    garment.hide_render=True;garment.hide_set(True)
    author_rig.hide_render=True;author_rig.hide_set(True)
    author_rig['privateAuthoringAid']=True;author_rig['isFinalSharedRig']=False
    author_rig['instructions']='Toggle original selected source surface and this aid to edit pose bones. Visible evaluated derivative is a saved rest-fit candidate; wearer75 remains authoritative.'
    for name,row in controls['landmarks'].items():
        marker=bpy.data.objects.new('Cage05_anchor_'+name,None);collection.objects.link(marker)
        marker.location=row['target'];marker.empty_display_type='SPHERE';marker.empty_display_size=.008
        marker.hide_render=True;marker.hide_set(True)
        marker['sourceWorld']=row['source'];marker['targetWorld']=row['target']
        marker['role']='Documented source/target anchor; source-pose authoring aid is not the wearer rig'
    old.hide_render=True;old.hide_set(True)
    old['contextStatus']='FAILED_CORRECTED04_SHOULDER_RETAINED_TOGGLEABLE_REFERENCE'
    derivative.hide_render=False;derivative.hide_set(False)
    assert geometry_uv_signature(garment.data)==source_signature
    assert packed_maps(garment)==maps and packed_maps(derivative)==maps
    assert helper['signature'](body,rig)==controls['bodyRigSignature']
    for name,(pointer,matrix,modifiers) in other_visible.items():
        obj=bpy.data.objects[name]
        assert obj.data.as_pointer()==pointer and obj.matrix_world==matrix
        assert [(m.name,m.type,m.show_viewport,m.show_render) for m in obj.modifiers]==modifiers
        assert not obj.hide_render
    visible=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render)
    assert len(visible)==7 and body.name in visible and derivative.name in visible
    assert not derivative.modifiers and not derivative.vertex_groups
    out.mkdir(parents=True)
    native=out/'selected-cage-outfit.blend'
    notes=bpy.data.texts.new('CAGE05_ACTUAL_SELECTED_PBR_UNACCEPTED')
    notes.write(json.dumps({'controls':controls,'visibleMeshes':visible},indent=2))
    bpy.context.view_layer.objects.active=derivative
    for obj in bpy.context.selected_objects:obj.select_set(False)
    derivative.select_set(True)
    # Save the actual editable geometry and original PBR before any views or
    # field transfer. Original source and temporary authoring pose remain editable.
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    receipt={'accepted':False,'stage':'SAVED_ACTUAL_SELECTED_PBR_SOURCE_POSE_TRANSPORT_PENDING_REST_REVIEW',
        'controls':{'path':str(controls_path.relative_to(ROOT)),'sha256':sha(controls_path)},
        'author':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(__file__)},
        'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},
        'incomingNative':controls['incomingNative'],'originalDensePBR':controls['originalDensePBR'],
        'bodyAnd75RigSignature':controls['bodyRigSignature'],'originalBaseGeometryAndUVSignature':source_signature,
        'originalImportedBounds':imported_bounds,'sourceVertices':len(garment.data.vertices),
        'sourcePolygons':len(garment.data.polygons),'packedOriginalPBR':maps,
        'authoringBones':controls['authoringBones'],'visibleMeshes':visible,
        'visibleDerivativeGeometryAndUVSignature':geometry_uv_signature(derivative.data),
        'sourceAuthoringWeights':{'columns':group_names,'rowSumMaximumError':float(np.max(abs(weights.sum(1)-1)))},
        'garmentRigged':False,'limits':controls['limits']}
    (out/'author.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
