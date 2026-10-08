"""Actual selected dense alignment and ordinary cage bake reused from01.

Copied helper lineage: author.py SHA256
661880dd0ccb75738341ace95343cfbf46c11b202d0643dae520a6afcb8e8d59.
Geometry/panel construction never imports a BVH or uses these bake rays.
1024 is explicitly first review; 4096 is the final production master stage.
"""
import hashlib
import json
from pathlib import Path
import math
import bpy
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree
ROOT = Path(__file__).resolve().parents[4]
DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
unit = lambda p: np.asarray(p) / np.linalg.norm(p)


def mesh_object(name, vertices, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces); mesh.update()
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj)
    for p in mesh.polygons: p.use_smooth = True
    return obj


def donor_material(paths):
    mat = bpy.data.materials.new('SelectedDenseBlackLeather'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    color = mat.node_tree.nodes.new('ShaderNodeTexImage'); color.image = bpy.data.images.load(str(paths['baseColor']))
    mr = mat.node_tree.nodes.new('ShaderNodeTexImage'); mr.image = bpy.data.images.load(str(paths['metallicRoughness']))
    mr.image.colorspace_settings.name = 'Non-Color'
    channels = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
    mat.node_tree.links.new(color.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(mr.outputs['Color'], channels.inputs['Color'])
    mat.node_tree.links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
    mat.node_tree.links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat, color, mr


def align_dense(author, source, dense, material):
    # The compact exterior supplies source part routing and a detail cage only.
    # Direct landmark proportional edits align the selected high sculpt. There
    # is no ARAP, root filtration, correspondence proof, ray optimization or
    # requirement to retain this cage in the production garment.
    sv = source['vertices']; tree = KDTree(len(sv))
    for i, p in enumerate(sv): tree.insert(Vector(p), i)
    tree.balance()
    compact_ids = np.array([tree.find(Vector(p))[1] for p in dense['vertices']])
    labels = source['sourceBranchLabels'][compact_ids]
    source_cuff = sv[source['cuffBoundaryVertexIds']].mean(0)
    source_forward = unit(source['middle_centers'][0] - source_cuff)
    source_radial = unit(np.array([1., 0, 0]) - source_forward * source_forward[0])
    source_dorsal = unit(np.cross(source_radial, source_forward))
    old_frame = np.stack([source_radial, source_forward, source_dorsal], 1)
    new_frame = np.stack([author.radial, author.forward, author.dorsal], 1)
    radial_scale = np.linalg.norm(author.head('DEF-f_index.01.' + author.side) - author.head('DEF-f_pinky.01.' + author.side)) / np.linalg.norm(source['index_centers'][0] - source['pinky_centers'][0])
    length_scale = np.linalg.norm(author.head('DEF-f_middle.01.' + author.side) - author.hand['cuffOrigin']) / np.linalg.norm(source['middle_centers'][0] - source_cuff)
    matrix = np.einsum('ij,kj,j->ik', new_frame, old_frame,
                       np.array([radial_scale, length_scale, radial_scale * .68]))
    points = np.einsum('nj,ij->ni', dense['vertices'] - source_cuff, matrix) + author.hand['cuffOrigin']
    for label, digit in enumerate(DIGITS, 1):
        mask = labels == label
        if not mask.any(): continue
        old = source[digit + '_centers']
        chain = author.chain(digit)
        target = np.array([author.head(b) for b in chain] + [author.tail(chain[-1])])
        p = dense['vertices'][mask]
        segments = np.diff(old, axis=0)
        t = np.clip(np.sum((p[:, None] - old[None, :-1]) * segments[None], axis=2) / np.sum(segments ** 2, axis=1), 0, 1)
        projected = old[None, :-1] + t[:, :, None] * segments[None]
        selected = np.argmin(np.sum((p[:, None] - projected) ** 2, axis=2), axis=1)
        fitted = []
        for j in range(3):
            ids = np.flatnonzero(selected == j)
            if not len(ids): continue
            old_axis = unit(old[j + 1] - old[j]); new_axis = unit(target[j + 1] - target[j])
            old_x = unit(source_radial - old_axis * np.dot(source_radial, old_axis))
            new_x = unit(author.radial - new_axis * np.dot(author.radial, new_axis))
            old_z = unit(np.cross(old_x, old_axis))
            new_z = unit(np.cross(new_x, new_axis)) * (1 if author.side == 'R' else -1)
            delta = p[ids] - projected[ids, j]
            q = target[j] + t[ids, j, None] * (target[j + 1] - target[j])
            q += np.sum(delta * old_x, axis=1)[:, None] * new_x * radial_scale
            q += np.sum(delta * old_z, axis=1)[:, None] * new_z * radial_scale * .82
            fitted.append((ids, q))
        values = points[mask].copy()
        for ids, q in fitted: values[ids] = q
        # Broad authored falloff through the base prevents abrupt digit edits.
        axial = np.array([np.linalg.norm(old[i] - old[0]) for i in range(3)])[selected] + t[np.arange(len(p)), selected] * np.linalg.norm(segments[selected], axis=1)
        blend = np.clip(axial / .11, 0, 1); blend = blend * blend * (3 - 2 * blend)
        points[mask] = points[mask] * (1 - blend[:, None]) + values * blend[:, None]
    faces = dense['faces'].copy()
    uv = dense['originalCornerUV'].copy()
    if author.side == 'L':
        faces = faces[:, ::-1]; uv = uv[:, ::-1]
    obj = mesh_object('SelectedDenseBake.' + author.side, points, faces)
    layer = obj.data.uv_layers.new(name='OriginalDenseCornerUV')
    # glTF's texture coordinate origin becomes Blender's bottom-left origin.
    uv[:, :, 1] = 1 - uv[:, :, 1]
    layer.data.foreach_set('uv', uv.astype(np.float32).ravel())
    obj.data.materials.append(material)
    return obj


def bake(scene, target, donor, out, material, color_node, mr_node, resolution):
    target_material = bpy.data.materials.new('GloveSelectedPBR.' + target.name[-1]); target_material.use_nodes = True
    target.data.materials.append(target_material)
    bsdf = target_material.node_tree.nodes.get('Principled BSDF')
    outputs = {}
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = .004
    scene.render.bake.max_ray_distance = .008
    scene.render.bake.margin = max(10, resolution // 102)
    # Explicit per-side cage. Left and right bake targets are never combined.
    cage = target.copy(); cage.data = target.data.copy(); cage.name = target.name + '.BakeCage'
    cage.modifiers.clear(); bpy.context.collection.objects.link(cage)
    for v in cage.data.vertices: v.co += v.normal * .004
    scene.render.bake.use_cage = True; scene.render.bake.cage_object = cage.name
    cage.hide_render = True; cage.hide_set(True)
    for kind in ('baseColor', 'metallicRoughness', 'normal'):
        image = bpy.data.images.new(target.name + '.' + kind, width=resolution, height=resolution, alpha=False)
        if kind != 'baseColor': image.colorspace_settings.name = 'Non-Color'
        node = target_material.node_tree.nodes.new('ShaderNodeTexImage'); node.image = image
        target_material.node_tree.nodes.active = node
        bpy.ops.object.select_all(action='DESELECT'); donor.hide_set(False); donor.select_set(True); target.select_set(True)
        bpy.context.view_layer.objects.active = target
        if kind == 'normal':
            bpy.ops.object.bake(type='NORMAL')
        else:
            # Emit actual source map channels without lighting contamination.
            tree = material.node_tree; output = tree.nodes.get('Material Output')
            emission = tree.nodes.new('ShaderNodeEmission')
            tree.links.new((color_node if kind == 'baseColor' else mr_node).outputs['Color'], emission.inputs['Color'])
            tree.links.new(emission.outputs[0], output.inputs['Surface'])
            bpy.ops.object.bake(type='EMIT')
            tree.links.new(tree.nodes.get('Principled BSDF').outputs['BSDF'], output.inputs['Surface'])
            tree.nodes.remove(emission)
        image.filepath_raw = str(out / (target.name + '-' + kind + '.png')); image.file_format = 'PNG'; image.save(); image.pack()
        outputs[kind] = {'resolution': resolution, 'derivativeRole': 'FIRST_REVIEW' if resolution == 1024 else 'FINAL_4K_MASTER', 'path': str(Path(image.filepath_raw).relative_to(ROOT)), 'sha256': sha(image.filepath_raw)}
        if kind == 'baseColor': target_material.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
        elif kind == 'normal':
            normal = target_material.node_tree.nodes.new('ShaderNodeNormalMap')
            target_material.node_tree.links.new(node.outputs['Color'], normal.inputs['Color'])
            target_material.node_tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
        else:
            channels = target_material.node_tree.nodes.new('ShaderNodeSeparateColor')
            target_material.node_tree.links.new(node.outputs['Color'], channels.inputs['Color'])
            target_material.node_tree.links.new(channels.outputs['Green'], bsdf.inputs['Roughness'])
            target_material.node_tree.links.new(channels.outputs['Blue'], bsdf.inputs['Metallic'])
    donor.hide_set(True); donor.hide_render = True
    return outputs


def motion(rig, controls):
    # Short actual shared-rig movement; this is a review film action, not grip
    # acceptance or a replacement for the parent's real finite handlebar test.
    rig.animation_data_clear()
    for frame, flex, spread in ((1, 0, 0), (20, .75, 0), (40, 0, .12), (60, .5, 0), (80, 0, 0)):
        for side in ('left', 'right'):
            for name, spec in controls['digitFlex'][side].items():
                bone = rig.pose.bones[name]; bone.rotation_mode = 'QUATERNION'
                angle = spec['maxRadians'] * spec['positiveSign'] * flex
                bone.rotation_quaternion = Quaternion(Vector(spec['axisLocal']), angle)
                if spread and '.01.' in name and 'thumb' not in name:
                    direction = -1 if 'index' in name else (1 if 'pinky' in name else 0)
                    bone.rotation_quaternion @= Quaternion(Vector((0, 0, 1)), spread * direction)
                bone.keyframe_insert(data_path='rotation_quaternion', frame=frame)
    action = rig.animation_data.action; action.name = 'GloveReviewOpenFistSpreadApproxGripReturn'
    return action.name


def save_checkpoint(out, filename, report, report_name):
    blend = out / filename
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report['native'] = {'path': str(blend.relative_to(ROOT)), 'sha256': sha(blend)}
    (out / report_name).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'native': report['native']}), flush=True)
