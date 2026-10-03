"""Independent anatomical body and fitted sweatshirt control, not a rider release.

Run installed Blender headlessly. Native MHCLO fits a new canonical baked body;
no damaged rider underarm vertex, topology, bind or corrective is reused.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import addon_utils
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
parser.add_argument('--evidence', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out, evidence = Path(args.out).resolve(), Path(args.evidence).resolve()
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
if (out / 'control.blend').exists():
    raise RuntimeError('Frozen control exists; choose a new round directory')

addon = Path.home() / 'Library/Application Support/Blender/5.1/extensions/user_default'
asset_dir = Path.home() / 'Library/Application Support/Blender/5.1/extensions/.user/user_default/mpfb/data/clothes/male_casualsuit02'
donor_path = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


sources = [addon / 'mpfb/data/3dobjs/base.obj',
           addon / 'mpfb/data/rigs/standard/rig.game_engine.json',
           addon / 'mpfb/data/rigs/standard/weights.game_engine.json',
           asset_dir / 'male_casualsuit02.mhclo',
           asset_dir / 'male_casualsuit02.obj', donor_path]
pins = {str(p): sha(p) for p in sources}
assert pins[str(sources[0])] == '8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.extensions.repos.new(
    name='Anatomical foundation read-only source', module='foundation_mpfb',
    custom_directory=str(addon))
addon_utils.enable('bl_ext.foundation_mpfb.mpfb', default_set=True, persistent=False)
from bl_ext.foundation_mpfb.mpfb.services.humanservice import HumanService
from bl_ext.foundation_mpfb.mpfb.services.targetservice import TargetService

macro = TargetService.get_default_macro_info_dict()
macro.update(gender=1., age=.5, muscle=.55, weight=.5, proportions=.5,
             height=.5, race={'asian': 0., 'caucasian': 1., 'african': 0.})
body = HumanService.create_human(mask_helpers=True, detailed_helpers=True,
    extra_vertex_groups=True, feet_on_ground=True, scale=.1, macro_detail_dict=macro)
active_keys = [{'name': k.name, 'value': k.value} for k in body.data.shape_keys.key_blocks
               if k.name != 'Basis' and abs(k.value) > 1e-8]
TargetService.bake_targets(body)
rig = HumanService.add_builtin_rig(body, 'game_engine', import_weights=True)
cloth = HumanService.add_mhclo_asset(str(asset_dir / 'male_casualsuit02.mhclo'),
    body, asset_type='Clothes', subdiv_levels=0, material_type='NONE',
    set_up_rigging=True, interpolate_weights=True, import_subrig=False, import_weights=False)

# Fit occurs with all native helper vertices present. Only then remove helpers.
body_group = body.vertex_groups['body'].index
body_ids = {v.index for v in body.data.vertices
            if any(g.group == body_group and g.weight > .5 for g in v.groups)}
native_height = max(body.data.vertices[i].co.z for i in body_ids)
scale = 1.822571873664856 / native_height
bm = bmesh.new()
bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
ancestry = bm.verts.layers.int.new('hm08_source_vertex')
for v in bm.verts:
    v[ancestry] = v.index
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in body_ids], context='VERTS')
bm.to_mesh(body.data)
bm.free()
for mod in list(body.modifiers):
    if mod.type == 'MASK':
        body.modifiers.remove(mod)
body.name = 'Canonical anatomical body, baked adult hm08'
rig.name = 'Independent anatomical foundation rig'


def components(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    unseen = set(bm.verts)
    groups = []
    while unseen:
        seed = next(iter(unseen))
        comp, todo = {seed}, [seed]
        unseen.remove(seed)
        while todo:
            for edge in todo.pop().link_edges:
                for v in edge.verts:
                    if v in unseen:
                        unseen.remove(v)
                        comp.add(v)
                        todo.append(v)
        groups.append(sorted(v.index for v in comp))
    bm.free()
    return sorted(groups, key=lambda ids: (-len(ids), ids[0]))


def retain(obj, ids):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    keep = set(ids)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


cloth_components = components(cloth.data)
assert [len(g) for g in cloth_components] == [1250, 886]
pants = cloth.copy()
pants.data = cloth.data.copy()
bpy.context.collection.objects.link(pants)
retain(pants, cloth_components[1])
retain(cloth, cloth_components[0])
cloth.name = 'Separate fitted sweatshirt control, hood not constructed'
pants.name = 'Separate fitted native trousers control'
boxers = pants.copy()
boxers.data = pants.data.copy()
bpy.context.collection.objects.link(boxers)
bm = bmesh.new()
bm.from_mesh(boxers.data)
# Opaque modest coverage with independent waist/two thigh openings, no caps.
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
    dist=1e-7, plane_co=(0, 0, .64 / scale), plane_no=(0, 0, 1), clear_inner=True)
bm.to_mesh(boxers.data)
bm.free()
boxers.name = 'Opaque boxer fitting garment'

# One process-local adapter applies to body, garment and skeleton together.
# MPFB uses front=-Y, up=Z. +90 degrees around Z makes game front=+X.
rotation = Matrix.Rotation(math.pi / 2, 4, 'Z')
fit = rotation @ Matrix.Scale(scale, 4)
for obj in [body, cloth, pants, boxers]:
    obj.data.transform(fit)
    obj.data.update()
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones:
    bone.head = fit @ bone.head
    bone.tail = fit @ bone.tail
    bone.align_roll(rotation.to_3x3() @ bone.z_axis)
# Runtime owns19named roles. Remove an unowned intermediate spine and Root.
rig.data.edit_bones['spine_03'].parent = rig.data.edit_bones['spine_01']
rig.data.edit_bones['pelvis'].parent = None
for name in ['spine_02', 'Root']:
    rig.data.edit_bones.remove(rig.data.edit_bones[name])
bpy.ops.object.mode_set(mode='OBJECT')
base_map = {'spine_01': 'spine', 'spine_03': 'chest', 'neck_01': 'neck'}
side_map = {'clavicle': 'shoulder', 'upperarm': 'upperArm', 'lowerarm': 'forearm',
            'hand': 'hand', 'thigh': 'thigh', 'calf': 'shin', 'foot': 'foot'}
rename = dict(base_map)
for bone in rig.data.bones:
    if bone.name.endswith(('_l', '_r')):
        stem, side = bone.name.rsplit('_', 1)
        # Native l lies in game -Z. Map sides by the actual game +Z-left contract.
        rename[bone.name] = side_map.get(stem, stem) + ('.R' if side == 'l' else '.L')
for obj in [body, cloth, pants, boxers]:
    old = obj.vertex_groups.get('spine_02')
    target = obj.vertex_groups.get('spine_01')
    if old and target:
        for v in obj.data.vertices:
            weights = {g.group: g.weight for g in v.groups}
            if old.index in weights:
                target.add([v.index], weights[old.index] + weights.get(target.index, 0), 'REPLACE')
        obj.vertex_groups.remove(old)
    for group in obj.vertex_groups:
        if group.name in rename:
            group.name = rename[group.name]
for old, new in rename.items():
    rig.data.bones[old].name = new
rig.data.pose_position = 'POSE'
root = bpy.data.objects.new('Foundation file frame, game x0.65', None)
bpy.context.collection.objects.link(root)
root.location.x = .65
rig.parent = root
for obj in [body, cloth, pants, boxers]:
    obj.parent = rig
    obj.matrix_parent_inverse = Matrix.Identity(4)
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.object = rig
            mod.use_deform_preserve_volume = False  # Explicit runtime LBS.


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .7
    return mat


for obj, mat in [(body, material('Anatomical gray fitting base', (.4, .4, .4))),
                 (cloth, material('Flat mustard structural control', (.6, .32, .035))),
                 (pants, material('Flat denim structural control', (.06, .11, .2))),
                 (boxers, material('Opaque modest boxers', (.035, .04, .055)))]:
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for f in obj.data.polygons:
        f.use_smooth = True
boxers.hide_render = True


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    boundary = {e for e in bm.edges if e.is_boundary}
    loops = []
    while boundary:
        e = next(iter(boundary))
        verts, edges, todo = set(e.verts), {e}, list(e.verts)
        boundary.remove(e)
        while todo:
            for edge in todo.pop().link_edges:
                if edge in boundary:
                    boundary.remove(edge)
                    edges.add(edge)
                    for v in edge.verts:
                        if v not in verts:
                            verts.add(v)
                            todo.append(v)
        loops.append({'vertices': len(verts), 'edges': len(edges),
            'regular': all(sum(e.is_boundary for e in v.link_edges) == 2 for v in verts),
            'boundsBlenderM': [[min(v.co[i] for v in verts) for i in range(3)],
                               [max(v.co[i] for v in verts) for i in range(3)]]})
    report = {'vertices': len(bm.verts), 'polygons': len(bm.faces),
        'connectedComponents': len(components(obj.data)),
        'boundaryEdges': sum(e.is_boundary for e in bm.edges),
        'nonmanifoldBeyondBoundary': sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
        'looseVertices': sum(not v.link_faces for v in bm.verts), 'boundaryLoops': loops}
    bm.free()
    return report


def sample_mesh(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vertices = np.array([evaluated.matrix_world @ v.co for v in mesh.vertices])
    faces = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=np.int32)
    evaluated.to_mesh_clear()
    return vertices, faces


report = {'status': 'UNACCEPTED anatomy + independent fitted sweatshirt control; no hood/likeness acceptance',
    'sources': pins, 'macro': macro, 'bakedMacroShapeKeys': active_keys,
    'uniformScale': scale, 'nativeBodyHeightM': native_height,
    'nativeToFile': {'rotationZRadians': math.pi / 2, 'rootX': .65,
                    'fileSpace': '+Xforward,+Yup,+Zgame-left; metres; glTF'},
    'sideRenameByMeasuredCoordinates': rename,
    'topology': {o.name: topology(o) for o in [body, cloth, pants, boxers]},
    'bodyVertexAncestry': 'hm08_source_vertex POINT integer layer; helpers removed after fitting',
    'generatedHead': 'immutable donor retained separately; integration pending',
    'limits': ['No9/10score; parent judges.', 'Sweatshirt has no hood/pocket detail; control only.',
        'Native anatomy is fitting source, not final identity.', 'No production change or GPU model job.',
        'No sourceA/C19 weights/inverse binds/correctives imported.',
        'No garment clearance, contact, shoulder deformation or riding pass implied by topology.']}
assert report['topology'][body.name]['vertices'] == 13380
assert report['topology'][body.name]['boundaryEdges'] == 0
assert report['topology'][cloth.name]['connectedComponents'] == 1

# Explicit generic held-out FK stress poses, zero morphs, no correctives.
def world_axis_q(name, axis, radians):
    bone = rig.data.bones[name]
    local_axis = bone.matrix_local.to_3x3().inverted() @ Vector(axis)
    return Quaternion(local_axis.normalized(), radians)


poses = {}
def add_pose(name, rotations):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    for bone, axis, degrees in rotations:
        rig.pose.bones[bone].rotation_quaternion = world_axis_q(bone, axis, math.radians(degrees))
    bpy.context.view_layer.update()
    poses[name] = {pb.name: {'location': list(pb.location),
        'rotationQuaternionWXYZ': list(pb.rotation_quaternion), 'scale': list(pb.scale)}
        for pb in rig.pose.bones}


add_pose('native_A', [])
add_pose('neutral', [('upperArm.L', (1, 0, 0), -35), ('upperArm.R', (1, 0, 0), 35)])
add_pose('T', [('upperArm.L', (1, 0, 0), 45), ('upperArm.R', (1, 0, 0), -45)])
add_pose('forward', [('upperArm.L', (0, 1, 0), 65), ('upperArm.R', (0, 1, 0), 65)])
add_pose('bent_elbows', [('forearm.L', (0, 1, 0), 65), ('forearm.R', (0, 1, 0), 65)])
add_pose('raised', [('upperArm.L', (1, 0, 0), 120), ('upperArm.R', (1, 0, 0), -120)])
add_pose('asymmetric', [('upperArm.L', (1, 0, 0), 105), ('forearm.R', (0, 1, 0), 70)])

for name, trs in poses.items():
    for bone, row in trs.items():
        rig.pose.bones[bone].rotation_quaternion = row['rotationQuaternionWXYZ']
    bpy.context.view_layer.update()
    vv, ff = sample_mesh(cloth)
    np.savez_compressed(out / (name + '-cloth.npz'), verticesBlenderWorldM=vv, triangles=ff)
    bb, bf = sample_mesh(body)
    np.savez_compressed(out / (name + '-body.npz'), verticesBlenderWorldM=bb, triangles=bf)

# A complete animation sequence measures native pose changes and export playback.
sequence = ['native_A', 'neutral', 'T', 'native_A', 'forward', 'bent_elbows', 'raised', 'asymmetric', 'native_A']
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 193
for i, name in enumerate(sequence):
    frame = 1 + i * 24
    for bone, row in poses[name].items():
        pb = rig.pose.bones[bone]
        pb.rotation_quaternion = row['rotationQuaternionWXYZ']
        pb.keyframe_insert('rotation_quaternion', frame=frame, group=bone)
rig.animation_data.action.name = 'foundation_stress'
scene.frame_set(1)
report['poseManifest'] = {'poses': poses, 'sequence': sequence, 'frames': list(range(1, 194, 24)),
    'fps': 24, 'durationS': 8, 'morphs': 0, 'correctives': 0,
    'warning': 'Generic FK stress, not accepted T-angle accuracy or bike choreography; independent rig only.'}
report['restBonesBlenderLocalM'] = {b.name: {'head': list(b.head_local), 'tail': list(b.tail_local),
    'parent': b.parent.name if b.parent else None,
    'matrixRows': [list(row) for row in b.matrix_local]} for b in rig.data.bones}
report['sourcesAfter'] = {str(p): sha(p) for p in sources}
assert report['sourcesAfter'] == pins
report['recipeSHA256'] = sha(__file__)
bpy.ops.object.select_all(action='DESELECT')
for obj in [root, rig, body, cloth, pants]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'control.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out / 'control.glb'), export_format='GLB',
    use_selection=True, export_yup=True, export_animations=True, export_force_sampling=True,
    export_frame_range=True, export_extras=True)
report['exports'] = {name: {'sha256': sha(out / name), 'bytes': (out / name).stat().st_size}
                     for name in ['control.blend', 'control.glb']}
(evidence / 'construction.json').write_text(json.dumps(report, indent=2) + '\n')
print('FOUNDATION_CONTROL_FROZEN', json.dumps(report['exports']), flush=True)
