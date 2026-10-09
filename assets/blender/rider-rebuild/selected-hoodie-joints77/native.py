"""Parent-guarded native assembly and independent reopen of authored77.

This verifier only proves exact native preservation/assembly. It does not
qualify finite garment contact, genuine detail baking, motion or appearance.
"""
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77'
TARGET = 'RiderHoodie'
DONOR = 'RiderHoodie__SelectedDenseBakeSource77'
COMPONENT = {'path': 'assets/blender/rider-rebuild/selected-sleeve-component47/component.py',
             'sha256': '6fcc124b1fe5cf69a3cd0cd4114ff3fc16b6bd3e7741fb4b2b7488648c6bbd87'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()


def pin(path):
    path=Path(path).resolve()
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}


def checked(row):
    path=ROOT/row['path'];assert sha(path)==row['sha256'],row
    return path


def write(path,row):
    assert not path.exists();path.write_text(json.dumps(row,indent=2)+'\n')


def receiver(path):
    row=json.loads(Path(path).read_text())
    assert row['status']=='AUTHORED_SELECTED_HOODIE_JOINT_RECEIVER_UNACCEPTED' and row['acceptedArt'] is False
    assert row['recipe']==pin(HERE/'author.py')
    for key in ('sourceReceiver','source47Receipt','fullBody','original47Geometry','actualGuides','receiver','editableOBJ','construction'):
        checked(row[key])
    return row


def helpers(source_receipt):
    component=runpy.run_path(str(checked(COMPONENT)))
    glove=component['intake_gate'](source_receipt)
    author,geometry=component['helpers'](json.loads(checked(source_receipt['priorInput']).read_text()))
    return component,author,geometry,glove


def normal_sha(obj,np):
    values=np.empty((len(obj.data.corner_normals),3),np.float32)
    obj.data.corner_normals.foreach_get('vector',values.ravel())
    return hashlib.sha256(values.tobytes()).hexdigest()


def actual_fields(obj,np):
    values=np.zeros((len(obj.data.vertices),len(obj.vertex_groups)),np.float32)
    for vertex in obj.data.vertices:
        for group in vertex.groups:values[vertex.index,group.group]=group.weight
    return values


def donor_original_named_geometry(obj,geometry):
    # Pinned original geometry helper includes object.name in its hash. Keep
    # the original47 digest as a content witness after the intentional rename,
    # without renaming live objects or colliding with the new receiver.
    return geometry(SimpleNamespace(name=TARGET,data=obj.data))


def derivative_ids(obj,np):
    attr=obj.data.attributes.get('_NATIVE_ID');assert attr and attr.domain=='POINT'and attr.data_type=='INT'
    values=np.empty(len(obj.data.vertices),np.int32);attr.data.foreach_get('value',values)
    assert np.array_equal(values,np.arange(len(values),dtype=np.int32))
    return hashlib.sha256(values.tobytes()).hexdigest()


def author(receiver_path,output):
    import bpy
    import numpy as np
    receiver_path=Path(receiver_path).resolve();output=Path(output).resolve()
    assert output.is_relative_to(OUT) and not output.exists()
    report=receiver(receiver_path);receipt=json.loads(checked(report['source47Receipt']).read_text())
    C,H,geometry,glove=helpers(receipt)
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])),use_scripts=False)=={'FINISHED'}
    rig=C['scoped'](bpy);source=bpy.data.objects[TARGET]
    rest=C['canonical'](H['rest'](rig));assert rest==receipt['expectedRest']
    assert geometry(source)==receipt['expectedHoodieGeometry']
    assert C['canonical'](C['metadata'](source,H['packed_maps']))==receipt['expectedHoodieMetadata']
    protected={name:geometry(bpy.data.objects[name])for name in C['PROTECTED']}
    assert protected[C['REFERENCE']]==glove['protectedBefore']['fullReference']
    for name in C['GLOVES']:assert protected[name]==glove['expectedConstructedGeometry'][name]
    donor_geometry=geometry(source);donor_normals=normal_sha(source,np)
    donor_metadata=C['canonical'](C['metadata'](source,H['packed_maps']))
    arrays=np.load(checked(report['receiver']));assert arrays['groupNames'].tolist()==[g.name for g in source.vertex_groups]
    assert all(name in rig.data.bones for name in arrays['groupNames'])
    source.name=DONOR;source.hide_render=True;source.hide_set(True)
    mesh=bpy.data.meshes.new('SelectedHoodie77__AuthoredShoulderElbowCuff')
    faces=[arrays['cornerVertexIds'][s:s+n].tolist()for s,n in zip(arrays['polygonStarts'],arrays['polygonCounts'])]
    mesh.from_pydata(arrays['positions'].tolist(),[],faces);mesh.update()
    garment=bpy.data.objects.new(TARGET,mesh);bpy.context.scene.collection.objects.link(garment)
    assert source.matrix_world.is_identity
    garment.matrix_world=source.matrix_world.copy();garment.parent=source.parent
    garment.matrix_parent_inverse=source.matrix_parent_inverse.copy()
    for material in source.data.materials:mesh.materials.append(material)
    for polygon,material in zip(mesh.polygons,arrays['polygonMaterialIds']):
        polygon.material_index=int(material);polygon.use_smooth=True
    mesh.set_sharp_from_angle(angle=math.radians(30))
    uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',arrays['cornerUV'].astype(np.float32).ravel())
    mesh.uv_layers.active_index=0;uv.active_render=True
    mesh.attributes.new('_NATIVE_ID','INT','POINT').data.foreach_set('value',np.arange(len(mesh.vertices),dtype=np.int32))
    for name,values in [('selected_receiver_coefficient',arrays['sourceReceiverCoefficients']),
                        ('selected_appearance_point',arrays['sourceAppearancePoints'])]:
        mesh.attributes.new(name,'FLOAT_VECTOR','POINT').data.foreach_set('vector',values.astype(np.float32).ravel())
    for index in range(3):
        mesh.attributes.new('selected_receiver_parent_'+str(index),'INT','POINT').data.foreach_set('value',np.ascontiguousarray(arrays['sourceReceiverVertexIds'][:,index]))
    mesh.attributes.new('selected_compact_polygon','INT','FACE').data.foreach_set('value',arrays['sourceCompactFace'])
    for gi,name in enumerate(arrays['groupNames'].tolist()):
        group=garment.vertex_groups.new(name=name)
        group.lock_weight=source.vertex_groups[gi].lock_weight
        for vi in np.flatnonzero(arrays['namedFields'][:,gi]>0):group.add([int(vi)],float(arrays['namedFields'][vi,gi]),'REPLACE')
    assert np.array_equal(actual_fields(garment,np),arrays['namedFields'])
    source_mod=[m for m in source.modifiers if m.type=='ARMATURE'];assert len(source_mod)==1 and source_mod[0].object==rig
    modifier=garment.modifiers.new('Actual native75 selected receiver77','ARMATURE');modifier.object=rig
    for name in ('use_deform_preserve_volume','use_vertex_groups','use_bone_envelopes','vertex_group',
                 'invert_vertex_group','show_viewport','show_render'):setattr(modifier,name,getattr(source_mod[0],name))
    garment['acceptedArt']=False;garment['constructionStatus']='AUTHORED_JOINTS_REAL_BAKE_CONTACT_MOTION_PENDING'
    garment['denseSelectedBakeAuthority']=DONOR;garment['sourceUVStatus']='Selected sampling preview only; genuine bake atlas absent'
    garment['nativeIdentitySemantic']='Saved authored receiver row; not original dense-source vertex identity'
    body=bpy.data.objects[C['REFERENCE']];body.hide_render=True;body.hide_set(False)
    assert C['canonical'](H['rest'](rig))==rest
    assert {name:geometry(bpy.data.objects[name])for name in protected}==protected
    assert donor_original_named_geometry(source,geometry)==donor_geometry and normal_sha(source,np)==donor_normals
    assert C['canonical'](C['metadata'](source,H['packed_maps']))==donor_metadata
    expected={'rest':rest,'protectedGeometry':protected,'donorGeometry':geometry(source),
              'donorOriginalNamedGeometry':donor_geometry,'donorNormals':donor_normals,
              'donorMetadata':donor_metadata,'receiverGeometry':geometry(garment),'receiverNormals':normal_sha(garment,np),
              'receiverMetadata':C['canonical'](C['metadata'](garment,H['packed_maps'])),
              'receiverNamedFieldsSHA256':hashlib.sha256(actual_fields(garment,np).tobytes()).hexdigest(),
              'receiverDerivativeNativeIdsSHA256':derivative_ids(garment,np),
              'objectNames':sorted(o.name for o in bpy.data.objects),
              'visibleRenderMeshes':sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render)}
    assert expected['visibleRenderMeshes']==sorted([TARGET,*C['GLOVES']])
    output.mkdir(parents=True);write(output/'expected-native-witness.json',expected)
    native=output/'UNACCEPTED-selected-hoodie-joints77.blend'
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=False)=={'FINISHED'}
    pending={'status':'AUTHORED77_NATIVE_SAVED_REOPEN_PENDING','acceptedArt':False,'recipe':pin(__file__),
             'receiverReceipt':pin(receiver_path),'source47Receipt':report['source47Receipt'],'componentHelper':COMPONENT,
             'actualGuides':report['actualGuides'],'native':pin(native),'expectedWitness':pin(output/'expected-native-witness.json'),
             'sourceCuffInput':glove['priorInput'],'sourceGloveReceipt':receipt['componentReceipt'],
             'denseBakeSourceObject':DONOR,'targetObject':TARGET,'independentReopenPassed':False,
             'detailBakePassed':False,'finiteContactPassed':False,'movingReviewPassed':False,
             'genuineBakeAtlasPresent':False,'nativeIdentitySemantic':'Saved authored receiver row; not original dense-source vertex identity',
             'scope':'Authored hoodie receiver, unchanged actual41 gloves, full reference and native75/rest. Dense original selected hoodie retained hidden for genuine bake.'}
    write(output/'receiver-pending.json',pending);print(pending['status'],flush=True)


def reopen(pending_path):
    import bpy
    import numpy as np
    pending_path=Path(pending_path).resolve();row=json.loads(pending_path.read_text())
    assert row['status']=='AUTHORED77_NATIVE_SAVED_REOPEN_PENDING'and row['recipe']==pin(__file__)
    assert row['componentHelper']==COMPONENT
    source=json.loads(checked(row['source47Receipt']).read_text());C,H,geometry,glove=helpers(source)
    receiver(checked(row['receiverReceipt']));checked(row['actualGuides']);checked(row['sourceCuffInput']);checked(row['sourceGloveReceipt'])
    expected=json.loads(checked(row['expectedWitness']).read_text())
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(row['native'])),use_scripts=False)=={'FINISHED'}
    assert sorted(o.name for o in bpy.data.objects)==expected['objectNames']
    rig=bpy.data.objects['RiderSkeleton'];assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert C['canonical'](H['rest'](rig))==expected['rest']==source['expectedRest']
    assert {name:geometry(bpy.data.objects[name])for name in expected['protectedGeometry']}==expected['protectedGeometry']
    donor,garment=bpy.data.objects[DONOR],bpy.data.objects[TARGET]
    assert geometry(donor)==expected['donorGeometry']and normal_sha(donor,np)==expected['donorNormals']
    assert donor_original_named_geometry(donor,geometry)==expected['donorOriginalNamedGeometry']==source['expectedHoodieGeometry']
    assert C['canonical'](C['metadata'](donor,H['packed_maps']))==expected['donorMetadata']
    assert geometry(garment)==expected['receiverGeometry']and normal_sha(garment,np)==expected['receiverNormals']
    assert C['canonical'](C['metadata'](garment,H['packed_maps']))==expected['receiverMetadata']
    assert hashlib.sha256(actual_fields(garment,np).tobytes()).hexdigest()==expected['receiverNamedFieldsSHA256']
    assert derivative_ids(garment,np)==expected['receiverDerivativeNativeIdsSHA256']
    assert sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render)==expected['visibleRenderMeshes']
    assert donor.hide_render and bpy.data.objects[C['REFERENCE']].hide_render
    row.update(status='AUTHORED77_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED',independentReopenPassed=True,
               pendingReceipt=pin(pending_path),nativeStorage={'compressed':False,'reopenVerified':True})
    write(pending_path.with_name('receiver-reopened.json'),row);print(row['status'],flush=True)


def qualify_receipt(receipt_path):
    """CPU identity admission for measurement, never a contact/bake admission."""
    path=Path(receipt_path).resolve();row=json.loads(path.read_text())
    assert row['status']=='AUTHORED77_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED'
    assert row['acceptedArt'] is False and row['independentReopenPassed'] is True
    assert row['recipe']==pin(__file__) and row['componentHelper']==COMPONENT
    for key in ('native','pendingReceipt','receiverReceipt','source47Receipt','componentHelper','actualGuides',
                'expectedWitness','sourceCuffInput','sourceGloveReceipt'):checked(row[key])
    pending=json.loads(checked(row['pendingReceipt']).read_text())
    for key,value in pending.items():
        if key not in ('status','independentReopenPassed'):assert row[key]==value
    assert pending['status']=='AUTHORED77_NATIVE_SAVED_REOPEN_PENDING'
    receiver(checked(row['receiverReceipt']))
    source=json.loads(checked(row['source47Receipt']).read_text());checked(source['native'])
    expected=json.loads(checked(row['expectedWitness']).read_text())
    assert expected['rest']==source['expectedRest']
    assert expected['donorOriginalNamedGeometry']==source['expectedHoodieGeometry']
    assert row['denseBakeSourceObject']==DONOR and row['targetObject']==TARGET
    return row


if __name__=='__main__':
    mode,*arguments=sys.argv[sys.argv.index('--')+1:]
    {'author':author,'reopen':reopen,'qualify':qualify_receipt}[mode](*arguments)
