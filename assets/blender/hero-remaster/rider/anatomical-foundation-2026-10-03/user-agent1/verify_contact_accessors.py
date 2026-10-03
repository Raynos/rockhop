"""Independent raw GLB ancestry check for frozen actual-loader contact proposals."""
import hashlib
import json
import struct
import sys
from pathlib import Path
source, map_file, output = map(Path, sys.argv[1:])
b = source.read_bytes(); n = struct.unpack_from('<I', b, 12)[0]
d = json.loads(b[20:20+n]); blob = b[28+n:]; receipt = json.loads(map_file.read_text())

def read(k):
    a = d['accessors'][k]; v = d['bufferViews'][a['bufferView']]
    code = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[a['componentType']]
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    stride = v.get('byteStride', struct.calcsize('<' + code) * count)
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return [struct.unpack_from('<' + code * count, blob, offset + i * stride) for i in range(a['count'])]

rows = []; maximum_raw_weight_difference = 0
for s in receipt['surfaces']:
    prim = d['meshes'][s['source']['mesh']]['primitives'][s['source']['primitive']]
    idx = read(prim['indices']); attrs = prim['attributes']; pos = read(attrs['POSITION'])
    weights, joints = read(attrs['WEIGHTS_0']), read(attrs['JOINTS_0'])
    source_ids = read(attrs['_SOURCE_ID']) if '_SOURCE_ID' in attrs else None
    for t in s['triangles']:
        ids = [idx[3 * t['triangleID'] + k][0] for k in range(3)]
        assert ids == t['vertexIDs']
        if source_ids is not None:
            assert [source_ids[i][0] for i in ids] == t['sourceIDs']
    for v in s['vertices']:
        i = v['vertexID']; assert list(pos[i]) == v['rawPositionM']
        assert [w['jointIndex'] for w in v['weights']] == list(joints[i])
        # Three normalizes skin weights on load. Verify that exact operation,
        # rather than falsely describing its normalized field as raw bytes.
        total = sum(abs(w) for w in weights[i])
        expected = [struct.unpack('<f', struct.pack('<f', w / total))[0] for w in weights[i]]
        actual = [w['weight'] for w in v['weights']]
        assert actual == expected, (s['label'], i, actual, expected)
        maximum_raw_weight_difference = max(maximum_raw_weight_difference, *[abs(a-c) for a, c in zip(actual, weights[i])])
        assert source_ids is None or source_ids[i][0] == v['sourceID']
    adjacency = {v['vertexID']: set() for v in s['vertices']}
    for t in s['triangles']:
        for i in t['vertexIDs']:
            adjacency[i].update(t['vertexIDs'])
    remaining = set(adjacency); components = []
    while remaining:
        queue = [remaining.pop()]; count = 0
        while queue:
            i = queue.pop(); count += 1; new = adjacency[i] & remaining
            remaining -= new; queue.extend(new)
        components.append(count)
    rows.append({'label': s['label'], 'vertexRowsVerified': len(s['vertices']), 'trianglesVerified': len(s['triangles']),
        'exportedRowConnectedComponentSizes': sorted(components, reverse=True)})
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {'status': 'PASS independent raw GLB accessor ancestry against actual-loader proposal',
    'GLBSHA256': sha(source), 'mapSHA256': sha(map_file), 'verifierSHA256': sha(__file__),
    'rawPositionsJointIndicesSourceIDsAndTriangleIndicesExact': True,
    'actualLoaderWeightsEqualFloat32L1NormalizedRawWeights': True,
    'maximumRawVsLoaderNormalizedWeightDifference': maximum_raw_weight_difference, 'surfaces': rows,
    'limits': ['Raw index component splits include export seam duplication; no closed-volume or automatic anatomical-label acceptance.',
        'Actual-loader rest positions/transforms are recorded by owner recipe; parent/Agent3 independently review.']}
output.write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report))
