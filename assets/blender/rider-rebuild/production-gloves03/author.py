"""Ordinary offline source-rest armature authoring for actual selected glove.

No registration, categorical segment affine, ray projection, cage or bake.
The actual source topology/corner UV/PBR survive evaluated armature posing.
A source-rest rig is a modeling aid; unchanged RiderSkeleton remains authority.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(v):
    return np.asarray(v) / np.linalg.norm(v)


def projection(v, axis):
    return np.einsum('ij,j->i', v, axis)


def frame(head, tail, radial):
    y = unit(tail - head)
    x = unit(radial - y * np.dot(radial, y))
    z = unit(np.cross(x, y))
    matrix = np.eye(4)
    matrix[:3, :3] = np.stack((x, y, z), axis=1)
    matrix[:3, 3] = head
    return matrix


def protected_signature(body, rig):
    h = hashlib.sha256()
    for vertex in body.data.vertices:
        h.update(struct.pack('<3f', *vertex.co))
        for group in vertex.groups:
            h.update(struct.pack('<If', group.group, group.weight))
    for polygon in body.data.polygons:
        h.update(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
    for bone in rig.data.bones:
        h.update(bone.name.encode())
        h.update(struct.pack('<16f', *(v for row in bone.matrix_local for v in row)))
    return h.hexdigest()


def material(paths):
    mat = bpy.data.materials.new('SelectedOriginalGlovePBR03')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    for key in ('baseColor', 'metallicRoughness'):
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(paths[key]), check_existing=True)
        node.image.pack()
        if key == 'baseColor':
            links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        else:
            node.image.colorspace_settings.name = 'Non-Color'
            channels = nodes.new('ShaderNodeSeparateColor')
            links.new(node.outputs['Color'], channels.inputs['Color'])
            links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
            links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def make_mesh(name, vertices, faces, uv, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    layer = mesh.uv_layers.new(name='OriginalSelectedCornerUV')
    blender_uv = uv.copy()
    blender_uv[:, :, 1] = 1 - blender_uv[:, :, 1]
    layer.data.foreach_set('uv', blender_uv.astype(np.float32).ravel())
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def authored_bones(control, native, side):
    names = native['jointNames'].tolist()
    lookup = {name: i for i, name in enumerate(names)}
    head = lambda name: native['jointHeads'][lookup[name]]
    tail = lambda name: native['jointTails'][lookup[name]]
    mirror = np.array([-1., 1., 1.]) if side == 'L' else np.ones(3)
    wrist = np.array(control['wrist']) * mirror
    radial = np.array([1., 0., 0.]) * mirror
    target_wrist = head('DEF-hand.' + side)
    target_forward = unit(head('DEF-f_middle.01.' + side) - target_wrist)
    target_radial = head('DEF-f_index.01.' + side) - head('DEF-f_pinky.01.' + side)
    target_radial = unit(target_radial - target_forward * np.dot(target_radial, target_forward))
    bones = []
    def append(name, sh, st, th, tt, parent, kind, native_name):
        bones.append({'name': name, 'sourceHead': sh, 'sourceTail': st,
                      'targetHead': th, 'targetTail': tt, 'parent': parent,
                      'kind': kind, 'nativeName': native_name,
                      'sourceFrame': frame(sh, st, radial),
                      'targetFrame': frame(th, tt, target_radial)})
    append('source-hand.' + side, wrist,
           np.array(control['digits']['middle'][0]) * mirror,
           target_wrist, head('DEF-f_middle.01.' + side), None, 'palm', 'DEF-hand.' + side)
    for digit in DIGITS:
        points = np.asarray(control['digits'][digit]) * mirror
        stem = 'thumb' if digit == 'thumb' else 'f_' + digit
        root = 'source-hand.' + side
        if digit != 'thumb':
            meta = 'source-metacarpal-' + digit + '.' + side
            append(meta, wrist, points[0], target_wrist,
                   head('DEF-' + stem + '.01.' + side), root, 'palm', 'DEF-hand.' + side)
            root = meta
        for segment in range(3):
            name = f'DEF-{stem}.{segment + 1:02d}.{side}'
            append(name, points[segment], points[segment + 1],
                   head(name), tail(name), root, 'digit', name)
            root = name
    return bones


def source_weights(vertices, bones):
    """Continuous overlapping capsule envelopes, normalized over all bones.

    Adjacent segments overlap at every joint. Metacarpals overlap through the
    palm; the thumb CMC envelope overlaps hand/metacarpals through thenar.
    No vertex is assigned one segment transform or an atlas digit category.
    """
    values = []
    for bone in bones:
        h, t = bone['sourceHead'], bone['sourceTail']
        axis = t - h
        u = np.clip(projection(vertices - h, axis) / np.dot(axis, axis), 0, 1)
        delta = vertices - (h + u[:, None] * axis)
        axes = bone['sourceFrame'][:3, :3]
        # Authored source envelope dimensions, not target depth scale factors.
        radius = (.28, .31) if bone['kind'] == 'palm' else (.115, .165)
        xx = projection(delta, axes[:, 0]) / radius[0]
        zz = projection(delta, axes[:, 2]) / radius[1]
        yy = projection(delta, axes[:, 1]) / (radius[0] * 1.3)
        distance2 = xx * xx + yy * yy + zz * zz
        values.append(np.exp(-2 * distance2 * distance2))
    weights = np.stack(values, axis=1)
    assert np.all(weights.sum(1) > 1e-100), 'Source beyond authored bone envelopes'
    weights /= weights.sum(1)[:, None]
    assert np.max(abs(weights.sum(1) - 1)) < 1e-12
    return weights


def section_dimensions(vertices, bone, source, candidates=None):
    """Measure actual transverse extent near the authored segment midpoint.

    This is one local width/thickness authoring measurement, not a surface
    correspondence or fit certification. No map or registration is computed.
    """
    prefix = 'source' if source else 'target'
    h, t = bone[prefix + 'Head'], bone[prefix + 'Tail']
    axes = bone[prefix + 'Frame'][:3, :3]
    delta = vertices - h
    longitudinal = projection(delta, axes[:, 1]) / np.linalg.norm(t - h)
    x, z = projection(delta, axes[:, 0]), projection(delta, axes[:, 2])
    near = (longitudinal > .27) & (longitudinal < .73)
    if bone['kind'] == 'digit':
        radius = .19 if source else .024
        near &= (x * x + z * z < radius * radius)
        if source:
            near &= abs(x) < .13
    elif source:
        # The selected palm excludes separate fingers/thumb for palm sizing.
        near &= (vertices[:, 1] > -.55) & (vertices[:, 1] < .10)
        near &= (vertices[:, 0] > -.64) & (vertices[:, 0] < .27) if h[0] < 0 else (vertices[:, 0] > -.27) & (vertices[:, 0] < .64)
    if candidates is not None:
        near &= candidates
    assert int(near.sum()) >= 4, (bone['name'], prefix, int(near.sum()))
    extent = np.array([np.quantile(abs(x[near]), .98), np.quantile(abs(z[near]), .98)])
    assert np.all(extent > 0), (bone['name'], prefix, extent)
    return extent, int(near.sum())


def set_pose_matrices(rig, desired):
    """Blender documented parent-first conversion; no inherited parent scale.

    https://docs.blender.org/api/current/bpy.types.Bone.html#bpy.types.Bone.convert_local_to_pose
    Each desired matrix remains the authored target frame and measured scale.
    Explicit local basis conversion respects each bone's inheritance settings.
    """
    def assign(pose, parent_matrix):
        matrix = desired[pose.name]
        options = {'invert': True}
        if pose.parent:
            options.update(parent_matrix=parent_matrix,
                           parent_matrix_local=pose.parent.bone.matrix_local)
        pose.matrix_basis = pose.bone.convert_local_to_pose(
            matrix, pose.bone.matrix_local, **options)
        for child in pose.children:
            assign(child, matrix)
    for pose in rig.pose.bones:
        if not pose.parent:
            assign(pose, None)
    bpy.context.view_layer.update()


def save_failed_pose(out, side, rig, obj, bones, desired, records, residuals):
    """Preserve editable authoring state and named diagnostics before raising."""
    obj.hide_render = False
    obj.hide_set(False)
    rig.hide_set(False)
    obj['status'] = 'FAILED_OFFLINE_POSE_CONTROL_CHECK_UNACCEPTED'
    native_path = out / ('failed-pose-' + side + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(native_path))
    rows = []
    for spec, residual in zip(bones, residuals):
        pose = rig.pose.bones[spec['name']]
        rows.append({'name': spec['name'], 'parent': spec['parent'],
                     'inheritScale': pose.bone.inherit_scale,
                     'desiredMatrix': [list(row) for row in desired[spec['name']]],
                     'actualMatrix': [list(row) for row in pose.matrix],
                     'actualMatrixBasis': [list(row) for row in pose.matrix_basis],
                     'sourceRestMatrix': [list(row) for row in pose.bone.matrix_local],
                     'desiredHead': spec['targetHead'].tolist(),
                     'desiredTail': spec['targetTail'].tolist(),
                     'actualHead': list(pose.head), 'actualTail': list(pose.tail),
                     'maxHeadTailResidualMeters': residual})
    receipt = {'status': 'FAILED_OFFLINE_POSE_CONTROL_CHECK_NATIVE_PRESERVED',
               'acceptedArt': False, 'side': side,
               'native': {'path': str(native_path.relative_to(ROOT)), 'sha256': sha(native_path)},
               'sourceRecipeSHA256': sha(__file__),
               'controlsSHA256': sha(HERE / 'controls.json'),
               'sourcePins': json.loads((HERE / 'inputs.json').read_text()),
               'controlToleranceMeters': 1e-5,
               'bodyAndMasterRestSignature': protected_signature(
                   bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']),
               'maxActualResidualMeters': max(residuals),
               'sourceRestObject': obj.name, 'offlineRig': rig.name,
               'sectionAndPoseScaleRecords': records, 'bones': rows}
    (out / ('failed-pose-' + side + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'failedSide': side, 'savedDiagnosticNative': receipt['native'],
                      'maxActualResidualMeters': max(residuals)}), flush=True)


def author_hand(side, dense, native, hand, control, mat, out):
    vertices, faces, uv = dense['vertices'].copy(), dense['faces'].copy(), dense['originalCornerUV'].copy()
    if side == 'L':
        vertices[:, 0] *= -1
        faces = faces[:, ::-1]
        uv = uv[:, ::-1]
    bones = authored_bones(control, native, side)
    weights = source_weights(vertices, bones)
    obj = make_mesh('SelectedSourceRest.' + side, vertices, faces, uv, mat)
    rig = bpy.data.objects.new('GloveSourceAuthoringRig.' + side,
                               bpy.data.armatures.new('GloveSourceAuthoringRig.' + side))
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for spec in bones:
        bone = rig.data.edit_bones.new(spec['name'])
        bone.head, bone.tail = Vector(spec['sourceHead']), Vector(spec['sourceTail'])
        bone.align_roll(Vector(spec['sourceFrame'][:3, 2]))
        if spec['parent']:
            bone.parent = rig.data.edit_bones[spec['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    for j, spec in enumerate(bones):
        # Independent offline length/width adaptation must not inherit parent
        # nonuniform scale and force a sheared local TRS decomposition.
        rig.data.bones[spec['name']].inherit_scale = 'NONE'
        group = obj.vertex_groups.new(name=spec['name'])
        # Keep every computed nonzero weight; full normalization survives.
        for i in np.flatnonzero(weights[:, j] > 0):
            group.add([int(i)], float(weights[i, j]), 'REPLACE')
    modifier = obj.modifiers.new('OfflineSourceRestPose', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    records = []
    desired = {}
    target_names = hand['jointNames'].tolist()
    for spec in bones:
        candidates = hand['nativeCoefficients'][:, target_names.index('DEF-hand.' + side)] > .25
        if spec['kind'] == 'digit':
            candidates = hand['nativeCoefficients'][:, target_names.index(spec['nativeName'])] > .10
        source_extent, source_count = section_dimensions(vertices, spec, True)
        target_extent, target_count = section_dimensions(hand['vertices'], spec, False, candidates)
        ease = control['authoredEaseMeters']
        label = 'palm' if spec['kind'] == 'palm' else 'finger'
        width = (target_extent + np.array([ease[label + 'Radial'], ease[label + 'Dorsal']])) / source_extent
        length_scale = np.linalg.norm(spec['targetTail'] - spec['targetHead']) / np.linalg.norm(spec['sourceTail'] - spec['sourceHead'])
        scale = np.diag([width[0], length_scale, width[1], 1.])
        desired[spec['name']] = Matrix((spec['targetFrame'] @ scale).tolist())
        records.append({'name': spec['name'], 'sourceHead': spec['sourceHead'].tolist(),
                        'sourceTail': spec['sourceTail'].tolist(),
                        'targetHead': spec['targetHead'].tolist(), 'targetTail': spec['targetTail'].tolist(),
                        'sourceMeasuredSectionHalfExtent': source_extent.tolist(),
                        'targetMeasuredSectionHalfExtent': target_extent.tolist(),
                        'sectionSamples': [source_count, target_count],
                        'authoredPoseScaleXYZ': [float(width[0]), float(length_scale), float(width[1])]})
    set_pose_matrices(rig, desired)
    control_residuals = []
    for spec in bones:
        pose = rig.pose.bones[spec['name']]
        residual = max(np.linalg.norm(np.asarray(pose.head) - spec['targetHead']),
                       np.linalg.norm(np.asarray(pose.tail) - spec['targetTail']))
        control_residuals.append(float(residual))
    if not max(control_residuals) < 1e-5:
        save_failed_pose(out, side, rig, obj, bones, desired, records, control_residuals)
    assert max(control_residuals) < 1e-5, ('Actual posed controls missed target', control_residuals)
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    frozen_mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True,
                                                depsgraph=bpy.context.evaluated_depsgraph_get())
    fitted = bpy.data.objects.new('SelectedFittedSource.' + side, frozen_mesh)
    bpy.context.collection.objects.link(fitted)
    fitted['status'] = 'UNACCEPTED_ORIGINAL_PBR_SOURCE_FIT_BEFORE_BAKE'
    fitted['sourceRig'] = rig.name
    fitted['sourceUVPreserved'] = True
    assert len(frozen_mesh.vertices) == len(vertices) and len(frozen_mesh.polygons) == len(faces)
    final_uv = np.empty((len(frozen_mesh.loops), 2), dtype=np.float32)
    frozen_mesh.uv_layers.active.data.foreach_get('uv', final_uv.ravel())
    expected_uv = uv.copy(); expected_uv[:, :, 1] = 1 - expected_uv[:, :, 1]
    assert np.array_equal(final_uv, expected_uv.reshape(-1, 2).astype(np.float32))
    obj.hide_render = True
    obj.hide_set(True)
    rig.hide_render = True
    rig.hide_set(True)
    fitted.select_set(False)
    np.savez_compressed(out / ('source-rest-weights-' + side + '.npz'), weights=weights,
                        jointNames=np.asarray([b['name'] for b in bones]))
    return {'object': fitted.name, 'offlineRig': rig.name, 'sourceRestObject': obj.name,
            'vertices': len(vertices), 'triangles': len(faces), 'controls': records,
            'normalizedWeightMaxResidual': float(np.max(abs(weights.sum(1) - 1))),
            'actualPoseControlMaxResidualMeters': max(control_residuals),
            'originalCornerUVByteParity': True,
            'sourceReflectedWithFaceAndUVCornerWinding': side == 'L'}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'docs/evidence/rider-rebuild/production-gloves03')
    records = json.loads((HERE / 'inputs.json').read_text())
    paths = {key: ROOT / record['path'] for key, record in records.items()}
    for key, record in records.items():
        assert sha(paths[key]) == record['sha256'], ('Changed input', key)
    out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(paths['nativeMaster']))
    body, master_rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(master_rig.data.bones) == 75
    signature = protected_signature(body, master_rig)
    master_rig.animation_data_clear()
    for bone in master_rig.pose.bones:
        bone.matrix_basis.identity()
    bpy.context.view_layer.update()
    body.hide_render = False
    body.hide_set(False)
    control = json.loads((HERE / 'controls.json').read_text())
    dense, native = np.load(paths['denseSelected']), np.load(paths['nativeArrays'])
    mat = material(paths)
    report = {'status': 'SOURCE_REST_CONSTRUCTION_IN_PROGRESS', 'acceptedArt': False,
              'sourcePins': records, 'sourceFiles': {p.name: sha(p) for p in HERE.glob('*') if p.is_file()},
              'bodyAndMasterRestBefore': signature, 'hands': {}, 'bakesExecuted': 0,
              'completeVisibleBody': body.name, 'sourceRigIsOfflineModelingAid': True}
    for side in ('R', 'L'):
        report['hands'][side] = author_hand(side, dense, native, np.load(paths['hand' + side]), control, mat, out)
        assert protected_signature(body, master_rig) == signature
        native_path = out / ('fitted-source-' + side + '.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(native_path))
        report['native'] = {'path': str(native_path.relative_to(ROOT)), 'sha256': sha(native_path)}
        (out / ('checkpoint-' + side + '.json')).write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'savedSide': side, 'native': report['native']}), flush=True)
    report['status'] = 'BOTH_ORIGINAL_PBR_FITTED_SOURCE_SAVED_FOR_PARENT_INSPECTION'
    report['bodyAndMasterRestAfter'] = protected_signature(body, master_rig)
    report['limits'] = ['No art acceptance; inspect all hand sides/web/cuff before baking.',
                        'Dense fitted sculpture is a master source, not runtime production mesh.',
                        'No production rebind, articulation, finite grip or outfit acceptance.']
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
