"""Private editable actual-source outfit context, never a delivery/export gate.

SOURCE ONLY until parent checkpoint + global serial CPU2 lease.
blender -b -t 2 --python-exit-code 1 --python assemble.py -- inputs.json FRESH_OUT
No bake, render, solver, retopology, weight conditioning or player export.
"""
import hashlib
import json
import runpy
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024*1024): h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed source',str(path))
    return path


def collect_pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value: yield value
        else:
            for child in value.values(): yield from collect_pins(child)
    elif isinstance(value,list):
        for child in value: yield from collect_pins(child)


def rest(rig):
    return [(b.name,b.parent.name if b.parent else None,list(b.head_local),list(b.tail_local),
             [list(r) for r in b.matrix_local],b.use_deform) for b in rig.data.bones]


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def packed_maps(obj):
    images = {}
    if obj.type != 'MESH': return images
    for material in obj.data.materials:
        if not material or not material.use_nodes: continue
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                image = node.image
                assert image.packed_file, ('Unpacked actual map',obj.name,image.name)
                images[image.name] = {'pixels':list(image.size),
                                     'sha256':hashlib.sha256(image.packed_file.data).hexdigest()}
    return images


def record(obj,source_name,role):
    return {'object':obj.name,'sourceObject':source_name,'role':role,'type':obj.type,
            'vertices':len(obj.data.vertices) if obj.type=='MESH' else None,
            'polygons':len(obj.data.polygons) if obj.type=='MESH' else None,
            'matrixWorld':[list(r) for r in obj.matrix_world],
            'modifiers':[{'name':m.name,'type':m.type,
                          'target':m.object.name if hasattr(m,'object') and m.object else
                                   m.target.name if hasattr(m,'target') and m.target else None,
                          'viewport':m.show_viewport,'render':m.show_render} for m in obj.modifiers],
            'packedMaps':packed_maps(obj),'visible':not obj.hide_render}


def append_unit(unit,rig,canonical_rest):
    requested = tuple(unit['visible']+unit['reference']+unit['editingAids'])
    assert len(requested)==len(set(requested))
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(pin(unit['native'])),link=False) as (available,selected):
        assert set(requested)<=set(available.objects), ('Actual source object absent',unit['part'],set(requested)-set(available.objects))
        selected.objects = list(requested)
    mapping = dict(zip(requested,selected.objects))
    new = set(bpy.data.objects)-before
    assert all(o is not None for o in mapping.values())
    source_names = {o:o.name for o in new}
    for name,obj in mapping.items(): source_names[obj]=name
    col = collection('AUTHORING '+unit['part']+' | REAL SOURCE / UNACCEPTED')
    rebound = []
    for obj in sorted(new,key=lambda o:source_names[o]):
        if obj.name not in col.objects: col.objects.link(obj)
        # Keep all appended offline dependencies, poses, lattices and modifiers.
        # Only equal-rest native75 targets can share this working wearer rig.
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE' and modifier.object and len(modifier.object.data.bones)==75:
                source_rig = modifier.object
                assert rest(source_rig)==canonical_rest, ('Invalid native75 rest',unit['part'],source_rig.name)
                assert source_rig.matrix_world.is_identity
                assert all(b.matrix_basis.is_identity for b in source_rig.pose.bones), ('Source native75 is posed',source_rig.name)
                modifier.object = rig
                rebound.append({'object':source_names[obj],'modifier':modifier.name})
                if obj.parent == source_rig:
                    world = obj.matrix_world.copy();obj.parent=rig;obj.matrix_world=world
        visible = obj in [mapping[n] for n in unit['visible']]
        obj.hide_render = not visible
        obj.hide_viewport = False
        obj.hide_set(not visible)
        obj.name = unit['part']+'__'+source_names[obj]
        obj['privateAuthoringContext'] = True
        obj['acceptedArt'] = False
        obj['sourceNativeSHA256'] = unit['native']['sha256']
        obj['sourceObjectName'] = source_names[obj]
        obj['contextStatus'] = unit['status']
    records = []
    for source_name,obj in mapping.items():
        role = 'VISIBLE_ACTUAL_SOURCE_CONTEXT' if source_name in unit['visible'] else 'TOGGLEABLE_CURRENT_WORK_REFERENCE' if source_name in unit['reference'] else 'EDITABLE_MODELING_AID'
        records.append(record(obj,source_name,role))
    actual_hashes = {r['sha256'] for n in unit['visible'] for r in packed_maps(mapping[n]).values()}
    assert set(unit['expectedPBRHashes'])<=actual_hashes, ('Missing actual original PBR',unit['part'])
    assert all(packed_maps(mapping[n]) for n in unit['visible'])
    return {'part':unit['part'],'source':unit['native'],'status':unit['status'],
            'objects':records,'dependencyObjects':[o.name for o in new if o not in mapping.values()],
            'equalRestNative75ModifierTargetsRebound':rebound}


def hoodie_dense(row,rig):
    source = pin(row['original'])
    helpers = runpy.run_path(str(pin(row['fitHelper'])))
    spec = json.loads(pin(row['frozenInputs']).read_text())
    receipt = json.loads(pin(row['authorReceipt']).read_text())
    assert {k:v for k,v in receipt['inputs'].items() if k!='targetHemZ'}==spec
    spec['targetHemZ']=receipt['inputs']['targetHemZ']
    with source.open('rb') as handle:
        _,_,_,size,_=struct.unpack('<5I',handle.read(20));doc=json.loads(handle.read(size))
    assert len(doc['nodes'])==len(doc['meshes'])==1
    assert not any(k in doc['nodes'][0] for k in ('matrix','rotation','translation','scale','skin'))
    accessor = doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['POSITION']]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(source))
    new = set(bpy.data.objects)-before
    dense = [o for o in new if o.type=='MESH']
    assert len(dense)==1
    obj=dense[0]
    assert len(obj.data.vertices)==row['sourceVertexCount']
    points=[obj.matrix_world@v.co for v in obj.data.vertices]
    axis=Matrix(row['gltfToBlenderRows'])
    corners=[axis@Vector((x,y,z)) for x in (accessor['min'][0],accessor['max'][0])
             for y in (accessor['min'][1],accessor['max'][1]) for z in (accessor['min'][2],accessor['max'][2])]
    bounds=lambda values:[[min(p[i] for p in values) for i in range(3)],
                          [max(p[i] for p in values) for i in range(3)]]
    raw_bounds,expected=bounds(points),bounds(corners)
    assert max(abs(a-b) for x,y in zip(raw_bounds,expected) for a,b in zip(x,y))<1e-5, 'Invalid hoodie original GLB axes'
    col=bpy.data.collections['AUTHORING Hoodie | REAL SOURCE / UNACCEPTED']
    for imported in new:
        if imported.name not in col.objects: col.objects.link(imported)
        for old_col in list(imported.users_collection):
            if old_col!=col: old_col.objects.unlink(imported)
    maps_before=packed_maps(obj)
    assert set(row['expectedPBRHashes'])<={r['sha256'] for r in maps_before.values()}
    targets=helpers['target_arms'](rig)
    obj.parent=None;obj.matrix_world=Matrix.Identity(4)
    for vertex,point in zip(obj.data.vertices,points):
        vertex.co=helpers['fit_point'](point,spec,targets,dense=True)[0]
    obj.data.update()
    obj.name='Hoodie__ActualOriginalDensePBR_FrozenFitContext'
    obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
    obj['privateAuthoringContext']=True
    obj['acceptedArt']=False
    obj['sourceNativeSHA256']=row['original']['sha256']
    obj['contextStatus']=row['placement']
    obj['frozenFitHelperSHA256']=row['fitHelper']['sha256']
    assert packed_maps(obj)==maps_before
    return {'object':record(obj,'Original selected GLB mesh','STATIC_ACTUAL_PBR_FROZEN_FIT_CONTEXT'),
            'input':row['original'],'importedBounds':raw_bounds,'fittedBounds':bounds([v.co for v in obj.data.vertices]),
            'unrigged':True,'noOutsideFinishOrBake':True}


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    assert len(args)==2
    manifest_path,out=(Path(x).resolve() for x in args)
    manifest=json.loads(manifest_path.read_text())
    assert manifest['accepted'] is False
    assert out.is_relative_to(ROOT/manifest['outputRoot']) and not out.exists()
    inputs=list(collect_pins(manifest))
    for row in inputs: pin(row)
    # One complete joined body, currently rejected, is visible. Canonical42f is
    # authority by immutable file and exact rig-rest comparison, never a duplicate.
    bpy.ops.wm.open_mainfile(filepath=str(pin(manifest['bodyCandidate']['native'])))
    body=bpy.data.objects[manifest['bodyCandidate']['bodyObject']]
    rig=bpy.data.objects[manifest['bodyCandidate']['rigObject']]
    assert body.type=='MESH' and rig.type=='ARMATURE' and len(rig.data.bones)==75
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    assert rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    with bpy.data.libraries.load(str(pin(manifest['canonical'])),link=False) as (available,selected):
        assert 'RiderSkeleton' in available.objects
        selected.objects=['RiderSkeleton']
    canonical=selected.objects[0]
    canonical_rest=rest(canonical)
    assert rest(rig)==canonical_rest, 'Body candidate rest differs from canonical75'
    bpy.data.objects.remove(canonical,do_unlink=True)
    helpers=runpy.run_path(str(pin(manifest['hoodieDense']['fitHelper'])))
    body_before=helpers['signature'](body,rig)
    body.hide_render=False;body.hide_viewport=False;body.hide_set(False)
    body['privateAuthoringContext']=True;body['acceptedArt']=False
    body['contextStatus']=manifest['bodyCandidate']['status']
    body['canonicalSourceSHA256']=manifest['canonical']['sha256']
    units=[append_unit(unit,rig,canonical_rest) for unit in manifest['units']]
    hoodie=hoodie_dense(manifest['hoodieDense'],rig)
    assert helpers['signature'](body,rig)==body_before
    visible=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    assert len(visible)==7 and body.name in visible, ('Unexpected visible body/garment set',visible)
    notes=bpy.data.texts.new('PRIVATE_AUTHORING_CONTEXT_NOT_ACCEPTED')
    notes.write(json.dumps({'inputs':manifest,'visibleMeshes':visible,'limits':manifest['limits']},indent=2))
    out.mkdir(parents=True)
    native=out/'editable-real-source-outfit.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    result={'accepted':False,'stage':'PRIVATE_EDITABLE_REAL_SOURCE_OUTFIT_SAVED_BEFORE_REVIEW',
            'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},
            'recipeSHA256':sha(__file__),'manifestSHA256':sha(manifest_path),
            'bodyCandidate':manifest['bodyCandidate'],'canonicalSource':manifest['canonical'],
            'visibleBodyVertices':len(body.data.vertices),'visibleMeshes':sorted(visible),
            'bodyAnd75RigUnchangedByAssembly':True,'bodyAnd75RigSignature':body_before,
            'canonical75RestExact':True,'units':units,'hoodieDense':hoodie,
            'limits':manifest['limits']}
    for row in inputs: pin(row)
    (out/'assembly.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PRIVATE_EDITABLE_REAL_SOURCE_OUTFIT_SAVED',str(native),flush=True)


if __name__=='__main__':main()
