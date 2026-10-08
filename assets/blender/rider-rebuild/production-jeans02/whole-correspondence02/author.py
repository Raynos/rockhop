"""One whole selected-denim4K transfer, fixed wearing/source geometry.
Reuse actual successful pelvis; extend existing native control lineage below it.
"""
import hashlib
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[5]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path


def used(obj):
    return np.unique(np.concatenate([tuple(p.vertices) for p in obj.data.polygons]))


def triangulate(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.hide_set(False); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new('FrozenPairedCorrespondenceTriangles', 'TRIANGULATE')
    modifier.quad_method = 'FIXED'; modifier.ngon_method = 'CLIP'
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    assert all(len(p.vertices) == 3 for p in obj.data.polygons)


def lower_surfaces(target, intake, original, local, prior, pairs):
    recipe = json.loads(pin(intake['inputs']['originalRecipe']).read_text())
    with np.load(pin(intake['inputs']['lowerControls'])) as data:
        authored = [data['authoredProjectionControlPositions'], data['authoredCaptureControlPositions']]
    evaluated_positions = []; editable = []
    for name, points in zip(('JeansLowerProjectionControls', 'JeansLowerCaptureControls'), authored):
        obj = local['template_surface'](original, recipe, name)
        assert len(obj.data.vertices) == len(points) == 1691
        for vertex, point in zip(obj.data.vertices, points): vertex.co = point
        obj.data.update(); obj['correspondenceOnly'] = True; obj['wearerFitAuthority'] = False
        obj['sourceEnvelopeSHA256'] = intake['inputs']['sourceEnvelope']['sha256']
        obj.hide_render = True
        mesh = local['evaluated_mesh'](obj)
        assert local['topology'](mesh) == local['topology'](target.data), 'Existing native subdivision lineage changed'
        evaluated_positions.append(np.asarray([tuple(v.co) for v in mesh.vertices], dtype=np.float32))
        bpy.data.meshes.remove(mesh); editable.append(obj)
    # Preserve actual successful pelvis coordinates at every shared boundary ID.
    pinned = [{}, {}]
    for _, _, proxy, cage, _ in pairs:
        for column, obj in enumerate((proxy, cage)):
            lineage = obj.data.attributes['BakeOriginalVertex']
            for vertex in used(obj):
                index = lineage.data[int(vertex)].value; point = np.asarray(obj.data.vertices[int(vertex)].co, dtype=np.float32)
                if index in pinned[column]: assert np.array_equal(pinned[column][index], point)
                pinned[column][index] = point
    for positions, shared in zip(evaluated_positions, pinned):
        for index, point in shared.items(): positions[index] = point
    return evaluated_positions, editable, [len(p) for p in pinned]


def capture(region, selected, proxy, cage, diag, intake, out):
    low, high, shell = [diag['mesh_arrays'](obj) for obj in (proxy, selected, cage)]
    assert np.array_equal(low['triangles'], shell['triangles']) and np.array_equal(low['uv'], shell['uv'])
    size = intake['resolution']; coverage, owner, weights, boundary, degenerate = diag['raster'](low, size)
    assert degenerate == 0
    pixels = np.flatnonzero(owner >= 0); triangles, bary = owner[pixels], weights[pixels]
    vertices = low['triangles'][triangles]
    points = np.einsum('ij,ijk->ik', bary, low['vertices'][vertices])
    origins = np.einsum('ij,ijk->ik', bary, shell['vertices'][vertices])
    directions = points - origins; lengths = np.linalg.norm(directions, axis=1)
    assert np.all(lengths > 1e-6); directions /= lengths[:, None]
    tree = BVHTree.FromPolygons(high['vertices'].tolist(), high['triangles'].tolist(), all_triangles=True, epsilon=0)
    hits = np.full(len(pixels), -1, dtype=np.int32); distance = np.full(len(pixels), np.nan, dtype=np.float32)
    locations = np.full_like(points, np.nan)
    for i, (origin, direction) in enumerate(zip(origins, directions)):
        location, _, triangle, length = tree.ray_cast(Vector(origin), Vector(direction))
        if triangle is not None: hits[i], distance[i], locations[i] = triangle, length, location
    found = hits >= 0; overlap = intake['sourceCutOverlapMetres']
    if region == 'pelvis-front': opposite = found & (locations[:, 1] > -.017 + overlap)
    elif region == 'pelvis-rear': opposite = found & (locations[:, 1] < -.017 - overlap)
    else: opposite = found & (locations[:, 0] * (1 if region == 'lower-L' else -1) < -overlap)
    wrong_side = found & (np.abs(points[:, 0]) > .005) & (points[:, 0] * locations[:, 0] < 0)
    far = found & (distance > intake['maximumCaptureMetres'])
    source_uv = np.full((len(pixels), 2), np.nan, dtype=np.float32)
    t = high['vertices'][high['triangles'][hits[found]]]
    a, b, d = t[:, 0] - t[:, 2], t[:, 1] - t[:, 2], locations[found] - t[:, 2]
    aa, ab, bb = np.sum(a * a, 1), np.sum(a * b, 1), np.sum(b * b, 1)
    ad, bd = np.sum(a * d, 1), np.sum(b * d, 1); determinant = aa * bb - ab * ab
    assert np.all(determinant > 0)
    u, v = (ad * bb - bd * ab) / determinant, (bd * aa - ad * ab) / determinant
    source_uv[found] = np.einsum('ij,ijk->ik', np.column_stack((u, v, 1 - u - v)), high['uv'][hits[found]])
    sf = np.asarray([d.value for d in selected.data.attributes['BakeOriginalFace'].data])
    source_faces = np.full(len(pixels), -1, dtype=np.int32); source_faces[found] = sf[high['faces'][hits[found]]]
    tf = np.asarray([d.value for d in proxy.data.attributes['BakeOriginalFace'].data])
    receiver_faces = tf[low['faces'][triangles]]
    priority = np.full(size * size, -1, dtype=np.int32); priority[pixels] = receiver_faces
    path = out / (region + '-direct-capture.npz')
    np.savez_compressed(path, pixelIds=pixels, receiverOriginalFace=receiver_faces, proxyPoint=points,
        cageOrigin=origins, rayDirection=directions, firstHitMetres=distance, sourcePoint=locations,
        sourceUV=source_uv, originalSourceFace=source_faces, noHit=~found, oppositePhysicalRegion=opposite,
        wrongSide=wrong_side, excessiveDistance=far, boundarySample=boundary[pixels],
        targetUVCoverage=coverage.reshape(size, size))
    result = {'region': region, 'coveredSamples': len(pixels), 'noHit': int((~found).sum()),
        'oppositePhysicalRegion': int(opposite.sum()), 'wrongSide': int(wrong_side.sum()), 'excessiveDistance': int(far.sum()),
        'firstHitMetres': diag['statistics'](distance), 'UVOverlapPixels': int((coverage > 1).sum()),
        'boundarySamples': int(boundary[pixels].sum()), 'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
        'passed': not np.any(~found | opposite | wrong_side | far)}
    return result, coverage.reshape(size, size), priority.reshape(size, size)


def owners_with_native_priority(coverages, priorities, old):
    size = coverages[0].shape[0]; owners = np.zeros((size, size), dtype=np.uint8)
    priority = np.full((size, size), -1, dtype=np.int32); overlap = np.zeros((size, size), dtype=np.uint16)
    for index, (coverage, face) in enumerate(zip(coverages, priorities), 1):
        overlap += coverage
        chosen = (coverage > 0) & (face > priority); owners[chosen], priority[chosen] = index, face[chosen]
    # Existing composite helper supplies only margin domains from these exact
    # owners. Actual baked samples remain selected at the same atlas coordinates.
    disjoint = [(owners == i).astype(np.uint16) for i in range(1, len(coverages) + 1)]
    padded = old['composite_owners'](disjoint, 16)
    return padded, overlap


def matched_whole(scene, body, target, reference, out, report, helpers):
    scene.cycles.samples = 8; scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 800; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('WholeDenimComparisonWorld'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55; scene.world = world
    for name, position, energy in [('Key', (2, -3, 4), 650), ('Fill', (-3, -2, 2), 450), ('Rim', (0, 3, 3), 700)]:
        data = bpy.data.lights.new('Whole' + name, 'AREA'); data.energy, data.size = energy, 3
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj); obj.location = position
        helpers['aim'](obj, (0, 0, .58))
    camera = bpy.data.objects.new('WholeDenimCamera', bpy.data.cameras.new('WholeDenimCamera')); scene.collection.objects.link(camera)
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 1.17; scene.camera = camera
    report['photos'] = []
    for label, garment in [('mappedWholeJeans', target), ('originalSelectedWholeJeans', reference)]:
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, garment)
        body.hide_render = False; garment.hide_render = False; garment.hide_set(False)
        for view, position in [('front', (1.1, -3, .65)), ('back', (-1.1, 3, .65)), ('profile', (3, 0, .65))]:
            camera.location = position; helpers['aim'](camera, (0, 0, .58)); path = out / (label + '-' + view + '.png')
            scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
            report['photos'].append({'variant': label, 'view': view, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
            (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    intake_path, out = Path(args[0]).resolve(), Path(args[1]).resolve(); intake = json.loads(intake_path.read_text())
    assert not intake['accepted'] and intake['resolution'] == 4096 and not out.exists()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02/whole-correspondence02')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'authorSHA256': sha(__file__), 'intakeSHA256': sha(intake_path),
              'capture': [], 'regionalBakes': [], 'maps': {}, 'limits': intake['limits']}
    write = lambda: (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    try:
        paths = {key: pin(row) for key, row in intake['inputs'].items()}
        probe_intake = json.loads(paths['probeIntake'].read_text())
        for row in list(probe_intake['helpers'].values()) + list(probe_intake['maps'].values()): pin(row)
        old = runpy.run_path(str(paths['successfulAuthor'])); diag = runpy.run_path(str(paths['diagnosticSource']))
        helpers = runpy.run_path(str(pin(probe_intake['helpers']['pbr'])))
        local = runpy.run_path(str(pin(probe_intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(probe_intake['helpers']['originalAuthor'])))
        prior = json.loads(paths['successfulReport'].read_text())
        assert all(row['passed'] for row in prior['capture']) and prior['resultNative'] == intake['inputs']['native']
        bpy.ops.wm.open_mainfile(filepath=str(paths['native'])); assert list(bpy.app.version) == [5, 2, 1]
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton')]
        assert all(obj.matrix_world == Matrix.Identity(4) for obj in (target, source, body, rig))
        before = [helpers['shape'](obj, local) for obj in (target, source)]; body_before = original['signature'](body, rig)
        assert before == prior['wearingTargetSourceStateSHA256'] and body_before == prior['body75StateSHA256']
        maps = helpers['selected_maps'](source, probe_intake)
        assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
        assert target.get('productionJeansRecipe') == 'rockhop-native-local-gusset-v2'
        scene = bpy.context.scene; scene.frame_set(1); scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
        scene.cycles.samples = 1; scene.render.threads_mode, scene.render.threads = 'FIXED', 2
        pairs = []
        for label, prefix in [('pelvis-front', 'Front'), ('pelvis-rear', 'Rear')]:
            selected, proxy, cage, receiver = [bpy.data.objects[prefix + suffix] for suffix in
                ('OriginalSelectedSource', 'ProjectionReceiver', 'AuthoredCage', 'OriginalReceiverUVReference')]
            pairs.append((label, selected, proxy, cage, receiver))
        pelvis_before = [[helpers['shape'](obj, local) for obj in pair[1:]] for pair in pairs]
        lower_positions, editable, boundary_counts = lower_surfaces(target, intake, original, local, old, pairs)
        graph = bpy.context.evaluated_depsgraph_get()
        evaluated = source.copy(); evaluated.data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
        scene.collection.objects.link(evaluated)
        for modifier in list(evaluated.modifiers): evaluated.modifiers.remove(modifier)
        with np.load(paths['originalSourceLineage']) as arrays: expected = arrays['originalEvaluatedPositions']
        actual = np.asarray([tuple(v.co) for v in evaluated.data.vertices], dtype=np.float32)
        assert np.array_equal(actual, expected), 'Original source envelope array changed'
        reference = old['copy_object'](evaluated, 'OriginalSelectedWholeJeansReference')
        for side, sign in [('L', 1), ('R', -1)]:
            receiver = helpers['regional_copy'](target, side + 'LowerOriginalReceiverUVReference',
                lambda p, s=sign: p.z <= .84 and ((p.x >= 0) if s == 1 else (p.x < 0)))
            selected = helpers['regional_copy'](evaluated, side + 'LowerOriginalSelectedSource',
                lambda p, s=sign: p.z < .94 and p.x * s >= -intake['sourceCutOverlapMetres'])
            triangulate(receiver)
            proxy, cage = [old['copy_object'](receiver, side + 'Lower' + suffix) for suffix in ('ProjectionReceiver', 'AuthoredCage')]
            for obj, positions in zip((proxy, cage), lower_positions):
                lineage = obj.data.attributes['BakeOriginalVertex']
                for vertex in used(obj): obj.data.vertices[int(vertex)].co = positions[lineage.data[int(vertex)].value]
                obj.data.update(); obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
                obj['correspondenceOnly'] = True; obj['wearerFitAuthority'] = False
                assert local['topology'](obj.data) == local['topology'](receiver.data)
                assert local['uv_rows'](obj) == local['uv_rows'](receiver) and local['fields'](obj) == local['fields'](receiver)
            pairs.append(('lower-' + side, selected, proxy, cage, receiver))
        face_sets = [{d.value for d in pair[4].data.attributes['BakeOriginalFace'].data} for pair in pairs]
        assert sum(map(len, face_sets)) == len(set.union(*face_sets)) == len(target.data.polygons)
        assert set.union(*face_sets) == set(range(len(target.data.polygons)))
        data = evaluated.data; bpy.data.objects.remove(evaluated, do_unlink=True); bpy.data.meshes.remove(data)
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, target)
        body.hide_render = False; target.hide_render = False; target.hide_set(False)
        path = out / 'whole-correspondence-before-maps.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
        report.update(status='WHOLE_EDITABLE_NATIVE_SAVED_BEFORE_DIRECT_CAPTURE_AND_MAPS',
            authoredNative={'path': str(path.relative_to(ROOT)), 'sha256': sha(path)},
            wearingTargetSourceStateSHA256=before, body75StateSHA256=body_before,
            existingPelvisBoundaryVerticesPreserved=boundary_counts, originalSourceArrayExact=True,
            regionsPartitionEveryWearingFace=True, resolution=4096)
        write(); coverages = []; priorities = []
        for label, selected, proxy, cage, _ in pairs:
            result, coverage, priority = capture(label, selected, proxy, cage, diag, intake, out)
            report['capture'].append(result); coverages.append(coverage); priorities.append(priority); write()
        assert all(row['passed'] for row in report['capture']), 'Whole direct capture rejected; no maps admitted'
        owners, multiplicity = owners_with_native_priority(coverages, priorities, old)
        report['UVAtlas'] = {'coveredPixels': int((multiplicity > 0).sum()), 'overlapPixels': int((multiplicity > 1).sum()),
            'maximumMultiplicity': int(multiplicity.max()), 'policy': 'Original UV retained. Highest original face ID owns conflicts, matching ordinary last-face atlas writes. Raw regional maps and exact conflict mask persist; no UV/material acceptance inferred.'}
        np.savez_compressed(out / 'whole-atlas-ownership.npz', owners=owners, nativeUVSampleMultiplicity=multiplicity)
        material = source.data.materials[0].copy(); sn, sl = material.node_tree.nodes, material.node_tree.links
        output, principled = sn.get('Material Output'), sn.get('Principled BSDF'); emission = sn.new('ShaderNodeEmission')
        copied_maps = {label: sn[node.name] for label, node in maps.items()}
        for _, selected, _, _, _ in pairs:
            selected.data.materials.clear(); selected.data.materials.append(material)
        destination = bpy.data.materials.new('OriginalSelectedWholeJeansPBR4K'); destination.use_nodes = True
        dn, dl = destination.node_tree.nodes, destination.node_tree.links; image_node = dn.new('ShaderNodeTexImage'); dn.active = image_node
        for _, _, proxy, _, _ in pairs:
            proxy.data.materials.clear(); proxy.data.materials.append(destination)
        settings = scene.render.bake; settings.use_selected_to_active = True; settings.use_cage = True
        settings.cage_extrusion = .018; settings.max_ray_distance = 0; settings.margin = 16; settings.normal_space = 'TANGENT'
        report['actualBakeSettings'] = {'useCage': True, 'maximumRayMetres': 0, 'explicitSemanticCaptureGateMetres': intake['maximumCaptureMetres'], 'marginPixels': 16}
        baked = {}; size = intake['resolution']
        for label, kind in [('albedo', 'EMIT'), ('metallicRoughness', 'EMIT'), ('normal', 'NORMAL')]:
            if kind == 'EMIT':
                sl.new(copied_maps[label].outputs['Color'], emission.inputs['Color']); sl.new(emission.outputs[0], output.inputs['Surface'])
            else: sl.new(principled.outputs[0], output.inputs['Surface'])
            merged = np.zeros((size, size, 4), dtype=np.float32)
            for index, (region, selected, proxy, cage, _) in enumerate(pairs, 1):
                image = bpy.data.images.new('WholeSelected_' + region + '_' + label, width=size, height=size, alpha=True)
                image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'; image_node.image = image
                for obj in scene.objects:
                    if obj.type == 'MESH': obj.hide_render = obj not in (body, selected, proxy, cage)
                bpy.ops.object.select_all(action='DESELECT'); proxy.hide_set(False); selected.hide_set(False)
                proxy.select_set(True); selected.select_set(True); bpy.context.view_layer.objects.active = proxy
                settings.cage_object = cage; settings.use_clear = True; bpy.ops.object.bake(type=kind)
                path = out / (region + '-' + label + '.png'); image.filepath_raw, image.file_format = str(path), 'PNG'; image.save(); image.pack()
                pixels = diag['image_pixels'](image); chosen = owners == index; merged[chosen] = pixels[chosen]
                report['regionalBakes'].append({'region': region, 'map': label, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                    'coveredNearZeroRGB': int(((coverages[index - 1] > 0) & (np.max(np.abs(pixels[:, :, :3]), 2) < 1e-7)).sum())})
                write(); bpy.ops.wm.save_as_mainfile(filepath=str(out / 'partial-whole-selected.blend'))
            image = bpy.data.images.new('WholeSelectedCombined_' + label, width=size, height=size, alpha=True)
            image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'; image.pixels.foreach_set(merged.ravel()); image.update()
            path = out / (label + '.png'); image.filepath_raw, image.file_format = str(path), 'PNG'; image.save(); image.pack(); baked[label] = image
            report['maps'][label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': size,
                'coveredNearZeroRGB': int(((multiplicity > 0) & (np.max(np.abs(merged[:, :, :3]), 2) < 1e-7)).sum())}
            write()
        sl.new(principled.outputs[0], output.inputs['Surface'])
        target.data.materials.clear(); target.data.materials.append(destination)
        bs = dn.get('Principled BSDF'); image_node.image = baked['albedo']; dl.new(image_node.outputs['Color'], bs.inputs['Base Color'])
        mr = dn.new('ShaderNodeTexImage'); mr.image = baked['metallicRoughness']; split = dn.new('ShaderNodeSeparateColor')
        dl.new(mr.outputs[0], split.inputs[0]); dl.new(split.outputs['Green'], bs.inputs['Roughness']); dl.new(split.outputs['Blue'], bs.inputs['Metallic'])
        normal = dn.new('ShaderNodeTexImage'); normal.image = baked['normal']; convert = dn.new('ShaderNodeNormalMap')
        dl.new(normal.outputs[0], convert.inputs['Color']); dl.new(convert.outputs[0], bs.inputs['Normal'])
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before
        assert [[helpers['shape'](obj, local) for obj in pair[1:]] for pair in pairs[:2]] == pelvis_before
        helpers['selected_maps'](source, probe_intake)
        armature = [m for m in target.modifiers if m.type == 'ARMATURE']; assert len(armature) == 1 and armature[0].object == rig
        assert all(0 < sum(g.weight > 0 for g in v.groups) <= 4 for v in target.data.vertices)
        target['wholeSelectedPBRTransferUnaccepted'] = True
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, target)
        body.hide_render = False; target.hide_render = False
        path = out / 'whole-selected-jeans.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
        fields = out / 'production-jeans-fields.npz'; fields.write_bytes(paths['nativeFields'].read_bytes())
        native_row = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
        report.update(status='WHOLE_ACTUAL_SELECTED_PBR_NATIVE_SAVED_BEFORE_CONTEXT', resultNative=native_row,
            finishedGarment={'object': target.name, 'vertices': len(target.data.vertices), 'polygons': len(target.data.polygons),
                'stateSHA256': before[0], 'material': destination.name, 'packedMapSHA256': {k: v['sha256'] for k, v in report['maps'].items()},
                'modifier': {'name': armature[0].name, 'type': 'ARMATURE', 'target': rig.name, 'bones': len(rig.data.bones),
                    'preserveVolume': armature[0].use_deform_preserve_volume}, 'fields': {'path': str(fields.relative_to(ROOT)), 'sha256': sha(fields)}},
            wearingGeometryUVFullFourAnd75Exact=True, originalSelectedSourceGeometryUVMapsExact=True, workingPelvisGeometryExact=True,
            dressedContext=intake['dressedContext'])
        unit = {'part': 'Jeans', 'native': native_row, 'visible': [target.name],
            'reference': [source.name, reference.name], 'editingAids': [obj.name for obj in editable] + ['FrontAuthoredCage', 'RearAuthoredCage'],
            'expectedPBRHashes': [v['sha256'] for v in report['maps'].values()],
            'status': 'First whole selected4KPBR correspondence; actual parent art/fit/motion/device review pending'}
        (out / 'context-unit.json').write_text(json.dumps(unit, indent=2) + '\n'); write()
        matched_whole(scene, body, target, reference, out, report, helpers)
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before
        for row in intake['inputs'].values(): pin(row)
        report['status'] = 'ONE_WHOLE_SELECTED4K_CORRESPONDENCE_PARENT_REVIEW_PENDING'; write()
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_WHOLE_CORRESPONDENCE_NO_RETRY', error=repr(error), traceback=traceback.format_exc()); write()
        raise


if __name__ == '__main__': main()
