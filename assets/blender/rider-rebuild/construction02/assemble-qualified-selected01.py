"""Assemble qualified real garment units on a prepared anatomical master.

No stock appearance is generated. Original native units remain unchanged.
This exporter produces an unaccepted complete candidate for played review.
"""
import hashlib
import json
import math
import runpy
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qualified_assembly_preflight import validate_manifest, recheck_manifest_pins, validate_body_operator, STALE_DRIVER_KEYS
EXPECTED = {'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L',
            'ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}
REQUIRED = {'restSurfaceClearanceQualified','selfIntersectionQualified',
            'sourceArtworkTransportQualified','bodyAndSourceRestValidated'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pinned(record):
    path = Path(record['path']).resolve()
    assert sha(path) == record['sha256'], ('Source pin changed', str(path))
    return path

args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 2
manifest_path, out = [Path(p).resolve() for p in args]
manifest = json.loads(manifest_path.read_text())
manifest_sha = sha(manifest_path)
assembler_sha = sha(__file__)
preflight_path = Path(__file__).with_name('qualified_assembly_preflight.py')
preflight_sha = sha(preflight_path)
preflight = validate_manifest(manifest, ROOT)
rig_native = preflight['paths']['rigMaster']
base_contract = preflight['baseContract']
face_recipe, field_recipe = [preflight['paths'][key] for key in ('faceRecipe','fieldRecipe')]
assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild')

import bpy
from mathutils import Matrix, Vector

out.mkdir(parents=True)
bpy.ops.wm.open_mainfile(filepath=str(rig_native))
rig, body = bpy.data.objects['RiderSkeleton'], bpy.data.objects['RiderBody']
assert len(rig.data.bones) == 75 and len(body.data.vertices) == 10582
assert rig.matrix_world.is_identity and body.matrix_world.is_identity and not rig.constraints and rig.parent is None
assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH'} == {'RiderBody'}
assert body.parent == rig
assert set(base_contract['specification']['jointNames'].values())=={bone.name for bone in rig.data.bones}
source_ids = body.data.attributes.get('_SOURCE_VERTEX_ID')
assert source_ids and source_ids.domain=='POINT' and source_ids.data_type=='INT'
assert [item.value for item in source_ids.data]==list(range(10582)), 'Prepared master must preserve explicit source point IDs'
body_modifiers = list(body.modifiers)
actual_operators = []
for index, modifier in enumerate(body_modifiers):
    assert modifier.type in {'ARMATURE','TRIANGULATE'}, 'Unsupported prepared body modifier'
    properties = ['show_viewport','show_render']
    properties += ['quad_method','ngon_method','min_vertices','keep_custom_normals'] if modifier.type=='TRIANGULATE' else [
        'use_deform_preserve_volume','use_vertex_groups','use_bone_envelopes','use_multi_modifier','vertex_group','invert_vertex_group']
    actual_operators.append({'index':index,'name':modifier.name,'type':modifier.type,
        'options':{key:getattr(modifier,key) for key in properties if hasattr(modifier,key)}})
validate_body_operator(preflight['bodyOperatorReceipt'], manifest['rigMaster'], actual_operators)
assert next(modifier for modifier in body_modifiers if modifier.type=='ARMATURE').object==rig
rig.animation_data_clear()
for bone in rig.pose.bones:
    assert not bone.constraints, ('Prepared master must be constraint-free', bone.name)
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
prepared_rest = {bone.name: (bone.parent.name if bone.parent else None, tuple(bone.head_local), tuple(bone.tail_local),
                            tuple(tuple(row) for row in bone.matrix_local)) for bone in rig.data.bones}

def identity(obj):
    h = hashlib.sha256()
    for vertex in obj.data.vertices: h.update(struct.pack('<3f', *vertex.co))
    for polygon in obj.data.polygons:
        h.update(struct.pack('<II',len(polygon.vertices),polygon.material_index))
        h.update(struct.pack('<'+'I'*len(polygon.vertices),*polygon.vertices))
    for uv in obj.data.uv_layers:
        for corner in uv.data: h.update(struct.pack('<2f',*corner.uv))
    for vertex in obj.data.vertices:
        for group in vertex.groups:
            h.update(obj.vertex_groups[group.group].name.encode()+struct.pack('<f',group.weight))
    return h.hexdigest()

def assert_zero_helper_influences(objects):
    helpers = {'PalmSocket.L','PalmSocket.R','SoleSocket.L','SoleSocket.R'}
    for obj in objects:
        names = {group.index:group.name for group in obj.vertex_groups}
        assert all(names[group.group] not in helpers for vertex in obj.data.vertices for group in vertex.groups if group.weight>0), \
            ('Contact helpers must have exactly zero source influence',obj.name)

append_reports = []
for unit, qualification in zip(manifest['units'], preflight['qualifications']):
    with bpy.data.libraries.load(str(pinned(unit['native'])), link=False) as (available, selected):
        assert set(unit['objects']) <= set(available.objects)
        selected.objects = unit['objects']
    for obj in selected.objects:
        assert obj.type == 'MESH' and obj.name in unit['objects'] and obj.matrix_world.is_identity
        before = identity(obj)
        assert before == qualification['objectGeometryUVAndFieldsSHA256'][obj.name], ('Qualified object fingerprint changed',obj.name)
        assert not obj.constraints and obj.animation_data is None, 'Garment object cannot carry independent constraints/animation'
        modifiers = list(obj.modifiers)
        assert len(modifiers) == 1 and modifiers[0].type == 'ARMATURE'
        operator = modifiers[0]
        assert operator.show_viewport and operator.show_render and operator.use_vertex_groups
        assert not operator.use_deform_preserve_volume and not operator.use_bone_envelopes and not operator.use_multi_modifier
        assert operator.vertex_group=='' and not operator.invert_vertex_group, 'Qualified garment must already use the same linear skin operator'
        old = modifiers[0].object
        assert old is not None and {b.name for b in old.data.bones} == {b.name for b in rig.data.bones}
        used = {obj.vertex_groups[g.group].name for v in obj.data.vertices for g in v.groups if g.weight > 0}
        required_rest = set(used)
        for name in used:
            required_rest.update(b.name for b in old.data.bones[name].parent_recursive)
        unused_changes = []
        for old_bone in old.data.bones:
            new = rig.data.bones[old_bone.name]
            assert (old_bone.parent.name if old_bone.parent else None) == (new.parent.name if new.parent else None)
            equal = old_bone.matrix_local == new.matrix_local and old_bone.head_local == new.head_local and old_bone.tail_local == new.tail_local
            if old_bone.name in required_rest:
                assert equal, ('Used garment rest changed; explicit rebinding required',obj.name,old_bone.name)
            elif not equal: unused_changes.append(old_bone.name)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = Matrix.Identity(4)
        modifiers[0].object = rig
        obj.hide_render = obj.hide_viewport = False
        obj.hide_set(False)
        assert all(m and m.use_nodes for m in obj.data.materials)
        images = [n.image for m in obj.data.materials for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
        assert images and all(i.packed_file for i in images)
        assert identity(obj) == before
        append_reports.append({'object':obj.name,'sourceGeometryUVAndFieldsSHA256':before,
                               'usedJointAndAncestorRestExactlyPreserved':True,
                               'explicitUnusedRestDifferences':unused_changes})

assert_zero_helper_influences([o for o in bpy.context.scene.objects if o.type=='MESH'])
face = runpy.run_path(str(face_recipe))['buildFace'](body,rig,out)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
assert {o.name for o in meshes} == EXPECTED
for obj in meshes:
    obj.hide_render = obj.hide_viewport = False
    obj.hide_set(False)
    assert obj.data.polygons and all(material and material.use_nodes for material in obj.data.materials)
    assert all(image.packed_file for material in obj.data.materials for node in material.node_tree.nodes
               if node.type=='TEX_IMAGE' and (image:=node.image) is not None), 'Complete final source maps must be packed'
canonical = runpy.run_path(str(field_recipe))['canonicalizeSelectedFields'](meshes,rig,out)
assert_zero_helper_influences(meshes)
# Foot support is an explicit source measurement in the manifest, not the old
# foot floor and not the minimum of arbitrary calf/lining vertices.
assert set(manifest['soleSupport']) == {'L','R'}
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for side, support in manifest['soleSupport'].items():
    assert support['object'] == 'ActualSelectedBoot.'+side
    pinned(support['independentMeasurement'])
    bone = rig.data.edit_bones['SoleSocket.'+side]
    assert not bone.use_connect and not bone.children, 'Sole helper must be a free rigid leaf'
    matrix = Matrix(support['nativeFrame'])
    assert matrix.to_3x3().determinant() > 0
    bone.matrix = matrix
    bone.length = support['boneLengthM']
    assert 0 < bone.length < .1
bpy.ops.object.mode_set(mode='OBJECT')
for side, support in manifest['soleSupport'].items():
    obj = bpy.data.objects[support['object']]
    obj.data.calc_loop_triangles()
    patch = support['supportPatch']; points = []; normal = Vector((0,0,0))
    for triangle_row, weights in zip(patch['triangleRows'],patch['barycentrics']):
        assert triangle_row < len(obj.data.loop_triangles)
        triangle = obj.data.loop_triangles[triangle_row]
        a,b,c = [obj.data.vertices[index].co for index in triangle.vertices]
        points.append(sum((point*weight for point,weight in zip((a,b,c),weights)),Vector((0,0,0))))
        normal += (b-a).cross(c-a)
    measured = sum(points,Vector((0,0,0)))/len(points)
    assert (measured-Vector(patch['pointNative'])).length < 1e-7, 'Sole patch point differs from actual source triangles'
    assert normal.length>0 and normal.normalized().dot(Vector(patch['outwardNormalNative'])) > 1-1e-7, 'Sole patch normal differs from actual source triangles'
    assert max(abs(rig.data.bones['SoleSocket.'+side].matrix_local[i][j]-support['nativeFrame'][i][j]) for i in range(4) for j in range(4)) < 1e-6
for bone in rig.data.bones:
    if not bone.name.startswith('SoleSocket.'):
        assert prepared_rest[bone.name] == (bone.parent.name if bone.parent else None, tuple(bone.head_local),tuple(bone.tail_local),
                                            tuple(tuple(row) for row in bone.matrix_local)), ('Assembly changed prepared actual rest',bone.name)
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1,49
rig.animation_data_create()
rig.animation_data.action = bpy.data.actions.new('RiderIdleBreath')
for frame, angle in [(1,0),(13,.012),(25,0),(37,-.012),(49,0)]:
    scene.frame_set(frame)
    for name,multiplier in [('DEF-spine.002',1),('DEF-spine.003',-.5),('DEF-spine.006',-.5)]:
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = (angle*multiplier,0,0)
        bone.keyframe_insert(data_path='rotation_euler',frame=frame,group=name)
scene.frame_set(1)
contract = base_contract
contract['accepted'] = False
contract['specification']['jointNames'] = {b.name:b.name for b in rig.data.bones}
contract['specification']['meshNames'] = {o.name:o.name for o in meshes}
contract['nativeRest']['bones'] = [{'name':b.name,'parent':b.parent.name if b.parent else None,
    'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(row) for row in b.matrix_local]} for b in rig.data.bones]
assert 'correctedDigitControls' in manifest, 'Physiological digit controls require explicit new-rig authority'
digit_receipt = preflight['digitReceipt']
assert digit_receipt['rigNativeSHA256'] == manifest['rigMaster']['sha256']
contract['driver']['digitFlex'] = digit_receipt['digitFlex']
contract['driver']['socketOrientationCalibrationRequired'] = True
for key in ['sourceSHA256','metadataSHA256','glbSHA256','genericAction','exportedObjectMeshes','poseCalibration']:
    contract.pop(key,None)
assert not STALE_DRIVER_KEYS.intersection(contract['driver'])
contract['driver']['freshSourceCalibrationRequired'] = True
contract['calibrationState'] = 'NEW_NATIVE_GPU_AND_CONTACT_CALIBRATION_REQUIRED'
contract['qualificationState'] = {'digitEnvelopes':'DECLARED_FINITE_LIMITS_RANGE_REVIEW_PENDING',
    'movingAnatomy':'COMPLETE_CLOTHED_NATIVE_ENGINE_REVIEW_PENDING','playedArt':'PARENT_REVIEW_PENDING',
    'promotionAllowed':False}
bpy.ops.object.select_all(action='DESELECT')
rig.hide_set(False)
rig.select_set(True)
for obj in meshes: obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider-assembled.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'),export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_force_sampling=True,
    export_bake_animation=True,export_def_bones=True,export_skins=True,export_influence_nb=4,
    export_all_influences=False,export_apply=True,export_yup=True,export_attributes=True)
raw = (out/'rider.glb').read_bytes()
size = struct.unpack_from('<I',raw,12)[0]
doc = json.loads(raw[20:20+size])
assert len(doc['skins']) == 1 and len(doc['skins'][0]['joints']) == 75
mesh_nodes = [node for node in doc['nodes'] if 'mesh' in node]
assert len(mesh_nodes)==7 and {node['name'] for node in mesh_nodes}==EXPECTED
assert all(node.get('skin')==0 and doc['meshes'][node['mesh']]['primitives'] for node in mesh_nodes)
for node in mesh_nodes:
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        assert {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','_NATIVE_ID'} <= set(primitive['attributes'])
        assert 'material' in primitive and primitive['material'] < len(doc['materials'])
contract['glbSHA256'] = sha(out/'rider.glb')
contract['exportedObjectMeshes'] = [{'nodeIndex':i,'nodeName':n.get('name'),'meshIndex':n['mesh'],
    'meshName':doc['meshes'][n['mesh']].get('name'),'primitiveCount':len(doc['meshes'][n['mesh']]['primitives'])}
    for i,n in enumerate(doc['nodes']) if 'mesh' in n]
(out/'rider-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
recheck_manifest_pins(manifest)
assert sha(manifest_path)==manifest_sha and sha(__file__)==assembler_sha and sha(preflight_path)==preflight_sha, 'Assembly source changed during construction'
report = {'accepted':False,'inputManifest':{'path':str(manifest_path),'sha256':sha(manifest_path)},
    'native':{'path':str(out/'rider-assembled.blend'),'sha256':sha(out/'rider-assembled.blend')},
    'glb':{'path':str(out/'rider.glb'),'sha256':sha(out/'rider.glb')},'appendReports':append_reports,
    'selectedFace':face['report'],'canonicalFinalFields':canonical,'objects':sorted(EXPECTED),
    'contactHelperSourceAndCanonicalInfluencesExactlyZero':True,
    'soleFramesMatchPinnedActualOuterSolePatches':True,
    'nonSolePreparedRestExactlyPreserved':True,
    'preparedRigNativeSHA256':manifest['rigMaster']['sha256'],
    'preparedBodyOperatorReceipt':manifest['preparedBodyOperator'],
    'preparedBodyModifierOperators':actual_operators,
    'qualificationState':contract['qualificationState'],
    'digitMotionReceipt':digit_receipt['smallCurlSignProof'],
    'assemblerSHA256':assembler_sha, 'preflightSHA256':preflight_sha,
    'sourceQualificationReceipts':[unit['independentQualification'] for unit in manifest['units']],
    'requiredFinalReadbacks':['fresh native reopen and protected selected face/source IDs','all material primitive decoded current IDs and canonical named FOUR equality',
                             'fresh changed-rig native/GPU/socket/contact calibration','parent naturally played complete outfit art and physical-phone gate'],
    'limits':['Independent final native/decoded readback and fresh changed-rig calibration required.',
              'No complete-outfit played art, contact or physical-phone acceptance.']}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
recheck_manifest_pins(manifest)
assert sha(manifest_path)==manifest_sha and sha(__file__)==assembler_sha and sha(preflight_path)==preflight_sha, 'Assembly source changed during construction'
print(json.dumps({'status':'COMPLETE_QUALIFIED_SOURCE_CANDIDATE_UNACCEPTED','glbSHA256':report['glb']['sha256']}))
