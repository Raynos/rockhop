"""One authored selected-glove pass, run only under the parent's CPU2 lease.

Native hand topology is a construction scaffold. Production adds deliberately
shaped ease, sewn panels, articulated ribs, palm pads, cuff lip and closure.
The original dense corner UVs are the paint authority. No old fitting solver,
source-face preservation requirement or prototype UV is used.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DIGITS = ('pinky', 'ring', 'middle', 'index', 'thumb')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(value):
    return np.asarray(value) / np.linalg.norm(value)


def body_signature(body, rig):
    h = hashlib.sha256()
    for v in body.data.vertices:
        h.update(struct.pack('<3f', *v.co))
        for g in v.groups:
            h.update(struct.pack('<If', g.group, g.weight))
    for p in body.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
    for b in rig.data.bones:
        h.update(b.name.encode())
        h.update(struct.pack('<16f', *(x for row in b.matrix_local for x in row)))
    return h.hexdigest()


def mesh_object(name, vertices, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = True
    return obj


class HandAuthor:
    def __init__(self, side, hand, body, rig):
        self.side, self.hand, self.body, self.rig = side, hand, body, rig
        self.names = body['jointNames'].tolist()
        self.lookup = {name: i for i, name in enumerate(self.names)}
        self.hand_name = 'DEF-hand.' + side
        self.forearm_name = 'DEF-forearm.' + side
        self.wrist = self.head(self.hand_name)
        self.forward = unit(self.head('DEF-f_middle.01.' + side) - self.wrist)
        self.radial = self.head('DEF-f_index.01.' + side) - self.head('DEF-f_pinky.01.' + side)
        self.radial = unit(self.radial - self.forward * np.dot(self.radial, self.forward))
        # Each actual geometry supplies its own frame. Left donor appearance is
        # reflected; target geometry, topology and skin are never mirrored.
        self.dorsal = unit(np.cross(self.radial, self.forward)) * (1 if side == 'R' else -1)
        self.vertices, self.faces, self.fields, self.parts = [], [], [], []
        self.features = []
        v, f = hand['vertices'].copy(), hand['faces'].copy()
        n = np.zeros_like(v)
        area = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
        for j in range(3):
            np.add.at(n, f[:, j], area)
        n /= np.linalg.norm(n, axis=1)[:, None]
        fields = hand['fourCoefficients']
        masses = np.stack([fields[:, [self.lookup[x] for x in self.chain(d)]].sum(1) for d in DIGITS], 1)
        labels = np.where(masses.max(1) > .28, masses.argmax(1), -1)
        # Deliberate palm/finger tailoring: dorsal padding, palm grip allowance,
        # less bulk at interdigital webs and distal taper. Not uniform inflation.
        back = np.clip(np.sum(n * self.dorsal, axis=1), 0, 1)
        palm = np.clip(-np.sum(n * self.dorsal, axis=1), 0, 1)
        ease = .0016 + back * .0014 + palm * .0007
        ease[labels < 0] += back[labels < 0] * .0012
        for i, digit in enumerate(DIGITS):
            mask = labels == i
            end = self.tail(self.chain(digit)[-1])
            taper = np.clip(np.linalg.norm(v[mask] - end, axis=1) / .022, 0, 1)
            ease[mask] *= .72 + .28 * taper
        self.scaffold = v + n * ease[:, None]
        self.bvh = BVHTree.FromPolygons(self.scaffold.tolist(), f.tolist(), all_triangles=True)
        self.digit_bvh = {digit: BVHTree.FromPolygons(self.scaffold.tolist(),
            f[np.max(masses[f, i], axis=1) > .08].tolist(), all_triangles=True)
            for i, digit in enumerate(DIGITS)}
        shell_fields = [self.paint(p, DIGITS[int(label)] if label >= 0 else None) for p, label in zip(v, labels)]
        self.append('tailored-shell', self.scaffold, f, shell_fields)

    def chain(self, digit):
        stem = 'thumb' if digit == 'thumb' else 'f_' + digit
        return [f'DEF-{stem}.{i:02d}.{self.side}' for i in (1, 2, 3)]

    def head(self, name):
        return self.body['jointHeads'][self.lookup[name]]

    def tail(self, name):
        return self.body['jointTails'][self.lookup[name]]

    def paint(self, p, digit):
        field = np.zeros(75)
        if digit is None:
            proximal = np.dot(p - self.wrist, self.hand['cuffProximalAxis'])
            t = np.clip((proximal - .003) / .025, 0, 1)
            t = t * t * (3 - 2 * t)
            field[self.lookup[self.hand_name]] = 1 - t
            field[self.lookup[self.forearm_name]] = t
            return field
        chain = self.chain(digit)
        lengths = np.array([np.linalg.norm(self.tail(b) - self.head(b)) for b in chain])
        starts = np.r_[0, np.cumsum(lengths)]
        distance, axial = [], []
        for i, bone in enumerate(chain):
            segment = self.tail(bone) - self.head(bone)
            t = np.clip(np.dot(p - self.head(bone), segment) / np.dot(segment, segment), 0, 1)
            distance.append(np.linalg.norm(p - self.head(bone) - t * segment))
            axial.append(starts[i] + t * lengths[i])
        s = axial[int(np.argmin(distance))]
        # Joint-local painted transitions, restricted to this chain and hand.
        centers = (starts[:-1] + starts[1:]) / 2
        positions = np.r_[-.012, centers]
        ids = [self.lookup[self.hand_name]] + [self.lookup[b] for b in chain]
        if s >= positions[-1]:
            field[ids[-1]] = 1
        else:
            i = max(0, int(np.searchsorted(positions, s) - 1))
            t = np.clip((s - positions[i]) / (positions[i + 1] - positions[i]), 0, 1)
            t = t * t * (3 - 2 * t)
            field[ids[i]], field[ids[i + 1]] = 1 - t, t
        return field

    def append(self, name, vertices, faces, fields):
        start = len(self.vertices)
        self.vertices.extend(np.asarray(vertices).tolist())
        self.fields.extend(np.asarray(fields).tolist())
        self.faces.extend((np.asarray(faces) + start).tolist())
        self.parts.extend([name] * len(faces))
        self.features.append({'name': name, 'vertices': len(vertices), 'faces': len(faces)})

    def surface(self, p, outward, digit=None):
        bvh = self.digit_bvh[digit] if digit else self.bvh
        hit, normal, _, _ = bvh.ray_cast(Vector(p + outward * .06), Vector(-outward), .12)
        if hit is None or np.dot(normal, outward) < .1:
            raise RuntimeError(f'{self.side}: authored panel ray misses its hand at {p}')
        return np.array(hit), unit(normal)

    def panel(self, name, center, along, across, outward, length, width, digit=None, height=.0012):
        # Rounded sewn patch with a modeled raised perimeter and domed padding.
        vertices, fields, faces = [], [], []
        rows, cols = 9, 9
        for j in range(rows):
            y = j / (rows - 1) * 2 - 1
            round_width = width * (.84 + .16 * math.sqrt(max(0, 1 - y * y)))
            for i in range(cols):
                x = i / (cols - 1) * 2 - 1
                p = center + along * y * length / 2 + across * x * round_width / 2
                q, n = self.surface(p, outward, digit)
                bulge = max(0, (1 - x * x) * (1 - y * y)) ** .6
                q += n * (.00045 + height * bulge)
                vertices.append(q); fields.append(self.paint(q, digit))
        for j in range(rows - 1):
            for i in range(cols - 1):
                a = j * cols + i
                face = [a, a + 1, a + cols + 1, a + cols]
                if np.dot(np.cross(vertices[face[1]] - vertices[face[0]], vertices[face[2]] - vertices[face[0]]), outward) < 0:
                    face.reverse()
                faces.append(face)
        self.append(name, vertices, faces, fields)
        boundary = list(range(cols)) + [j * cols + cols - 1 for j in range(1, rows)]
        boundary += list(range(rows * cols - 2, (rows - 1) * cols - 1, -1))
        boundary += [j * cols for j in range(rows - 2, 0, -1)]
        self.tube(name + '-sewn-edge', np.array(vertices)[boundary + [boundary[0]]], .0003, digit)

    def tube(self, name, path, radius, digit=None):
        vertices, faces, fields = [], [], []
        for j, p in enumerate(path):
            tangent = unit(path[min(j + 1, len(path) - 1)] - path[max(j - 1, 0)])
            radial = self.dorsal - tangent * np.dot(tangent, self.dorsal)
            if np.linalg.norm(radial) < .1:
                radial = self.radial - tangent * np.dot(tangent, self.radial)
            radial = unit(radial); second = np.cross(tangent, radial)
            for i in range(6):
                angle = i * math.tau / 6
                q = p + radius * (radial * math.cos(angle) + second * math.sin(angle))
                vertices.append(q); fields.append(self.paint(q, digit))
            if j:
                for i in range(6):
                    a = (j - 1) * 6 + i; b = (j - 1) * 6 + (i + 1) % 6
                    faces.append([a, b, b + 6, a + 6])
        self.append(name, vertices, faces, fields)

    def construct(self):
        width = np.linalg.norm(self.head('DEF-f_index.01.' + self.side) - self.head('DEF-f_pinky.01.' + self.side))
        self.panel('selected-knuckle-pad', self.wrist + self.forward * .061, self.forward, self.radial, self.dorsal,
                   .029, width * .76, height=.0021)
        self.panel('selected-back-panel', self.wrist + self.forward * .027, self.forward, self.radial, self.dorsal,
                   .026, width * .68, height=.00065)
        self.panel('selected-palm-grip-pad', self.wrist + self.forward * .043, self.forward, self.radial, -self.dorsal,
                   .042, width * .55, height=.001)
        for digit in DIGITS:
            chain = self.chain(digit)
            for segment in (0, 1, 2):
                a, b = self.head(chain[segment]), self.tail(chain[segment])
                along = unit(b - a)
                across = unit(self.radial - along * np.dot(self.radial, along))
                outward = unit(self.dorsal - along * np.dot(self.dorsal, along))
                # Width is fitted to each actual digit's two radial surfaces.
                mid = (a + b) / 2
                plus, _ = self.surface(mid, across, digit)
                minus, _ = self.surface(mid, -across, digit)
                finger_width = min(.017, np.linalg.norm(plus - minus))
                self.panel(f'{digit}-segment{segment + 1}-leather-panel', mid, along, across, outward,
                           np.linalg.norm(b - a) * .62, finger_width * .48, digit, .00065)
                if segment < 2:
                    # Three narrow articulated ribs sit before the joint.
                    for rib in range(3):
                        c = b - along * (.004 + rib * .0021)
                        path = []
                        for x in np.linspace(-.28, .28, 9):
                            q, n = self.surface(c + across * x * finger_width, outward, digit)
                            path.append(q + n * .0007)
                        self.tube(f'{digit}-joint{segment + 1}-rib{rib + 1}', np.array(path), .00065, digit)
        boundary = self.hand['cuffBoundaryEdges']
        adjacency = {}
        for a, b in boundary:
            adjacency.setdefault(int(a), []).append(int(b)); adjacency.setdefault(int(b), []).append(int(a))
        order = [int(boundary[0, 0])]
        while len(order) < len(adjacency):
            candidates = [x for x in adjacency[order[-1]] if x not in order]
            assert candidates
            order.append(candidates[0])
        ring = self.scaffold[order]
        self.tube('selected-cuff-lip', np.vstack([ring, ring[0]]), .00115)
        # Closure is a sewn, raised band across the back of the actual wrist.
        center = self.wrist + self.hand['cuffProximalAxis'] * .010
        self.panel('selected-cuff-closure-strap', center, self.forward, self.radial, self.dorsal,
                   .012, width * .58, height=.0018)
        obj = mesh_object('GloveProduction.' + self.side, self.vertices, self.faces)
        coefficients = np.asarray(self.fields)
        assert np.max(abs(coefficients.sum(1) - 1)) < 1e-10
        for i, name in enumerate(self.names):
            ids = np.flatnonzero(coefficients[:, i] > 0)
            if len(ids):
                group = obj.vertex_groups.new(name=name)
                for vertex in ids:
                    group.add([int(vertex)], float(coefficients[vertex, i]), 'REPLACE')
        armature = obj.modifiers.new('SharedActual75', 'ARMATURE'); armature.object = self.rig
        obj.parent = self.rig
        obj['selected_source'] = 'painted.glb:890f8693256347156c20f82a62dd79e2145cf511e7a85eb5239089644a20bfea'
        obj['production_status'] = 'UNACCEPTED_AUTHORED_PASS'
        obj['hand_side_independently_constructed'] = self.side
        # UV seams follow topology angle and anatomical part boundaries, and
        # every polygon receives coherent new corner UVs from Blender unwrap.
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=.018)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.uv_layers.active.name = 'SelectedBakeUV'
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


def bake(scene, target, donor, out, material, color_node, mr_node):
    target_material = bpy.data.materials.new('GloveSelectedPBR.' + target.name[-1]); target_material.use_nodes = True
    target.data.materials.append(target_material)
    bsdf = target_material.node_tree.nodes.get('Principled BSDF')
    outputs = {}
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 8
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = .015
    scene.render.bake.max_ray_distance = .030
    scene.render.bake.margin = 10
    # Explicit per-side cage. Left and right bake targets are never combined.
    cage = target.copy(); cage.data = target.data.copy(); cage.name = target.name + '.BakeCage'
    cage.modifiers.clear(); bpy.context.collection.objects.link(cage)
    for v in cage.data.vertices: v.co += v.normal * .015
    scene.render.bake.use_cage = True; scene.render.bake.cage_object = cage.name
    cage.hide_render = True; cage.hide_set(True)
    for kind in ('baseColor', 'metallicRoughness', 'normal'):
        image = bpy.data.images.new(target.name + '.' + kind, width=1024, height=1024, alpha=False)
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
        outputs[kind] = {'path': str(Path(image.filepath_raw).relative_to(ROOT)), 'sha256': sha(image.filepath_raw)}
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out')
    parser.add_argument('--stage', choices=('geometry', 'bake', 'all'), default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = Path(args.out).resolve()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/production-gloves01')
    records = json.loads((HERE / 'inputs.json').read_text())
    paths = {k: ROOT / v['path'] for k, v in records.items()}
    for key, record in records.items(): assert sha(paths[key]) == record['sha256'], ('Changed input', key)
    if args.stage == 'bake':
        report = json.loads((out / 'geometry-report.json').read_text())
        assert report['sourcePins'] == records
        geometry_native = ROOT / report['native']['path']
        assert sha(geometry_native) == report['native']['sha256']
        bpy.ops.wm.open_mainfile(filepath=str(geometry_native))
    else:
        assert not out.exists()
        out.mkdir(parents=True)
        bpy.ops.wm.open_mainfile(filepath=str(paths['nativeMaster']))
    body_obj, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(body_obj.data.vertices) == 10582 and len(rig.data.bones) == 75
    before = body_signature(body_obj, rig)
    arrays = np.load(paths['nativeArrays'])
    if args.stage != 'bake':
        rig.animation_data_clear()
        for bone in rig.pose.bones:
            bone.matrix_basis.identity()
        bpy.context.view_layer.update()
        report = {'acceptedArt': False, 'status': 'AUTHORED_GEOMETRY_COMPLETE_BAKE_PENDING',
                  'sourcePins': records, 'hands': {},
                  'textureResolution': {'selectedPaintSource': 4096, 'firstLookDerivative': 1024,
                                        'final4KMasterBake': 'NOT_EXECUTED'},
                  'limits': ['Geometry checkpoint has no accepted textured appearance.',
                             'Approximate flex review is not finite handlebar grip calibration.',
                             'No full lining fabrication or anatomical art acceptance claimed.',
                             'Selected bake and played inspection remain pending.']}
        for side in ('R', 'L'):
            author = HandAuthor(side, np.load(paths['hand' + side]), arrays, rig)
            target = author.construct()
            report['hands'][side] = {'vertices': len(target.data.vertices), 'polygons': len(target.data.polygons),
                                    'authoredFeatures': author.features, 'textures': {},
                                    'actualTargetGeometry': records['hand' + side], 'donorAppearanceReflected': side == 'L',
                                    'sharedArmature': rig.name, 'newUV': target.data.uv_layers.active.name}
        report['bodyAndRestBefore'] = before
        report['bodyAndRestAfter'] = body_signature(body_obj, rig)
        assert report['bodyAndRestAfter'] == before
        report['reviewAction'] = motion(rig, json.loads(paths['actualDigitControls'].read_text()))
        bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = 80; bpy.context.scene.frame_set(1)
        # Both complete gloves, semantic skin and review action survive any
        # later donor alignment/bake timeout or memory guard termination.
        save_checkpoint(out, 'authored-geometry.blend', report, 'geometry-report.json')
    else:
        assert before == report['bodyAndRestAfter']
    if args.stage == 'geometry':
        return
    report['geometryNative'] = dict(report['native'])
    source = np.load(paths['sourceDetailCage']); dense = np.load(paths['denseSelected'])
    material, color, mr = donor_material(paths)
    for side in ('R', 'L'):
        author = HandAuthor(side, np.load(paths['hand' + side]), arrays, rig)
        target = bpy.data.objects['GloveProduction.' + side]
        donor = align_dense(author, source, dense, material)
        textures = bake(bpy.context.scene, target, donor, out, material, color, mr)
        report['hands'][side]['textures'] = textures
        report['status'] = 'FIRST_LOOK_1024_BAKE_' + side + '_COMPLETE'
        assert body_signature(body_obj, rig) == before
        save_checkpoint(out, 'bake-progress.blend', report, 'bake-progress.json')
    report['bodyAndRestAfter'] = body_signature(body_obj, rig)
    assert report['bodyAndRestAfter'] == before
    report['status'] = 'ONE_AUTHORED_PAIR_WITH_FIRST_LOOK_1024_BAKE_FOR_PARENT_REVIEW'
    report['limits'] = ['Unaccepted until parent plays textured motion and compares selected source.',
                        'Approximate flex review is not finite handlebar grip calibration.',
                        'No full lining fabrication or anatomical art acceptance claimed.',
                        'Bake misses, ray contamination and seams require actual textured inspection.',
                        'Actual1024 first-look bake does not satisfy a final4K master-bake requirement.']
    save_checkpoint(out, 'selected-articulated-gloves.blend', report, 'report.json')
    for key, record in records.items(): assert sha(paths[key]) == record['sha256'], ('Input changed', key)
    print(json.dumps({'status': report['status'], 'native': report['native'], 'bodyAndRestUnchanged': True}))


if __name__ == '__main__':
    main()
