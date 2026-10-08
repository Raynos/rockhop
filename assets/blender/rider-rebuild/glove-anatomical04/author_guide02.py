"""Selected coarse-guide sculpt in source units, then dense Surface Deform.

Parent CPU2 only. Save each solved guide BEFORE dense transfer or native75 bind.
No source-envelope fit, fitting rays, bake or replacement appearance mesh.
"""
import contextlib
import ctypes
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@contextlib.contextmanager
def modifier_log(path):
    """Capture actual Blender C-level modifier errors, including solver warnings."""
    sys.stdout.flush(); sys.stderr.flush()
    libc = ctypes.CDLL(None)
    libc.fflush(None)
    old = [os.dup(1), os.dup(2)]
    try:
        with path.open('wb') as stream:
            os.dup2(stream.fileno(), 1); os.dup2(stream.fileno(), 2)
            try:
                yield
            finally:
                sys.stdout.flush(); sys.stderr.flush(); libc.fflush(None)
    finally:
        os.dup2(old[0], 1); os.dup2(old[1], 2)
        os.close(old[0]); os.close(old[1])
    messages = path.read_text(errors='replace')
    rejected = ('did not find a solution', 'bind failed', 'target contains', 'error:')
    assert not any(text in messages.lower() for text in rejected), ('Actual modifier error', str(path), messages)


def mesh_object(name, points, faces, corner_uv, materials, matrix):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points.tolist(), [], faces.tolist())
    mesh.update()
    if corner_uv is not None:
        uv = mesh.uv_layers.new(name='OriginalSelectedCornerUV')
        uv.data.foreach_set('uv', corner_uv.astype(np.float32).ravel())
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    for material in materials:
        mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.matrix_world = matrix
    return obj


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_viewport = False; obj.hide_set(False); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def evaluated_mesh(obj):
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    return bpy.data.meshes.new_from_object(obj.evaluated_get(graph),
                                         preserve_all_data_layers=True, depsgraph=graph)


def points(mesh):
    value = np.empty((len(mesh.vertices), 3), dtype=np.float64)
    mesh.vertices.foreach_get('co', value.ravel())
    return value


def positive_cotangent_geometry(vertices, faces):
    magnitude = np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                        vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
    active_triangles = magnitude > np.finfo(np.float32).eps
    incidents = np.zeros(len(vertices), dtype=np.int32)
    np.add.at(incidents, faces[active_triangles].ravel(), 1)
    assert active_triangles.all() and np.all(incidents > 0), 'Guide violates Blender cotangent area gate'
    return {'trianglesSuppressed': 0, 'verticesWithZeroActiveTriangles': 0,
            'minimumTriangleCrossMagnitudeSourceUnits': float(magnitude.min())}


def check_error(modifier):
    value = getattr(modifier, 'error', None)
    assert not value, ('Exposed modifier error', modifier.name, value)
    return {'modifierErrorRNAExposed': value is not None,
            'modifierErrorRNA': value,
            'actualCLevelModifierLogChecked': True}


def author(side, control, frozen, guide_arrays, dense, native, core, out, rig):
    negative = bpy.data.objects['Gloves__SelectedFittedSource.' + side]
    placement = control['hands'][side]['initialPlacement']
    linear, translation = np.asarray(placement['linear']), np.asarray(placement['translation'])
    transform = np.eye(4); transform[:3, :3] = linear; transform[:3, 3] = translation
    matrix = Matrix(transform.tolist())
    reflected = placement['reflectionFromSelectedSource']
    guide_points, guide_faces = guide_arrays['vertices'].astype(np.float32), guide_arrays['faces'].copy()
    dense_faces, dense_uv = dense['faces'].copy(), dense['originalCornerUV'].copy()
    if reflected:
        guide_faces = guide_faces[:, ::-1]; dense_faces = dense_faces[:, ::-1]; dense_uv = dense_uv[:, ::-1]
    dense_uv[:, :, 1] = 1 - dense_uv[:, :, 1]
    guide_uv = guide_arrays['uv'][guide_faces].copy(); guide_uv[:, :, 1] = 1 - guide_uv[:, :, 1]
    pre_gate = positive_cotangent_geometry(guide_points, guide_faces)
    guide = mesh_object('Gloves__SelectedGuideSculpt.' + side, guide_points, guide_faces,
                        guide_uv, negative.data.materials, matrix)
    guide['role'] = 'COARSE_SELECTED_MODELING_GUIDE_ONLY_NOT_FINAL_APPEARANCE'
    handles = frozen['hands'][side]['handles']
    ids = [h['guideVertex'] for h in handles]
    assert len(ids) == len(set(ids)) == 303
    group = guide.vertex_groups.new(name='Explicit303AnatomicalHandles')
    group.add(ids, 1., 'REPLACE')
    laplace = guide.modifiers.new('SelectedGuideSourceUnitLaplacian', 'LAPLACIANDEFORM')
    laplace.vertex_group = group.name; laplace.iterations = control['laplacianIterations']
    active(guide)
    log = out / ('guide-modifier-' + side + '.log')
    with modifier_log(log):
        bpy.ops.object.laplaciandeform_bind(modifier=laplace.name)
        assert laplace.is_bind
        for handle in handles:
            guide.data.vertices[handle['guideVertex']].co = handle['targetOriginalSourceFrame']
        guide.data.update()
        solved_mesh = evaluated_mesh(guide)
        guide_error = check_error(laplace)
    solved = points(solved_mesh)
    assert np.isfinite(solved).all()
    mask = np.ones(len(solved), dtype=bool); mask[ids] = False
    displacement = np.linalg.norm(solved - guide_points, axis=1)
    # With failed solve Blender returns unchanged nonanchors. This direct check
    # measures the behavior that is_bind and moved anchor residual cannot prove.
    moved = displacement[mask] > np.finfo(np.float32).eps
    assert moved.any(), 'No actual nonanchor guide movement; solve failed'
    expected = np.asarray([h['targetOriginalSourceFrame'] for h in handles])
    stats = {'guideObject': guide.name, 'sourceUnits': True, 'vertexCount': len(solved),
             'acceptedArt': False, 'status': 'SOLVED_GUIDE_SAVED_POSTDEFORMATION_GATE_PENDING',
             'distinctAnchorOwnership': True, 'anchorCount': len(ids),
             'nonanchorCount': int(mask.sum()), 'movedNonanchorCount': int(moved.sum()),
             'nonanchorDisplacementRMS': float(np.sqrt(np.mean(displacement[mask] ** 2))),
             'maximumAnchorResidualSourceUnits': float(np.linalg.norm(solved[ids] - expected, axis=1).max()),
             'anchorResidualIsReportOnly': True,
             'beforeCotangentGate': pre_gate, 'afterCotangentGate': None,
             'modifierDiagnostics': guide_error, 'modifierLogSHA256': sha(log)}
    negative.hide_render = True; negative.hide_set(True)
    guide_native = out / ('guide-sculpt-' + side + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(guide_native), compress=True)
    stats['nativeSavedBeforeDenseTransferOrRig'] = {'path': str(guide_native.relative_to(ROOT)), 'sha256': sha(guide_native)}
    receipt = out / ('guide-checkpoint-' + side + '.json')
    receipt.write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps({'savedActualGuide': side, 'nonanchorMovementRMS': stats['nonanchorDisplacementRMS']}), flush=True)
    # Preserve the actual solved guide even if its postdeformation area gate
    # fails. Dense transfer and rigging remain forbidden until this passes.
    try:
        stats['afterCotangentGate'] = positive_cotangent_geometry(solved, guide_faces)
    except AssertionError as error:
        stats['status'] = 'SOLVED_GUIDE_SAVED_POSTDEFORMATION_GATE_FAILED_NO_DENSE_TRANSFER'
        stats['postdeformationGateError'] = str(error)
        receipt.write_text(json.dumps(stats, indent=2) + '\n')
        raise
    stats['status'] = 'SOLVED_GUIDE_SAVED_POSTDEFORMATION_GATE_PASSED_FIT_UNACCEPTED'
    receipt.write_text(json.dumps(stats, indent=2) + '\n')
    driver = mesh_object('Gloves__SelectedGuideTransferDriver.' + side, guide_points, guide_faces,
                         guide_uv, negative.data.materials, matrix)
    source = mesh_object('Gloves__UntouchedSelectedDenseTransfer.' + side, dense['vertices'], dense_faces,
                         dense_uv, negative.data.materials, matrix)
    transfer = source.modifiers.new('ActualSelectedDenseSurfaceDeform', 'SURFACE_DEFORM')
    transfer.target = driver
    active(source)
    log = out / ('dense-transfer-' + side + '.log')
    with modifier_log(log):
        bpy.ops.object.surfacedeform_bind(modifier=transfer.name)
        assert transfer.is_bound, 'Dense selected Surface Deform did not bind'
        driver.data.vertices.foreach_set('co', solved.astype(np.float32).ravel()); driver.data.update()
        mesh = evaluated_mesh(source)
        transfer_error = check_error(transfer)
    assert core['uv_bytes'](mesh) == dense_uv.astype(np.float32).reshape(-1, 2).tobytes()
    assert len(mesh.vertices) == len(dense['vertices']) and len(mesh.polygons) == len(dense_faces)
    result_faces = np.empty((len(mesh.polygons), 3), dtype=np.int32)
    mesh.polygons.foreach_get('vertices', result_faces.ravel())
    assert np.array_equal(result_faces, dense_faces)
    transferred = points(mesh)
    assert np.isfinite(transferred).all()
    dense_move = np.linalg.norm(transferred - dense['vertices'], axis=1)
    assert np.any(dense_move > np.finfo(np.float32).eps), 'Dense source did not follow solved selected guide'
    # Convert once after both modeling modifiers succeeded. Reflection already
    # reversed face AND matching UV-corner order; no normal replacement shader.
    world = transferred @ linear.T + translation
    mesh.vertices.foreach_set('co', world.astype(np.float32).ravel()); mesh.update()
    result = bpy.data.objects.new('Gloves__AnatomicallySculptedSelected.' + side, mesh)
    bpy.context.collection.objects.link(result)
    result['acceptedArt'] = False; result['originalSelectedUVAndMaterialAncestry'] = True
    binding = core['bind_native'](result, dense['vertices'], native,
                                   np.load(ROOT / control['pins']['hand' + side]['path']), control, side, rig)
    for aid in (guide, driver, source):
        aid.hide_render = True; aid.hide_set(True)
    return {'object': result.name, 'guide': stats, 'vertexCount': len(world),
            'triangleCount': len(dense_faces), 'reflectionFromSelectedSource': reflected,
            'faceAndUVCornerWindingReversedTogether': reflected,
            'originalSelectedUVAndFaceAncestry': True, 'denseTransferModifierDiagnostics': transfer_error,
            'denseTransferLogSHA256': sha(log), 'denseSourceFrameDisplacementRMS': float(np.sqrt(np.mean(dense_move ** 2))),
            'bounds': [world.min(0).tolist(), world.max(0).tolist()], 'binding': binding}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]; assert len(args) == 2
    frozen_path, out = (Path(x).resolve() for x in args)
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/glove-anatomical04')
    frozen = json.loads(frozen_path.read_text()); assert frozen['acceptedArt'] is False
    for key in ('sourceControls', 'selectedGuide', 'previousAuthorHelpers'):
        row = frozen[key]; assert sha(ROOT / row['path']) == row['sha256']
    control = json.loads((ROOT / frozen['sourceControls']['path']).read_text())
    for row in control['pins'].values(): assert sha(ROOT / row['path']) == row['sha256']
    core = runpy.run_path(str(ROOT / frozen['previousAuthorHelpers']['path']))
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / control['pins']['native']['path']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before = core['signature'](body, rig)
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    out.mkdir(parents=True)
    guide = np.load(ROOT / frozen['selectedGuide']['path'])
    dense, native = (np.load(ROOT / control['pins'][k]['path']) for k in ('denseSelected', 'nativeArrays'))
    report = {'acceptedArt': False, 'operation': 'SELECTED_COARSE_GUIDE_AND_DENSE_SURFACEDEFORM',
              'controlsSHA256': frozen['sourceControls']['sha256'], 'guideControlsSHA256': sha(frozen_path),
              'recipeSHA256': sha(__file__), 'bodyAndMasterBefore': before, 'hands': {},
              'bakesExecuted': 0, 'newPlayerAssets': 0,
              'limits': ['Saved geometry and actual modifier checks are not wearing fit or art acceptance.',
                         'Parent must inspect actual PBR before any moving/grip review.']}
    for side in ('R', 'L'):
        report['hands'][side] = author(side, control, frozen, guide, dense, native, core, out, rig)
        assert core['signature'](body, rig) == before
        path = out / 'editable-selected-bilateral-gloves.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
        report['native'] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}
        (out / ('checkpoint-' + side + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    report['bodyAndMasterAfter'] = core['signature'](body, rig)
    report['status'] = 'BILATERAL_SELECTED_SCULPT_SAVED_BEFORE_PARENT_PBR_REVIEW'
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
