"""Prepared bounded read-only native rest/turn244 packed and fan snapshot.

No saves, renders, exports or field/normal/bind changes. Actual decoded corner
normals are captured alongside true geometric crosses, packed INT16_2D rows,
smooth-face flags, sharp edges and independently reconstructed connectivity.
RNA polygon_normals are deliberately never used as geometric normals.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix

p = argparse.ArgumentParser(description=__doc__)
for key in ('source', 'fields', 'intake', 'out'):
    p.add_argument('--' + key, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, fields_path, intake, out = [Path(getattr(a, key)).resolve() for key in ('source', 'fields', 'intake', 'out')]
assert not out.exists()
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
assert sha(source) == '66c45ab5a76fe592b0b284a5a96dc3e6ba1f74b2854e5dae849aaff03f43bb77'
assert sha(fields_path) == 'ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a'
report_path = intake / 'report.json'
assert sha(report_path) == '1d19d3d4abbaf27258b296ca0f4307d705f3c4ed4a0c1d4cc479020c5d6a39d4'
report = json.loads(report_path.read_text())
pins = {str(x): sha(x) for x in (source, fields_path, report_path)}
fields = np.load(fields_path)
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Finish rig']
names = [bone.name for bone in rig.data.bones]
assert names == fields['boneNames'].tolist() and len(names) == 51
bind_before = np.array([bone.matrix_local for bone in rig.data.bones])
rig_world_before = np.array(rig.matrix_world)
objects = {kind: bpy.data.objects['Finish head ' + kind.upper()] for kind in ('full', 'four')}
corner, vertex = 196454, 45084

def normalized(vector):
    vector = np.array(vector, float)
    assert np.isfinite(vector).all()
    length = np.linalg.norm(vector)
    assert length > 0 and np.isfinite(length)
    return vector / length

def raw(mesh):
    attr = mesh.attributes['custom_normal']
    assert attr.domain == 'CORNER' and attr.data_type == 'INT16_2D'
    rows = np.empty(len(attr.data) * 2, np.int32)
    attr.data.foreach_get('value', rows)
    return rows.reshape(-1, 2)

def stable_source_digest(obj):
    mesh = obj.data
    payload = {'xyz': [list(v.co) for v in mesh.vertices], 'polygons': [list(p.vertices) for p in mesh.polygons],
               'decodedNormals': [list(n.vector) for n in mesh.corner_normals],
               'packedSHA256': hashlib.sha256(raw(mesh).tobytes()).hexdigest(),
               'uvs': [[list(row.uv) for row in layer.data] for layer in mesh.uv_layers],
               'memberships': [[(item.group, item.weight) for item in v.groups] for v in mesh.vertices],
               'groups': [group.name for group in obj.vertex_groups], 'world': np.array(obj.matrix_world).tolist()}
    return hashlib.sha256(json.dumps(payload, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

before = {kind: stable_source_digest(obj) for kind, obj in objects.items()}
for kind, obj in objects.items():
    actual = np.zeros((len(obj.data.vertices), 51), np.float32)
    for v in obj.data.vertices:
        for item in v.groups:
            name = obj.vertex_groups[item.group].name
            if name in names:
                actual[v.index, names.index(name)] = item.weight
    assert np.array_equal(actual, fields['head' + kind.title() + 'Weights'])
    obj.data.calc_loop_triangles()
    assert np.array_equal(np.array([list(t.vertices) for t in obj.data.loop_triangles]), fields['headTriangles'])
    assert not obj.data.shape_keys
    active = [m for m in obj.modifiers if m.show_viewport]
    assert len(active) == 1 and active[0].type == 'ARMATURE' and active[0].object == rig and not active[0].use_deform_preserve_volume

def newell(points):
    points = np.array(points, np.float32)
    total = np.zeros(3, np.float32)
    terms = []
    for i in range(len(points)):
        previous, current = points[i - 1], points[i]
        term = np.array([(previous[k] - current[k]) * (previous[(k + 1) % 3] + current[(k + 1) % 3]) for k in (1, 2, 0)], np.float32)
        total += term
        terms.append(term.tolist())
    return {'terms': terms, 'sum': total.tolist(), 'unitTrueGeometricNormal': normalized(total).tolist()}

def read_mesh(mesh, world):
    assert mesh.loops[corner].vertex_index == vertex
    packed = raw(mesh)
    incident = [poly for poly in mesh.polygons if vertex in poly.vertices]
    by_id = {poly.index: poly for poly in incident}
    edge_faces = {}
    for poly in incident:
        for loop in poly.loop_indices:
            edge = mesh.loops[loop].edge_index
            if vertex in mesh.edges[edge].vertices:
                edge_faces.setdefault(edge, []).append(poly.index)
    attr = mesh.attributes.get('sharp_edge')
    is_sharp = lambda e: bool(attr.data[e].value) if attr else False
    adjacency = {poly.index: set() for poly in incident}
    for edge, face_ids in edge_faces.items():
        if len(face_ids) == 2 and not is_sharp(edge) and all(by_id[f].use_smooth for f in face_ids):
            adjacency[face_ids[0]].add(face_ids[1])
            adjacency[face_ids[1]].add(face_ids[0])
    target = next(poly for poly in incident if corner in poly.loop_indices)
    fan, stack = set(), [target.index]
    while stack:
        face = stack.pop()
        if face in fan:
            continue
        fan.add(face)
        stack.extend(adjacency[face] - fan)
    polygons = []
    aggregate_cross, aggregate_newell = np.zeros(3), np.zeros(3)
    custom_rows = []
    for poly in incident:
        ids, loops = list(poly.vertices), list(poly.loop_indices)
        assert len(ids) == 3
        xyz = np.array([mesh.vertices[v].co[:] for v in ids], float)
        at = ids.index(vertex)
        incoming = normalized(xyz[(at - 1) % 3] - xyz[at])
        outgoing = normalized(xyz[(at + 1) % 3] - xyz[at])
        angle = float(np.arccos(np.clip(np.dot(incoming, outgoing), -1, 1)))
        cross = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
        newell_data = newell(xyz)
        if poly.index in fan:
            aggregate_cross += angle * normalized(cross)
            aggregate_newell += angle * np.array(newell_data['unitTrueGeometricNormal'])
            custom_rows.append(packed[loops[at]])
        polygons.append({'polygon': poly.index, 'nativeVertexIDs': ids, 'cornerIDs': loops,
            'inReconstructedTargetFan': poly.index in fan, 'smooth': poly.use_smooth,
            'localXYZ': xyz.tolist(), 'trueCrossFloat64': cross.tolist(), 'trueArea2M2': float(np.linalg.norm(cross)),
            'trueNewellFloat32': newell_data, 'cornerAngleFloat64Acos': angle,
            'packedCustomNormals': packed[loops].tolist(), 'decodedLocalNormals': [list(mesh.corner_normals[l].vector) for l in loops]})
    result = {'corner': corner, 'nativeVertex': vertex, 'targetPolygon': target.index,
        'targetPacked': packed[corner].tolist(), 'targetDecodedLocalNormal': list(mesh.corner_normals[corner].vector),
        'objectWorldRows': np.array(world).tolist(), 'incidentPolygons': polygons,
        'incidentEdges': [{'edge': e, 'nativeVertexIDs': list(mesh.edges[e].vertices), 'sharp': is_sharp(e), 'incidentFaces': faces} for e, faces in edge_faces.items()],
        'reconstructedTargetSmoothFanPolygons': sorted(fan),
        'averageFanPackedTruncated': np.trunc(np.mean(custom_rows, axis=0)).astype(int).tolist(),
        'automaticTrueCrossAngleWeightedProxyLocal': normalized(aggregate_cross).tolist(),
        'automaticTrueNewellAngleWeightedProxyLocal': normalized(aggregate_newell).tolist(),
        'sourcePointReference': fields['headAttributeEdgeSources'][vertex].tolist(),
        'sourceCornerReference': fields['headCornerAttributeEdgeSources'][corner].tolist(),
        'limits': ['Connectivity reconstructed from actual smooth faces, sharp edges and manifold adjacency; traversal order/frame space still requires exact source decoder validation.',
                   'Proxy geometry uses true crosses or explicit Float32 Newell, never RNA custom-normal polygon_normals.',
                   'Angle weights use float64 acos, not Blender fast approximation; native decoded corner remains authority.']}
    return result

source_states = {kind: read_mesh(obj.data, obj.matrix_world) for kind, obj in objects.items()}
rig.animation_data_clear()
rig.hide_viewport = False
rig.hide_set(False)
for bone in rig.pose.bones:
    for constraint in bone.constraints:
        constraint.mute = True
for obj in objects.values():
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.animation_data_clear()
records = []
for index in (0, 244):
    sample_path = intake / ('sample-%04d.json.gz' % index)
    pin = next(x for x in report['samples'] if x['path'] == sample_path.name)
    assert sha(sample_path) == pin['sha256']
    pins[str(sample_path)] = sha(sample_path)
    sample = json.loads(gzip.decompress(sample_path.read_bytes()))
    for name, pose in sample['poseBasisBlender'].items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis = Matrix.Identity(4)
        bone.location, bone.rotation_quaternion, bone.scale = pose['location'], pose['quaternionWXYZ'], pose['scale']
    bpy.context.view_layer.update()
    actual_pose = {name: {'location': list(rig.pose.bones[name].location), 'quaternionWXYZ': list(rig.pose.bones[name].rotation_quaternion), 'scale': list(rig.pose.bones[name].scale)} for name in names}
    assert actual_pose == sample['poseBasisBlender']
    skin = np.array([rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted() for name in names])
    assert np.array_equal(skin, sample['skinNativeRows'])
    row = {'index': index, 'case': sample['case'], 'exactSavedPoseAndSkinRows': True, 'skinNativeRows': skin.tolist(), 'fields': {}}
    for kind, obj in objects.items():
        e = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = e.to_mesh()
        captured = read_mesh(mesh, e.matrix_world)
        for poly in captured['incidentPolygons']:
            for v in poly['nativeVertexIDs']:
                world_point = np.array(list(e.matrix_world @ mesh.vertices[v].co))
                assert np.array_equal(world_point, np.array(sample['parts']['head'][kind]['xyzWorld'][v]))
        actual_world_normal = e.matrix_world.to_3x3().inverted().transposed() @ mesh.corner_normals[corner].vector
        actual_world_normal = normalized(actual_world_normal)
        assert np.array_equal(actual_world_normal, np.array(sample['parts']['head'][kind]['normalWorldCorners'][corner]))
        captured['targetDecodedWorldNormalExactlyExistingCapture'] = True
        e.to_mesh_clear()
        row['fields'][kind] = captured
    records.append(row)
assert before == {kind: stable_source_digest(obj) for kind, obj in objects.items()}
assert np.array_equal(bind_before, np.array([bone.matrix_local for bone in rig.data.bones]))
assert np.array_equal(rig_world_before, np.array(rig.matrix_world))
assert pins == {name: sha(name) for name in pins}
result = {'status': 'UNACCEPTED_READ_ONLY_BODY06_SOURCE_REST_AND_TURN244_PACKED_FAN_SNAPSHOT',
    'recipeSHA256': sha(__file__), 'inputPins': pins, 'blender': bpy.app.version_string,
    'sourceBasisRest': source_states, 'records': records, 'nativeSourceMeshDataRestBindsWorldExactAfterInMemoryPoseDiagnostics': True,
    'sourcePackedDecodedXYZUVAndRawFieldDigestBeforeAfter': before,
    'limits': ['No save/render/export/field/normal/source mutation or new animation stream.',
               'Source basis rest and two exact previously captured pose payloads only; no unmeasured intervening motion acceptance.',
               'Packed rows and actual edge/smooth topology are captured; exact corner fan-space decode is subsequent independent analysis.',
               'No general loft fold, shader parity tolerance, art or release certificate.']}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print('BODY06_PACKED_FAN_SNAPSHOT_READY', flush=True)
