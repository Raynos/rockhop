"""Independent read-only decoded export inspection; no render or acceptance."""
import hashlib
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path


def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def matrix(node):
    if 'matrix' in node:
        return [[node['matrix'][4 * j + i] for j in range(4)] for i in range(4)]
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    scale = node.get('scale', [1, 1, 1])
    rotation = [[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]]
    translation = node.get('translation', [0, 0, 0])
    return [[rotation[i][j] * scale[j] for j in range(3)] + [translation[i]]
            for i in range(3)] + [[0, 0, 0, 1]]


def audit(directory):
    raw = (directory / 'rider.glb').read_bytes()
    json_length = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + json_length])
    binary = raw[28 + json_length:]
    formats = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

    def accessor(index):
        item = gltf['accessors'][index]
        view = gltf['bufferViews'][item['bufferView']]
        fmt = '<' + formats[item['componentType']] * widths[item['type']]
        offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
        stride = view.get('byteStride', struct.calcsize(fmt))
        return [struct.unpack_from(fmt, binary, offset + n * stride)
                for n in range(item['count'])]

    contract = json.loads((directory / 'rider-contract.json').read_text())
    names = {node['name']: i for i, node in enumerate(gltf['nodes'])}
    parents = {child: i for i, node in enumerate(gltf['nodes'])
               for child in node.get('children', [])}
    worlds = {}

    def world(index):
        if index not in worlds:
            local = matrix(gltf['nodes'][index])
            worlds[index] = multiply(world(parents[index]), local) if index in parents else local
        return worlds[index]

    native_bones = contract['nativeRest']['bones']
    errors = []
    hierarchy_errors = []
    for bone in native_bones:
        index = names[bone['name']]
        expected_parent = bone['parent'] or 'RiderSkeleton'
        actual_parent = gltf['nodes'][parents[index]]['name']
        if actual_parent != expected_parent:
            hierarchy_errors.append([bone['name'], expected_parent, actual_parent])
        x, y, z = bone['head']
        actual = [world(index)[i][3] for i in range(3)]
        errors.append(math.dist(actual, [x, z, -y]))

    skin = gltf['skins'][0]
    joint_names = [gltf['nodes'][i]['name'] for i in skin['joints']]
    inverse_errors = []
    rest_skin_matrices = []
    for index, flattened in zip(skin['joints'], accessor(skin['inverseBindMatrices'])):
        inverse = [[flattened[4 * j + i] for j in range(4)] for i in range(4)]
        product = multiply(world(index), inverse)
        rest_skin_matrices.append(product)
        inverse_errors.append(max(abs(product[i][j] - (i == j))
                                  for i in range(4) for j in range(4)))
    assert len(skin['joints']) == len(native_bones) == 75
    assert not hierarchy_errors, hierarchy_errors
    assert max(errors) < 1e-6, max(errors)

    rest_skin_error = 0
    for node in gltf['nodes']:
        if 'mesh' not in node or 'skin' not in node:
            continue
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            for point, slots, weights in zip(accessor(attrs['POSITION']),
                                             accessor(attrs['JOINTS_0']), accessor(attrs['WEIGHTS_0'])):
                skinned = [0.0, 0.0, 0.0]
                for slot, weight in zip(slots, weights):
                    transform = rest_skin_matrices[int(slot)]
                    for axis in range(3):
                        skinned[axis] += weight * sum(transform[axis][k] * (*point, 1)[k]
                                                     for k in range(4))
                rest_skin_error = max(rest_skin_error, math.dist(point, skinned))
    assert rest_skin_error <= .0001, rest_skin_error

    body_node = gltf['nodes'][names['RiderBody']]
    body = gltf['meshes'][body_node['mesh']]['primitives'][0]
    attributes = body['attributes']
    ids = [int(row[0]) for row in accessor(attributes['_SOURCE_VERTEX_ID'])]
    positions = accessor(attributes['POSITION'])
    by_id = dict(zip(ids, positions))
    adjacency = {i: set() for i in by_id}
    indices = [int(row[0]) for row in accessor(body['indices'])]
    for offset in range(0, len(indices), 3):
        a, b, c = [ids[i] for i in indices[offset:offset + 3]]
        adjacency[a].update([b, c]); adjacency[b].update([a, c]); adjacency[c].update([a, b])
    unseen = set(adjacency)
    components = []
    while unseen:
        pending = [unseen.pop()]
        found = set(pending)
        while pending:
            for adjacent in adjacency[pending.pop()] & unseen:
                unseen.remove(adjacent); found.add(adjacent); pending.append(adjacent)
        components.append(found)
    components.sort(key=len, reverse=True)
    main = components[0]
    neck = {i for i, p in by_id.items() if 1.43 <= p[1] <= 1.58}
    head = {i for i, p in by_id.items() if p[1] > 1.58}
    assert neck <= main and head <= main

    rig_directory = directory.parent / 'rig04'
    full = json.loads((rig_directory / 'weights-full.json').read_text())
    four = json.loads((rig_directory / 'weights-four.json').read_text())
    losses = sorted([(sum(w for _, w in rows[4:]), i) for i, rows in enumerate(full)], reverse=True)
    export_joints = accessor(attributes['JOINTS_0'])
    export_weights = accessor(attributes['WEIGHTS_0'])
    field_error = 0
    field_mismatches = []
    for i, slots, weights in zip(ids, export_joints, export_weights):
        actual = {joint_names[int(slot)]: weight for slot, weight in zip(slots, weights) if weight > 0}
        expected = dict(four[i])
        row_error = max(abs(actual.get(name, 0) - expected.get(name, 0))
                        for name in set(actual) | set(expected))
        field_error = max(field_error, row_error)
        if set(actual) != set(expected) or row_error >= 2e-7:
            field_mismatches.append({'sourceID': i, 'maxWeightError': row_error,
                                     'source': expected, 'export': actual})

    eyes = []
    for name in ['GEO-body_male_realistic.eye.L', 'GEO-body_male_realistic.eye.R']:
        node = gltf['nodes'][names[name]]
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            a = primitive['attributes']; points = accessor(a['POSITION'])
            weighted = Counter()
            for slots, weights in zip(accessor(a['JOINTS_0']), accessor(a['WEIGHTS_0'])):
                for slot, weight in zip(slots, weights):
                    if weight > 0: weighted[joint_names[int(slot)]] += 1
            assert set(weighted) == {'DEF-spine.006'}, weighted
            assert min(p[1] for p in points) > 1.55 and max(p[1] for p in points) < 1.75
            eyes.append({'object': name, 'material': gltf['materials'][primitive['material']]['name'],
                         'bounds': [[min(p[k] for p in points), max(p[k] for p in points)] for k in range(3)],
                         'weightedJoints': dict(weighted)})

    return {'accepted': False, 'kind': 'independent static frozen04 readback',
            'glbSHA256': hashlib.sha256(raw).hexdigest(), 'sourceDirectory': str(directory),
            'jointCount': len(skin['joints']), 'hierarchyErrors': hierarchy_errors,
            'maxRestHeadErrorMetres': max(errors), 'maxInverseBindIdentityError': max(inverse_errors),
            'maxRestSkinPositionErrorMetres': rest_skin_error,
            'sourceIDCount': len(by_id), 'bodyComponentVertexCounts': [len(c) for c in components],
            'headAndNeckSameMainComponent': True, 'maxBodyFOURReadbackWeightError': field_error,
            'bodyFOURReadbackMismatchUniqueIDs': len({row['sourceID'] for row in field_mismatches}),
            'largestBodyFOURReadbackMismatches': sorted(field_mismatches,
                                                       key=lambda row: -row['maxWeightError'])[:20],
            'eyePrimitives': eyes,
            'removedFULLMassThresholdCounts': {str(t): sum(loss > t for loss, _ in losses)
                                             for t in [.001, .01, .05, .1, .2]},
            'largestRemovedFULLRows': [{'sourceID': i, 'positionGLTFMetres': by_id[i],
                                       'removedMass': loss, 'full': full[i], 'four': four[i]}
                                      for loss, i in losses[:20]],
            'limits': ['Static transport/topology/field identity only; parent judges actual played engine evidence.',
                       'FULL-to-FOUR deformation loss remains unmeasured; removed mass is not deformation error.',
                       'Connected body topology does not certify anatomical sculpture, moving shading, garments or contact.']}


if __name__ == '__main__':
    source = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    report = audit(source)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ['largestRemovedFULLRows', 'eyePrimitives']}, indent=2))
