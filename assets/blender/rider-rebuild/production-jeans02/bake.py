"""Inspect the actual selected donor first; then bake isolated real PBR regions.
The canonical source, target geometry/UV/fields and wearer remain untouched.
"""
import argparse
import hashlib
import json
import runpy
import traceback
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path


def write(out, report):
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def shape(obj, helpers):
    return hashlib.sha256(json.dumps({
        'vertices': [list(v.co) for v in obj.data.vertices],
        'polygons': helpers['topology'](obj.data),
        'uv': helpers['uv_rows'](obj), 'fields': helpers['fields'](obj)},
        separators=(',', ':')).encode()).hexdigest()


def selected_maps(source, intake):
    material = source.data.materials[0]
    nodes = [n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    result = {}
    for label, row in intake['maps'].items():
        matches = [n for n in nodes if n.image.packed_file and
                   hashlib.sha256(n.image.packed_file.data).hexdigest() == row['sha256']]
        assert len(matches) == 1, ('Actual original packed map absent/ambiguous', label)
        image = matches[0].image
        assert list(image.size) == row['size'], ('Original map size changed', label)
        assert image.colorspace_settings.name == ('sRGB' if label == 'albedo' else 'Non-Color')
        result[label] = matches[0]
    return result


def aim(obj, target=(0, 0, .55)):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def inspect(scene, body, target, source, intake, out, report):
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Jeans02MatchedSelectedWorld')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55
    scene.world = world
    for label, position, energy in [('Key', (2, -3, 4), 650),
                                    ('Fill', (-3, -2, 2), 450), ('Rim', (0, 3, 3), 700)]:
        data = bpy.data.lights.new('Jeans02' + label, 'AREA')
        data.energy, data.size = energy, 3
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        aim(obj, (0, 0, .65))
    camera = bpy.data.objects.new('Jeans02MatchedCamera', bpy.data.cameras.new('Jeans02MatchedCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 1.2
    report['photos'] = []
    for variant, garment in [('actualTarget', target), ('actualAlignedSelectedDonor', source)]:
        for obj in scene.objects:
            if obj.type == 'MESH':
                obj.hide_render = obj not in (body, garment)
        body.hide_render = False
        garment.hide_render = False
        garment.hide_set(False)
        for label, position in [('front', (1.1, -3, .9)), ('back', (-1.1, 3, .9)), ('profile', (3, 0, .9))]:
            camera.location = position
            aim(camera)
            path = out / (variant + '-' + label + '.png')
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            report['photos'].append({'variant': variant, 'view': label,
                                     'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
            write(out, report)
    report['status'] = 'MATCHED_ACTUAL_DONOR_AND_TARGET_VIEWS_SAVED_REVIEW_PENDING'
    report['completeBodyVisibleInEveryView'] = True


def regional_copy(obj, name, keep):
    """Keep original UVs and exact corner normals across the regional cut."""
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = name
    bpy.context.scene.collection.objects.link(copy)
    copy.hide_render = False
    copy.hide_set(False)
    for modifier in list(copy.modifiers):
        copy.modifiers.remove(modifier)
    normals = [tuple(n.vector) for n in copy.data.corner_normals]
    old_normal = {(p.index, copy.data.loops[i].vertex_index): normals[i]
                  for p in copy.data.polygons for i in p.loop_indices}
    bm = bmesh.new()
    bm.from_mesh(copy.data)
    vertex_id = bm.verts.layers.int.new('BakeOriginalVertex')
    face_id = bm.faces.layers.int.new('BakeOriginalFace')
    for vertex in bm.verts:
        vertex[vertex_id] = vertex.index
    for face in bm.faces:
        face[face_id] = face.index
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f.calc_center_median())], context='FACES')
    bm.to_mesh(copy.data)
    bm.free()
    vi, fi = copy.data.attributes['BakeOriginalVertex'], copy.data.attributes['BakeOriginalFace']
    retained = [old_normal[(fi.data[p.index].value, vi.data[copy.data.loops[i].vertex_index].value)]
                for p in copy.data.polygons for i in p.loop_indices]
    assert retained and len(retained) == len(copy.data.loops)
    copy.data.normals_split_custom_set(retained)
    return copy


def bake(scene, body, target, source, maps, intake, out, report, resolution):
    admission = intake['inspectionAdmission']
    assert admission['parentViewedMatchedDonor'] and admission['approvedForFirstTransfer'], 'Actual matched donor review required before baking'
    prior = json.loads(pin(admission['receipt']).read_text())
    assert prior['native'] == intake['native'] and prior['targetMarker'] == intake['targetMarker']
    assert prior['status'] == 'MATCHED_ACTUAL_DONOR_AND_TARGET_VIEWS_SAVED_REVIEW_PENDING'
    assert len(prior['photos']) == 6
    assert prior['targetGeometryUVFullFourExact'] and prior['originalPackedMapsExact']
    for photo in prior['photos']:
        pin(photo)
    if resolution == 4096:
        assert intake['final4KAdmission']['approved'], 'Final4K requires actual first-transfer review'
        first = json.loads(pin(intake['final4KAdmission']['firstTransferReceipt']).read_text())
        assert first['native'] == intake['native'] and first['resolution'] in (1024, 2048)
        assert first['status'] == 'ACTUAL_SELECTED_PBR_TRANSFER_SAVED_REVIEW_PENDING'
    settings = intake['bakeSettings']
    scene.cycles.samples = 1
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.use_cage = False
    scene.render.bake.cage_extrusion = settings['extrusionMetres']
    scene.render.bake.max_ray_distance = settings['maximumRayMetres']
    scene.render.bake.margin = settings['marginPixels']
    # Save the unchanged real geometry/source before any map or PBR mutation.
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'pre-bake-native.blend'))
    graph = bpy.context.evaluated_depsgraph_get()
    dense = source.copy()
    dense.data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
    dense.name = 'TemporaryEvaluatedSelectedJeans'
    scene.collection.objects.link(dense)
    for modifier in list(dense.modifiers):
        dense.modifiers.remove(modifier)
    dense.hide_render = True
    dense.data.materials.clear()
    selected_material = source.data.materials[0].copy()
    dense.data.materials.append(selected_material)
    sn, sl = selected_material.node_tree.nodes, selected_material.node_tree.links
    output, principled = sn.get('Material Output'), sn.get('Principled BSDF')
    emission = sn.new('ShaderNodeEmission')
    # The copied material keeps the same exact original map image datablocks.
    copied_maps = {label: sn[node.name] for label, node in maps.items()}
    destination = bpy.data.materials.new('ActualSelectedJeans02BakedPBR')
    destination.use_nodes = True
    dn, dl = destination.node_tree.nodes, destination.node_tree.links
    image_node = dn.new('ShaderNodeTexImage')
    target.data.materials.clear()
    target.data.materials.append(destination)
    regions = [('pelvis', lambda p: p.z > .84, lambda p: p.z > .80),
               ('left', lambda p: p.z <= .84 and p.x >= 0, lambda p: p.z < .89 and p.x >= -.004),
               ('right', lambda p: p.z <= .84 and p.x < 0, lambda p: p.z < .89 and p.x <= .004)]
    report.update(status='ACTUAL_SELECTED_PBR_TRANSFER_RUNNING', resolution=resolution,
                  settings={'useCage': False, **settings}, maps={}, regionalBakes=[])
    write(out, report)
    baked = {}
    for label, kind in [('albedo', 'EMIT'), ('metallicRoughness', 'EMIT'), ('normal', 'NORMAL')]:
        image = bpy.data.images.new('Jeans02Selected_' + label, width=resolution, height=resolution, alpha=True)
        image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'
        image_node.image = image
        dn.active = image_node
        if kind == 'EMIT':
            sl.new(copied_maps[label].outputs['Color'], emission.inputs['Color'])
            sl.new(emission.outputs[0], output.inputs['Surface'])
        else:
            sl.new(principled.outputs[0], output.inputs['Surface'])
            scene.render.bake.normal_space = 'TANGENT'
        for region, target_keep, source_keep in regions:
            src = regional_copy(dense, 'BakeSelected_' + region, source_keep)
            dst = regional_copy(target, 'BakeTarget_' + region, target_keep)
            bpy.ops.object.select_all(action='DESELECT')
            dst.select_set(True)
            src.select_set(True)
            bpy.context.view_layer.objects.active = dst
            scene.render.bake.use_clear = region == 'pelvis'
            bpy.ops.object.bake(type=kind)
            report['regionalBakes'].append({'map': label, 'region': region,
                                           'sourceFaces': len(src.data.polygons), 'targetFaces': len(dst.data.polygons)})
            for obj in (src, dst):
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.meshes.remove(data)
            write(out, report)
        path = out / (label + '.png')
        image.filepath_raw, image.file_format = str(path), 'PNG'
        image.save()
        image.pack()
        baked[label] = image
        report['maps'][label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': resolution}
        write(out, report)
        bpy.ops.wm.save_as_mainfile(filepath=str(out / 'partial-selected-transfer.blend'))
    bs = dn.get('Principled BSDF')
    image_node.image = baked['albedo']
    dl.new(image_node.outputs['Color'], bs.inputs['Base Color'])
    mr = dn.new('ShaderNodeTexImage')
    mr.image = baked['metallicRoughness']
    split = dn.new('ShaderNodeSeparateColor')
    dl.new(mr.outputs[0], split.inputs[0])
    dl.new(split.outputs['Green'], bs.inputs['Roughness'])
    dl.new(split.outputs['Blue'], bs.inputs['Metallic'])
    normal = dn.new('ShaderNodeTexImage')
    normal.image = baked['normal']
    convert = dn.new('ShaderNodeNormalMap')
    dl.new(normal.outputs[0], convert.inputs['Color'])
    dl.new(convert.outputs[0], bs.inputs['Normal'])
    data = dense.data
    bpy.data.objects.remove(dense, do_unlink=True)
    bpy.data.meshes.remove(data)
    target.hide_render = False
    target.hide_set(False)
    body.hide_render = False
    report['status'] = 'ACTUAL_SELECTED_PBR_TRANSFER_SAVED_REVIEW_PENDING'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('intake')
    parser.add_argument('out')
    parser.add_argument('--stage', choices=('inspect', 'bake'), required=True)
    parser.add_argument('--resolution', type=int, choices=(1024, 2048, 4096), default=1024)
    args = parser.parse_args(__import__('sys').argv[__import__('sys').argv.index('--') + 1:])
    intake_path = Path(args.intake).resolve()
    intake = json.loads(intake_path.read_text())
    out = Path(args.out).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'stage': args.stage,
              'native': intake['native'], 'intakeSHA256': sha(intake_path), 'authorSHA256': sha(__file__),
              'limits': ['No rest/motion/art/player acceptance.', 'Configured bake rays are not a proved coverage/correspondence bound.',
                         'Original selected donor and PBR only; misses/distortion require actual review.']}
    try:
        assert intake['accepted'] is False
        for row in [intake[k] for k in ('native', 'dense', 'nativeFields')] + list(intake['helpers'].values()) + list(intake['maps'].values()):
            pin(row)
        bpy.ops.wm.open_mainfile(filepath=str(pin(intake['native'])))
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton')]
        assert target.get('productionJeansRecipe') == intake['targetMarker'] == 'rockhop-native-local-gusset-v2'
        assert target.get('selectedAppearanceAuthority') == intake['dense']['sha256']
        assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
        assert not body.hide_get() and not body.hide_render
        report['targetMarker'] = target.get('productionJeansRecipe')
        helpers = runpy.run_path(str(pin(intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(intake['helpers']['originalAuthor'])))
        target_before = shape(target, helpers)
        source_before = shape(source, helpers)
        body_before = original['signature'](body, rig)
        maps = selected_maps(source, intake)
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.render.threads_mode, scene.render.threads = 'FIXED', 2
        scene.frame_set(1)
        write(out, report)
        if args.stage == 'inspect':
            inspect(scene, body, target, source, intake, out, report)
        else:
            bake(scene, body, target, source, maps, intake, out, report, args.resolution)
        assert shape(target, helpers) == target_before and shape(source, helpers) == source_before
        assert original['signature'](body, rig) == body_before
        assert selected_maps(source, intake).keys() == maps.keys()
        report.update(targetGeometryUVFullFourExact=True, canonicalDenseGeometryUVFieldsExact=True,
                      bodyAnd75RestUntouched=True, originalPackedMapsExact=True,
                      targetGeometryUVFullFourSHA256=target_before, canonicalDenseStateSHA256=source_before,
                      bodyAnd75RestSHA256=body_before)
        if args.stage == 'bake':
            path = out / 'production-jeans-textured.blend'
            bpy.ops.wm.save_as_mainfile(filepath=str(path))
            report['resultNative'] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
        assert sha(pin(intake['native'])) == intake['native']['sha256']
        write(out, report)
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_STAGE', error=repr(error), traceback=traceback.format_exc())
        write(out, report)
        if args.stage == 'bake' and (out / 'pre-bake-native.blend').exists():
            try:
                for image in bpy.data.images:
                    if image.name.startswith('Jeans02Selected_'):
                        image.pack()
                bpy.ops.wm.save_as_mainfile(filepath=str(out / 'failed-selected-transfer.blend'))
            except BaseException as save_error:
                report['failedCheckpointError'] = repr(save_error)
                write(out, report)
        raise


if __name__ == '__main__':
    main()
