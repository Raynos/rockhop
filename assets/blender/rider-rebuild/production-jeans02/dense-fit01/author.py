"""One conventional OUTSIDE finish on a new evaluated selected-denim source.
No target rebuild, lattice edit, registration, material rewrite or bake.
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


def positions(mesh):
    result = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', result.ravel())
    return result


def triangles(mesh):
    mesh.calc_loop_triangles()
    result = np.empty((len(mesh.loop_triangles), 3), dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', result.ravel())
    return result


def uv_hash(mesh):
    h = hashlib.sha256()
    for layer in mesh.uv_layers:
        values = np.empty((len(layer.data), 2), dtype=np.float32)
        layer.data.foreach_get('uv', values.ravel())
        h.update(layer.name.encode()); h.update(values.tobytes())
    return h.hexdigest()


def topology(mesh):
    arrays = []
    for collection, name in [(mesh.loops, 'vertex_index'), (mesh.polygons, 'loop_start'), (mesh.polygons, 'loop_total')]:
        values = np.empty(len(collection), dtype=np.int32)
        collection.foreach_get(name, values)
        arrays.append(values)
    return hashlib.sha256(b''.join(a.tobytes() for a in arrays)).hexdigest()


def surface(mesh):
    return (sha_bytes(positions(mesh)), topology(mesh), uv_hash(mesh))


def sha_bytes(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def face_vectors(vertices, faces):
    return np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])


def topology_report(vertices, faces):
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    _, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
    net = np.bincount(inverse, weights=np.where(edges[:, 0] < edges[:, 1], 1, -1))
    vectors = face_vectors(vertices, faces)
    areas = np.linalg.norm(vectors, axis=1) / 2
    return {'boundaryEdges': int((counts == 1).sum()), 'nonmanifoldEdges': int((counts > 2).sum()),
            'sameWindingSharedEdges': int(((counts == 2) & (net != 0)).sum()),
            'minimumTriangleAreaM2': float(areas.min()), 'tinyTriangleCountBelow1e12M2': int((areas < 1e-12).sum()),
            'signedVolumeM3': float(np.einsum('ij,ij->i', vertices[faces[:, 0]], vectors).sum() / 6)}


def render(scene, body, donor, out, report, aim):
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('ActualSelectedDenseFitWorld'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .24, .28, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .55
    scene.world = world
    for label, location, energy in [('Key', (2, -3, 4), 650), ('Fill', (-3, -2, 2), 450), ('Rim', (0, 3, 3), 700)]:
        data = bpy.data.lights.new('DenseFit' + label, 'AREA'); data.energy, data.size = energy, 3
        light = bpy.data.objects.new(data.name, data); scene.collection.objects.link(light)
        light.location = location; aim(light, (0, 0, .65))
    camera = bpy.data.objects.new('ActualSelectedDenseFitCamera', bpy.data.cameras.new('ActualSelectedDenseFitCamera'))
    scene.collection.objects.link(camera); scene.camera = camera
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 1.2
    for obj in scene.objects:
        if obj.type == 'MESH': obj.hide_render = obj not in (body, donor)
    body.hide_render = False; donor.hide_render = False; donor.hide_set(False)
    report['photos'] = []
    for label, location in [('front', (1.1, -3, .9)), ('back', (-1.1, 3, .9)), ('profile', (3, 0, .9))]:
        camera.location = location; aim(camera)
        path = out / (label + '.png'); scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        report['photos'].append({'view': label, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    intake_path = Path(args[0]).resolve(); intake = json.loads(intake_path.read_text())
    out = Path(args[1]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-jeans02/dense-fit01')
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'PREFLIGHT', 'nativeInput': intake['native'],
              'authorSHA256': sha(__file__), 'intakeSHA256': sha(intake_path), 'photos': []}
    save_report = lambda: (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    donor = None
    try:
        assert intake['accepted'] is False and intake['offsetMetres'] == .012
        for row in [intake[k] for k in ('native', 'nativeFields', 'dense', 'bodyArrays', 'negativeInspection')] + list(intake['helpers'].values()) + list(intake['maps'].values()): pin(row)
        bpy.ops.wm.open_mainfile(filepath=str(pin(intake['native'])))
        target, source, body, rig = [bpy.data.objects[n] for n in ('RiderJeans', 'AlignedSelectedDenseJeans', 'RiderBody', 'RiderSkeleton')]
        assert target.get('productionJeansRecipe') == 'rockhop-native-local-gusset-v2'
        assert target.get('selectedAppearanceAuthority') == intake['dense']['sha256']
        assert all(obj.matrix_world == Matrix.Identity(4) for obj in (target, source, body, rig))
        assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75 and not body.hide_get() and not body.hide_render
        helpers = runpy.run_path(str(pin(intake['helpers']['pbr'])))
        local = runpy.run_path(str(pin(intake['helpers']['localAuthor'])))
        original = runpy.run_path(str(pin(intake['helpers']['originalAuthor'])))
        target_before = helpers['shape'](target, local); source_before = surface(source.data)
        body_before = original['signature'](body, rig)
        helpers['selected_maps'](source, intake)
        graph = bpy.context.evaluated_depsgraph_get()
        donor = source.copy(); donor.data = bpy.data.meshes.new_from_object(source.evaluated_get(graph), depsgraph=graph)
        donor.name = intake['derivativeObject']; bpy.context.scene.collection.objects.link(donor)
        for modifier in list(donor.modifiers): donor.modifiers.remove(modifier)
        assert topology(donor.data) == topology(source.data) and uv_hash(donor.data) == uv_hash(source.data)
        before = positions(donor.data); faces = triangles(donor.data)
        original_normals = np.empty((len(donor.data.corner_normals), 3), dtype=np.float32)
        donor.data.corner_normals.foreach_get('vector', original_normals.ravel())
        before_uv, before_topology = uv_hash(donor.data), topology(donor.data)
        report['evaluatedDonorTopology'] = topology_report(before, faces)
        body_mesh = bpy.data.meshes.new_from_object(body.evaluated_get(graph), depsgraph=graph)
        bv, bf = positions(body_mesh), triangles(body_mesh)
        report['actualBodyTopology'] = topology_report(bv, bf)
        for label in ('evaluatedDonorTopology', 'actualBodyTopology'):
            metrics = report[label]
            assert metrics['boundaryEdges'] == metrics['nonmanifoldEdges'] == metrics['sameWindingSharedEdges'] == 0, ('Unsafe topology', label, metrics)
            assert metrics['signedVolumeM3'] > 0, ('Inward winding', label)
        donor.hide_render = True; donor.hide_set(True)
        bpy.ops.wm.save_as_mainfile(filepath=str(out / 'evaluated-before-fit.blend'))
        scope = (before[:, 2] > intake['scopeZMetres'][0]) & (before[:, 2] < intake['scopeZMetres'][1])
        group = donor.vertex_groups.new(name='ActualBodyOutsideFinish')
        group.add(np.flatnonzero(scope).tolist(), 1.0, 'REPLACE')
        finish = donor.modifiers.new('One actual body OUTSIDE12mm finish', 'SHRINKWRAP')
        finish.target = body; finish.wrap_method = 'NEAREST_SURFACEPOINT'; finish.wrap_mode = 'OUTSIDE'
        finish.offset = intake['offsetMetres']; finish.vertex_group = group.name
        bpy.ops.object.select_all(action='DESELECT'); donor.hide_set(False); donor.select_set(True)
        bpy.context.view_layer.objects.active = donor
        bpy.ops.object.modifier_apply(modifier=finish.name)
        group = donor.vertex_groups.get('ActualBodyOutsideFinish'); assert group is not None
        donor.vertex_groups.remove(group)
        after = positions(donor.data); distances = np.linalg.norm(after - before, axis=1)
        changed = np.flatnonzero(distances > 1e-8)
        old_vectors, new_vectors = face_vectors(before, faces), face_vectors(after, faces)
        old_area, new_area = np.linalg.norm(old_vectors, axis=1) / 2, np.linalg.norm(new_vectors, axis=1) / 2
        meaningful = old_area > 1e-12
        collapsed = np.flatnonzero(meaningful & (new_area < np.maximum(1e-14, old_area * .01)))
        flipped = np.flatnonzero(meaningful & (new_area > 1e-12) & (np.einsum('ij,ij->i', old_vectors, new_vectors) < 0))
        tree = BVHTree.FromPolygons([Vector(p) for p in bv], bf.tolist(), all_triangles=True)
        gaps, normal_signs, loose_moved = [], [], []
        for i in changed:
            hit, normal, _, old_distance = tree.find_nearest(Vector(before[i]))
            old_sign = (Vector(before[i]) - hit).dot(normal)
            if old_sign > 0 and old_distance > intake['offsetMetres'] + 1e-5: loose_moved.append(int(i))
            hit, normal, _, distance = tree.find_nearest(Vector(after[i]))
            gaps.append(distance); normal_signs.append((Vector(after[i]) - hit).dot(normal))
        report.update(changedVertices=len(changed), eligibleVertices=int(scope.sum()),
                      maximumDisplacementMetres=float(distances.max()), newlyCollapsedTriangleIds=collapsed.tolist(),
                      faceNormalRotationsOver90DegreesIds=flipped.tolist(), looseOutsideVerticesMoved=loose_moved,
                      appliedPointNearestBodyGapMetres={'minimum': min(gaps) if gaps else None, 'median': float(np.median(gaps)) if gaps else None, 'maximum': max(gaps) if gaps else None},
                      appliedPointsNegativeNearestNormal=int(np.count_nonzero(np.asarray(normal_signs) < -1e-6)))
        # Original normals are retained in lineage. Zero custom vectors request
        # Blender's automatic normals from the edited actual geometry.
        donor.data.normals_split_custom_set_from_vertices([(0., 0., 0.)] * len(donor.data.vertices))
        donor.data.update()
        derived_normals = np.empty((len(donor.data.corner_normals), 3), dtype=np.float32)
        donor.data.corner_normals.foreach_get('vector', derived_normals.ravel())
        donor['selectedAppearanceAuthority'] = intake['dense']['sha256']
        donor['denseFitStatus'] = 'UNACCEPTED_ONE_OUTSIDE_FINISH'
        donor['derivedNormalsPolicy'] = 'Automatic normals from edited geometry; original evaluated normals retained in lineage NPZ'
        donor.hide_render = True; donor.hide_set(True)
        saved = out / 'selected-dense-fitted.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(saved))
        report['native'] = {'path': str(saved.relative_to(ROOT)), 'sha256': sha(saved)}
        np.savez_compressed(out / 'dense-fit-lineage.npz', originalEvaluatedPositions=before, fittedPositions=after,
                            originalEvaluatedCornerNormals=original_normals, derivedCornerNormals=derived_normals,
                            eligibleVertexMask=scope, displacementMetres=distances)
        report['lineage'] = {'path': str((out / 'dense-fit-lineage.npz').relative_to(ROOT)), 'sha256': sha(out / 'dense-fit-lineage.npz')}
        assert np.array_equal(before[~scope], after[~scope]), 'Protected aperture/end bands moved'
        assert report['maximumDisplacementMetres'] <= intake['maximumLocalChangeMetres'], 'Local-change guard exceeded'
        assert not len(collapsed) and not len(flipped) and not loose_moved, 'Outside operation is unsafe on this actual region'
        assert not report['appliedPointsNegativeNearestNormal'], 'Nearest-normal sign is unsafe after finish'
        assert not gaps or min(gaps) >= intake['offsetMetres'] - intake['gapToleranceMetres'], '12mm ease not retained against actual body'
        assert uv_hash(donor.data) == before_uv and topology(donor.data) == before_topology
        assert helpers['shape'](target, local) == target_before and surface(source.data) == source_before
        assert original['signature'](body, rig) == body_before
        helpers['selected_maps'](source, intake); helpers['selected_maps'](donor, intake)
        report.update(status='NATIVE_SAVED_BEFORE_ORIGINAL_PBR_MATCHED_REVIEW',
                      originalCanonicalDonorExact=True, targetGeometryUVFullFourExact=True, bodyAnd75RestUntouched=True,
                      donorUVTopologyOriginalMapsExact=True, protectedEndBandsExact=True, automaticNormalsRecomputed=True)
        save_report()
        scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
        scene.render.threads_mode, scene.render.threads = 'FIXED', 2
        render(scene, body, donor, out, report, helpers['aim'])
        report['status'] = 'ACTUAL_ORIGINAL_PBR_DONOR_VIEWS_SAVED_PARENT_REVIEW_PENDING'
        assert helpers['shape'](target, local) == target_before and original['signature'](body, rig) == body_before
        assert surface(source.data) == source_before and sha(pin(intake['native'])) == intake['native']['sha256']
        save_report()
        bpy.data.meshes.remove(body_mesh)
    except BaseException as error:
        report.update(status='FAILED_ACTUAL_DENSE_FINISH_NO_BAKE', error=repr(error), traceback=traceback.format_exc())
        save_report()
        raise


if __name__ == '__main__': main()
