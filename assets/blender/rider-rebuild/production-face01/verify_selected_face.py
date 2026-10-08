"""Fresh-process readback of the saved native75 face derivative; no rendering.

Compares actual native02 before/after and raw selected donor corner arrays.
No canonicalization, garment assembly, field rewrite or positive art judgment.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG = json.loads((HERE / 'controls.json').read_text())
CUT = CONFIG['construction']['bodyCutNativeZ']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def source_path(name):
    row = CONFIG['inputs'][name]
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], ('Changed source', name)
    return path


def capture(body, rig, protected_ids):
    ids = [item.value for item in body.data.attributes['_SOURCE_VERTEX_ID'].data]
    groups = {g.index: g.name for g in body.vertex_groups}
    rows = {}
    for v in body.data.vertices:
        if ids[v.index] in protected_ids:
            assert ids[v.index] not in rows
            rows[ids[v.index]] = (list(v.co), sorted((groups[g.group], g.weight) for g in v.groups))
    assert set(rows) == protected_ids, 'Lost an original protected body row'
    faces = {}
    uv = body.data.uv_layers.active.data
    for p in body.data.polygons:
        if not all(ids[i] in protected_ids for i in p.vertices):
            continue
        corners = [(ids[body.data.loops[i].vertex_index], tuple(uv[i].uv)) for i in p.loop_indices]
        offset = min(range(len(corners)), key=lambda i: corners[i][0])
        corners = corners[offset:] + corners[:offset]
        key = tuple(c[0] for c in corners)
        assert key not in faces
        faces[key] = (p.material_index, corners)
    rest = [(b.name, b.parent.name if b.parent else None,
             tuple(b.head_local), tuple(b.tail_local),
             tuple(tuple(row) for row in b.matrix_local), b.use_connect, b.use_deform)
            for b in rig.data.bones]
    modifiers = [(m.name, m.type, m.show_viewport, m.show_render,
                  m.use_deform_preserve_volume if m.type == 'ARMATURE' else None,
                  m.object.name if m.type == 'ARMATURE' else None)
                 for m in body.modifiers]
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    assert not rig.constraints and all(not pb.constraints for pb in rig.pose.bones)
    assert rig.animation_data is None
    assert all(pb.matrix_basis.is_identity for pb in rig.pose.bones)
    return rows, faces, rest, modifiers


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out == ROOT / CONFIG['execution']['out']
    output = out / 'independent-verification.json'
    assert not output.exists(), 'Never overwrite an independent receipt'
    inputs = {name: source_path(name) for name in CONFIG['inputs']}
    report = json.loads((out / 'report.json').read_text())
    receipt = json.loads((out / 'input-receipt.json').read_text())
    assert receipt['inputs'] == CONFIG['inputs']
    for row in receipt['recipes']:
        assert sha(ROOT / row['path']) == row['sha256']
    candidate = ROOT / report['candidate']['path']
    assert candidate == out / 'selected-face-native75.blend'
    assert sha(candidate) == report['candidate']['sha256']
    arrays = dict(np.load(inputs['arrays']))
    names = arrays['jointNames'].tolist()
    protected_ids = set(map(int, arrays['nativeSourceVertexIds'][arrays['vertices'][:, 2] < CUT]))
    assert len(protected_ids) == 6933 and min(protected_ids) >= 0 and max(protected_ids) < 10582
    bpy.ops.wm.open_mainfile(filepath=str(inputs['native']))
    original_body, original_rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert len(original_body.data.vertices) == 10582 and len(original_rig.data.bones) == 75
    original = capture(original_body, original_rig, protected_ids)
    assert len(original[0]) == 6933
    bpy.ops.wm.open_mainfile(filepath=str(candidate))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert set(bpy.data.objects.keys()) == {'RiderBody', 'RiderSkeleton'}
    actual = capture(body, rig, protected_ids)
    assert actual == original, 'Below-cut rows/polygons/UV, all75 rest or body operators changed'
    source_ids = [item.value for item in body.data.attributes['_SOURCE_VERTEX_ID'].data]
    lookup = {identity: v for identity, v in zip(source_ids, body.data.vertices) if identity >= 0}
    assert len(lookup) == sum(identity >= 0 for identity in source_ids), 'Duplicate positive source ID'
    groups = {g.index: g.name for g in body.vertex_groups}
    hand_ids = np.flatnonzero(arrays['newFieldBlendAlpha'] > 0)
    assert len(hand_ids) == 1446 and np.all(arrays['vertices'][hand_ids, 2] < CUT)
    for identity in hand_ids:
        vertex = lookup[int(identity)]
        assert np.array_equal(vertex.co, arrays['vertices'][identity])
        coefficients = np.zeros(75, dtype=np.float32)
        for g in vertex.groups:
            coefficients[names.index(groups[g.group])] = g.weight
        assert np.array_equal(coefficients, arrays['nativeCoefficients'][identity])
    for i, name in enumerate(names):
        b = rig.data.bones[name]
        assert np.array_equal(b.head_local, arrays['jointHeads'][i])
        assert np.array_equal(b.tail_local, arrays['jointTails'][i])
        assert np.array_equal(b.matrix_local, arrays['jointMatrices'][i])
    raw = inputs['donor'].read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size]); binary = raw[28 + size:]

    def accessor(index):
        item = doc['accessors'][index]; view = doc['bufferViews'][item['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[item['componentType']]
        count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
        width = np.dtype(dtype).itemsize
        return np.ndarray((item['count'], count), dtype=dtype, buffer=binary,
                          offset=view.get('byteOffset', 0) + item.get('byteOffset', 0),
                          strides=(view.get('byteStride', width * count), width))

    node = next(n for n in doc['nodes'] if n.get('name') == 'textured')
    primitives = doc['meshes'][node['mesh']]['primitives']
    point_ids = {}
    for part, primitive in enumerate(primitives):
        for index, point in enumerate(accessor(primitive['attributes']['POSITION'])):
            point_ids.setdefault(tuple(float(x) for x in point), 1000000 + part * 100000 + index)
    polygons = {item.value: p for item, p in zip(body.data.attributes['SelectedSourceFace'].data, body.data.polygons)
                if item.value >= 0}
    uv = body.data.uv_layers.active.data; normals = body.data.corner_normals
    scale = CONFIG['construction']['uniformScale']
    errors = np.zeros(3); protected = 0
    for part, primitive in enumerate(primitives):
        points = accessor(primitive['attributes']['POSITION'])
        source_uv = accessor(primitive['attributes']['TEXCOORD_0'])
        source_normals = accessor(primitive['attributes']['NORMAL'])
        for index, triangle in enumerate(accessor(primitive['indices']).reshape(-1, 3)):
            if not all(points[int(i)][1] > 1.56 + 1e-5 for i in triangle):
                continue
            if len({tuple(points[int(i)]) for i in triangle}) < 3:
                continue
            polygon = polygons[part * 1000000 + index]
            assert len(polygon.vertices) == 3
            for loop, i in zip(polygon.loop_indices, triangle):
                i = int(i); point = points[i]; n = source_normals[i]
                v = body.data.vertices[body.data.loops[loop].vertex_index]
                assert source_ids[v.index] == point_ids[tuple(float(x) for x in point)]
                expected = Vector((-point[2] * scale, -(point[0] - .65) * scale, point[1] * scale))
                errors[0] = max(errors[0], (v.co - expected).length)
                errors[1] = max(errors[1], (uv[loop].uv - Vector((float(source_uv[i][0]), 1 - float(source_uv[i][1])))).length)
                errors[2] = max(errors[2], (normals[loop].vector - Vector((-n[2], -n[0], n[1])).normalized()).length)
            protected += 1
    print(json.dumps({'protectedDonorTriangles': protected,
                      'actualPositionUVNormalMaximumErrors': errors.tolist()}), flush=True)
    assert protected == 66364 and np.all(errors < [2e-7, 2e-7, 2e-6]), ('Actual donor readback errors', protected, errors.tolist())
    expected_skin = report['selectedFace']['sourceSampledSkinLinearRGB']
    material = body.data.materials[0]
    actual_skin = list(material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value)[:3]
    assert np.max(abs(np.asarray(actual_skin) - expected_skin)) < 3e-8
    assert np.max(abs(np.asarray(list(material.diffuse_color)[:3]) - expected_skin)) < 3e-8
    packed_images = {node.image.name: hashlib.sha256(node.image.packed_file.data).hexdigest()
                     for mat in body.data.materials for node in mat.node_tree.nodes
                     if node.type == 'TEX_IMAGE' and node.image and node.image.packed_file}
    assert packed_images, 'Genuine selected source PBR must remain packed'
    edges = {}; adjacent = [set() for _ in body.data.vertices]
    for p in body.data.polygons:
        vertices = list(p.vertices)
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            edges.setdefault(tuple(sorted((a, b))), []).append((a, b))
            adjacent[a].add(b); adjacent[b].add(a)
    assert all(len(rows) == 2 and rows[0] == rows[1][::-1] for rows in edges.values())
    seen = {0}; pending = [0]
    while pending:
        for vertex in adjacent[pending.pop()] - seen:
            seen.add(vertex); pending.append(vertex)
    assert len(seen) == len(body.data.vertices)
    for name in CONFIG['inputs']:
        source_path(name)
    result = {'accepted': False, 'status': 'INDEPENDENT_SAVED_NATIVE_SOURCE_CHECK_ONLY',
              'candidate': report['candidate'], 'validatorSHA256': sha(__file__),
              'belowCutSourceIDPositionNamedFieldRowsExactlyRetained': 6933,
              'belowCutOriginalPolygonCornerUVRecordsExactlyRetained': len(actual[1]),
              'nativeHandDomainPositionsAndFloat32FieldsExactlyRetained': 1446,
              'all75ActualNativeRestRecordsAndHierarchyExactlyRetained': True,
              'bodyModifierOperatorsRetained': True,
              'protectedGenuineDonorTriangles': protected,
              'protectedDonorPositionUVNormalMaximumErrors': errors.tolist(),
              'closedOppositeWindingComponents': 1,
              'candidateVertices': len(body.data.vertices), 'contract': CONFIG['contract']}
    result['actualBodyConstantLinearRGB'] = actual_skin
    result['packedSelectedSourceImagesSHA256'] = packed_images
    result['restConstructionHasNoActionAndIdentityPoseBases'] = True
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
