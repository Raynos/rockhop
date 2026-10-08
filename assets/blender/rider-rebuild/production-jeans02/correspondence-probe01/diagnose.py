"""Read-only directed correspondence measurement of the actual rejected probe.
No bake, render, source edit, cage construction, changed ray setting or retry.
"""
import hashlib
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[5]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    path = ROOT / row['path']
    assert path.is_file() and sha(path) == row['sha256'], ('Changed input', row)
    return path


def mesh_arrays(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = np.asarray([tuple(v.co) for v in mesh.vertices], dtype=np.float32)
    vertex_normals = np.asarray([tuple(v.normal) for v in mesh.vertices], dtype=np.float32)
    triangles = np.asarray([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    loops = np.asarray([tuple(t.loops) for t in mesh.loop_triangles], dtype=np.int32)
    faces = np.asarray([t.polygon_index for t in mesh.loop_triangles], dtype=np.int32)
    uv = np.asarray([tuple(d.uv) for d in mesh.uv_layers.active.data], dtype=np.float32)[loops]
    smooth = np.asarray([mesh.polygons[int(f)].use_smooth for f in faces])
    face_normals = np.asarray([tuple(mesh.polygons[int(f)].normal) for f in faces], dtype=np.float32)
    return dict(vertices=vertices, normals=vertex_normals, triangles=triangles,
                uv=uv, faces=faces, smooth=smooth, faceNormals=face_normals)


def raster(data, size, keep_owner=True):
    """Interior pixel samples, Blender's UV offset and last-triangle ownership.
    This is explicit barycentric rasterization, not Blender's zspan scan converter.
    Boundary samples are marked; no claim of byte-identical backend rasterization.
    """
    count = np.zeros(size * size, dtype=np.uint16)
    owner = np.full(size * size, -1, dtype=np.int32) if keep_owner else None
    weights = np.zeros((size * size, 3), dtype=np.float32) if keep_owner else None
    boundary = np.zeros(size * size, dtype=bool) if keep_owner else None
    degenerate = 0
    for index, triangle_uv in enumerate(data['uv']):
        xy = triangle_uv * np.float32(size) - np.asarray([.501, .502], dtype=np.float32)
        lo = np.maximum(np.ceil(xy.min(axis=0)).astype(int), 0)
        hi = np.minimum(np.floor(xy.max(axis=0)).astype(int), size - 1)
        if np.any(lo > hi):
            continue
        a, b = (xy[0] - xy[2]).astype(np.float64), (xy[1] - xy[2]).astype(np.float64)
        determinant = a[0] * b[1] - a[1] * b[0]
        if abs(determinant) < 1e-12:
            degenerate += 1
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        x, y = xx.ravel() - xy[2, 0], yy.ravel() - xy[2, 1]
        u, v = (x * b[1] - y * b[0]) / determinant, (a[0] * y - a[1] * x) / determinant
        bary = np.column_stack((u, v, 1 - u - v))
        valid = np.all(bary >= 0, axis=1)
        pixels = yy.ravel()[valid] * size + xx.ravel()[valid]
        count[pixels] += 1
        if keep_owner:
            owner[pixels], weights[pixels] = index, bary[valid]
            boundary[pixels] = bary[valid].min(axis=1) < 1e-5
    return count, owner, weights, boundary, degenerate


LABELS = ['front-waist', 'front-fly-centre', 'front-left-panel', 'front-right-panel',
          'rear-waist', 'rear-seat-centre', 'rear-left-panel', 'rear-right-panel',
          'left-side-panel', 'right-side-panel']


def labels(points, normals):
    result = np.where(points[:, 0] >= 0, 8, 9)
    front = normals[:, 1] < -np.abs(normals[:, 0])
    rear = normals[:, 1] > np.abs(normals[:, 0])
    waist, centre = points[:, 2] >= 1.02, np.abs(points[:, 0]) <= .045
    result[front] = np.where(waist[front], 0, np.where(centre[front], 1,
        np.where(points[front, 0] >= 0, 2, 3)))
    result[rear] = np.where(waist[rear], 4, np.where(centre[rear], 5,
        np.where(points[rear, 0] >= 0, 6, 7)))
    return result.astype(np.int16)


def image_pixels(image):
    result = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(result)
    return result.reshape(int(image.size[1]), int(image.size[0]), 4)


def bilinear_repeat(pixels, uv):
    height, width = pixels.shape[:2]
    xy = uv * [width, height] - .5
    lo = np.floor(xy).astype(np.int64)
    fraction = xy - lo
    x, y, fx, fy = lo[:, 0], lo[:, 1], fraction[:, 0:1], fraction[:, 1:2]
    return ((1 - fy) * ((1 - fx) * pixels[y % height, x % width] +
            fx * pixels[y % height, (x + 1) % width]) +
            fy * ((1 - fx) * pixels[(y + 1) % height, x % width] +
            fx * pixels[(y + 1) % height, (x + 1) % width])).astype(np.float32)


def statistics(values):
    values = values[np.isfinite(values)]
    return None if not len(values) else dict(zip(('min', 'median', 'p95', 'max'),
        [float(v) for v in np.percentile(values, [0, 50, 95, 100])]))


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 2
    intake_path, out = Path(args[0]).resolve(), Path(args[1]).resolve()
    intake = json.loads(intake_path.read_text())
    assert intake['accepted'] is False and not out.exists()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02/correspondence-probe01')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'diagnosticSHA256': sha(__file__),
              'intakeSHA256': sha(intake_path), 'inputs': intake['inputs'], 'limitations': intake['limitations']}
    write = lambda: (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    try:
        paths = {name: pin(row) for name, row in intake['inputs'].items()}
        probe_intake = json.loads(paths['probeIntake'].read_text())
        for row in list(probe_intake['helpers'].values()) + list(probe_intake['maps'].values()):
            pin(row)
        actual = json.loads(paths['actualProbeReport'].read_text())
        assert actual['resultNative'] == intake['inputs']['actualProbeNative']
        assert actual['native'] == probe_intake['native'] == intake['inputs']['constructionNative']
        for photo in actual['photos']:
            pin(photo)
        bpy.ops.wm.open_mainfile(filepath=str(paths['actualProbeNative']))
        assert list(bpy.app.version) == intake['blenderVersion'], bpy.app.version_string
        target, source, body, rig, receiver, selected = [bpy.data.objects[name] for name in
            ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton',
             'MappedPelvisCorrespondenceProbe', 'OriginalSelectedPelvisProbe')]
        helpers = runpy.run_path(str(pin(probe_intake['helpers']['pbr'])))
        local = runpy.run_path(str(pin(probe_intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(probe_intake['helpers']['originalAuthor'])))
        before = [helpers['shape'](obj, local) for obj in (target, source, receiver, selected)]
        body_before = original['signature'](body, rig)
        assert before[:2] == [actual['targetStateSHA256'], actual['originalSourceStateSHA256']]
        assert body_before == actual['body75StateSHA256']
        maps = helpers['selected_maps'](source, probe_intake)
        assert maps['albedo'].extension == 'REPEAT' and not maps['albedo'].inputs['Vector'].is_linked
        settings = bpy.context.scene.render.bake
        assert settings.use_selected_to_active and not settings.use_cage and not settings.cage_object
        extrusion, maximum = float(settings.cage_extrusion), float(settings.max_ray_distance)
        assert abs(extrusion - .018) < 1e-8 and abs(maximum - .045) < 1e-8
        assert len(selected.data.polygons) == actual['sourceFaces'] == 222598
        assert len(receiver.data.polygons) == actual['receiverFaces'] == 7008
        report.update(status='READ_ONLY_RASTER_AND_DIRECTED_RAYS', blenderVersion=bpy.app.version_string,
                      actualRaySettings={'extrusionMetres': extrusion, 'maximumMetres': maximum, 'useCage': False})
        write()
        low, high, full = [mesh_arrays(obj) for obj in (receiver, selected, target)]
        size = intake['resolution']
        coverage, owner, bary_all, boundary, degenerate = raster(low, size)
        full_coverage, _, _, _, full_degenerate = raster(full, size, False)
        pixel_ids = np.flatnonzero(owner >= 0)
        triangles, bary = owner[pixel_ids], bary_all[pixel_ids]
        vertex_ids = low['triangles'][triangles]
        points_local = np.einsum('ij,ijk->ik', bary, low['vertices'][vertex_ids])
        normals_local = np.einsum('ij,ijk->ik', bary, low['normals'][vertex_ids])
        normals_local[~low['smooth'][triangles]] = low['faceNormals'][triangles[~low['smooth'][triangles]]]
        lengths = np.linalg.norm(normals_local, axis=1)
        assert np.all(lengths > 1e-8), 'Zero receiver ray normal'
        normals_local /= lengths[:, None]
        matrix = np.asarray(receiver.matrix_world, dtype=np.float64)
        normal_matrix = np.linalg.inv(matrix[:3, :3]).T
        points = points_local @ matrix[:3, :3].T + matrix[:3, 3]
        origins = (points_local + extrusion * normals_local) @ matrix[:3, :3].T + matrix[:3, 3]
        normals = normals_local @ normal_matrix.T
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        directions = -normals
        high_matrix = np.asarray(selected.matrix_world, dtype=np.float64)
        high_vertices = high['vertices'] @ high_matrix[:3, :3].T + high_matrix[:3, 3]
        tree = BVHTree.FromPolygons(high_vertices.tolist(), high['triangles'].tolist(), all_triangles=True, epsilon=0)
        # Blender itself first finds the nearest directed intersection, then applies
        # the unchanged strict maximum-distance test. No longer bake is attempted.
        count = len(pixel_ids)
        hit_triangle = np.full(count, -1, dtype=np.int32)
        hit_distance = np.full(count, np.nan, dtype=np.float32)
        hit_points = np.full((count, 3), np.nan, dtype=np.float32)
        hit_normals = np.full((count, 3), np.nan, dtype=np.float32)
        for index, (origin, direction) in enumerate(zip(origins, directions)):
            location, normal, triangle, distance = tree.ray_cast(Vector(origin), Vector(direction))
            if triangle is not None:
                hit_triangle[index], hit_distance[index] = triangle, distance
                hit_points[index], hit_normals[index] = location, normal
        found = hit_triangle >= 0
        bounded = found & (hit_distance < maximum)
        status = np.where(bounded, 1, np.where(found, 2, 3)).astype(np.uint8)
        nearest_distance = np.full(count, np.nan, dtype=np.float32)
        nearest_ray_cosine = np.full(count, np.nan, dtype=np.float32)
        nearest_outward_offset = np.full(count, np.nan, dtype=np.float32)
        for index in np.flatnonzero(~bounded):
            location, _, _, distance = tree.find_nearest(Vector(points[index]))
            if location is not None:
                delta = np.asarray(location) - points[index]
                nearest_distance[index] = distance
                nearest_outward_offset[index] = np.dot(delta, normals[index])
                vector = np.asarray(location) - origins[index]
                length = np.linalg.norm(vector)
                if length > 1e-12:
                    nearest_ray_cosine[index] = np.dot(vector / length, directions[index])
        source_uv = np.full((count, 2), np.nan, dtype=np.float32)
        high_triangles = high_vertices[high['triangles'][hit_triangle[found]]]
        a, b = high_triangles[:, 0] - high_triangles[:, 2], high_triangles[:, 1] - high_triangles[:, 2]
        delta = hit_points[found] - high_triangles[:, 2]
        aa, ab, bb = np.sum(a * a, axis=1), np.sum(a * b, axis=1), np.sum(b * b, axis=1)
        ad, bd = np.sum(a * delta, axis=1), np.sum(b * delta, axis=1)
        denominator = aa * bb - ab * ab
        assert np.all(denominator > 0), 'Degenerate source hit triangle'
        u, v = (ad * bb - bd * ab) / denominator, (bd * aa - ad * ab) / denominator
        source_bary = np.column_stack((u, v, 1 - u - v))
        source_uv[found] = np.einsum('ij,ijk->ik', source_bary, high['uv'][hit_triangle[found]])
        actual_atlases = {}
        for label in ('albedo', 'metallicRoughness', 'normal'):
            image = bpy.data.images['PelvisProbe_' + label]
            assert list(image.size) == [size, size]
            assert image.packed_file and hashlib.sha256(image.packed_file.data).hexdigest() == actual['maps'][label]['sha256']
            actual_atlases[label] = image_pixels(image).reshape(-1, 4)
        actual_pixels = {label: pixels[pixel_ids] for label, pixels in actual_atlases.items()}
        actual_black = np.max(np.abs(actual_pixels['albedo'][:, :3]), axis=1) < 1e-7
        actual_transparent = actual_pixels['albedo'][:, 3] < .5
        original_rgb = np.full((count, 4), np.nan, dtype=np.float32)
        original_rgb[found] = bilinear_repeat(image_pixels(maps['albedo'].image), source_uv[found])
        original_black = np.max(np.abs(original_rgb[:, :3]), axis=1) < 1e-7
        panel = labels(points, normals)
        source_panel = np.full(count, -1, dtype=np.int16)
        source_panel[found] = labels(hit_points[found], hit_normals[found])
        facing_dot = np.sum(normals * hit_normals, axis=1)
        changed = np.asarray(json.loads(target['local_gusset_changed_vertex_ids']), dtype=np.int32)
        lineage = np.asarray([v.value for v in receiver.data.attributes['BakeOriginalVertex'].data], dtype=np.int32)
        gusset_weight = np.sum(bary * np.isin(lineage[vertex_ids], changed), axis=1)
        original_source_faces = np.asarray([v.value for v in selected.data.attributes['BakeOriginalFace'].data])
        source_face = np.full(count, -1, dtype=np.int32)
        source_face[found] = original_source_faces[high['faces'][hit_triangle[found]]]
        mask = np.zeros(size * size, dtype=np.uint8)
        mask[pixel_ids] = status
        samples_path = out / 'directed-correspondence.npz'
        np.savez_compressed(samples_path, pixelIds=pixel_ids, receiverTriangle=triangles,
            receiverOriginalFace=np.asarray([d.value for d in receiver.data.attributes['BakeOriginalFace'].data])[low['faces'][triangles]],
            receiverBarycentric=bary, targetPoint=points, rayOrigin=origins, rayDirection=directions,
            panel=panel, newGussetSupportWeight=gusset_weight, sourceTriangle=hit_triangle,
            sourceOriginalFace=source_face, sourcePoint=hit_points, sourcePanel=source_panel,
            sourceUV=source_uv, firstDirectedHitMetres=hit_distance, correspondingNormalsDot=facing_dot,
            nearestSourceMetresOnMiss=nearest_distance, nearestSourceRayCosineOnMiss=nearest_ray_cosine,
            nearestSourceOutwardOffsetOnMiss=nearest_outward_offset, originalAlbedoBilinearRepeat=original_rgb,
            actualAlbedo=actual_pixels['albedo'], actualMR=actual_pixels['metallicRoughness'],
            actualNormal=actual_pixels['normal'], statusMask=mask.reshape(size, size),
            actualRawBlackAtlas=(np.max(np.abs(actual_atlases['albedo'][:, :3]), axis=1) < 1e-7).reshape(size, size),
            actualRawAlphaBelowHalfAtlas=(actual_atlases['albedo'][:, 3] < .5).reshape(size, size),
            regionalUVSampleMultiplicity=coverage.reshape(size, size), fullTargetUVSampleMultiplicity=full_coverage.reshape(size, size),
            rasterBoundarySample=boundary.reshape(size, size))
        rows = []
        for label, selection in [(name, panel == index) for index, name in enumerate(LABELS)] + [
                ('all-pelvis', np.ones(count, dtype=bool)), ('new-gusset-support', gusset_weight > 0),
                ('outside-new-gusset', gusset_weight == 0)]:
            rows.append({'panel': label, 'samples': int(selection.sum()),
                'boundedHits': int((selection & bounded).sum()),
                'directedHitsBeyondMaximum': int((selection & (status == 2)).sum()),
                'noDirectedIntersection': int((selection & (status == 3)).sum()),
                'actualBlack': int((selection & actual_black).sum()),
                'actualTransparent': int((selection & actual_transparent).sum()),
                'blackAndPredictedMiss': int((selection & actual_black & ~bounded).sum()),
                'blackDespitePredictedHit': int((selection & actual_black & bounded).sum()),
                'nonblackDespitePredictedMiss': int((selection & ~actual_black & ~bounded).sum()),
                'boundedHitOriginalAlbedoBlack': int((selection & bounded & original_black).sum()),
                'opposedSourceNormalOnBoundedHit': int((selection & bounded & (facing_dot < 0)).sum()),
                'frontReceiverHitRearSource': int((selection & bounded & (panel <= 3) & (source_panel >= 4) & (source_panel <= 7)).sum()),
                'rearReceiverHitFrontSource': int((selection & bounded & (panel >= 4) & (panel <= 7) & (source_panel >= 0) & (source_panel <= 3)).sum()),
                'regionalUVOverlap': int((selection & (coverage[pixel_ids] > 1)).sum()),
                'firstDirectedHitMetres': statistics(hit_distance[selection]),
                'nearestSourceMetresOnMiss': statistics(nearest_distance[selection]),
                'nearestSourceOutwardOffsetOnMiss': statistics(nearest_outward_offset[selection]),
                'nearestSourceRayCosineOnMiss': statistics(nearest_ray_cosine[selection])})
        assert [helpers['shape'](obj, local) for obj in (target, source, receiver, selected)] == before
        assert original['signature'](body, rig) == body_before
        helpers['selected_maps'](source, probe_intake)
        for row in intake['inputs'].values():
            pin(row)
        report.update(status='READ_ONLY_CORRESPONDENCE_MEASURED_PARENT_REVIEW_PENDING',
            samples={'path': str(samples_path.relative_to(ROOT)), 'sha256': sha(samples_path)},
            statusMaskLegend={'0': 'outside regional receiver UV sample coverage', '1': 'first directed hit within unchanged maximum',
                              '2': 'first directed hit beyond/equal unchanged maximum', '3': 'no intersection along directed ray'},
            panels=LABELS, panelDefinition=intake['panelDefinition'], summaries=rows,
            receiverUV={'coveredPixels': len(pixel_ids), 'overlapPixels': int((coverage > 1).sum()),
                'maximumMultiplicity': int(coverage.max()), 'boundarySamples': int(boundary[pixel_ids].sum()),
                'degenerateTriangles': degenerate, 'fullTargetCoveredPixels': int((full_coverage > 0).sum()),
                'fullTargetOverlapPixels': int((full_coverage > 1).sum()), 'fullTargetDegenerateTriangles': full_degenerate},
            canonicalTargetSourceRegionalCopiesExact=True, body75Exact=True, allInputFilesSHA256Exact=True,
            bakeCalls=0, renderCalls=0, savedNativeCalls=0, changedRaySettings=0,
            correction='No cage/correspondence change authored or admitted. Parent reviews actual measurements first.')
        write()
    except BaseException as error:
        report.update(status='FAILED_READ_ONLY_DIAGNOSTIC_NO_RETRY', error=repr(error), traceback=traceback.format_exc())
        write()
        raise


if __name__ == '__main__':
    main()
