"""One authored selected-boot pass; run only on the parent's CPU2 lease.

blender -b -t 2 --python-exit-code 1 --python THIS -- author FRESH_PRIVATE_OUT
blender -b -t 2 --python-exit-code 1 --python THIS -- bake AUTHOR_PRIVATE_OUT
Explicit controls are controls.json. No foot/cavity/chart solver is imported.
The selected dense mesh is the shape/detail source; its failed hidden shaft floor
is removed using the already recorded semantic source witness. The production
boot is a conventional simplified rigid derivative, with fresh UV and real bake.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG_PATH = HERE / 'controls.json'
CONFIG = json.loads(CONFIG_PATH.read_text())
CONTROL = CONFIG['authoring']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def input_path(name):
    row = CONFIG['inputs'][name]
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], ('Changed source', path)
    return path


def snapshot(body, rig):
    names = {g.index: g.name for g in body.vertex_groups}
    return {
        'body': [(tuple(v.co), sorted((names[g.group], g.weight) for g in v.groups))
                 for v in body.data.vertices],
        'faces': [tuple(p.vertices) for p in body.data.polygons],
        'rest': [(b.name, tuple(b.head_local), tuple(b.tail_local),
                  tuple(tuple(row) for row in b.matrix_local)) for b in rig.data.bones],
        'visibility': (body.hide_render, body.hide_viewport),
    }


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def affine(body_arrays, side):
    names = body_arrays['jointNames'].tolist()
    ankle = body_arrays['jointHeads'][names.index('DEF-foot.' + side)]
    toe = body_arrays['jointHeads'][names.index('DEF-toe.' + side)]
    toward_toe = np.r_[toe[:2] - ankle[:2], 0.]
    toward_toe /= np.linalg.norm(toward_toe)
    frame = np.column_stack([-toward_toe, [0., 0., 1.],
                             np.cross(-toward_toe, [0., 0., 1.])])
    spec = CONTROL['targetSides'][side]
    scales = np.array(spec['scales'])
    scales[2] *= spec['mirrorWidth']
    result = np.eye(4)
    result[:3, :3] = frame * scales[None, :]
    result[:3, 3] = np.r_[ankle[:2], 0.] + np.einsum('ij,j->i', frame, spec['offset'], optimize=False)
    return result, frame, ankle


def source_selection(dense, compact, witness):
    # Source selection only: the recorded actual shaft-floor witness is projected
    # to the original dense source. No body fitting or anatomical detection here.
    tree = BVHTree.FromPolygons([Vector(p) for p in compact['vertices']],
                               compact['faces'].tolist(), all_triangles=True)
    centers = dense['vertices'][dense['faces']].mean(1)
    remove = np.zeros(len(centers), dtype=bool)
    below = centers[:, 1] < CONTROL['sourceLandmarks']['innerShaftDeleteBelowY']
    # The original witness lies only in this explicitly authored shaft box.
    box = below & (centers[:, 0] > .02) & (centers[:, 0] < .91)
    box &= (centers[:, 2] > -.31) & (centers[:, 2] < .23)
    for row in np.flatnonzero(box):
        _, _, owner, _ = tree.find_nearest(Vector(centers[row]))
        remove[row] = witness['sourceInnerVisibleMask'][owner]
    return np.flatnonzero(~remove), np.flatnonzero(remove)


def selected_material():
    mat = bpy.data.materials.new('Actual selected black boot PBR source')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    textures = {}
    for role, filename in [('albedo', 'baseColorTexture.png'),
                           ('metallicRoughness', 'metallicRoughnessTexture.png')]:
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(input_path(filename)), check_existing=False)
        tex.image.colorspace_settings.name = 'sRGB' if role == 'albedo' else 'Non-Color'
        tex.image.pack()
        textures[role] = tex
    links.new(textures['albedo'].outputs['Color'], bsdf.inputs['Base Color'])
    split = nodes.new('ShaderNodeSeparateColor')
    split.mode = 'RGB'
    links.new(textures['metallicRoughness'].outputs['Color'], split.inputs['Color'])
    links.new(split.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(split.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat, textures


def lattice_author(source):
    spec = CONTROL['sourceLattice']
    low, high = np.array(spec['bounds'])
    data = bpy.data.lattices.new('Authored forefoot instep cage; sole heel collar held')
    data.points_u, data.points_v, data.points_w = spec['resolution']
    data.interpolation_type_u = data.interpolation_type_v = data.interpolation_type_w = 'KEY_LINEAR'
    obj = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = (low + high) / 2
    obj.scale = high - low
    for w in range(data.points_w):
        for v in range(data.points_v):
            for u in range(data.points_u):
                row = (w * data.points_v + v) * data.points_u + u
                data.points[row].co_deform.y += spec['liftYByVThenU'][v][u] / (high[1] - low[1])
                data.points[row].co_deform.z *= spec['transverseScaleByU'][u]
    modifier = source.modifiers.new('Author upper volume around unchanged foot', 'LATTICE')
    modifier.object = obj
    active(source)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.hide_render = True
    obj.hide_set(True)
    return obj


def weight_boot(obj, rig, body_arrays, side):
    _, frame, ankle = affine(body_arrays, side)
    ankle_shin = 'DEF-shin.' + side + '.001'
    groups = {name: obj.vertex_groups.new(name=name)
              for name in ('DEF-foot.' + side, 'DEF-toe.' + side, ankle_shin)}
    lo_toe, hi_toe = CONTROL['toeBlendLocalX']
    lo_shin, hi_shin = CONTROL['shinBlendHeightM']
    for vertex in obj.data.vertices:
        p = np.asarray(vertex.co)
        longitudinal = float(np.einsum('i,i->', p-np.r_[ankle[:2], 0.], frame[:,0], optimize=False))
        toe = CONTROL['toeMaximumWeight'] * np.clip((longitudinal-lo_toe)/(hi_toe-lo_toe), 0, 1)
        shin = CONTROL['shinMaximumWeight'] * np.clip((p[2]-lo_shin)/(hi_shin-lo_shin), 0, 1)
        if p[2] < CONTROL['soleRigidBelowHeightM']:
            toe = shin = 0.
        for name, weight in [('DEF-foot.' + side, 1-toe-shin),
                             ('DEF-toe.' + side, toe), (ankle_shin, shin)]:
            if weight > 0:
                groups[name].add([vertex.index], float(weight), 'REPLACE')
    modifier = obj.modifiers.new('Same actual shared75 wearer rig', 'ARMATURE')
    modifier.object = rig
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()


def isolate_diagnostic(scene, objects):
    body = bpy.data.objects['RiderBody']
    assert not body.hide_render and not body.hide_viewport
    allowed = {body.name, *(obj.name for obj in objects)}
    for obj in scene.objects:
        if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            obj.hide_render = obj.name not in allowed
    body.hide_render = False
    for obj in objects:
        obj.hide_set(False)


def mirrored_partner(obj, name, left_affine, right_affine):
    import bmesh
    partner = obj.copy()
    partner.data = obj.data.copy()
    partner.name = name
    bpy.context.collection.objects.link(partner)
    transform = np.einsum('ij,jk->ik', left_affine, np.linalg.inv(right_affine), optimize=False)
    partner.data.transform(Matrix(transform))
    bm = bmesh.new()
    bm.from_mesh(partner.data)
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(partner.data)
    bm.free()
    partner.data.update()
    return partner


def save_boot_arrays(out, objects, body_arrays):
    receipts = []
    names = body_arrays['jointNames'].tolist()
    for obj, side in objects:
        obj.data.calc_loop_triangles()
        vertices = np.array([tuple(v.co) for v in obj.data.vertices])
        faces = np.array([tuple(t.vertices) for t in obj.data.loop_triangles], dtype=np.int32)
        field = np.zeros((len(vertices), len(names)), dtype=np.float32)
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                name = obj.vertex_groups[group.group].name
                field[vertex.index, names.index(name)] = group.weight
        sole = vertices[:,2] < CONTROL['soleRigidBelowHeightM']
        assert abs(field.sum(1)-1).max() < 1e-6
        assert np.all(field[sole, names.index('DEF-foot.'+side)] == 1), 'Sole must remain rigid'
        uvs = np.array([tuple(obj.data.uv_layers.active.data[l].uv)
                        for t in obj.data.loop_triangles for l in t.loops]).reshape(-1,3,2)
        arrays = out/('production-boot-'+side+'.npz')
        np.savez_compressed(arrays, vertices=vertices, faces=faces, coefficients=field,
                            jointNames=body_arrays['jointNames'], triangleCornerUV=uvs,
                            uvCoordinateSystem=np.array('Blender V-up'))
        collar = vertices[(vertices[:,2] > .085) & (vertices[:,2] < .104)]
        receipts.append({'side': side, 'vertices':len(vertices), 'triangles':len(faces),
            'bounds':[vertices.min(0).tolist(),vertices.max(0).tolist()],
            'collarBandBounds':[collar.min(0).tolist(),collar.max(0).tolist()],
            'fieldsSumMaximumError':float(abs(field.sum(1)-1).max()),
            'rigidSoleVertices':int(sole.sum()), 'arrays':{'path':str(arrays),'sha256':sha(arrays)}})
    return receipts


def copy_partner_atlas(right, left):
    assert len(right.data.polygons) == len(left.data.polygons)
    for layer in list(left.data.uv_layers):
        left.data.uv_layers.remove(layer)
    layer = left.data.uv_layers.new(name='ActualCoherentDenseBakeAtlas')
    layer.active_render = True
    left.data.uv_layers.active = layer
    for right_face, left_face in zip(right.data.polygons, left.data.polygons):
        assert set(right_face.vertices) == set(left_face.vertices), 'Mirrored face correspondence changed'
        right_uv = {vertex:tuple(right.data.uv_layers.active.data[loop].uv)
                    for vertex, loop in zip(right_face.vertices, right_face.loop_indices)}
        for vertex, loop in zip(left_face.vertices, left_face.loop_indices):
            layer.data[loop].uv = right_uv[vertex]


def render_views(scene, out, objects, name):
    isolate_diagnostic(scene, objects)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('Boot source matched studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.25, .27, .31, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .6
    scene.world = world
    for i, loc in enumerate([(-.6, -.8, 1.), (.4, .4, .6)]):
        name = 'Boot matching light ' + str(i)
        if bpy.data.objects.get(name):
            continue
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = 45, 1.3
        lamp = bpy.data.objects.new(data.name, data)
        bpy.context.collection.objects.link(lamp)
        lamp.location = loc
        lamp.rotation_euler = (Vector((-.2, -.02, .065))-lamp.location).to_track_quat('-Z','Y').to_euler()
    data = bpy.data.cameras.new('Boot matched view')
    data.type, data.ortho_scale = 'ORTHO', .43
    camera = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    focus = Vector((-.218, -.015, .068))
    for role, offset in [('lateral', (-.56, .275, .05)),
                         ('toe-threequarter', (-.42, -.46, .30))]:
        camera.location = focus + Vector(offset)
        camera.rotation_euler = (focus-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath = str(out / (name + '-' + role + '.png'))
        bpy.ops.render.render(write_still=True)
    return camera


def author(out):
    assert not out.exists(), 'Fresh private result only'
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'AUTHORING_IN_PROGRESS',
              'appearanceStatus': 'PENDING_ACTUAL_BAKE_AND_PARENT_PLAYED_JUDGMENT',
              'controlsSHA256': sha(CONFIG_PATH), 'recipeSHA256': sha(__file__),
              'sourceInputs': CONFIG['inputs'], 'boots': []}
    def save_report():
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save_report()
    dense = dict(np.load(input_path('cleaned-donor.npz')))
    compact = dict(np.load(input_path('retopology-prototype.npz')))
    witness = dict(np.load(input_path('source-semantic-witness.npz')))
    body_arrays = dict(np.load(input_path('native-body.npz')))
    kept, removed = source_selection(dense, compact, witness)
    original_vertex_rows, dense_faces = np.unique(dense['faces'][kept], return_inverse=True)
    dense_faces = dense_faces.reshape(-1, 3)
    np.savez_compressed(out/'source-selection.npz', originalDenseFaceRows=kept,
                        originalDenseVertexRows=original_vertex_rows,
                        removedHiddenShaftFloorOriginalDenseFaceRows=removed)
    report['sourceSelection'] = {'kept': len(kept), 'removedHiddenShaftFloor': len(removed)}
    save_report()
    bpy.ops.wm.open_mainfile(filepath=str(input_path('anatomical-hand-rig.blend')))
    scene = bpy.context.scene
    scene.render.threads_mode, scene.render.threads = 'FIXED', 2
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before = snapshot(body, rig)
    assert len(rig.data.bones) == 75 and not body.hide_render and not body.hide_viewport
    material, source_textures = selected_material()
    mesh = bpy.data.meshes.new('Retained actual dense source with visible collar depth')
    mesh.from_pydata(dense['vertices'][original_vertex_rows].tolist(), [], dense_faces.tolist())
    mesh.update()
    mesh.materials.append(material)
    original_uv = mesh.uv_layers.new(name='Exact Original Dense Selected Corner UV')
    blender_source_uv = dense['originalCornerUV'][kept].copy()
    blender_source_uv[:,:,1] = 1. - blender_source_uv[:,:,1]
    original_uv.data.foreach_set('uv', blender_source_uv.ravel())
    mesh.normals_split_custom_set(dense['donorCornerNormals'][kept].reshape(-1,3).tolist())
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    high = bpy.data.objects.new('Aligned actual selected dense boot.R', mesh)
    bpy.context.collection.objects.link(high)
    lattice = lattice_author(high)
    authored_source_vertices = np.array([tuple(v.co) for v in high.data.vertices])
    right_affine, _, _ = affine(body_arrays, 'R')
    high.data.transform(Matrix(right_affine))
    high.data.update()
    target = high.copy()
    target.data = high.data.copy()
    target.name = 'ProductionSelectedBoot.R'
    bpy.context.collection.objects.link(target)
    active(target)
    simplify = target.modifiers.new('Rigid boot selected detail simplification', 'DECIMATE')
    simplify.ratio = CONTROL['productionDecimateRatio']
    bpy.ops.object.modifier_apply(modifier=simplify.name)
    left_affine, _, _ = affine(body_arrays, 'L')
    left = mirrored_partner(target, 'ProductionSelectedBoot.L', left_affine, right_affine)
    high_left = mirrored_partner(high, 'Aligned actual selected dense boot.L', left_affine, right_affine)
    for obj, side in [(target, 'R'), (left, 'L')]:
        weight_boot(obj, rig, body_arrays, side)
    report['boots'] = save_boot_arrays(out, [(target, 'R'), (left, 'L')], body_arrays)
    report['atlasStatus'] = 'PENDING_NEW_COHERENT_PRODUCTION_ATLAS'
    report['sourceUVPolicy'] = 'Original immutable glTF TEXCOORD_0; Blender donor uses copied UV with V=1-V'
    np.savez_compressed(out/'authored-dense-reference.npz', sourceAuthoredVertices=authored_source_vertices,
                        sourceOriginalDenseVertexRows=original_vertex_rows,
                        originalDenseFaceRows=kept, sourceToRightNativeAffine=right_affine,
                        sourceToLeftNativeAffine=left_affine)
    isolate_diagnostic(scene, [target, left])
    high.hide_set(True)
    high_left.hide_set(True)
    assert snapshot(body, rig) == before, 'Complete body/fields/shared75 rest changed'
    assert all(sha(ROOT/row['path']) == row['sha256'] for row in CONFIG['inputs'].values())
    report['bodyAnd75RestUntouched'] = True
    report['status'] = 'UNACCEPTED_FITTED_WEIGHTED_BOOTS_MAPS_PENDING'
    pending = out/'geometry-appearance-pending.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(pending))
    report['geometryNative'] = {'path':str(pending), 'sha256':sha(pending)}
    save_report()
    # This quick source comparison precedes unwrap and expensive 4K maps.
    # The simplified geometry still carries actual dense-source UV/material;
    # that transient atlas is explicitly pending coherent production baking.
    render_views(scene, out, [target, left], 'prefit-production-selected-map-carrier')
    render_views(scene, out, [high, high_left], 'prefit-actual-aligned-selected-dense')
    report['quickActualSourceFitComparisonRendered'] = True
    isolate_diagnostic(scene, [target, left])
    high.hide_set(True)
    high_left.hide_set(True)
    assert snapshot(body, rig) == before
    checked = out/'author-checked-appearance-pending.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(checked))
    report['authorNative'] = {'path':str(checked), 'sha256':sha(checked)}
    save_report()
    print(json.dumps({'status':report['status'], 'native':report['authorNative'], 'boots':report['boots']}))


def bake(author_out):
    assert author_out.is_relative_to(ROOT / 'harness/out/rider-rebuild')
    report = json.loads((author_out/'report.json').read_text())
    assert report['accepted'] is False and report['bodyAnd75RestUntouched'] is True
    assert report['controlsSHA256'] == sha(CONFIG_PATH)
    assert report['quickActualSourceFitComparisonRendered'] is True
    row = report['authorNative']
    assert sha(row['path']) == row['sha256'], 'Changed authored native'
    out = author_out/'bake01'
    assert not out.exists(), 'Fresh appearance result only'
    out.mkdir()
    report['authorRecipeSHA256'] = report['recipeSHA256']
    report['recipeSHA256'] = sha(__file__)
    report['status'] = 'ACTUAL_SELECTED_BAKE_IN_PROGRESS'
    def save_report():
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save_report()
    bpy.ops.wm.open_mainfile(filepath=row['path'])
    scene = bpy.context.scene
    scene.render.threads_mode, scene.render.threads = 'FIXED', 2
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before = snapshot(body, rig)
    body_arrays = dict(np.load(input_path('native-body.npz')))
    target, left = bpy.data.objects['ProductionSelectedBoot.R'], bpy.data.objects['ProductionSelectedBoot.L']
    high = bpy.data.objects['Aligned actual selected dense boot.R']
    high_left = bpy.data.objects['Aligned actual selected dense boot.L']
    material = high.data.materials[0]
    source_textures = {role:next(n for n in material.node_tree.nodes
                               if n.type=='TEX_IMAGE' and n.image.name.startswith(filename))
                       for role, filename in [('albedo','baseColorTexture.png'),
                                              ('metallicRoughness','metallicRoughnessTexture.png')]}
    # Reuse ordinary atlas/bake helpers, never the old transport/fitting main.
    helper_path = input_path('bake_fitted_detail.py')
    sys.path.insert(0, str(helper_path.parent))
    spec = importlib.util.spec_from_file_location('ordinary_boot_bake_helpers', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.unwrap(target)
    destination = bpy.data.materials.new('Actual Selected Boot 4K Derived PBR')
    destination.use_nodes = True
    target.data.materials.clear()
    target.data.materials.append(destination)
    image_node = destination.node_tree.nodes.new('ShaderNodeTexImage')
    destination.node_tree.nodes.active = image_node
    high.hide_render = False
    high.hide_set(False)
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples = 'CPU', 1
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_cage = False
    scene.render.bake.cage_extrusion = CONTROL['bakeCageOffsetM']
    scene.render.bake.max_ray_distance = CONTROL['maximumBakeRayDistanceM']
    scene.render.bake.margin = CONTROL['marginPixels']
    scene.render.bake.normal_space = 'TANGENT'
    # Same shape, independent coherent target atlas. Emit the actual selected
    # texture values; normals are selected-to-active dense geometry detail.
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.get('Material Output')
    emission = nodes.new('ShaderNodeEmission')
    links.new(emission.outputs[0], output.inputs['Surface'])
    baked, map_receipts = {}, {}
    emission.inputs['Color'].default_value = (1, 1, 1, 1)
    support, support_receipt = helper.bake_image(
        scene, high, target, [image_node], 'boot-actual-selected-support',
        'EMIT', out, CONTROL['mapSize'])
    report['actualBakeSupport'] = helper.support_pixels(support, target, len(target.data.polygons))
    map_receipts['support'] = support_receipt
    save_report()
    for role in ['albedo', 'metallicRoughness']:
        links.new(source_textures[role].outputs['Color'], emission.inputs['Color'])
        baked[role], map_receipts[role] = helper.bake_image(
            scene, high, target, [image_node], 'boot-actual-selected-'+role,
            'EMIT', out, CONTROL['mapSize'])
        report['maps'] = map_receipts
        save_report()
    links.new(nodes.get('Principled BSDF').outputs[0], output.inputs['Surface'])
    baked['normal'], map_receipts['normal'] = helper.bake_image(
        scene, high, target, [image_node], 'boot-actual-selected-normal',
        'NORMAL', out, CONTROL['mapSize'])
    bsdf = destination.node_tree.nodes.get('Principled BSDF')
    for role, image in baked.items():
        node = destination.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        image.colorspace_settings.name = 'sRGB' if role == 'albedo' else 'Non-Color'
        if role == 'albedo':
            destination.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        elif role == 'metallicRoughness':
            split = destination.node_tree.nodes.new('ShaderNodeSeparateColor')
            split.mode = 'RGB'
            destination.node_tree.links.new(node.outputs['Color'], split.inputs['Color'])
            destination.node_tree.links.new(split.outputs['Green'], bsdf.inputs['Roughness'])
            destination.node_tree.links.new(split.outputs['Blue'], bsdf.inputs['Metallic'])
        else:
            normal = destination.node_tree.nodes.new('ShaderNodeNormalMap')
            destination.node_tree.links.new(node.outputs['Color'], normal.inputs['Color'])
            destination.node_tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    copy_partner_atlas(target, left)
    left.data.materials.clear()
    left.data.materials.append(destination)
    report['boots'] = save_boot_arrays(out, [(target, 'R'), (left, 'L')], body_arrays)
    isolate_diagnostic(scene, [target, left])
    high.hide_set(True)
    high_left.hide_set(True)
    assert snapshot(body, rig) == before, 'Appearance stage changed complete body/fields/shared75 rest'
    assert all(sha(ROOT/row['path']) == row['sha256'] for row in CONFIG['inputs'].values())
    report['bodyAnd75RestUntouched'] = True
    report['maps'] = map_receipts
    report['appearanceStatus'] = 'ACTUAL_SELECTED_PBR_BAKED_PARENT_REVIEW_PENDING'
    report['atlasStatus'] = 'ACTUAL_COHERENT_SELECTED_TO_ACTIVE_BAKE'
    report['status'] = 'UNACCEPTED_AUTHORED_SELECTED_BOOT_CANDIDATE'
    native = out/'production-boots.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    report['native'] = {'path':str(native), 'sha256':sha(native)}
    save_report()
    render_views(scene, out, [target, left], 'production-with-complete-body')
    render_views(scene, out, [high, high_left], 'actual-aligned-selected-dense')
    report['matchingStaticViewsRendered'] = True
    save_report()
    print(json.dumps({'status':report['status'],'native':report['native'],'boots':report['boots']}))


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--')+1:]
    assert len(arguments) == 2 and arguments[0] in {'author', 'bake'}
    operation = author if arguments[0] == 'author' else bake
    operation(Path(arguments[1]).resolve())
