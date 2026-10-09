"""Local original47 selected-to-active sleeve bake; parent CPU2 only.

prepare NATIVE77_REOPENED_RECEIPT FRESH_OUT
bake ATLAS_PENDING FRESH_OUT
reopen BAKE_PENDING

Retained panels keep original UV/PBR. Only actual77 rebuilt face roles receive
an atlas and appended material. The local highpoly donors keep original47
positions/UV/PBR; exterior, cavity and cuff use separate custom cages. Global
source-wall tracing and the unqualified73 ray pairing are not bake authority.
"""
import hashlib
import ast
import importlib.util
import json
import runpy
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/'harness/out/rider-rebuild/selected-engine-receiver79'
sys.path.insert(0,str(HERE))
import atlas
import patches

LEGACY25={'path':'assets/blender/rider-rebuild/selected-rider-production25/bake.py',
          'sha256':'6e3a32a515a48ef9e85710aaf0fab97869a56ec3c158d2b19f3979eaf42331f9'}
LIFETIME32={'path':'assets/blender/rider-rebuild/selected-production-bake32/lifetime.py',
            'sha256':'da4b1f82bd9858bbd9ca7cb966655d05fffc01aed28a935362fd58cfdf50439d'}
AUTHOR77={'path':'assets/blender/rider-rebuild/selected-hoodie-joints77/author.py',
          'sha256':'9477ea7896d42a91f0c91c18aed760d2987aabb4b9bd8953ceccf95220361fb7'}
ACTION_STATE={'path':'assets/blender/rider-rebuild/selected-seated-anatomical09/sculpt-reference05.py',
              'sha256':'57ced8447bc80ab541b4240739364f31e4e54c3f13504434b9ddc33466ae3425'}
NATIVE77=ROOT/'assets/blender/rider-rebuild/selected-hoodie-joints77/native.py'
SOURCE47={'path':'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json',
          'sha256':'55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'}
TARGET='RiderHoodie'
DONOR='RiderHoodie__SelectedDenseBakeSource77'
SIZES={'albedo':1024,'normal':1024,'orm':512}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1048576):h.update(block)
    return h.hexdigest()


def pin(path):
    path=Path(path).resolve();return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}


def checked(row):
    assert set(row)=={'path','sha256'}
    relative=Path(row['path']);assert not relative.is_absolute() and '..' not in relative.parts
    path=(ROOT/relative).resolve();assert path.is_relative_to(ROOT) and sha(path)==row['sha256'];return path


def read(row):return json.loads(checked(row).read_text())


def write(path,row):
    with Path(path).open('x') as stream:json.dump(row,stream,indent=2);stream.write('\n')


def load(row,name):
    spec=importlib.util.spec_from_file_location(name,checked(row));module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def arrays(mesh,field,width,dtype,np):
    values=np.empty((len(mesh),width),dtype);mesh.foreach_get(field,values.ravel());return values


def source(path):
    row=json.loads(Path(path).read_text())
    assert row['recipe']['path']==str(NATIVE77.relative_to(ROOT))
    original=runpy.run_path(str(checked(row['recipe'])))
    assert original['qualify_receipt'](Path(path).resolve())==row
    assert row['source47Receipt']==SOURCE47
    assert 'receiver13' not in Path(row['receiverReceipt']['path']).parts,'Rejected13 is never a bake master'
    assert not row['detailBakePassed'] and not row['genuineBakeAtlasPresent']
    return row,original


def helpers(original):
    C,H,geometry,_=original['helpers'](read(SOURCE47));return C,H,geometry


def surface(obj,original,np):
    mesh=obj.data;mesh.calc_loop_triangles()
    positions=arrays(mesh.vertices,'co',3,np.float32,np)
    triangles=arrays(mesh.loop_triangles,'vertices',3,np.int32,np)
    normals=arrays(mesh.corner_normals,'vector',3,np.float32,np)
    fields=original['actual_fields'](obj,np)
    return {'positions':hashlib.sha256(positions.tobytes()).hexdigest(),
        'triangles':hashlib.sha256(triangles.tobytes()).hexdigest(),
        'cornerNormals':hashlib.sha256(normals.tobytes()).hexdigest(),
        'fields':hashlib.sha256(fields.tobytes()).hexdigest(),
        'nativeIds':original['derivative_ids'](obj,np),
        'controlFieldAuthority':obj['controlFieldAuthority']}


def scene_witness(bpy,original,np):
    C,H,geometry=helpers(original);rig=bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones)==75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    # Reuse only the exact reviewed action-state function; avoid importing its
    # unrelated sculpt runtime. This includes every native curve/key/handle.
    function=next(n for n in ast.parse(checked(ACTION_STATE).read_text()).body
                  if isinstance(n,ast.FunctionDef) and n.name=='action_state')
    scope={};exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(checked(ACTION_STATE)),'exec'),scope)
    result={'rest':C['canonical'](H['rest'](rig)),
        'otherMeshes':{o.name:{'geometry':geometry(o),'metadata':C['canonical'](C['metadata'](o,H['packed_maps']))}
                       for o in bpy.data.objects if o.type=='MESH' and o.name!=TARGET},
        'objectNames':sorted(o.name for o in bpy.data.objects),
        'actions':{a.name:scope['action_state'](a) for a in bpy.data.actions},
        'frame':[bpy.context.scene.frame_current,bpy.context.scene.frame_start,bpy.context.scene.frame_end],
        'targetSurface':surface(bpy.data.objects[TARGET],original,np)}
    contact=runpy.run_path(str(HERE/'contact.py'))
    result['contactInputs']=contact['capture'](bpy,np,contact['helper']())
    return json.loads(json.dumps(result))


def retained_witness(target,donor,retained,np):
    """Retained slots reference the unchanged original donor material objects."""
    count=len(donor.data.materials);assert count>0
    assert list(target.data.materials)[:count]==list(donor.data.materials)
    polygons=np.flatnonzero(retained).astype(np.int32)
    loops=np.concatenate([np.arange(p.loop_start,p.loop_start+p.loop_total)
                          for p in target.data.polygons if retained[p.index]])
    materials=np.asarray([target.data.polygons[int(i)].material_index for i in polygons],np.int32)
    assert np.all((materials>=0)&(materials<count))
    return {'originalMaterialSlots':[m.name for m in donor.data.materials],
        'retainedPolygonsSHA256':hashlib.sha256(polygons.tobytes()).hexdigest(),
        'retainedMaterialIdsSHA256':hashlib.sha256(materials.tobytes()).hexdigest(),
        'retainedUV':{layer.name:hashlib.sha256(arrays(layer.data,'uv',2,np.float32,np)[loops].tobytes()).hexdigest()
                      for layer in target.data.uv_layers},'activeUV':target.data.uv_layers.active.name}


def atlas_report(uv,loops,indices,name,np):
    report=atlas.verify(uv[loops[indices]].reshape(-1,2),np.arange(len(indices)*3).reshape(-1,3),np)
    report.update(scope='Rebuilt polygons only; retained selected UV/PBR preserved',uvLayer=name)
    return report


def prepare(native_path,out):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    native_path,out=map(lambda p:Path(p).resolve(),(native_path,out))
    assert out.is_relative_to(OUT) and not out.exists()
    row,original=source(native_path)
    receiver=read(row['receiverReceipt']);assert receiver['source47Receipt']==SOURCE47
    checked(receiver['recipe'])
    authored=np.load(checked(receiver['receiver']))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(row['native'])),use_scripts=False)=={'FINISHED'}
    C,H,geometry=helpers(original);expected=read(row['expectedWitness'])
    donor,target=bpy.data.objects[DONOR],bpy.data.objects[TARGET]
    assert geometry(target)==expected['receiverGeometry'] and geometry(donor)==expected['donorGeometry']
    assert original['donor_original_named_geometry'](donor,geometry)==read(SOURCE47)['expectedHoodieGeometry']
    before=scene_witness(bpy,original,np)
    donor.data.calc_loop_triangles();target.data.calc_loop_triangles()
    sp=arrays(donor.data.vertices,'co',3,np.float32,np)
    sf=arrays(donor.data.loop_triangles,'vertices',3,np.int32,np)
    tl=arrays(target.data.loop_triangles,'loops',3,np.int32,np)
    tv=arrays(target.data.loop_triangles,'vertices',3,np.int32,np)
    tp=arrays(target.data.vertices,'co',3,np.float32,np)
    assert len(donor.data.polygons)==len(sf) and all(len(p.vertices)==3 for p in donor.data.polygons)
    # Current selected source has one sampling UV layer. Refuse a different
    # material coordinate contract instead of silently dropping another layer.
    assert len(donor.data.uv_layers)==len(target.data.uv_layers)==1
    keep,walls=patches.receiver_parts(authored,target.data,np)
    healthy=retained_witness(target,donor,keep,np)
    triangle_keys=walls[np.asarray([t.polygon_index for t in target.data.loop_triangles])]
    # Reuse only the literal reviewed cut function; no author execution.
    function=next(n for n in ast.parse(checked(AUTHOR77).read_text()).body
                  if isinstance(n,ast.FunctionDef) and n.name=='cut_width')
    scope={'np':np};exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(checked(AUTHOR77)),'exec'),scope)
    data={'receiverTriangles':tv,'receiverTriangleLoops':tl,'triangleDomains':triangle_keys,
          'retainedPolygons':keep}
    reports={};sources={}
    for side in ('L','R'):
        donor_ids,selection=patches.source_patch(sp,sf,side,scope['cut_width'],np)
        data['sourceFaces_'+side]=donor_ids;sources[side]=selection
        used=np.unique(sf[donor_ids]);inverse=np.full(len(sp),-1,np.int32);inverse[used]=np.arange(len(used))
        local_points=sp[used];local_faces=inverse[sf[donor_ids]]
        tree=BVHTree.FromPolygons(local_points.tolist(),local_faces.tolist(),all_triangles=True)
        for wall in ('outer','inner','rim'):
            key=side+':'+wall;indices=np.flatnonzero(triangle_keys==key)
            vertices=np.unique(tv[indices]);remap=np.full(len(tp),-1,np.int32);remap[vertices]=np.arange(len(vertices))
            positions,report=patches.cage(tp[vertices],remap[tv[indices]],local_points,local_faces,
                tree,before['rest'],key,Vector,np)
            # Store literal original47 face IDs, not labels or a nearest UV map.
            data['firstHitSourceFaces_'+side+'_'+wall]=donor_ids[np.asarray(report.pop('firstHitLocalFaceIds'),np.int32)]
            data['cageVertices_'+side+'_'+wall]=vertices
            data['cagePositions_'+side+'_'+wall]=positions
            reports[key]=report
    atlas_uv,atlas_loops,rebuilt,packed=atlas.unwrap(target,walls,bpy,np)
    assert np.array_equal(atlas_loops,tl)
    assert retained_witness(target,donor,keep,np)==healthy
    assert scene_witness(bpy,original,np)==before,'UV-only preparation changed source, fields or rest'
    data.update(atlasUV=atlas_uv,rebuiltTriangles=rebuilt)
    out.mkdir(parents=True);np.savez(out/'local-sleeve-cages.npz',**data)
    native=out/'UNACCEPTED-selected77-real-atlas79.blend'
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=False)=={'FINISHED'}
    write(out/'atlas-pending.json',{'status':'SELECTED79_REAL_ATLAS_CAGES_SAVED_BAKE_PENDING','acceptedArt':False,
        'recipe':pin(__file__),'atlasRecipe':pin(HERE/'atlas.py'),'cageRecipe':pin(HERE/'patches.py'),
        'native77Receipt':pin(native_path),'native77Recipe':row['recipe'],'native':pin(native),
        'receiverArrays':receiver['receiver'],'cutRecipe':AUTHOR77,'ancestry':pin(out/'local-sleeve-cages.npz'),
        'originalWitness':before,'retainedPanels':healthy,'atlas':packed,'localSourcePatches':sources,'cages':reports,
        'sourceRecipe25':LEGACY25,'lifetime32':LIFETIME32,'actionWitnessRecipe':ACTION_STATE,'nativeStorage':{'compressed':False},
        'detailBakePassed':False,'poseContactPassed':False,'movingReviewPassed':False})


def copied_patch(source,positions,faces,uv,normals,material_ids,bpy,np,name,tracker):
    used=np.unique(faces);inverse=np.full(len(positions),-1,np.int32);inverse[used]=np.arange(len(used))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(positions[used].tolist(),[],inverse[faces].tolist());mesh.update()
    obj=source.copy();obj.data=mesh;obj.name=name;bpy.context.scene.collection.objects.link(obj)
    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    for mat in source.data.materials:mesh.materials.append(mat)
    mesh.polygons.foreach_set('material_index',np.asarray(material_ids,np.int32))
    for face in mesh.polygons:face.use_smooth=True
    layer=mesh.uv_layers.new(name=source.data.uv_layers.active.name)
    layer.data.foreach_set('uv',np.asarray(uv,np.float32).ravel());layer.active_render=True
    mesh.normals_split_custom_set(np.asarray(normals,float).reshape(-1,3).tolist())
    obj.hide_render=False;obj.hide_set(False);tracker.register(obj,source,name)
    return obj


def coverage_materials(materials,bpy):
    """Only temporary material copies emit white; selected PBR is untouched."""
    for material in materials:
        nt=material.node_tree;output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
        emit=nt.nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(1,1,1,1)
        for link in list(output.inputs['Surface'].links):nt.links.remove(link)
        nt.links.new(emit.outputs['Emission'],output.inputs['Surface'])


def material_witness(obj,maps,original_slots):
    """Observe the actual fixed25 shader wiring and packed channel bytes."""
    assert len(obj.data.materials)==original_slots+1
    mat=obj.data.materials[original_slots];assert mat.use_nodes
    nodes=mat.node_tree.nodes;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    normal=next(n for n in nodes if n.type=='NORMAL_MAP');orm=next(n for n in nodes if n.type=='SEPARATE_COLOR')
    def linked(socket,from_node,from_socket):
        assert len(socket.links)==1
        link=socket.links[0];assert link.from_node==from_node and link.from_socket==from_node.outputs[from_socket]
    channels={name:nodes['Production_'+name] for name in SIZES}
    linked(shader.inputs['Base Color'],channels['albedo'],'Color')
    linked(shader.inputs['Normal'],normal,'Normal');linked(normal.inputs['Color'],channels['normal'],'Color')
    linked(orm.inputs['Color'],channels['orm'],'Color')
    linked(shader.inputs['Roughness'],orm,'Green');linked(shader.inputs['Metallic'],orm,'Blue')
    output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    linked(output.inputs['Surface'],shader,'BSDF')
    assert normal.space=='TANGENT' and normal.uv_map==obj.data.uv_layers.active.name and orm.mode=='RGB'
    actual={}
    for name,node in channels.items():
        im=node.image;assert im and im.packed_file
        digest=hashlib.sha256(bytes(im.packed_file.data)).hexdigest()
        assert digest==maps[name]['file']['sha256'] and list(im.size)==maps[name]['size']
        assert im.colorspace_settings.name==('sRGB' if name=='albedo' else 'Non-Color')
        actual[name]={'image':im.name,'packedSHA256':digest,'size':list(im.size),'colorSpace':im.colorspace_settings.name}
    return {'material':mat.name,'slot':original_slots,'channels':actual,'normalSpace':normal.space,'normalUV':normal.uv_map,
            'shader':'Exact fixed25 albedo/normal/ORM channel connections independently observed'}


def bake(atlas_path,out):
    import bpy
    import numpy as np
    atlas_path,out=Path(atlas_path).resolve(),Path(out).resolve();assert out.is_relative_to(OUT) and not out.exists()
    pending=json.loads(atlas_path.read_text());assert pending['status']=='SELECTED79_REAL_ATLAS_CAGES_SAVED_BAKE_PENDING'
    assert pending['recipe']==pin(__file__) and pending['atlasRecipe']==pin(HERE/'atlas.py') and pending['cageRecipe']==pin(HERE/'patches.py')
    row,original=source(checked(pending['native77Receipt']))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(pending['native'])),use_scripts=False)=={'FINISHED'}
    assert scene_witness(bpy,original,np)==pending['originalWitness']
    actual=np.load(checked(pending['ancestry']));target,source_obj=bpy.data.objects[TARGET],bpy.data.objects[DONOR]
    target.data.calc_loop_triangles();source_obj.data.calc_loop_triangles()
    tp=arrays(target.data.vertices,'co',3,np.float32,np);tv=arrays(target.data.loop_triangles,'vertices',3,np.int32,np)
    tl=arrays(target.data.loop_triangles,'loops',3,np.int32,np)
    uv=arrays(target.data.uv_layers[pending['atlas']['uvLayer']].data,'uv',2,np.float32,np)
    assert np.array_equal(uv,actual['atlasUV']) and atlas_report(uv,tl,actual['rebuiltTriangles'],pending['atlas']['uvLayer'],np)==pending['atlas']
    assert np.array_equal(tv,actual['receiverTriangles']) and np.array_equal(tl,actual['receiverTriangleLoops'])
    sp=arrays(source_obj.data.vertices,'co',3,np.float32,np);sf=arrays(source_obj.data.loop_triangles,'vertices',3,np.int32,np)
    sl=arrays(source_obj.data.loop_triangles,'loops',3,np.int32,np)
    su=arrays(source_obj.data.uv_layers.active.data,'uv',2,np.float32,np)
    sn=arrays(source_obj.data.corner_normals,'vector',3,np.float32,np)
    tn=arrays(target.data.corner_normals,'vector',3,np.float32,np)
    materials=arrays(source_obj.data.loop_triangles,'material_index',1,np.int32,np).ravel()
    assert retained_witness(target,source_obj,actual['retainedPolygons'],np)==pending['retainedPanels']
    keys=sorted(set(actual['triangleDomains'])-{'retained'})
    engine=load(LEGACY25,'bake79_exact25');lifetime=runpy.run_path(str(checked(LIFETIME32)))
    tracker=lifetime['OwnedMeshes'](lambda:bpy.data.objects,lambda:bpy.data.meshes)
    engine.bpy=lifetime['BpyProxy'](bpy,tracker.remove)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
    scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=True
    scene.render.bake.margin=8;scene.render.bake.normal_space='TANGENT'
    mat,images,nodes=engine.receiver('selectedHoodie79',SIZES)
    next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP').uv_map=pending['atlas']['uvLayer']
    rough=engine.image('selectedHoodie79.roughness',512,False);metal=engine.image('selectedHoodie79.metallic',512,False)
    coverage=engine.image('selectedHoodie79.actualSourceRayCoverage',1024,False)
    modifier_states=[]
    for obj in (target,source_obj):
        for mod in obj.modifiers:
            modifier_states.append((mod,mod.show_viewport,mod.show_render));mod.show_viewport=mod.show_render=False
    out.mkdir(parents=True);passes=[]
    for pass_name,socket in [('coverage',None),('albedo','Base Color'),('normal',None),('roughness','Roughness'),('metallic','Metallic')]:
        image=images.get(pass_name,{'coverage':coverage,'roughness':rough,'metallic':metal}.get(pass_name))
        scene.render.bake.margin=0 if pass_name=='coverage' else 8
        node=nodes.get(pass_name) or mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node
        for n in mat.node_tree.nodes:n.select=n==node
        for index,key in enumerate(keys):
            indices=np.flatnonzero(actual['triangleDomains']==key)
            if not len(indices):continue
            side,wall=key.split(':');suffix=side+'_'+wall
            donor_faces=actual['sourceFaces_'+side]
            patch=copied_patch(source_obj,sp,sf[donor_faces],su[sl[donor_faces]],sn[sl[donor_faces]],materials[donor_faces],bpy,np,'Selected79Domain.'+key,tracker)
            donor,copies=engine.emission_source(patch,socket);tracker.register(donor,patch,'emission')
            if pass_name=='coverage':coverage_materials(copies,bpy)
            receiver=copied_patch(target,tp,tv[indices],uv[tl[indices]],tn[tl[indices]],np.zeros(len(indices),np.int32),bpy,np,'Selected79Receiver.'+key,tracker)
            receiver.data.materials.clear();receiver.data.materials.append(mat)
            assert receiver.data.uv_layers.active.name==pending['atlas']['uvLayer']
            assert np.array_equal(np.unique(tv[indices]),actual['cageVertices_'+suffix])
            cage=receiver.copy();cage.data=receiver.data.copy();cage.name='Selected79Cage.'+key
            bpy.context.scene.collection.objects.link(cage);tracker.register(cage,receiver,'matching-topology-cage')
            cage.data.vertices.foreach_set('co',actual['cagePositions_'+suffix].ravel());cage.data.update()
            cage.hide_render=True;cage.hide_set(True);scene.render.bake.cage_object=cage
            # Blender applies max_ray_distance to custom cages as well. Use
            # the finite source+cage envelope, converted to world units.
            scale=float(np.linalg.norm(np.asarray(target.matrix_world)[:3,:3],ord=2))
            scene.render.bake.max_ray_distance=pending['cages'][key]['maximumBakeRayDistanceLocalM']*scale
            scene.render.bake.use_clear=not any(p['pass']==pass_name for p in passes)
            engine.select(donor,receiver);bpy.context.view_layer.update()
            assert bpy.ops.object.bake(type='NORMAL' if pass_name=='normal' else 'EMIT')=={'FINISHED'}
            passes.append({'pass':pass_name,'domain':key,'sourceTriangles':len(donor_faces),'receiverTriangles':len(indices)})
            for obj in (cage,receiver,donor,patch):tracker.remove(obj,do_unlink=True)
            for material in copies:bpy.data.materials.remove(material)
        if pass_name not in nodes:mat.node_tree.nodes.remove(node)
    assert not tracker.pending and len(tracker.created)==len(tracker.released)
    mask,coverage_report=atlas.interior_pixels(uv,tl[actual['rebuiltTriangles']],1024,np)
    pixels=np.empty(1024*1024*4,np.float32);coverage.pixels.foreach_get(pixels)
    values=pixels.reshape(1024,1024,4)[:,:,:3][mask]
    assert np.isfinite(values).all()
    missed=np.flatnonzero(np.any(values<1-4*np.finfo(np.float32).eps,axis=1))
    assert not len(missed),('Selected source cage ray coverage incomplete',len(missed),len(values))
    coverage_report.update(actualUncoveredInteriorTexelCenters=0,minimumWhiteEmission=float(values.min()),
        bakeMarginPixels=0,passName='coverage',source='Exact original47 local sleeve patches and matching-topology exterior/cavity/cuff cages; rebuilt polygons only')
    coverage_path=out/'actual-source-ray-coverage.png';coverage.filepath_raw=str(coverage_path)
    coverage.file_format='PNG';coverage.save();bpy.data.images.remove(coverage)
    r=np.empty(512*512*4,np.float32);m=np.empty_like(r);rough.pixels.foreach_get(r);metal.pixels.foreach_get(m)
    packed=np.ones((512*512,4),np.float32);packed[:,1]=r.reshape(-1,4)[:,0];packed[:,2]=m.reshape(-1,4)[:,0]
    images['orm'].pixels.foreach_set(packed.ravel());images['orm'].update()
    bpy.data.images.remove(rough);bpy.data.images.remove(metal)
    maps={}
    for name,image in images.items():
        values=np.empty(image.size[0]*image.size[1]*4,np.float32);image.pixels.foreach_get(values)
        assert np.isfinite(values).all() and np.all((values>=0)&(values<=1)),('Invalid actual baked channel',name)
        path=out/('selected-hoodie-'+name+'.png');image.filepath_raw=str(path);image.file_format='PNG';image.save();image.pack()
        maps[name]={'file':pin(path),'size':list(image.size),'residentRGBA8MipMiB':image.size[0]*image.size[1]*4*4/3/1048576}
    for mod,viewport,render in modifier_states:mod.show_viewport=viewport;mod.show_render=render
    assert scene_witness(bpy,original,np)==pending['originalWitness'],'Bake scratch changed source, original PBR, fields,75 rest or other meshes'
    original_slots=len(target.data.materials);target.data.materials.append(mat)
    for poly in target.data.polygons:
        if not actual['retainedPolygons'][poly.index]:poly.material_index=original_slots
    assert retained_witness(target,source_obj,actual['retainedPolygons'],np)==pending['retainedPanels']
    target['sourceUVStatus']='Retained original selected UV/PBR; actual local source47 cage bake on rebuilt sleeves only'
    target['genuineBakeAtlasPresent']=True
    actual_material=material_witness(target,maps,original_slots)
    C,H,geometry=helpers(original)
    expected={'rest':pending['originalWitness']['rest'],
        'protectedGeometry':read(row['expectedWitness'])['protectedGeometry'],
        'donorGeometry':geometry(source_obj),'donorOriginalNamedGeometry':original['donor_original_named_geometry'](source_obj,geometry),
        'donorMetadata':C['canonical'](C['metadata'](source_obj,H['packed_maps'])),
        'receiverGeometry':geometry(target),'receiverMetadata':C['canonical'](C['metadata'](target,H['packed_maps'])),
        'objectNames':sorted(o.name for o in bpy.data.objects),
        'visibleRenderMeshes':sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render)}
    write(out/'expected-baked-witness.json',expected)
    native=out/'UNACCEPTED-selected77-genuine-bake79.blend'
    assert bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=False)=={'FINISHED'}
    write(out/'bake-pending.json',{'status':'SELECTED79_GENUINE_BAKE_SAVED_REOPEN_PENDING','acceptedArt':False,
        'recipe':pin(__file__),'native':pin(native),'sourceNative77':pending['native77Receipt'],
        'sourceReceipt':SOURCE47,'source47Receipt':SOURCE47,'receiverReceipt':row['receiverReceipt'],
        'expectedWitness':pin(out/'expected-baked-witness.json'),'originalWitness':pending['originalWitness'],
        'atlasPending':pin(atlas_path),'maps':maps,'passes':passes,'sourceRecipe25':LEGACY25,'lifetime32':LIFETIME32,
        'actionWitnessRecipe':ACTION_STATE,'sourceRayCoverage':{'file':pin(coverage_path),'report':coverage_report},
        'bakedMaterial':actual_material,'contactRecipe':pin(HERE/'contact.py'),
        'assemblyWitnessRecipe':pin(HERE/'witness.py'),
        'ownedMeshLifetime':{'created':tracker.created,'released':tracker.released,'unreleased':[]},
        'denseBakeSourceObject':DONOR,'targetObject':TARGET,'nativeStorage':{'compressed':False,'reopenVerified':False},
        'detailBakePassed':False,'bakeReopened':False,'independentReopenPassed':False,
        'posedContactPassed':False,'movingReviewPassed':False,'native75FieldConditioningApplied':False,
        'limits':'Actual local sleeve maps, unchanged retained UV/PBR, strict rebuilt interior coverage and saved native only. Transported shading and complete moving appearance require parent review; no posed/contact or device acceptance.'})


def reopen(path):
    import bpy
    import numpy as np
    path=Path(path).resolve();row=json.loads(path.read_text());assert row['recipe']==pin(__file__)
    assert row['status']=='SELECTED79_GENUINE_BAKE_SAVED_REOPEN_PENDING'
    _,original=source(checked(row['sourceNative77']));C,H,geometry=helpers(original)
    expected=read(row['expectedWitness']);assert bpy.ops.wm.open_mainfile(filepath=str(checked(row['native'])),use_scripts=False)=={'FINISHED'}
    actual=scene_witness(bpy,original,np);assert actual==row['originalWitness']
    for name,obj in [(DONOR,bpy.data.objects[DONOR]),(TARGET,bpy.data.objects[TARGET])]:
        key='donor' if name==DONOR else 'receiver'
        assert geometry(obj)==expected[key+'Geometry']
        assert C['canonical'](C['metadata'](obj,H['packed_maps']))==expected[key+'Metadata']
    assert original['donor_original_named_geometry'](bpy.data.objects[DONOR],geometry)==expected['donorOriginalNamedGeometry']
    target=bpy.data.objects[TARGET];assert target['genuineBakeAtlasPresent'] is True
    assert material_witness(target,row['maps'],row['bakedMaterial']['slot'])==row['bakedMaterial']
    prepared=read(row['atlasPending']);ancestry=__import__('numpy').load(checked(prepared['ancestry']))
    target.data.calc_loop_triangles()
    uv=arrays(target.data.uv_layers[prepared['atlas']['uvLayer']].data,'uv',2,np.float32,np)
    loops=arrays(target.data.loop_triangles,'loops',3,np.int32,np)
    assert np.array_equal(uv,ancestry['atlasUV']) and atlas_report(uv,loops,ancestry['rebuiltTriangles'],prepared['atlas']['uvLayer'],np)==prepared['atlas']
    assert retained_witness(target,bpy.data.objects[DONOR],ancestry['retainedPolygons'],np)==prepared['retainedPanels']
    assert all(p.material_index==row['bakedMaterial']['slot'] for p in target.data.polygons if not ancestry['retainedPolygons'][p.index])
    merger=runpy.run_path(str(HERE/'merge.py'));methods=merger['methods']()
    target=methods['read'](methods['TARGET_QUALIFIED11'])
    contract=methods['read'](target['sourcePins']['contract'])
    observer=runpy.run_path(str(checked(row['assemblyWitnessRecipe'])))
    source_witness=observer['capture']('source',target,contract,bpy,methods)
    row.update(status='BAKED79_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED',bakeReopened=True,
        independentReopenPassed=True,detailBakePassed=True,pendingReceipt=pin(path),
        receiverGeometry=expected['receiverGeometry'],receiverMetadata=expected['receiverMetadata'],
        assemblySourceWitness=source_witness)
    row['nativeStorage']['reopenVerified']=True
    write(path.with_name('bake-reopened.json'),row)


def qualify_receipt(path):
    path=Path(path).resolve();row=json.loads(path.read_text())
    assert row['status']=='BAKED79_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED' and row['recipe']==pin(__file__)
    assert row['acceptedArt'] is False and row['bakeReopened'] is row['independentReopenPassed'] is row['detailBakePassed'] is True
    assert row['nativeStorage']=={'compressed':False,'reopenVerified':True}
    for key in ('native','sourceNative77','sourceReceipt','receiverReceipt','expectedWitness','atlasPending','pendingReceipt','sourceRecipe25','lifetime32','actionWitnessRecipe'):checked(row[key])
    assert row['sourceReceipt']==row['source47Receipt']==SOURCE47
    assert row['sourceRecipe25']==LEGACY25 and row['lifetime32']==LIFETIME32 and row['actionWitnessRecipe']==ACTION_STATE
    assert row['contactRecipe']==pin(HERE/'contact.py') and row['assemblyWitnessRecipe']==pin(HERE/'witness.py')
    assert set(row['assemblySourceWitness']['parts'])=={TARGET,'ActualSelectedGlove.L','ActualSelectedGlove.R','RiderBody__FullAnatomyReference'}
    prepared=read(row['atlasPending'])
    assert prepared['recipe']==pin(__file__) and prepared['atlasRecipe']==pin(HERE/'atlas.py') and prepared['cageRecipe']==pin(HERE/'patches.py')
    for key in ('native77Receipt','native77Recipe','native','receiverArrays','cutRecipe','ancestry','sourceRecipe25','lifetime32','actionWitnessRecipe'):checked(prepared[key])
    assert prepared['native77Receipt']==row['sourceNative77']
    assert prepared['originalWitness']==row['originalWitness']
    assert prepared['cutRecipe']==AUTHOR77
    assert prepared['receiverArrays']==read(row['receiverReceipt'])['receiver']
    pending=read(row['pendingReceipt'])
    for key,value in pending.items():
        if key not in ('status','bakeReopened','independentReopenPassed','detailBakePassed','nativeStorage'):assert row[key]==value
    assert pending['status']=='SELECTED79_GENUINE_BAKE_SAVED_REOPEN_PENDING'
    expected=read(row['expectedWitness']);assert row['receiverGeometry']==expected['receiverGeometry']
    assert row['receiverMetadata']==expected['receiverMetadata']
    for map_row in row['maps'].values():checked(map_row['file'])
    assert set(row['maps'])==set(SIZES)
    for name,size in SIZES.items():assert row['maps'][name]['size']==[size,size]
    assert abs(sum(r['residentRGBA8MipMiB'] for r in row['maps'].values())-12)<1e-12
    checked(row['sourceRayCoverage']['file'])
    assert row['sourceRayCoverage']['report']['actualUncoveredInteriorTexelCenters']==0
    assert row['sourceRayCoverage']['report']['bakeMarginPixels']==0
    assert not row['ownedMeshLifetime']['unreleased']
    source(checked(row['sourceNative77']))
    return row


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0]=='prepare':prepare(*args[1:])
    elif args[0]=='bake':bake(*args[1:])
    elif args[0]=='reopen':reopen(*args[1:])
    else:raise AssertionError(args)
