"""One authored projection proxy/cage, direct capture gate, pelvis PBR probe.
The wearing target and original selected sculpture/PBR remain unchanged.
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


def authored_points(points, controls, key):
    """Bilinear interpolation of forty frozen artist controls, no fit solver."""
    rows = controls['rows']; heights = np.asarray([r['targetZ'] for r in rows])
    z = np.clip(points[:, 2], heights[0], heights[-1])
    width = np.interp(z, heights, [r['targetReferenceWidth'] for r in rows])
    centre = controls['centreY']; y = points[:, 1] - centre
    front = centre - np.interp(z, heights, [r['targetReferenceFrontY'] for r in rows])
    rear = np.interp(z, heights, [r['targetReferenceRearY'] for r in rows]) - centre
    theta = np.mod(np.arctan2(-y / np.where(y <= 0, front, rear), points[:, 0] / width), 2 * np.pi)
    angular = theta / (np.pi / 4)
    a0 = np.floor(angular).astype(int) % 8; a1 = (a0 + 1) % 8
    u = (angular - np.floor(angular))[:, None]
    r0 = np.clip(np.searchsorted(heights, z, side='right') - 1, 0, len(rows) - 2)
    r1 = r0 + 1; v = ((z - heights[r0]) / (heights[r1] - heights[r0]))[:, None]
    grid = np.asarray([r[key] for r in rows])
    lower = grid[r0, a0] * (1 - u) + grid[r0, a1] * u
    upper = grid[r1, a0] * (1 - u) + grid[r1, a1] * u
    return (lower * (1 - v) + upper * v).astype(np.float32)


def copy_object(obj, name):
    result = obj.copy(); result.data = obj.data.copy(); result.name = name
    bpy.context.scene.collection.objects.link(result)
    return result


def make_proxy(receiver, controls, name):
    proxy = copy_object(receiver, name + 'ProjectionReceiver')
    cage = copy_object(receiver, name + 'AuthoredCage')
    used = np.unique(np.concatenate([tuple(p.vertices) for p in receiver.data.polygons]))
    original = np.asarray([tuple(receiver.data.vertices[int(i)].co) for i in used], dtype=np.float32)
    for obj, key in [(proxy, 'proxyPoints'), (cage, 'cagePoints')]:
        authored = authored_points(original, controls, key)
        for vertex, point in zip(used, authored):
            obj.data.vertices[int(vertex)].co = point
        obj.data.update()
        # The proxy geometry changed: inherited wearer corner normals are stale.
        # Zero custom normals request honest normals derived from this geometry.
        obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
        obj['correspondenceOnly'] = True; obj['wearerFitAuthority'] = False
    return proxy, cage


def capture(region, source, receiver, cage, controls, diag, out):
    low, high, shell = [diag['mesh_arrays'](obj) for obj in (receiver, source, cage)]
    assert np.array_equal(low['triangles'], shell['triangles']), 'Proxy/cage tessellation changed'
    assert np.array_equal(low['uv'], shell['uv']), 'Proxy/cage UV changed'
    size = controls['captureGate']['resolution']
    coverage, owner, weights, boundary, degenerate = diag['raster'](low, size)
    assert degenerate == 0 and coverage.max() <= 1
    pixels = np.flatnonzero(owner >= 0); triangles = owner[pixels]; bary = weights[pixels]
    vertices = low['triangles'][triangles]
    points = np.einsum('ij,ijk->ik', bary, low['vertices'][vertices])
    origins = np.einsum('ij,ijk->ik', bary, shell['vertices'][vertices])
    directions = points - origins; length = np.linalg.norm(directions, axis=1)
    assert np.all(length > 1e-6), 'Zero cage ray'
    directions /= length[:, None]
    tree = BVHTree.FromPolygons(high['vertices'].tolist(), high['triangles'].tolist(), all_triangles=True, epsilon=0)
    hit_ids = np.full(len(pixels), -1, dtype=np.int32)
    hit_distances = np.full(len(pixels), np.nan, dtype=np.float32)
    hit_points = np.full_like(points, np.nan)
    for i, (origin, direction) in enumerate(zip(origins, directions)):
        location, _, triangle, distance = tree.ray_cast(Vector(origin), Vector(direction))
        if triangle is not None:
            hit_ids[i], hit_distances[i], hit_points[i] = triangle, distance, location
    found = hit_ids >= 0; centre = controls['isolation']['planeY']
    overlap = controls['isolation']['sourceCutOverlapMetres']
    opposite = found & ((hit_points[:, 1] > centre + overlap) if region == 'front' else
                        (hit_points[:, 1] < centre - overlap))
    wrong_side = found & (np.abs(points[:, 0]) > .005) & (points[:, 0] * hit_points[:, 0] < 0)
    far = found & (hit_distances > controls['captureGate']['maximumFirstHitMetres'])
    uv = np.full((len(pixels), 2), np.nan, dtype=np.float32)
    tris = high['vertices'][high['triangles'][hit_ids[found]]]
    a, b, d = tris[:, 0] - tris[:, 2], tris[:, 1] - tris[:, 2], hit_points[found] - tris[:, 2]
    aa, ab, bb = np.sum(a * a, 1), np.sum(a * b, 1), np.sum(b * b, 1)
    ad, bd = np.sum(a * d, 1), np.sum(b * d, 1)
    determinant = aa * bb - ab * ab; assert np.all(determinant > 0)
    u, v = (ad * bb - bd * ab) / determinant, (bd * aa - ad * ab) / determinant
    uv[found] = np.einsum('ij,ijk->ik', np.column_stack((u, v, 1 - u - v)), high['uv'][hit_ids[found]])
    source_faces = np.asarray([d.value for d in source.data.attributes['BakeOriginalFace'].data])
    hit_original_faces = np.full(len(pixels), -1, dtype=np.int32)
    hit_original_faces[found] = source_faces[high['faces'][hit_ids[found]]]
    path = out / (region + '-direct-capture.npz')
    np.savez_compressed(path, pixelIds=pixels, proxyPoint=points, cageOrigin=origins, rayDirection=directions,
                        firstHitMetres=hit_distances, sourcePoint=hit_points, sourceUV=uv,
                        originalSourceFace=hit_original_faces, noHit=~found, oppositeHalf=opposite,
                        wrongPocketSide=wrong_side, excessiveDistance=far, boundarySample=boundary[pixels],
                        targetUVCoverage=coverage.reshape(size, size))
    result = {'region': region, 'coveredSamples': len(pixels), 'noHit': int((~found).sum()),
              'oppositePhysicalHalf': int(opposite.sum()), 'wrongPocketSide': int(wrong_side.sum()),
              'excessiveDistance': int(far.sum()), 'firstHitMetres': diag['statistics'](hit_distances),
              'boundarySamples': int(boundary[pixels].sum()), 'arrayPath': str(path.relative_to(ROOT)),
              'arraySHA256': sha(path), 'passed': not np.any(~found | opposite | wrong_side | far)}
    return result, coverage.reshape(size, size)


def composite_owners(coverages, margin):
    """Choose actual region pixels/margins; never fill a covered miss synthetically."""
    owners = np.zeros_like(coverages[0], dtype=np.uint8)
    for index, coverage in enumerate(coverages, 1):
        assert not np.any((owners > 0) & (coverage > 0)), 'Regional UV ownership overlap'
        owners[coverage > 0] = index
    for _ in range(margin):
        previous = owners.copy()
        for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            shifted = np.roll(previous, (dy, dx), (0, 1))
            if dy == 1: shifted[0] = 0
            if dy == -1: shifted[-1] = 0
            if dx == 1: shifted[:, 0] = 0
            if dx == -1: shifted[:, -1] = 0
            eligible = (owners == 0) & (shifted > 0); owners[eligible] = shifted[eligible]
    return owners


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    intake_path, out = Path(args[0]).resolve(), Path(args[1]).resolve()
    intake = json.loads(intake_path.read_text()); assert not intake['accepted'] and not out.exists()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02/correspondence-probe01')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'authorSHA256': sha(__file__),
              'intakeSHA256': sha(intake_path), 'controls': intake['controls'], 'capture': [], 'regionalBakes': [],
              'maps': {}, 'limits': intake['limits']}
    write = lambda: (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    try:
        paths = {key: pin(row) for key, row in intake['inputs'].items()}
        controls = json.loads(pin(intake['controls']).read_text())
        original_intake = json.loads(paths['probeIntake'].read_text())
        for row in list(original_intake['maps'].values()) + list(original_intake['helpers'].values()): pin(row)
        with np.load(pin(controls['envelopeMethod']['originalEvaluatedArray'])) as arrays:
            original_evaluated = arrays['originalEvaluatedPositions'].copy()
        assert hashlib.sha256(original_evaluated.tobytes()).hexdigest() == controls['envelopeMethod']['arraySHA256']
        bpy.ops.wm.open_mainfile(filepath=str(paths['native']))
        assert list(bpy.app.version) == [5, 2, 1]
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton')]
        assert target.get('productionJeansRecipe') == 'rockhop-native-local-gusset-v2'
        assert target.get('selectedAppearanceAuthority') == original_intake['dense']['sha256']
        assert all(obj.matrix_world == Matrix.Identity(4) for obj in (target, source, body, rig))
        helpers = runpy.run_path(str(pin(original_intake['helpers']['pbr'])))
        local = runpy.run_path(str(pin(original_intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(original_intake['helpers']['originalAuthor'])))
        diag = runpy.run_path(str(paths['diagnosticSource']))
        view_helpers = runpy.run_path(str(paths['probeSource']))
        before = [helpers['shape'](obj, local) for obj in (target, source)]
        body_before = original['signature'](body, rig)
        maps = helpers['selected_maps'](source, original_intake)
        assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75 and not body.hide_render and not body.hide_get()
        scene = bpy.context.scene; scene.frame_set(1); scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
        scene.cycles.samples = 1; scene.render.threads_mode, scene.render.threads = 'FIXED', 2
        graph = bpy.context.evaluated_depsgraph_get()
        evaluated = source.copy(); evaluated.data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
        scene.collection.objects.link(evaluated)
        for modifier in list(evaluated.modifiers): evaluated.modifiers.remove(modifier)
        actual_points = np.asarray([tuple(v.co) for v in evaluated.data.vertices], dtype=np.float32)
        assert np.array_equal(actual_points, original_evaluated), 'Original pre-edit source envelope lineage changed'
        reference = helpers['regional_copy'](evaluated, 'OriginalSelectedPelvisReference', lambda p: p.z > .80)
        wearing = helpers['regional_copy'](target, 'MappedAuthoredCorrespondencePelvis', lambda p: p.z > .84)
        pairs = []; centre = controls['isolation']['planeY']; overlap = controls['isolation']['sourceCutOverlapMetres']
        for region in ('front', 'rear'):
            keep_target = lambda p, r=region: p.z > .84 and ((p.y <= centre) if r == 'front' else (p.y > centre))
            keep_source = lambda p, r=region: p.z > .80 and ((p.y <= centre + overlap) if r == 'front' else (p.y >= centre - overlap))
            receiver = helpers['regional_copy'](target, region.title() + 'OriginalReceiverUVReference', keep_target)
            selected = helpers['regional_copy'](evaluated, region.title() + 'OriginalSelectedSource', keep_source)
            # Explicitly triangulate this correspondence-only derivative ONCE
            # before either shape edit. Blender otherwise chooses quad/ngon
            # diagonals from each edited geometry independently, breaking cage
            # corner pairing even with identical polygon vertex order/UVs.
            bpy.ops.object.select_all(action='DESELECT')
            receiver.hide_set(False); receiver.select_set(True)
            bpy.context.view_layer.objects.active = receiver
            triangulate = receiver.modifiers.new('FrozenPairedCorrespondenceTriangles', 'TRIANGULATE')
            triangulate.quad_method = 'FIXED'; triangulate.ngon_method = 'CLIP'
            bpy.ops.object.modifier_apply(modifier=triangulate.name)
            assert all(len(p.vertices) == 3 for p in receiver.data.polygons)
            proxy, cage = make_proxy(receiver, controls, region.title())
            proxy['authoredCorrespondenceControls'] = json.dumps(controls['rows'])
            cage['authoredCorrespondenceControls'] = json.dumps(controls['rows'])
            cage['originalSourceEnvelopeArraySHA256'] = controls['envelopeMethod']['arraySHA256']
            assert local['topology'](proxy.data) == local['topology'](cage.data) == local['topology'](receiver.data)
            assert local['uv_rows'](proxy) == local['uv_rows'](cage) == local['uv_rows'](receiver)
            assert local['fields'](proxy) == local['fields'](cage) == local['fields'](receiver)
            pairs.append((region, selected, proxy, cage, receiver))
        face_ids = lambda obj: {d.value for d in obj.data.attributes['BakeOriginalFace'].data}
        assert not (face_ids(pairs[0][4]) & face_ids(pairs[1][4]))
        assert face_ids(pairs[0][4]) | face_ids(pairs[1][4]) == face_ids(wearing)
        data = evaluated.data; bpy.data.objects.remove(evaluated, do_unlink=True); bpy.data.meshes.remove(data)
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, wearing)
        native = out / 'authored-correspondence.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(native))
        report.update(status='EDITABLE_PROXY_CAGE_SAVED_BEFORE_CAPTURE_AND_MAPS',
            authoredNative={'path': str(native.relative_to(ROOT)), 'sha256': sha(native)},
            originalEvaluatedSourceArrayExact=True, wearingTargetSourceStateSHA256=before,
            body75StateSHA256=body_before, normalPolicy='Proxy/cage custom normals reset to geometry-derived automatic normals; original selected source normals unchanged')
        write()
        coverages = []
        for region, selected, proxy, cage, _ in pairs:
            result, coverage = capture(region, selected, proxy, cage, controls, diag, out)
            report['capture'].append(result); coverages.append(coverage); write()
        assert all(row['passed'] for row in report['capture']), 'Direct authored cage capture rejected; no bake allowed'
        owners = composite_owners(coverages, 16)
        material = source.data.materials[0].copy(); sn, sl = material.node_tree.nodes, material.node_tree.links
        output, principled = sn.get('Material Output'), sn.get('Principled BSDF')
        emission = sn.new('ShaderNodeEmission'); copied_maps = {label: sn[node.name] for label, node in maps.items()}
        for _, selected, _, _, _ in pairs:
            selected.data.materials.clear(); selected.data.materials.append(material)
        destination = bpy.data.materials.new('AuthoredCorrespondenceActualSelectedPBR'); destination.use_nodes = True
        dn, dl = destination.node_tree.nodes, destination.node_tree.links
        image_node = dn.new('ShaderNodeTexImage'); dn.active = image_node
        for _, _, proxy, _, _ in pairs:
            proxy.data.materials.clear(); proxy.data.materials.append(destination)
        settings = scene.render.bake; settings.use_selected_to_active = True; settings.use_cage = True
        settings.cage_extrusion = .018; settings.max_ray_distance = 0; settings.margin = 16; settings.normal_space = 'TANGENT'
        report['actualBakeSettings'] = {'useSelectedToActive': True, 'useCage': True, 'maximumRayMetres': 0,
            'retainedExtrusionMetresIgnoredByExplicitCage': float(settings.cage_extrusion),
            'guardedFirstHitMaximumMetres': controls['captureGate']['maximumFirstHitMetres'], 'marginPixels': 16,
            'maximumMeaning': 'Explicit custom cage with no distance cutoff; direct semantic/first-hit gate already passed'}
        baked = {}; size = controls['captureGate']['resolution']
        for label, kind in [('albedo', 'EMIT'), ('metallicRoughness', 'EMIT'), ('normal', 'NORMAL')]:
            if kind == 'EMIT':
                sl.new(copied_maps[label].outputs['Color'], emission.inputs['Color']); sl.new(emission.outputs[0], output.inputs['Surface'])
            else: sl.new(principled.outputs[0], output.inputs['Surface'])
            merged = np.zeros((size, size, 4), dtype=np.float32)
            for index, (region, selected, proxy, cage, _) in enumerate(pairs, 1):
                image = bpy.data.images.new('AuthoredCage_' + region + '_' + label, width=size, height=size, alpha=True)
                image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'; image_node.image = image
                for obj in scene.objects:
                    if obj.type == 'MESH': obj.hide_render = obj not in (body, selected, proxy, cage)
                bpy.ops.object.select_all(action='DESELECT'); proxy.hide_set(False); selected.hide_set(False)
                proxy.select_set(True); selected.select_set(True); bpy.context.view_layer.objects.active = proxy
                settings.cage_object = cage; settings.use_clear = True
                bpy.ops.object.bake(type=kind)
                path = out / (region + '-' + label + '.png'); image.filepath_raw, image.file_format = str(path), 'PNG'; image.save(); image.pack()
                pixels = diag['image_pixels'](image); chosen = owners == index; merged[chosen] = pixels[chosen]
                report['regionalBakes'].append({'region': region, 'map': label, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                    'coveredNearZeroRGB': int(((coverages[index - 1] > 0) & (np.max(np.abs(pixels[:, :, :3]), axis=2) < 1e-7)).sum())})
                write(); bpy.ops.wm.save_as_mainfile(filepath=str(out / 'partial-authored-probe.blend'))
            image = bpy.data.images.new('AuthoredCageCombined_' + label, width=size, height=size, alpha=True)
            image.colorspace_settings.name = 'sRGB' if label == 'albedo' else 'Non-Color'; image.pixels.foreach_set(merged.ravel()); image.update()
            path = out / (label + '.png'); image.filepath_raw, image.file_format = str(path), 'PNG'; image.save(); image.pack(); baked[label] = image
            report['maps'][label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'size': size,
                'coveredNearZeroRGB': int(((sum(coverages) > 0) & (np.max(np.abs(merged[:, :, :3]), axis=2) < 1e-7)).sum()),
                'composite': 'Exact receiver UV ownership plus16pixel domain dilation selects actual regional baked pixels; no fabricated covered texels'}
            write()
        sl.new(principled.outputs[0], output.inputs['Surface'])
        wearing.data.materials.clear(); wearing.data.materials.append(destination)
        bs = dn.get('Principled BSDF'); image_node.image = baked['albedo']; dl.new(image_node.outputs['Color'], bs.inputs['Base Color'])
        mr = dn.new('ShaderNodeTexImage'); mr.image = baked['metallicRoughness']; split = dn.new('ShaderNodeSeparateColor')
        dl.new(mr.outputs[0], split.inputs[0]); dl.new(split.outputs['Green'], bs.inputs['Roughness']); dl.new(split.outputs['Blue'], bs.inputs['Metallic'])
        normal = dn.new('ShaderNodeTexImage'); normal.image = baked['normal']; convert = dn.new('ShaderNodeNormalMap')
        dl.new(normal.outputs[0], convert.inputs['Color']); dl.new(convert.outputs[0], bs.inputs['Normal'])
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before; helpers['selected_maps'](source, original_intake)
        for obj in scene.objects:
            if obj.type == 'MESH': obj.hide_render = obj not in (body, wearing)
        body.hide_render = False; wearing.hide_render = False
        path = out / 'mapped-authored-pelvis.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(path))
        report.update(status='ACTUAL_AUTHORED_PELVIS_PROBE_SAVED_BEFORE_VIEWS', resultNative={'path': str(path.relative_to(ROOT)), 'sha256': sha(path)},
                      wearingTargetGeometryUVFullFourExact=True, originalSelectedSourceGeometryUVMapsExact=True, body75RestExact=True)
        write(); view_helpers['matched_views'](scene, body, wearing, reference, out, report, helpers)
        assert [helpers['shape'](obj, local) for obj in (target, source)] == before
        assert original['signature'](body, rig) == body_before
        for row in intake['inputs'].values(): pin(row)
        report['status'] = 'ONE_AUTHORED_PELVIS_CORRESPONDENCE_PROBE_PARENT_REVIEW_PENDING'; write()
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_AUTHORED_CORRESPONDENCE_NO_RETRY', error=repr(error), traceback=traceback.format_exc()); write()
        raise


if __name__ == '__main__':
    main()
