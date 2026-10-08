"""One conventional selected-surface sculpt, frozen for parent CPU2 execution.

Laplacian Deform retains the selected surface's differential detail while
explicit mesh handles tailor its palm, digits, webs and cuff. No fitting rays,
independent segment transforms, donor surface projection or bake is used.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def signature(body, rig):
    h = hashlib.sha256()
    for vertex in body.data.vertices:
        h.update(struct.pack('<3f', *vertex.co))
        for group in vertex.groups:
            h.update(struct.pack('<If', group.group, group.weight))
    for polygon in body.data.polygons:
        h.update(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
    for bone in rig.data.bones:
        h.update(bone.name.encode())
        h.update(struct.pack('<16f', *(x for row in bone.matrix_local for x in row)))
    return h.hexdigest()


def uv_bytes(mesh):
    uv = np.empty((len(mesh.loops), 2), dtype=np.float32)
    mesh.uv_layers.active.data.foreach_get('uv', uv.ravel())
    return uv.tobytes()


def vertices(mesh):
    points = np.empty((len(mesh.vertices), 3), dtype=np.float64)
    mesh.vertices.foreach_get('co', points.ravel())
    return points


def hand_domain(source, controls, side):
    """Anatomical candidate restrictions for weight transfer, not deformation.

    Distal source fingers are separated in their original selected rest shape.
    Their narrow candidates exclude every neighboring finger. Web/thenar points
    remain in the broad hand domain; cuff points use the actual forearm surface.
    """
    labels = np.full(len(source), -1, dtype=np.int16)
    distances = np.full((len(source), 5), np.inf)
    for digit_id, digit in enumerate(DIGITS):
        path = np.asarray(controls['sourceRest']['digits'][digit], dtype=float)
        for head, tail in zip(path[:-1], path[1:]):
            axis = tail - head
            u = np.clip((source - head) @ axis / np.dot(axis, axis), 0, 1)
            d = np.linalg.norm(source - head - u[:, None] * axis, axis=1)
            distances[:, digit_id] = np.minimum(distances[:, digit_id], d)
        # Below these deliberately authored proximal boundaries the palm/web
        # must retain mixed native hand fields rather than a nearest digit.
        if digit == 'thumb':
            eligible = (source[:, 0] > .27) & (source[:, 1] > -.36)
        else:
            eligible = source[:, 1] > path[0, 1] + .075
        distances[~eligible, digit_id] = np.inf
    nearest = np.argmin(distances, axis=1)
    finite = np.isfinite(distances[np.arange(len(source)), nearest])
    labels[finite] = nearest[finite]
    labels[source[:, 1] < -.52] = -2
    # Explicit saved web handles define proximal mixed domains. A nearest
    # centerline must never turn a shared web into one isolated finger field.
    for web_id, (first, second) in enumerate(zip(DIGITS[:-1], DIGITS[1:])):
        prefix = f'web/{first}_{second}/'
        witnesses = np.asarray([h['sourceRest'] for h in controls['hands'][side]['handles']
                                if h['label'].startswith(prefix)])
        lower = witnesses[:, :2].min(0) - [.045, .065]
        upper = witnesses[:, :2].max(0) + [.045, .065]
        inside = ((source[:, :2] > lower) & (source[:, :2] < upper)).all(1)
        labels[inside & (source[:, 1] > -.52)] = 5 + web_id
    witnesses = np.asarray([h['sourceRest'] for h in controls['hands'][side]['handles']
                            if h['label'].startswith('thenar/')])
    lower = witnesses[:, :2].min(0) - [.07, .08]
    upper = witnesses[:, :2].max(0) + [.07, .08]
    inside = ((source[:, :2] > lower) & (source[:, :2] < upper)).all(1)
    labels[inside & (source[:, 1] > -.52)] = 9
    return labels


def barycentric(point, triangle):
    a, b, c = triangle
    e, f, q = b - a, c - a, point - a
    ee, ef, ff = np.dot(e, e), np.dot(e, f), np.dot(f, f)
    denominator = ee * ff - ef * ef
    assert denominator > 1e-20
    v = (ff * np.dot(q, e) - ef * np.dot(q, f)) / denominator
    w = (ee * np.dot(q, f) - ef * np.dot(q, e)) / denominator
    result = np.maximum([1 - v - w, v, w], 0)
    return result / sum(result)


def bind_native(obj, source, body_arrays, hand, controls, side, rig):
    """Interpolate actual wearer triangle fields within anatomical domains.

    Source semantic domains restrict candidate wearer triangles. Distal thumb
    candidates include all three real CMC/MCP/IP controls; no second hand rig.
    This is ordinary rig-field transfer after the selected sculpt is frozen.
    """
    names = body_arrays['jointNames'].tolist()
    lookup = {name: i for i, name in enumerate(names)}
    body_v, body_f, body_w = (body_arrays[k] for k in
                              ('vertices', 'faces', 'nativeCoefficients'))
    hand_v, hand_f, hand_w = (hand[k] for k in
                              ('vertices', 'faces', 'nativeCoefficients'))
    domains = {}
    for digit_id, digit in enumerate(DIGITS):
        stem = 'thumb' if digit == 'thumb' else 'f_' + digit
        indices = [lookup[f'DEF-{stem}.{segment:02d}.{side}'] for segment in (1, 2, 3)]
        mass = hand_w[:, indices].sum(1)
        kept = np.flatnonzero(mass[hand_f].mean(1) > .20)
        assert len(kept) >= 20, (side, digit, len(kept))
        allowed = indices
        domains[digit_id] = (hand_v, hand_f[kept], hand_w, allowed)
    hand_indices = [i for i, name in enumerate(names) if name.endswith('.' + side)
                    and (name.startswith('DEF-hand') or name.startswith('DEF-palm'))]
    mass = hand_w[:, hand_indices].sum(1)
    kept = np.flatnonzero(mass[hand_f].mean(1) > .20)
    # Palm/web triangles retain the native smooth fields, including neighboring
    # proximal digit influences already deliberately authored on the real hand.
    allowed_hand = [i for i, name in enumerate(names) if name.endswith('.' + side)
                    and any(name.startswith(prefix) for prefix in
                            ('DEF-hand', 'DEF-palm', 'DEF-f_', 'DEF-thumb', 'DEF-forearm'))]
    domains[-1] = (hand_v, hand_f[kept], hand_w, allowed_hand)
    for web_id, (first, second) in enumerate(zip(DIGITS[:-1], DIGITS[1:])):
        prefix = f'web/{first}_{second}/'
        witnesses = np.asarray([h['targetWorld'] for h in controls['hands'][side]['handles']
                                if h['label'].startswith(prefix)])
        center = witnesses.mean(0)
        pair = []
        for digit in (first, second):
            stem = 'thumb' if digit == 'thumb' else 'f_' + digit
            pair.append([lookup[f'DEF-{stem}.{i:02d}.{side}'] for i in (1, 2, 3)])
        a, b = (hand_w[:, indices].sum(1) for indices in pair)
        near = np.linalg.norm(hand_v[hand_f].mean(1) - center, axis=1) < .045
        kept = np.flatnonzero(near & (a[hand_f].mean(1) > .01) & (b[hand_f].mean(1) > .01))
        assert len(kept) >= 10, ('Missing adjacent-digit web donor', side, first, second)
        domains[5 + web_id] = (hand_v, hand_f[kept], hand_w,
                               hand_indices + pair[0] + pair[1])
    thumb = [lookup[f'DEF-thumb.{i:02d}.{side}'] for i in (1, 2, 3)]
    thenar_center = body_arrays['jointHeads'][lookup['DEF-thumb.01.' + side]]
    near = np.linalg.norm(hand_v[hand_f].mean(1) - thenar_center, axis=1) < .07
    thumb_mass = hand_w[:, thumb].sum(1)
    kept = np.flatnonzero(near & (thumb_mass[hand_f].mean(1) > .01)
                         & (mass[hand_f].mean(1) > .025))
    assert len(kept) >= 10, ('Missing actual thenar donor', side)
    domains[9] = (hand_v, hand_f[kept], hand_w, hand_indices + thumb)
    forearm = [lookup['DEF-forearm.' + side], lookup['DEF-forearm.' + side + '.001']]
    wrist = body_arrays['jointHeads'][lookup['DEF-hand.' + side]]
    near = np.linalg.norm(body_v - wrist, axis=1) < .13
    mass = body_w[:, forearm + hand_indices].sum(1)
    kept = np.flatnonzero(near[body_f].all(1) & (mass[body_f].mean(1) > .5))
    domains[-2] = (body_v, body_f[kept], body_w, forearm + hand_indices)
    trees = {key: BVHTree.FromPolygons(v.tolist(), f.tolist(), all_triangles=True)
             for key, (v, f, _, _) in domains.items()}
    labels = hand_domain(source, controls, side)
    weights = np.zeros((len(source), 75), dtype=np.float32)
    maximum_distance = 0.
    for vertex_id, point in enumerate(vertices(obj.data)):
        label = int(labels[vertex_id])
        v, f, w, allowed = domains[label]
        location, _, row, distance = trees[label].find_nearest(Vector(point))
        assert row is not None, ('No native weight candidate', side, vertex_id, label)
        bary = barycentric(np.asarray(location), v[f[row]])
        value = bary @ w[f[row]][:, allowed]
        assert value.sum() > 1e-10
        weights[vertex_id, allowed] = value / value.sum()
        maximum_distance = max(maximum_distance, distance)
    obj.vertex_groups.clear()
    for j, name in enumerate(names):
        group = obj.vertex_groups.new(name=name)
        for i in np.flatnonzero(weights[:, j] > 0):
            group.add([int(i)], float(weights[i, j]), 'REPLACE')
    modifier = obj.modifiers.new('OnlySharedNative75', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    return {'sharedRig': rig.name, 'jointNames': names,
            'normalizedWeightMaximumResidual': float(np.max(abs(weights.sum(1) - 1))),
            'candidateDomainCounts': {str(k): int(np.count_nonzero(labels == k)) for k in domains},
            'webCandidateDomains': {str(5 + i): first + '/' + second
                                   for i, (first, second) in enumerate(zip(DIGITS[:-1], DIGITS[1:]))},
            'thenarCandidateDomain': 9,
            'maximumNativeTransferDistanceMeters': float(maximum_distance),
            'thumbControls': [f'DEF-thumb.{i:02d}.{side}' for i in (1, 2, 3)],
            'limits': ['Weight transfer is unqualified until bilateral moving grip/release review.']}


def sculpt(side, controls, dense, body_arrays, hand, rig):
    rejected = bpy.data.objects['Gloves__SelectedFittedSource.' + side]
    assert rejected.matrix_world.is_identity and not rejected.modifiers
    original = dense['vertices'].astype(np.float64)
    initial = controls['hands'][side]['initialPlacement']
    initial_points = original @ np.asarray(initial['linear']).T + np.asarray(initial['translation'])
    assert len(initial_points) == len(rejected.data.vertices)
    faces = dense['faces'].copy()
    corner_uv = dense['originalCornerUV'].copy()
    if initial['reflectionFromSelectedSource']:
        faces = faces[:, ::-1]
        corner_uv = corner_uv[:, ::-1]
    corner_uv[:, :, 1] = 1 - corner_uv[:, :, 1]
    expected_uv = corner_uv.astype(np.float32).reshape(-1, 2).tobytes()
    working = rejected.copy()
    # Reconstruct only corner ordering from the original selected source.
    # Canonical MCP curl shows R needs reflection and L does not. Reusing the
    # rejected pair's opposite winding would invert the newly assigned surfaces.
    mesh = bpy.data.meshes.new('AnatomicallyAssignedSelectedSource.' + side)
    mesh.from_pydata(initial_points.tolist(), [], faces.tolist())
    mesh.update()
    uv = mesh.uv_layers.new(name='OriginalSelectedCornerUV')
    uv.data.foreach_set('uv', corner_uv.astype(np.float32).ravel())
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    for material in rejected.data.materials:
        mesh.materials.append(material)
    working.data = mesh
    bpy.context.collection.objects.link(working)
    working.name = 'Gloves__EditableSelectedLaplacianSculpt.' + side
    working.vertex_groups.clear()
    anchors = working.vertex_groups.new(name='ExplicitAnatomicalSculptHandles')
    handles = controls['hands'][side]['handles']
    indices = [handle['sourceVertex'] for handle in handles]
    assert len(set(indices)) == len(indices), 'Ambiguous duplicate sculpt handle'
    anchors.add(indices, 1., 'REPLACE')
    modifier = working.modifiers.new('SelectedSurfaceDifferentialDetail', 'LAPLACIANDEFORM')
    modifier.vertex_group = anchors.name
    modifier.iterations = controls['laplacianIterations']
    bpy.ops.object.select_all(action='DESELECT')
    working.hide_render = False
    working.hide_viewport = False
    working.hide_set(False)
    working.select_set(True)
    bpy.context.view_layer.objects.active = working
    bpy.ops.object.laplaciandeform_bind(modifier=modifier.name)
    assert modifier.is_bind, 'Ordinary Laplacian sculpt did not bind'
    for handle in handles:
        working.data.vertices[handle['sourceVertex']].co = handle['targetWorld']
    working.data.update()
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    frozen = bpy.data.meshes.new_from_object(working.evaluated_get(depsgraph),
                                           preserve_all_data_layers=True, depsgraph=depsgraph)
    assert len(frozen.vertices) == len(rejected.data.vertices)
    assert len(frozen.polygons) == len(rejected.data.polygons)
    assert uv_bytes(frozen) == expected_uv
    frozen_faces = np.empty((len(frozen.polygons), 3), dtype=np.int32)
    frozen.polygons.foreach_get('vertices', frozen_faces.ravel())
    assert np.array_equal(frozen_faces, faces), 'Selected source corner ancestry changed'
    result = bpy.data.objects.new('Gloves__AnatomicallySculptedSelected.' + side, frozen)
    bpy.context.collection.objects.link(result)
    points = vertices(frozen)
    assert np.isfinite(points).all()
    anchor_residual = max(np.linalg.norm(points[h['sourceVertex']] - h['targetWorld']) for h in handles)
    result['acceptedArt'] = False
    result['status'] = 'UNACCEPTED_SELECTED_ANATOMICAL_LAPLACIAN_SCULPT'
    result['sourceNativeSHA256'] = controls['pins']['native']['sha256']
    result['sourceMeshSHA256'] = controls['pins']['denseSelected']['sha256']
    result['sourceCornerUVByteParity'] = True
    result['editableSculptObject'] = working.name
    binding = bind_native(result, original, body_arrays, hand, controls, side, rig)
    rejected.hide_render = True
    rejected.hide_set(True)
    working.hide_render = True
    working.hide_set(True)
    return {'object': result.name, 'negativeControl': rejected.name,
            'editableSculpt': working.name, 'vertexCount': len(points),
            'triangleCount': len(frozen.polygons), 'sourceCornerUVByteParity': True,
            'handleCount': len(handles), 'maximumHandleResidualMeters': float(anchor_residual),
            'reflectionFromSelectedSource': initial['reflectionFromSelectedSource'],
            'faceAndUVCornerWindingReversedTogether': initial['reflectionFromSelectedSource'],
            'selectedFaceOrderByteParity': True,
            'signedMCPPalmCurlChecks': initial['signedMCPPalmCurlChecks'],
            'bounds': [points.min(0).tolist(), points.max(0).tolist()], 'binding': binding}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 2
    controls_path, out = (Path(value).resolve() for value in args)
    controls = json.loads(controls_path.read_text())
    assert controls['acceptedArt'] is False
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/glove-anatomical04')
    assert not out.exists()
    paths = {}
    for name, pin in controls['pins'].items():
        paths[name] = ROOT / pin['path']
        assert sha(paths[name]) == pin['sha256'], ('Changed frozen source', name)
    bpy.ops.wm.open_mainfile(filepath=str(paths['native']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and rig.matrix_world.is_identity
    assert all(bone.matrix_basis.is_identity for bone in rig.pose.bones)
    before = signature(body, rig)
    out.mkdir(parents=True)
    dense = np.load(paths['denseSelected'])
    native = np.load(paths['nativeArrays'])
    report = {'acceptedArt': False, 'operation': 'SELECTED_SURFACE_ANATOMICAL_LAPLACIAN_SCULPT',
              'controlsSHA256': sha(controls_path), 'recipeSHA256': sha(__file__),
              'pins': controls['pins'], 'bodyAndMasterBefore': before, 'hands': {},
              'bakesExecuted': 0, 'newPlayerAssets': 0,
              'limits': ['Actual PBR views and bilateral moving art remain parent review.',
                         'Dense selected derivative is an editable master; runtime topology is not qualified.',
                         'No static control/UV/rig assertion confers wearing fit or art acceptance.']}
    for side in ('R', 'L'):
        report['hands'][side] = sculpt(side, controls, dense, native, np.load(paths['hand' + side]), rig)
        assert signature(body, rig) == before
        native_path = out / 'editable-selected-bilateral-gloves.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(native_path), compress=True)
        report['native'] = {'path': str(native_path.relative_to(ROOT)), 'sha256': sha(native_path)}
        (out / ('checkpoint-' + side + '.json')).write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'savedSide': side, 'native': report['native']}), flush=True)
    report['bodyAndMasterAfter'] = signature(body, rig)
    report['status'] = 'BILATERAL_SELECTED_SCULPT_SAVED_BEFORE_PARENT_PBR_REVIEW'
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
